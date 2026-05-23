import asyncio
import aiohttp
from typing import Optional
import config

BASE_URL = "https://contract.mexc.com/api/v1/contract"

_session: Optional[aiohttp.ClientSession] = None


async def _get_session() -> aiohttp.ClientSession:
    global _session
    if _session is None:
        _session = aiohttp.ClientSession()
    return _session


def _to_ccxt_symbol(contract_symbol: str) -> str:
    return contract_symbol.replace("_", "/") + ":USDT"


def _from_ccxt_symbol(ccxt_sym: str) -> str:
    return ccxt_sym.replace("/", "_").replace(":USDT", "")


async def fetch_all_data() -> list[dict]:
    session = await _get_session()
    async with session.get(f"{BASE_URL}/ticker") as resp:
        data = await resp.json()

    if not data.get("success"):
        raise RuntimeError(f"Mexc ticker API failed: {data}")

    tickers = data["data"]
    results = []
    for t in tickers:
        symbol = t.get("symbol", "")
        if not symbol.endswith("_USDT"):
            continue
        pair = _to_ccxt_symbol(symbol)
        pair = pair[:50] if len(pair) > 50 else pair
        results.append({
            "pair": pair,
            "price": t.get("lastPrice"),
            "volume": t.get("volume24"),
            "funding_rate": t.get("fundingRate"),
            "open_interest": t.get("holdVol"),
        })
    return results


async def close() -> None:
    global _session
    if _session:
        await _session.close()
        _session = None
