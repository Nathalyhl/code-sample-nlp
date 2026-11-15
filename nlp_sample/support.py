"""Review-only logging adapter; this is not the original production utility module."""
import logging

logger = logging.getLogger("thesis_source_review")
logger.addHandler(logging.NullHandler())
logger.propagate = False


def log_message(message, level="INFO"):
    logger.log(getattr(logging, level, logging.INFO), message)


def handle_error(message, error):
    logger.error("%s (%s)", message, type(error).__name__)
