-- Supabase SQL Schema for Crypto Funding Rate Arbitrage System

-- Table 1: Historical Market Data (lightweight, few days lookback)
CREATE TABLE IF NOT EXISTS historical_market_data (
    id BIGSERIAL PRIMARY KEY,
    pair VARCHAR(20) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    funding_rate DOUBLE PRECISION,
    open_interest DOUBLE PRECISION,
    volume DOUBLE PRECISION,
    price DOUBLE PRECISION
);

CREATE INDEX idx_hmd_pair_timestamp ON historical_market_data (pair, timestamp DESC);

-- Table 2: Top Arbitrage Pairs (latest calculated results)
CREATE TABLE IF NOT EXISTS top_arbitrage_pairs (
    id BIGSERIAL PRIMARY KEY,
    pair VARCHAR(20) NOT NULL UNIQUE,
    total_score DOUBLE PRECISION NOT NULL DEFAULT 0,
    momentum_score DOUBLE PRECISION NOT NULL DEFAULT 0,
    execution_score DOUBLE PRECISION NOT NULL DEFAULT 0,
    recommended_direction VARCHAR(10) NOT NULL DEFAULT 'NEUTRAL',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tap_score ON top_arbitrage_pairs (total_score DESC);
