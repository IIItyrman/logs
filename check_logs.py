"""Проверка логов в Loki API."""
import urllib.request
import urllib.parse
import json
import time

end = int(time.time() * 1e9)
start = end - 600 * int(1e9)

# Проверка user-service
q = '{service="user-service"}'
url = f"http://localhost:3100/loki/api/v1/query_range?query={urllib.parse.quote(q)}&limit=3&start={start}&end={end}"
r = json.loads(urllib.request.urlopen(url).read())
print("=== user-service ===")
print("Status:", r["status"])
results = r.get("data", {}).get("result", [])
print("Streams found:", len(results))
for s in results:
    print("Labels:", s["stream"], "Log entries:", len(s["values"]))

# Проверка order-service
q = '{service="order-service"}'
url = f"http://localhost:3100/loki/api/v1/query_range?query={urllib.parse.quote(q)}&limit=3&start={start}&end={end}"
r = json.loads(urllib.request.urlopen(url).read())
print("\n=== order-service ===")
print("Status:", r["status"])
results = r.get("data", {}).get("result", [])
print("Streams found:", len(results))
for s in results:
    print("Labels:", s["stream"], "Log entries:", len(s["values"]))

# Проверка ошибок в order-service
q = '{service="order-service"} | level="ERROR"'
url = f"http://localhost:3100/loki/api/v1/query_range?query={urllib.parse.quote(q)}&limit=3&start={start}&end={end}"
r = json.loads(urllib.request.urlopen(url).read())
print("\n=== order-service ERROR ===")
print("Status:", r["status"])
results = r.get("data", {}).get("result", [])
print("Streams found:", len(results))
for s in results:
    print("Labels:", s["stream"], "Log entries:", len(s["values"]))