"""Streamlit UI: triage with vs without memory, teach the agent, see patterns."""
import streamlit as st

import memory as mem
from agent import triage_with_memory, triage_without_memory

st.set_page_config(page_title="OnCall Memory", page_icon="🚨", layout="wide")

DEMO_ALERT = (
    "checkout-api p99 latency 8.2s, error rate 14%. DB connection count at 100% of pool. "
    "Started ~10 minutes after deploy v2.31 of checkout-api."
)


@st.cache_resource
def client():
    c = mem.get_client()
    mem.ensure_bank(c)
    return c


st.title("🚨 OnCall Memory")
st.caption("An incident response agent that remembers every outage, powered by Hindsight.")

tab_triage, tab_learn, tab_patterns = st.tabs(["1. Triage an alert", "2. Teach the agent", "3. Pattern insights"])

with tab_triage:
    alert = st.text_area("Incoming alert", value=DEMO_ALERT, height=110)
    if st.button("Triage", type="primary"):
        st.session_state["alert"] = alert
        left, right = st.columns(2)
        with left:
            st.subheader("Without memory")
            with st.spinner("Thinking..."):
                base = triage_without_memory(alert)
            st.markdown(base)
        with right:
            st.subheader("With Hindsight memory")
            with st.spinner("Recalling past incidents..."):
                res = triage_with_memory(client(), alert)
            st.markdown(res["answer"])
            st.session_state["answer"] = res["answer"]
            with st.expander(f"{len(res['memories'])} memories recalled"):
                for m in res["memories"]:
                    st.markdown(f"**[{m['type']}]** {m['text']}")

with tab_learn:
    st.write("After the incident, tell the agent what actually happened. It retains this and uses it next time.")
    last_alert = st.session_state.get("alert", DEMO_ALERT)
    last_answer = st.session_state.get("answer", "(no suggestion yet, run a triage first)")
    st.text_area("Alert", value=last_alert, key="fb_alert", height=80)
    resolution = st.text_area("What actually resolved it?", height=90)
    worked = st.radio("Did the agent's suggestion work?", ["Yes", "No"], horizontal=True)
    notes = st.text_input("Notes for future on-call (optional)")
    if st.button("Save to memory"):
        if not resolution.strip():
            st.warning("Add the actual resolution first.")
        else:
            mem.learn_from_feedback(
                client(),
                st.session_state["fb_alert"],
                last_answer,
                resolution,
                worked == "Yes",
                notes,
            )
            st.success("Retained. Go back to tab 1 and triage a similar alert to see the difference.")

with tab_patterns:
    service = st.text_input("Service", value="checkout-api")
    if st.button("Analyze history"):
        with st.spinner("Reflecting over incident history..."):
            st.markdown(mem.pattern_insights(client(), service))
