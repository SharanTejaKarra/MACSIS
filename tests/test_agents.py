"""
Unit tests for agent node functions using a mock LLM.

We patch get_llm where it's imported in each agent module so no real API calls
are made. The mock LLM returns predetermined responses that the agents can parse.
"""
import json
import pytest
from unittest.mock import patch, MagicMock
from langchain_core.messages import AIMessage

from memory.state_schema import GraphState, InvestigationStep
from agents.llm_factory import reset_llm


@pytest.fixture(autouse=True)
def clear_llm_cache():
    reset_llm()
    yield
    reset_llm()


def _make_ai_message(content: str) -> AIMessage:
    """Build an AIMessage with fake usage metadata so token tracking works."""
    msg = AIMessage(content=content)
    msg.usage_metadata = {"input_tokens": 100, "output_tokens": 50}
    msg.response_metadata = {"model_name": "mock-model"}
    return msg


def _make_mock_llm(content: str):
    """Create a mock LLM that returns a fixed AIMessage and supports bind_tools."""
    response = _make_ai_message(content)
    response.tool_calls = []

    mock_llm = MagicMock()
    mock_llm.invoke.return_value = response
    bound = MagicMock()
    bound.invoke.return_value = response
    mock_llm.bind_tools.return_value = bound
    return mock_llm


def _base_state(**overrides) -> dict:
    """Minimal valid graph state for testing."""
    state = {
        "customer_query": "How do I enable dark mode?",
        "customer_id": "CUST-002",
        "scenario_id": "",
        "messages": [],
        "query_classification": "basic_feature",
        "investigation_plan": [],
        "current_phase": "investigating",
        "findings": [],
        "escalation_decision": None,
        "final_response": "",
        "internal_reasoning": "",
        "token_usage_log": [],
        "errors": [],
    }
    state.update(overrides)
    return state


# patch at the import site in each agent module, not at agents.llm_factory

class TestOrchestratorAnalyze:
    def test_returns_classification_and_plan(self):
        llm_response = json.dumps({
            "query_classification": "basic_feature",
            "agents_needed": [
                {"agent_name": "feature_agent", "reason": "dark mode is a feature question"}
            ],
        })
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = _make_ai_message(llm_response)

        with patch("agents.orchestrator.get_llm", return_value=mock_llm):
            from agents.orchestrator import orchestrator_analyze_node
            result = orchestrator_analyze_node(_base_state())

        assert result["query_classification"] == "basic_feature"
        assert result["current_phase"] == "investigating"
        assert len(result["investigation_plan"]) == 1
        assert result["investigation_plan"][0].agent_name == "feature_agent"
        assert result["investigation_plan"][0].status == "pending"

    def test_token_usage_logged(self):
        llm_response = json.dumps({
            "query_classification": "basic_feature",
            "agents_needed": [],
        })
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = _make_ai_message(llm_response)

        with patch("agents.orchestrator.get_llm", return_value=mock_llm):
            from agents.orchestrator import orchestrator_analyze_node
            result = orchestrator_analyze_node(_base_state())

        assert len(result["token_usage_log"]) == 1
        assert result["token_usage_log"][0].agent_name == "orchestrator_analyze"

    def test_fallback_on_bad_json(self):
        """If the LLM returns garbage, the orchestrator should fall back to all agents."""
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = _make_ai_message("this is not json at all")

        with patch("agents.orchestrator.get_llm", return_value=mock_llm):
            from agents.orchestrator import orchestrator_analyze_node
            result = orchestrator_analyze_node(_base_state())

        assert len(result["investigation_plan"]) == 3
        agent_names = {s.agent_name for s in result["investigation_plan"]}
        assert agent_names == {"account_agent", "feature_agent", "contract_agent"}


