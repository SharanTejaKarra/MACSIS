"""
Tests for all 16 mock tools across account, feature, contract, and escalation modules.

Every tool gets tested for both valid and invalid inputs.
Failure simulation is disabled by mocking random.random to always return 1.0.
"""
import pytest
from unittest.mock import patch


# Disable simulated latency and failures for all tool tests.
# random.random() returning 1.0 is above any failure_rate threshold,
# and we patch time.sleep so tests don't actually wait.
@pytest.fixture(autouse=True)
def disable_simulation():
    with patch("time.sleep"), patch("random.random", return_value=1.0), \
         patch("random.uniform", return_value=0.0):
        yield


# ---------- account_tools ----------

class TestLookupCustomer:
    def test_valid_customer(self):
        from tools.account_tools import lookup_customer
        result = lookup_customer.invoke({"customer_id": "CUST-001"})
        assert result["customer_id"] == "CUST-001"
        assert result["name"] == "Alice Johnson"
        assert result["plan"] == "starter"

    def test_invalid_customer(self):
        from tools.account_tools import lookup_customer
        result = lookup_customer.invoke({"customer_id": "CUST-999"})
        assert "error" in result


class TestGetBillingHistory:
    def test_valid_customer(self):
        from tools.account_tools import get_billing_history
        result = get_billing_history.invoke({"customer_id": "CUST-002"})
        assert isinstance(result, list)
        assert len(result) > 0
        assert "amount" in result[0]

    def test_invalid_customer(self):
        from tools.account_tools import get_billing_history
        result = get_billing_history.invoke({"customer_id": "CUST-999"})
        assert isinstance(result, list)
        assert "error" in result[0]


class TestCheckAccountStatus:
    def test_valid_customer(self):
        from tools.account_tools import check_account_status
        result = check_account_status.invoke({"customer_id": "CUST-003"})
        assert result["customer_id"] == "CUST-003"
        assert result["plan"] == "enterprise"
        assert result["seats_purchased"] == 100
        assert result["seats_available"] == 100 - 85

    def test_invalid_customer(self):
        from tools.account_tools import check_account_status
        result = check_account_status.invoke({"customer_id": "CUST-999"})
        assert "error" in result


class TestListEnabledFeatures:
    def test_valid_customer(self):
        from tools.account_tools import list_enabled_features
        result = list_enabled_features.invoke({"customer_id": "CUST-001"})
        assert isinstance(result, list)
        assert "dashboard" in result

    def test_pro_customer_has_api(self):
        from tools.account_tools import list_enabled_features
        result = list_enabled_features.invoke({"customer_id": "CUST-002"})
        assert "api_access" in result
        assert "dark_mode" in result

    def test_invalid_customer(self):
        from tools.account_tools import list_enabled_features
        result = list_enabled_features.invoke({"customer_id": "CUST-999"})
        assert isinstance(result, list)
        assert "error" in result[0]


# ---------- feature_tools ----------

class TestGetFeatureMatrix:
    def test_returns_dict(self):
        from tools.feature_tools import get_feature_matrix
        result = get_feature_matrix.invoke({})
        assert isinstance(result, dict)
        assert "dark_mode" in result
        assert "api_access" in result

    def test_plan_availability(self):
        from tools.feature_tools import get_feature_matrix
        result = get_feature_matrix.invoke({})
        assert result["dark_mode"]["starter"] is False
        assert result["dark_mode"]["pro"] is True
        assert result["dashboard"]["starter"] is True


class TestGetFeatureDocumentation:
    def test_valid_feature(self):
        from tools.feature_tools import get_feature_documentation
        result = get_feature_documentation.invoke({"feature_name": "dark_mode"})
        assert result["feature"] == "dark_mode"
        assert "description" in result
        assert "setup_instructions" in result

    def test_api_access_has_public_docs_note(self):
        from tools.feature_tools import get_feature_documentation
        result = get_feature_documentation.invoke({"feature_name": "api_access"})
        # This is the intentional contradiction in the mock data
        assert "public_docs_note" in result

    def test_unknown_feature(self):
        from tools.feature_tools import get_feature_documentation
        result = get_feature_documentation.invoke({"feature_name": "teleportation"})
        assert "error" in result


