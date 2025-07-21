# Deployment Guide

## Backend

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Start Server**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

3. **Deploy (Railway/Render/Heroku)**

## Frontend

- Use Netlify or Vercel for static `index.html`

## Environment Notes

- `.env` should never be committed
- Use secure CORS settings
