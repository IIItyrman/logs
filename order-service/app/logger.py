"""
Структурированный JSON-логгер для микросервисов.

Формат лога:
{
  "timestamp": "2026-06-18T10:00:00.000Z",
  "level": "INFO",
  "service": "order-service",
  "trace_id": "abc-123",
  "message": "...",
  ...дополнительные поля
}
"""

import json
import logging
import sys
import os
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    """Форматтер, выводящий логи в JSON одной строкой (удобно для Loki)."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "level": record.levelname,
            "service": os.getenv("SERVICE_NAME", "unknown"),
            "message": record.getMessage(),
        }

        # trace_id — для отслеживания цепочки вызовов между сервисами
        trace_id = getattr(record, "trace_id", None)
        if trace_id:
            log_entry["trace_id"] = trace_id

        # Дополнительные поля из extra
        for key in ("method", "path", "status_code", "duration_ms", "error"):
            val = getattr(record, key, None)
            if val is not None:
                log_entry[key] = val

        return json.dumps(log_entry, ensure_ascii=False)


def setup_logger() -> logging.Logger:
    """Создаёт и настраивает JSON-логгер, пишущий в stdout."""
    logger = logging.getLogger("app")
    logger.setLevel(logging.DEBUG)

    # Не дублируем хендлеры при пересоздании
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)

    return logger


# Глобальный логгер для импорта
logger = setup_logger()