class TestValidateConfiguration:
    def test_active_feature(self):
        from tools.feature_tools import validate_configuration
        result = validate_configuration.invoke({
            "feature_name": "dark_mode",
            "customer_id": "CUST-002",
        })
        assert result["status"] == "active"
        assert result["plan_eligible"] is True
        assert result["currently_enabled"] is True

    def test_not_available_on_plan(self):
        from tools.feature_tools import validate_configuration
        result = validate_configuration.invoke({
            "feature_name": "api_access",
            "customer_id": "CUST-001",
        })
        assert result["status"] == "not_available_on_plan"

    def test_invalid_customer(self):
        from tools.feature_tools import validate_configuration
        result = validate_configuration.invoke({
            "feature_name": "dark_mode",
            "customer_id": "CUST-999",
        })
        assert "error" in result

    def test_unknown_feature(self):
        from tools.feature_tools import validate_configuration
        result = validate_configuration.invoke({
            "feature_name": "jetpack",
            "customer_id": "CUST-001",
        })
        assert "error" in result


class TestCheckFeatureLimits:
    def test_api_pro_limits(self):
        from tools.feature_tools import check_feature_limits
        result = check_feature_limits.invoke({
            "feature_name": "api_access",
            "plan": "pro",
        })
        assert result["limits"]["monthly_limit"] == 50000

    def test_feature_not_on_plan(self):
        from tools.feature_tools import check_feature_limits
        result = check_feature_limits.invoke({
            "feature_name": "api_access",
            "plan": "starter",
        })
        assert result["limits"] is None
        assert "not available" in result["note"]

    def test_no_limits_feature(self):
        from tools.feature_tools import check_feature_limits
        result = check_feature_limits.invoke({
            "feature_name": "dashboard",
            "plan": "starter",
        })
        assert result["limits"] is None
        assert "no rate limits" in result["note"].lower()

    def test_unknown_feature(self):
        from tools.feature_tools import check_feature_limits
        result = check_feature_limits.invoke({
            "feature_name": "warp_drive",
            "plan": "pro",
        })
        assert "error" in result


# ---------- contract_tools ----------

class TestLookupContract:
    def test_valid_contract(self):
        from tools.contract_tools import lookup_contract
        result = lookup_contract.invoke({"contract_id": "CONTRACT-003"})
        assert result["contract_id"] == "CONTRACT-003"
        assert result["plan"] == "enterprise"
        assert result["customer_id"] == "CUST-003"

    def test_invalid_contract(self):
        from tools.contract_tools import lookup_contract
        result = lookup_contract.invoke({"contract_id": "CONTRACT-999"})
        assert "error" in result


class TestGetContractTerms:
    def test_valid_contract(self):
        from tools.contract_tools import get_contract_terms
        result = get_contract_terms.invoke({"contract_id": "CONTRACT-003"})
        assert result["contract_id"] == "CONTRACT-003"
        assert "sla" in result
        assert result["sla"]["response_time_hours"] == 24

    def test_invalid_contract(self):
        from tools.contract_tools import get_contract_terms
        result = get_contract_terms.invoke({"contract_id": "CONTRACT-999"})
        assert "error" in result


class TestValidateSlaCompliance:
    def test_sla_violation(self):
        """CONTRACT-003 has 24h response SLA. A 10-day-old issue should breach it."""
        from tools.contract_tools import validate_sla_compliance
        # 10 days before the hardcoded "now" of 2026-03-22T12:00:00
        result = validate_sla_compliance.invoke({
            "contract_id": "CONTRACT-003",
            "issue_date": "2026-03-12T12:00:00",
        })
        assert result["response_sla_breached"] is True
        assert result["resolution_sla_breached"] is True
        assert result["elapsed_hours"] == 240.0
        # Should flag the penalty clause from special_terms
        assert "applicable_penalties" in result
        assert any("credit" in p.lower() for p in result["applicable_penalties"])

    def test_sla_not_violated(self):
        """An issue filed 1 hour ago should not breach a 24h SLA."""
        from tools.contract_tools import validate_sla_compliance
        result = validate_sla_compliance.invoke({
            "contract_id": "CONTRACT-003",
            "issue_date": "2026-03-22T11:00:00",
        })
        assert result["response_sla_breached"] is False
        assert result["resolution_sla_breached"] is False

    def test_invalid_contract(self):
        from tools.contract_tools import validate_sla_compliance
        result = validate_sla_compliance.invoke({
            "contract_id": "CONTRACT-999",
            "issue_date": "2026-03-12T12:00:00",
        })
        assert "error" in result

    def test_bad_date_format(self):
        from tools.contract_tools import validate_sla_compliance
        result = validate_sla_compliance.invoke({
            "contract_id": "CONTRACT-003",
            "issue_date": "not-a-date",
        })
        assert "error" in result


