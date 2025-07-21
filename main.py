# arka_backend/main.py

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uuid
import json
import os

app = FastAPI()

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Storage directories
NEEDS_DIR = "data/needs"
OFFERS_DIR = "data/offers"
LOGS_DIR = "data/logs"
os.makedirs(NEEDS_DIR, exist_ok=True)
os.makedirs(OFFERS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# Data models
class Need(BaseModel):
    node_id: str
    item: str
    quantity: int
    urgency: float
    timestamp: str

class Offer(BaseModel):
    node_id: str
    item: str
    quantity: int
    availability_window_hours: int
    timestamp: str

class Match(BaseModel):
    need_node: str
    offer_node: str
    item: str
    quantity_needed: int
    quantity_offered: int
    urgency: float

# Save JSON to disk
def save_json(data, folder, prefix):
    filename = f"{prefix}_{uuid.uuid4().hex}.json"
    with open(os.path.join(folder, filename), "w") as f:
        json.dump(data, f)

# In-memory stores for now
needs_store = []
offers_store = []

@app.post("/needs")
def submit_need(need: Need):
    needs_store.append(need.dict())
    save_json(need.dict(), NEEDS_DIR, "need")
    return {"status": "received"}

@app.post("/offers")
def submit_offer(offer: Offer):
    offers_store.append(offer.dict())
    save_json(offer.dict(), OFFERS_DIR, "offer")
    return {"status": "received"}


@app.get("/matches", response_model=List[Match])
def get_matches():
    raw_matches = match_needs_to_offers(needs_store, offers_store)
    return [Match(**m) for m in raw_matches]
