from typing import Optional
from supabase import create_client, Client
import pandas as pd
from datetime import datetime, timedelta, timezone

import config

_supabase: Optional[Client] = None


def get_supabase() -> Client:
    global _supabase
    if _supabase is None:
        if not config.SUPABASE_URL or not config.SUPABASE_KEY:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_KEY must be set in environment"
            )
        _supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
    return _supabase


async def insert_market_data(rows: list[dict]) -> None:
    if not rows:
        return
    sb = get_supabase()
    sb.table("historical_market_data").insert(rows).execute()


async def get_historical_data(
    pair: str, hours: int = 24, limit: int = 100
) -> list[dict]:
    sb = get_supabase()
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    resp = (
        sb.table("historical_market_data")
        .select("*")
        .eq("pair", pair)
        .gte("timestamp", since.isoformat())
        .order("timestamp", desc=True)
        .limit(limit)
        .execute()
    )
    return resp.data or []


async def get_recent_market_data(
    pair: str, hours: int = 24
) -> pd.DataFrame:
    sb = get_supabase()
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    resp = (
        sb.table("historical_market_data")
        .select("*")
        .eq("pair", pair)
        .gte("timestamp", since.isoformat())
        .order("timestamp", desc=True)
        .execute()
    )
    return pd.DataFrame(resp.data) if resp.data else pd.DataFrame()


async def upsert_top_pairs(rows: list[dict]) -> None:
    if not rows:
        return
    sb = get_supabase()
    now = datetime.now(timezone.utc).isoformat()
    sb.table("top_arbitrage_pairs").delete().gte("id", 0).execute()
    for row in rows:
        row["updated_at"] = now
        sb.table("top_arbitrage_pairs").insert(row).execute()


async def delete_old_market_data(days: int = 30) -> int:
    sb = get_supabase()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    resp = sb.table("historical_market_data").delete().lt("timestamp", cutoff).execute()
    return len(resp.data or [])


async def get_top_pairs(limit: int = 10, direction: str | None = None) -> list[dict]:
    sb = get_supabase()
    query = sb.table("top_arbitrage_pairs").select("*")
    if direction:
        query = query.eq("recommended_direction", direction.upper())
    resp = query.order("total_score", desc=True).limit(limit).execute()
    return resp.data or []
