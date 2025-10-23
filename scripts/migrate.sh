#!/bin/bash

# Database Migration Script
# This script runs ClickHouse migrations

set -e

echo "🔄 Running ClickHouse migrations..."

# Navigate to clickhouse tools directory
cd "$(dirname "$0")/../clickhouse/tools"

# Check if Python dependencies are installed
if ! python -c "import clickhouse_connect" 2>/dev/null; then
    echo "📦 Installing Python dependencies..."
    pip install clickhouse-connect pandas
fi

# Run migrations
python migrate.py

echo "✅ Migrations completed!"
