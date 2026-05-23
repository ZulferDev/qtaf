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
    sb = get_supabase()
    sb.table("historical_market_data").insert(rows).execute()


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
    sb = get_supabase()
    now = datetime.now(timezone.utc).isoformat()
    pairs_incoming = {r["pair"] for r in rows}
    existing = sb.table("top_arbitrage_pairs").select("pair").execute()
    for row in existing.data or []:
        if row["pair"] not in pairs_incoming:
            sb.table("top_arbitrage_pairs").delete().eq("pair", row["pair"]).execute()
    for row in rows:
        row["updated_at"] = now
        pair = row["pair"]
        found = (
            sb.table("top_arbitrage_pairs")
            .select("id")
            .eq("pair", pair)
            .execute()
        )
        if found.data:
            sb.table("top_arbitrage_pairs").update(row).eq("pair", pair).execute()
        else:
            sb.table("top_arbitrage_pairs").insert(row).execute()


async def delete_old_market_data(days: int = 30) -> int:
    sb = get_supabase()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    resp = sb.table("historical_market_data").delete().lt("timestamp", cutoff).execute()
    return len(resp.data or [])


async def get_top_pairs(limit: int = 10) -> list[dict]:
    sb = get_supabase()
    resp = (
        sb.table("top_arbitrage_pairs")
        .select("*")
        .order("total_score", desc=True)
        .limit(limit)
        .execute()
    )
    return resp.data or []
