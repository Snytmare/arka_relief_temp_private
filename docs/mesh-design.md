# Global Relief Mesh – Design Principles

The Global Relief Mesh is a decentralized humanitarian aid network designed to respond dynamically to crisis zones.

## Core Ideas

- Everything is a node
- Needs are JSONs
- No central authority
- Live Matching

## Key Elements

- **Node Definition**
```json
{
  "node_id": "auto or self-assigned",
  "location": "optional or encrypted",
  "needs": ["insulin", "formula"],
  "offers": ["blankets", "cash"],
  "urgency": 0.95,
  "vitality": 1.0,
  "last_updated": "2025-07-21T22:58:00Z"
}
```

- **Routing Engine**
  - Urgency
  - Distance & Risk
  - Availability
  - Trust metrics

- **Trust Without Surveillance**
  - Peer-signed vouches
  - Fulfilled-action logs
  - Dimensional reputation
