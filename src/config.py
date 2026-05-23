import os
from typing import Optional

SUPABASE_URL: Optional[str] = os.environ.get("SUPABASE_URL")
SUPABASE_KEY: Optional[str] = os.environ.get("SUPABASE_KEY")

DATA_RETENTION_DAYS: int = 30
EXCHANGE: str = "mexc"
LOOKBACK_HOURS: int = 24
TOP_PAIRS_LIMIT: int = 10
CRON_INTERVAL_MINUTES: int = 30

FUNDING_RED_FLAG_THRESHOLD: float = 0.003  # 0.3% per 8h
OI_SIGNIFICANT_PCT: float = 5.0           # 5% OI change threshold
VOLUME_MA_PERIOD: int = 20
