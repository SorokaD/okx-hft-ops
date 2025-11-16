OKX HFT Ops (okx-hft-ops)

Назначение
- Этот репозиторий — узел операций/инфраструктуры/мониторинга для пет‑проекта OKX HFT.
- Здесь нет бизнес‑логики трейдинга — только инфраструктура, мониторинг и сопутствующие сервисы.
- Связанные репозитории: `okx-hft-collector`, `okx-hft-executor`, `okx-hft-timescaledb`.

Что входит
- MinIO — объектное хранилище (артефакты, данные)
- MLflow — трекинг ML‑экспериментов (артефакты в MinIO)
- Prometheus — сбор метрик
- Loki + Promtail — сбор и хранение логов контейнеров
- Grafana — дашборды по метрикам и логам
- Superset — BI/аналитика
- Опционально: Nginx reverse‑proxy для доступа ко всем UI через один порт

Архитектура (Ops‑узел)
- Общая сеть Docker: `hft_network`
- Сервисы:
  - `minio`: объектное хранилище (в т.ч. бакет `mlflow` для артефактов)
  - `mlflow`: сервер экспериментов (SQLite backend, артефакты в S3/MinIO)
  - `prometheus`: сбор метрик из сервисов
  - `loki`: хранилище логов
  - `promtail`: агент, отправляющий docker‑логи в Loki
  - `grafana`: дашборды (datasource: Prometheus и Loki)
  - `superset`: BI
  - `reverse-proxy` (опция): единая точка входа по HTTP

Быстрый старт (локально)
1) Подготовить окружение:
   - Скопируйте `.env.example` в `.env` и задайте надёжные секреты.
2) Запустить стек:
   - `docker compose up -d`
3) Доступ к UI (порты/пути по умолчанию):
   - Grafana: через reverse‑proxy http://localhost:8080/grafana (прямой порт 3000 не публикуется)
   - Prometheus: http://localhost:9090
   - Loki (API): http://localhost:3100
   - MLflow: http://localhost:5000 (или через reverse‑proxy http://localhost:8080/mlflow)
   - MinIO Console: http://localhost:9001, S3 endpoint: http://localhost:9000 (или http://localhost:8080/minio)
   - Superset: http://localhost:8088 (или через reverse‑proxy http://localhost:8080/superset)

Примечания
- Для MLflow требуется бакет `mlflow` в MinIO. Создайте его один раз в консоли MinIO (http://localhost:9001).
- Grafana автоматически провиженит источники данных (Prometheus, Loki) и подхватывает дашборды из `grafana/dashboards/`.
- Promtail собирает логи всех docker‑контейнеров хоста и отправляет их в Loki.
- Prometheus пытается скрапить стандартные эндпоинты сервисов; если сервис не экспортирует метрики, он может быть в состоянии DOWN — это ожидаемо.

Следующие шаги
- Airflow стек в `airflow/` с примерными DAG’ами
- Отдельные docker‑compose файлы для MLflow и Superset в `mlflow/` и `superset/`
- IaC: `terraform/` (Hetzner Cloud пример) и `ansible/` (bootstrap роли)

Сервисы и порты (по умолчанию)
- MinIO API: 9000, MinIO Console: 9001
- MLflow: 5000
- Prometheus: 9090
- Loki: 3100
- Grafana: доступ через reverse‑proxy на 8080 (`/grafana`) — прямой порт не маппится
- Superset: 8088
- Reverse‑proxy (опция): 8080

Переменные окружения
- Все чувствительные значения задаются через `.env` (см. шаблон `.env.example`).
- Для MLflow артефактов используются `MLFLOW_S3_ENDPOINT_URL`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `MLFLOW_ARTIFACT_ROOT`.

Обновления
- Стек ориентирован на локальный запуск для разработки/отладки инфраструктуры OKX HFT.
- В продакшене предусмотрено вынесение сервисов, хранение данных на выделенных томах, мониторинг и алертинг через Prometheus/Grafana, логи в Loki.



---
Вот короткие описания.  

### Сервисы `okx-hft-ops`

* **MinIO**
  Объектное хранилище (аналог S3). Храним артефакты ML (модели, датасеты, логи), к нему ходит MLflow как в S3.

* **MLflow**
  Трекер экспериментов и реестр моделей. Логируем метрики, параметры, версии моделей, сохраняем артефакты в MinIO.

* **Prometheus**
  Сбор метрик со всех сервисов (ops-нод, баз данных, приложений). Источник данных для мониторинга и алёртов.

* **Grafana**
  Визуализация метрик и логов. Дашборды по состоянию collector/executor, БД, ops-сервисов, инфраструктуры.

* **Loki**
  Хранилище логов (log aggregation). Принимает логи от promtail, даёт возможность удобно искать их через Grafana.

* **Promtail**
  Агент сбора логов. Читает docker-логи контейнеров и отправляет их в Loki.

* **Superset**
  BI и аналитика. Делаем дашборды и аналитические отчёты по данным (стакан, трейды, фичи, PnL и т.д.).

* **Reverse-proxy (Nginx)**
  Единая точка входа к веб-интерфейсам (Grafana, Superset, MLflow, MinIO и др.). Упрощает маршрутизацию и в будущем — авторизацию/TLS.

