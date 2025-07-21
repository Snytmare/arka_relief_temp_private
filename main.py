from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import os, json, uuid, datetime

app = FastAPI()

# ─── CORS ────────────────────────────────────────────────────────────────────
# allow all origins (or replace "*" with a list of your exact domains)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ─────────────────────────────────────────────────────────────────────────────

DATA_DIR = "data"
NEEDS_PATH = os.path.join(DATA_DIR, "needs.json")
OFFERS_PATH = os.path.join(DATA_DIR, "offers.json")
LOG_PATH = os.path.join(DATA_DIR, "log.json")

# ensure data files and folder exist
os.makedirs(DATA_DIR, exist_ok=True)
for path in (NEEDS_PATH, OFFERS_PATH, LOG_PATH):
    if not os.path.isfile(path):
        with open(path, "w") as f:
            json.dump([], f)

# ─── Models ──────────────────────────────────────────────────────────────────
class Need(BaseModel):
    node_id: str
    item: str
    quantity: int
    unit: str
    timestamp: str

class Offer(BaseModel):
    node_id: str
    item: str
    quantity: int
    unit: str
    timestamp: str

class LogEntry(BaseModel):
    log_id: str
    timestamp: str
    status: str
    need: Dict[str, Any]
    offer: Dict[str, Any]
    transport_chain: List[Dict[str, Any]]
    verification: Dict[str, Any]
    trust_update: Dict[str, Any]
    notes: str

# ─── Helpers ─────────────────────────────────────────────────────────────────
def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# ─── Endpoints ───────────────────────────────────────────────────────────────
@app.post("/needs")
def create_need(need: Need):
    lst = load(NEEDS_PATH)
    entry = need.dict()
    entry["id"] = str(uuid.uuid4())
    entry["created_at"] = datetime.datetime.utcnow().isoformat()
    lst.append(entry)
    save(NEEDS_PATH, lst)
    return {"status": "need submitted", "id": entry["id"]}

@app.get("/needs")
def get_needs():
    return load(NEEDS_PATH)

@app.post("/offers")
def create_offer(offer: Offer):
    lst = load(OFFERS_PATH)
    entry = offer.dict()
    entry["id"] = str(uuid.uuid4())
    entry["created_at"] = datetime.datetime.utcnow().isoformat()
    lst.append(entry)
    save(OFFERS_PATH, lst)
    return {"status": "offer submitted", "id": entry["id"]}

@app.get("/offers")
def get_offers():
    return load(OFFERS_PATH)

@app.get("/matches")
def get_matches():
    needs = load(NEEDS_PATH)
    offers = load(OFFERS_PATH)
    matches = []
    for n in needs:
        for o in offers:
            if n["item"].lower() == o["item"].lower() and o["quantity"] >= n["quantity"]:
                matches.append({
                    "need": n,
                    "offer": o,
                    "matched_at": datetime.datetime.utcnow().isoformat()
                })
    return matches

@app.post("/log")
def create_log(log: LogEntry):
    lst = load(LOG_PATH)
    entry = log.dict()
    lst.append(entry)
    save(LOG_PATH, lst)
    return {"status": "log entry created", "log_id": entry["log_id"]}

@app.get("/log")
def get_log():
    return load(LOG_PATH)
