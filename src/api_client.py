import requests

SERVER_URL = "http://10.150.133.139:8000/api/events"
API_KEY = "123456"


def send_event(payload: dict) -> bool:
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(SERVER_URL, json=payload, headers=headers, timeout=5)
        print(f"Status: {response.status_code} | Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Connection error: {e}")
        return False
