"""Repository for customer database operations."""

import logging
from typing import Dict, List, Optional
from uuid import UUID
from datetime import datetime

from psycopg2.extensions import connection
from psycopg2.extras import execute_batch

from src.utils.tenant_context import tenant_context


logger = logging.getLogger(__name__)


class CustomerRepository:
    """Handle all database operations for customers."""

    def __init__(self, conn: connection):
        """
        Initialize repository with database connection.

        Args:
            conn: Active database connection
        """
        self.conn = conn

    def batch_upsert_customers(
        self, integration_id: UUID, customers: List[Dict]
    ) -> None:
        """
        Batch upsert customers using explicit transaction.

        Args:
            integration_id: Shopify integration UUID
            customers: List of customer dictionaries
        """
        if not customers:
            logger.info("No customers to upsert")
            return

        customers_table = tenant_context.get_table_name("customers")

        query = f"""
            INSERT INTO {customers_table} (
                shopify_integration_id, shopify_customer_id, display_name, email,
                first_name, last_name, phone, locale, has_accepted_marketing,
                marketing_opt_in_level, email_marketing_state, sms_marketing_state,
                total_spent, orders_count, predicted_spend_tier, rfm_group,
                lifetime_duration, rfm_score, is_email_verified, is_tax_exempt,
                tax_exemptions, state, tags, note, default_address_id, company,
                address1, address2, city, province, province_code, country,
                country_code, zip, geo_location, formatted,
                last_purchased_at, shopify_created_at, shopify_updated_at, last_synced_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s::customer_rfm_group, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                ST_SetSRID(ST_MakePoint(%s::numeric, %s::numeric), 4326),
                %s, %s, %s, %s, CURRENT_TIMESTAMP
            )
            ON CONFLICT (shopify_integration_id, shopify_customer_id)
            DO UPDATE SET
                display_name = EXCLUDED.display_name,
                email = EXCLUDED.email,
                first_name = EXCLUDED.first_name,
                last_name = EXCLUDED.last_name,
                phone = EXCLUDED.phone,
                locale = EXCLUDED.locale,
                has_accepted_marketing = EXCLUDED.has_accepted_marketing,
                marketing_opt_in_level = EXCLUDED.marketing_opt_in_level,
                email_marketing_state = EXCLUDED.email_marketing_state,
                sms_marketing_state = EXCLUDED.sms_marketing_state,
                total_spent = EXCLUDED.total_spent,
                orders_count = EXCLUDED.orders_count,
                predicted_spend_tier = EXCLUDED.predicted_spend_tier,
                rfm_group = EXCLUDED.rfm_group,
                lifetime_duration = EXCLUDED.lifetime_duration,
                is_email_verified = EXCLUDED.is_email_verified,
                is_tax_exempt = EXCLUDED.is_tax_exempt,
                tax_exemptions = EXCLUDED.tax_exemptions,
                state = EXCLUDED.state,
                tags = EXCLUDED.tags,
                note = EXCLUDED.note,
                default_address_id = EXCLUDED.default_address_id,
                company = EXCLUDED.company,
                address1 = EXCLUDED.address1,
                address2 = EXCLUDED.address2,
                city = EXCLUDED.city,
                province = EXCLUDED.province,
                province_code = EXCLUDED.province_code,
                country = EXCLUDED.country,
                country_code = EXCLUDED.country_code,
                zip = EXCLUDED.zip,
                geo_location = CASE
                    WHEN EXCLUDED.geo_location IS NOT NULL
                    THEN EXCLUDED.geo_location
                    ELSE {customers_table}.geo_location
                END,
                formatted = EXCLUDED.formatted,
                last_purchased_at = EXCLUDED.last_purchased_at,
                shopify_updated_at = EXCLUDED.shopify_updated_at,
                last_synced_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
        """

        try:
            with self.conn.cursor() as cursor:
                batch_data = [
                    (
                        str(integration_id),
                        c.get("shopify_customer_id"),
                        c.get("display_name"),
                        c.get("email"),
                        c.get("first_name"),
                        c.get("last_name"),
                        c.get("phone"),
                        c.get("locale"),
                        c.get("has_accepted_marketing", False),
                        c.get("marketing_opt_in_level"),
                        c.get("email_marketing_state"),
                        c.get("sms_marketing_state"),
                        c.get("total_spent", 0.00),
                        c.get("orders_count", 0),
                        c.get("predicted_spend_tier"),
                        c.get("rfm_group", "NEW"),
                        c.get("lifetime_duration"),
                        c.get("rfm_score", -1),
                        c.get("is_email_verified", False),
                        c.get("is_tax_exempt", False),
                        c.get("tax_exemptions"),
                        c.get("state"),
                        c.get("tags"),
                        c.get("note"),
                        c.get("default_address_id"),
                        c.get("company"),
                        c.get("address1"),
                        c.get("address2"),
                        c.get("city"),
                        c.get("province"),
                        c.get("province_code"),
                        c.get("country"),
                        c.get("country_code"),
                        c.get("zip"),
                        c.get("longitude"),
                        c.get("latitude"),
                        c.get("formatted"),
                        c.get("last_purchased_at"),
                        c.get("shopify_created_at"),
                        c.get("shopify_updated_at"),
                    )
                    for c in customers
                ]
                execute_batch(cursor, query, batch_data, page_size=500)
                self.conn.commit()
                logger.info(f"Successfully upserted {len(customers)} customers")

        except Exception as e:
            self.conn.rollback()
            logger.error(f"Batch upsert failed: {str(e)}")
            raise

    def batch_get_customer_ids(
        self, integration_id: UUID, shopify_customer_ids: List[str]
    ) -> Dict[str, str]:
        """
        Batch resolve Shopify customer IDs to internal UUIDs in a single query.
        Replaces N individual get_customer_id_by_shopify_id() calls.

        Returns:
            {shopify_customer_id: internal_uuid_str}
        """
        if not shopify_customer_ids:
            return {}

        customers_table = tenant_context.get_table_name("customers")
        query = f"""
            SELECT id, shopify_customer_id
            FROM {customers_table}
            WHERE shopify_integration_id = %s
              AND shopify_customer_id = ANY(%s)
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, (str(integration_id), list(shopify_customer_ids)))
                return {
                    row["shopify_customer_id"]: row["id"] for row in cursor.fetchall()
                }
        except Exception as e:
            logger.error(f"Failed to batch fetch customer IDs: {str(e)}")
            raise

    def get_customer_id_by_shopify_id(
        self, integration_id: UUID, shopify_customer_id: str
    ) -> Optional[str]:
        """Get single customer ID — delegates to batch method."""
        mapping = self.batch_get_customer_ids(integration_id, [shopify_customer_id])
        return mapping.get(shopify_customer_id)

    def get_latest_customer_created_at(
        self, integration_id: UUID
    ) -> Optional[datetime]:
        """Get the latest shopify_created_at for an integration."""
        customers_table = tenant_context.get_table_name("customers")
        query = f"""
            SELECT MAX(shopify_created_at) as latest_created_at
            FROM {customers_table}
            WHERE shopify_integration_id = %s
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, (str(integration_id),))
                result = cursor.fetchone()
                return result["latest_created_at"] if result else None
        except Exception as e:
            logger.error(f"Failed to fetch latest customer created at: {str(e)}")
            raise
