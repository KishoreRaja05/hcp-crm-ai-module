from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import CORS_ORIGINS
from app.database import Base, engine, get_db
from app.models import Interaction
from app.schemas import ChatRequest, ChatResponse, InteractionSaveRequest
from app.agent import run_agent

try:
    Base.metadata.create_all(bind=engine)
except SQLAlchemyError:
    # Allow the API to boot even if the configured database is unavailable.
    # Routes that need persistence will fail gracefully when the DB is unreachable.
    pass

app = FastAPI(title="AI-First CRM - HCP Module")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    result = run_agent(
        db=db,
        message=req.message,
        form_state=req.form_state.model_dump(),
        chat_history=[m.model_dump() for m in req.chat_history],
    )
    return ChatResponse(**result)


@app.post("/interactions")
def save_interaction(req: InteractionSaveRequest, db: Session = Depends(get_db)):
    record = Interaction(**req.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return {"id": record.id, "status": "saved"}


@app.get("/interactions")
def list_interactions(db: Session = Depends(get_db)):
    rows = db.query(Interaction).order_by(Interaction.created_at.desc()).all()
    return [
        {c.name: getattr(r, c.name) for c in Interaction.__table__.columns} for r in rows
    ]
