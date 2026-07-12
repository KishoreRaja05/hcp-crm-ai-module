from typing import Optional, List
from pydantic import BaseModel


class InteractionForm(BaseModel):
    hcp_name: Optional[str] = ""
    interaction_type: Optional[str] = "Meeting"
    date: Optional[str] = ""
    time: Optional[str] = ""
    attendees: Optional[str] = ""
    topics_discussed: Optional[str] = ""
    materials_shared: Optional[List[str]] = []
    samples_distributed: Optional[List[str]] = []
    sentiment: Optional[str] = ""
    outcomes: Optional[str] = ""
    follow_up_actions: Optional[str] = ""


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    form_state: InteractionForm
    chat_history: List[ChatMessage] = []


class ChatResponse(BaseModel):
    reply: str
    form_state: InteractionForm
    tool_calls: List[str] = []


class InteractionSaveRequest(InteractionForm):
    pass
