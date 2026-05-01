"""Neo4j repository for order data access."""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from neo4j import GraphDatabase, Driver, Session
from neo4j.exceptions import ServiceUnavailable, AuthError

from src.config.settings import settings

logger = logging.getLogger(__name__)


class Neo4jRepository:
    """Repository for accessing Neo4j order data."""

    def __init__(self):
        """Initialize Neo4j driver."""
        self._driver: Optional[Driver] = None
        self._initialize_driver()

    def _initialize_driver(self) -> None:
        """Initialize Neo4j driver with connection settings."""
        try:
            self._driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
            )
            logger.info("Neo4j driver initialized successfully")
            self._test_connection()
        except (ServiceUnavailable, AuthError) as e:
            logger.error(f"Failed to initialize Neo4j driver: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error initializing Neo4j driver: {str(e)}")
            raise

    def _test_connection(self) -> None:
        """Test the Neo4j connection."""
        if not self._driver:
            raise RuntimeError("Neo4j driver not initialized")

        try:
            with self._driver.session() as session:
                result = session.run("RETURN 'Connection successful!' AS message")
                record = result.single()
                if record:
                    logger.info(f"Neo4j connection test: {record['message']}")
        except Exception as e:
            logger.error(f"Neo4j connection test failed: {str(e)}")
            raise

    def fetch_orders_for_month(
        self, 
        year: int, 
        month: int,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch online orders for a specific month.

        Args:
            year: Year (e.g., 2025)
            month: Month (1-12)
            limit: Optional limit on number of records to return

        Returns:
            List of order dictionaries with order data

        Raises:
            RuntimeError: If driver is not initialized
            Exception: For other Neo4j errors
        """
        if not self._driver:
            raise RuntimeError("Neo4j driver not initialized")

        # Create date range for the month
        start_date = f"{year}-{month:02d}-01T00:00:00-04:00"
        if month == 12:
            end_date = f"{year+1}-01-01T00:00:00-04:00"
        else:
            end_date = f"{year}-{month+1:02d}-01T00:00:00-04:00"

        query = """
        MATCH (o:OnlineOrder)
        WHERE o.createdDate >= datetime($start_date)
          AND o.createdDate < datetime($end_date)
        RETURN id(o) AS id, 
               o.createdDate as createdDate,
               o.externalOrderId as externalOrderId, 
               o.landingPage as landingPage, 
               o.orderAmount as orderAmount
        ORDER BY o.createdDate
        """

        if limit:
            query += f" LIMIT {limit}"

        try:
            with self._driver.session() as session:
                result = session.run(query, start_date=start_date, end_date=end_date)
                records = [record.data() for record in result]
                logger.info(f"Fetched {len(records)} orders for {year}-{month:02d}")
                return records
        except Exception as e:
            logger.error(f"Error fetching orders for {year}-{month:02d}: {str(e)}")
            raise

    def fetch_orders_by_date_range(
        self, 
        start_date: str, 
        end_date: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch online orders within a date range.

        Args:
            start_date: Start date in ISO format (e.g., "2025-09-01T00:00:00-04:00")
            end_date: End date in ISO format (e.g., "2025-09-30T23:59:59-04:00")
            limit: Optional limit on number of records to return

        Returns:
            List of order dictionaries with order data
        """
        if not self._driver:
            raise RuntimeError("Neo4j driver not initialized")

        query = """
        MATCH (o:OnlineOrder)
        WHERE o.createdDate >= datetime($start_date)
          AND o.createdDate < datetime($end_date)
        RETURN id(o) AS id, 
               o.createdDate as createdDate,
               o.externalOrderId as externalOrderId, 
               o.landingPage as landingPage, 
               o.orderAmount as orderAmount
        ORDER BY o.createdDate
        """

        if limit:
            query += f" LIMIT {limit}"

        try:
            with self._driver.session() as session:
                result = session.run(query, start_date=start_date, end_date=end_date)
                records = [record.data() for record in result]
                logger.info(f"Fetched {len(records)} orders between {start_date} and {end_date}")
                return records
        except Exception as e:
            logger.error(f"Error fetching orders between {start_date} and {end_date}: {str(e)}")
            raise

    def close(self) -> None:
        """Close Neo4j driver."""
        if self._driver:
            self._driver.close()
            logger.info("Neo4j driver closed")