"""Cross-agent context — formats other agents' findings for prompt injection."""
from __future__ import annotations
from memory.state_schema import GraphState


def build_context_for_agent(state: GraphState, agent_name: str) -> str:
    """Gather findings from other agents as context for the current one."""
    findings = state.get("findings", [])
    other_findings = [f for f in findings if f.agent_name != agent_name]

    if not other_findings:
        return "No prior findings from other agents."

    parts = []
    for f in other_findings:
        parts.append(f"--- {f.agent_name} ---")
        parts.append(f.summary)
        if f.raw_data:
            parts.append(f"  Data: {f.raw_data}")
        parts.append("")

    return "\n".join(parts)


def get_customer_id(state: GraphState) -> str:
    return state.get("customer_id", "unknown")
