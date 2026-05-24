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

## GitHub Secrets

- `SUPABASE_URL`
- `SUPABASE_KEY`

## Cron via Webhook (cron-job.org)

Trigger GitHub Actions workflow via [cron-job.org](https://cron-job.org) setiap 8 jam (00:00, 08:00, 16:00 UTC).

### 1. Buat GitHub Personal Access Token

Buka https://github.com/settings/tokens → **Generate new token (classic)**:
- Scope: `repo` (full control)
- Copy tokennya, simpan

### 2. Setup di cron-job.org

1. Buka https://cron-job.org → Create account (free)
2. **Create Cronjob**:
   - **URL**: `https://api.github.com/repos/ZulferDev/qtaf/dispatches`
   - **Method**: `POST`
   - **Headers**:
     ```
     Authorization: Bearer <github_pat>
     Accept: application/vnd.github+json
     Content-Type: application/json
     ```
   - **Body**:
     ```json
     {"event_type": "run-engine"}
     ```
   - **Interval**: Every 8 hours
   - **Time of day**: 00:00, 08:00, 16:00
3. Save

cron-job.org akan POST ke GitHub API → trigger `repository_dispatch` → jalankan workflow di runner GitHub.
