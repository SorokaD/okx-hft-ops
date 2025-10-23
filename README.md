# OKX HFT Infrastructure
upd 23.10.25 все поднимается, все работает

High-frequency trading infrastructure for OKX exchange data processing with ClickHouse, monitoring, and object storage.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │───▶│   ClickHouse    │───▶│   Analytics     │
│   (OKX API)     │    │   (Time Series) │    │   (Grafana)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   MinIO S3      │
                       │   (Object Store)│
                       └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.9+
- Make (optional, for convenience commands)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd okx-hft-infra
```

### 2. Start All Services

```bash
# Using Make (recommended)
make setup

# Or manually
chmod +x scripts/*.sh
./scripts/start.sh
```

### 3. Verify Installation

```bash
# Check status
make status

# Run tests
make test
```

## 📊 Services

| Service | URL | Credentials |
|---------|-----|-------------|
| **ClickHouse** | http://localhost:8123 | default (hft_user/hft_password)  |
| **MinIO Console** | http://localhost:9001 | minioadmin / minioadmin123 |
| **Grafana** | http://localhost:3001 | admin / admin |
| **MLflow** | http://localhost:5000 | - |
| **Redis** | localhost:6379 | - |
| **Kafka** | localhost:9093 | - |
| **Kafka UI** | http://localhost:8080 | - |
| **Jupyter Lab** | http://localhost:8888 | token: hft123 |
| **Superset** | http://localhost:8081 | admin / admin |
| **Airflow** | http://localhost:8082 | admin / admin |
| **Prometheus** | http://localhost:9092 | - |
| **Node Exporter** | http://localhost:9100 | - |
| **ClickHouse Exporter** | http://localhost:9116 | - |

## 🛠️ Management Commands

### Using Make (Recommended)

```bash
make help          # Show all available commands
make start         # Start all services
make stop          # Stop all services
make clean         # Remove all data
make status        # Show service status
make migrate       # Run database migrations
make test          # Run tests
make mlflow-experiments  # Run MLflow experiments
make logs          # Show all logs
make logs-mlflow   # Show MLflow logs
make restart       # Restart services
```

### Using Scripts Directly

```bash
./scripts/start.sh    # Start all services
./scripts/stop.sh     # Stop all services
./scripts/clean.sh    # Remove all data
./scripts/status.sh   # Show status
./scripts/migrate.sh  # Run migrations
./scripts/test.sh     # Run tests
```

## 📁 Project Structure

```
okx-hft-infra/
├── docker-compose/          # Local development environment
│   ├── docker-compose.yml   # Main orchestration file
│   ├── clickhouse/          # ClickHouse configuration
│   ├── minio/              # MinIO configuration
│   └── monitoring/         # Prometheus + Grafana
├── clickhouse/             # Database schemas and logic
│   ├── migrations/         # SQL migrations
│   ├── seeds/             # Initial data
│   ├── views/             # Materialized views
│   ├── tests/             # Data quality tests
│   └── tools/             # Python utilities
├── scripts/               # Management scripts
├── k8s/                   # Kubernetes manifests
├── terraform/             # Infrastructure as Code
├── ansible/               # Configuration management
└── ci/                    # CI/CD pipelines
```

## 🗄️ Database Schema

### Raw Data Tables

- **`hft_data.raw_ticks`** - Raw tick data from OKX
- **`hft_data.symbols`** - Trading symbols reference

### Aggregated Data Tables

- **`hft_analytics.agg_1s`** - 1-second aggregated data
- **`hft_analytics.agg_1m`** - 1-minute aggregated data

### Materialized Views

- **`mv_agg_1s`** - Real-time 1-second aggregation
- **`mv_agg_1m`** - Real-time 1-minute aggregation

## 🔧 Development

### Adding New Migrations

1. Create new SQL file in `clickhouse/migrations/`
2. Follow naming convention: `XXXX_description.sql`
3. Run migrations: `make migrate`

### Adding New Tests

1. Add SQL queries to `clickhouse/tests/`
2. Run tests: `make test`

### Monitoring

- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **ClickHouse Metrics**: http://localhost:9116

## 🚀 Production Deployment

### Kubernetes

```bash
# Deploy to Kubernetes
kubectl apply -f k8s/manifests/
```

### Terraform (Hetzner)

```bash
cd terraform/hetzner
terraform init
terraform plan
terraform apply
```

### Ansible

```bash
# Deploy to servers
ansible-playbook -i ansible/inventories/prod ansible/site.yml
```

## 📈 Performance

- **Raw ticks**: ~1M rows/second ingestion
- **Storage**: Compressed with LZ4
- **Retention**: 30 days raw, 1 year aggregated
- **Query performance**: Sub-second for most analytics

## 🔍 Troubleshooting

### Common Issues

1. **Port conflicts**: Check if ports 8123, 9000, 3000, 9090 are free
2. **Memory issues**: Ensure Docker has at least 4GB RAM
3. **Permission errors**: Run `chmod +x scripts/*.sh`

### Logs

```bash
# View all logs
make logs

# View specific service logs
make logs-clickhouse
make logs-minio
make logs-monitoring
```

### Reset Everything

```bash
make clean
make setup
```

## 📚 Documentation

- [ClickHouse Documentation](https://clickhouse.com/docs/)
- [MinIO Documentation](https://docs.min.io/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.