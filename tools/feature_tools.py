"""Feature tools — availability, limits, docs, config validation."""
import time
import random
import logging

from langchain_core.tools import tool
from tools.tool_base import ToolExecutionError

logger = logging.getLogger("macsis.tools.feature")


def _simulate(tool_name, latency_range=(0.1, 0.5), failure_rate=0.05):
    delay = random.uniform(*latency_range)
    time.sleep(delay)
    if random.random() < failure_rate:
        logger.warning(f"[{tool_name}] simulated timeout after {delay:.2f}s")
        raise ToolExecutionError(f"{tool_name}: simulated timeout")


@tool
def get_feature_matrix() -> dict:
    """Get the full feature availability matrix showing which features are available on each plan."""
    _simulate("get_feature_matrix")
    from mock_data.features import FEATURE_MATRIX
    return FEATURE_MATRIX


@tool
def get_feature_documentation(feature_name: str) -> dict:
    """Get documentation for a specific feature including description, setup instructions, and known issues."""
    _simulate("get_feature_documentation")
    from mock_data.features import FEATURE_DOCUMENTATION

    doc = FEATURE_DOCUMENTATION.get(feature_name)
    if not doc:
        return {"error": f"No documentation found for feature '{feature_name}'"}
    return {"feature": feature_name, **doc}


@tool
def validate_configuration(feature_name: str, customer_id: str) -> dict:
    """Check if a feature is available and properly configured for a specific customer."""
    _simulate("validate_configuration")
    from mock_data.features import FEATURE_MATRIX
    from mock_data.customers import CUSTOMERS

    customer = CUSTOMERS.get(customer_id)
    if not customer:
        return {"error": f"Customer {customer_id} not found"}

    plan = customer["plan"]
    feature_plans = FEATURE_MATRIX.get(feature_name)
    if not feature_plans:
        return {"error": f"Unknown feature '{feature_name}'"}

    plan_eligible = feature_plans.get(plan, False)
    actually_enabled = feature_name in customer["features_enabled"]

    return {
        "feature": feature_name,
        "customer_id": customer_id,
        "plan": plan,
        "plan_eligible": plan_eligible,
        "currently_enabled": actually_enabled,
        "status": "active" if (plan_eligible and actually_enabled) else
                  "eligible_not_enabled" if (plan_eligible and not actually_enabled) else
                  "not_available_on_plan",
    }


@tool
def check_feature_limits(feature_name: str, plan: str) -> dict:
    """Check the rate limits and usage caps for a feature on a specific plan."""
    _simulate("check_feature_limits")
    from mock_data.features import FEATURE_LIMITS, FEATURE_MATRIX

    # make sure the feature exists at all
    if feature_name not in FEATURE_MATRIX:
        return {"error": f"Unknown feature '{feature_name}'"}

    limits = FEATURE_LIMITS.get(feature_name)
    if not limits:
        return {
            "feature": feature_name,
            "plan": plan,
            "limits": None,
            "note": "This feature has no rate limits or caps.",
        }

    plan_limits = limits.get(plan)
    if plan_limits is None:
        return {
            "feature": feature_name,
            "plan": plan,
            "limits": None,
            "note": f"Feature '{feature_name}' is not available on the {plan} plan.",
        }

    return {
        "feature": feature_name,
        "plan": plan,
        "limits": plan_limits,
    }


feature_tools = [get_feature_matrix, get_feature_documentation, validate_configuration, check_feature_limits]
