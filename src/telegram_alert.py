import os
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def send_telegram_alert(message: str) -> bool:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("❌ Telegram not configured in .env")
        return False

    if not message or len(message.strip()) < 3:
        print("⚠️ Empty or invalid message")
        return False

    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    full_message = f"{message}\nTime: {timestamp}"

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": full_message
    }

    try:
        response = requests.post(url, json=payload, timeout=10)

        if response.status_code == 200:
            print("📩 Telegram message sent")
            return True
        else:
            print("❌ Telegram error:", response.status_code)
            print(response.text)
            return False

    except Exception as e:
        print("❌ Exception sending Telegram:", e)
        return False


if __name__ == "__main__":
    ok = send_telegram_alert("Test message from telegram_alert.py")
    print("Sent:", ok)