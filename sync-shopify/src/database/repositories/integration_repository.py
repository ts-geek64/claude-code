"""Repository for Shopify integration database operations."""

import logging
from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from psycopg2.extensions import connection

from src.utils.tenant_context import tenant_context


logger = logging.getLogger(__name__)


class IntegrationRepository:
    """Handle all database operations for integrations."""

    def __init__(self, conn: connection):
        """
        Initialize repository with database connection.

        Args:
            conn: Active database connection
        """
        self.conn = conn

    def get_active_shopify_integrations(
        self, integration_ids: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Fetch all active Shopify integrations.

        Args:
            integration_ids: Optional list of specific integration IDs to fetch

        Returns:
            List of integration dictionaries with store details
        """
        integrations_table = tenant_context.get_table_name("integrations")
        shopify_integrations_table = tenant_context.get_table_name(
            "shopify_integrations"
        )

        query = f"""
            SELECT 
                i.id,
                i.token,
                i.last_refreshed_at,
                si.myshopify_domain,
                si.shop_name
            FROM {integrations_table} i
            JOIN {shopify_integrations_table} si ON i.id = si.integration_id
            WHERE i.integration_type = 'shopify'
                AND i.is_active = TRUE
        """

        params = []
        if integration_ids:
            query += " AND i.id = ANY(%s::uuid[])"
            params.append(integration_ids)

        query += " ORDER BY i.created_at"

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, tuple(params) if params else None)
                results = cursor.fetchall()
                logger.info(f"Found {len(results)} active Shopify integrations")
                self.conn.commit()
                return results
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to fetch integrations: {str(e)}")
            raise

    def update_health_status(self, integration_id: UUID, status: str) -> None:
        """
        Update integration health status.

        Args:
            integration_id: Integration UUID
            status: Health status ('healthy' or 'unhealthy')
        """
        integrations_table = tenant_context.get_table_name("integrations")

        query = f"""
            UPDATE {integrations_table}
            SET health_status = %s::integration_health_status,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, (status, str(integration_id)))
                self.conn.commit()
                logger.info(f"Updated health status to {status} for {integration_id}")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to update health status: {str(e)}")
            raise

    def update_last_sync_timestamp(self, integration_id: UUID) -> None:
        """
        Update last sync timestamp after successful sync.

        Args:
            integration_id: Integration UUID
        """
        integrations_table = tenant_context.get_table_name("integrations")

        query = f"""
            UPDATE {integrations_table}
            SET last_refreshed_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, (str(integration_id),))
                self.conn.commit()
                logger.info(f"Updated sync timestamp for {integration_id}")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to update sync timestamp: {str(e)}")
            raise
