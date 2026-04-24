"""
Application configuration classes for the Intelligence Query Engine.

Each class reads DATABASE_URL (and optionally TEST_DATABASE_URL) from the
environment.  python-dotenv is used to load a .env file before the values
are read, so the classes work both with an explicit .env file and with
environment variables injected by the host (e.g. Docker, CI).
"""

import os

from dotenv import load_dotenv

# Load .env once at import time so os.environ.get() picks up the values.
load_dotenv()


class BaseConfig:
    """Shared defaults for all environments."""

    SECRET_KEY: str = os.environ.get("SECRET_KEY", "change-me-in-production")
    DATABASE_URL: str | None = os.environ.get("DATABASE_URL")

    # SQLAlchemy / connection-pool settings
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False


class DevelopmentConfig(BaseConfig):
    """Configuration for local development."""

    DEBUG: bool = True
    TESTING: bool = False


class TestingConfig(BaseConfig):
    """Configuration for the automated test suite.

    Reads TEST_DATABASE_URL first; falls back to DATABASE_URL so that a
    single-database setup still works out of the box.
    """

    DEBUG: bool = False
    TESTING: bool = True

    # Prefer a dedicated test database; fall back to the main DATABASE_URL.
    DATABASE_URL: str | None = os.environ.get(
        "TEST_DATABASE_URL", os.environ.get("DATABASE_URL")
    )


class ProductionConfig(BaseConfig):
    """Configuration for production deployments."""

    DEBUG: bool = False
    TESTING: bool = False


# Mapping used by the application factory to select a config by name.
config: dict[str, type[BaseConfig]] = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
