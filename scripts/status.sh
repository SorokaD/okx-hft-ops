#!/bin/bash

# OKX HFT Infrastructure Status Script
# This script shows the status of all services

echo "📊 OKX HFT Infrastructure Status"
echo "================================"

# Navigate to docker-compose directory
cd "$(dirname "$0")/../docker-compose"

# Show container status
echo ""
echo "🐳 Container Status:"
docker-compose ps

echo ""
echo "💾 Volume Status:"
docker volume ls | grep -E "(clickhouse|minio|prometheus|grafana)"

echo ""
echo "🌐 Service Health Checks:"

# Check ClickHouse
if curl -s http://localhost:8123/ping > /dev/null 2>&1; then
    echo "  ✅ ClickHouse: Running"
else
    echo "  ❌ ClickHouse: Not responding"
fi

# Check MinIO
if curl -s http://localhost:9000/minio/health/live > /dev/null 2>&1; then
    echo "  ✅ MinIO: Running"
else
    echo "  ❌ MinIO: Not responding"
fi

# Check Prometheus
if curl -s http://localhost:9090/-/ready > /dev/null 2>&1; then
    echo "  ✅ Prometheus: Running"
else
    echo "  ❌ Prometheus: Not responding"
fi

# Check Grafana
if curl -s http://localhost:3001/api/health > /dev/null 2>&1; then
    echo "  ✅ Grafana: Running"
else
    echo "  ❌ Grafana: Not responding"
fi

# Check MLflow
if curl -s http://localhost:5000/health > /dev/null 2>&1; then
    echo "  ✅ MLflow: Running"
else
    echo "  ❌ MLflow: Not responding"
fi

echo ""
echo "🔗 Service URLs:"
echo "  ClickHouse:     http://localhost:8124"
echo "  MinIO Console:  http://localhost:9001"
echo "  Prometheus:     http://localhost:9090"
echo "  Grafana:        http://localhost:3001"
echo "  MLflow:         http://localhost:5000"
echo "  Node Exporter:  http://localhost:9100"
echo "  CH Exporter:    http://localhost:9116"
