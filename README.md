# OKX HFT Ops

Infrastructure-as-Code repository for the OKX HFT (High-Frequency Trading) pet project.

## 📁 Repository Structure

```
okx-hft-ops/
├── config/                          # Configuration files
│   ├── grafana/                     # Grafana configuration
│   │   ├── grafana.ini              # Main config
│   │   ├── dashboards/              # Dashboard JSON files
│   │   └── provisioning/            # Auto-provisioning (datasources, dashboards)
│   ├── prometheus/                  # Prometheus configuration
│   │   ├── prometheus.yml           # Scrape configs
│   │   └── alert.rules.yml          # Alerting rules
│   ├── loki/                        # Loki & Promtail configuration
│   │   ├── loki-config.yml          # Loki config
│   │   └── promtail-config.yml      # Promtail config
│   └── superset/                    # Superset configuration
│       └── superset_config.py       # Python config
│
├── docker/                          # Docker Compose stacks
│   ├── docker-compose.traefik.yml   # Traefik reverse proxy + Let's Encrypt
│   ├── docker-compose.portainer.yaml# Portainer container management
│   ├── docker-compose.stack.yaml    # Monitoring: Prometheus, Grafana, Loki, Promtail
│   └── docker-compose.ml.yaml       # ML Platform: MinIO, MLflow, Superset, Airflow
│
├── airflow/                         # Airflow DAGs, logs, plugins
│   ├── dags/                        # DAG definitions
│   ├── logs/                        # Airflow logs (gitignored)
│   └── plugins/                     # Custom plugins
│
├── Dockerfile.mlflow                # Custom MLflow image with psycopg2 + boto3
├── Dockerfile.superset              # Custom Superset image with psycopg2
├── .env.example                     # Environment variables template
└── README.md                        # This file
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose v2
- Domain pointing to your server (*.tumar.tech in this example)

### 1. Create External Network

All services communicate through a shared external network `web`:

```bash
docker network create web || true
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your actual secrets and passwords
```

**Generate secure keys:**
```bash
# Fernet key for Airflow
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Random secret key
openssl rand -hex 32
```

### 3. Deploy Stacks

Deploy in order (Traefik should be first):

```bash
# 1. Traefik (reverse proxy, SSL termination)
docker compose -f docker/docker-compose.traefik.yml up -d

# 2. Portainer (optional, container management UI)
docker compose -f docker/docker-compose.portainer.yaml up -d

# 3. Monitoring Stack (Prometheus, Grafana, Loki, Promtail)
docker compose -f docker/docker-compose.stack.yaml --env-file .env up -d

# 4. ML Platform (MinIO, MLflow, Superset, Airflow)
docker compose -f docker/docker-compose.ml.yaml --env-file .env up -d
```

### 4. Initialize Superset (first time only)

After Superset container is healthy, create admin user:

```bash
# Load environment variables
source .env

# Create admin user
docker exec superset superset fab create-admin \
  --username "$SUPERSET_ADMIN_USER" \
  --firstname Admin \
  --lastname User \
  --email admin@example.com \
  --password "$SUPERSET_ADMIN_PASSWORD"

# Initialize database
docker exec superset superset db upgrade
docker exec superset superset init
```

## 🌐 Service Endpoints

After deployment, services are available at:

| Service    | URL                           | Description                        |
|------------|-------------------------------|------------------------------------|
| Traefik    | https://traefik.tumar.tech    | Reverse proxy dashboard            |
| Portainer  | https://portainer.tumar.tech  | Container management UI            |
| Grafana    | https://grafana.tumar.tech    | Metrics visualization & dashboards |
| Prometheus | https://prometheus.tumar.tech | Metrics storage & alerting         |
| MLflow     | https://mlflow.tumar.tech     | ML experiment tracking             |
| MinIO      | https://minio.tumar.tech      | S3-compatible object storage (UI)  |
| MinIO S3   | https://s3.tumar.tech         | S3 API endpoint                    |
| Superset   | https://superset.tumar.tech   | Data exploration & visualization   |
| Airflow    | https://airflow.tumar.tech    | Workflow orchestration             |

### Local Development Ports

For local testing without Traefik:

| Service    | Local URL              |
|------------|------------------------|
| Grafana    | http://localhost:3000  |
| Prometheus | http://localhost:9090  |
| MinIO      | http://localhost:9001  |
| MinIO S3   | http://localhost:9000  |
| MLflow     | http://localhost:5050  |
| Superset   | http://localhost:8088  |
| Airflow    | http://localhost:8080  |

## 📊 Stack Components

### Monitoring Stack (`docker-compose.stack.yaml`)

- **Prometheus** — Time-series database for metrics
- **Grafana** — Dashboards and visualization (credentials from `.env`)
- **Loki** — Log aggregation system
- **Promtail** — Log shipper (collects Docker logs)

### ML Platform (`docker-compose.ml.yaml`)

- **MinIO** — S3-compatible object storage for artifacts
- **MLflow** — ML experiment tracking and model registry (PostgreSQL backend)
- **Superset** — Business intelligence and data visualization
- **Airflow** — Workflow orchestration for data pipelines (LocalExecutor)

## 🔧 Management Commands

### View Logs

```bash
# All services in a stack
docker compose -f docker/docker-compose.stack.yaml logs -f

# Specific service
docker logs -f grafana
docker logs -f mlflow
```

### Stop Stacks

```bash
docker compose -f docker/docker-compose.ml.yaml down
docker compose -f docker/docker-compose.stack.yaml down
docker compose -f docker/docker-compose.portainer.yaml down
docker compose -f docker/docker-compose.traefik.yml down
```

### Reset with Data Loss

```bash
# Stop and remove volumes (DESTROYS DATA)
docker compose -f docker/docker-compose.ml.yaml down -v
docker compose -f docker/docker-compose.stack.yaml down -v
```

### Update Images

```bash
docker compose -f docker/docker-compose.stack.yaml pull
docker compose -f docker/docker-compose.stack.yaml up -d
```

## 🔐 Security Notes

1. **Change all default passwords** in `.env` before deploying to production
2. **Traefik dashboard** is protected with Basic Auth
3. **Prometheus** is protected with Basic Auth
4. **MLflow** has no built-in auth — consider adding Traefik middleware
5. Credentials are stored in `.env` file — **do not commit it to git**

## 📝 Notes

- Grafana datasources (Prometheus, Loki) are auto-provisioned via `config/grafana/provisioning/`
- Airflow uses LocalExecutor (no Redis/Celery) — suitable for small workloads
- MLflow stores artifacts in MinIO via S3 API
- All databases use PostgreSQL 16-alpine
- Superset admin user must be created manually after first deployment

## 🤝 Contributing

This is a personal pet project, but feel free to fork and adapt for your needs.
