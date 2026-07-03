"""
Непрерывный генератор логов — отправляет запросы к user-service и order-service,
пока не остановят вручную (Ctrl+C). Каждый цикл — 30 запросов с паузой 2 секунды.
"""
import urllib.request
import random
import time
import signal
import sys
import json

USERS = ["1", "2", "3"]
ITEMS = ["laptop", "phone", "book", "monitor", "keyboard", "mouse", "headphones"]
BASE = "http://localhost:8001"

total = 0
oks = 0
fails = 0
running = True


def handle_sigint(sig, frame):
    """Обработчик Ctrl+C — плавное завершение."""
    global running
    running = False
    print("\n\n⏹ Получен сигнал остановки. Завершаю...")


signal.signal(signal.SIGINT, handle_sigint)

print("🔄 Непрерывный генератор логов (Ctrl+C для остановки)")
print("=" * 60)
print()

while running:
    # 1. GET /users/{id} — 5 запросов
    for _ in range(5):
        if not running:
            break
        uid = random.choice(USERS)
        try:
            req = urllib.request.Request(f"{BASE}/users/{uid}", method="GET")
            resp = urllib.request.urlopen(req, timeout=5)
            body = resp.read().decode()
            data = json.loads(body)
            print(f"  [{resp.status}] GET  /users/{uid}  trace_id={data.get('trace_id', 'N/A')[:8]}...")
            oks += 1
        except Exception as e:
            print(f"  [ERR] GET  /users/{uid}  {type(e).__name__}")
            fails += 1
        total += 1
        time.sleep(0.1)

    # 2. POST /users/{id}/order — 10 запросов
    for _ in range(10):
        if not running:
            break
        uid = random.choice(USERS)
        item = random.choice(ITEMS)
        qty = random.randint(1, 5)
        try:
            url = f"{BASE}/users/{uid}/order?item={item}&quantity={qty}"
            req = urllib.request.Request(url, method="POST")
            resp = urllib.request.urlopen(req, timeout=10)
            body = resp.read().decode()
            data = json.loads(body)
            trace_id = data.get("trace_id", "N/A")
            order_status = data.get("order", {}).get("order", {}).get("status", "N/A")
            print(f"  [{resp.status}] POST /users/{uid}/order  item={item} qty={qty}  status={order_status}  trace_id={trace_id[:8]}...")
            oks += 1
        except Exception:
            print(f"  [502] POST /users/{uid}/order  item={item} qty={qty}  (order-service error — нормально)")
            fails += 1
        total += 1
        time.sleep(0.15)

    # 3. GET /health — 2 запроса
    for _ in range(2):
        if not running:
            break
        try:
            req = urllib.request.Request(f"{BASE}/health", method="GET")
            resp = urllib.request.urlopen(req, timeout=5)
            print(f"  [{resp.status}] GET  /health")
            oks += 1
        except Exception:
            print(f"  [ERR] GET  /health")
            fails += 1
        total += 1
        time.sleep(0.05)

    if running:
        print(f"  --- цикл завершён: всего {total} запросов ({oks} OK, {fails} ошибок) ---")
        time.sleep(2.0)  # пауза между циклами

print()
print("=" * 60)
print(f"✅ Итого: {total} запросов отправлено ({oks} OK, {fails} ошибок)")
print()
print("Открой Grafana: http://localhost:3000 → Dashboards → 🪵 Мониторинг микросервисов")