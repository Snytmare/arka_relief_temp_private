from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel
from typing import List, Dict, Any
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
    need: str
    
    
# ─── Init App ──────────────────────────────────────────────────────
app = FastAPI()
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# ─── Exception Handler ─────────────────────────────────────────────
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"message": "Too many requests, slow down."}
    )

# ─── CORS ───────────────────────────────────────────────────────────
origins = [
    "https://brilliant-gingersnap-a8e6d2.netlify.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,        
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Directory Setup ───────────────────────────────────────────────
BASE_DIR = "data"
NEEDS_DIR = os.path.join(BASE_DIR, "needs")
OFFERS_DIR = os.path.join(BASE_DIR, "offers")
LOGS_DIR = os.path.join(BASE_DIR, "logs")
for d in (NEEDS_DIR, OFFERS_DIR, LOGS_DIR):
    os.makedirs(d, exist_ok=True)

# ─── Utils ─────────────────────────────────────────────────────────
def save_json(obj: Dict[str, Any], folder: str, prefix: str) -> str:
    fn = f"{prefix}_{uuid.uuid4().hex}.json"
    with open(os.path.join(folder, fn), "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)
    return fn

def load_folder(folder: str) -> List[Dict[str, Any]]:
    out = []
    for fn in sorted(os.listdir(folder)):
        if fn.endswith(".json"):
            with open(os.path.join(folder, fn), "r", encoding="utf-8") as f:
                out.append(json.load(f))
    return out

# ─── API Endpoints ─────────────────────────────────────────────────


@app.post("/match")
async def match_nodes(match_request: MatchRequest, request: Request):
    need = match_request.need.lower()
    matches = []

    offers = load_folder(OFFERS_DIR)

    for node in offers:
        for offer in node.get("offers", []):
            if need == offer.get("item", "").lower():
                score = 0.6 * node.get("vitality", 1.0) + 0.4 * (1 - node.get("urgency", 0.5))
                node_with_score = node.copy()
                node_with_score["score"] = round(score, 3)
                matches.append(node_with_score)

    matches.sort(key=lambda n: n["score"], reverse=True)
    return matches



@app.post("/needs")
@limiter.limit("5/minute")
async def post_needs(request: Request):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
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
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
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
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    payload["_logged_at"] = datetime.datetime.utcnow().isoformat()
    fn = save_json(payload, LOGS_DIR, "log")
    return {"status": "log stored", "file": fn}

@app.get("/log")
@limiter.limit("5/minute")
async def get_log(request: Request):
    return load_folder(LOGS_DIR)

@app.get("/match")
@limiter.limit("5/minute")
def get_matches(request: Request):
    return match_needs_to_offers()



@app.get("/route/{need_id}/{offer_id}")
async def get_route(need_id: str, offer_id: str):
    return generate_route(need_id, offer_id)


# ─── Match & Routing Logic ─────────────────────────────────────────

def generate_route(need_node_id: str, offer_node_id: str) -> Dict[str, str]:
    return {
        "from": offer_node_id,
        "to": need_node_id,
        "method": "direct relay (simulated)",  # Placeholder
    }

def match_needs_to_offers() -> List[Dict[str, Any]]:
    needs = load_folder(NEEDS_DIR)
    offers = load_folder(OFFERS_DIR)
    matches = []

    for n in needs:
        node_id_n = n.get("node_id")
        urgency = float(n.get("urgency", 0.5))
        vitality = float(n.get("vitality", 1.0))
        need_items = n.get("needs", [])

        for need_item in need_items:
            item_needed = need_item.get("item", "").lower()
            quantity_needed = int(need_item.get("quantity", 0))

            for o in offers:
                node_id_o = o.get("node_id")
                offer_items = o.get("offers", [])

                for offer_item in offer_items:
                    item_offered = offer_item.get("item", "").lower()
                    quantity_offered = int(offer_item.get("quantity", 0))

                    if item_needed == item_offered and quantity_offered >= quantity_needed:
                        score = 0.6 * urgency + 0.3 * vitality + 0.1
                        matches.append({
                            "need_node": node_id_n,
                            "offer_node": node_id_o,
                            "item": item_needed,
                            "quantity_needed": quantity_needed,
                            "quantity_offered": quantity_offered,
                            "matched_at": datetime.datetime.utcnow().isoformat(),
                            "score": round(score, 3),
                            "route": generate_route(node_id_n, node_id_o),
                        })

    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches


# ─── Admin Protected ──────────────────────────────────────────────
@app.post("/admin")
def do_admin_action(x_admin_token: str = Header(...)):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"message": "✅ Admin action authorized"}