class TestGetIncludedFeatures:
    def test_valid_contract(self):
        from tools.contract_tools import get_included_features
        result = get_included_features.invoke({"contract_id": "CONTRACT-003"})
        assert isinstance(result, list)
        assert "dashboard" in result
        assert "custom_integrations" in result

    def test_invalid_contract(self):
        from tools.contract_tools import get_included_features
        result = get_included_features.invoke({"contract_id": "CONTRACT-999"})
        assert isinstance(result, list)
        assert "error" in result[0]


# ---------- escalation_tools ----------

class TestCreateEscalationTicket:
    def test_ticket_creation(self):
        from tools.escalation_tools import create_escalation_ticket
        result = create_escalation_ticket.invoke({
            "reason": "SLA breach detected",
            "priority": "critical",
            "context": "Customer CUST-003 waiting 10 days",
        })
        assert "ticket_id" in result
        assert result["ticket_id"].startswith("ESC-")
        assert result["status"] == "created"
        assert result["priority"] == "critical"

    def test_ticket_stored_in_memory(self):
        from tools.escalation_tools import create_escalation_ticket
        from mock_data.escalations import ESCALATION_TICKETS

        result = create_escalation_ticket.invoke({
            "reason": "test storage",
            "priority": "low",
            "context": "just testing",
        })
        ticket_id = result["ticket_id"]
        assert ticket_id in ESCALATION_TICKETS
        assert ESCALATION_TICKETS[ticket_id]["reason"] == "test storage"


class TestGetEscalationRouting:
    def test_valid_issue_type(self):
        from tools.escalation_tools import get_escalation_routing
        result = get_escalation_routing.invoke({"issue_type": "sla_violation"})
        assert result["team"] == "customer_success"
        assert result["default_priority"] == "critical"

    def test_unknown_issue_type(self):
        from tools.escalation_tools import get_escalation_routing
        result = get_escalation_routing.invoke({"issue_type": "alien_invasion"})
        assert "error" in result
        assert "available_types" in result


class TestNotifySupportTeam:
    def test_notify_existing_ticket(self):
        from tools.escalation_tools import create_escalation_ticket, notify_support_team

        ticket = create_escalation_ticket.invoke({
            "reason": "notify test",
            "priority": "high",
            "context": "testing notifications",
        })
        result = notify_support_team.invoke({"ticket_id": ticket["ticket_id"]})
        assert result["notification_status"] == "delivered"
        assert "slack" in result["channels"]

    def test_notify_missing_ticket(self):
        from tools.escalation_tools import notify_support_team
        result = notify_support_team.invoke({"ticket_id": "ESC-NONEXISTENT"})
        assert "error" in result


class TestLogEscalationReason:
    def test_log_to_existing_ticket(self):
        from tools.escalation_tools import create_escalation_ticket, log_escalation_reason

        ticket = create_escalation_ticket.invoke({
            "reason": "log test",
            "priority": "medium",
            "context": "testing log append",
        })
        result = log_escalation_reason.invoke({
            "ticket_id": ticket["ticket_id"],
            "reason": "Additional context: customer is enterprise tier",
        })
        assert result["status"] == "reason_logged"
        assert result["total_log_entries"] == 2  # creation + the one we just added

    def test_log_to_missing_ticket(self):
        from tools.escalation_tools import log_escalation_reason
        result = log_escalation_reason.invoke({
            "ticket_id": "ESC-NONEXISTENT",
            "reason": "this should fail",
        })
        assert "error" in result
