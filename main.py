from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json
import uuid
from datetime import datetime
import os

app = FastAPI()

DATA_DIR = "data"
NEEDS_PATH = os.path.join(DATA_DIR, "needs.json")
OFFERS_PATH = os.path.join(DATA_DIR, "offers.json")
LOG_PATH = os.path.join(DATA_DIR, "log.json")


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


@app.post("/needs")
def submit_need(need: dict):
    data = load_json(NEEDS_PATH)
    data["id"] = str(uuid.uuid4())
    data["timestamp"] = datetime.utcnow().isoformat()
    save_json(NEEDS_PATH, need)
    return {"status": "Need submitted", "id": data["id"]}


@app.post("/offers")
def submit_offer(offer: dict):
    data = load_json(OFFERS_PATH)
    data["id"] = str(uuid.uuid4())
    data["timestamp"] = datetime.utcnow().isoformat()
    save_json(OFFERS_PATH, offer)
    return {"status": "Offer submitted", "id": data["id"]}


@app.get("/needs")
def get_all_needs():
    return load_json(NEEDS_PATH)


@app.get("/offers")
def get_all_offers():
    return load_json(OFFERS_PATH)


@app.get("/log")
def get_logs():
    return load_json(LOG_PATH)


@app.get("/matches")
def get_matches():
    needs = load_json(NEEDS_PATH)
    offers = load_json(OFFERS_PATH)

    matched_items = []
    for need in needs.get("needs", []):
        for offer in offers.get("offers", []):
            if need["type"] == offer["type"] and need["item"] == offer["item"]:
                matched_items.append({
                    "need": need,
                    "offer": offer,
                    "matched_on": "type+item"
                })
    return {"matches": matched_items}


@app.post("/fulfill")
def fulfill_delivery(entry: dict):
    logs = load_json(LOG_PATH)
    entry["timestamp"] = datetime.utcnow().isoformat()
    logs.append(entry)
    save_json(LOG_PATH, logs)
    return {"status": "Logged"}
