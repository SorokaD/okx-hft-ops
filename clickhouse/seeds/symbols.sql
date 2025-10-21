-- Seed data for trading symbols
-- This file contains initial symbol configurations

INSERT INTO hft_data.symbols (symbol, exchange, base_asset, quote_asset, min_tick_size, min_lot_size, is_active) VALUES
('BTC-USDT', 'OKX', 'BTC', 'USDT', 0.01, 0.00001, 1),
('ETH-USDT', 'OKX', 'ETH', 'USDT', 0.01, 0.0001, 1),
('SOL-USDT', 'OKX', 'SOL', 'USDT', 0.001, 0.01, 1),
('ADA-USDT', 'OKX', 'ADA', 'USDT', 0.0001, 1, 1),
('DOT-USDT', 'OKX', 'DOT', 'USDT', 0.001, 0.1, 1),
('MATIC-USDT', 'OKX', 'MATIC', 'USDT', 0.0001, 1, 1),
('AVAX-USDT', 'OKX', 'AVAX', 'USDT', 0.001, 0.1, 1),
('LINK-USDT', 'OKX', 'LINK', 'USDT', 0.001, 0.1, 1),
('UNI-USDT', 'OKX', 'UNI', 'USDT', 0.001, 0.1, 1),
('ATOM-USDT', 'OKX', 'ATOM', 'USDT', 0.001, 0.1, 1);

-- Create symbols table if it doesn't exist
CREATE TABLE IF NOT EXISTS hft_data.symbols (
    symbol String,
    exchange String,
    base_asset String,
    quote_asset String,
    min_tick_size Float64,
    min_lot_size Float64,
    is_active UInt8,
    created_at DateTime DEFAULT now()
) ENGINE = MergeTree()
ORDER BY (symbol, exchange)
SETTINGS index_granularity = 8192;
