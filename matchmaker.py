from typing import List, Dict

def generate_route(need_node: str, offer_node: str) -> Dict[str, Any]:
    route = {
        "logistics_nodes": [],
        "estimated_travel_time": "unknown",
        "risk_score": 1.0
    }

    # Load known logistics nodes (posted via /log endpoint or elsewhere)
    logistics_candidates = load_folder(LOGS_DIR)

    for node in logistics_candidates:
        if node.get("type") == "logistics":
            route["logistics_nodes"].append(node.get("node_id"))

    if route["logistics_nodes"]:
        route["estimated_travel_time"] = f"{len(route['logistics_nodes']) * 30}m"
        route["risk_score"] = round(1.0 / len(route["logistics_nodes"]), 2)

    return route



def match_needs_to_offers(needs_store: List[Dict], offers_store: List[Dict]) -> List[Dict]:
    matches = []
    for need in needs_store:
        for offer in offers_store:
            if offer["item"].lower() == need["item"].lower() and offer["quantity"] >= need["quantity"]:
                match = {
                        "need_node": "node123",
                        "offer_node": "node456",
                        "item": "insulin",
                        "quantity_needed": 2,
                        "quantity_offered": 5,
                        "matched_at": "2025-07-21T...",
                         "route": {
                            "logistics_nodes": ["logiA", "logiB"],
                            "estimated_travel_time": "3h",
                            "risk_score": 0.7
                            }
                        }

                matches.append(match)
    return matches
