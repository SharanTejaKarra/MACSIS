from __future__ import annotations

from typing import TypedDict, Literal, Annotated
from dataclasses import dataclass, field
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
import operator
import time
import uuid


# -- small structures that get stacked inside the graph state --

@dataclass
class AgentFinding:
    """Single agent's findings."""
    agent_name: str
    finding_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    summary: str = ""
    raw_data: dict = field(default_factory=dict)
    confidence: float = 1.0
    timestamp: float = field(default_factory=time.time)
    tool_calls_made: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class InvestigationStep:
    """One step in the investigation plan."""
    agent_name: str
    reason: str
    depends_on: list[str] = field(default_factory=list)
    status: Literal["pending", "running", "completed", "failed", "skipped"] = "pending"
    order: int = 0


@dataclass
class EscalationDecision:
    """Escalation verdict."""
    should_escalate: bool = False
    severity: Literal["low", "medium", "high", "critical"] = "low"
    reason: str = ""
    ticket_id: str | None = None
    routed_to: str | None = None


@dataclass
class TokenUsage:
    """Tokens used in a single LLM call."""
    agent_name: str
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = ""
    timestamp: float = field(default_factory=time.time)


# -- reducers for append-only state fields --

def append_findings(existing: list[AgentFinding], new: list[AgentFinding]) -> list[AgentFinding]:
    return existing + new


def append_token_usage(existing: list[TokenUsage], new: list[TokenUsage]) -> list[TokenUsage]:
    return existing + new


def merge_investigation_plan(
    existing: list[InvestigationStep], new: list[InvestigationStep]
) -> list[InvestigationStep]:
    """Merge by agent_name — update status without clobbering other steps."""
    plan = {s.agent_name: s for s in existing}
    for step in new:
        plan[step.agent_name] = step
    return list(plan.values())


# -- the actual graph state that flows through every node --

class GraphState(TypedDict):
    # input
    customer_query: str
    customer_id: str
    scenario_id: str

    # conversation (uses langgraph's built-in message reducer)
    messages: Annotated[list[BaseMessage], add_messages]

    # orchestrator planning
    query_classification: str
    investigation_plan: Annotated[list[InvestigationStep], merge_investigation_plan]
    current_phase: Literal[
        "analyzing", "investigating", "synthesizing", "responding", "escalating", "done"
    ]

    # findings from specialist agents (append-only)
    findings: Annotated[list[AgentFinding], append_findings]

    # escalation
    escalation_decision: EscalationDecision | None

    # final output
    final_response: str
    internal_reasoning: str

    # token tracking (append-only)
    token_usage_log: Annotated[list[TokenUsage], append_token_usage]

    # errors (append-only)
    errors: Annotated[list[str], operator.add]
