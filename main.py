from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel
from typing import List, Dict, Any, Literal, Optional
from dotenv import load_dotenv

import os, json, uuid, datetime

# ─── Load ENV ──────────────────────────────────────────────────────
load_dotenv()
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

# ─── Models ────────────────────────────────────────────────────────
class NeedItem(BaseModel):
    item: str
    quantity: int

class NeedPayload(BaseModel):
    node_id: str
    needs: List[NeedItem]

class MatchRequest(BaseModel):
    needs: List[NeedItem]

class MatchedItem(BaseModel):
    item: str
    quantity_needed: int
    quantity_offered: int
    coverage: float

class MatchResponse(BaseModel):
    offer_node: str
    score: float
    matched_items: List[MatchedItem]

class TrustEvent(BaseModel):
    node_id: str
    event: str
    delta: float
    reason: str
    timestamp: str

class TrustLog(BaseModel):
    node_id: str
    type: Literal["relieve", "warn", "commend"]
    value: float
    reason: Optional[str] = None
    timestamp: Optional[str] = None

# ─── Init App ──────────────────────────────────────────────────────
app = FastAPI()
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content={"message": "Too many requests, slow down."})

# ─── CORS ───────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://brilliant-gingersnap-a8e6d2.netlify.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Directory Setup ───────────────────────────────────────────────
BASE_DIR = "app/data"
NEEDS_DIR = os.path.join(BASE_DIR, "needs")
OFFERS_DIR = os.path.join(BASE_DIR, "offers")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
TRUST_DIR = os.path.join(BASE_DIR, "trust")
for d in (NEEDS_DIR, OFFERS_DIR, LOGS_DIR, TRUST_DIR):
    os.makedirs(d, exist_ok=True)

