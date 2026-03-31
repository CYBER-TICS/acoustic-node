from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
from datetime import datetime

app = FastAPI()

API_KEY = "123456"
DB_PATH = "events.db"

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

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id TEXT, timestamp TEXT, lat REAL, lon REAL,
            event_class TEXT, confidence REAL, status TEXT
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

@app.on_event("startup")
def startup():
    init_db()

@app.post("/api/events")
async def receive_event(event: Event, x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        # ACTUALIZAR SALUD DEL NODO
        cur.execute("""
            INSERT INTO nodes (node_id, last_seen, lat, lon) 
            VALUES (?, ?, ?, ?)
            ON CONFLICT(node_id) DO UPDATE SET 
                last_seen = excluded.last_seen,
                lat = COALESCE(excluded.lat, nodes.lat),
                lon = COALESCE(excluded.lon, nodes.lon)
        """, (event.node_id, datetime.now().isoformat(), event.lat, event.lon))

        # GUARDAR ALERTA SI NO ES HEARTBEAT
        if event.event_class != "HEARTBEAT":
            cur.execute("""
                INSERT INTO events (node_id, timestamp, lat, lon, event_class, confidence, status) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (event.node_id, event.timestamp, event.lat, event.lon, 
                  event.event_class, event.confidence, event.status))

        conn.commit()
        return {"ok": True}
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.get("/api/nodes")
def list_nodes():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM nodes")
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return rows

@app.get("/api/events")
def list_events(limit: int = 20):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,))
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return rows
