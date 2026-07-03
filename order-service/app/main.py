"""
order-service — сервис управления заказами.

Предоставляет эндпоинты:
- POST /orders               — создать заказ (вызывается из user-service)
- GET  /orders/{order_id}    — получить статус заказа
- GET  /health               — проверка здоровья сервиса
"""

import uuid
import time
import random
from typing import Optional

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel

from logger import logger


class CreateOrderRequest(BaseModel):
    user_id: str = "unknown"
    item: str = "default-item"
    quantity: int = 1

app = FastAPI(title="order-service")

# Имитация хранилища заказов
_ORDERS: dict = {}


@app.get("/health")
async def health():
    logger.info("health check OK")
    return {"status": "ok", "service": "order-service"}


@app.post("/orders")
async def create_order(
    body: CreateOrderRequest,
    x_trace_id: Optional[str] = Header(None, alias="X-Trace-Id"),
):
    """Создаёт заказ. Принимает trace_id из заголовка от user-service."""
    trace_id = x_trace_id or str(uuid.uuid4())
    start = time.time()

    logger.info(
        "Получен запрос на создание заказа",
        extra={
            "trace_id": trace_id,
            "method": "POST",
            "path": "/orders",
        },
    )

    # Имитация бизнес-логики: иногда заказы падают с ошибкой
    if random.random() < 0.1:  # 10% шанс ошибки
        duration = (time.time() - start) * 1000
        logger.error(
            "Ошибка при обработке заказа: товар не найден на складе",
            extra={
                "trace_id": trace_id,
                "method": "POST",
                "path": "/orders",
                "status_code": 500,
                "duration_ms": round(duration, 2),
                "error": f"Item '{body.item}' out of stock",
            },
        )
        raise HTTPException(status_code=500, detail="Item out of stock")

    # Имитация задержки обработки
    await _simulate_processing(trace_id, body.item, body.quantity)

    order_id = str(uuid.uuid4())
    order = {
        "order_id": order_id,
        "user_id": body.user_id,
        "item": body.item,
        "quantity": body.quantity,
        "status": "confirmed",
    }
    _ORDERS[order_id] = order

    duration = (time.time() - start) * 1000
    logger.info(
        "Заказ успешно создан",
        extra={
            "trace_id": trace_id,
            "method": "POST",
            "path": "/orders",
            "status_code": 201,
            "duration_ms": round(duration, 2),
        },
    )

    return {"order": order, "trace_id": trace_id}


@app.get("/orders/{order_id}")
async def get_order(order_id: str):
    trace_id = str(uuid.uuid4())
    start = time.time()

    logger.info(
        "Запрос статуса заказа",
        extra={
            "trace_id": trace_id,
            "method": "GET",
            "path": f"/orders/{order_id}",
        },
    )

    order = _ORDERS.get(order_id)
    if not order:
        duration = (time.time() - start) * 1000
        logger.warning(
            "Заказ не найден",
            extra={
                "trace_id": trace_id,
                "method": "GET",
                "path": f"/orders/{order_id}",
                "status_code": 404,
                "duration_ms": round(duration, 2),
            },
        )
        raise HTTPException(status_code=404, detail="Order not found")

    duration = (time.time() - start) * 1000
    logger.info(
        "Заказ найден",
        extra={
            "trace_id": trace_id,
            "method": "GET",
            "path": f"/orders/{order_id}",
            "status_code": 200,
            "duration_ms": round(duration, 2),
        },
    )

    return {"order": order, "trace_id": trace_id}


async def _simulate_processing(trace_id: str, item: str, quantity: int):
    """Имитирует задержку обработки заказа (50–200ms)."""
    delay = random.uniform(0.05, 0.2)
    time.sleep(delay)
    logger.debug(
        "Обработка позиции заказа завершена",
        extra={"trace_id": trace_id},
    )