"""Repository for order line items database operations."""

import logging
from typing import Dict, List
from uuid import UUID

from psycopg2.extensions import connection
from psycopg2.extras import execute_batch

from src.utils.tenant_context import tenant_context


logger = logging.getLogger(__name__)


class OrderLineItemRepository:
    """Handle all database operations for order line items."""

    def __init__(self, conn: connection):
        """
        Initialize repository with database connection.

        Args:
            conn: Active database connection
        """
        self.conn = conn

    def batch_upsert_line_items(self, line_items: List[Dict]) -> None:
        """
        Batch upsert order line items using explicit transaction.

        Snapshot columns (cost_snapshot, price_snapshot, margin_snapshot_pct)
        are written once on initial insert and are intentionally excluded from
        the ON CONFLICT DO UPDATE clause so they are never overwritten.
        This guarantees historical profitability accuracy — updating a product
        cost or price after an order was placed does not change the order's margin.

        Args:
            line_items: List of line item dictionaries with order_id
        """
        if not line_items:
            logger.info("No line items to upsert")
            return

        line_items_table = tenant_context.get_table_name("order_line_items")

        query = f"""
            INSERT INTO {line_items_table} (
                order_id,
                product_id,
                product_variant_id,
                shopify_line_item_id,
                shopify_product_id,
                shopify_variant_id,
                product_title,
                variant_title,
                sku,
                quantity,
                price,
                total_discount,
                cost_snapshot,
                price_snapshot,
                margin_snapshot_pct
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s
            )
            ON CONFLICT (order_id, shopify_line_item_id)
            DO UPDATE SET
                product_id         = EXCLUDED.product_id,
                product_variant_id = EXCLUDED.product_variant_id,
                shopify_product_id = EXCLUDED.shopify_product_id,
                shopify_variant_id = EXCLUDED.shopify_variant_id,
                product_title      = EXCLUDED.product_title,
                variant_title      = EXCLUDED.variant_title,
                sku                = EXCLUDED.sku,
                quantity           = EXCLUDED.quantity,
                price              = EXCLUDED.price,
                total_discount     = EXCLUDED.total_discount,
                updated_at         = CURRENT_TIMESTAMP
        """

        try:
            with self.conn.cursor() as cursor:
                batch_data = []
                for item in line_items:
                    batch_data.append(
                        (
                            item.get("order_id"),
                            item.get("product_id"),
                            item.get("variant_id"),
                            item.get("shopify_line_item_id"),
                            item.get("shopify_product_id"),
                            item.get("shopify_variant_id"),
                            item.get("product_title"),
                            item.get("variant_title"),
                            item.get("sku"),
                            item.get("quantity", 1),
                            item.get("price", 0.00),
                            item.get("total_discount", 0.00),
                            item.get("cost_snapshot"),
                            item.get("price_snapshot"),
                            item.get("margin_snapshot_pct"),
                        )
                    )

                execute_batch(cursor, query, batch_data, page_size=500)
            self.conn.commit()
            logger.info(f"Successfully upserted {len(line_items)} line items")

        except Exception as e:
            self.conn.rollback()
            logger.error(f"Batch line items upsert failed: {str(e)}")
            raise
