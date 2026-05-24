from fastapi import FastAPI, Query, HTTPException

import database as db

app = FastAPI(title="Funding Rate Arbitrage API", version="1.0.0")

VALID_DIRECTIONS = {"LONG", "SHORT", "NEUTRAL"}


@app.get("/api/v1/top-pairs")
async def get_top_pairs(direction: str | None = Query(None)):
    if direction and direction.upper() not in VALID_DIRECTIONS:
        raise HTTPException(422, f"Invalid direction. Valid: {', '.join(VALID_DIRECTIONS)}")
    pairs = await db.get_top_pairs(direction=direction)
    return {"data": pairs, "count": len(pairs)}


@app.get("/api/v1/historical/{pair:path}")
async def get_historical_data(
    pair: str,
    hours: int = Query(24, ge=1, le=720),
    limit: int = Query(100, ge=1, le=1000),
):
    data = await db.get_historical_data(pair, hours=hours, limit=limit)
    return {"data": data, "count": len(data)}
