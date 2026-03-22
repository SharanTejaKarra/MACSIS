"""
Tests for the 5 predefined test scenarios.

Validates the structure of scenario definitions and their mappings to mock data.
Full end-to-end tests (which need a real LLM) are marked with skipif.
"""
import os
import pytest

from main import SCENARIOS
from mock_data.customers import CUSTOMERS


class TestScenarioDefinitions:
    """Every scenario should have the right keys and point to valid customers."""

    @pytest.mark.parametrize("scenario_id", ["1", "2", "3", "4", "5"])
    def test_has_required_keys(self, scenario_id):
        scenario = SCENARIOS[scenario_id]
        assert "query" in scenario
        assert "customer_id" in scenario
        assert "name" in scenario

    @pytest.mark.parametrize("scenario_id", ["1", "2", "3", "4", "5"])
    def test_query_is_nonempty(self, scenario_id):
        assert len(SCENARIOS[scenario_id]["query"]) > 0

    @pytest.mark.parametrize("scenario_id", ["1", "2", "3", "4", "5"])
    def test_customer_exists(self, scenario_id):
        customer_id = SCENARIOS[scenario_id]["customer_id"]
        assert customer_id in CUSTOMERS, (
            f"Scenario {scenario_id} references {customer_id} "
            f"which doesn't exist in mock data"
        )


class TestScenarioCustomerMappings:
    """Verify each scenario targets the right customer for its purpose."""

    def test_scenario_1_basic_feature(self):
        s = SCENARIOS["1"]
        assert s["customer_id"] == "CUST-002"
        assert s["name"] == "Basic Feature Question"
        # CUST-002 is on Pro, should have dark mode
        assert "dark_mode" in CUSTOMERS["CUST-002"]["features_enabled"]

    def test_scenario_2_plan_mismatch(self):
        s = SCENARIOS["2"]
        assert s["customer_id"] == "CUST-001"
        assert s["name"] == "Plan-to-Feature Mismatch"
        # CUST-001 is on starter, shouldn't have API access
        assert "api_access" not in CUSTOMERS["CUST-001"]["features_enabled"]

    def test_scenario_3_contradiction(self):
        s = SCENARIOS["3"]
        assert s["customer_id"] == "CUST-002"
        assert s["name"] == "Contradictory Information"
        # CUST-002 is on pro, which has a 50k API limit (but docs say "unlimited")

    def test_scenario_4_sla_violation(self):
        s = SCENARIOS["4"]
        assert s["customer_id"] == "CUST-003"
        assert s["name"] == "SLA Violation"
        # CUST-003 is enterprise with CONTRACT-003
        assert CUSTOMERS["CUST-003"]["contract_id"] == "CONTRACT-003"

    def test_scenario_5_config_help(self):
        s = SCENARIOS["5"]
        assert s["customer_id"] == "CUST-004"
        assert s["name"] == "Account Configuration Help"
        # CUST-004 has 10 seats purchased, 10 used (at capacity)
        assert CUSTOMERS["CUST-004"]["seats_purchased"] == 10
        assert CUSTOMERS["CUST-004"]["seats_used"] == 10


class TestScenarioCount:
    def test_exactly_five_scenarios(self):
        assert len(SCENARIOS) == 5


# Full end-to-end tests require a real LLM. Skip if no API key is set.
needs_openai = pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set — skipping live LLM tests",
)


@needs_openai
class TestScenarioE2E:
    """
    These tests actually run the full graph with a real LLM.
    Only run them when you have an API key and want to burn tokens.
    """

    @pytest.fixture(scope="class")
    def graph(self):
        from agents.orchestrator import (
            orchestrator_analyze_node,
            orchestrator_synthesize_node,
            orchestrator_respond_node,
        )
        from agents.account_agent import account_agent_node
        from agents.feature_agent import feature_agent_node
        from agents.contract_agent import contract_agent_node
        from agents.escalation_agent import escalation_agent_node
        from graph.builder import build_graph

        return build_graph(
            orchestrator_analyze_fn=orchestrator_analyze_node,
            orchestrator_synthesize_fn=orchestrator_synthesize_node,
            orchestrator_respond_fn=orchestrator_respond_node,
            account_agent_fn=account_agent_node,
            feature_agent_fn=feature_agent_node,
            contract_agent_fn=contract_agent_node,
            escalation_agent_fn=escalation_agent_node,
        )

    @pytest.mark.parametrize("scenario_id", ["1", "2", "3", "4", "5"])
    def test_scenario_produces_response(self, graph, scenario_id):
        from main import build_initial_state

        scenario = SCENARIOS[scenario_id]
        initial_state = build_initial_state(
            query=scenario["query"],
            customer_id=scenario["customer_id"],
            scenario_id=f"scenario_{scenario_id}",
        )

        final_state = graph.invoke(initial_state)

        assert final_state["current_phase"] == "done"
        assert len(final_state["final_response"]) > 0
        assert len(final_state["token_usage_log"]) > 0
