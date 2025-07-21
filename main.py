from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import datetime
import uuid
import json
import os

app = FastAPI()

DATA_DIR = "data"
NEEDS_PATH = os.path.join(DATA_DIR, "needs.json")
OFFERS_PATH = os.path.join(DATA_DIR, "offers.json")
LOG_PATH = os.path.join(DATA_DIR, "log.json")

# ------------------- Models -------------------
class Entry(BaseModel):
    node_id: str
    item: str
    quantity: int
    unit: str
    timestamp: str

class LogEntry(BaseModel):
    need_id: str
    offer_id: str
    delivered_by: str
    notes: str

# ------------------- Helpers -------------------
def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# ------------------- Endpoints -------------------
@app.post("/needs")
def submit_need(need: Entry):
    all_needs = load_json(NEEDS_PATH)
    new_entry = need.dict()
    new_entry["id"] = str(uuid.uuid4())
    all_needs.append(new_entry)
    save_json(NEEDS_PATH, all_needs)
    return {"status": "Need submitted", "id": new_entry["id"]}

@app.post("/offers")
def submit_offer(offer: Entry):
    all_offers = load_json(OFFERS_PATH)
    new_entry = offer.dict()
    new_entry["id"] = str(uuid.uuid4())
    all_offers.append(new_entry)
    save_json(OFFERS_PATH, all_offers)
    return {"status": "Offer submitted", "id": new_entry["id"]}

@app.get("/needs")
def get_needs():
    return load_json(NEEDS_PATH)

@app.get("/offers")
def get_offers():
    return load_json(OFFERS_PATH)

@app.get("/log")
def get_log():
    return load_json(LOG_PATH)

@app.get("/matches")
def get_matches():
    needs = load_json(NEEDS_PATH)
    offers = load_json(OFFERS_PATH)

    matches = []
    for need in needs:
        for offer in offers:
            if need["item"].lower() == offer["item"].lower() and need["unit"] == offer["unit"]:
                matches.append({
                    "need_id": need["id"],
                    "offer_id": offer["id"],
                    "item": need["item"],
                    "quantity_needed": need["quantity"],
                    "quantity_offered": offer["quantity"],
                    "unit": need["unit"]
                })

    return {"matches": matches}

@app.post("/fulfill")
def log_delivery(entry: LogEntry):
    logs = load_json(LOG_PATH)
    new_log = entry.dict()
    new_log["timestamp"] = datetime.utcnow().isoformat()
    logs.append(new_log)
    save_json(LOG_PATH, logs)
    return {"status": "Delivery logged"}
