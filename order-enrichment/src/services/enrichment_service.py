"""Order enrichment orchestrator service."""

import logging
from typing import Dict, Any, List, Optional
from psycopg2.extensions import connection

from src.database.repositories.neo4j_repository import Neo4jRepository
from src.database.repositories.enrichment_repository import EnrichmentRepository
from src.data_processor.enrichment_processor import EnrichmentProcessor
from src.config.settings import settings

logger = logging.getLogger(__name__)


class EnrichmentService:
    """Orchestrates the order enrichment process."""

    def __init__(self, conn: connection):
        """
        Initialize service with database connection.

        Args:
            conn: PostgreSQL connection for storing results
        """
        self.conn = conn
        self.neo4j_repo = Neo4jRepository()
        self.enrichment_repo = EnrichmentRepository(conn)
        self.processor = EnrichmentProcessor()

    def enrich_orders_for_month(
        self, 
        year: int, 
        month: int,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Enrich orders for a specific month.

        Args:
            year: Year (e.g., 2025)
            month: Month (1-12)
            limit: Optional limit on number of orders to process

        Returns:
            Statistics about the enrichment process
        """
        try:
            logger.info(f"Starting order enrichment for {year}-{month:02d}")

            # Ensure enrichment table exists
            self.enrichment_repo.create_table_if_not_exists()
            self.conn.commit()
            logger.info("Enrichment table ready")

            # Fetch orders from Neo4j
            logger.info("Fetching orders from Neo4j...")
            orders = self.neo4j_repo.fetch_orders_for_month(year, month, limit)
            
            if not orders:
                logger.warning(f"No orders found for {year}-{month:02d}")
                return {
                    'status': 'success',
                    'orders_fetched': 0,
                    'orders_processed': 0,
                    'orders_stored': 0,
                    'message': f'No orders found for {year}-{month:02d}'
                }

            logger.info(f"Fetched {len(orders)} orders from Neo4j")

            # Process orders in batches
            total_processed = 0
            total_stored = 0
            batch_size = settings.BATCH_SIZE

            for i in range(0, len(orders), batch_size):
                batch = orders[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (len(orders) + batch_size - 1) // batch_size
                
                logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} orders)")

                # Process batch
                enriched_orders = self.processor.process_orders_batch(batch)
                total_processed += len(enriched_orders)

                if enriched_orders:
                    # Store batch results
                    stored_count = self.enrichment_repo.upsert_enrichments(enriched_orders)
                    total_stored += stored_count
                    self.conn.commit()
                    logger.info(f"Stored {stored_count} enriched orders from batch {batch_num}")

            logger.info(f"Enrichment completed: {total_processed} processed, {total_stored} stored")

            return {
                'status': 'success',
                'orders_fetched': len(orders),
                'orders_processed': total_processed,
                'orders_stored': total_stored,
                'year': year,
                'month': month,
                'message': f'Successfully enriched orders for {year}-{month:02d}'
            }

        except Exception as e:
            logger.error(f"Error in order enrichment for {year}-{month:02d}: {str(e)}")
            try:
                self.conn.rollback()
            except Exception as rollback_err:
                logger.error(f"Failed to rollback transaction: {str(rollback_err)}")
            
            return {
                'status': 'error',
                'orders_fetched': 0,
                'orders_processed': 0,
                'orders_stored': 0,
                'error': str(e),
                'message': f'Failed to enrich orders for {year}-{month:02d}'
            }

    def enrich_orders_by_date_range(
        self, 
        start_date: str, 
        end_date: str,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Enrich orders within a date range.

        Args:
            start_date: Start date in ISO format (e.g., "2025-09-01T00:00:00-04:00")
            end_date: End date in ISO format (e.g., "2025-09-30T23:59:59-04:00")
            limit: Optional limit on number of orders to process

        Returns:
            Statistics about the enrichment process
        """
        try:
            logger.info(f"Starting order enrichment from {start_date} to {end_date}")

            # Ensure enrichment table exists
            self.enrichment_repo.create_table_if_not_exists()
            self.conn.commit()
            logger.info("Enrichment table ready")

            # Fetch orders from Neo4j
            logger.info("Fetching orders from Neo4j...")
            orders = self.neo4j_repo.fetch_orders_by_date_range(start_date, end_date, limit)
            
            if not orders:
                logger.warning(f"No orders found between {start_date} and {end_date}")
                return {
                    'status': 'success',
                    'orders_fetched': 0,
                    'orders_processed': 0,
                    'orders_stored': 0,
                    'message': f'No orders found between {start_date} and {end_date}'
                }

            logger.info(f"Fetched {len(orders)} orders from Neo4j")

            # Process orders in batches
            total_processed = 0
            total_stored = 0
            batch_size = settings.BATCH_SIZE

            for i in range(0, len(orders), batch_size):
                batch = orders[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (len(orders) + batch_size - 1) // batch_size
                
                logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} orders)")

                # Process batch
                enriched_orders = self.processor.process_orders_batch(batch)
                total_processed += len(enriched_orders)

                if enriched_orders:
                    # Store batch results
                    stored_count = self.enrichment_repo.upsert_enrichments(enriched_orders)
                    total_stored += stored_count
                    self.conn.commit()
                    logger.info(f"Stored {stored_count} enriched orders from batch {batch_num}")

            logger.info(f"Enrichment completed: {total_processed} processed, {total_stored} stored")

            return {
                'status': 'success',
                'orders_fetched': len(orders),
                'orders_processed': total_processed,
                'orders_stored': total_stored,
                'start_date': start_date,
                'end_date': end_date,
                'message': f'Successfully enriched orders from {start_date} to {end_date}'
            }

        except Exception as e:
            logger.error(f"Error in order enrichment from {start_date} to {end_date}: {str(e)}")
            try:
                self.conn.rollback()
            except Exception as rollback_err:
                logger.error(f"Failed to rollback transaction: {str(rollback_err)}")
            
            return {
                'status': 'error',
                'orders_fetched': 0,
                'orders_processed': 0,
                'orders_stored': 0,
                'error': str(e),
                'message': f'Failed to enrich orders from {start_date} to {end_date}'
            }

    def get_enrichment_stats(self) -> Dict[str, Any]:
        """
        Get statistics about stored enrichment data.

        Returns:
            Dictionary with enrichment statistics
        """
        try:
            self.enrichment_repo.create_table_if_not_exists()
            self.conn.commit()
            
            stats = self.enrichment_repo.get_enrichment_stats()
            logger.info("Retrieved enrichment statistics")
            
            return {
                'status': 'success',
                'stats': stats,
                'message': 'Successfully retrieved enrichment statistics'
            }
        
        except Exception as e:
            logger.error(f"Error retrieving enrichment stats: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'message': 'Failed to retrieve enrichment statistics'
            }

    def close(self) -> None:
        """Close Neo4j connection."""
        try:
            if self.neo4j_repo:
                self.neo4j_repo.close()
                logger.info("Neo4j connection closed")
        except Exception as e:
            logger.error(f"Error closing Neo4j connection: {str(e)}")