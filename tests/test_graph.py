"""
Integration test for the LangGraph graph structure.

Uses stub node functions (no real LLM calls) to verify:
- The graph compiles without errors
- It can be invoked and reaches END
- The final state has the expected shape
"""
import pytest
from memory.state_schema import (
    GraphState, InvestigationStep, AgentFinding, TokenUsage, EscalationDecision,
)
from graph.builder import build_graph


def _stub_orchestrator_analyze(state: GraphState) -> dict:
    """Classify and send to feature_agent only."""
    return {
        "query_classification": "basic_feature",
        "investigation_plan": [
            InvestigationStep(
                agent_name="feature_agent",
                reason="testing",
                status="pending",
                order=0,
            ),
        ],
        "current_phase": "investigating",
        "token_usage_log": [
            TokenUsage(agent_name="orchestrator_analyze", input_tokens=50, output_tokens=20),
        ],
    }


def _stub_account_agent(state: GraphState) -> dict:
    return {
        "findings": [
            AgentFinding(agent_name="account_agent", summary="stub account finding"),
        ],
        "investigation_plan": [
            InvestigationStep(agent_name="account_agent", reason="done", status="completed"),
        ],
        "token_usage_log": [
            TokenUsage(agent_name="account_agent", input_tokens=30, output_tokens=10),
        ],
    }


def _stub_feature_agent(state: GraphState) -> dict:
    return {
        "findings": [
            AgentFinding(agent_name="feature_agent", summary="stub feature finding"),
        ],
        "investigation_plan": [
            InvestigationStep(agent_name="feature_agent", reason="done", status="completed"),
        ],
        "token_usage_log": [
            TokenUsage(agent_name="feature_agent", input_tokens=40, output_tokens=15),
        ],
    }


def _stub_contract_agent(state: GraphState) -> dict:
    return {
        "findings": [
            AgentFinding(agent_name="contract_agent", summary="stub contract finding"),
        ],
        "investigation_plan": [
            InvestigationStep(agent_name="contract_agent", reason="done", status="completed"),
        ],
        "token_usage_log": [
            TokenUsage(agent_name="contract_agent", input_tokens=35, output_tokens=12),
        ],
    }


def _stub_orchestrator_synthesize(state: GraphState) -> dict:
    """Go straight to responding (no escalation)."""
    return {
        "current_phase": "responding",
        "internal_reasoning": "All looks fine, no conflicts found.",
        "token_usage_log": [
            TokenUsage(agent_name="orchestrator_synthesize", input_tokens=80, output_tokens=30),
        ],
    }


def _stub_escalation_agent(state: GraphState) -> dict:
    return {
        "findings": [
            AgentFinding(agent_name="escalation_agent", summary="escalation assessment"),
        ],
        "escalation_decision": EscalationDecision(
            should_escalate=True,
            severity="high",
            reason="stub escalation",
            ticket_id="ESC-TEST01",
            routed_to="engineering",
        ),
        "token_usage_log": [
            TokenUsage(agent_name="escalation_agent", input_tokens=60, output_tokens=25),
        ],
    }


def _stub_orchestrator_respond(state: GraphState) -> dict:
    return {
        "final_response": "Here is the answer to your question.",
        "current_phase": "done",
        "token_usage_log": [
            TokenUsage(agent_name="orchestrator_respond", input_tokens=70, output_tokens=40),
        ],
    }


class TestGraphCompilation:
    def test_graph_compiles(self):
        graph = build_graph(
            orchestrator_analyze_fn=_stub_orchestrator_analyze,
            orchestrator_synthesize_fn=_stub_orchestrator_synthesize,
            orchestrator_respond_fn=_stub_orchestrator_respond,
            account_agent_fn=_stub_account_agent,
            feature_agent_fn=_stub_feature_agent,
            contract_agent_fn=_stub_contract_agent,
            escalation_agent_fn=_stub_escalation_agent,
        )
        assert graph is not None


class TestGraphExecution:
    @pytest.fixture
    def graph(self):
        return build_graph(
            orchestrator_analyze_fn=_stub_orchestrator_analyze,
            orchestrator_synthesize_fn=_stub_orchestrator_synthesize,
            orchestrator_respond_fn=_stub_orchestrator_respond,
            account_agent_fn=_stub_account_agent,
            feature_agent_fn=_stub_feature_agent,
            contract_agent_fn=_stub_contract_agent,
            escalation_agent_fn=_stub_escalation_agent,
        )

    def test_reaches_end(self, graph):
        initial_state = {
            "customer_query": "How do I enable dark mode?",
            "customer_id": "CUST-002",
            "scenario_id": "",
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

        final_state = graph.invoke(initial_state)

        assert final_state["current_phase"] == "done"
        assert final_state["final_response"] != ""

    def test_final_state_has_required_keys(self, graph):
        initial_state = {
            "customer_query": "Test query",
            "customer_id": "CUST-001",
            "scenario_id": "",
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

        final_state = graph.invoke(initial_state)

        required_keys = [
            "customer_query", "customer_id", "query_classification",
            "investigation_plan", "current_phase", "findings",
            "final_response", "token_usage_log",
        ]
        for key in required_keys:
            assert key in final_state, f"Missing key: {key}"

    def test_token_usage_accumulated(self, graph):
        initial_state = {
            "customer_query": "Test query",
            "customer_id": "CUST-001",
            "scenario_id": "",
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

        final_state = graph.invoke(initial_state)

        # Should have at least: analyze + feature_agent + synthesize + respond
        assert len(final_state["token_usage_log"]) >= 3

    def test_findings_collected(self, graph):
        initial_state = {
            "customer_query": "Test query",
            "customer_id": "CUST-001",
            "scenario_id": "",
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

        final_state = graph.invoke(initial_state)

        # At least the feature_agent should have contributed a finding
        assert len(final_state["findings"]) >= 1
        agent_names = {f.agent_name for f in final_state["findings"]}
        assert "feature_agent" in agent_names
