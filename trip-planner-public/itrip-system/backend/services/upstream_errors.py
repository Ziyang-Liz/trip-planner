"""Public errors and diagnostics that never include upstream URLs or credentials."""

import logging

logger = logging.getLogger(__name__)


class PlacesError(Exception):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code


def log_upstream_error(service: str, error: Exception):
    response = getattr(error, "response", None)
    status = getattr(response, "status_code", None)
    logger.warning("%s failed: type=%s status=%s", service, type(error).__name__, status)
