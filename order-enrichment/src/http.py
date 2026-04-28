"""HTTP handler for order enrichment pipeline."""

import json
import logging
from typing import Dict, Any, Tuple

from src.config.settings import settings
from src.database.database_context import db_context
from src.services.enrichment_service import EnrichmentService
from src.utils.tenant_context import tenant_context
from src.utils.logger import setup_logging

logger = logging.getLogger(__name__)


def order_enrichment_pipeline(request_data: Dict[str, Any]) -> Tuple[str, int]:
    """
    Process order enrichment HTTP request.

    Args:
        request_data: JSON request data

    Returns:
        Tuple of (response_body, status_code)
    """
    setup_logging()
    logger.info("Starting order enrichment pipeline")

    try:
        # Validate settings
        settings.validate()
        logger.info("Settings validated successfully")

        # Extract tenant_id from request
        tenant_id = request_data.get('tenant_id')
        if not tenant_id:
            logger.error("Missing tenant_id in request")
            return json.dumps({
                'status': 'error',
                'message': 'tenant_id is required'
            }), 400

        # Set tenant context
        tenant_context.set_tenant(tenant_id)
        logger.info(f"Tenant context set to: {tenant_id}")

        # Initialize database connection pool
        db_context.initialize()

        # Process the enrichment request
        service = None
        try:
            with db_context.get_connection() as conn:
                service = EnrichmentService(conn)
                
                # Determine the type of enrichment request
                if 'year' in request_data and 'month' in request_data:
                    # Month-based enrichment
                    year = int(request_data['year'])
                    month = int(request_data['month'])
                    limit = request_data.get('limit')
                    
                    if limit is not None:
                        limit = int(limit)
                    
                    logger.info(f"Processing month-based enrichment: {year}-{month:02d}")
                    result = service.enrich_orders_for_month(year, month, limit)
                    
                elif 'start_date' in request_data and 'end_date' in request_data:
                    # Date range-based enrichment
                    start_date = request_data['start_date']
                    end_date = request_data['end_date']
                    limit = request_data.get('limit')
                    
                    if limit is not None:
                        limit = int(limit)
                    
                    logger.info(f"Processing date range enrichment: {start_date} to {end_date}")
                    result = service.enrich_orders_by_date_range(start_date, end_date, limit)
                    
                elif request_data.get('action') == 'stats':
                    # Get enrichment statistics
                    logger.info("Retrieving enrichment statistics")
                    result = service.get_enrichment_stats()
                    
                else:
                    # Default: enrich September 2025 as per original script
                    logger.info("No specific parameters provided, defaulting to September 2025")
                    result = service.enrich_orders_for_month(2025, 9)

                # Return response
                status_code = 200 if result.get('status') == 'success' else 500
                response = json.dumps(result, default=str, ensure_ascii=False)
                
                logger.info(f"Pipeline completed with status: {result.get('status')}")
                return response, status_code

        finally:
            # Clean up
            if service:
                service.close()
            db_context.close()

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return json.dumps({
            'status': 'error',
            'message': f'Validation error: {str(e)}'
        }), 400

    except Exception as e:
        logger.error(f"Unexpected error in pipeline: {str(e)}")
        return json.dumps({
            'status': 'error',
            'message': 'Internal server error'
        }), 500

    finally:
        # Always clear tenant context
        try:
            tenant_context.clear_tenant()
        except Exception as e:
            logger.error(f"Error clearing tenant context: {str(e)}")