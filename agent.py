"""Incident triage agent: same LLM, with and without Hindsight memory."""
import os
import time

from dotenv import load_dotenv
from openai import OpenAI

import memory as mem

import re

load_dotenv()

llm = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)
MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")

_DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "incidents.json")
with open(_DATA_FILE) as _f:
    KNOWN_IDS = set(re.findall(r"INC-\d+", _f.read()))

OUTPUT_FORMAT = """Respond in markdown with exactly these sections:
### Likely root cause
(one or two sentences + confidence: low/medium/high)
### Do this first
(3-5 numbered steps, most valuable first)
### Do NOT waste time on
(fixes that are unlikely to help; write "n/a" if unknown)
### Escalate if
(one line)"""

BASELINE_SYSTEM = (
    "You are an on-call SRE assistant. You have NO access to this team's incident "
    "history. Give sound, generic troubleshooting advice.\n" + OUTPUT_FORMAT
)

MEMORY_SYSTEM = (
    "You are an on-call SRE assistant for one specific team. You are given MEMORIES "
    "retrieved from that team's incident history and feedback.\n"
    "Rules:\n"
    "- Ground your answer in the memories. Cite incident IDs (e.g. INC-2041) when you use them.\n"
    "- Prefer fixes that worked before. Explicitly steer away from fixes memory says failed.\n"
    "- Follow team conventions found in memory.\n"
    "- If feedback memory says your earlier suggestion did not work, do not repeat it.\n"
    "- If no memory is relevant, say so and fall back to generic advice.\n"
    "- In 'Do NOT waste time on', list ONLY fixes that failed in past incidents involving the SAME service or the SAME symptoms as this alert. Never mention other services.\n"
    "- Only cite incident IDs that appear verbatim in the recalled memories. Never invent an incident ID. If you are unsure of an ID, describe the incident without one.\n"
    "- Before listing a failed fix under 'Do NOT waste time on', check which service that incident was about. If it was not checkout-api (for example orders-api), leave it out completely, even if the fix sounds similar.\n"
    + OUTPUT_FORMAT
)


def scrub_citations(text: str) -> str:
    """Replace any INC-#### that isn't in incidents.json with a marker.
    Handles the non-breaking hyphen (U+2011) the model sometimes writes."""
    def check(m):
        normalized = "INC-" + m.group(1)
        return m.group(0) if normalized in KNOWN_IDS else "[unverified ID removed]"
    return re.sub(r"INC[-\u2011](\d+)", check, text)

def has_bad_id(text: str) -> bool:
    return any("INC-" + n not in KNOWN_IDS
               for n in re.findall(r"INC[-\u2011](\d+)", text))

def _chat(system: str, user: str, retries: int = 3) -> str:
    """LLM call with retry/backoff (Groq models can occasionally error)."""
    last_err = None
    for attempt in range(retries):
        try:
            resp = llm.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.2,
            )
            return resp.choices[0].message.content or ""
        except Exception as exc:
            last_err = exc
            time.sleep(2**attempt)
    raise RuntimeError(f"LLM call failed after {retries} attempts: {last_err}")


def triage_with_memory(client, alert: str) -> dict:
    memories = mem.recall_similar(client, alert)
    block = "\n".join(f"- [{m['type']}] {m['text']}" for m in memories) or "(no memories found)"
    prompt = f"ALERT:\n{alert}\n\nMEMORIES:\n{block}"
    answer = _chat(MEMORY_SYSTEM, prompt)
    for _ in range(2):  # retry if the model cited an ID that isn't in our data
        if not has_bad_id(answer):
            break
        answer = _chat(MEMORY_SYSTEM, prompt)
    answer = scrub_citations(answer)  # last resort: blank anything still fake
    return {"answer": answer, "memories": memories}




def triage_without_memory(alert: str) -> str:
    return _chat(BASELINE_SYSTEM, f"ALERT:\n{alert}")
