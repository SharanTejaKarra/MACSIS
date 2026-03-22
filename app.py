"""
Streamlit UI for MACSIS.
Run with: streamlit run app.py
"""
import re
import time
import streamlit as st
import yaml
from dotenv import load_dotenv

from memory.state_schema import GraphState


# -- input guardrails --

BLOCKED_PATTERNS = re.compile(
    r"\b(fuck|shit|bitch|asshole|dick|cunt|bastard|damn|stfu|wtf|"
    r"kill\s+(your|my|him|her|them)self|"
    r"hack|inject|drop\s+table|rm\s+-rf|<script)"
    , re.IGNORECASE
)

MIN_QUERY_LENGTH = 5

def validate_query(query: str) -> tuple[bool, str]:
    """Quick check before we burn LLM tokens on garbage input."""
    q = query.strip()
    if len(q) < MIN_QUERY_LENGTH:
        return False, "Query is too short. Please describe your support issue."
    if BLOCKED_PATTERNS.search(q):
        return False, "Your message contains inappropriate language. Please rephrase your support question."
    return True, ""
from monitoring.langfuse_config import init_langfuse
from monitoring.token_tracker import TokenTracker
from graph.builder import build_graph
from agents.orchestrator import (
    orchestrator_analyze_node,
    orchestrator_synthesize_node,
    orchestrator_respond_node,
)
from agents.account_agent import account_agent_node
from agents.feature_agent import feature_agent_node
from agents.contract_agent import contract_agent_node
from agents.escalation_agent import escalation_agent_node

load_dotenv()
init_langfuse()

SCENARIOS = {
    "1 — Basic Feature Question": {
        "query": "How do I enable dark mode in my account?",
        "customer_id": "CUST-002",
    },
    "2 — Plan-to-Feature Mismatch": {
        "query": (
            "I'm on the Starter plan, but I need to integrate with your API "
            "for my automation workflow. What are my options?"
        ),
        "customer_id": "CUST-001",
    },
    "3 — Contradictory Information": {
        "query": (
            "Your documentation says the Pro plan includes unlimited API calls, "
            "but I'm seeing rate limit errors after 1000 calls/month. I've checked "
            "my account and it shows Pro. Is this a bug, or am I misunderstanding something?"
        ),
        "customer_id": "CUST-002",
    },
    "4 — SLA Violation": {
        "query": (
            "I've been waiting for support response for 10 days on a critical "
            "production issue. My company has a contract with a 24-hour SLA guarantee. "
            "This is now costing us $500/day in lost revenue. Please verify if the SLA "
            "was violated and escalate this immediately."
        ),
        "customer_id": "CUST-003",
    },
    "5 — Account Configuration Help": {
        "query": (
            "Our company just migrated from the competitor platform. We have 15 users, "
            "but the plan shows only 10 seats. Can you help me understand the licensing "
            "model and figure out how to set up all our users?"
        ),
        "customer_id": "CUST-004",
    },
}

CUSTOMER_IDS = ["CUST-001", "CUST-002", "CUST-003", "CUST-004"]


@st.cache_resource
def get_graph():
    """Build the graph once and cache it."""
    return build_graph(
        orchestrator_analyze_fn=orchestrator_analyze_node,
        orchestrator_synthesize_fn=orchestrator_synthesize_node,
        orchestrator_respond_fn=orchestrator_respond_node,
        account_agent_fn=account_agent_node,
        feature_agent_fn=feature_agent_node,
        contract_agent_fn=contract_agent_node,
        escalation_agent_fn=escalation_agent_node,
    )


def build_initial_state(query: str, customer_id: str, scenario_id: str = "") -> dict:
    return {
        "customer_query": query,
        "customer_id": customer_id,
        "scenario_id": scenario_id,
        "messages": [],
        "query_classification": "",
        "investigation_plan": [],
        "current_phase": "analyzing",
        "findings": [],
        "escalation_decision": None,
        "final_response": "",
        "internal_reasoning": "",
        "token_usage_log": [],
        "errors": [],
    }


# -- page config --
st.set_page_config(page_title="MACSIS", page_icon="🎯", layout="wide")
st.title("MACSIS")
st.caption("MultiAgent Customer Support Intelligence System")

