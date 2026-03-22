"""Convenience accessors for graph state."""
from __future__ import annotations
from memory.state_schema import GraphState, AgentFinding, InvestigationStep


def get_findings_by_agent(state: GraphState, agent_name: str) -> list[AgentFinding]:
    return [f for f in state.get("findings", []) if f.agent_name == agent_name]


def get_all_findings_summary(state: GraphState) -> str:
    """Readable summary of all agent findings so far."""
    findings = state.get("findings", [])
    if not findings:
        return "No findings yet."

    lines = []
    for f in findings:
        prefix = f"[{f.agent_name}]"
        lines.append(f"{prefix} {f.summary}")
        if f.errors:
            lines.append(f"  ^ encountered errors: {', '.join(f.errors)}")
    return "\n".join(lines)


def is_plan_complete(state: GraphState) -> bool:
    """True if all investigation steps are done."""
    plan = state.get("investigation_plan", [])
    if not plan:
        return True
    return all(s.status in ("completed", "failed", "skipped") for s in plan)


def get_pending_steps(state: GraphState) -> list[InvestigationStep]:
    return [s for s in state.get("investigation_plan", []) if s.status == "pending"]
