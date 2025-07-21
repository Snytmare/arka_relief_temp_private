from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import Optional, List

app = FastAPI()

# =========================
# ✅ Data Models
# =========================

class Need(BaseModel):
    description: str
    location: str
    contact_info: str
    callback_url: Optional[str] = None

class Offer(BaseModel):
    description: str
    location: str
    contact_info: str
    callback_url: Optional[str] = None

class EncryptedNeed(BaseModel):
    encrypted_data: str
    recipient_key: str
    nonce: str

class EncryptedOffer(BaseModel):
    encrypted_data: str
    recipient_key: str
    nonce: str

# =========================
# ✅ In-Memory Storage
# =========================

needs_store: List[dict] = []
offers_store: List[dict] = []
inbox_store: List[dict] = []

# =========================
# ✅ Decrypted Endpoints
# =========================

@app.post("/needs")
async def receive_need(need: Need):
    needs_store.append(need.dict())
    return {"status": "Need stored"}

@app.get("/needs")
def get_needs():
    return needs_store

@app.post("/offers")
async def receive_offer(offer: Offer):
    offers_store.append(offer.dict())
    return {"status": "Offer stored"}

@app.get("/offers")
def get_offers():
    return offers_store

# =========================
# ✅ Encrypted Endpoints
# =========================

@app.post("/encrypted-needs")
async def receive_encrypted_need(payload: EncryptedNeed):
    inbox_store.append(payload.dict())
    return {"status": "Encrypted need stored"}

@app.post("/encrypted-offers")
async def receive_encrypted_offer(payload: EncryptedOffer):
    inbox_store.append(payload.dict())
    return {"status": "Encrypted offer stored"}

# =========================
# ✅ Inbox Retrieval by Recipient Key
# =========================

@app.get("/inbox/{recipient_key}")
def get_inbox(recipient_key: str):
    messages = [msg for msg in inbox_store if msg.get("recipient_key") == recipient_key]
    return {"messages": messages}
