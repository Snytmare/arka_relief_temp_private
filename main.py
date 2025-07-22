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
