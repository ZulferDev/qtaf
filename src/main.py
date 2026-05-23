import asyncio
import sys
import config
import database as db
import fetcher
from engine import run_quant_engine


async def main() -> None:
    data = await fetcher.fetch_all_data()
    if not data:
        print("No data fetched. Exiting.")
        return

    await db.insert_market_data(data)
    print(f"Ingested {len(data)} rows into historical_market_data")

    deleted = await db.delete_old_market_data(config.DATA_RETENTION_DAYS)
    print(f"Cleaned {deleted} rows older than {config.DATA_RETENTION_DAYS} days")

    top = await run_quant_engine(data)
    print(f"Computed & upserted {len(top)} top arbitrage pairs")

    await fetcher.close()


if __name__ == "__main__":
    asyncio.run(main())
