#!/usr/bin/env python3
"""
ClickHouse client utility for HFT infrastructure
Provides convenient methods for data operations
"""

import clickhouse_connect
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

class ClickHouseClient:
    def __init__(self, host='localhost', port=8123, user='default', password='', database='default'):
        self.client = clickhouse_connect.get_client(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
    
    def insert_raw_ticks(self, ticks_data: List[Dict[str, Any]]):
        """Insert raw tick data"""
        if not ticks_data:
            return
        
        self.client.insert('hft_data.raw_ticks', ticks_data)
        print(f"Inserted {len(ticks_data)} raw ticks")
    
    def get_latest_ticks(self, symbol: str, limit: int = 100) -> pd.DataFrame:
        """Get latest ticks for a symbol"""
        query = f"""
            SELECT *
            FROM hft_data.raw_ticks
            WHERE symbol = '{symbol}'
            ORDER BY timestamp DESC
            LIMIT {limit}
        """
        return self.client.query_df(query)
    
    def get_aggregated_data(self, symbol: str, start_time: datetime, end_time: datetime, interval: str = '1s') -> pd.DataFrame:
        """Get aggregated data for a symbol in a time range"""
        if interval == '1s':
            table = 'hft_analytics.agg_1s'
        elif interval == '1m':
            table = 'hft_analytics.agg_1m'
        else:
            raise ValueError("Interval must be '1s' or '1m'")
        
        query = f"""
            SELECT *
            FROM {table}
            WHERE symbol = '{symbol}'
            AND timestamp >= '{start_time}'
            AND timestamp <= '{end_time}'
            ORDER BY timestamp
        """
        return self.client.query_df(query)
    
    def get_symbol_stats(self, symbol: str) -> Dict[str, Any]:
        """Get statistics for a symbol"""
        query = f"""
            SELECT 
                count() as total_ticks,
                min(timestamp) as first_tick,
                max(timestamp) as last_tick,
                avg(trade_price) as avg_price,
                min(trade_price) as min_price,
                max(trade_price) as max_price,
                sum(trade_size) as total_volume
            FROM hft_data.raw_ticks
            WHERE symbol = '{symbol}'
        """
        result = self.client.query(query)
        return dict(zip([col[0] for col in result.column_names], result.result_rows[0]))
    
    def get_top_symbols_by_volume(self, limit: int = 10) -> pd.DataFrame:
        """Get top symbols by trading volume"""
        query = f"""
            SELECT 
                symbol,
                count() as tick_count,
                sum(trade_size) as total_volume,
                avg(trade_price) as avg_price
            FROM hft_data.raw_ticks
            WHERE timestamp >= now() - INTERVAL 1 HOUR
            GROUP BY symbol
            ORDER BY total_volume DESC
            LIMIT {limit}
        """
        return self.client.query_df(query)
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old data based on retention policy"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        # This would typically be handled by TTL policies
        # but can be used for manual cleanup
        query = f"""
            ALTER TABLE hft_data.raw_ticks DELETE
            WHERE timestamp < '{cutoff_date}'
        """
        self.client.command(query)
        print(f"Cleaned up data older than {days_to_keep} days}")

if __name__ == "__main__":
    # Example usage
    client = ClickHouseClient()
    
    # Get top symbols by volume
    top_symbols = client.get_top_symbols_by_volume(5)
    print("Top 5 symbols by volume:")
    print(top_symbols)
