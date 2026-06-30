import uuid
import time
import random
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from .logger import logger, trace_id_ctx

app = FastAPI(title="Order Service")

class OrderRequest(BaseModel):
    user_id: int
    item: str
    quantity: int = 1

# Dummy in-memory DB
orders_db = {}

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    # Retrieve trace_id from headers if present
    trace_id = request.headers.get("X-Trace-Id", str(uuid.uuid4()))
    trace_id_ctx.set(trace_id)

    start_time = time.time()

    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as e:
        status_code = 500
        logger.error(f"Internal server error: {e}", extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": status_code,
            "env": "dev"
        })
        raise
    finally:
        duration_ms = round((time.time() - start_time) * 1000, 2)
        logger.info(f"Handled request {request.method} {request.url.path}", extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "env": "dev"
        })

    return response

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "order-service"}

@app.post("/orders")
def create_order(order: OrderRequest):
    # Simulate a 10% failure rate
    if random.random() < 0.1:
        logger.error("Simulated internal error occurred during order creation", extra={
            "method": "POST",
            "path": "/orders",
            "status_code": 500,
            "env": "dev"
        })
        raise HTTPException(status_code=500, detail="Simulated Internal Server Error")

    order_id = str(uuid.uuid4())
    orders_db[order_id] = {
        "order_id": order_id,
        "user_id": order.user_id,
        "item": order.item,
        "quantity": order.quantity,
        "status": "created"
    }

    logger.info(f"Order {order_id} created successfully", extra={
        "method": "POST",
        "path": "/orders",
        "env": "dev"
    })

    return orders_db[order_id]

@app.get("/orders/{order_id}")
def get_order(order_id: str):
    if order_id not in orders_db:
        logger.warning(f"Order {order_id} not found", extra={
            "method": "GET",
            "path": f"/orders/{order_id}",
            "status_code": 404,
            "env": "dev"
        })
        raise HTTPException(status_code=404, detail="Order not found")

    return orders_db[order_id]
