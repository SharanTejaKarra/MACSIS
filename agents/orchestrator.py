"""Orchestrator nodes: analyze -> specialists -> synthesize -> respond (+ escalate if needed)."""
from __future__ import annotations

import json
import logging

from langchain_core.messages import SystemMessage, HumanMessage

from memory.state_schema import (
    GraphState, InvestigationStep, TokenUsage, EscalationDecision,
)
from memory.state_manager import get_all_findings_summary

from agents.llm_factory import get_llm

logger = logging.getLogger("macsis.orchestrator")


def _extract_token_usage(response, agent_name: str) -> TokenUsage:
    usage = getattr(response, "usage_metadata", None) or {}
    model = (getattr(response, "response_metadata", {}).get("model_name", ""))
    return TokenUsage(
        agent_name=agent_name,
        input_tokens=usage.get("input_tokens", 0),
        output_tokens=usage.get("output_tokens", 0),
        model=model,
    )


# ── step 1: classify the query and build an investigation plan ───────────

ANALYZE_SYSTEM_PROMPT = """\
You are the orchestrator of TechCorp's customer support system.
Your job is to classify the customer query and decide which specialist agents
should investigate it.

Available agents:
- account_agent: looks up customer profile, plan details, billing, enabled features
- feature_agent: checks feature availability, docs, configuration, limits
- contract_agent: reviews contracts, SLA terms, compliance

Output ONLY a valid JSON object — no markdown fences, no explanation:
{
    "query_classification": "<one of: basic_feature, plan_mismatch, contradiction, sla_violation, config_help>",
    "agents_needed": [
        {"agent_name": "<agent>", "reason": "why this agent is needed"}
    ]
}

Classification guide:
- basic_feature: straightforward feature question — usually just feature_agent
- plan_mismatch: customer asks about something their plan may not cover — account_agent + feature_agent
- contradiction: conflicting information between what the customer sees and what should be true — all three agents
- sla_violation: anything about SLA, uptime guarantees, response times — contract_agent (+ account_agent if context helps)
- config_help: setup or configuration question — account_agent + feature_agent"""


def orchestrator_analyze_node(state: GraphState) -> dict:
    llm = get_llm()

    messages = [
        SystemMessage(content=ANALYZE_SYSTEM_PROMPT),
        HumanMessage(content=(
            f"Customer ID: {state['customer_id']}\n"
            f"Query: {state['customer_query']}"
        )),
    ]

    response = llm.invoke(messages)
    token_usage = _extract_token_usage(response, "orchestrator_analyze")

    # parse classification
    try:
        raw = response.content.strip()
        # strip markdown code fences if the model wrapped them anyway
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
        parsed = json.loads(raw)
    except (json.JSONDecodeError, IndexError) as e:
        logger.error(f"Failed to parse orchestrator output: {e}\nRaw: {response.content}")
        # fallback: send everything to all agents
        parsed = {
            "query_classification": "contradiction",
            "agents_needed": [
                {"agent_name": "account_agent", "reason": "fallback — parse failure"},
                {"agent_name": "feature_agent", "reason": "fallback — parse failure"},
                {"agent_name": "contract_agent", "reason": "fallback — parse failure"},
            ],
        }

    classification = parsed.get("query_classification", "basic_feature")
    agents_needed = parsed.get("agents_needed", [])

    # convert to typed steps
    plan = []
    for i, entry in enumerate(agents_needed):
        plan.append(InvestigationStep(
            agent_name=entry["agent_name"],
            reason=entry.get("reason", ""),
            status="pending",
            order=i,
        ))

    return {
        "query_classification": classification,
        "investigation_plan": plan,
        "current_phase": "investigating",
        "token_usage_log": [token_usage],
        "messages": [response],
    }


# ── step 2: pull findings together and check for conflicts ───────────────

SYNTHESIZE_SYSTEM_PROMPT = """\
You are the orchestrator reviewing findings from specialist agents.

Your tasks:
1. Read each agent's findings carefully.
2. Explicitly check for CONTRADICTIONS between agents — for example, one agent
   says a feature is available but another says the customer's plan doesn't include it.
3. Decide whether this issue needs escalation (true/false) and explain why.

Output a JSON object — no markdown fences:
{
    "has_contradictions": true/false,
    "contradiction_details": "describe any conflicts, or empty string",
    "needs_escalation": true/false,
    "escalation_reason": "why, or empty string",
    "synthesis": "your overall assessment tying the findings together"
}"""


def orchestrator_synthesize_node(state: GraphState) -> dict:
    llm = get_llm()

    findings_text = get_all_findings_summary(state)

    messages = [
        SystemMessage(content=SYNTHESIZE_SYSTEM_PROMPT),
        HumanMessage(content=(
            f"Customer query: {state['customer_query']}\n\n"
            f"Classification: {state.get('query_classification', 'unknown')}\n\n"
            f"Agent findings:\n{findings_text}"
        )),
    ]

    response = llm.invoke(messages)
    token_usage = _extract_token_usage(response, "orchestrator_synthesize")

    try:
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
        parsed = json.loads(raw)
    except (json.JSONDecodeError, IndexError):
        logger.error(f"Synthesize parse failed, defaulting to no escalation")
        parsed = {
            "has_contradictions": False,
            "needs_escalation": False,
            "synthesis": response.content,
        }

    needs_escalation = parsed.get("needs_escalation", False)
    next_phase = "escalating" if needs_escalation else "responding"

    # stash reasoning for the respond step
    internal = (
        f"Contradictions: {parsed.get('contradiction_details', 'none')}\n"
        f"Synthesis: {parsed.get('synthesis', '')}\n"
        f"Escalation: {parsed.get('escalation_reason', 'not needed')}"
    )

    return {
        "current_phase": next_phase,
        "internal_reasoning": internal,
        "token_usage_log": [token_usage],
        "messages": [response],
    }


# ── step 3: craft the final customer-facing response ─────────────────────

RESPOND_SYSTEM_PROMPT = """\
You are writing the final response to a TechCorp customer support query.

You have access to:
- The original query
- Investigation findings from specialist agents
- Internal reasoning and contradiction analysis
- Escalation decision (if any)

Write a clear, helpful, and professional response. Include:
- A direct answer to the customer's question
- Relevant details from the investigation
- Next steps or recommendations
- If the issue was escalated, let them know a specialist team will follow up

Keep the tone friendly but professional. Don't reference internal agent names
or system details — the customer doesn't need to know about those."""


def orchestrator_respond_node(state: GraphState) -> dict:
    llm = get_llm()

    findings_text = get_all_findings_summary(state)
    escalation = state.get("escalation_decision")
    reasoning = state.get("internal_reasoning", "")

    escalation_note = "No escalation."
    if escalation and escalation.should_escalate:
        escalation_note = (
            f"ESCALATED — severity: {escalation.severity}, "
            f"reason: {escalation.reason}, "
            f"ticket: {escalation.ticket_id or 'pending'}, "
            f"routed to: {escalation.routed_to or 'triage'}"
        )

    messages = [
        SystemMessage(content=RESPOND_SYSTEM_PROMPT),
        HumanMessage(content=(
            f"Customer ID: {state['customer_id']}\n"
            f"Query: {state['customer_query']}\n\n"
            f"Findings:\n{findings_text}\n\n"
            f"Internal reasoning:\n{reasoning}\n\n"
            f"Escalation status: {escalation_note}"
        )),
    ]

    response = llm.invoke(messages)
    token_usage = _extract_token_usage(response, "orchestrator_respond")

    return {
        "final_response": response.content,
        "current_phase": "done",
        "token_usage_log": [token_usage],
        "messages": [response],
    }
