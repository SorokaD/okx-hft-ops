-- Materialized view for 1-second aggregation
-- Migration: 0003_mv_agg_1s.sql

-- Create materialized view for 1-second aggregation
CREATE MATERIALIZED VIEW IF NOT EXISTS hft_analytics.mv_agg_1s
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

-- Create materialized view for 1-minute aggregation
CREATE MATERIALIZED VIEW IF NOT EXISTS hft_analytics.mv_agg_1m
TO hft_analytics.agg_1m AS
SELECT
    toStartOfMinute(timestamp) as timestamp,
    symbol,
    exchange,
    first_value(close_price) as open_price,
    max(high_price) as high_price,
    min(low_price) as low_price,
    last_value(close_price) as close_price,
    sum(volume) as volume,
    sum(trade_count) as trade_count,
    sum(bid_volume) as bid_volume,
    sum(ask_volume) as ask_volume,
    avg(spread) as spread,
    now() as created_at
FROM hft_analytics.agg_1s
GROUP BY symbol, exchange, timestamp;