# ─── Utils ─────────────────────────────────────────────────────────
def save_json(obj: Dict[str, Any], folder: str, prefix: str) -> str:
    fn = f"{prefix}_{uuid.uuid4().hex}.json"
    with open(os.path.join(folder, fn), "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)
    return fn

def load_folder(folder: str) -> List[Dict[str, Any]]:
    return [
        json.load(open(os.path.join(folder, fn), "r", encoding="utf-8"))
        for fn in sorted(os.listdir(folder)) if fn.endswith(".json")
    ]

def log_trust_event(event: TrustEvent):
    filename = f"trust_{uuid.uuid4().hex}.json"
    path = os.path.join(TRUST_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(event.dict(), f, indent=2)

def get_trust_score(node_id: str) -> float:
    score = 0.0
    for fn in os.listdir(TRUST_DIR):
        if fn.endswith(".json"):
            with open(os.path.join(TRUST_DIR, fn), "r") as f:
                entry = json.load(f)
                if entry.get("node_id") == node_id:
                    score += entry.get("delta", 0.0)
    return round(score, 3)

# ─── API Endpoints ─────────────────────────────────────────────────

@app.post("/trustlog")
@limiter.limit("5/minute")
async def post_trust_log(trust_entry: TrustLog, request: Request):
    log_file = os.path.join(TRUST_DIR, f"{trust_entry.node_id}.jsonl")
    entry = trust_entry.dict()
    if not entry.get("timestamp"):
        entry["timestamp"] = datetime.datetime.utcnow().isoformat()
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return {"message": "✅ Trust log recorded.", "file": log_file}

@app.get("/trustlog/{node_id}")
def get_trust_logs(node_id: str):
    log_file = os.path.join(TRUST_DIR, f"{node_id}.jsonl")
    if not os.path.exists(log_file):
        raise HTTPException(status_code=404, detail="Trust log not found.")
    with open(log_file, "r", encoding="utf-8") as f:
        return [json.loads(line.strip()) for line in f if line.strip()]

@app.get("/trustlog")
@limiter.limit("5/minute")
async def get_trust_log(request: Request, node_id: str = ""):
    logs = load_folder(TRUST_DIR)
    if node_id:
        logs = [log for log in logs if log.get("node_id") == node_id]
    return logs

@app.post("/trust/relieve")
async def relieve_trust(request: Request):
    data = await request.json()
    event = TrustEvent(
        node_id=data["node_id"],
        event="relief_action",
        delta=+0.5,
        reason=data.get("reason", "Relief action taken"),
        timestamp=datetime.datetime.utcnow().isoformat()
    )
    log_trust_event(event)
    return {"status": "relieved", "trust_delta": 0.5}

@app.post("/trust/revoke")
async def revoke_trust(request: Request):
    data = await request.json()
    event = TrustEvent(
        node_id=data["node_id"],
        event="consent_revoked",
        delta=-1.0,
        reason=data.get("reason", "Consent revoked"),
        timestamp=datetime.datetime.utcnow().isoformat()
    )
    log_trust_event(event)
    return {"status": "revoked", "trust_delta": -1.0}

@app.post("/needs")
@limiter.limit("5/minute")
async def post_needs(request: Request):
    payload = await request.json()
    payload["_received_at"] = datetime.datetime.utcnow().isoformat()
    fn = save_json(payload, NEEDS_DIR, "need")
    return {"status": "need stored", "file": fn}

@app.get("/needs")
@limiter.limit("5/minute")
async def get_needs(request: Request):
    return load_folder(NEEDS_DIR)

@app.post("/offers")
@limiter.limit("5/minute")
async def post_offers(request: Request):
    payload = await request.json()
    payload["_received_at"] = datetime.datetime.utcnow().isoformat()
    fn = save_json(payload, OFFERS_DIR, "offer")
    return {"status": "offer stored", "file": fn}

@app.get("/offers")
@limiter.limit("5/minute")
async def get_offers(request: Request):
    return load_folder(OFFERS_DIR)

@app.post("/log")
@limiter.limit("5/minute")
async def post_log(request: Request):
    payload = await request.json()
    payload["_logged_at"] = datetime.datetime.utcnow().isoformat()
    fn = save_json(payload, LOGS_DIR, "log")
    return {"status": "log stored", "file": fn}

@app.get("/log")
@limiter.limit("5/minute")
async def get_log(request: Request):
    return load_folder(LOGS_DIR)

@app.get("/route/{need_id}/{offer_id}")
async def get_route(need_id: str, offer_id: str):
    return generate_route(need_id, offer_id)

@app.post("/match", response_model=List[MatchResponse])
async def match_needs(match_request: MatchRequest):
    offers_db = load_folder(OFFERS_DIR)
    results = []
    for offer in offers_db:
        match_score = 0.0
        matched_items = []
        for need in match_request.needs:
            for offered in offer.get("offers", []):
                if need.item.lower() == offered.get("item", "").lower():
                    quantity_offered = offered.get("quantity", 0)
                    quantity_ratio = min(need.quantity / quantity_offered, 1.0) if quantity_offered else 0.0
                    item_score = 0.4
                    quantity_score = 0.3 * quantity_ratio
                    match_score += item_score + quantity_score
                    matched_items.append({
                        "item": need.item,
                        "quantity_needed": need.quantity,
                        "quantity_offered": quantity_offered,
                        "coverage": round(quantity_ratio, 2)
                    })
        if matched_items:
            results.append({
                "offer_node": offer.get("node_id", "unknown"),
                "score": round(match_score, 3),
                "matched_items": matched_items
            })
    results.sort(key=lambda x: x["score"], reverse=True)
    return results

@app.post("/admin")
def do_admin_action(x_admin_token: str = Header(...)):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"message": "✅ Admin action authorized"}

# ─── Routing Helper ────────────────────────────────────────────────
def generate_route(need_node_id: str, offer_node_id: str) -> Dict[str, str]:
    return {
        "from": offer_node_id,
        "to": need_node_id,
        "method": "direct relay (simulated)"
    }
