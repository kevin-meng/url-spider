import requests

print("Testing API...")
try:
    response = requests.get("http://127.0.0.1:8000/api/stats", timeout=5)
    print(f"Status: {response.status_code}")
    print(f"Content: {response.text}")
except Exception as e:
    print(f"Error: {e}")
