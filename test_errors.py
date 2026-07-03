"""Test if ERROR logs exist in Loki."""
import urllib.request
import urllib.parse
import json
import time

end = int(time.time() * 1e9)
start = end - 600 * int(1e9)

# Test 1: simple filter with regular regex
q1 = '{env="dev"} | json | level =~ "ERROR"'
url1 = f"http://localhost:3100/loki/api/v1/query_range?query={urllib.parse.quote(q1)}&limit=2&start={start}&end={end}"
r1 = json.loads(urllib.request.urlopen(url1).read())
res1 = r1.get("data", {}).get("result", [])
print(f"Test 1 (level =~ ERROR): {len(res1)} streams")
for s in res1:
    print(f"  service={s['stream'].get('service','?')} values={len(s['values'])}")

# Test 2: with backtick
q2 = '{env="dev"} | json | level = `ERROR`'
url2 = f"http://localhost:3100/loki/api/v1/query_range?query={urllib.parse.quote(q2)}&limit=2&start={start}&end={end}"
try:
    r2 = json.loads(urllib.request.urlopen(url2).read())
    res2 = r2.get("data", {}).get("result", [])
    print(f"Test 2 (level = `ERROR`): {len(res2)} streams")
    for s in res2:
        print(f"  service={s['stream'].get('service','?')} values={len(s['values'])}")
except Exception as e:
    print(f"Test 2 ERROR: {e}")

# Test 3: what level values exist in JSON?
q3 = '{env="dev"} | json | level != ""'
url3 = f"http://localhost:3100/loki/api/v1/query_range?query={urllib.parse.quote(q3)}&limit=5&start={start}&end={end}"
r3 = json.loads(urllib.request.urlopen(url3).read())
res3 = r3.get("data", {}).get("result", [])
print(f"Test 3 (any level): {len(res3)} streams")
for s in res3:
    # Get first line
    line = s["values"][0][1] if s["values"] else ""
    print(f"  service={s['stream'].get('service','?')} line={line[:100]}")