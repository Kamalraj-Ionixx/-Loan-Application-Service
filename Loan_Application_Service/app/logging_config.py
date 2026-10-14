import logging
import os


class DefaultExtrasFilter(logging.Filter):
    def filter(self, record):
        if not hasattr(record, "request_id"):
            record.request_id = "-"
        if not hasattr(record, "user_id"):
            record.user_id = "anonymous"
        if not hasattr(record, "status_code"):
            record.status_code = 0
        if not hasattr(record, "duration_ms"):
            record.duration_ms = 0
        if not hasattr(record, "client_ip"):
            record.client_ip = "-"
        return True


LOG_FORMAT = (
    '{"timestamp":"%(asctime)s",'
    '"level":"%(levelname)s",'
    '"request_id":"%(request_id)s",'
    '"user_id":"%(user_id)s",'
    '"status_code":%(status_code)s,'
    '"duration_ms":%(duration_ms)s,'
    '"client_ip":"%(client_ip)s",'
    '"message":"%(message)s"}'
)


def configure_logging() -> None:
    """Configure application logging."""
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    formatter = logging.Formatter(LOG_FORMAT, datefmt="%Y-%m-%dT%H:%M:%S")
    extras_filter = DefaultExtrasFilter()

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.addFilter(extras_filter)

    app_logger = logging.getLogger("loan-api")
    app_logger.setLevel(level)
    app_logger.handlers.clear()
    app_logger.addHandler(handler)
    app_logger.propagate = False


logger = logging.getLogger("loan-api")
