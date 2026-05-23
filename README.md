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
- FastAPI (Hugging Face Spaces / Docker)

## Setup

1. Copy `.env.example` and fill in credentials.
2. Run `schema.sql` in your Supabase SQL editor.
3. Install deps: `pip install -r requirements.txt`
4. Run locally: `python src/main.py`
5. Start API: `uvicorn src.api:app --reload`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/top-pairs` | Returns top 10 arbitrage opportunities |
| `POST` | `/api/v1/run-engine` | Trigger pipeline manually (requires `Authorization: Bearer <API_SECRET>`) |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | ✅ | Supabase project URL |
| `SUPABASE_KEY` | ✅ | Supabase anon or service_role key |
| `API_SECRET` | ❌ | Secret token for /run-engine endpoint |

## Cron via Webhook (cron-job.org)

Disable GitHub Actions cron and use [cron-job.org](https://cron-job.org) for more reliable scheduling:

1. Go to https://cron-job.org and create a free account
2. Create a new cron job:
   - **URL**: `https://Hdevpem-qtaf-api.hf.space/api/v1/run-engine`
   - **Method**: `POST`
   - **Headers**: `Authorization: Bearer <your_api_secret>`
   - **Interval**: Every 30 minutes
   - **Time of day**: Any
3. Save — it will hit your endpoint every 30 minutes

cron-job.org is free, has 99.9% uptime, and will retry on failure.
