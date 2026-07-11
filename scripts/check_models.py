import requests, json
resp = requests.get("http://localhost:4000/models",
    headers={"Authorization": "Bearer omniroute"}, timeout=5)
data = resp.json()
print(json.dumps(data, indent=2))
