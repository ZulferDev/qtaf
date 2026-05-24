import sys
sys.path.insert(0, "src")

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta

import config
config.SUPABASE_URL = "test"
config.SUPABASE_KEY = "test"

from engine import (
    _compute_momentum,
    _compute_momentum_fallback,
    _compute_execution,
)
from fetcher import _to_ccxt_symbol


def _hist(rows: list) -> pd.DataFrame:
    return pd.DataFrame(rows)


def _ts(hours_ago: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()


class TestComputeMomentum:
    def test_less_than_two_rows_returns_zero(self):
        hist = _hist([{"timestamp": _ts(8), "funding_rate": 0.0001, "open_interest": 100, "volume": 100, "price": 100}])
        row = {"funding_rate": 0.0002, "open_interest": 200, "volume": 200, "price": 200}
        assert _compute_momentum(row, hist) == 0.0

    def test_empty_hist_returns_zero(self):
        hist = _hist([])
        row = {"funding_rate": 0.0002, "open_interest": 200, "volume": 200, "price": 200}
        assert _compute_momentum(row, hist) == 0.0

    def test_funding_trend_up_adds_two(self):
        hist = _hist([
            {"timestamp": _ts(16), "funding_rate": 0.00005, "open_interest": 100, "volume": 100, "price": 100},
            {"timestamp": _ts(8), "funding_rate": 0.00007, "open_interest": 100, "volume": 100, "price": 100},
        ])
        row = {"funding_rate": 0.00010, "open_interest": 100, "volume": 100, "price": 100}
        assert _compute_momentum(row, hist) == 2.0

    def test_funding_trend_down_adds_zero(self):
        hist = _hist([
            {"timestamp": _ts(16), "funding_rate": 0.00010, "open_interest": 100, "volume": 100, "price": 100},
            {"timestamp": _ts(8), "funding_rate": 0.00008, "open_interest": 100, "volume": 100, "price": 100},
        ])
        row = {"funding_rate": 0.00007, "open_interest": 100, "volume": 100, "price": 100}
        assert _compute_momentum(row, hist) == 0.0

    def test_oi_spike_adds_two(self):
        hist = _hist([
            {"timestamp": _ts(16), "funding_rate": 0.0, "open_interest": 100, "volume": 100, "price": 100},
            {"timestamp": _ts(8), "funding_rate": 0.0, "open_interest": 100, "volume": 100, "price": 100},
        ])
        row = {"funding_rate": 0.0, "open_interest": 200, "volume": 100, "price": 100}
        m = _compute_momentum(row, hist)
        assert m == 2.0

    def test_oi_small_change_no_points(self):
        hist = _hist([
            {"timestamp": _ts(16), "funding_rate": 0.0, "open_interest": 100, "volume": 100, "price": 100},
            {"timestamp": _ts(8), "funding_rate": 0.0, "open_interest": 100, "volume": 100, "price": 100},
        ])
        row = {"funding_rate": 0.0, "open_interest": 102, "volume": 100, "price": 100}
        assert _compute_momentum(row, hist) == 0.0

    def test_volume_above_ma_adds_one(self):
        hist = _hist([
            {"timestamp": _ts(16 + i), "funding_rate": 0.0, "open_interest": 100, "volume": 100, "price": 100}
            for i in range(config.VOLUME_MA_PERIOD, 0, -1)
        ])
        row = {"funding_rate": 0.0, "open_interest": 100, "volume": 500, "price": 100}
        m = _compute_momentum(row, hist)
        assert m == 1.0

    def test_price_breakout_adds_one(self):
        hist = _hist([
            {"timestamp": _ts(16 + i), "funding_rate": 0.0, "open_interest": 100, "volume": 100, "price": 100}
            for i in range(config.VOLUME_MA_PERIOD, 0, -1)
        ])
        row = {"funding_rate": 0.0, "open_interest": 100, "volume": 100, "price": 500}
        m = _compute_momentum(row, hist)
        assert m == 1.0

    def test_price_breakdown_subtracts_one(self):
        hist = _hist([
            {"timestamp": _ts(16 + i), "funding_rate": 0.0, "open_interest": 100, "volume": 100, "price": 100}
            for i in range(config.VOLUME_MA_PERIOD, 0, -1)
        ])
        row = {"funding_rate": 0.0, "open_interest": 100, "volume": 100, "price": 1}
        m = _compute_momentum(row, hist)
        assert m == -1.0

    def test_red_flag_subtracts_two(self):
        hist = _hist([
            {"timestamp": _ts(16), "funding_rate": 0.005, "open_interest": 100, "volume": 100, "price": 100},
            {"timestamp": _ts(8), "funding_rate": 0.005, "open_interest": 100, "volume": 100, "price": 100},
        ])
        row = {"funding_rate": 0.004, "open_interest": 100, "volume": 100, "price": 100}
        assert _compute_momentum(row, hist) == -2.0

    def test_max_score_six(self):
        hist = _hist([
            {"timestamp": _ts(16 + i), "funding_rate": 0.00001 * i, "open_interest": 100 * i, "volume": 100 * i, "price": 100 * i}
            for i in range(config.VOLUME_MA_PERIOD, 0, -1)
        ])
        row = {"funding_rate": 0.0002, "open_interest": 5000, "volume": 5000, "price": 5000}
        m = _compute_momentum(row, hist)
        assert m == 6.0

    def test_min_score_minus_two(self):
        hist = _hist([
            {"timestamp": _ts(16), "funding_rate": 0.1, "open_interest": 100, "volume": 100, "price": 100},
            {"timestamp": _ts(8), "funding_rate": 0.1, "open_interest": 100, "volume": 100, "price": 100},
        ])
        row = {"funding_rate": 0.1, "open_interest": 100, "volume": 100, "price": 100}
        m = _compute_momentum(row, hist)
        assert m >= -2.0
        assert m == -2.0

    def test_nan_funding_rate_handled(self):
        hist = _hist([
            {"timestamp": _ts(16), "funding_rate": np.nan, "open_interest": 100, "volume": 100, "price": 100},
            {"timestamp": _ts(8), "funding_rate": 0.0001, "open_interest": 100, "volume": 100, "price": 100},
        ])
        row = {"funding_rate": 0.0002, "open_interest": 100, "volume": 100, "price": 100}
        m = _compute_momentum(row, hist)
        assert m == 2.0

    def test_missing_field_in_row(self):
        hist = _hist([
            {"timestamp": _ts(16), "funding_rate": 0.0, "open_interest": 100, "volume": 100, "price": 100},
            {"timestamp": _ts(8), "funding_rate": 0.0, "open_interest": 100, "volume": 100, "price": 100},
        ])
        row: dict = {}
        m = _compute_momentum(row, hist)
        assert m == -1.0

    def test_zero_values_in_hist(self):
        hist = _hist([
            {"timestamp": _ts(16), "funding_rate": 0.0, "open_interest": 0.0, "volume": 0.0, "price": 0.0},
            {"timestamp": _ts(8), "funding_rate": 0.0, "open_interest": 0.0, "volume": 0.0, "price": 0.0},
        ])
        row = {"funding_rate": 0.0, "open_interest": 0.0, "volume": 0.0, "price": 0.0}
        m = _compute_momentum(row, hist)
        assert m == 0.0


class TestComputeMomentumFallback:
    def test_no_red_flag_returns_zero(self):
        row = {"funding_rate": 0.0001}
        assert _compute_momentum_fallback(row) == 0.0

    def test_red_flag_returns_minus_two(self):
        row = {"funding_rate": 0.004}
        assert _compute_momentum_fallback(row) == -2.0

    def test_missing_funding_rate_returns_zero(self):
        row: dict = {}
        assert _compute_momentum_fallback(row) == 0.0

    def test_negative_funding_rate_red_flag(self):
        row = {"funding_rate": -0.004}
        assert _compute_momentum_fallback(row) == -2.0

    def test_zero_funding_rate(self):
        row = {"funding_rate": 0.0}
        assert _compute_momentum_fallback(row) == 0.0


class TestComputeExecution:
    def test_no_data_returns_above_one(self):
        row = {"funding_rate": 0.0, "volume": 0, "price": 0}
        hist = _hist([])
        e = _compute_execution(row, hist)
        assert 0 < e < 5.0

    def test_high_liquidity_yields_high_score(self):
        row = {"funding_rate": 0.001, "volume": 1_000_000, "price": 100}
        hist = _hist([
            {"timestamp": _ts(16), "price": 100},
            {"timestamp": _ts(8), "price": 100},
        ])
        e = _compute_execution(row, hist)
        assert 1.0 <= e <= 5.0

    def test_low_liquidity_yields_low_score(self):
        row = {"funding_rate": 0.00001, "volume": 100, "price": 1}
        hist = _hist([
            {"timestamp": _ts(16), "price": 1},
            {"timestamp": _ts(8), "price": 1},
        ])
        e = _compute_execution(row, hist)
        assert 1.0 <= e <= 5.0

    def test_high_volatility_lowers_score(self):
        row = {"funding_rate": 0.001, "volume": 1_000_000, "price": 100}
        high_vol = _hist([
            {"timestamp": _ts(16), "price": 50},
            {"timestamp": _ts(8), "price": 150},
        ])
        low_vol = _hist([
            {"timestamp": _ts(16), "price": 99},
            {"timestamp": _ts(8), "price": 101},
        ])
        e_high = _compute_execution(row, high_vol)
        e_low = _compute_execution(row, low_vol)
        assert e_high <= e_low

    def test_missing_fields_default_to_zero(self):
        row: dict = {}
        hist = _hist([])
        e = _compute_execution(row, hist)
        assert 1.0 <= e <= 5.0

    def test_hist_with_single_row(self):
        row = {"funding_rate": 0.001, "volume": 1_000_000, "price": 100}
        hist = _hist([{"timestamp": _ts(8), "price": 100}])
        e = _compute_execution(row, hist)
        assert 1.0 <= e <= 5.0


class TestToCcxtSymbol:
    def test_standard_conversion(self):
        assert _to_ccxt_symbol("BTC_USDT") == "BTC/USDT:USDT"

    def test_multi_underscore(self):
        assert _to_ccxt_symbol("NFLXSTOCK_USDT") == "NFLXSTOCK/USDT:USDT"

    def test_empty_string(self):
        assert _to_ccxt_symbol("") == ":USDT"
