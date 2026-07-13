"""
5 LangGraph tools for the HCP Log Interaction agent.

Each tool returns a JSON string describing what changed, in the shape:
    {"form_updates": {...}, "note": "..."}

form_updates is merged into the interaction form state by the graph.
note is optional extra context the agent can relay to the rep.
"""
import json
from datetime import datetime, timedelta
from typing import Optional, List

from langchain_core.tools import tool
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import Interaction


@tool
def log_interaction(
    hcp_name: Optional[str] = None,
    interaction_type: Optional[str] = None,
    date: Optional[str] = None,
    time: Optional[str] = None,
    attendees: Optional[str] = None,
    topics_discussed: Optional[str] = None,
    sentiment: Optional[str] = None,
    outcomes: Optional[str] = None,
    follow_up_actions: Optional[str] = None,
) -> str:
    """Extract structured interaction data from the rep's natural language description
    and populate the Log HCP Interaction form. Use this the FIRST time an interaction
    is described. date should be DD-MM-YYYY, time should be HH:MM (24hr). sentiment
    must be one of Positive, Neutral, Negative if mentioned or implied."""
    updates = {
        k: v
        for k, v in {
            "hcp_name": hcp_name,
            "interaction_type": interaction_type,
            "date": date,
            "time": time,
            "attendees": attendees,
            "topics_discussed": topics_discussed,
            "sentiment": sentiment,
            "outcomes": outcomes,
            "follow_up_actions": follow_up_actions,
        }.items()
        if v not in (None, "")
    }
    if "sentiment" in updates:
        normalized = updates["sentiment"].strip().capitalize()
        if normalized in {"Positive", "Neutral", "Negative"}:
            updates["sentiment"] = normalized
        else:
            updates.pop("sentiment")
    return json.dumps({"form_updates": updates, "note": "Logged interaction fields."})


@tool
def edit_interaction(field: str, value: str) -> str:
    """Correct or update a SINGLE field already on the form, without resetting the
    rest of the form. Use this when the rep corrects something already logged, e.g.
    'actually the sentiment was negative'. field must be one of: hcp_name,
    interaction_type, date, time, attendees, topics_discussed, sentiment, outcomes,
    follow_up_actions."""
    valid_fields = {
        "hcp_name",
        "interaction_type",
        "date",
        "time",
        "attendees",
        "topics_discussed",
        "sentiment",
        "outcomes",
        "follow_up_actions",
    }
    if field not in valid_fields:
        return json.dumps({"form_updates": {}, "note": f"Unknown field: {field}"})

    if field == "sentiment":
        value = value.strip().capitalize()
        if value not in {"Positive", "Neutral", "Negative"}:
            return json.dumps(
                {
                    "form_updates": {},
                    "note": f"Invalid sentiment value: {value}. Must be Positive, Neutral, or Negative.",
                }
            )

    return json.dumps(
        {"form_updates": {field: value}, "note": f"Updated {field} to '{value}'."}
    )


@tool
def suggest_materials(topics_discussed: str) -> str:
    """Suggest sales/marketing materials or product samples to log as shared with
    the HCP, based on the topics discussed in the interaction. Adds suggestions to
    materials_shared on the form."""
    topic_lower = topics_discussed.lower()
    catalog = {
        "efficacy": "Clinical Efficacy Data Sheet",
        "safety": "Safety Profile Brochure",
        "dosage": "Dosage & Administration Guide",
        "trial": "Phase III Trial Summary",
        "pricing": "Formulary & Pricing One-Pager",
        "oncology": "OncoBoost Phase III PDF",
        "cardio": "Cardiac Outcomes Study Reprint",
    }
    matches = [v for k, v in catalog.items() if k in topic_lower]
    if not matches:
        matches = ["General Product Overview Brochure"]
    return json.dumps(
        {
            "form_updates": {"materials_shared": matches},
            "note": f"Suggested materials: {', '.join(matches)}",
        }
    )


@tool
def schedule_followup(action: str, days_from_now: int = 14) -> str:
    """Schedule a follow-up action/task related to this HCP interaction, e.g.
    'Schedule follow-up meeting' or 'Send OncoBoost Phase III PDF'. days_from_now
    is how many days out the follow-up should be scheduled, default 14."""
    due = (datetime.now() + timedelta(days=days_from_now)).strftime("%d-%m-%Y")
    entry = f"{action} (by {due})"
    return json.dumps(
        {
            "form_updates": {"follow_up_actions": {"__append__": entry}},
            "note": f"Scheduled follow-up: {entry}",
        }
    )


def make_summarize_hcp_history_tool(db: Session):
    """Factory so the tool can access the current request's DB session."""

    @tool
    def summarize_hcp_history(hcp_name: str) -> str:
        """Look up past logged interactions with this HCP in the database and
        summarize sentiment trend and key history, to give the rep context before
        logging today's visit."""
        try:
            past: List[Interaction] = (
                db.query(Interaction)
                .filter(Interaction.hcp_name.ilike(f"%{hcp_name}%"))
                .order_by(Interaction.created_at.desc())
                .limit(5)
                .all()
            )
        except SQLAlchemyError:
            note = (
                f"Unable to query prior interactions for {hcp_name} right now, "
                "but I can still log this visit."
            )
            return json.dumps({"form_updates": {}, "note": note})

        if not past:
            note = f"No prior logged interactions found for {hcp_name}."
        else:
            lines = [
                f"{p.date or 'unknown date'}: sentiment={p.sentiment or 'n/a'}, "
                f"outcome={p.outcomes or 'n/a'}"
                for p in past
            ]
            note = f"Found {len(past)} prior interaction(s) with {hcp_name}:\n" + "\n".join(
                lines
            )
        return json.dumps({"form_updates": {}, "note": note})

    return summarize_hcp_history


def build_tools(db: Session):
    return [
        log_interaction,
        edit_interaction,
        suggest_materials,
        schedule_followup,
        make_summarize_hcp_history_tool(db),
    ]