#!/bin/bash

# OKX HFT Infrastructure Startup Script
# This script starts all services for the HFT infrastructure

set -e

echo "🚀 Starting OKX HFT Infrastructure..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Navigate to docker-compose directory
cd "$(dirname "$0")/../docker-compose"

echo "📦 Starting all services with Docker Compose..."

# Start all services
docker-compose up -d

echo "⏳ Waiting for services to be ready..."

# Wait for ClickHouse to be ready
echo "🔄 Waiting for ClickHouse..."
timeout 60 bash -c 'until docker exec clickhouse wget --no-verbose --tries=1 --spider http://localhost:8123/ping; do sleep 2; done'

# Wait for MinIO to be ready
echo "🔄 Waiting for MinIO..."
timeout 60 bash -c 'until docker exec minio curl -f http://localhost:9000/minio/health/live; do sleep 2; done'

# Wait for Prometheus to be ready
echo "🔄 Waiting for Prometheus..."
timeout 60 bash -c 'until curl -f http://localhost:9090/-/ready; do sleep 2; done'

echo "✅ All services are ready!"
echo ""
echo "🌐 Service URLs:"
echo "  ClickHouse:     http://localhost:8124"
echo "  MinIO Console:  http://localhost:9001 (admin/minioadmin123)"
echo "  Prometheus:     http://localhost:9090"
echo "  Grafana:        http://localhost:3001 (admin/admin)"
echo "  MLflow:         http://localhost:5000"
echo "  Redis:          localhost:6379"
echo "  Kafka:          localhost:9092"
echo "  Kafka UI:       http://localhost:8080"
echo "  Jupyter Lab:    http://localhost:8888 (token: hft123)"
echo "  Superset:       http://localhost:8081 (admin/admin)"
echo "  Airflow:        http://localhost:8082 (admin/admin)"
echo "  Node Exporter:  http://localhost:9100"
echo "  CH Exporter:    http://localhost:9116"
echo ""

# Run database migrations
echo "🔄 Running database migrations..."
cd ../clickhouse/tools
python migrate.py

echo "🎉 OKX HFT Infrastructure is ready!"
echo ""
echo "📊 To view logs: docker-compose -f ../docker-compose/docker-compose.yml logs -f"
echo "🛑 To stop: ./scripts/stop.sh"
