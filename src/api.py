from fastapi import FastAPI
import database as db

app = FastAPI(title="Funding Rate Arbitrage API", version="1.0.0")


@app.get("/api/v1/top-pairs")
async def get_top_pairs():
    pairs = await db.get_top_pairs()
    return {"data": pairs, "count": len(pairs)}
