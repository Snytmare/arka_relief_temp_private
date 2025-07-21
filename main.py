# main.py

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os, json, uuid, datetime
from typing import List, Dict, Any

app = FastAPI()

# ─── CORS ────────────────────────────────────────────────────────────────────
# allow all origins for now; later you can lock to your Netlify URL if you like
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ─────────────────────────────────────────────────────────────────────────────

# Ensure data directories exist
BASE_DIR = "data"
NEEDS_DIR = os.path.join(BASE_DIR, "needs")
OFFERS_DIR = os.path.join(BASE_DIR, "offers")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

for d in (NEEDS_DIR, OFFERS_DIR, LOGS_DIR):
    os.makedirs(d, exist_ok=True)

def save_json(obj: Dict[str, Any], folder: str, prefix: str) -> str:
    """Save obj to folder/prefix_<uuid>.json"""
    fn = f"{prefix}_{uuid.uuid4().hex}.json"
    with open(os.path.join(folder, fn), "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)
    return fn

def load_folder(folder: str) -> List[Dict[str, Any]]:
    """Load all JSON files in folder as a list of dicts."""
    out = []
    for fn in sorted(os.listdir(folder)):
        if fn.endswith(".json"):
            with open(os.path.join(folder, fn), "r", encoding="utf-8") as f:
                out.append(json.load(f))
    return out

# ─── /needs ───────────────────────────────────────────────────────────────────
@app.post("/needs")
async def post_needs(req: Request):
    payload = await req.json()
    payload["_received_at"] = datetime.datetime.utcnow().isoformat()
    fn = save_json(payload, NEEDS_DIR, "need")
    return {"status": "need stored", "file": fn}

@app.get("/needs")
def get_needs():
    return load_folder(NEEDS_DIR)

# ─── /offers ──────────────────────────────────────────────────────────────────
@app.post("/offers")
async def post_offers(req: Request):
    payload = await req.json()
    payload["_received_at"] = datetime.datetime.utcnow().isoformat()
    fn = save_json(payload, OFFERS_DIR, "offer")
    return {"status": "offer stored", "file": fn}

@app.get("/offers")
def get_offers():
    return load_folder(OFFERS_DIR)

# ─── /matches ─────────────────────────────────────────────────────────────────
@app.get("/matches")
def get_matches():
    needs = load_folder(NEEDS_DIR)
    offers = load_folder(OFFERS_DIR)
    matches = []
    for n in needs:
        # adjust these keys to match your JSON schema exactly
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

# ─── /log ─────────────────────────────────────────────────────────────────────
@app.post("/log")
async def post_log(req: Request):
    payload = await req.json()
    payload["_logged_at"] = datetime.datetime.utcnow().isoformat()
    fn = save_json(payload, LOGS_DIR, "log")
    return {"status": "log stored", "file": fn}

@app.get("/log")
def get_log():
    return load_folder(LOGS_DIR)



#forece reset