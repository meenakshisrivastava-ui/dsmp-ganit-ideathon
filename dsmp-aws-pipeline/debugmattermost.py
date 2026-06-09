import requests

BASE     = "http://localhost:8065/api/v4"
USERNAME = "meenakshsri"
PASSWORD = "Srime220197"

# ── Step 1: Test login ───────────────────────────────────────────
print("Testing login...")
resp = requests.post(f"{BASE}/users/login", json={
    "login_id" : USERNAME,
    "password" : PASSWORD
})

print(f"Status code : {resp.status_code}")
print(f"Response    : {resp.json()}")
print(f"Token       : {resp.headers.get('Token', 'NO TOKEN FOUND')}")
