"""Repository for order database operations."""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from psycopg2.extensions import connection
from psycopg2.extras import execute_values

from src.utils.tenant_context import tenant_context


logger = logging.getLogger(__name__)


class OrderRepository:
    """Handle all database operations for orders."""

    def __init__(self, conn: connection):
        self.conn = conn

    def batch_upsert_orders(
        self, integration_id: UUID, orders: List[Dict]
    ) -> Dict[str, str]:
        """
        Batch upsert orders and return {shopify_order_id: internal_uuid}.
        Uses RETURNING so callers never need to re-query for IDs.

        Args:
            integration_id: Shopify integration UUID
            orders: List of order dictionaries

        Returns:
            {shopify_order_id: internal_uuid_str}
        """
        if not orders:
            return {}

        orders_table = tenant_context.get_table_name("orders")

        query = f"""
            INSERT INTO {orders_table} (
                shopify_integration_id, shopify_order_id, customer_id,
                order_number, order_name, email, phone, financial_status,
                fulfillment_status, order_status, return_status, is_confirmed,
                is_test_order, currency, total_tax, total_discounts,
                total_shipping, total_price, total_refunded_shipping,
                total_refunded_amount, net_payment_amount, note, tags,
                discount_codes, payment_gateway_names, cancelled_at, cancel_reason,
                closed_at, shopify_created_at, shopify_updated_at,
                last_landing_page, last_utm_source, last_utm_medium,
                last_utm_campaign, last_utm_content, last_utm_term, last_utm_id,
                last_original_landing_page, last_original_utm_source,
                first_landing_page, first_utm_source, first_utm_medium,
                first_utm_campaign, first_utm_content, first_utm_term, first_utm_id,
                first_original_landing_page, first_original_utm_source,
                last_synced_at
            ) VALUES %s
            ON CONFLICT (shopify_integration_id, shopify_order_id)
            DO UPDATE SET
                customer_id = EXCLUDED.customer_id,
                order_number = EXCLUDED.order_number,
                order_name = EXCLUDED.order_name,
                email = EXCLUDED.email,
                phone = EXCLUDED.phone,
                financial_status = EXCLUDED.financial_status,
                fulfillment_status = EXCLUDED.fulfillment_status,
                order_status = EXCLUDED.order_status,
                return_status = EXCLUDED.return_status,
                is_confirmed = EXCLUDED.is_confirmed,
                is_test_order = EXCLUDED.is_test_order,
                currency = EXCLUDED.currency,
                total_tax = EXCLUDED.total_tax,
                total_discounts = EXCLUDED.total_discounts,
                total_shipping = EXCLUDED.total_shipping,
                total_price = EXCLUDED.total_price,
                total_refunded_shipping = EXCLUDED.total_refunded_shipping,
                total_refunded_amount = EXCLUDED.total_refunded_amount,
                net_payment_amount = EXCLUDED.net_payment_amount,
                note = EXCLUDED.note,
                tags = EXCLUDED.tags,
                discount_codes = EXCLUDED.discount_codes,
                payment_gateway_names = EXCLUDED.payment_gateway_names,
                cancelled_at = EXCLUDED.cancelled_at,
                cancel_reason = EXCLUDED.cancel_reason,
                closed_at = EXCLUDED.closed_at,
                shopify_updated_at = EXCLUDED.shopify_updated_at,
                last_landing_page = EXCLUDED.last_landing_page,
                last_utm_source = EXCLUDED.last_utm_source,
                last_utm_medium = EXCLUDED.last_utm_medium,
                last_utm_campaign = EXCLUDED.last_utm_campaign,
                last_utm_content = EXCLUDED.last_utm_content,
                last_utm_term = EXCLUDED.last_utm_term,
                last_utm_id = EXCLUDED.last_utm_id,
                last_original_landing_page = EXCLUDED.last_original_landing_page,
                last_original_utm_source = EXCLUDED.last_original_utm_source,
                first_landing_page = EXCLUDED.first_landing_page,
                first_utm_source = EXCLUDED.first_utm_source,
                first_utm_medium = EXCLUDED.first_utm_medium,
                first_utm_campaign = EXCLUDED.first_utm_campaign,
                first_utm_content = EXCLUDED.first_utm_content,
                first_utm_term = EXCLUDED.first_utm_term,
                first_utm_id = EXCLUDED.first_utm_id,
                first_original_landing_page = EXCLUDED.first_original_landing_page,
                first_original_utm_source = EXCLUDED.first_original_utm_source,
                last_synced_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            RETURNING id, shopify_order_id
        """

        template = """(
            %s, %s, %s, %s, %s, %s, %s, %s::financial_status,
            %s::fulfillment_status, %s::order_status,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP
        )"""

        try:
            batch_data = [
                (
                    str(integration_id),
                    o.get("shopify_order_id"),
                    o.get("customer_id"),
                    o.get("order_number"),
                    o.get("order_name"),
                    o.get("email"),
                    o.get("phone"),
                    o.get("financial_status"),
                    o.get("fulfillment_status"),
                    o.get("order_status", "pending"),
                    o.get("return_status"),
                    o.get("is_confirmed", True),
                    o.get("is_test_order", False),
                    o.get("currency", "USD"),
                    o.get("total_tax", 0.00),
                    o.get("total_discounts", 0.00),
                    o.get("total_shipping", 0.00),
                    o.get("total_price", 0.00),
                    o.get("total_refunded_shipping", 0.00),
                    o.get("total_refunded_amount", 0.00),
                    o.get("net_payment_amount", 0.00),
                    o.get("note"),
                    o.get("tags"),
                    (
                        json.dumps(o.get("discount_codes"))
                        if o.get("discount_codes")
                        else None
                    ),
                    o.get("payment_gateway_names"),
                    o.get("cancelled_at"),
                    o.get("cancel_reason"),
                    o.get("closed_at"),
                    o.get("shopify_created_at"),
                    o.get("shopify_updated_at"),
                    o.get("last_landing_page"),
                    o.get("last_utm_source"),
                    o.get("last_utm_medium"),
                    o.get("last_utm_campaign"),
                    o.get("last_utm_content"),
                    o.get("last_utm_term"),
                    o.get("last_utm_id"),
                    o.get("last_original_landing_page"),
                    o.get("last_original_utm_source"),
                    o.get("first_landing_page"),
                    o.get("first_utm_source"),
                    o.get("first_utm_medium"),
                    o.get("first_utm_campaign"),
                    o.get("first_utm_content"),
                    o.get("first_utm_term"),
                    o.get("first_utm_id"),
                    o.get("first_original_landing_page"),
                    o.get("first_original_utm_source"),
                )
                for o in orders
            ]

            with self.conn.cursor() as cursor:
                rows = execute_values(
                    cursor, query, batch_data, template=template, fetch=True
                )
                self.conn.commit()
                id_map = {row["shopify_order_id"]: row["id"] for row in rows}
                logger.info(f"Successfully upserted {len(orders)} orders")
                return id_map

        except Exception as e:
            self.conn.rollback()
            logger.error(f"Batch upsert failed: {str(e)}")
            raise

    def batch_get_order_ids(
        self, integration_id: UUID, shopify_order_ids: List[str]
    ) -> Dict[str, str]:
        """
        Batch resolve Shopify order IDs to internal UUIDs in a single query.

        Returns:
            {shopify_order_id: internal_uuid_str}
        """
        if not shopify_order_ids:
            return {}

        orders_table = tenant_context.get_table_name("orders")
        query = f"""
            SELECT id, shopify_order_id
            FROM {orders_table}
            WHERE shopify_integration_id = %s
              AND shopify_order_id = ANY(%s)
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, (str(integration_id), list(shopify_order_ids)))
                return {row["shopify_order_id"]: row["id"] for row in cursor.fetchall()}
        except Exception as e:
            logger.error(f"Failed to batch fetch order IDs: {str(e)}")
            raise

    def get_order_id_by_shopify_id(
        self, integration_id: UUID, shopify_order_id: str
    ) -> Optional[str]:
        """Get single order ID — delegates to batch method."""
        mapping = self.batch_get_order_ids(integration_id, [shopify_order_id])
        return mapping.get(shopify_order_id)

    def get_latest_order_created_at(self, integration_id: UUID) -> Optional[datetime]:
        """Get the latest shopify_created_at for an integration."""
        orders_table = tenant_context.get_table_name("orders")
        query = f"""
            SELECT MAX(shopify_created_at) as latest_created_at
            FROM {orders_table}
            WHERE shopify_integration_id = %s
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, (str(integration_id),))
                result = cursor.fetchone()
                return result["latest_created_at"] if result else None
        except Exception as e:
            logger.error(f"Failed to fetch latest order created at: {str(e)}")
            raise
