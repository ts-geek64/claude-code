"""Service for syncing Shopify orders."""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from src.data_processor.processor import DataProcessor
from src.database.repositories.customer_repository import CustomerRepository
from src.database.repositories.order_repository import OrderRepository
from src.http import ShopifyHTTPClient
from src.utils.queries import ORDERS_QUERY
from config.settings import settings
from src.database.repositories.order_line_item_repository import OrderLineItemRepository
from src.database.repositories.product_repository import ProductRepository

logger = logging.getLogger(__name__)


class OrderSyncService:
    """Handle order synchronization logic."""

    def __init__(
        self,
        http_client: ShopifyHTTPClient,
        order_repo: OrderRepository,
        customer_repo: CustomerRepository,
        line_item_repo: OrderLineItemRepository,
        product_repo: ProductRepository,
        data_processor: DataProcessor,
    ):
        self.http_client = http_client
        self.order_repo = order_repo
        self.customer_repo = customer_repo
        self.line_item_repo = line_item_repo
        self.product_repo = product_repo
        self.data_processor = data_processor

    def sync_orders(
        self, integration_id: UUID, last_sync: Optional[datetime] = None
    ) -> int:
        """
        Sync orders from Shopify using cursor pagination.

        Key optimizations:
        - Customer IDs resolved via single batch SELECT (not N individual queries)
        - Order IDs returned by RETURNING clause (not re-queried after insert)
        - Product/variant IDs resolved via single batch SELECT per page
        - In-memory caches for product/variant IDs persist across pages

        Returns:
            Total number of orders synced
        """
        total_synced = 0
        cursor = None
        has_next_page = True

        query_filter = None
        if last_sync:
            formatted_date = last_sync.strftime("%Y-%m-%dT%H:%M:%SZ")
            query_filter = f"updated_at:>='{formatted_date}'"
            logger.info(f"Syncing orders updated after {formatted_date}")

        # In-memory caches persist across all pages for this sync run,
        # avoiding repeated DB queries for the same product/variant IDs.
        product_id_cache: Dict[str, str] = {}
        variant_id_cache: Dict[str, str] = {}

        try:
            while has_next_page:
                variables = {
                    "first": settings.SHOPIFY_BATCH_SIZE,
                    "after": cursor,
                    "query": query_filter,
                }

                response = self.http_client.execute_query(ORDERS_QUERY, variables)

                orders_data = (response.get("data") or {}).get("orders") or {}
                nodes = orders_data.get("nodes") or []
                page_info = orders_data.get("pageInfo") or {}

                if not nodes:
                    logger.info("No more orders to sync")
                    break

                # ── Step 1: Process all orders in the page ──────────────────
                processed_orders = []
                all_line_items = []
                shopify_customer_ids = set()

                for order_node in nodes:
                    try:
                        if not order_node or not isinstance(order_node, dict):
                            logger.warning("Missing or invalid order node")
                            continue

                        processed = self.data_processor.process_order(order_node)

                        shopify_customer_id = processed.get("shopify_customer_id")
                        if shopify_customer_id:
                            shopify_customer_ids.add(shopify_customer_id)

                        processed_orders.append(processed)

                        line_items = self.data_processor.process_order_line_items(
                            order_node
                        )
                        for item in line_items:
                            item["shopify_order_id"] = order_node.get("id")
                            all_line_items.append(item)

                    except Exception as e:
                        logger.error(f"Failed to process order: {str(e)}")
                        continue

                if not processed_orders:
                    has_next_page = page_info.get("hasNextPage", False)
                    cursor = page_info.get("endCursor")
                    if not cursor:
                        has_next_page = False
                    continue

                # ── Step 2: Batch resolve customer IDs (1 query for entire page) ──
                customer_id_map = self.customer_repo.batch_get_customer_ids(
                    integration_id, list(shopify_customer_ids)
                )
                for order in processed_orders:
                    shopify_cid = order.get("shopify_customer_id")
                    order["customer_id"] = (
                        customer_id_map.get(shopify_cid) if shopify_cid else None
                    )

                # ── Step 3: Upsert orders, get IDs back via RETURNING ──────────
                order_id_map = self.order_repo.batch_upsert_orders(
                    integration_id, processed_orders
                )
                total_synced += len(processed_orders)
                logger.info(
                    f"Synced batch of {len(processed_orders)} orders (total: {total_synced})"
                )

                # ── Step 4: Resolve product/variant IDs for line items ─────────
                if all_line_items:
                    # Collect uncached IDs
                    unknown_product_ids = {
                        item["shopify_product_id"]
                        for item in all_line_items
                        if item.get("shopify_product_id")
                        and item["shopify_product_id"] not in product_id_cache
                    }
                    unknown_variant_ids = {
                        item["shopify_variant_id"]
                        for item in all_line_items
                        if item.get("shopify_variant_id")
                        and item["shopify_variant_id"] not in variant_id_cache
                    }

                    # Single batch query per uncached set
                    if unknown_product_ids:
                        product_id_cache.update(
                            self.product_repo.batch_get_product_ids(
                                integration_id, list(unknown_product_ids)
                            )
                        )
                    if unknown_variant_ids:
                        variant_id_cache.update(
                            self.product_repo.batch_get_variant_ids(
                                list(unknown_variant_ids)
                            )
                        )

                    # Assemble line items with all resolved references
                    line_items_with_refs = []

                    # Step 4b: Batch-fetch active cost & price snapshots
                    # Collect all internal variant IDs seen on this page, then
                    # resolve their current-active cost and price in one query
                    # each. This maintains the existing O(1-query-per-set) pattern.
                    all_internal_variant_ids = list(
                        {v for v in variant_id_cache.values() if v}
                    )
                    cost_snapshot_map: Dict[str, float] = {}
                    price_snapshot_map: Dict[str, float] = {}
                    if all_internal_variant_ids:
                        try:
                            cost_snapshot_map = (
                                self.product_repo.batch_get_active_costs(
                                    all_internal_variant_ids
                                )
                            )
                            price_snapshot_map = (
                                self.product_repo.batch_get_active_prices(
                                    all_internal_variant_ids
                                )
                            )
                        except Exception as snap_err:
                            logger.warning(
                                f"Failed to fetch cost/price snapshots: {snap_err}. "
                                f"Snapshots will be NULL for this batch."
                            )

                    for item in all_line_items:
                        shopify_order_id = item.get("shopify_order_id")
                        order_id = order_id_map.get(shopify_order_id)
                        if not order_id:
                            continue

                        item["order_id"] = order_id
                        item["product_id"] = product_id_cache.get(
                            item.get("shopify_product_id")
                        )
                        internal_variant_id = variant_id_cache.get(
                            item.get("shopify_variant_id")
                        )
                        item["variant_id"] = internal_variant_id

                        # Attach immutable snapshots (None if no history exists yet)
                        cost_snap = cost_snapshot_map.get(internal_variant_id)
                        price_snap = price_snapshot_map.get(internal_variant_id)
                        item["cost_snapshot"] = cost_snap
                        item["price_snapshot"] = price_snap

                        # Gross margin % = ((price - cost) / price) * 100
                        if (
                            cost_snap is not None
                            and price_snap is not None
                            and price_snap > 0
                        ):
                            item["margin_snapshot_pct"] = round(
                                ((price_snap - cost_snap) / price_snap) * 100, 4
                            )
                        else:
                            item["margin_snapshot_pct"] = None

                        line_items_with_refs.append(item)

                    if line_items_with_refs:
                        self.line_item_repo.batch_upsert_line_items(
                            line_items_with_refs
                        )
                        logger.info(f"Synced {len(line_items_with_refs)} line items")

                has_next_page = page_info.get("hasNextPage", False)
                cursor = page_info.get("endCursor")
                if not cursor:
                    has_next_page = False

            logger.info(f"Completed sync of {total_synced} orders")
            return total_synced

        except Exception as e:
            logger.error(f"Sync failed: {str(e)}")
            raise
