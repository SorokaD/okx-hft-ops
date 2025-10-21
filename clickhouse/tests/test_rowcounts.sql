-- Test queries to verify data integrity and row counts
-- This file contains basic tests for the HFT infrastructure

-- Test 1: Check if raw_ticks table has data
SELECT 
    'raw_ticks' as table_name,
    count() as row_count,
    min(timestamp) as earliest_timestamp,
    max(timestamp) as latest_timestamp
FROM hft_data.raw_ticks;

-- Test 2: Check if 1-second aggregated data is being generated
SELECT 
    'agg_1s' as table_name,
    count() as row_count,
    min(timestamp) as earliest_timestamp,
    max(timestamp) as latest_timestamp
FROM hft_analytics.agg_1s;

-- Test 3: Check if 1-minute aggregated data is being generated
SELECT 
    'agg_1m' as table_name,
    count() as row_count,
    min(timestamp) as earliest_timestamp,
    max(timestamp) as latest_timestamp
FROM hft_analytics.agg_1m;

-- Test 4: Verify data consistency between raw and aggregated data
SELECT 
    'data_consistency_check' as test_name,
    count() as raw_ticks_count,
    (SELECT count() FROM hft_analytics.agg_1s) as agg_1s_count,
    (SELECT count() FROM hft_analytics.agg_1m) as agg_1m_count
FROM hft_data.raw_ticks;

-- Test 5: Check for data quality issues
SELECT 
    'data_quality_check' as test_name,
    countIf(trade_price <= 0) as invalid_prices,
    countIf(trade_size <= 0) as invalid_sizes,
    countIf(symbol = '') as empty_symbols
FROM hft_data.raw_ticks;
