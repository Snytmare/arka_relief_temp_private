from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uuid
import json
import os
import httpx
import asyncio

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

NEEDS_DIR = "data/needs"
OFFERS_DIR = "data/offers"
LOGS_DIR = "data/logs"
os.makedirs(NEEDS_DIR, exist_ok=True)
os.makedirs(OFFERS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

class Need(BaseModel):
    node_id: str
    item: str
    quantity: int
    urgency: float
    timestamp: str
    callback_url: Optional[str] = None

class Offer(BaseModel):
    node_id: str
    item: str
    quantity: int
    availability_window_hours: int
    timestamp: str
    callback_url: Optional[str] = None

class Match(BaseModel):
    need_node: str
    offer_node: str
    item: str
    quantity_needed: int
    quantity_offered: int
    urgency: float
    
class EncryptedOffer(BaseModel):
    encrypted_data: str
    nonce: str
    sender_node_id: str
    item_hint: Optional[str] = None


node_callbacks = {}
needs_store = []
offers_store = []

def save_json(data, folder, prefix):
    filename = f"{prefix}_{uuid.uuid4().hex}.json"
    with open(os.path.join(folder, filename), "w") as f:
        json.dump(data, f)

@app.post("/register")
def register_node(data: dict):
    node_callbacks[data["node_id"]] = data["callback_url"]
    return {"status": "registered"}

def get_callback_url(node_id):
    return node_callbacks.get(node_id)

def match_needs_to_offers(needs: List[dict], offers: List[dict]) -> List[dict]:
    matches = []
    for need in needs:
        for offer in offers:
            if need['item'].lower() == offer['item'].lower() and offer['quantity'] > 0:
                match_quantity = min(need['quantity'], offer['quantity'])
                match = {
                    "need_node": need['node_id'],
                    "offer_node": offer['node_id'],
                    "item": need['item'],
                    "quantity_needed": need['quantity'],
                    "quantity_offered": match_quantity,
                    "urgency": need['urgency']
                }
                matches.append(match)
    return matches

async def notify_match(match, callback_url):
    try:
        async with httpx.AsyncClient() as client:
            await client.post(callback_url, json=match)
            print(f"✅ Notified {callback_url}")
    except Exception as e:
        print(f"❌ Failed to notify {callback_url}: {e}")

@app.post("/needs")
async def submit_need(need: Need):
    need_data = need.dict()
    needs_store.append(need_data)
    save_json(need_data, NEEDS_DIR, "need")

    matches = match_needs_to_offers([need_data], offers_store)
    tasks = []

    for match in matches:
        offer_callback = get_callback_url(match['offer_node'])
        if offer_callback:
            tasks.append(notify_match(match, offer_callback))
        if need.callback_url:
            tasks.append(notify_match(match, need.callback_url))

    if tasks:
        await asyncio.gather(*tasks)

    return {"status": "received", "matches_sent": len(matches)}

@app.post("/offers")
async def submit_offer(offer: Offer):
    offer_data = offer.dict()
    offers_store.append(offer_data)
    save_json(offer_data, OFFERS_DIR, "offer")

    matches = match_needs_to_offers(needs_store, [offer_data])
    tasks = []

    for match in matches:
        need_callback = get_callback_url(match['need_node'])
        if need_callback:
            tasks.append(notify_match(match, need_callback))
        if offer.callback_url:
            tasks.append(notify_match(match, offer.callback_url))

    if tasks:
        await asyncio.gather(*tasks)

    return {"status": "received", "matches_sent": len(matches)}

@app.get("/matches", response_model=List[Match])
def get_matches():
    raw_matches = match_needs_to_offers(needs_store, offers_store)
    return [Match(**m) for m in raw_matches]


class EncryptedNeed(BaseModel):
    encrypted_data: str
    nonce: str
    sender_node_id: str
    item_hint: Optional[str] = None
    timestamp: Optional[str] = None

@app.post("/encrypted-needs")
async def receive_encrypted_need(payload: EncryptedNeed):
    # Save the encrypted payload as a file for later processing
    encrypted_entry = payload.dict()
    save_json(encrypted_entry, NEEDS_DIR, "encrypted")

    return {"status": "encrypted need received"}

class EncryptedOffer(BaseModel):
    encrypted_data: str
    nonce: str
    sender_node_id: str
    item_hint: Optional[str] = None
    timestamp: Optional[str] = None

@app.post("/encrypted-offers")
async def receive_encrypted_offer(payload: EncryptedOffer):
    encrypted_entry = payload.dict()
    save_json(encrypted_entry, OFFERS_DIR, "encrypted_offer")

    return {"status": "encrypted offer received"}

@app.post("/encrypted-offers")
async def encrypted_offer(offer: EncryptedOffer):
    # Log to disk (optional but good for future matching)
    offer_data = offer.dict()
    save_json(offer_data, OFFERS_DIR, "encrypted_offer")

    # Attempt notification to the recipient node (if registered)
    recipient_callback = get_callback_url(offer.item_hint)  # Fallback to hint if no full match

    if recipient_callback:
        try:
            await notify_match(offer_data, recipient_callback)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to notify: {e}")

    return {"status": "received", "delivered": bool(recipient_callback)}

@app.post("/decrypted-need")
async def receive_decrypted_need(need: Need):
    need_data = need.dict()
    needs_store.append(need_data)
    save_json(need_data, NEEDS_DIR, "decrypted_need")

    # Match against decrypted offers
    matches = match_needs_to_offers([need_data], offers_store)
    tasks = []

    for match in matches:
        offer_callback = get_callback_url(match['offer_node'])
        if offer_callback:
            tasks.append(notify_match(match, offer_callback))
        if need.callback_url:
            tasks.append(notify_match(match, need.callback_url))

    if tasks:
        await asyncio.gather(*tasks)

    return {"status": "decrypted need accepted", "matches_sent": len(matches)}

@app.post("/decrypted-offer")
async def receive_decrypted_offer(offer: Offer):
    offer_data = offer.dict()
    offers_store.append(offer_data)
    save_json(offer_data, OFFERS_DIR, "decrypted_offer")

    # Match against decrypted needs
    matches = match_needs_to_offers(needs_store, [offer_data])
    tasks = []

    for match in matches:
        need_callback = get_callback_url(match['need_node'])
        if need_callback:
            tasks.append(notify_match(match, need_callback))
        if offer.callback_url:
            tasks.append(notify_match(match, offer.callback_url))

    if tasks:
        await asyncio.gather(*tasks)

    return {"status": "decrypted offer accepted", "matches_sent": len(matches)}

inbox_store = []

@app.post("/encrypted-inbox")
def receive_encrypted(payload: dict):
    # Store encrypted message in inbox
    inbox_store.append(payload)
    return {"status": "stored"}

@app.get("/inbox/{recipient_key}")
def get_inbox(recipient_key: str):
    messages = [msg for msg in inbox_store if msg.get("recipient_key") == recipient_key]
    return {"messages": messages}

