import uuid
import time
import httpx
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse
from .logger import logger, trace_id_ctx

app = FastAPI(title="User Service")

ORDER_SERVICE_URL = "http://order-service:8002"

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    # Get or generate trace_id
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

    response.headers["X-Trace-Id"] = trace_id
    return response

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "user-service"}

@app.get("/users/{user_id}")
def get_user(user_id: int):
    return {"user_id": user_id, "name": f"User {user_id}", "email": f"user{user_id}@example.com"}

@app.post("/users/{user_id}/order")
async def create_user_order(user_id: int, item: str, quantity: int = 1):
    trace_id = trace_id_ctx.get()

    logger.info(f"Creating order for user {user_id}", extra={
        "method": "POST",
        "path": f"/users/{user_id}/order",
        "env": "dev"
    })

    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(
                f"{ORDER_SERVICE_URL}/orders",
                json={"user_id": user_id, "item": item, "quantity": quantity},
                headers={"X-Trace-Id": trace_id}
            )
            res.raise_for_status()
            order_data = res.json()
            return {"message": "Order created successfully", "order": order_data}
        except httpx.HTTPStatusError as e:
            logger.error(f"Order service returned error: {e.response.text}", extra={
                "method": "POST",
                "path": f"/users/{user_id}/order",
                "status_code": e.response.status_code,
                "env": "dev"
            })
            raise HTTPException(status_code=502, detail="Order service failed")
        except httpx.RequestError as e:
            logger.error(f"Failed to connect to order service: {str(e)}", extra={
                "method": "POST",
                "path": f"/users/{user_id}/order",
                "status_code": 502,
                "env": "dev"
            })
            raise HTTPException(status_code=502, detail="Order service unavailable")
