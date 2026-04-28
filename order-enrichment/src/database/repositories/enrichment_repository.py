"""PostgreSQL repository for storing order enrichment results."""

import logging
from typing import List, Dict, Any, Optional
from psycopg2.extensions import connection
from psycopg2.extras import execute_values
import hashlib

from src.utils.tenant_context import tenant_context

logger = logging.getLogger(__name__)


class EnrichmentRepository:
    """Repository for storing order enrichment data in PostgreSQL."""

    def __init__(self, conn: connection):
        """
        Initialize repository with database connection.

        Args:
            conn: psycopg2 database connection
        """
        self.conn = conn

    def create_table_if_not_exists(self) -> None:
        """Create the order enrichments table if it doesn't exist."""
        table_name = tenant_context.get_table_name("order_enrichments")
        
        create_query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id BIGSERIAL PRIMARY KEY,
            neo4j_order_id BIGINT NOT NULL,
            external_order_id VARCHAR(255),
            created_date TIMESTAMP WITH TIME ZONE,
            order_amount DECIMAL(10, 2),
            original_landing_page TEXT,
            resolved_landing_page TEXT,
            decoded_from_jwt BOOLEAN DEFAULT FALSE,
            attribution_source VARCHAR(100),
            all_sources TEXT,
            utm_medium VARCHAR(255),
            utm_campaign VARCHAR(255),
            utm_content VARCHAR(255),
            utm_term VARCHAR(255),
            utm_id VARCHAR(255),
            campaign_id VARCHAR(255),
            ad_id VARCHAR(255),
            processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(neo4j_order_id)
        );
        
        CREATE INDEX IF NOT EXISTS idx_{table_name.replace('.', '_')}_external_order_id 
        ON {table_name} (external_order_id);
        
        CREATE INDEX IF NOT EXISTS idx_{table_name.replace('.', '_')}_created_date 
        ON {table_name} (created_date);
        
        CREATE INDEX IF NOT EXISTS idx_{table_name.replace('.', '_')}_attribution_source 
        ON {table_name} (attribution_source);
        """

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(create_query)
                logger.info(f"Ensured table {table_name} exists with proper structure")
        except Exception as e:
            logger.error(f"Error creating table {table_name}: {str(e)}")
            raise

    def upsert_enrichments(self, enrichments: List[Dict[str, Any]]) -> int:
        """
        Upsert order enrichment records.

        Args:
            enrichments: List of enrichment dictionaries

        Returns:
            Number of records upserted

        Raises:
            Exception: If database operation fails
        """
        if not enrichments:
            return 0

        table_name = tenant_context.get_table_name("order_enrichments")
        
        # Prepare data for bulk insert
        values = []
        for enrichment in enrichments:
            values.append((
                enrichment.get('neo4j_order_id'),
                enrichment.get('external_order_id'),
                enrichment.get('created_date'),
                enrichment.get('order_amount'),
                enrichment.get('original_landing_page', ''),
                enrichment.get('resolved_landing_page', ''),
                enrichment.get('decoded_from_jwt', False),
                enrichment.get('attribution_source', 'Unknown'),
                enrichment.get('all_sources', ''),
                enrichment.get('utm_medium', ''),
                enrichment.get('utm_campaign', ''),
                enrichment.get('utm_content', ''),
                enrichment.get('utm_term', ''),
                enrichment.get('utm_id', ''),
                enrichment.get('campaign_id', ''),
                enrichment.get('ad_id', '')
            ))

        upsert_query = f"""
        INSERT INTO {table_name} (
            neo4j_order_id, external_order_id, created_date, order_amount,
            original_landing_page, resolved_landing_page, decoded_from_jwt,
            attribution_source, all_sources, utm_medium, utm_campaign,
            utm_content, utm_term, utm_id, campaign_id, ad_id
        ) VALUES %s
        ON CONFLICT (neo4j_order_id) DO UPDATE SET
            external_order_id = EXCLUDED.external_order_id,
            created_date = EXCLUDED.created_date,
            order_amount = EXCLUDED.order_amount,
            original_landing_page = EXCLUDED.original_landing_page,
            resolved_landing_page = EXCLUDED.resolved_landing_page,
            decoded_from_jwt = EXCLUDED.decoded_from_jwt,
            attribution_source = EXCLUDED.attribution_source,
            all_sources = EXCLUDED.all_sources,
            utm_medium = EXCLUDED.utm_medium,
            utm_campaign = EXCLUDED.utm_campaign,
            utm_content = EXCLUDED.utm_content,
            utm_term = EXCLUDED.utm_term,
            utm_id = EXCLUDED.utm_id,
            campaign_id = EXCLUDED.campaign_id,
            ad_id = EXCLUDED.ad_id,
            processed_at = NOW()
        """

        try:
            with self.conn.cursor() as cursor:
                execute_values(
                    cursor,
                    upsert_query,
                    values,
                    template=None,
                    page_size=250
                )
                affected_rows = cursor.rowcount
                logger.info(f"Upserted {affected_rows} enrichment records into {table_name}")
                return affected_rows
        except Exception as e:
            logger.error(f"Error upserting enrichments into {table_name}: {str(e)}")
            raise

    def get_enrichments_by_date_range(
        self, 
        start_date: str, 
        end_date: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve enrichments within a date range.

        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            limit: Optional limit on records returned

        Returns:
            List of enrichment records
        """
        table_name = tenant_context.get_table_name("order_enrichments")
        
        query = f"""
        SELECT 
            neo4j_order_id, external_order_id, created_date, order_amount,
            original_landing_page, resolved_landing_page, decoded_from_jwt,
            attribution_source, all_sources, utm_medium, utm_campaign,
            utm_content, utm_term, utm_id, campaign_id, ad_id, processed_at
        FROM {table_name}
        WHERE created_date >= %s AND created_date < %s
        ORDER BY created_date
        """

        if limit:
            query += f" LIMIT {limit}"

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query, (start_date, end_date))
                columns = [desc[0] for desc in cursor.description]
                results = []
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
                
                logger.info(f"Retrieved {len(results)} enrichments from {table_name}")
                return results
        except Exception as e:
            logger.error(f"Error retrieving enrichments from {table_name}: {str(e)}")
            raise

    def get_enrichment_stats(self) -> Dict[str, Any]:
        """
        Get statistics about enrichment data.

        Returns:
            Dictionary with various statistics
        """
        table_name = tenant_context.get_table_name("order_enrichments")
        
        stats_query = f"""
        SELECT 
            COUNT(*) as total_records,
            COUNT(DISTINCT attribution_source) as unique_sources,
            COUNT(CASE WHEN decoded_from_jwt = true THEN 1 END) as jwt_decoded_count,
            COUNT(CASE WHEN utm_campaign != '' THEN 1 END) as with_utm_campaign,
            MAX(processed_at) as last_processed,
            MIN(created_date) as earliest_order,
            MAX(created_date) as latest_order
        FROM {table_name}
        """

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(stats_query)
                result = cursor.fetchone()
                if result:
                    columns = [desc[0] for desc in cursor.description]
                    stats = dict(zip(columns, result))
                    logger.info(f"Retrieved enrichment stats from {table_name}")
                    return stats
                return {}
        except Exception as e:
            logger.error(f"Error retrieving stats from {table_name}: {str(e)}")
            raise