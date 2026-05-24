import asyncio
import sys
import config
import database as db
import fetcher
from engine import run_quant_engine


async def main() -> None:
    try:
        data = await fetcher.fetch_all_data()
        if not data:
            print("No data fetched. Exiting.")
            return

        await db.delete_old_market_data(config.DATA_RETENTION_DAYS)
        print(f"Cleaned rows older than {config.DATA_RETENTION_DAYS} days")

        await db.insert_market_data(data)
        print(f"Ingested {len(data)} rows into historical_market_data")

        top = await run_quant_engine(data)
        print(f"Computed & upserted {len(top)} top arbitrage pairs")
    except Exception as e:
        print(f"ERROR: {e}")
        raise
    finally:
        await fetcher.close()


if __name__ == "__main__":
    asyncio.run(main())
