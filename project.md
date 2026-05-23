# PROJECT OVERVIEW
You are an expert Quantitative Trading Developer. Your task is to build "Group 1", the Data Collection, Processing, and Delivery backend for a Crypto Funding Rate Arbitrage system.

This system is strictly designed for a 100% FREE cloud architecture. It must be efficient, avoid exchange rate limits, and use standard Python quant libraries.

# TECH STACK & ARCHITECTURE
- **Language**: Python 3.10+
- **Data Ingestion & Calculation**: `ccxt` (async), `pandas`, `numpy`
- **Database**: Supabase (PostgreSQL) using `supabase-py`
- **Automation/Cron**: GitHub Actions (running every 30 minutes)
- **API Delivery**: `FastAPI` (to be deployed on Render/Hugging Face Spaces)

# SCORING LOGIC (THE QUANT ENGINE)
The system calculates a "Total Quant Score" for each crypto perpetual pair based on two stages.
Total Score Max = 11.0.

**Stage 1: Momentum Score (Max +6, Min -2)**
Calculate deltas using historical data from the database.
- Funding Trend increasing: +2 points
- Open Interest (OI) increasing significantly: +2 points
- Volume above 20-period MA: +1 point
- Price breaking key resistance/support: +1 point
- Funding rate extreme (> 0.3% per 8h): -2 points (Red Flag penalty)

**Stage 2: Execution Score (Scale 1 to 5, Weighted)**
- Yield Spread (Funding rate minus estimated maker/taker fees): Weight 0.4
- Liquidity (Order book depth / Volume to determine slippage): Weight 0.4
- Risk/Volatility (ATR - Average True Range): Weight 0.2
Formula: `Execution_Score = (Yield * 0.4) + (Liquidity * 0.4) + (Volatility * 0.2)`

**Final Calculation:**
`Total_Quant_Score = Momentum_Score + Execution_Score`

# DIRECTORY STRUCTURE
Please structure the repository as follows:
/
├── .github/
│   └── workflows/
│       └── quant_engine_cron.yml  # GitHub Actions cron scheduler
├── src/
│   ├── config.py                  # Environment variables loading
│   ├── database.py                # Supabase connection & queries
│   ├── fetcher.py                 # CCXT data fetching logic
│   ├── engine.py                  # Pandas scoring logic & math
│   └── api.py                     # FastAPI application
├── requirements.txt
└── README.md

# IMPLEMENTATION STEPS (Execute sequentially)

## Step 1: Database Schema & Setup
Create the SQL schema for Supabase. We need two tables:
1. `historical_market_data`: Stores timestamp, pair symbol, funding_rate, open_interest, volume, price. (Keep it lightweight, we only need a few days of lookback).
2. `top_arbitrage_pairs`: Stores the latest calculated results (pair, total_score, momentum_score, execution_score, recommended_direction, updated_at).
Write the SQL commands in a `schema.sql` file and setup `database.py`.

## Step 2: Data Ingestion (fetcher.py)
Write an async function using `ccxt` to fetch current Funding Rate, Open Interest, Volume, and Price for top 50 USDT perpetual pairs on Mexc. Include error handling and rate-limit safety (sleep between batches if necessary). 

## Step 3: Quant Engine (engine.py)
Write the core logic. 
1. Fetch the last 24h of data from the `historical_market_data` table.
2. Merge with current data fetched from `fetcher.py`.
3. Use `pandas` to calculate the deltas (OI change, Volume MA, Funding trend).
4. Apply the exact Scoring Logic defined above.
5. Save/Update the top 10 highest-scoring pairs into the `top_arbitrage_pairs` table.

## Step 4: Automation Wrapper (GitHub Actions)
Write the `quant_engine_cron.yml`. It should trigger every 30 minutes, setup Python, install `requirements.txt`, and run a `main.py` script that ties Step 2 and Step 3 together. Make sure it uses GitHub Secrets for the Supabase URL and API Key.

## Step 5: Delivery API (api.py)
Create a lightweight FastAPI app. It should have a single endpoint `GET /api/v1/top-pairs`. This endpoint ONLY queries the `top_arbitrage_pairs` table from Supabase and returns it as a clean JSON response. No heavy calculation is done here.

Please acknowledge this plan. Let's start with Step 1. Give me the SQL schema and the database.py code.
