"""Contract tools — lookup, SLA terms, compliance checks."""
import time
import random
import logging
from datetime import datetime

from langchain_core.tools import tool
from tools.tool_base import ToolExecutionError

logger = logging.getLogger("macsis.tools.contract")


def _simulate(tool_name, latency_range=(0.1, 0.5), failure_rate=0.05):
    delay = random.uniform(*latency_range)
    time.sleep(delay)
    if random.random() < failure_rate:
        logger.warning(f"[{tool_name}] simulated timeout after {delay:.2f}s")
        raise ToolExecutionError(f"{tool_name}: simulated timeout")


@tool
def lookup_contract(contract_id: str) -> dict:
    """Look up a service contract by its ID. Returns full contract details including SLA and pricing."""
    _simulate("lookup_contract")
    from mock_data.contracts import CONTRACTS

    contract = CONTRACTS.get(contract_id)
    if not contract:
        return {"error": f"Contract {contract_id} not found"}
    return contract


@tool
def get_contract_terms(contract_id: str) -> dict:
    """Get the SLA terms and special conditions for a contract."""
    _simulate("get_contract_terms")
    from mock_data.contracts import CONTRACTS

    contract = CONTRACTS.get(contract_id)
    if not contract:
        return {"error": f"Contract {contract_id} not found"}

    return {
        "contract_id": contract_id,
        "plan": contract["plan"],
        "sla": contract["sla"],
        "special_terms": contract["special_terms"],
        "start_date": contract["start_date"],
        "end_date": contract["end_date"],
        "auto_renew": contract["auto_renew"],
    }


@tool
def validate_sla_compliance(contract_id: str, issue_date: str) -> dict:
    """Check whether SLA targets have been met for a given issue. Compares elapsed time against contracted response and resolution windows."""
    _simulate("validate_sla_compliance")
    from mock_data.contracts import CONTRACTS

    contract = CONTRACTS.get(contract_id)
    if not contract:
        return {"error": f"Contract {contract_id} not found"}

    sla = contract["sla"]

    try:
        issue_dt = datetime.fromisoformat(issue_date)
    except ValueError:
        return {"error": f"Invalid date format: '{issue_date}'. Use ISO format (YYYY-MM-DDTHH:MM:SS)."}

    # how long since the issue was filed
    now = datetime(2026, 3, 22, 12, 0, 0)
    elapsed = now - issue_dt
    elapsed_hours = elapsed.total_seconds() / 3600

    response_limit = sla["response_time_hours"]
    resolution_limit = sla["resolution_time_hours"]

    response_breached = elapsed_hours > response_limit
    resolution_breached = elapsed_hours > resolution_limit

    result = {
        "contract_id": contract_id,
        "issue_date": issue_date,
        "current_date": now.isoformat(),
        "elapsed_hours": round(elapsed_hours, 1),
        "sla_response_time_hours": response_limit,
        "sla_resolution_time_hours": resolution_limit,
        "response_sla_breached": response_breached,
        "resolution_sla_breached": resolution_breached,
    }

    if resolution_breached and contract["special_terms"]:
        # check for penalty clauses
        penalties = [t for t in contract["special_terms"] if "penalty" in t.lower() or "credit" in t.lower()]
        if penalties:
            result["applicable_penalties"] = penalties

    return result


@tool
def get_included_features(contract_id: str) -> list:
    """List all features included in a service contract."""
    _simulate("get_included_features")
    from mock_data.contracts import CONTRACTS

    contract = CONTRACTS.get(contract_id)
    if not contract:
        return [{"error": f"Contract {contract_id} not found"}]
    return contract["included_features"]


contract_tools = [lookup_contract, get_contract_terms, validate_sla_compliance, get_included_features]
