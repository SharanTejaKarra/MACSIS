"""Routing functions for conditional edges in the graph."""
from __future__ import annotations
from memory.state_schema import GraphState


def route_to_agents(state: GraphState) -> list[str]:
    """Pick which specialist agents to fan out to (LangGraph runs them in parallel)."""
    plan = state.get("investigation_plan", [])
    agents_to_run = [
        step.agent_name
        for step in plan
        if step.status == "pending"
    ]

    # nothing pending? skip to synthesis
    if not agents_to_run:
        return ["orchestrator_synthesize"]

    return agents_to_run


def should_escalate(state: GraphState) -> str:
    """Route to escalation or straight to response."""
    phase = state.get("current_phase", "")
    if phase == "escalating":
        return "escalation_agent"
    return "orchestrator_respond"
