"""Service for syncing Shopify products."""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from src.data_processor.processor import DataProcessor
from src.database.repositories.product_repository import ProductRepository
from src.http import ShopifyHTTPClient
from src.utils.queries import PRODUCTS_QUERY
from src.utils.tenant_context import tenant_context
from config.settings import settings


logger = logging.getLogger(__name__)


class ProductSyncService:
    """Handle product synchronization logic."""

    def __init__(
        self,
        http_client: ShopifyHTTPClient,
        product_repo: ProductRepository,
        data_processor: DataProcessor,
    ):
        self.http_client = http_client
        self.product_repo = product_repo
        self.data_processor = data_processor

    def sync_products(
        self, integration_id: UUID, last_sync: Optional[datetime] = None
    ) -> int:
        """
        Sync products from Shopify using cursor pagination.

        Key optimization: batch_upsert_products now returns a
        {shopify_product_id: internal_id} map via RETURNING, so variants
        are linked without any additional DB round-trips per product.

        Returns:
            Total number of products synced
        """
        total_synced = 0
        cursor = None
        has_next_page = True

        query_filter = None
        if last_sync:
            formatted_date = last_sync.strftime("%Y-%m-%dT%H:%M:%SZ")
            query_filter = f"updated_at:>='{formatted_date}'"
            logger.info(f"Syncing products updated after {formatted_date}")

        try:
            while has_next_page:
                variables = {
                    "first": settings.SHOPIFY_BATCH_SIZE,
                    "after": cursor,
                    "query": query_filter,
                }

                response = self.http_client.execute_query(PRODUCTS_QUERY, variables)

                products_data = (response.get("data") or {}).get("products") or {}
                nodes = products_data.get("nodes") or []
                page_info = products_data.get("pageInfo") or {}

                if not nodes:
                    logger.info("No more products to sync")
                    break

                processed_products = []
                all_variants = []

                for product_node in nodes:
                    try:
                        if not product_node or not isinstance(product_node, dict):
                            logger.warning("Missing or invalid product node")
                            continue

                        processed = self.data_processor.process_product(product_node)
                        processed_products.append(processed["product"])
                        all_variants.extend(processed["variants"])

                    except Exception as e:
                        logger.error(f"Failed to process product: {str(e)}")
                        continue

                if processed_products:
                    # OPTIMIZATION: batch_upsert_products returns the shopify→internal
                    # ID mapping via RETURNING, eliminating N individual SELECT queries.
                    product_id_map = self.product_repo.batch_upsert_products(
                        integration_id, processed_products
                    )
                    total_synced += len(processed_products)
                    logger.info(
                        f"Synced batch of {len(processed_products)} products "
                        f"(total: {total_synced})"
                    )

                    # Link variants using the returned ID map — zero extra DB queries
                    if all_variants:
                        variants_with_product_id = []
                        for variant in all_variants:
                            shopify_product_id = variant.get("shopify_product_id")
                            product_id = product_id_map.get(shopify_product_id)
                            if product_id:
                                variant["product_id"] = product_id
                                variants_with_product_id.append(variant)

                        if variants_with_product_id:
                            variant_id_map = (
                                self.product_repo.batch_upsert_product_variants(
                                    variants_with_product_id
                                )
                            )
                            logger.info(
                                f"Synced {len(variants_with_product_id)} product variants"
                            )

                            # ── History tracking ─────────────────────────────
                            # Check tenant policy before writing any history.
                            # ALLOWED:
                            #   1. Initial creation (no history record exists yet)
                            #   2. Update IF value changed AND tenant policy allows it
                            #
                            # Rejected updates are logged for audit but do not
                            # create any history records.
                            internal_vids = list(variant_id_map.values())
                            existing_costs = self.product_repo.batch_get_active_costs(
                                internal_vids
                            )
                            existing_prices = self.product_repo.batch_get_active_prices(
                                internal_vids
                            )

                            cost_records = []
                            price_records = []
                            rejected_cost = 0
                            rejected_price = 0

                            for variant in variants_with_product_id:
                                shopify_vid = variant.get("shopify_variant_id")
                                internal_vid = variant_id_map.get(shopify_vid)
                                product_id = variant.get("product_id")

                                if not internal_vid or not product_id:
                                    continue

                                # ── Cost history ─────────────────────────────
                                cost_amount = variant.get("unit_cost_amount")
                                if cost_amount is not None and cost_amount > 0:
                                    existing_cost = existing_costs.get(internal_vid)

                                    if existing_cost is None:
                                        # Initial creation — ALWAYS allow
                                        cost_records.append(
                                            {
                                                "variant_id": internal_vid,
                                                "product_id": product_id,
                                                "cost_amount": cost_amount,
                                                "currency_code": variant.get(
                                                    "unit_cost_currency_code"
                                                ),
                                            }
                                        )
                                    else:
                                        # Update — check if value changed
                                        if (
                                            abs(float(cost_amount) - existing_cost)
                                            > 0.0001
                                        ):
                                            if tenant_context.shopify_can_update(
                                                "cost"
                                            ):
                                                cost_records.append(
                                                    {
                                                        "variant_id": internal_vid,
                                                        "product_id": product_id,
                                                        "cost_amount": cost_amount,
                                                        "currency_code": variant.get(
                                                            "unit_cost_currency_code"
                                                        ),
                                                    }
                                                )
                                            else:
                                                rejected_cost += 1

                                # ── Price history ────────────────────────────
                                price_amount = variant.get("price")
                                if price_amount is not None:
                                    existing_price = existing_prices.get(internal_vid)

                                    if existing_price is None:
                                        # Initial creation — ALWAYS allow
                                        price_records.append(
                                            {
                                                "variant_id": internal_vid,
                                                "product_id": product_id,
                                                "price_amount": price_amount,
                                                "compare_at_price": variant.get(
                                                    "compare_at_price"
                                                ),
                                            }
                                        )
                                    else:
                                        # Update — check if value changed
                                        if (
                                            abs(float(price_amount) - existing_price)
                                            > 0.0001
                                        ):
                                            if tenant_context.shopify_can_update(
                                                "price"
                                            ):
                                                price_records.append(
                                                    {
                                                        "variant_id": internal_vid,
                                                        "product_id": product_id,
                                                        "price_amount": price_amount,
                                                        "compare_at_price": variant.get(
                                                            "compare_at_price"
                                                        ),
                                                    }
                                                )
                                            else:
                                                rejected_price += 1

                            if rejected_cost:
                                logger.info(
                                    f"Tenant policy: {rejected_cost} Shopify cost "
                                    f"update(s) rejected (updates blocked for this tenant)"
                                )
                            if rejected_price:
                                logger.info(
                                    f"Tenant policy: {rejected_price} Shopify price "
                                    f"update(s) rejected (updates blocked for this tenant)"
                                )

                            if cost_records:
                                self.product_repo.batch_upsert_cost_history(
                                    cost_records, source="shopify"
                                )
                                logger.info(
                                    f"Cost history updated for {len(cost_records)} variants"
                                )

                            if price_records:
                                self.product_repo.batch_upsert_price_history(
                                    price_records, source="shopify"
                                )
                                logger.info(
                                    f"Price history updated for {len(price_records)} variants"
                                )

                has_next_page = page_info.get("hasNextPage", False)
                cursor = page_info.get("endCursor")
                if not cursor:
                    has_next_page = False

            logger.info(f"Completed sync of {total_synced} products")
            return total_synced

        except Exception as e:
            logger.error(f"Product sync failed: {str(e)}")
            raise
