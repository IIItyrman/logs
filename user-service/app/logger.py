import logging
import json
from datetime import datetime
from typing import Any, Dict
from contextvars import ContextVar

# Context variable to hold trace_id
trace_id_ctx: ContextVar[str] = ContextVar("trace_id", default="")

class JSONFormatter(logging.Formatter):
    def __init__(self, service_name: str):
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "service": self.service_name,
            "message": record.getMessage(),
            "trace_id": trace_id_ctx.get(),
        }

        if hasattr(record, "method"):
            log_obj["method"] = record.method
        if hasattr(record, "path"):
            log_obj["path"] = record.path
        if hasattr(record, "status_code"):
            log_obj["status_code"] = record.status_code
        if hasattr(record, "duration_ms"):
            log_obj["duration_ms"] = record.duration_ms
        if hasattr(record, "env"):
            log_obj["env"] = getattr(record, "env")

        return json.dumps(log_obj)

def setup_logger(service_name: str) -> logging.Logger:
    logger = logging.getLogger(service_name)
    logger.setLevel(logging.INFO)

    # Remove existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()

    handler = logging.StreamHandler()
    formatter = JSONFormatter(service_name)
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger

logger = setup_logger("user-service")
