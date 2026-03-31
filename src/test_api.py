from api_client import send_event
from datetime import datetime

payload = {
    "node_id": "NODE-001",
    "timestamp": datetime.utcnow().isoformat(),
    "event_class": "motor_objetivo",
    "confidence": 0.88,
    "status": "alert"
}

ok = send_event(payload)
print("Sent:", ok)