"""Application configuration settings for order enrichment."""

import os
from dotenv import load_dotenv

load_dotenv()


def _str(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _int(name: str, default: int) -> int:
    val = os.getenv(name, "").strip()
    try:
        return int(val) if val else default
    except ValueError:
        return default


def _float(name: str, default: float) -> float:
    val = os.getenv(name, "").strip()
    try:
        return float(val) if val else default
    except ValueError:
        return default


def _db_host() -> str:
    """Convert Cloud SQL connection name to Unix socket path on Cloud Run."""
    host = _str("DB_HOST", "localhost")
    if host and not host.startswith("/") and ":" in host:
        # e.g. "auvodka:us-central1:omnigrowthos" → "/cloudsql/auvodka:us-central1:omnigrowthos"
        return f"/cloudsql/{host}"
    return host


class Settings:
    # Database
    DB_HOST: str = _db_host()
    DB_PORT: int = _int("DB_PORT", 5432)
    DB_NAME: str = _str("DB_NAME", "shopify_db")
    DB_USER: str = _str("DB_USER", "postgres")
    DB_PASSWORD: str = _str("DB_PASSWORD", "")
    DB_POOL_MIN: int = _int("DB_POOL_MIN", 2)
    DB_POOL_MAX: int = _int("DB_POOL_MAX", 10)

    # Neo4j
    NEO4J_URI: str = _str("NEO4J_URI", "")
    NEO4J_USERNAME: str = _str("NEO4J_USERNAME", "neo4j")
    NEO4J_PASSWORD: str = _str("NEO4J_PASSWORD", "")

    # Encryption
    FERNET_KEY: str = _str("FERNET_KEY", "")

    # Processing
    BATCH_SIZE: int = _int("BATCH_SIZE", 250)
    MAX_RETRIES: int = _int("MAX_RETRIES", 3)
    INITIAL_BACKOFF: float = _float("INITIAL_BACKOFF", 1.0)
    MAX_BACKOFF: float = _float("MAX_BACKOFF", 60.0)

    # Logging
    LOG_LEVEL: str = _str("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls) -> None:
        """Validate required settings."""
        required_fields = [
            "DB_PASSWORD",
            "NEO4J_URI", 
            "NEO4J_PASSWORD",
            "FERNET_KEY"
        ]
        
        for field in required_fields:
            value = getattr(cls, field)
            if not value:
                raise ValueError(f"{field} is required")


settings = Settings()