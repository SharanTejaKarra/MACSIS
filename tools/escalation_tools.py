"""Escalation tools — ticket creation, routing, notifications. In-memory storage."""
import time
import random
import logging
import uuid
from datetime import datetime

from langchain_core.tools import tool
from tools.tool_base import ToolExecutionError

logger = logging.getLogger("macsis.tools.escalation")


def _simulate(tool_name, latency_range=(0.1, 0.5), failure_rate=0.05):
    delay = random.uniform(*latency_range)
    time.sleep(delay)
    if random.random() < failure_rate:
        logger.warning(f"[{tool_name}] simulated timeout after {delay:.2f}s")
        raise ToolExecutionError(f"{tool_name}: simulated timeout")


def _generate_ticket_id() -> str:
    short_id = uuid.uuid4().hex[:8].upper()
    return f"ESC-{short_id}"


@tool
def create_escalation_ticket(reason: str, priority: str, context: str) -> dict:
    """Create a new escalation ticket. Returns the ticket ID and status. Priority should be one of: low, medium, high, critical."""
    _simulate("create_escalation_ticket")
    from mock_data.escalations import ESCALATION_TICKETS

    ticket_id = _generate_ticket_id()
    now = datetime(2026, 3, 22, 12, 0, 0).isoformat()

    ticket = {
        "ticket_id": ticket_id,
        "reason": reason,
        "priority": priority,
        "context": context,
        "status": "open",
        "created_at": now,
        "escalation_log": [
            {"timestamp": now, "action": "ticket_created", "details": reason}
        ],
        "notifications_sent": [],
    }

    ESCALATION_TICKETS[ticket_id] = ticket
    logger.info(f"Created escalation ticket {ticket_id} (priority={priority})")

    return {
        "ticket_id": ticket_id,
        "status": "created",
        "priority": priority,
        "created_at": now,
    }


@tool
def get_escalation_routing(issue_type: str) -> dict:
    """Get the routing rules for an issue type — which team handles it and the default priority."""
    _simulate("get_escalation_routing")
    from mock_data.escalations import ROUTING_RULES

    rule = ROUTING_RULES.get(issue_type)
    if not rule:
        available = list(ROUTING_RULES.keys())
        return {
            "error": f"No routing rule for issue type '{issue_type}'",
            "available_types": available,
        }

    return {"issue_type": issue_type, **rule}


@tool
def notify_support_team(ticket_id: str) -> dict:
    """Send a notification to the assigned support team for an escalation ticket."""
    _simulate("notify_support_team", latency_range=(0.2, 0.8))
    from mock_data.escalations import ESCALATION_TICKETS

    ticket = ESCALATION_TICKETS.get(ticket_id)
    if not ticket:
        return {"error": f"Ticket {ticket_id} not found"}

    now = datetime(2026, 3, 22, 12, 0, 0).isoformat()
    notification = {
        "timestamp": now,
        "channel": "slack + email",
        "status": "delivered",
    }
    ticket["notifications_sent"].append(notification)
    ticket["escalation_log"].append({
        "timestamp": now,
        "action": "team_notified",
        "details": "Notification sent via Slack and email",
    })

    logger.info(f"Notified support team for ticket {ticket_id}")
    return {
        "ticket_id": ticket_id,
        "notification_status": "delivered",
        "channels": ["slack", "email"],
    }


@tool
def log_escalation_reason(ticket_id: str, reason: str) -> dict:
    """Append an additional reason or note to an existing escalation ticket's log."""
    _simulate("log_escalation_reason")
    from mock_data.escalations import ESCALATION_TICKETS

    ticket = ESCALATION_TICKETS.get(ticket_id)
    if not ticket:
        return {"error": f"Ticket {ticket_id} not found"}

    now = datetime(2026, 3, 22, 12, 0, 0).isoformat()
    ticket["escalation_log"].append({
        "timestamp": now,
        "action": "reason_logged",
        "details": reason,
    })

    logger.info(f"Logged additional reason on ticket {ticket_id}")
    return {
        "ticket_id": ticket_id,
        "status": "reason_logged",
        "total_log_entries": len(ticket["escalation_log"]),
    }


escalation_tools = [create_escalation_ticket, get_escalation_routing, notify_support_team, log_escalation_reason]
