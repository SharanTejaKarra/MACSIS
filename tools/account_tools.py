"""Account lookup tools — customer profiles, billing, features."""
import time
import random
import logging

from langchain_core.tools import tool
from tools.tool_base import ToolExecutionError

logger = logging.getLogger("macsis.tools.account")


def _simulate(tool_name, latency_range=(0.1, 0.5), failure_rate=0.05):
    delay = random.uniform(*latency_range)
    time.sleep(delay)
    if random.random() < failure_rate:
        logger.warning(f"[{tool_name}] simulated timeout after {delay:.2f}s")
        raise ToolExecutionError(f"{tool_name}: simulated timeout")


@tool
def lookup_customer(customer_id: str) -> dict:
    """Look up a customer's profile by their ID. Returns account details, plan info, and status."""
    _simulate("lookup_customer")
    from mock_data.customers import CUSTOMERS

    customer = CUSTOMERS.get(customer_id)
    if not customer:
        return {"error": f"Customer {customer_id} not found"}
    return customer


@tool
def get_billing_history(customer_id: str) -> list:
    """Retrieve the billing history for a customer. Returns a list of past invoices with dates and amounts."""
    _simulate("get_billing_history")
    from mock_data.customers import CUSTOMERS

    customer = CUSTOMERS.get(customer_id)
    if not customer:
        return [{"error": f"Customer {customer_id} not found"}]
    return customer["billing_history"]


@tool
def check_account_status(customer_id: str) -> dict:
    """Check a customer's current account status including plan, seat usage, and contract info."""
    _simulate("check_account_status")
    from mock_data.customers import CUSTOMERS

    customer = CUSTOMERS.get(customer_id)
    if not customer:
        return {"error": f"Customer {customer_id} not found"}

    return {
        "customer_id": customer["customer_id"],
        "account_status": customer["account_status"],
        "plan": customer["plan"],
        "seats_purchased": customer["seats_purchased"],
        "seats_used": customer["seats_used"],
        "seats_available": customer["seats_purchased"] - customer["seats_used"],
        "contract_id": customer["contract_id"],
    }


@tool
def list_enabled_features(customer_id: str) -> list:
    """List all features currently enabled on a customer's account."""
    _simulate("list_enabled_features")
    from mock_data.customers import CUSTOMERS

    customer = CUSTOMERS.get(customer_id)
    if not customer:
        return [{"error": f"Customer {customer_id} not found"}]
    return customer["features_enabled"]


account_tools = [lookup_customer, get_billing_history, check_account_status, list_enabled_features]
