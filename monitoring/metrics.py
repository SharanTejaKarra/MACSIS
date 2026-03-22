import logging
from monitoring.langfuse_config import get_langfuse, is_langfuse_available

logger = logging.getLogger("macsis.metrics")


def log_escalation_event(reason: str, severity: str, ticket_id: str = None):
    """Log an escalation event."""
    ticket_info = f" (ticket={ticket_id})" if ticket_id else ""
    logger.info(f"[ESCALATION] severity={severity} reason={reason}{ticket_info}")

    if is_langfuse_available():
        langfuse = get_langfuse()
        trace = langfuse.trace(name="escalation")
        trace.event(
            name="escalation_triggered",
            metadata={
                "reason": reason,
                "severity": severity,
                "ticket_id": ticket_id,
            },
        )


def log_conflict_detected(agents_involved: list[str], description: str):
    """Log a conflict between agents."""
    agents_str = ", ".join(agents_involved)
    logger.warning(f"[CONFLICT] between [{agents_str}]: {description}")

    if is_langfuse_available():
        langfuse = get_langfuse()
        trace = langfuse.trace(name="conflict_detection")
        trace.event(
            name="conflict_detected",
            metadata={
                "agents_involved": agents_involved,
                "description": description,
            },
        )


def log_scenario_complete(scenario_id: str, duration_seconds: float, token_summary: dict):
    """Log a completed scenario run."""
    logger.info(
        f"[SCENARIO COMPLETE] {scenario_id} "
        f"duration={duration_seconds:.2f}s "
        f"tokens={token_summary.get('total_tokens', '?')}"
    )

    if is_langfuse_available():
        langfuse = get_langfuse()
        trace = langfuse.trace(
            name="scenario_complete",
            metadata={
                "scenario_id": scenario_id,
                "duration_seconds": round(duration_seconds, 3),
                "token_summary": token_summary,
            },
        )
        # scores show up in Langfuse analytics
        trace.score(name="duration_seconds", value=duration_seconds)
        if "total_tokens" in token_summary:
            trace.score(name="total_tokens", value=token_summary["total_tokens"])


def log_tool_failure(tool_name: str, error: str, agent_name: str):
    """Log a failed tool call."""
    logger.error(f"[TOOL FAILURE] {tool_name} (called by {agent_name}): {error}")

    if is_langfuse_available():
        langfuse = get_langfuse()
        trace = langfuse.trace(name="tool_failure")
        trace.event(
            name="tool_call_failed",
            metadata={
                "tool_name": tool_name,
                "error": error,
                "agent_name": agent_name,
            },
        )
