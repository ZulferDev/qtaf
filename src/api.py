from fastapi import FastAPI, Header, HTTPException
import config
import database as db
from fetcher import fetch_all_data, close
from engine import run_quant_engine

app = FastAPI(title="Funding Rate Arbitrage API", version="1.0.0")


def _verify_secret(authorization: str | None = None) -> None:
    if not config.API_SECRET:
        return
    if not authorization:
        raise HTTPException(401, "Missing Authorization header")
    token = authorization.removeprefix("Bearer ").strip()
    if token != config.API_SECRET:
        raise HTTPException(403, "Invalid secret")


@app.get("/api/v1/top-pairs")
async def get_top_pairs():
    pairs = await db.get_top_pairs()
    return {"data": pairs, "count": len(pairs)}


@app.post("/api/v1/run-engine")
async def run_engine(authorization: str | None = Header(None)):
    _verify_secret(authorization)

    data = await fetch_all_data()
    if not data:
        raise HTTPException(502, "No data fetched from exchange")

    await db.insert_market_data(data)

    deleted = await db.delete_old_market_data(config.DATA_RETENTION_DAYS)

    top = await run_quant_engine(data)

    await close()

    return {
        "status": "ok",
        "fetched": len(data),
        "cleaned": deleted,
        "top_pairs": top,
    }
