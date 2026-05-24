import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import Any
import config
import database as db
from fetcher import fetch_spot_pairs


async def compute_scores(current_data: list[dict]) -> list[dict]:
    spot_bases = await fetch_spot_pairs()
    top_rows = []
    for row in current_data:
        pair = row["pair"]
        base = pair.split("/")[0]
        if "STOCK" in base.upper():
            continue
        if base not in spot_bases:
            continue
        hist_df = await db.get_recent_market_data(pair, config.LOOKBACK_HOURS)
        if hist_df.empty:
            momentum = _compute_momentum_fallback(row)
        else:
            momentum = _compute_momentum(row, hist_df)
        execution = _compute_execution(row, hist_df)
        total = momentum + execution
        fr = row.get("funding_rate") or 0
        if fr > 0.0001:
            direction = "SHORT"
        elif fr < -0.0001:
            direction = "LONG"
        else:
            direction = "NEUTRAL"
        top_rows.append({
            "pair": pair,
            "total_score": round(total, 4),
            "momentum_score": round(momentum, 4),
            "execution_score": round(execution, 4),
            "recommended_direction": direction,
        })
    top_rows.sort(key=lambda r: r["total_score"], reverse=True)
    return top_rows[: config.TOP_PAIRS_LIMIT]


def _compute_momentum(row: dict, hist: pd.DataFrame) -> float:
    score = 0.0
    current_fr = row.get("funding_rate") or 0
    current_oi = row.get("open_interest") or 0
    current_vol = row.get("volume") or 0
    current_price = row.get("price") or 0

    if hist.empty or len(hist) < 2:
        return 0.0

    hist_sorted = hist.sort_values("timestamp")

    # Funding trend
    prev_fr = hist_sorted["funding_rate"].iloc[-1]
    if pd.isna(prev_fr):
        prev_fr = 0.0
    if current_fr > prev_fr:
        score += 2.0

    # OI increasing significantly
    prev_oi = hist_sorted["open_interest"].iloc[-1]
    if pd.isna(prev_oi):
        prev_oi = 0.0
    if prev_oi > 0 and current_oi > 0:
        oi_pct = ((current_oi - prev_oi) / prev_oi) * 100
        if oi_pct > config.OI_SIGNIFICANT_PCT:
            score += 2.0

    # Volume above MA
    if len(hist_sorted) >= config.VOLUME_MA_PERIOD:
        vol_ma = hist_sorted["volume"].tail(config.VOLUME_MA_PERIOD).mean()
        if pd.notna(vol_ma) and current_vol > vol_ma:
            score += 1.0

    # Price breaking key resistance/support
    period = max(config.VOLUME_MA_PERIOD, 5)
    recent_high = hist_sorted["price"].tail(period).max()
    recent_low = hist_sorted["price"].tail(period).min()
    if pd.notna(recent_high) and pd.notna(recent_low):
        if current_price > recent_high:
            score += 1.0
        elif current_price < recent_low:
            score -= 1.0

    # Funding rate red flag
    if abs(current_fr) > config.FUNDING_RED_FLAG_THRESHOLD:
        score -= 2.0

    return max(score, -2.0)


def _compute_momentum_fallback(row: dict) -> float:
    score = 0.0
    current_fr = abs(row.get("funding_rate") or 0)
    if current_fr > config.FUNDING_RED_FLAG_THRESHOLD:
        score -= 2.0
    return max(score, -2.0)


def _compute_execution(row: dict, hist: pd.DataFrame) -> float:
    fr = abs(row.get("funding_rate") or 0)
    vol = row.get("volume") or 0
    price = row.get("price") or 0

    # Yield spread (funding rate minus estimated round-trip fees)
    yield_score = min((fr - config.MAKER_FEE_RATE * 2) * 100 * 10, 5.0)
    yield_score = max(yield_score, 1.0)

    # Liquidity score based on volume + OI depth proxy
    if vol > 0 and price > 0:
        usd_volume = vol * price
        if usd_volume > 50_000_000:
            liq_score = 5.0
        elif usd_volume > 10_000_000:
            liq_score = 4.0
        elif usd_volume > 5_000_000:
            liq_score = 3.0
        elif usd_volume > 1_000_000:
            liq_score = 2.0
        else:
            liq_score = 1.0
    else:
        liq_score = 1.0

    # Volatility via ATR approximation
    if not hist.empty and len(hist) > 1:
        hist_sorted = hist.sort_values("timestamp")
        high = hist_sorted["price"].max()
        low = hist_sorted["price"].min()
        prev_close = hist_sorted["price"].iloc[-1] if len(hist_sorted) > 1 else price
        atr = abs(high - low)
        atr_pct = atr / prev_close if prev_close > 0 else 0
        vol_score = 5.0 - min(atr_pct * 50, 4.0)
    else:
        vol_score = 3.0

    exec_score = (yield_score * 0.4) + (liq_score * 0.4) + (vol_score * 0.2)
    return max(min(exec_score, 5.0), 1.0)


async def run_quant_engine(current_data: list[dict]) -> list[dict]:
    top = await compute_scores(current_data)
    await db.upsert_top_pairs(top)
    return top
