"""
Escalation Agent — severity assessment and routing.
Skips BaseAgent since it's a single LLM call, no tool loop.
"""
from __future__ import annotations

import json
import logging
import uuid

from langchain_core.messages import SystemMessage, HumanMessage

from agents.llm_factory import get_llm
from memory.state_schema import GraphState, EscalationDecision, AgentFinding, TokenUsage
from memory.state_manager import get_all_findings_summary

logger = logging.getLogger("macsis.escalation")


ESCALATION_SYSTEM_PROMPT = """\
You are the Escalation Agent for TechCorp customer support.

You receive findings from other agents plus the orchestrator's internal reasoning.
Your job is to decide:
1. The severity of this issue (low / medium / high / critical)
2. Whether to create an escalation ticket
3. Which team to route it to

Routing options:
- billing_team: payment disputes, refunds, plan changes
- engineering: bugs, outages, data issues
- legal_compliance: contract violations, SLA breaches
- account_management: relationship issues, churn risk, enterprise concerns
- product_team: feature requests, gaps in functionality

Output a JSON object — no markdown fences:
{
    "severity": "low|medium|high|critical",
    "should_escalate": true/false,
    "reason": "why this severity and decision",
    "routed_to": "team name or null if no escalation",
    "summary": "brief summary for the ticket"
}

Severity guide:
- low: minor question, info already available
- medium: real issue but workaround exists
- high: customer is blocked or losing money, no easy workaround
- critical: SLA breach, data loss, legal exposure, or enterprise customer at churn risk"""


def escalation_agent_node(state: GraphState) -> dict:
    llm = get_llm()

    findings_text = get_all_findings_summary(state)
    reasoning = state.get("internal_reasoning", "")

    messages = [
        SystemMessage(content=ESCALATION_SYSTEM_PROMPT),
        HumanMessage(content=(
            f"Customer ID: {state['customer_id']}\n"
            f"Query: {state['customer_query']}\n"
            f"Classification: {state.get('query_classification', 'unknown')}\n\n"
            f"Agent findings:\n{findings_text}\n\n"
            f"Orchestrator reasoning:\n{reasoning}"
        )),
    ]

    response = llm.invoke(messages)

    # token tracking
    usage = getattr(response, "usage_metadata", None) or {}
    model = getattr(response, "response_metadata", {}).get("model_name", "")
    token_record = TokenUsage(
        agent_name="escalation_agent",
        input_tokens=usage.get("input_tokens", 0),
        output_tokens=usage.get("output_tokens", 0),
        model=model,
    )

    # parse the decision
    try:
        raw = response.content.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
        parsed = json.loads(raw)
    except (json.JSONDecodeError, IndexError):
        logger.error(f"Escalation parse failed, defaulting to medium severity")
        parsed = {
            "severity": "medium",
            "should_escalate": True,
            "reason": "Parse failure — escalating to be safe",
            "routed_to": "account_management",
            "summary": response.content,
        }

    should_escalate = parsed.get("should_escalate", False)
    ticket_id = f"ESC-{uuid.uuid4().hex[:6].upper()}" if should_escalate else None

    decision = EscalationDecision(
        should_escalate=should_escalate,
        severity=parsed.get("severity", "medium"),
        reason=parsed.get("reason", ""),
        ticket_id=ticket_id,
        routed_to=parsed.get("routed_to"),
    )

    # store as a finding too so downstream nodes can see it
    finding = AgentFinding(
        agent_name="escalation_agent",
        summary=parsed.get("summary", parsed.get("reason", "")),
        raw_data=parsed,
        confidence=1.0,
    )

    return {
        "findings": [finding],
        "escalation_decision": decision,
        "token_usage_log": [token_record],
    }
