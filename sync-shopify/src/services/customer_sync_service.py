"""Service for syncing Shopify customers."""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from src.data_processor.processor import DataProcessor
from src.database.repositories.customer_repository import CustomerRepository
from src.http import ShopifyHTTPClient
from src.utils.queries import CUSTOMERS_QUERY
from config.settings import settings


logger = logging.getLogger(__name__)


class CustomerSyncService:
    """Handle customer synchronization logic."""

    def __init__(
        self,
        http_client: ShopifyHTTPClient,
        customer_repo: CustomerRepository,
        data_processor: DataProcessor,
    ):
        """
        Initialize customer sync service.

        Args:
            http_client: Shopify HTTP client
            customer_repo: Customer repository
            data_processor: Data processor
        """
        self.http_client = http_client
        self.customer_repo = customer_repo
        self.data_processor = data_processor

    def sync_customers(
        self, integration_id: UUID, last_sync: Optional[datetime] = None
    ) -> int:
        """
        Sync customers from Shopify using cursor pagination.

        Args:
            integration_id: Shopify integration UUID
            last_sync: Last successful sync timestamp

        Returns:
            Total number of customers synced
        """
        total_synced = 0
        cursor = None
        has_next_page = True

        # Build incremental query filter
        query_filter = None
        if last_sync:
            # Format: updated_at:>='2024-01-01T00:00:00Z'
            formatted_date = last_sync.strftime("%Y-%m-%dT%H:%M:%SZ")
            query_filter = f"updated_at:>='{formatted_date}'"
            logger.info(f"Syncing customers updated after {formatted_date}")

        try:
            while has_next_page:
                # Prepare variables
                variables = {
                    "first": settings.SHOPIFY_BATCH_SIZE,
                    "after": cursor,
                    "query": query_filter,
                }

                # Execute query
                response = self.http_client.execute_query(CUSTOMERS_QUERY, variables)

                # Extract data
                customers_data = (response.get("data") or {}).get("customers") or {}
                nodes = customers_data.get("nodes") or []
                page_info = customers_data.get("pageInfo") or {}

                if not nodes:
                    logger.info("No more customers to sync")
                    break

                # Process customers
                processed_customers = []
                for customer_node in nodes:
                    try:
                        # Validate node structure
                        if not customer_node or not isinstance(customer_node, dict):
                            logger.warning(f"Missing or invalid customer node")
                            continue

                        processed = self.data_processor.process_customer(customer_node)
                        processed_customers.append(processed)
                    except Exception as e:
                        logger.error(f"Failed to process customer: {str(e)}")
                        continue

                # Batch upsert
                if processed_customers:
                    self.customer_repo.batch_upsert_customers(
                        integration_id, processed_customers
                    )
                    total_synced += len(processed_customers)
                    logger.info(
                        f"Synced batch of {len(processed_customers)} customers (total: {total_synced})"
                    )

                # Check pagination
                has_next_page = page_info.get("hasNextPage", False)
                cursor = page_info.get("endCursor")

                if not cursor:
                    has_next_page = False

            logger.info(f"Completed sync of {total_synced} customers")
            return total_synced

        except Exception as e:
            logger.error(f"Sync failed: {str(e)}")
            raise
