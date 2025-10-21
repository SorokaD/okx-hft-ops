-- Initial database setup for OKX HFT infrastructure
-- Migration: 0001_init.sql

-- Create databases
CREATE DATABASE IF NOT EXISTS hft_data;
CREATE DATABASE IF NOT EXISTS hft_analytics;

-- Create basic tables for raw tick data
CREATE TABLE IF NOT EXISTS hft_data.raw_ticks (
    timestamp DateTime64(3),
    symbol String,
    exchange String,
    bid_price Float64,
    ask_price Float64,
    bid_size Float64,
    ask_size Float64,
    trade_price Float64,
    trade_size Float64,
    trade_side Enum8('buy' = 1, 'sell' = 2),
    source String,
    created_at DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (symbol, timestamp)
SETTINGS index_granularity = 8192;

-- Create aggregated tables for 1-second intervals
CREATE TABLE IF NOT EXISTS hft_analytics.agg_1s (
    timestamp DateTime,
    symbol String,
    exchange String,
    open_price Float64,
    high_price Float64,
    low_price Float64,
    close_price Float64,
    volume Float64,
    trade_count UInt32,
    bid_volume Float64,
    ask_volume Float64,
    spread Float64,
    created_at DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (symbol, timestamp)
SETTINGS index_granularity = 8192;

-- Create aggregated tables for 1-minute intervals
CREATE TABLE IF NOT EXISTS hft_analytics.agg_1m (
    timestamp DateTime,
    symbol String,
    exchange String,
    open_price Float64,
    high_price Float64,
    low_price Float64,
    close_price Float64,
    volume Float64,
    trade_count UInt32,
    bid_volume Float64,
    ask_volume Float64,
    spread Float64,
    created_at DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (symbol, timestamp)
SETTINGS index_granularity = 8192;
