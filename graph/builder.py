"""Wires up the LangGraph StateGraph and compiles it."""
from __future__ import annotations

from langgraph.graph import StateGraph, START, END
from memory.state_schema import GraphState
from graph.routing import route_to_agents, should_escalate


def build_graph(
    orchestrator_analyze_fn,
    orchestrator_synthesize_fn,
    orchestrator_respond_fn,
    account_agent_fn,
    feature_agent_fn,
    contract_agent_fn,
    escalation_agent_fn,
):
    """Build and compile the agent graph. Takes node fns as args for testability."""
    graph = StateGraph(GraphState)

    # register all nodes
    graph.add_node("orchestrator_analyze", orchestrator_analyze_fn)
    graph.add_node("account_agent", account_agent_fn)
    graph.add_node("feature_agent", feature_agent_fn)
    graph.add_node("contract_agent", contract_agent_fn)
    graph.add_node("orchestrator_synthesize", orchestrator_synthesize_fn)
    graph.add_node("escalation_agent", escalation_agent_fn)
    graph.add_node("orchestrator_respond", orchestrator_respond_fn)

    # entry point: always start with analysis
    graph.add_edge(START, "orchestrator_analyze")

    # fan-out: orchestrator decides which specialists to invoke
    graph.add_conditional_edges(
        "orchestrator_analyze",
        route_to_agents,
        {
            "account_agent": "account_agent",
            "feature_agent": "feature_agent",
            "contract_agent": "contract_agent",
            "orchestrator_synthesize": "orchestrator_synthesize",
        },
    )

    # fan-in: all specialists converge at synthesis
    graph.add_edge("account_agent", "orchestrator_synthesize")
    graph.add_edge("feature_agent", "orchestrator_synthesize")
    graph.add_edge("contract_agent", "orchestrator_synthesize")

    # after synthesis: escalate or respond
    graph.add_conditional_edges(
        "orchestrator_synthesize",
        should_escalate,
        {
            "escalation_agent": "escalation_agent",
            "orchestrator_respond": "orchestrator_respond",
        },
    )

    # escalation always leads to response
    graph.add_edge("escalation_agent", "orchestrator_respond")

    # response is the end
    graph.add_edge("orchestrator_respond", END)

    return graph.compile()