# -- sidebar --
with st.sidebar:
    st.header("Configuration")

    with open("config.yaml") as f:
        config = yaml.safe_load(f)
    provider = config["llm"]["provider"]
    model = config["llm"]["model"]
    st.info(f"**LLM:** {provider} / {model}")

    st.divider()
    mode = st.radio("Input mode", ["Preset scenario", "Custom query"])

    if mode == "Preset scenario":
        scenario_key = st.selectbox("Scenario", list(SCENARIOS.keys()))
        scenario = SCENARIOS[scenario_key]
        query = scenario["query"]
        customer_id = scenario["customer_id"]
        scenario_id = scenario_key.split(" ")[0]
    else:
        query = st.text_area("Customer query", height=100,
                             placeholder="Type a customer support question...")
        customer_id = st.selectbox("Customer ID", CUSTOMER_IDS)
        scenario_id = "custom"

    st.divider()
    run = st.button("Run query", type="primary", use_container_width=True)

# -- main area --
if run and query.strip():
    # guardrail check
    is_valid, rejection_msg = validate_query(query)
    if not is_valid:
        st.error(rejection_msg)
        st.stop()

    graph = get_graph()
    initial_state = build_initial_state(query, customer_id, f"scenario_{scenario_id}")

    # show what we're running
    st.markdown(f"**Query:** {query}")
    st.markdown(f"**Customer:** `{customer_id}`")
    st.divider()

    # run the graph
    with st.spinner("Agents are investigating..."):
        start = time.time()
        final_state = graph.invoke(initial_state)
        elapsed = time.time() - start

    # -- results --
    col1, col2 = st.columns([3, 2])

    with col1:
        # customer response
        st.subheader("Response")
        st.markdown(final_state.get("final_response", "*No response generated.*"))

        # internal reasoning
        reasoning = final_state.get("internal_reasoning", "")
        if reasoning:
            with st.expander("Internal reasoning", expanded=False):
                st.text(reasoning)

        # escalation
        esc = final_state.get("escalation_decision")
        if esc and esc.should_escalate:
            st.error(f"**Escalated** — {esc.severity.upper()}")
            esc_cols = st.columns(3)
            esc_cols[0].metric("Severity", esc.severity)
            esc_cols[1].metric("Ticket", esc.ticket_id or "—")
            esc_cols[2].metric("Routed to", esc.routed_to or "—")
            with st.expander("Escalation reason"):
                st.write(esc.reason)
        else:
            st.success("Resolved without escalation")

    with col2:
        # token tracking
        st.subheader("Token usage")
        tracker = TokenTracker(final_state.get("token_usage_log", []))
        totals = tracker.total()

        metric_cols = st.columns(3)
        metric_cols[0].metric("Input", f"{totals['input_tokens']:,}")
        metric_cols[1].metric("Output", f"{totals['output_tokens']:,}")
        metric_cols[2].metric("Total", f"{totals['total_tokens']:,}")

        # per-agent breakdown
        by_agent = tracker.by_agent()
        if by_agent:
            st.markdown("**Per-agent breakdown**")
            rows = []
            for name, data in sorted(by_agent.items()):
                rows.append({
                    "Agent": name,
                    "Input": data["input_tokens"],
                    "Output": data["output_tokens"],
                    "Total": data["total_tokens"],
                    "Calls": data["calls"],
                })
            st.dataframe(rows, use_container_width=True, hide_index=True)

        st.divider()

        # execution info
        st.subheader("Execution")
        st.metric("Time", f"{elapsed:.1f}s")
        st.metric("LLM calls", totals["num_llm_calls"])
        st.metric("Classification", final_state.get("query_classification", "—"))

        # agents invoked
        agents_used = list({f.agent_name for f in final_state.get("findings", [])})
        if agents_used:
            st.markdown("**Agents invoked:** " + ", ".join(sorted(agents_used)))

        # findings detail
        findings = final_state.get("findings", [])
        if findings:
            with st.expander(f"Agent findings ({len(findings)})"):
                for f in findings:
                    st.markdown(f"**{f.agent_name}**")
                    st.text(f.summary[:500] if f.summary else "(no summary)")
                    if f.errors:
                        st.warning(f"Errors: {', '.join(f.errors)}")
                    st.divider()

elif run:
    st.warning("Please enter a query first.")
