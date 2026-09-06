"""Configuration, read from the environment (with a .env file if present)."""

import os

from dotenv import load_dotenv

load_dotenv()


def _int(name, default):
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-not-secret")
    DEBUG = os.environ.get("FLASK_DEBUG", "").lower() in ("1", "true", "yes")

    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/")
    MONGO_DB = os.environ.get("MONGO_DB", "achecker_db")

    ANALYSIS_TIMEOUT = _int("ACHECKER_TIMEOUT", 300)  # seconds
    ANALYSIS_MEMORY_GB = _int("ACHECKER_MEMORY_GB", 6)
    TIMEZONE = os.environ.get("ACHECKER_TZ", "Europe/Berlin")

    MAX_CONTENT_LENGTH = _int("ACHECKER_MAX_UPLOAD", 5 * 1024 * 1024)
