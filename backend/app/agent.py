import json
from typing import TypedDict, Annotated, Sequence

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_groq import ChatGroq
from langgraph.errors import GraphRecursionError
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from sqlalchemy.orm import Session

from app.config import GROQ_API_KEY, GROQ_MODEL
from app.tools import build_tools

SYSTEM_PROMPT = """You are the AI Assistant embedded in a pharma field rep's CRM, on the
Log HCP Interaction screen. The rep will describe interactions with healthcare
professionals in natural language, or ask you to correct/add to what's logged.

Rules:
- Never invent facts the rep didn't say. Only extract what's stated or clearly implied.
- On the FIRST description of a visit, call log_interaction with everything you can
  extract. In that SAME turn, also call suggest_materials if the topics discussed
  suggest relevant materials, and call schedule_followup if a next step was
  mentioned. You CAN and SHOULD call multiple different tools together in one turn
  when the message gives you reason to.
- On a correction to something already logged, call edit_interaction for just that
  field.
- If the rep asks about history/past visits with an HCP, call summarize_hcp_history.
- IMPORTANT: never call the exact same tool twice in a single turn, even with
  different arguments. Each tool may run at most once per turn.
- Once you've called every tool that's relevant for this message, STOP calling
  tools and reply to the rep in plain text with a short, natural confirmation of
  what you updated. Do not repeat the raw JSON. Keep replies to 1-3 sentences.
- If you are ever unsure what to do next, just reply in plain text instead of
  calling another tool.
"""

# Hard ceiling on tool calls per single /chat turn. This is independent of
# LangGraph's recursion_limit and guarantees the graph cannot loop forever
# regardless of what the model decides to do.
MAX_TOOL_CALLS_PER_TURN = 6


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    form_state: dict
    tool_calls_made: list


def build_graph(db: Session):
    tools = build_tools(db)
    llm = ChatGroq(api_key=GROQ_API_KEY, model=GROQ_MODEL, temperature=0.2)
    llm_with_tools = llm.bind_tools(tools)
    tool_node = ToolNode(tools)

    def agent_node(state: AgentState):
        messages = state["messages"]
        if not any(isinstance(m, SystemMessage) for m in messages):
            messages = [SystemMessage(content=SYSTEM_PROMPT), *messages]

        # Hard stop: if we've already made enough tool calls this turn, force
        # the model to answer in plain text instead of calling another tool.
        if len(state.get("tool_calls_made", [])) >= MAX_TOOL_CALLS_PER_TURN:
            response = llm.invoke(
                [
                    *messages,
                    SystemMessage(
                        content=(
                            "You have made enough tool calls for this turn. "
                            "Do not call any more tools. Reply in plain text "
                            "summarizing what you've updated so far."
                        )
                    ),
                ]
            )
            return {"messages": [response]}

        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def apply_tool_results(state: AgentState):
        """Runs after ToolNode: merge each ToolMessage's form_updates into form_state."""
        form_state = dict(state["form_state"])
        tool_calls_made = list(state.get("tool_calls_made", []))
        for msg in state["messages"]:
            if isinstance(msg, ToolMessage):
                try:
                    payload = json.loads(msg.content)
                except (json.JSONDecodeError, TypeError):
                    continue
                updates = payload.get("form_updates", {})
                for k, v in updates.items():
                    if k in ("materials_shared", "samples_distributed") and isinstance(
                        v, list
                    ):
                        existing = form_state.get(k) or []
                        form_state[k] = list(dict.fromkeys(existing + v))
                    elif isinstance(v, dict) and "__append__" in v:
                        existing = form_state.get(k) or ""
                        addition = v["__append__"]
                        form_state[k] = f"{existing}; {addition}" if existing else addition
                    else:
                        form_state[k] = v
                if msg.name:
                    tool_calls_made.append(msg.name)
        return {"form_state": form_state, "tool_calls_made": tool_calls_made}

    def should_continue(state: AgentState):
        last = state["messages"][-1]
        tool_calls = getattr(last, "tool_calls", None)
        if not tool_calls:
            return END

        # Hard stop: never let total tool calls in this turn exceed the cap,
        # even if the model just requested more.
        if len(state.get("tool_calls_made", [])) >= MAX_TOOL_CALLS_PER_TURN:
            return END

        # Refuse to loop on a tool the model has already called this turn.
        already_called = set(state.get("tool_calls_made", []))
        requested_names = {tc["name"] for tc in tool_calls}
        if requested_names.issubset(already_called):
            return END

        return "tools"

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.add_node("apply_updates", apply_tool_results)

    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "apply_updates")
    graph.add_edge("apply_updates", "agent")

    return graph.compile()


def run_agent(db: Session, message: str, form_state: dict, chat_history: list):
    app_graph = build_graph(db)

    messages: list[BaseMessage] = [SystemMessage(content=SYSTEM_PROMPT)]
    for turn in chat_history:
        if turn["role"] == "user":
            messages.append(HumanMessage(content=turn["content"]))
        else:
            messages.append(SystemMessage(content=f"[assistant said]: {turn['content']}"))
    messages.append(HumanMessage(content=message))

    try:
        result = app_graph.invoke(
            {"messages": messages, "form_state": form_state, "tool_calls_made": []},
            config={"recursion_limit": 25},
        )
    except GraphRecursionError:
        # Absolute last-resort safety net: even if every other guard somehow
        # fails, never let this crash the /chat endpoint with a 500. Return
        # the form state unchanged and tell the rep plainly what happened.
        return {
            "reply": (
                "I got a bit stuck processing that one — could you try rephrasing "
                "it, or send it as a couple of shorter messages instead?"
            ),
            "form_state": form_state,
            "tool_calls": [],
        }

    final_message = result["messages"][-1]
    reply = final_message.content if isinstance(final_message.content, str) else str(
        final_message.content
    )
    if not reply.strip():
        reply = "Got it — I've updated the form based on what you shared."

    return {
        "reply": reply,
        "form_state": result["form_state"],
        "tool_calls": result.get("tool_calls_made", []),
    }