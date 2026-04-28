"""Database context manager for connection handling."""

import logging
from contextlib import contextmanager
from typing import Generator, Optional

import psycopg2
import psycopg2.extras
import psycopg2.pool
from psycopg2.extensions import connection

from config.settings import settings


logger = logging.getLogger(__name__)


class DatabaseContext:
    """Database connection pool manager."""

    def __init__(self):
        """Initialize connection pool."""
        self._pool: Optional[psycopg2.pool.SimpleConnectionPool] = None

    def initialize(self) -> None:
        """Create connection pool."""
        try:
            self._pool = psycopg2.pool.SimpleConnectionPool(
                settings.DB_POOL_MIN,
                settings.DB_POOL_MAX,
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                database=settings.DB_NAME,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                cursor_factory=psycopg2.extras.RealDictCursor,
            )
            logger.info("Connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize pool: {str(e)}")
            raise

    def close(self) -> None:
        """Close all connections in pool."""
        if self._pool:
            self._pool.closeall()
            logger.info("Connection pool closed")

    @contextmanager
    def get_connection(self) -> Generator[connection, None, None]:
        """
        Get a connection from the pool.

        Yields:
            Database connection with auto-commit disabled
        """
        if not self._pool:
            raise RuntimeError("Connection pool not initialized")

        conn = None
        try:
            conn = self._pool.getconn()
            conn.autocommit = False
            yield conn
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except Exception as rollback_err:
                    logger.error(f"Failed to rollback connection: {str(rollback_err)}")
            logger.error(f"Connection error: {str(e)}")
            raise
        finally:
            if conn:
                self._pool.putconn(conn)


# Global database context instance
db_context = DatabaseContext()
