# ============================================
# Superset Configuration for HFT/Crypto Analytics
# Tumar HFT Project
# ============================================
# Документация: https://superset.apache.org/docs/configuration/configuring-superset
# ============================================

import os
from datetime import timedelta

# ============================================
# CORE SETTINGS
# ============================================

# Secret key - ОБЯЗАТЕЛЬНО задать через SUPERSET_SECRET_KEY
# Минимум 32 байта для JWT токенов
SECRET_KEY = os.getenv(
    "SUPERSET_SECRET_KEY", 
    "tumar_hft_superset_secret_key_32b!"  # Fallback для dev (32+ chars)
)

# Подключение к метаданным Superset (PostgreSQL)
SQLALCHEMY_DATABASE_URI = os.getenv(
    "SUPERSET_DATABASE_URI",
    "postgresql://superset:superset@superset-db:5432/superset"
)

# ============================================
# FEATURE FLAGS - Включаем расширенные возможности
# ============================================
# Документация: https://superset.apache.org/docs/configuration/configuring-superset#feature-flags

FEATURE_FLAGS = {
    # === Визуализации ===
    # Включает все ECharts визуализации (уже включены по умолчанию в 4.x)
    "ENABLE_EXPLORE_DRAG_AND_DROP": True,  # Drag & drop в Explore
    
    # === Шаблоны и SQL ===
    "ENABLE_TEMPLATE_PROCESSING": True,     # Jinja2 шаблоны в SQL
    "ENABLE_TEMPLATE_REMOVE_FILTERS": True, # Удаление фильтров через шаблоны
    
    # === Dashboard ===
    "DASHBOARD_NATIVE_FILTERS": True,       # Нативные фильтры дашборда
    "DASHBOARD_CROSS_FILTERS": True,        # Кросс-фильтрация между чартами
    "DASHBOARD_NATIVE_FILTERS_SET": True,   # Сеты фильтров
    "DASHBOARD_RBAC": True,                 # Row-level security для дашбордов
    
    # === Alerts & Reports ===
    # "ALERT_REPORTS": True,                # Email/Slack (требует Celery/Redis)
    
    # === Advanced ===
    # GLOBAL_ASYNC_QUERIES отключен - требует Celery/Redis и JWT secret
    # "GLOBAL_ASYNC_QUERIES": True,
    "EMBEDDED_SUPERSET": True,              # Встраивание дашбордов
    "ESTIMATE_QUERY_COST": True,            # Оценка стоимости запроса
    
    # === Data Exploration ===
    "DRILL_TO_DETAIL": True,                # Drill-down в данные
    "DRILL_BY": True,                       # Drill-by dimension
    
    # === Experimental (HFT-relevant) ===
    "HORIZONTAL_FILTER_BAR": True,          # Горизонтальная панель фильтров
}

# ============================================
# SECURITY (CSRF & Auth)
# ============================================

WTF_CSRF_ENABLED = True
WTF_CSRF_EXEMPT_LIST = []
WTF_CSRF_TIME_LIMIT = 60 * 60 * 24 * 365  # 1 year

# Session timeout (для HFT важно долгое время сессии)
PERMANENT_SESSION_LIFETIME = timedelta(hours=24)

# ============================================
# CACHE CONFIGURATION
# ============================================
# Для production рекомендуется Redis

# Проверяем, есть ли Redis
REDIS_URL = os.getenv("REDIS_URL", None)

if REDIS_URL:
    # Production: используем Redis
    CACHE_CONFIG = {
        "CACHE_TYPE": "RedisCache",
        "CACHE_DEFAULT_TIMEOUT": 60 * 60 * 24,  # 24 hours
        "CACHE_KEY_PREFIX": "superset_",
        "CACHE_REDIS_URL": REDIS_URL,
    }
    
    # Cache для результатов запросов
    DATA_CACHE_CONFIG = {
        "CACHE_TYPE": "RedisCache",
        "CACHE_DEFAULT_TIMEOUT": 60 * 60,  # 1 hour для данных
        "CACHE_KEY_PREFIX": "superset_data_",
        "CACHE_REDIS_URL": REDIS_URL,
    }
    
    # Cache для фильтров
    FILTER_STATE_CACHE_CONFIG = {
        "CACHE_TYPE": "RedisCache",
        "CACHE_DEFAULT_TIMEOUT": 60 * 60 * 24 * 7,  # 7 days
        "CACHE_KEY_PREFIX": "superset_filter_",
        "CACHE_REDIS_URL": REDIS_URL,
    }
else:
    # Development: SimpleCache
    CACHE_CONFIG = {
        "CACHE_TYPE": "SimpleCache",
        "CACHE_DEFAULT_TIMEOUT": 60 * 60 * 24,
    }
    DATA_CACHE_CONFIG = CACHE_CONFIG
    FILTER_STATE_CACHE_CONFIG = CACHE_CONFIG

# ============================================
# WEBSERVER CONFIGURATION
# ============================================

WEBSERVER_THREADS = 8
SUPERSET_WEBSERVER_TIMEOUT = 120  # Увеличен для тяжелых HFT запросов

# Row limit для SQL Lab (HFT может генерировать много данных)
ROW_LIMIT = 50000
SQL_MAX_ROW = 100000
DISPLAY_MAX_ROW = 10000

# ============================================
# SQL LAB CONFIGURATION
# ============================================

