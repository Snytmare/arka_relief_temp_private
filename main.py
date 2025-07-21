# main.py

from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

import os, json, uuid, datetime
from typing import List, Dict, Any
from dotenv import load_dotenv


load_dotenv()
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

# ─── Init App ──────────────────────────────────────────────────────
app = FastAPI()

# CORS
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

# ─── Rate Limiting (optional but included) ─────────────────────────
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"message": "Too many requests, slow down."}
    )

# ─── Directories ───────────────────────────────────────────────────
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

@app.post("/needs")
async def post_needs(req: Request):
    payload = await req.json()
    payload["_received_at"] = datetime.datetime.utcnow().isoformat()
    fn = save_json(payload, NEEDS_DIR, "need")
    return {"status": "need stored", "file": fn}

@app.get("/needs")
def get_needs():
    return load_folder(NEEDS_DIR)

@app.post("/offers")
async def post_offers(req: Request):
    payload = await req.json()
    payload["_received_at"] = datetime.datetime.utcnow().isoformat()
    fn = save_json(payload, OFFERS_DIR, "offer")
    return {"status": "offer stored", "file": fn}

@app.get("/offers")
def get_offers():
    return load_folder(OFFERS_DIR)

@app.post("/log")
async def post_log(req: Request):
    payload = await req.json()
    payload["_logged_at"] = datetime.datetime.utcnow().isoformat()
    fn = save_json(payload, LOGS_DIR, "log")
    return {"status": "log stored", "file": fn}

@app.get("/log")
def get_log():
    return load_folder(LOGS_DIR)

@app.get("/matches")
def get_matches():
    needs = load_folder(NEEDS_DIR)
    offers = load_folder(OFFERS_DIR)
    matches = []
    for n in needs:
        for need_item in n.get("needs", []):
            for o in offers:
                for offer_item in o.get("offers", []):
                    if (
                        need_item.get("item", "").lower()
                        == offer_item.get("item", "").lower()
                        and offer_item.get("quantity", 0)
                        >= need_item.get("quantity", 0)
                    ):
                        matches.append({
                            "need_node": n.get("node_id"),
                            "offer_node": o.get("node_id"),
                            "item": need_item.get("item"),
                            "quantity_needed": need_item.get("quantity"),
                            "quantity_offered": offer_item.get("quantity"),
                            "matched_at": datetime.datetime.utcnow().isoformat()
                        })
    return matches

# ─── Secure Admin Endpoint ─────────────────────────────────────────
@app.post("/admin")
def do_admin_action(x_admin_token: str = Header(...)):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return {"message": "✅ Admin action authorized"}

#force reset