-- Data retention policies for OKX HFT infrastructure
-- This file contains TTL policies for different data types

-- Raw ticks retention: 30 days
ALTER TABLE hft_data.raw_ticks MODIFY TTL timestamp + INTERVAL 30 DAY;

-- 1-second aggregated data retention: 90 days
ALTER TABLE hft_analytics.agg_1s MODIFY TTL timestamp + INTERVAL 90 DAY;

-- 1-minute aggregated data retention: 1 year
ALTER TABLE hft_analytics.agg_1m MODIFY TTL timestamp + INTERVAL 1 YEAR;

-- Create compression policy for older data
ALTER TABLE hft_data.raw_ticks MODIFY SETTINGS storage_policy = 'old_data_policy';

-- Create storage policy for different retention periods
CREATE STORAGE POLICY IF NOT EXISTS old_data_policy
AS STORAGE 'default'
TO 'default'
MOVE TO 'default' AFTER 7 DAY;

-- Create compression settings for better storage efficiency
ALTER TABLE hft_data.raw_ticks MODIFY SETTINGS 
    compression_codec = 'LZ4',
    min_bytes_for_wide_part = 0,
    min_rows_for_wide_part = 0;
