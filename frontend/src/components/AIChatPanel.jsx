import { useState, useRef, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { addMessage, setLoading, setLastToolCalls } from "../redux/chatSlice";
import { setFormState } from "../redux/interactionSlice";
import { sendChatMessage, saveInteraction } from "../api/client";

export default function AIChatPanel() {
  const dispatch = useDispatch();
  const { messages, loading, lastToolCalls } = useSelector((s) => s.chat);
  const formState = useSelector((s) => s.interaction);
  const [input, setInput] = useState("");
  const [saveStatus, setSaveStatus] = useState("");
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || loading) return;

    dispatch(addMessage({ role: "user", content: text }));
    setInput("");
    dispatch(setLoading(true));

    try {
      const history = messages.map(({ role, content }) => ({ role, content }));
      const result = await sendChatMessage(text, formState, history);
      dispatch(setFormState(result.form_state));
      dispatch(addMessage({ role: "assistant", content: result.reply }));
      dispatch(setLastToolCalls(result.tool_calls || []));
    } catch (err) {
      dispatch(
        addMessage({
          role: "assistant",
          content: "Sorry, I couldn't reach the AI backend. Is the FastAPI server running?",
        })
      );
    } finally {
      dispatch(setLoading(false));
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleLog = async () => {
    setSaveStatus("Saving...");
    try {
      await saveInteraction(formState);
      setSaveStatus("Saved ✓");
    } catch {
      setSaveStatus("Save failed");
    }
    setTimeout(() => setSaveStatus(""), 2500);
  };

  return (
    <div className="panel chat-panel">
      <div className="chat-header">
        <span className="ai-dot" />
        <div>
          <div className="panel-title">AI Assistant</div>
          <div className="panel-subtitle">Log interaction via chat</div>
        </div>
      </div>

      <div className="chat-messages" ref={scrollRef}>
        {messages.length === 0 && (
          <div className="chat-placeholder">
            Log interaction details here (e.g., "Met Dr. Smith, discussed Product X
            efficacy, positive sentiment, shared brochure") or ask for help.
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`chat-bubble ${m.role}`}>
            {m.content}
          </div>
        ))}
        {loading && <div className="chat-bubble assistant typing">Thinking...</div>}
        {lastToolCalls.length > 0 && !loading && (
          <div className="tool-trace">Tools used: {lastToolCalls.join(", ")}</div>
        )}
      </div>

      <div className="chat-input-row">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Describe interaction..."
          disabled={loading}
        />
        <button className="log-btn" onClick={handleSend} disabled={loading}>
          {loading ? "..." : "Send"}
        </button>
      </div>
    </div>
  );
}

