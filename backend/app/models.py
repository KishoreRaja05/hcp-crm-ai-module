from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.sql import func

from app.database import Base


class Interaction(Base):
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    hcp_name = Column(String(255), nullable=True)
    interaction_type = Column(String(100), nullable=True, default="Meeting")
    date = Column(String(20), nullable=True)
    time = Column(String(20), nullable=True)
    attendees = Column(Text, nullable=True)
    topics_discussed = Column(Text, nullable=True)
    materials_shared = Column(JSON, nullable=True, default=list)
    samples_distributed = Column(JSON, nullable=True, default=list)
    sentiment = Column(String(20), nullable=True)  # Positive / Neutral / Negative
    outcomes = Column(Text, nullable=True)
    follow_up_actions = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
