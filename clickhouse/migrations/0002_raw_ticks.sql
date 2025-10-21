-- Raw ticks table optimization and additional fields
-- Migration: 0002_raw_ticks.sql

-- Add additional fields to raw_ticks table
ALTER TABLE hft_data.raw_ticks ADD COLUMN IF NOT EXISTS order_id String;
ALTER TABLE hft_data.raw_ticks ADD COLUMN IF NOT EXISTS sequence_number UInt64;
ALTER TABLE hft_data.raw_ticks ADD COLUMN IF NOT EXISTS is_snapshot UInt8 DEFAULT 0;

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_raw_ticks_symbol_timestamp ON hft_data.raw_ticks (symbol, timestamp) TYPE minmax GRANULARITY 1;
CREATE INDEX IF NOT EXISTS idx_raw_ticks_exchange ON hft_data.raw_ticks (exchange) TYPE set(0) GRANULARITY 1;

-- Create materialized view for real-time aggregation
CREATE MATERIALIZED VIEW IF NOT EXISTS hft_data.raw_ticks_mv
TO hft_analytics.agg_1s AS
SELECT
    toStartOfSecond(timestamp) as timestamp,
    symbol,
    exchange,
    first_value(trade_price) as open_price,
    max(trade_price) as high_price,
    min(trade_price) as low_price,
    last_value(trade_price) as close_price,
    sum(trade_size) as volume,
    count() as trade_count,
    sumIf(trade_size, trade_side = 'buy') as bid_volume,
    sumIf(trade_size, trade_side = 'sell') as ask_volume,
    avg(ask_price - bid_price) as spread,
    now() as created_at
FROM hft_data.raw_ticks
WHERE trade_price > 0
GROUP BY symbol, exchange, timestamp;
