import time
import logging
import functools
from monitoring.langfuse_config import get_langfuse, is_langfuse_available

logger = logging.getLogger("macsis.tracing")


def trace_agent(agent_name: str):
    """Decorator — logs timing + creates Langfuse spans for agent nodes."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(state, *args, **kwargs):
            start = time.time()
            scenario_id = state.get("scenario_id", "unknown")

            trace = None
            span = None
            if is_langfuse_available():
                langfuse = get_langfuse()
                trace = langfuse.trace(
                    name=f"agent:{agent_name}",
                    metadata={"scenario_id": scenario_id},
                )
                span = trace.span(
                    name=f"{agent_name}.run",
                    metadata={"scenario_id": scenario_id},
                )

            logger.info(f"[{agent_name}] starting (scenario={scenario_id})")

            try:
                result = func(state, *args, **kwargs)
                elapsed = time.time() - start
                logger.info(f"[{agent_name}] completed in {elapsed:.2f}s")

                if span:
                    span.end(metadata={"duration_s": round(elapsed, 3), "status": "ok"})

                return result
            except Exception as e:
                elapsed = time.time() - start
                logger.error(f"[{agent_name}] failed after {elapsed:.2f}s: {e}")

                if span:
                    span.end(metadata={"duration_s": round(elapsed, 3), "status": "error", "error": str(e)})

                raise

        return wrapper
    return decorator


def trace_tool(tool_name: str):
    """Same as trace_agent but for tool calls."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()

            span = None
            if is_langfuse_available():
                langfuse = get_langfuse()
                trace = langfuse.trace(name=f"tool:{tool_name}")
                span = trace.span(name=f"{tool_name}.call")

            logger.info(f"[tool:{tool_name}] invoked")

            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start
                logger.info(f"[tool:{tool_name}] done in {elapsed:.2f}s")

                if span:
                    span.end(metadata={"duration_s": round(elapsed, 3), "status": "ok"})

                return result
            except Exception as e:
                elapsed = time.time() - start
                logger.error(f"[tool:{tool_name}] failed after {elapsed:.2f}s: {e}")

                if span:
                    span.end(metadata={"duration_s": round(elapsed, 3), "status": "error", "error": str(e)})

                raise

        return wrapper
    return decorator


def trace_decision(decision_name: str, reasoning: str, metadata: dict = None):
    """Log a routing/classification decision (not a decorator)."""
    extra = f" | {metadata}" if metadata else ""
    logger.info(f"[DECISION] {decision_name}: {reasoning}{extra}")

    if is_langfuse_available():
        langfuse = get_langfuse()
        trace = langfuse.trace(
            name=f"decision:{decision_name}",
            metadata={
                "reasoning": reasoning,
                **(metadata or {}),
            },
        )
        # also record as a trace event
        trace.event(
            name=decision_name,
            metadata={"reasoning": reasoning, **(metadata or {})},
        )
