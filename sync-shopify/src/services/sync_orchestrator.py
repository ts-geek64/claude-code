"""Orchestrator service for managing the entire sync process."""

import logging
import concurrent.futures
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
from uuid import UUID

from psycopg2.extensions import connection

from src.data_processor.processor import DataProcessor
from src.database.database_context import db_context
from src.database.repositories.customer_repository import CustomerRepository
from src.database.repositories.integration_repository import IntegrationRepository
from src.database.repositories.order_repository import OrderRepository
from src.http import ShopifyHTTPClient
from src.services.customer_sync_service import CustomerSyncService
from src.services.order_sync_service import OrderSyncService
from src.services.product_sync_service import ProductSyncService
from src.utils.encryption import encryption_service
from src.utils.tenant_context import tenant_context
from src.database.repositories.order_line_item_repository import OrderLineItemRepository
from src.database.repositories.product_repository import ProductRepository


logger = logging.getLogger(__name__)

# Max number of integrations synced in parallel.
# Bounded to avoid exhausting the DB connection pool.
MAX_PARALLEL_INTEGRATIONS = 4


def _compute_sync_start(latest_date: Optional[datetime]) -> Optional[datetime]:
    """Return 15-day look-back from latest date, normalized to UTC."""
    if not latest_date:
        return None
    if latest_date.tzinfo is None:
        latest_date = latest_date.replace(tzinfo=timezone.utc)
    else:
        latest_date = latest_date.astimezone(timezone.utc)
    return latest_date - timedelta(days=15)