class TestAccountAgent:
    def test_returns_findings(self):
        mock_llm = _make_mock_llm("Customer CUST-002 is on the Pro plan with 25 seats.")

        with patch("agents.account_agent.get_llm", return_value=mock_llm):
            from agents.account_agent import account_agent_node
            result = account_agent_node(_base_state())

        assert "findings" in result
        assert len(result["findings"]) == 1
        assert result["findings"][0].agent_name == "account_agent"

    def test_token_usage_logged(self):
        mock_llm = _make_mock_llm("Account details retrieved.")

        with patch("agents.account_agent.get_llm", return_value=mock_llm):
            from agents.account_agent import account_agent_node
            result = account_agent_node(_base_state())

        assert len(result["token_usage_log"]) == 1
        assert result["token_usage_log"][0].agent_name == "account_agent"


class TestFeatureAgent:
    def test_returns_findings(self):
        mock_llm = _make_mock_llm("Dark mode is available on Pro and above.")

        with patch("agents.feature_agent.get_llm", return_value=mock_llm):
            from agents.feature_agent import feature_agent_node
            result = feature_agent_node(_base_state())

        assert "findings" in result
        assert len(result["findings"]) == 1
        assert result["findings"][0].agent_name == "feature_agent"

    def test_token_usage_logged(self):
        mock_llm = _make_mock_llm("Feature info retrieved.")

        with patch("agents.feature_agent.get_llm", return_value=mock_llm):
            from agents.feature_agent import feature_agent_node
            result = feature_agent_node(_base_state())

        assert len(result["token_usage_log"]) == 1
        assert result["token_usage_log"][0].agent_name == "feature_agent"


class TestContractAgent:
    def test_returns_findings(self):
        mock_llm = _make_mock_llm("Contract reviewed, SLA terms verified.")

        with patch("agents.contract_agent.get_llm", return_value=mock_llm):
            from agents.contract_agent import contract_agent_node
            state = _base_state(customer_id="CUST-003")
            result = contract_agent_node(state)

        assert "findings" in result
        assert len(result["findings"]) == 1
        assert result["findings"][0].agent_name == "contract_agent"


class TestEscalationAgent:
    def test_returns_escalation_decision(self):
        llm_response = json.dumps({
            "severity": "critical",
            "should_escalate": True,
            "reason": "SLA breach with financial impact",
            "routed_to": "legal_compliance",
            "summary": "Enterprise customer SLA violated, penalty clause applies",
        })
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = _make_ai_message(llm_response)

        with patch("agents.escalation_agent.get_llm", return_value=mock_llm):
            from agents.escalation_agent import escalation_agent_node
            state = _base_state(
                customer_id="CUST-003",
                current_phase="escalating",
                internal_reasoning="SLA breached by 216 hours",
            )
            result = escalation_agent_node(state)

        assert result["escalation_decision"].should_escalate is True
        assert result["escalation_decision"].severity == "critical"
        assert result["escalation_decision"].routed_to == "legal_compliance"
        assert result["escalation_decision"].ticket_id is not None

    def test_no_escalation(self):
        llm_response = json.dumps({
            "severity": "low",
            "should_escalate": False,
            "reason": "Simple feature question, no risk",
            "routed_to": None,
            "summary": "Routine inquiry",
        })
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = _make_ai_message(llm_response)

        with patch("agents.escalation_agent.get_llm", return_value=mock_llm):
            from agents.escalation_agent import escalation_agent_node
            result = escalation_agent_node(_base_state())

        assert result["escalation_decision"].should_escalate is False
        assert result["escalation_decision"].ticket_id is None

    def test_token_usage_logged(self):
        llm_response = json.dumps({
            "severity": "low",
            "should_escalate": False,
            "reason": "test",
            "routed_to": None,
            "summary": "test",
        })
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = _make_ai_message(llm_response)

        with patch("agents.escalation_agent.get_llm", return_value=mock_llm):
            from agents.escalation_agent import escalation_agent_node
            result = escalation_agent_node(_base_state())

        assert len(result["token_usage_log"]) == 1
        assert result["token_usage_log"][0].agent_name == "escalation_agent"
