# OnCall Memory

An incident response agent that remembers every production incident: symptoms, root cause,
the fix that worked, and the fixes that did **not**. When a new alert fires, it recalls
similar past incidents and gives the on-call engineer a briefing grounded in *their* history
instead of generic SRE advice.

## How Hindsight memory is used

| Hindsight call | Where | Purpose |
|---|---|---|
| `retain()` | `memory.retain_incident`, `retain_team_note`, `learn_from_feedback` | Store post-mortems, team conventions, and whether the agent's own advice worked |
| `recall()` | `memory.recall_similar` | Fetch similar incidents for a new alert (semantic, keyword, graph, temporal) |
| `reflect()` | `memory.pattern_insights` | Reason across the full history for recurring failure patterns |
| `create_bank(mission=...)` | `memory.ensure_bank` | Give the memory bank an on-call identity |

The UI shows the same LLM answering the same alert **without** and **with** memory, side by side.

## Run it

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # fill in keys
python seed.py              # load past incidents into Hindsight
python demo.py              # terminal before/after
streamlit run app.py        # web UI
```

Hindsight: use Hindsight Cloud (https://ui.hindsight.vectorize.io) or run the open-source server
(https://github.com/vectorize-io/hindsight). Docs: https://hindsight.vectorize.io/
