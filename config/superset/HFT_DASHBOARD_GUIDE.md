# HFT Dashboard Guide for Apache Superset

## Tumar HFT Analytics Platform

Данный гайд описывает создание аналитических дашбордов для HFT/крипто-данных в Apache Superset.

---

## 📊 Доступные визуализации

После настройки Superset поддерживает следующие типы графиков:

### Time Series (ECharts)

| Тип | Название в UI | Применение в HFT |
|-----|---------------|------------------|
| `echarts_timeseries_line` | Time-series Line Chart | Цена, PnL во времени |
| `echarts_timeseries_bar` | Time-series Bar Chart | Объём трейдов |
| `echarts_timeseries_scatter` | Time-series Scatter | Отдельные трейды |
| `mixed_timeseries` | **Mixed Time-Series** | ⭐ Dual-axis: цена + объём |
| `echarts_timeseries_step` | Time-series Step Line | Orderbook changes |

### Распределения и статистика

| Тип | Название в UI | Применение в HFT |
|-----|---------------|------------------|
| `echarts_histogram` | **Histogram** | ⭐ Распределение latency |
| `echarts_boxplot` | Box Plot | Статистика спредов |
| `dist_bar` | Distribution Bar | Распределение по категориям |

### Heatmaps и матрицы

| Тип | Название в UI | Применение в HFT |
|-----|---------------|------------------|
| `echarts_heatmap` | **Heatmap** | ⭐ Orderbook depth, volume profile |
| `pivot_table_v2` | Pivot Table | Агрегация по времени/цене |

### Gauges и KPI

| Тип | Название в UI | Применение в HFT |
|-----|---------------|------------------|
| `echarts_gauge` | Gauge Chart | Текущая latency, fill rate |
| `big_number_total` | Big Number | Общий PnL, количество трейдов |
| `big_number` | Big Number with Trendline | PnL с трендом |

### Прочие полезные

| Тип | Название в UI | Применение в HFT |
|-----|---------------|------------------|
| `table` | Table | Детали трейдов, ордеров |
| `echarts_radar` | Radar Chart | Сравнение стратегий |
| `echarts_sankey` | Sankey Chart | Flow analysis (buy→sell) |
| `echarts_treemap` | Treemap | Breakdown по инструментам |

---

## 🗄️ Примеры SQL-запросов для TimescaleDB

### 1. OHLCV данные (свечи)

```sql
-- Агрегация трейдов в OHLCV свечи (1-минутные)
SELECT 
    time_bucket('1 minute', timestamp) AS bucket,
    symbol,
    first(price, timestamp) AS open,
    max(price) AS high,
    min(price) AS low,
    last(price, timestamp) AS close,
    sum(quantity) AS volume,
    count(*) AS trade_count
FROM trades
WHERE 
    timestamp >= {{ from_dttm }} 
    AND timestamp < {{ to_dttm }}
    {% if filter_values('symbol') %}
    AND symbol IN {{ filter_values('symbol') | where_in }}
    {% endif %}
GROUP BY bucket, symbol
ORDER BY bucket DESC
```

### 2. Orderbook Depth (для Heatmap)

```sql
-- Snapshot orderbook для heatmap визуализации
SELECT 
    time_bucket('1 second', timestamp) AS time_bucket,
    price_level,
    side,
    sum(quantity) AS total_quantity
FROM orderbook_snapshots
WHERE 
    timestamp >= {{ from_dttm }}
    AND timestamp < {{ to_dttm }}
    AND symbol = '{{ filter_values("symbol")[0] | default("BTC-USDT") }}'
GROUP BY time_bucket, price_level, side
ORDER BY time_bucket, price_level
```

### 3. Latency Distribution

```sql
-- Распределение latency для гистограммы
SELECT 
    latency_ms,
    count(*) AS frequency
FROM pipeline_metrics
WHERE 
    timestamp >= {{ from_dttm }}
    AND timestamp < {{ to_dttm }}
    AND metric_type = 'order_latency'
GROUP BY latency_ms
ORDER BY latency_ms
```

### 4. Trading Metrics Summary

