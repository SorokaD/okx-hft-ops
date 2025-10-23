#!/bin/bash

# MLflow Experiments Runner for OKX HFT Infrastructure
# This script runs MLflow experiments for HFT data analysis

set -e

echo "🧪 Running MLflow Experiments for HFT Infrastructure..."

# Navigate to mlflow experiments directory
cd "$(dirname "$0")/../mlflow/experiments"

# Check if Python dependencies are installed
if ! python -c "import mlflow, clickhouse_connect, sklearn" 2>/dev/null; then
    echo "📦 Installing Python dependencies..."
    pip install mlflow clickhouse-connect scikit-learn pandas numpy
fi

echo "🔄 Running price prediction experiments..."
python price_prediction.py

echo "🔄 Running strategy backtest experiments..."
python strategy_backtest.py

echo "✅ All MLflow experiments completed!"
echo ""
echo "🌐 View results at: http://localhost:5000"
echo "📊 MLflow UI: http://localhost:5000"
