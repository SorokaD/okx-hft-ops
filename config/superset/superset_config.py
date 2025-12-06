# Superset configuration
# https://superset.apache.org/docs/configuration/configuring-superset

import os

# Secret key - MUST be set via SUPERSET_SECRET_KEY environment variable
SECRET_KEY = os.getenv("SUPERSET_SECRET_KEY", "CHANGE_ME_TO_A_SECURE_RANDOM_KEY")

# Database connection string
SQLALCHEMY_DATABASE_URI = os.getenv(
    "SUPERSET_DATABASE_URI",
    "postgresql://superset:superset@superset-db:5432/superset"
)

# Flask-WTF flag for CSRF
WTF_CSRF_ENABLED = True
WTF_CSRF_EXEMPT_LIST = []
WTF_CSRF_TIME_LIMIT = 60 * 60 * 24 * 365

# Set this API key to enable Mapbox visualizations
MAPBOX_API_KEY = os.getenv("MAPBOX_API_KEY", "")

# Enable feature flags as needed
FEATURE_FLAGS = {
    "ENABLE_TEMPLATE_PROCESSING": True,
}

# Cache configuration
CACHE_CONFIG = {
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 60 * 60 * 24,
}

# Webserver configuration
WEBSERVER_THREADS = 8

