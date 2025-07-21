# main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid, os, json

app = FastAPI()

# ─── CORS ────────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://brilliant-gingersnap-a8e6d2.netlify.app",  # your frontend URL
        # "",
        # or use "*" to allow all origins (not recommended for production)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ────────────────────────────────────────────────────────────────────────────────

DATA_DIR = "data"
NEEDS_PATH = os.path.join(DATA_DIR, "needs.json")
OFFERS_PATH = os.path.join(DATA_DIR, "offers.json")
LOG_PATH = os.path.join(DATA_DIR, "log.json")

def load_list(path: str) -> List[Any]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_list(path: str, lst: List[Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(lst, f, indent=2, ensure_ascii=False)

# 1️⃣ Needs

class NeedItem(BaseModel):
    type: str
    item: str
    quantity: int
    unit: str
    time_sensitivity_hours: int
    recurrence: str
    alt_items: List[str]
    notes: str

class Constraints(BaseModel):
    accessible_routes: List[str]
    delivery_window_hours: int
    security_risks: List[str]

class Contact(BaseModel):
    method: str
    handle: str
    preferred_lang: str

class TrustInfo(BaseModel):
    vouched_by: List[str]
    last_fulfilled: Optional[str]

class NeedSubmission(BaseModel):
    node_id: str
    timestamp: str
    location: Dict[str, Optional[Any]]
    urgency: float
    vitality: float
    needs: List[NeedItem]
    constraints: Constraints
    contact: Contact
    trust: TrustInfo

@app.post("/needs")
def submit_need(sub: NeedSubmission):
    arr = load_list(NEEDS_PATH)
    entry = sub.dict()
    entry["entry_id"] = str(uuid.uuid4())
    arr.append(entry)
    save_list(NEEDS_PATH, arr)
    return {"status": "need stored", "entry_id": entry["entry_id"]}

@app.get("/needs")
def get_needs():
    return load_list(NEEDS_PATH)

# 2️⃣ Offers

class OfferItem(BaseModel):
    type: str
    item: str
    quantity: int
    unit: str
    availability_window_hours: int
    recurrence: str
    dimensions: Dict[str, Any]
    notes: str

class OfferSubmission(BaseModel):
    node_id: str
    timestamp: str
    location: Dict[str, Optional[Any]]
    offers: List[OfferItem]
    constraints: Dict[str, Any]
    contact: Contact
    trust: Dict[str, Any]

@app.post("/offers")
def submit_offer(sub: OfferSubmission):
    arr = load_list(OFFERS_PATH)
    entry = sub.dict()
    entry["entry_id"] = str(uuid.uuid4())
    arr.append(entry)
    save_list(OFFERS_PATH, arr)
    return {"status": "offer stored", "entry_id": entry["entry_id"]}

@app.get("/offers")
def get_offers():
    return load_list(OFFERS_PATH)

# 3️⃣ Matches

@app.get("/matches")
def get_matches():
    needs = load_list(NEEDS_PATH)
    offers = load_list(OFFERS_PATH)
    out = []
    for n in needs:
        for need in n["needs"]:
            for o in offers:
                for offer in o["offers"]:
                    if need["item"].lower() == offer["item"].lower() and offer["quantity"] >= need["quantity"]:
                        out.append({
                            "need_entry_id": n["entry_id"],
                            "offer_entry_id": o["entry_id"],
                            "item": need["item"],
                            "quantity_needed": need["quantity"],
                            "quantity_offered": offer["quantity"],
                            "unit": need["unit"],
                            "need_timestamp": n["timestamp"],
                            "offer_timestamp": o["timestamp"]
                        })
    return {"matches": out}

# 4️⃣ Log Fulfillments

class TransportChainEntry(BaseModel):
    node_id: str
    handoff_time: str
    route: str
    risk: str
    verified: bool

class Verification(BaseModel):
    witness_nodes: List[str]
    method: str
    verified_at: str

class TrustUpdateNode(BaseModel):
    node_id: str
    credit: float

class TrustUpdate(BaseModel):
    recipient: TrustUpdateNode
    provider: TrustUpdateNode
    carrier: TrustUpdateNode

class NeedLog(BaseModel):
    node_id: str
    item: str
    quantity: int
    unit: str
    original_timestamp: str

class OfferLog(BaseModel):
    node_id: str
    item: str
    quantity: int
    unit: str
    timestamp: str

class LogSubmission(BaseModel):
    log_id: str
    timestamp: str
    status: str
    need: NeedLog
    offer: OfferLog
    transport_chain: List[TransportChainEntry]
    verification: Verification
    trust_update: TrustUpdate
    notes: str

@app.post("/log")
def submit_log(sub: LogSubmission):
    arr = load_list(LOG_PATH)
    entry = sub.dict()
    arr.append(entry)
    save_list(LOG_PATH, arr)
    return {"status": "log stored", "log_id": entry["log_id"]}

@app.get("/log")
def get_log():
    return load_list(LOG_PATH)
