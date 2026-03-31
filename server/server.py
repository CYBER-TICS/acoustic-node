from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
from datetime import datetime, timezone

app = FastAPI()

API_KEY = "123456"
DB_PATH = "events.db"

HEARTBEAT_INTERVAL_SECONDS = 120
WARNING_THRESHOLD_SECONDS = 120
OFFLINE_THRESHOLD_SECONDS = 300

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Event(BaseModel):
    node_id: str
    timestamp: str
    lat: float | None = None
    lon: float | None = None
    event_class: str | None = None
    confidence: float | None = None
    status: str


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id TEXT,
            timestamp TEXT,
            lat REAL,
            lon REAL,
            event_class TEXT,
            confidence REAL,
            status TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS nodes (
            node_id TEXT PRIMARY KEY,
            last_seen TEXT,
            lat REAL,
            lon REAL
        )
    """)

    conn.commit()
    conn.close()


def parse_iso(dt_str: str | None):
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except Exception:
        return None


def seconds_since(dt_str: str | None):
    dt = parse_iso(dt_str)
    if not dt:
        return None
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (now - dt).total_seconds()


def compute_node_state(last_seen: str | None, has_active_alert: bool, latest_event_status: str | None):
    delta = seconds_since(last_seen)

    if delta is None:
        return "offline"

    if delta > OFFLINE_THRESHOLD_SECONDS:
        return "offline"

    if has_active_alert:
        return "alert"

    if latest_event_status == "resolved":
        return "resolved"

    if delta > WARNING_THRESHOLD_SECONDS:
        return "warning"

    return "online"


@app.on_event("startup")
def startup():
    init_db()


@app.post("/api/events")
async def receive_event(event: Event, x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    conn = get_connection()
    cur = conn.cursor()

    try:
        now_iso = datetime.now(timezone.utc).isoformat()

        cur.execute("""
            INSERT INTO nodes (node_id, last_seen, lat, lon)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(node_id) DO UPDATE SET
                last_seen = excluded.last_seen,
                lat = COALESCE(excluded.lat, nodes.lat),
                lon = COALESCE(excluded.lon, nodes.lon)
        """, (
            event.node_id,
            now_iso,
            event.lat,
            event.lon
        ))

        if event.event_class != "HEARTBEAT":
            cur.execute("""
                INSERT INTO events (node_id, timestamp, lat, lon, event_class, confidence, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                event.node_id,
                event.timestamp,
                event.lat,
                event.lon,
                event.event_class,
                event.confidence,
                event.status
            ))

        conn.commit()
        return {"ok": True}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        conn.close()


@app.get("/api/events")
def list_events(limit: int = 20):
    conn = get_connection()
    cur = conn.cursor()

    if limit <= 0:
        limit = 20
    if limit > 1000:
        limit = 1000

    cur.execute("""
        SELECT id, node_id, timestamp, lat, lon, event_class, confidence, status
        FROM events
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))

    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return rows


@app.get("/api/events/by-date")
def events_by_date(date: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, node_id, timestamp, lat, lon, event_class, confidence, status
        FROM events
        WHERE DATE(timestamp) = DATE(?)
        ORDER BY id DESC
    """, (date,))

    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return rows


@app.put("/api/events/{event_id}/resolve")
def resolve_event(event_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE events
        SET status = 'resolved'
        WHERE id = ?
    """, (event_id,))

    updated_rows = cur.rowcount
    conn.commit()
    conn.close()

    return {"ok": True, "updated_rows": updated_rows}



@app.get("/api/health")
def health():
    return {"service": "buman-server", "ok": True}



@app.get("/api/nodes")
def list_nodes(status: str = "all"):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT node_id, last_seen, lat, lon
        FROM nodes
        ORDER BY node_id ASC
    """)
    nodes = [dict(row) for row in cur.fetchall()]

    result = []

    for node in nodes:
        node_id = node["node_id"]

        cur.execute("""
            SELECT id, timestamp, lat, lon, event_class, confidence, status
            FROM events
            WHERE node_id = ?
            ORDER BY id DESC
            LIMIT 1
        """, (node_id,))
        latest_event = cur.fetchone()

        cur.execute("""
            SELECT COUNT(*) AS count
            FROM events
            WHERE node_id = ? AND status = 'alert'
        """, (node_id,))
        active_alert_count = cur.fetchone()["count"]
        has_active_alert = active_alert_count > 0

        latest_event_status = latest_event["status"] if latest_event else None
        latest_event_class = latest_event["event_class"] if latest_event else None
        latest_confidence = latest_event["confidence"] if latest_event else None

        node_state = compute_node_state(
            node["last_seen"],
            has_active_alert,
            latest_event_status
        )

        row = {
            "node_id": node_id,
            "last_seen": node["last_seen"],
            "lat": node["lat"],
            "lon": node["lon"],
            "state": node_state,
            "latest_event_class": latest_event_class,
            "latest_confidence": latest_confidence,
            "latest_event_status": latest_event_status,
            "active_alert_count": active_alert_count
        }

        result.append(row)

    if status != "all":
        result = [n for n in result if n["state"] == status]

    conn.close()
    return result