```sql
-- Сводные метрики за период
SELECT 
    time_bucket('1 hour', timestamp) AS hour,
    symbol,
    count(*) FILTER (WHERE side = 'buy') AS buy_count,
    count(*) FILTER (WHERE side = 'sell') AS sell_count,
    sum(quantity) FILTER (WHERE side = 'buy') AS buy_volume,
    sum(quantity) FILTER (WHERE side = 'sell') AS sell_volume,
    sum(quantity * price) AS notional_volume,
    avg(price) AS avg_price,
    percentile_cont(0.5) WITHIN GROUP (ORDER BY price) AS median_price
FROM trades
WHERE timestamp >= {{ from_dttm }} AND timestamp < {{ to_dttm }}
GROUP BY hour, symbol
ORDER BY hour DESC
```

### 5. Fill Rate Analysis

```sql
-- Анализ исполнения ордеров
SELECT 
    time_bucket('5 minutes', created_at) AS bucket,
    order_type,
    count(*) AS total_orders,
    count(*) FILTER (WHERE status = 'filled') AS filled_orders,
    count(*) FILTER (WHERE status = 'partially_filled') AS partial_fills,
    count(*) FILTER (WHERE status = 'cancelled') AS cancelled_orders,
    round(100.0 * count(*) FILTER (WHERE status = 'filled') / count(*), 2) AS fill_rate_pct,
    avg(fill_time_ms) FILTER (WHERE status = 'filled') AS avg_fill_time_ms
FROM orders
WHERE created_at >= {{ from_dttm }} AND created_at < {{ to_dttm }}
GROUP BY bucket, order_type
ORDER BY bucket DESC
```

---

## 📈 Рекомендуемая структура HFT Dashboard

### Layout (12-column grid)

```
┌─────────────────────────────────────────────────────────────────────┐
│  [Symbol Filter]  [Time Range]  [Strategy Filter]  [Refresh: 30s]  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│   │ Total PnL│  │# Trades  │  │Fill Rate │  │Avg Latency│          │
│   │  +$12.5K │  │  45,231  │  │  98.7%   │  │   2.3ms  │           │
│   └──────────┘  └──────────┘  └──────────┘  └──────────┘           │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │                    PRICE + VOLUME                            │  │
│   │  Mixed Time-Series (Dual Axis)                              │  │
│   │  - Y1: Price line (OHLC average or close)                   │  │
│   │  - Y2: Volume bars                                          │  │
│   │                              [8 columns]                     │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                                                      │
│   ┌─────────────────────┐                                           │
│   │  ORDERBOOK HEATMAP  │                                           │
│   │  X: Time            │                                           │
│   │  Y: Price Level     │                                           │
│   │  Color: Volume      │                                           │
│   │     [4 columns]     │                                           │
│   └─────────────────────┘                                           │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌─────────────────────┐  ┌─────────────────────┐                  │
│   │  LATENCY HISTOGRAM  │  │   FILL RATE GAUGE   │                  │
│   │                     │  │                     │                  │
│   │  Distribution of    │  │    ┌───────────┐   │                  │
│   │  order latencies    │  │    │   98.7%   │   │                  │
│   │     [6 columns]     │  │    └───────────┘   │                  │
│   └─────────────────────┘  │     [6 columns]    │                  │
│                            └─────────────────────┘                  │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌─────────────────────────────────────────────────────────────┐  │
│   │                    RECENT TRADES TABLE                       │  │
│   │  timestamp | symbol | side | price | quantity | latency_ms  │  │
│   │  ─────────────────────────────────────────────────────────  │  │
│   │  2024-01-15 10:32:15.123 | BTC-USDT | buy  | 42350.5 | ... │  │
│   │                             [12 columns]                     │  │
│   └─────────────────────────────────────────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🎨 Настройка визуализаций

### Mixed Time-Series (Dual-Axis для Price + Volume)

1. **Chart Type**: Mixed Time-Series
2. **Metrics**:
   - Primary: `AVG(price)` или `CLOSE`
   - Secondary: `SUM(volume)`
3. **Chart Options**:
   - Series 1: Line chart, Y-axis left
   - Series 2: Bar chart, Y-axis right
4. **Color**: Используйте схему "HFT Trading"

### Heatmap (Orderbook Depth)

1. **Chart Type**: Heatmap
2. **X-Axis**: `time_bucket` (время)
3. **Y-Axis**: `price_level` (уровни цен)
4. **Metric**: `SUM(quantity)`
5. **Color Scheme**: "HFT Heatmap" (Red-Yellow-Green)
6. **Options**:
   - Show Legend: Yes
   - Normalize: By row (для сравнения уровней)

### Latency Histogram

1. **Chart Type**: Histogram
2. **Column**: `latency_ms`
3. **Bins**: 50-100 (автоматически)
4. **Options**:
   - Cumulative: Off
   - Normalized: Optional (density)
   - X-axis label: "Latency (ms)"

### KPI Big Numbers

1. **Chart Type**: Big Number with Trendline
2. **Metric**: `SUM(pnl)` или `COUNT(*)`
3. **Time Grain**: 1 hour
4. **Comparison**: Period over period

---

## 🔧 Подключение TimescaleDB

### 1. Создание Database Connection

В Superset UI: **Data → Databases → + Database**

```
Display Name: TimescaleDB HFT
SQLAlchemy URI: postgresql://user:password@host:5432/hft_data

