# 🌍 Arka Relief Mesh (Backend)

**Arka** is a decentralized humanitarian coordination system for warzones and crisis regions.  
It connects people in need (`needs.json`) with those who can offer help (`offers.json`),  
matches them, and logs fulfilled deliveries (`log.json`) in a transparent and trustworthy way.

This repo contains the backend API built in FastAPI + Python.

---

## 🚀 Features

- Submit needs from crisis nodes
- Submit offers from allies, medics, drivers, donors
- Match offers to needs in real time
- Log fulfilled deliveries
- Ready for deployment on Railway, Render, or Fly.io

---

## 💠 How to Use (Locally)

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn main:app --reload
```

Then open your browser at:
```
http://127.0.0.1:8000/docs
```

---

## 📡 Endpoints

| Method | Endpoint      | Description                  |
|--------|---------------|------------------------------|
| POST   | /needs        | Submit a need                |
| POST   | /offers       | Submit an offer              |
| GET    | /matches      | Get current matches          |
| (soon) | /fulfill      | Finalize a delivery log      |

---

## 🧲 Example JSON

See `/data/examples/needs.json` and `offers.json` for testing.

---

## 🛠️ Project Structure

```
arka-relief-mesh/
├── main.py             # FastAPI backend
├── requirements.txt    # Dependencies
├── Procfile            # Railway deployment config
├── data/
│   ├── needs/          # Stored need submissions
│   ├── offers/         # Stored offer submissions
│   └── logs/           # Fulfilled deliveries
```

---

## 🛍️ Vision

> Relief that moves at the speed of need.
>
> Built for trust, not control.  
> Built for people, not platforms.

This is version `0.1-alpha`. The work continues.

---

## ✨ License

MIT. Fork it. Use it. Share it. Just don’t let it sit still.
