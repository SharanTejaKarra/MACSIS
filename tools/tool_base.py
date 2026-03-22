"""Mock tool decorator — adds fake latency, random failures, and logging."""
import time
import random
import logging
import functools

logger = logging.getLogger("macsis.tools")


class ToolExecutionError(Exception):
    """Raised when a mock tool hits a simulated failure."""
    pass


def mock_tool(latency_range=(0.1, 0.5), failure_rate=0.05, name=None):
    """Wraps a function with simulated latency, random failures, and logging."""
    def decorator(func):
        tool_name = name or func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()

            # fake network delay
            delay = random.uniform(*latency_range)
            time.sleep(delay)

            # random failure
            if random.random() < failure_rate:
                logger.warning(f"[{tool_name}] simulated failure after {delay:.2f}s")
                raise ToolExecutionError(
                    f"{tool_name} failed: simulated timeout/network error"
                )

            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start
                logger.info(
                    f"[{tool_name}] completed in {elapsed:.2f}s | "
                    f"args={args} kwargs={kwargs}"
                )
                return result
            except ToolExecutionError:
                raise
            except Exception as e:
                logger.error(f"[{tool_name}] unexpected error: {e}")
                raise ToolExecutionError(f"{tool_name} error: {e}") from e

        # expose name for monitoring
        wrapper.tool_name = tool_name
        return wrapper

    return decorator
