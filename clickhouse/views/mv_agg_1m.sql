-- Materialized view for 1-minute aggregation
-- This view aggregates 1-second data into 1-minute intervals

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
