"""
user-service — сервис управления пользователями.

Предоставляет эндпоинты:
- GET  /users/{user_id}         — получить профиль пользователя
- POST /users/{user_id}/order   — создать заказ (вызывает order-service)
- GET  /health                  — проверка здоровья сервиса
"""

import uuid
import time
import os

import httpx
from fastapi import FastAPI, HTTPException

from logger import logger

app = FastAPI(title="user-service")

ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://localhost:8002")

# Имитация базы пользователей
_USERS = {
    "1": {"id": "1", "name": "Alice", "email": "alice@example.com"},
    "2": {"id": "2", "name": "Bob", "email": "bob@example.com"},
    "3": {"id": "3", "name": "Charlie", "email": "charlie@example.com"},
}


@app.get("/health")
async def health():
    logger.info("health check OK")
    return {"status": "ok", "service": "user-service"}


@app.get("/users/{user_id}")
async def get_user(user_id: str):
    trace_id = str(uuid.uuid4())
    start = time.time()

    logger.info(
        "Запрос профиля пользователя",
        extra={"trace_id": trace_id, "method": "GET", "path": f"/users/{user_id}"},
    )

    user = _USERS.get(user_id)
    if not user:
        duration = (time.time() - start) * 1000
        logger.warning(
            "Пользователь не найден",
            extra={
                "trace_id": trace_id,
                "method": "GET",
                "path": f"/users/{user_id}",
                "status_code": 404,
                "duration_ms": round(duration, 2),
            },
        )
        raise HTTPException(status_code=404, detail="User not found")

    duration = (time.time() - start) * 1000
    logger.info(
        "Пользователь найден",
        extra={
            "trace_id": trace_id,
            "method": "GET",
            "path": f"/users/{user_id}",
            "status_code": 200,
            "duration_ms": round(duration, 2),
        },
    )

    return {"user": user, "trace_id": trace_id}


@app.post("/users/{user_id}/order")
async def create_order(user_id: str, item: str = "default-item", quantity: int = 1):
    """Создаёт заказ — вызывает order-service с пробросом trace_id."""
    trace_id = str(uuid.uuid4())
    start = time.time()

    logger.info(
        "Запрос на создание заказа",
        extra={
            "trace_id": trace_id,
            "method": "POST",
            "path": f"/users/{user_id}/order",
        },
    )

    if user_id not in _USERS:
        duration = (time.time() - start) * 1000
        logger.warning(
            "Пользователь не найден при создании заказа",
            extra={
                "trace_id": trace_id,
                "method": "POST",
                "path": f"/users/{user_id}/order",
                "status_code": 404,
                "duration_ms": round(duration, 2),
            },
        )
        raise HTTPException(status_code=404, detail="User not found")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            logger.info(
                "Вызов order-service",
                extra={"trace_id": trace_id},
            )
            resp = await client.post(
                f"{ORDER_SERVICE_URL}/orders",
                json={
                    "user_id": user_id,
                    "item": item,
                    "quantity": quantity,
                },
                headers={"X-Trace-Id": trace_id},
            )
            resp.raise_for_status()
            order_data = resp.json()

    except httpx.HTTPError as exc:
        duration = (time.time() - start) * 1000
        logger.error(
            "Ошибка при вызове order-service",
            extra={
                "trace_id": trace_id,
                "method": "POST",
                "path": f"/users/{user_id}/order",
                "status_code": 502,
                "duration_ms": round(duration, 2),
                "error": str(exc),
            },
        )
        raise HTTPException(status_code=502, detail="Order service unavailable")

    duration = (time.time() - start) * 1000
    logger.info(
        "Заказ успешно создан",
        extra={
            "trace_id": trace_id,
            "method": "POST",
            "path": f"/users/{user_id}/order",
            "status_code": 201,
            "duration_ms": round(duration, 2),
        },
    )

    return {
        "user": _USERS[user_id],
        "order": order_data,
        "trace_id": trace_id,
    }