# Async queries - важно для больших HFT датасетов
SQLLAB_ASYNC_TIME_LIMIT_SEC = 60 * 15  # 15 min
SQLLAB_TIMEOUT = 60 * 5  # 5 min default timeout

# Разрешаем CTAS/CVAS для создания таблиц из запросов
SQLLAB_CTAS_NO_LIMIT = True

# ============================================
# VISUALIZATION SETTINGS
# ============================================

# Mapbox (если нужны географические визуализации)
MAPBOX_API_KEY = os.getenv("MAPBOX_API_KEY", "")

# Default timezone для HFT (UTC recommended)
DEFAULT_TIMEZONE = "UTC"

# VIZ_TYPE_DENYLIST - можно отключить ненужные визуализации
# VIZ_TYPE_DENYLIST = ["pivot_table_v2"]  # Пример

# ============================================
# HFT-SPECIFIC: Custom CSS для dark theme
# ============================================

# Дополнительный CSS для HFT дашбордов (dark trading theme)
EXTRA_CATEGORICAL_COLOR_SCHEMES = [
    {
        "id": "hft_trading",
        "description": "HFT Trading Color Scheme",
        "label": "HFT Trading",
        "isDefault": False,
        "colors": [
            "#00C853",  # Green (buy/profit)
            "#FF1744",  # Red (sell/loss)
            "#2196F3",  # Blue (neutral)
            "#FF9800",  # Orange (warning)
            "#9C27B0",  # Purple (volume)
            "#00BCD4",  # Cyan (bid)
            "#FFEB3B",  # Yellow (ask)
            "#795548",  # Brown (spread)
            "#607D8B",  # Blue Grey (other)
            "#E91E63",  # Pink (highlight)
        ],
    }
]

EXTRA_SEQUENTIAL_COLOR_SCHEMES = [
    {
        "id": "hft_heatmap",
        "description": "HFT Heatmap (Red-Yellow-Green)",
        "label": "HFT Heatmap",
        "isDefault": False,
        "isDiverging": True,
        "colors": [
            "#B71C1C",  # Dark Red
            "#F44336",  # Red
            "#FF5722",  # Deep Orange
            "#FF9800",  # Orange
            "#FFEB3B",  # Yellow
            "#CDDC39",  # Lime
            "#8BC34A",  # Light Green
            "#4CAF50",  # Green
            "#2E7D32",  # Dark Green
        ],
    },
    {
        "id": "hft_volume",
        "description": "HFT Volume Depth",
        "label": "HFT Volume",
        "isDefault": False,
        "isDiverging": False,
        "colors": [
            "#E3F2FD",
            "#BBDEFB",
            "#90CAF9",
            "#64B5F6",
            "#42A5F5",
            "#2196F3",
            "#1E88E5",
            "#1565C0",
            "#0D47A1",
        ],
    }
]

# ============================================
# DATABASE CONNECTION SETTINGS
# ============================================

# Дополнительные параметры для подключения к TimescaleDB
# Можно переопределить engine_params для конкретных database connections

SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_size": 10,
    "pool_recycle": 3600,
    "pool_pre_ping": True,
    "max_overflow": 20,
}

# ============================================
# LOGGING
# ============================================

# Уровень логирования
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Логирование SQL запросов (включить для debug)
# SQLALCHEMY_ECHO = True

# ============================================
# COMMENTS: Доступные визуализации в Superset 4.x
# ============================================
# 
# === ECharts (все включены по умолчанию) ===
# - echarts_timeseries         : Основной time series (линии, бары)
# - echarts_timeseries_bar     : Time series bar chart
# - echarts_timeseries_line    : Time series line chart
# - echarts_timeseries_scatter : Time series scatter
# - echarts_timeseries_smooth  : Smooth line chart
# - echarts_timeseries_step    : Step chart
# - mixed_timeseries           : DUAL-AXIS! Два Y-axis для разных метрик
# - echarts_area               : Area chart
# - echarts_boxplot            : Box plot (для анализа распределения цен)
# - echarts_bubble             : Bubble chart
# - echarts_funnel             : Funnel chart
# - echarts_gauge              : Gauge (для метрик типа latency)
# - echarts_graph              : Graph/Network
# - echarts_heatmap            : HEATMAP! Для orderbook depth
# - echarts_histogram          : ГИСТОГРАММА! Для распределения latency
# - echarts_pie                : Pie/Donut
# - echarts_radar              : Radar chart
# - echarts_sankey             : Sankey diagram (для flow analysis)
# - echarts_sunburst           : Sunburst
# - echarts_tree               : Tree chart
# - echarts_treemap            : Treemap
#
# === Для HFT особенно полезны ===
# 1. mixed_timeseries - два Y-axis (цена + объём)
# 2. echarts_heatmap - визуализация orderbook/volume по цене и времени
# 3. echarts_histogram - распределение latency
# 4. echarts_boxplot - статистика по ценам/спредам
# 5. echarts_gauge - текущие метрики (latency, fill rate)
# 6. table - детальные данные трейдов
#
# === OHLC/Candlestick ===
# ВАЖНО: Superset НЕ имеет нативного candlestick chart.
# Альтернативы:
# 1. Использовать mixed_timeseries с 4 линиями (O/H/L/C)
# 2. Встраивать внешний виджет через Markup
# 3. Использовать Handlebars chart с кастомным HTML/JS
#
# ============================================
