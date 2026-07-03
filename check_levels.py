"""Check actual level values in Loki."""
import urllib.request
import urllib.parse
import json
import time

end = int(time.time() * 1e9)
start = end - 3600 * int(1e9)

# Check level label values
url_levels = "http://localhost:3100/loki/api/v1/label/level/values"
r = json.loads(urllib.request.urlopen(url_levels).read())
print("Level values:", r.get("data", []))

# Check all labels
url_labels = "http://localhost:3100/loki/api/v1/labels"
r = json.loads(urllib.request.urlopen(url_labels).read())
print("All labels:", r.get("data", []))

# Get actual log lines with their stream labels
for service in ["user-service", "order-service"]:
    q = '{service="' + service + '"}'
    url = ("http://localhost:3100/loki/api/v1/query_range?query="
           + urllib.parse.quote(q) + "&limit=3&start=" + str(start) + "&end=" + str(end))
    r = json.loads(urllib.request.urlopen(url).read())
    for stream in r.get("data", {}).get("result", []):
        level = stream["stream"].get("level", "NO_LEVEL")
        line = stream["values"][0][1][:200]
        print(f"\n[{service}] level={level}")
        print(f"  line: {line}")