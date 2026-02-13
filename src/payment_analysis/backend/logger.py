"""Application logger.

Logging configuration is handled by APX via uvicorn's log config.
This module exposes the default app logger.
"""

import logging

try:
    from .._metadata import app_name
except ImportError:
    app_name = "payment-analysis"

logger: logging.Logger = logging.getLogger(app_name)
