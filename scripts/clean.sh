#!/bin/bash

# OKX HFT Infrastructure Clean Script
# This script removes all containers, volumes, and data

set -e

echo "🧹 Cleaning OKX HFT Infrastructure..."

# Navigate to docker-compose directory
cd "$(dirname "$0")/../docker-compose"

# Stop and remove all containers, networks, and volumes
docker-compose down -v --remove-orphans

# Remove any remaining containers
docker container prune -f

# Remove any remaining volumes
docker volume prune -f

echo "✅ All data cleaned!"
echo ""
echo "🚀 To start fresh: ./scripts/start.sh"