# Engine Parameters (JSON):
{
  "connect_args": {
    "options": "-c timezone=UTC"
  }
}
```

### 2. Создание Datasets

После подключения базы:

1. **Data → Datasets → + Dataset**
2. Выберите базу TimescaleDB
3. Выберите таблицу или создайте Virtual Dataset с SQL-запросом

**Рекомендуемые datasets для HFT:**

| Dataset Name | Тип | Источник |
|--------------|-----|----------|
| `trades_raw` | Physical | таблица `trades` |
| `ohlcv_1m` | Virtual | SQL с time_bucket('1 minute', ...) |
| `ohlcv_1h` | Virtual | SQL с time_bucket('1 hour', ...) |
| `orderbook_depth` | Virtual | SQL для heatmap |
| `latency_metrics` | Physical | таблица `pipeline_metrics` |
| `orders_summary` | Virtual | SQL с агрегацией |

---

## ⚠️ Ограничения и альтернативы

### Candlestick/OHLC Charts

**Проблема**: Superset не имеет нативного candlestick chart.

**Альтернативы**:

1. **Mixed Time-Series с 4 линиями**:
   - Open (dashed line)
   - High (dots, верхний)
   - Low (dots, нижний)
   - Close (solid line)

2. **Handlebars Chart** (кастомный HTML):
   ```html
   <div id="candlestick-{{rowId}}"></div>
   <script>
     // Используйте lightweight-charts или ECharts напрямую
   </script>
   ```

3. **Внешний embedding**:
   - TradingView widget через Markup
   - Grafana panel через iframe

### Real-time Updates

**Проблема**: Superset — не real-time dashboard.

**Решение**:
- Включить автообновление: Dashboard → Settings → Refresh interval → 10-30s
- Для настоящего real-time используйте Grafana

---

## 📋 Checklist для создания дашборда

- [ ] Подключить TimescaleDB как Database
- [ ] Создать Virtual Datasets с time_bucket агрегациями
- [ ] Создать фильтры: Symbol, Time Range, Strategy
- [ ] Добавить KPI cards (Big Numbers)
- [ ] Создать Mixed Time-Series для Price + Volume
- [ ] Создать Heatmap для orderbook
- [ ] Создать Histogram для latency
- [ ] Настроить автообновление (30 секунд)
- [ ] Применить цветовую схему "HFT Trading"
- [ ] Настроить Row-Level Security (если нужно)

---

## 🚀 Быстрый старт

```bash
# 1. Пересобрать образ Superset
cd /path/to/okx-hft-ops
docker compose -f docker/docker-compose.ml.yaml build superset superset-init

# 2. Перезапустить Superset
docker compose -f docker/docker-compose.ml.yaml up -d superset-init
docker compose -f docker/docker-compose.ml.yaml up -d superset

# 3. Открыть Superset
open https://superset.tumar.tech
```

---

*Документация обновлена: 2024-12*
*Версия Superset: 4.0.1*


