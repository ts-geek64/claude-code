"""Repository for product database operations."""

import json
import logging
from typing import Dict, List, Optional, Tuple
from uuid import UUID
from datetime import datetime

from psycopg2.extensions import connection
from psycopg2.extras import execute_values

from src.utils.tenant_context import tenant_context


logger = logging.getLogger(__name__)


class ProductRepository:
    """Handle all database operations for products."""

    def __init__(self, conn: connection):
        self.conn = conn

    def batch_upsert_products(
        self, integration_id: UUID, products: List[Dict]
    ) -> Dict[str, str]:
        """
        Batch upsert products and return a mapping of Shopify ID -> internal UUID.
        Uses the RETURNING clause so callers never need to re-query for IDs.

        Args:
            integration_id: Shopify integration UUID
            products: List of product dictionaries

        Returns:
            {shopify_product_id: internal_uuid_str}
        """
        if not products:
            return {}

        products_table = tenant_context.get_table_name("products")

        # execute_values supports RETURNING and fetch=True
        query = f"""
            INSERT INTO {products_table} (
                shopify_integration_id, shopify_product_id, title, handle,
                description_html, product_type, vendor, status, price,
                compare_at_price, unit_cost_amount, unit_cost_currency_code,
                total_inventory, tags, seo_title, seo_description, published_at,
                featured_media_alt, featured_media_url, media_url, media_count,
                variants_count, options, shopify_created_at, shopify_updated_at,
                last_synced_at
            ) VALUES %s
            ON CONFLICT (shopify_integration_id, shopify_product_id)
            DO UPDATE SET
                title = EXCLUDED.title,
                handle = EXCLUDED.handle,
                description_html = EXCLUDED.description_html,
                product_type = EXCLUDED.product_type,
                vendor = EXCLUDED.vendor,
                status = EXCLUDED.status,
                price = EXCLUDED.price,
                compare_at_price = EXCLUDED.compare_at_price,
                unit_cost_amount = EXCLUDED.unit_cost_amount,
                unit_cost_currency_code = EXCLUDED.unit_cost_currency_code,
                total_inventory = EXCLUDED.total_inventory,
                tags = EXCLUDED.tags,
                seo_title = EXCLUDED.seo_title,
                seo_description = EXCLUDED.seo_description,
                published_at = EXCLUDED.published_at,
                featured_media_alt = EXCLUDED.featured_media_alt,
                featured_media_url = EXCLUDED.featured_media_url,
                media_url = EXCLUDED.media_url,
                media_count = EXCLUDED.media_count,
                variants_count = EXCLUDED.variants_count,
                options = EXCLUDED.options,
                shopify_updated_at = EXCLUDED.shopify_updated_at,
                last_synced_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            RETURNING id, shopify_product_id
        """

        template = """(
            %s, %s, %s, %s, %s, %s, %s, %s::product_status, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, CURRENT_TIMESTAMP
        )"""

        try:
            batch_data = [
                (
                    str(integration_id),
                    p.get("shopify_product_id"),
                    p.get("title"),
                    p.get("handle"),
                    p.get("description_html"),
                    p.get("product_type"),
                    p.get("vendor"),
                    p.get("status", "ACTIVE"),
                    p.get("price"),
                    p.get("compare_at_price"),
                    p.get("unit_cost_amount"),
                    p.get("unit_cost_currency_code"),
                    p.get("total_inventory", 0),
                    p.get("tags"),
                    p.get("seo_title"),
                    p.get("seo_description"),
                    p.get("published_at"),
                    p.get("featured_media_alt"),
                    p.get("featured_media_url"),
                    p.get("media_url"),
                    p.get("media_count", 0),
                    p.get("variants_count", 0),
                    json.dumps(p.get("options")) if p.get("options") else None,
                    p.get("shopify_created_at"),
                    p.get("shopify_updated_at"),
                )
                for p in products
            ]

            with self.conn.cursor() as cursor:
                rows = execute_values(
                    cursor, query, batch_data, template=template, fetch=True
                )
                self.conn.commit()
                id_map = {row["shopify_product_id"]: row["id"] for row in rows}
                logger.info(f"Successfully upserted {len(products)} products")
                return id_map

        except Exception as e:
            self.conn.rollback()
            logger.error(f"Batch upsert failed: {str(e)}")
            raise

    def batch_upsert_product_variants(self, variants: List[Dict]) -> Dict[str, str]:
        """
        Batch upsert product variants and return {shopify_variant_id: internal_id}.

        Args:
            variants: List of variant dicts (must include product_id)

        Returns:
            {shopify_variant_id: internal_uuid_str}
        """
        if not variants:
            return {}

        variants_table = tenant_context.get_table_name("product_variants")

        query = f"""
            INSERT INTO {variants_table} (
                product_id, shopify_variant_id, shopify_product_id, title, sku,
                barcode, price, compare_at_price, unit_cost_amount,
                unit_cost_currency_code, inventory_quantity, inventory_policy,
                position, option1, option2, option3, is_available_for_sale,
                shopify_created_at, shopify_updated_at, last_synced_at
            ) VALUES %s
            ON CONFLICT (product_id, shopify_variant_id)
            DO UPDATE SET
                title = EXCLUDED.title,
                sku = EXCLUDED.sku,
                barcode = EXCLUDED.barcode,
                price = EXCLUDED.price,
                compare_at_price = EXCLUDED.compare_at_price,
                inventory_quantity = EXCLUDED.inventory_quantity,
                inventory_policy = EXCLUDED.inventory_policy,
                position = EXCLUDED.position,
                option1 = EXCLUDED.option1,
                option2 = EXCLUDED.option2,
                option3 = EXCLUDED.option3,
                is_available_for_sale = EXCLUDED.is_available_for_sale,
                shopify_updated_at = EXCLUDED.shopify_updated_at,
                last_synced_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            RETURNING id, shopify_variant_id
        """

        template = """(
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP
        )"""

        try:
            batch_data = [
                (
                    v.get("product_id"),
                    v.get("shopify_variant_id"),
                    v.get("shopify_product_id"),
                    v.get("title"),
                    v.get("sku"),
                    v.get("barcode"),
                    v.get("price"),
                    v.get("compare_at_price"),
                    v.get("unit_cost_amount"),
                    v.get("unit_cost_currency_code"),
                    v.get("inventory_quantity", 0),
                    v.get("inventory_policy"),
                    v.get("position"),
                    v.get("option1"),
                    v.get("option2"),
                    v.get("option3"),
                    v.get("is_available_for_sale", True),
                    v.get("shopify_created_at"),
                    v.get("shopify_updated_at"),
                )
                for v in variants
            ]

            with self.conn.cursor() as cursor:
                rows = execute_values(
                    cursor, query, batch_data, template=template, fetch=True
                )
                self.conn.commit()
                id_map = {row["shopify_variant_id"]: row["id"] for row in rows}
                logger.info(f"Successfully upserted {len(variants)} product variants")
                return id_map

        except Exception as e:
            self.conn.rollback()
            logger.error(f"Batch variant upsert failed: {str(e)}")
            raise

    def batch_get_product_ids(
        self, integration_id: UUID, shopify_product_ids: List[str]
    ) -> Dict[str, str]:
        """
        Batch resolve Shopify product IDs to internal UUIDs in a single query.

        Returns:
            {shopify_product_id: internal_uuid_str}
        """
        if not shopify_product_ids:
            return {}

        products_table = tenant_context.get_table_name("products")
        query = f"""
            SELECT id, shopify_product_id
            FROM {products_table}
            WHERE shopify_integration_id = %s
              AND shopify_product_id = ANY(%s)
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, (str(integration_id), list(shopify_product_ids)))
                return {
                    row["shopify_product_id"]: row["id"] for row in cursor.fetchall()
                }
        except Exception as e:
            logger.error(f"Failed to batch fetch product IDs: {str(e)}")
            raise

    def batch_get_variant_ids(self, shopify_variant_ids: List[str]) -> Dict[str, str]:
        """
        Batch resolve Shopify variant IDs to internal UUIDs in a single query.

        Returns:
            {shopify_variant_id: internal_uuid_str}
        """
        if not shopify_variant_ids:
            return {}

        variants_table = tenant_context.get_table_name("product_variants")
        query = f"""
            SELECT id, shopify_variant_id
            FROM {variants_table}
            WHERE shopify_variant_id = ANY(%s)
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, (list(shopify_variant_ids),))
                return {
                    row["shopify_variant_id"]: row["id"] for row in cursor.fetchall()
                }
        except Exception as e:
            logger.error(f"Failed to batch fetch variant IDs: {str(e)}")
            raise

    def get_product_id_by_shopify_id(
        self, integration_id: UUID, shopify_product_id: str
    ) -> Optional[str]:
        """Get single product ID — delegates to batch method."""
        mapping = self.batch_get_product_ids(integration_id, [shopify_product_id])
        return mapping.get(shopify_product_id)

    def get_variant_id_by_shopify_id(self, shopify_variant_id: str) -> Optional[str]:
        """Get single variant ID — delegates to batch method."""
        mapping = self.batch_get_variant_ids([shopify_variant_id])
        return mapping.get(shopify_variant_id)

    def get_latest_product_updated_at(self, integration_id: UUID) -> Optional[datetime]:
        """Get the latest shopify_updated_at for products."""
        products_table = tenant_context.get_table_name("products")
        query = f"""
            SELECT MAX(shopify_updated_at) as latest_updated_at
            FROM {products_table}
            WHERE shopify_integration_id = %s
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, (str(integration_id),))
                result = cursor.fetchone()
                return result["latest_updated_at"] if result else None
        except Exception as e:
            logger.error(f"Failed to fetch latest product updated at: {str(e)}")
            raise

    def get_latest_product_created_at(self, integration_id: UUID) -> Optional[datetime]:
        """Get the latest shopify_created_at for an integration."""
        products_table = tenant_context.get_table_name("products")
        query = f"""
            SELECT MAX(shopify_created_at) as latest_created_at
            FROM {products_table}
            WHERE shopify_integration_id = %s
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, (str(integration_id),))
                result = cursor.fetchone()
                return result["latest_created_at"] if result else None
        except Exception as e:
            logger.error(f"Failed to fetch latest product created at: {str(e)}")
            raise

    # =========================================================================
    # Cost history
    # =========================================================================

    def batch_upsert_cost_history(
        self,
        variant_history_records: List[Dict],
        source: str = "shopify",
    ) -> None:
        """
        Close existing open cost records and insert new ones for a batch of
        variants atomically within a single transaction.

        Each dict in variant_history_records must contain:
            variant_id    (str UUID)
            product_id    (str UUID)
            cost_amount   (float)
            currency_code (str | None)

        Args:
            variant_history_records: List of cost update dicts.
            source: Origin of the update — 'shopify' or 'admin_panel'.
        """
        if not variant_history_records:
            return

        history_table = tenant_context.get_table_name("product_variant_cost_history")
        variant_ids = [r["variant_id"] for r in variant_history_records]

        try:
            with self.conn.cursor() as cursor:
                # Step 1: Close all currently-open records for these variants.
                cursor.execute(
                    f"""
                    UPDATE {history_table}
                    SET effective_end_at = CURRENT_TIMESTAMP,
                        updated_at       = CURRENT_TIMESTAMP
                    WHERE product_variant_id = ANY(%s::uuid[])
                      AND effective_end_at IS NULL
                    """,
                    (variant_ids,),
                )

                # Step 2: Batch-insert new active records.
                execute_values(
                    cursor,
                    f"""
                    INSERT INTO {history_table}
                      (product_variant_id, product_id, cost_amount,
                       currency_code, effective_start_at, updated_by_source)
                    VALUES %s
                    """,
                    [
                        (
                            r["variant_id"],
                            r["product_id"],
                            r["cost_amount"],
                            r.get("currency_code"),
                            source,
                        )
                        for r in variant_history_records
                    ],
                    template="(%s, %s, %s, %s, CURRENT_TIMESTAMP, %s)",
                )
            self.conn.commit()
            logger.info(
                f"Batch cost history upserted for "
                f"{len(variant_history_records)} variants (source={source})"
            )
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Batch cost history upsert failed: {str(e)}")
            raise

    def upsert_variant_cost_history(
        self,
        variant_id: str,
        product_id: str,
        cost_amount: float,
        currency_code: Optional[str],
        source: str = "admin_panel",
    ) -> None:
        """
        Version-controlled insert for a single variant cost update.
        Calls the upsert_variant_cost_history Postgres stored procedure which
        closes the existing open record and inserts a fresh active one
        atomically.

        Used by the Admin Panel code path (single-variant update).

        Args:
            variant_id:    Internal UUID of the product variant.
            product_id:    Internal UUID of the parent product.
            cost_amount:   New cost value.
            currency_code: Currency code (e.g. 'USD').
            source:        Origin of the update (default 'admin_panel').
        """
        history_table = tenant_context.get_table_name("product_variant_cost_history")
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT upsert_variant_cost_history(%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        history_table,
                        variant_id,
                        product_id,
                        cost_amount,
                        currency_code,
                        source,
                    ),
                )
            self.conn.commit()
            logger.info(
                f"Cost history upserted for variant {variant_id} "
                f"(source={source}, cost={cost_amount})"
            )
        except Exception as e:
            self.conn.rollback()
            logger.error(
                f"Cost history upsert failed for variant {variant_id}: {str(e)}"
            )
            raise

    def batch_get_active_costs(
        self, variant_ids: List[str]
    ) -> Dict[str, Optional[float]]:
        """
        Batch-fetch the currently-active cost for a list of variant IDs.

        Returns:
            {variant_id: cost_amount}  — only includes variants that have an
            active cost record. Missing keys mean no history record exists yet.
        """
        if not variant_ids:
            return {}

        history_table = tenant_context.get_table_name("product_variant_cost_history")
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT product_variant_id, cost_amount
                    FROM {history_table}
                    WHERE product_variant_id = ANY(%s::uuid[])
                      AND effective_end_at IS NULL
                    """,
                    (variant_ids,),
                )
                return {
                    row["product_variant_id"]: float(row["cost_amount"])
                    for row in cursor.fetchall()
                }
        except Exception as e:
            logger.error(f"Failed to batch fetch active costs: {str(e)}")
            raise

    # =========================================================================
    # Price history
    # =========================================================================

    def batch_upsert_price_history(
        self,
        variant_history_records: List[Dict],
        source: str = "shopify",
    ) -> None:
        """
        Close existing open price records and insert new ones for a batch of
        variants atomically within a single transaction.

        Each dict in variant_history_records must contain:
            variant_id       (str UUID)
            product_id       (str UUID)
            price_amount     (float)
            compare_at_price (float | None)

        Args:
            variant_history_records: List of price update dicts.
            source: Origin of the update — 'shopify' or 'admin_panel'.
        """
        if not variant_history_records:
            return

        history_table = tenant_context.get_table_name("product_variant_price_history")
        variant_ids = [r["variant_id"] for r in variant_history_records]

        try:
            with self.conn.cursor() as cursor:
                # Step 1: Close all currently-open records for these variants.
                cursor.execute(
                    f"""
                    UPDATE {history_table}
                    SET effective_end_at = CURRENT_TIMESTAMP,
                        updated_at       = CURRENT_TIMESTAMP
                    WHERE product_variant_id = ANY(%s::uuid[])
                      AND effective_end_at IS NULL
                    """,
                    (variant_ids,),
                )

                # Step 2: Batch-insert new active records.
                execute_values(
                    cursor,
                    f"""
                    INSERT INTO {history_table}
                      (product_variant_id, product_id, price_amount,
                       compare_at_price, effective_start_at, updated_by_source)
                    VALUES %s
                    """,
                    [
                        (
                            r["variant_id"],
                            r["product_id"],
                            r["price_amount"],
                            r.get("compare_at_price"),
                            source,
                        )
                        for r in variant_history_records
                    ],
                    template="(%s, %s, %s, %s, CURRENT_TIMESTAMP, %s)",
                )
            self.conn.commit()
            logger.info(
                f"Batch price history upserted for "
                f"{len(variant_history_records)} variants (source={source})"
            )
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Batch price history upsert failed: {str(e)}")
            raise

    def upsert_variant_price_history(
        self,
        variant_id: str,
        product_id: str,
        price_amount: float,
        compare_at_price: Optional[float],
        source: str = "admin_panel",
    ) -> None:
        """
        Version-controlled insert for a single variant price update.
        Calls the upsert_variant_price_history Postgres stored procedure.

        Used by the Admin Panel code path (single-variant update).

        Args:
            variant_id:       Internal UUID of the product variant.
            product_id:       Internal UUID of the parent product.
            price_amount:     New price value.
            compare_at_price: Compare-at price (optional).
            source:           Origin of the update (default 'admin_panel').
        """
        history_table = tenant_context.get_table_name("product_variant_price_history")
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT upsert_variant_price_history(%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        history_table,
                        variant_id,
                        product_id,
                        price_amount,
                        compare_at_price,
                        source,
                    ),
                )
            self.conn.commit()
            logger.info(
                f"Price history upserted for variant {variant_id} "
                f"(source={source}, price={price_amount})"
            )
        except Exception as e:
            self.conn.rollback()
            logger.error(
                f"Price history upsert failed for variant {variant_id}: {str(e)}"
            )
            raise

    def batch_get_active_prices(
        self, variant_ids: List[str]
    ) -> Dict[str, Optional[float]]:
        """
        Batch-fetch the currently-active price for a list of variant IDs.

        Returns:
            {variant_id: price_amount}  — only includes variants that have an
            active price record. Missing keys mean no history record exists yet.
        """
        if not variant_ids:
            return {}

        history_table = tenant_context.get_table_name("product_variant_price_history")
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT product_variant_id, price_amount
                    FROM {history_table}
                    WHERE product_variant_id = ANY(%s::uuid[])
                      AND effective_end_at IS NULL
                    """,
                    (variant_ids,),
                )
                return {
                    row["product_variant_id"]: float(row["price_amount"])
                    for row in cursor.fetchall()
                }
        except Exception as e:
            logger.error(f"Failed to batch fetch active prices: {str(e)}")
            raise
