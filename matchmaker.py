from typing import List, Dict

def match_needs_to_offers(needs_store: List[Dict], offers_store: List[Dict]) -> List[Dict]:
    matches = []
    for need in needs_store:
        for offer in offers_store:
            if offer["item"].lower() == need["item"].lower() and offer["quantity"] >= need["quantity"]:
                match = {
                    "need_node": need["node_id"],
                    "offer_node": offer["node_id"],
                    "item": need["item"],
                    "quantity_needed": need["quantity"],
                    "quantity_offered": offer["quantity"],
                    "urgency": need["urgency"]
                }
                matches.append(match)
    return matches
