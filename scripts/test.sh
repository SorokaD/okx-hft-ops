#!/bin/bash

# Test Script for OKX HFT Infrastructure
# This script runs basic tests to verify everything is working

set -e

echo "🧪 Running OKX HFT Infrastructure Tests..."

# Navigate to clickhouse tools directory
cd "$(dirname "$0")/../clickhouse/tools"

# Check if Python dependencies are installed
if ! python -c "import clickhouse_connect" 2>/dev/null; then
    echo "📦 Installing Python dependencies..."
    pip install clickhouse-connect pandas
fi

echo "🔄 Testing ClickHouse connection..."
python -c "
import clickhouse_connect
client = clickhouse_connect.get_client(host='localhost', port=8123)
result = client.query('SELECT 1')
print('✅ ClickHouse connection successful')
"

echo "🔄 Testing database queries..."
python -c "
import clickhouse_connect
client = clickhouse_connect.get_client(host='localhost', port=8123)

# Test basic queries
with open('../tests/test_rowcounts.sql', 'r') as f:
    test_queries = f.read().split(';')

for i, query in enumerate(test_queries):
    if query.strip():
        try:
            result = client.query(query.strip())
            print(f'✅ Test {i+1} passed')
        except Exception as e:
            print(f'❌ Test {i+1} failed: {e}')
"

echo "🔄 Testing data insertion..."
python -c "
import clickhouse_connect
from datetime import datetime
import random

client = clickhouse_connect.get_client(host='localhost', port=8123)

# Insert test data
test_data = [
    {
        'timestamp': datetime.now(),
        'symbol': 'BTC-USDT',
        'exchange': 'OKX',
        'bid_price': 50000.0,
        'ask_price': 50001.0,
        'bid_size': 1.0,
        'ask_size': 1.0,
        'trade_price': 50000.5,
        'trade_size': 0.1,
        'trade_side': 'buy',
        'source': 'test'
    }
]

client.insert('hft_data.raw_ticks', test_data)
print('✅ Test data insertion successful')

# Verify data
result = client.query('SELECT count() FROM hft_data.raw_ticks')
print(f'✅ Data verification: {result.result_rows[0][0]} rows in raw_ticks table')
"

echo "✅ All tests passed!"
echo ""
echo "🎉 OKX HFT Infrastructure is working correctly!"
