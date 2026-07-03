"""Проверка структуры данных в Loki."""
import urllib.request
import urllib.parse
import json
import time

end = int(time.time() * 1e9)
start = end - 3600 * int(1e9)  # последний час

# Запросим по 1 строке лога для каждого сервиса
for service in ["user-service", "order-service"]:
    q = f'{{service="{service}"}}'
    url = f"http://localhost:3100/loki/api/v1/query_range?query={urllib.parse.quote(q)}&limit=1&start={start}&end={end}"
    try:
        r = json.loads(urllib.request.urlopen(url).read())
        results = r.get("data", {}).get("result", [])
        if results:
            stream = results[0]
            labels = stream["stream"]
            # Первая строка лога
            ts, line = stream["values"][0]
            print(f"=== {service} ===")
            print(f"Stream labels: {json.dumps(labels, indent=2)}")
            print(f"Log line: {line}")
            print()
        else:
            print(f"=== {service} === No data\n")
    except Exception as e:
        print(f"=== {service} === Error: {e}\n")