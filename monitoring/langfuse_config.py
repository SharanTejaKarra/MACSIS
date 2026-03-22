import os
import logging

logger = logging.getLogger("macsis.monitoring")

_langfuse_client = None
_langfuse_available = False
_callback_handler = None


def init_langfuse():
    """Best-effort Langfuse init — falls back to console logging."""
    global _langfuse_client, _langfuse_available, _callback_handler

    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

    if not public_key or not secret_key:
        logger.warning("Langfuse keys not configured - tracing will use console logging")
        return

    try:
        from langfuse import Langfuse
        from langfuse.callback import CallbackHandler

        _langfuse_client = Langfuse(
            public_key=public_key, secret_key=secret_key, host=host
        )
        _callback_handler = CallbackHandler(
            public_key=public_key, secret_key=secret_key, host=host
        )
        _langfuse_available = True
        logger.info("Langfuse connected")
    except Exception as e:
        logger.warning(f"Langfuse init failed: {e} - falling back to console")
        _langfuse_available = False


def get_langfuse():
    return _langfuse_client if _langfuse_available else None


def get_callback_handler():
    return _callback_handler if _langfuse_available else None


def is_langfuse_available() -> bool:
    return _langfuse_available


def flush():
    """Flush buffered traces. No-op if Langfuse isn't active."""
    if _langfuse_available and _langfuse_client:
        _langfuse_client.flush()
