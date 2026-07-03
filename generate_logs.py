"""
Генератор логов — отправляет запросы к user-service и order-service,
чтобы наполнить Loki данными для анализа в Grafana.
"""
import urllib.request
import random
import time
import sys

USERS = ["1", "2", "3"]
ITEMS = ["laptop", "phone", "book", "monitor", "keyboard", "mouse", "headphones"]
BASE = "http://localhost:8001"

total = 0
oks = 0
fails = 0

print("🚀 Генерирую логи (50 запросов)...")
print()

# 1. GET /users/{id} — 15 запросов
for i in range(15):
    uid = random.choice(USERS)
    try:
        req = urllib.request.Request(f"{BASE}/users/{uid}", method="GET")
        resp = urllib.request.urlopen(req)
        body = resp.read().decode()
        data = __import__("json").loads(body)
        print(f"  [{resp.status}] GET  /users/{uid}  trace_id={data.get('trace_id', 'N/A')[:8]}...")
        oks += 1
    except Exception as e:
        print(f"  [ERR] GET  /users/{uid}  {e}")
        fails += 1
    total += 1
    time.sleep(0.1)

# 2. POST /users/{id}/order — 25 запросов
for i in range(25):
    uid = random.choice(USERS)
    item = random.choice(ITEMS)
    qty = random.randint(1, 5)
    try:
        url = f"{BASE}/users/{uid}/order?item={item}&quantity={qty}"
        req = urllib.request.Request(url, method="POST")
        resp = urllib.request.urlopen(req)
        body = resp.read().decode()
        data = __import__("json").loads(body)
        trace_id = data.get("trace_id", "N/A")
        order_status = data.get("order", {}).get("order", {}).get("status", "N/A")
        print(f"  [{resp.status}] POST /users/{uid}/order  item={item} qty={qty}  status={order_status}  trace_id={trace_id[:8]}...")
        oks += 1
    except Exception as e:
        print(f"  [502] POST /users/{uid}/order  item={item} qty={qty}  (order-service error — это нормально)")
        fails += 1
    total += 1
    time.sleep(0.15)

# 3. GET /health — 10 запросов
for i in range(10):
    try:
        req = urllib.request.Request(f"{BASE}/health", method="GET")
        resp = urllib.request.urlopen(req)
        print(f"  [{resp.status}] GET  /health")
        oks += 1
    except Exception:
        print(f"  [ERR] GET  /health")
        fails += 1
    total += 1
    time.sleep(0.05)

print()
print(f"✅ Готово: {total} запросов отправлено ({oks} OK, {fails} ошибок)")
print()
print("Теперь открой Grafana: http://localhost:3000 → Explore → Loki")
print("Попробуй LogQL:")
print("  {env=\"dev\"} | json")
print("  {service=\"order-service\"} | level=\"ERROR\"")