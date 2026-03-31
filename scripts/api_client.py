import requests
import socket

API_KEY = "123456"
SERVER_PORT = 8000
HEALTH_ENDPOINT = "/api/health"
EVENT_ENDPOINT = "/api/events"
SERVER_HOSTNAME = "buman-server.local"

_CACHED_SERVER_BASE = None


def get_local_prefix():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        local_ip = s.getsockname()[0]
        s.close()
        return ".".join(local_ip.split(".")[:-1]) + "."
    except Exception:
        return None


def validate_server(base_url: str) -> bool:
    try:
        r = requests.get(f"{base_url}{HEALTH_ENDPOINT}", timeout=1.5)
        if r.status_code == 200:
            data = r.json()
            return data.get("service") == "buman-server" and data.get("ok") is True
    except Exception:
        pass
    return False


def discover_server_base():
    global _CACHED_SERVER_BASE

    # 1) Try hostname first
    hostname_base = f"http://{SERVER_HOSTNAME}:{SERVER_PORT}"
    if validate_server(hostname_base):
        _CACHED_SERVER_BASE = hostname_base
        return hostname_base

    # 2) Fallback: scan local subnet
    prefix = get_local_prefix()
    if not prefix:
        return None

    print(f"Scanning local network: {prefix}0/24")

    for i in range(1, 255):
        candidate = f"http://{prefix}{i}:{SERVER_PORT}"
        if validate_server(candidate):
            _CACHED_SERVER_BASE = candidate
            return candidate

    return None


def get_server_base():
    global _CACHED_SERVER_BASE

    if _CACHED_SERVER_BASE and validate_server(_CACHED_SERVER_BASE):
        return _CACHED_SERVER_BASE

    _CACHED_SERVER_BASE = None
    return discover_server_base()


def send_event(payload: dict) -> bool:
    base = get_server_base()

    if not base:
        print("Error: server not found on local network.")
        return False

    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            f"{base}{EVENT_ENDPOINT}",
            json=payload,
            headers=headers,
            timeout=3
        )
        return response.status_code == 200

    except Exception as e:
        print(f"Connection error with {base}: {e}")
        global _CACHED_SERVER_BASE
        _CACHED_SERVER_BASE = None
        return False