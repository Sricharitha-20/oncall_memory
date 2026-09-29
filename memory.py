"""Hindsight memory layer for the on-call incident response agent.

All memory operations live here so it's obvious (to judges and readers)
exactly where Hindsight is used:
  retain()  -> store post-mortems, team conventions, engineer feedback
  recall()  -> fetch similar past incidents for a new alert
  reflect() -> reason over the whole history for pattern insights
"""
import os
import time
from datetime import datetime

from dotenv import load_dotenv
from hindsight_client import Hindsight

load_dotenv()

BANK_ID = os.getenv("HINDSIGHT_BANK_ID", "oncall-memory")

MISSION = (
    "I am an on-call incident response assistant for a platform engineering team. "
    "I remember every production incident: symptoms, root cause, the fix that worked, "
    "and the fixes that did NOT work. I also learn the team's conventions and learn "
    "from engineer feedback on my own suggestions. I prefer proven, previously "
    "successful resolutions over generic advice."
)


def get_client() -> Hindsight:
    return Hindsight(
        base_url=os.getenv("HINDSIGHT_URL", "http://localhost:8888"),
        api_key=os.getenv("HINDSIGHT_API_KEY") or None,
        timeout=120.0,
    )


def ensure_bank(client: Hindsight) -> None:
    """Create the memory bank with a mission. Safe to call repeatedly."""
    try:
        client.create_bank(
            bank_id=BANK_ID,
            name="On-call Memory",
            mission=MISSION,
            disposition={"skepticism": 4, "literalism": 3, "empathy": 2},
        )
    except Exception as exc:  # bank may already exist
        print(f"[memory] create_bank note: {exc}")


def format_incident(inc: dict) -> str:
    return (
        f"Incident {inc['id']} ({inc['severity']}) on {inc['date']} affecting {inc['service']}.\n"
        f"Alert/symptoms: {inc['symptoms']}\n"
        f"Root cause: {inc['root_cause']}\n"
        f"Resolution that worked: {inc['resolution']}\n"
        f"Attempted but did NOT work: {inc['failed_attempts']}\n"
        f"Time to resolve: {inc['ttr_minutes']} minutes."
    )


def retain_incident(client: Hindsight, inc: dict) -> None:
    client.retain(
        bank_id=BANK_ID,
        content=format_incident(inc),
        context="post-mortem of a resolved production incident",
        timestamp=datetime.fromisoformat(inc["date"]),
        document_id=inc["id"],
        metadata={"service": inc["service"], "severity": inc["severity"]},
        retain_async=False,
    )


def retain_team_note(client: Hindsight, note: str, idx: int) -> None:
    client.retain(
        bank_id=BANK_ID,
        content=note,
        context="team on-call convention",
        document_id=f"team-note-{idx}",
        retain_async=False,
    )


def recall_similar(client: Hindsight, alert: str, max_tokens: int = 1500) -> list[dict]:
    """Recall memories relevant to a new alert (semantic + keyword + graph + temporal)."""
    res = client.recall(
        bank_id=BANK_ID,
        query=alert,
        budget="mid",
        max_tokens=max_tokens,
    )
    return [{"type": getattr(r, "type", "memory"), "text": r.text} for r in res.results]


def learn_from_feedback(
    client: Hindsight,
    alert: str,
    suggestion: str,
    resolution: str,
    worked: bool,
    notes: str = "",
) -> None:
    """Close the loop: store whether the agent's own advice worked."""
    outcome = "WORKED" if worked else "DID NOT WORK"
    content = (
        "Feedback on my own triage suggestion.\n"
        f"Alert: {alert}\n"
        f"My suggestion (summary): {suggestion[:600]}\n"
        f"Outcome: my suggestion {outcome}.\n"
        f"Actual resolution: {resolution}\n"
        f"Engineer notes: {notes or 'none'}"
    )
    client.retain(
        bank_id=BANK_ID,
        content=content,
        context="engineer feedback on the agent's own incident triage",
        document_id=f"feedback-{int(time.time())}",
        retain_async=False,
    )


def pattern_insights(client: Hindsight, service: str) -> str:
    """Use reflect() to reason across the full incident history."""
    answer = client.reflect(
        bank_id=BANK_ID,
        query=(
            f"What recurring failure patterns and proven fixes do we have for {service}? "
            "What should the team change to stop these from repeating?"
        ),
        budget="mid",
        context="weekly reliability review",
    )
    return answer.text
