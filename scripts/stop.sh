#!/bin/bash

# OKX HFT Infrastructure Stop Script
# This script stops all services

set -e

echo "🛑 Stopping OKX HFT Infrastructure..."

# Navigate to docker-compose directory
cd "$(dirname "$0")/../docker-compose"

# Stop all services
docker-compose down

echo "✅ All services stopped!"
echo ""
echo "💡 To start again: ./scripts/start.sh"
echo "🗑️  To remove all data: ./scripts/clean.sh"