class SyncOrchestrator:
    """Orchestrate the complete sync process for Shopify integrations."""

    def __init__(self, conn: connection):
        """
        Initialize orchestrator with a database connection used only for
        fetching integration metadata. Each integration sync acquires its
        own connection from the pool for full parallelism.

        Args:
            conn: Active database connection
        """
        self.conn = conn
        self.integration_repo = IntegrationRepository(conn)

    def sync_integration(
        self,
        integration: Dict,
        tenant_prefix: Optional[str] = None,
        sync_from_start: bool = False,
    ) -> Dict:
        """
        Sync a single Shopify integration using a dedicated DB connection.

        Optimizations vs. original:
        - Products are fetched in parallel with customers (no dependency).
        - Orders are synced after customers complete (FK dependency).
        - Each section uses batch DB operations internally.

        Args:
            integration: Integration data dictionary
            tenant_prefix: Tenant prefix to re-apply inside worker threads.
                           ContextVar values are NOT inherited by OS threads
                           spawned via ThreadPoolExecutor (only by asyncio tasks).
                           The main thread captures the prefix and passes it here
                           so the worker can restore it before touching the DB.

        Returns:
            Sync result dictionary
        """
        # Re-apply tenant context inside the thread.
        # ContextVar is thread-local: each new OS thread starts with default=None.
        if tenant_prefix is not None:
            from src.utils.tenant_context import _current_tenant

            _current_tenant.set(tenant_prefix)

        integration_id = integration["id"]
        shop_domain = integration["myshopify_domain"]
        shop_name = integration["shop_name"]
        encrypted_token = integration["token"]

        http_client = None

        try:
            access_token = encryption_service.decrypt_token(encrypted_token)
            if not access_token:
                raise Exception("Failed to decrypt access token")

            http_client = ShopifyHTTPClient(shop_domain, access_token)

            # Use a fresh connection from the pool for this integration
            with db_context.get_connection() as conn:
                integration_repo = IntegrationRepository(conn)
                customer_repo = CustomerRepository(conn)
                order_repo = OrderRepository(conn)
                line_item_repo = OrderLineItemRepository(conn)
                product_repo = ProductRepository(conn)
                data_processor = DataProcessor()

                # Fetch latest timestamps if NOT syncing from start
                sync_customer_start = None
                sync_order_start = None
                sync_product_start = None

                if not sync_from_start:
                    sync_customer_start = _compute_sync_start(
                        customer_repo.get_latest_customer_created_at(integration_id)
                    )
                    sync_order_start = _compute_sync_start(
                        order_repo.get_latest_order_created_at(integration_id)
                    )
                    sync_product_start = _compute_sync_start(
                        product_repo.get_latest_product_created_at(integration_id)
                    )

                # Health check
                if not http_client.health_check():
                    integration_repo.update_health_status(integration_id, "unhealthy")
                    return {
                        "status": "error",
                        "code": "ERR_HEALTH_CHECK_FAILED",
                        "message": f"Health check failed for {shop_name}",
                        "details": {"integration_id": str(integration_id)},
                    }

                integration_repo.update_health_status(integration_id, "healthy")

                customer_sync = CustomerSyncService(
                    http_client, customer_repo, data_processor
                )
                order_sync = OrderSyncService(
                    http_client,
                    order_repo,
                    customer_repo,
                    line_item_repo,
                    product_repo,
                    data_processor,
                )
                product_sync = ProductSyncService(
                    http_client, product_repo, data_processor
                )

                logger.info(f"Starting sync for {shop_name} ({shop_domain})")

                # ── Phase 1: customers + products ──
                # These are run sequentially to avoid thread-safety issues with the
                # shared DB connection.
                logger.info(f"Syncing customers for {shop_name}")
                customers_synced = customer_sync.sync_customers(
                    integration_id, sync_customer_start
                )

                logger.info(f"Syncing products for {shop_name}")
                products_synced = product_sync.sync_products(
                    integration_id, sync_product_start
                )

                # ── Sequential Phase: orders (depend on customers + products) ──
                orders_synced = order_sync.sync_orders(integration_id, sync_order_start)

                integration_repo.update_last_sync_timestamp(integration_id)

                logger.info(
                    f"Sync completed for {shop_name}: "
                    f"{customers_synced} customers, {orders_synced} orders, "
                    f"{products_synced} products"
                )

                return {
                    "status": "success",
                    "integration_id": str(integration_id),
                    "shop_name": shop_name,
                    "customers_synced": customers_synced,
                    "orders_synced": orders_synced,
                    "products_synced": products_synced,
                }

        except Exception as e:
            logger.error(f"Sync failed for {shop_name}: {str(e)}")
            return {
                "status": "error",
                "code": "ERR_SYNC_FAILED",
                "message": f"Sync failed for {shop_name}",
                "details": {"integration_id": str(integration_id), "error": str(e)},
            }

        finally:
            if http_client:
                http_client.close()

    def sync_all_integrations(
        self, integration_ids: List[str] = None, sync_from_start: bool = False
    ) -> Dict:
        """
        Sync all (or specific) active Shopify integrations in parallel.

        Captures the tenant prefix from the main thread before submitting work
        to the thread pool, then passes it into each worker so it can be
        re-applied (ContextVar is not inherited by OS threads).

        Args:
            integration_ids: Optional list of integration IDs to sync

        Returns:
            Aggregated sync results
        """
        try:
            integrations = self.integration_repo.get_active_shopify_integrations(
                integration_ids
            )

            if not integrations:
                logger.info("No active Shopify integrations found")
                return {
                    "status": "success",
                    "message": "No active integrations to sync",
                    "results": [],
                }

            logger.info(
                f"Found {len(integrations)} integrations to sync "
                f"(max {MAX_PARALLEL_INTEGRATIONS} in parallel)"
            )

            # Capture tenant prefix NOW, in the main thread, before any worker is spawned.
            current_prefix = tenant_context.get_tenant_prefix()

            results = []

            if len(integrations) == 1:
                # Skip thread overhead for a single integration; context is already set.
                results.append(
                    self.sync_integration(
                        integrations[0],
                        tenant_prefix=None,
                        sync_from_start=sync_from_start,
                    )
                )
            else:
                with concurrent.futures.ThreadPoolExecutor(
                    max_workers=MAX_PARALLEL_INTEGRATIONS
                ) as executor:
                    futures = {
                        executor.submit(
                            self.sync_integration,
                            integration,
                            current_prefix,
                            sync_from_start,
                        ): integration
                        for integration in integrations
                    }
                    for future in concurrent.futures.as_completed(futures):
                        try:
                            results.append(future.result())
                        except Exception as e:
                            integration = futures[future]
                            logger.error(
                                f"Integration {integration.get('shop_name')} raised: {e}"
                            )
                            results.append(
                                {
                                    "status": "error",
                                    "code": "ERR_SYNC_FAILED",
                                    "integration_id": str(integration.get("id")),
                                    "shop_name": integration.get("shop_name"),
                                    "details": {"error": str(e)},
                                }
                            )

            successful = sum(1 for r in results if r["status"] == "success")
            failed = len(results) - successful

            logger.info(f"Sync complete: {successful} successful, {failed} failed")

            return {
                "status": "success",
                "total_integrations": len(integrations),
                "successful": successful,
                "failed": failed,
                "results": results,
            }

        except Exception as e:
            logger.error(f"Failed to sync integrations: {str(e)}")
            return {
                "status": "error",
                "code": "ERR_ORCHESTRATION_FAILED",
                "message": "Failed to sync integrations",
                "details": {"error": str(e)},
            }
