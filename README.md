Коротко: да, третий репо имеет смысл — но лучше не “только ClickHouse”, а общий **infra**-репозиторий, где ClickHouse — один из модулей. Это долговечнее: его будут использовать и collector, и executor, и дальше туда удобно добавить MinIO, Airflow/MLflow, мониторинг, IaC и т.д.

# Как назвать

* **okx-hft-infra** — мой фаворит (будет жить дольше любой конкретной БД).
* Альтернативы, если хочешь жёстко про ДWH:

  * **okx-hft-warehouse**
  * **okx-hft-clickhouse** (если точно только CH и ничего лишнего)

# Зачем выносить отдельно

**Плюсы**

* Единая точка правды для схем, ретеншна, материализованных вьюх.
* Независимый релизный цикл (обновил DDL/TTL без релиза collector/executor).
* Чистые CI/CD пайплайны: миграции → тесты → деплой CH.
* Проще переиспользовать для стендов (dev/stage/prod).

**Минусы**

* Третий репо = ещё один пайплайн и релизы.
* Если инфраструктуры мало и меняется редко, можно было бы держать как папку в одном из существующих репо. Но ты точно будешь наращивать стек → отдельный репо окупится.

# Рекомендуемая структура (**okx-hft-infra**)

```
okx-hft-infra/
  README.md
  docker-compose/             # локальный стенд
    clickhouse/
      docker-compose.yml
      users.xml
      config.d/*.xml
      macros.xml
    minio/
    monitoring/               # prometheus + grafana + exporters
  k8s/                         # если/когда выйдешь в k8s
    clickhouse-operator/       # манифесты Altinity Operator
    manifests/
  terraform/
    hetzner/                   # vpc, servers, volumes, firewall
  ansible/
    roles/clickhouse/
    inventories/{dev,stage,prod}
  clickhouse/                  # всё, что касается схем и логики
    migrations/
      0001_init.sql
      0002_raw_ticks.sql
      0003_mv_agg_1s.sql
      ...
    seeds/                     # стартовые справочники
    retention/
      policies.sql             # TTL/политики хранения
    views/
      mv_agg_1s.sql
      mv_agg_1m.sql
    tests/
      test_rowcounts.sql       # простые проверки
    tools/
      migrate.py               # простой раннер миграций
      ch_client.py
  ci/
    github-actions/
      ch_migrate.yml
      compose_smoke.yml
```

# Что именно положить в `clickhouse/`

* **`migrations/`**: чистые SQL-миграции (версионированные, idempotent).
* **`retention/policies.sql`**: TTL для `raw_ticks` (7 дней) и для агрегатов (3 месяца).
* **`views/`**: материализованные вьюхи (например, 50–100 мс агрегаты → 1s → 1m).
* **Лёгкий миграционный раннер** (`tools/migrate.py`):

  * хранит версию в таблице `_schema_migrations`
  * применяет только новые файлы
  * умеет `dry-run` и `--env dev/stage/prod`

# CI/CD идея

* При PR: поднять `docker-compose` CH, прогнать миграции + быстрые тесты.
* В main: деплой миграций на dev → прогон smoke-тестов → вручную promote на stage/prod.
* Теги релизов `infra-vX.Y.Z` синхронизируются с collector/executor релизами в описании.

# Когда оставить без отдельного репо

* Если ты точно решил “только локальный docker-compose” и “никакой IaC/мониторинг”, и изменения бывают раз в несколько месяцев — тогда можно держать `infra/` (или `clickhouse/`) как папку в **okx-hft-collector**. Но это временно и хуже масштабируется.

---

**Итого:** создай **`okx-hft-infra`**. Внутри — модуль `clickhouse/` со схемами, миграциями, TTL и матвьюхами, плюс docker-compose/k8s/terraform/ansible. Если прям хочется имя про БД — **`okx-hft-warehouse`** или **`okx-hft-clickhouse`**, но я бы брал **infra** для будущего роста.

