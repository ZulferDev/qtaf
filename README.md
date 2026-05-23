---
title: Crypto Funding Rate Arbitrage API
emoji: 📈
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
---

# Crypto Funding Rate Arbitrage System

Data Collection, Processing, and Delivery backend for Crypto Funding Rate Arbitrage.

## Tech Stack

- Python 3.10+, ccxt (async), pandas, numpy
- Supabase (PostgreSQL)
- GitHub Actions (cron every 30 min)
- FastAPI (Render / Hugging Face Spaces)

## Setup

1. Copy `.env.example` and fill in Supabase credentials.
2. Run `schema.sql` in your Supabase SQL editor.
3. Install deps: `pip install -r requirements.txt`
4. Run locally: `python src/main.py`
5. Start API: `uvicorn src.api:app --reload`

## Endpoints

- `GET /api/v1/top-pairs` — Returns top 10 arbitrage opportunities.

## GitHub Secrets

- `SUPABASE_URL`
- `SUPABASE_KEY`
