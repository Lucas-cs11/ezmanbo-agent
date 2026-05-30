"""Minimal logging utility — emits warnings for swallowed exceptions during debugging."""

import os
import logging
import traceback

_DEBUG = os.getenv("EZPLM_DEBUG", "").strip().lower() in ("1", "true", "yes")

logging.basicConfig(
    level=logging.DEBUG if _DEBUG else logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
_logger = logging.getLogger("ezplm")


def warn_swallow(module: str, exc: Exception, context: str = ""):
    """Log a warning when an exception is intentionally swallowed."""
    ctx = f" ({context})" if context else ""
    _logger.warning(f"[{module}]{ctx} Swallowed exception: {exc}")
    if _DEBUG:
        traceback.print_exc()
