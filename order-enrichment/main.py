"""Main entry point for order enrichment Cloud Function."""

import functions_framework
import logging
from flask import Request, Response

from src.http import order_enrichment_pipeline

logger = logging.getLogger(__name__)


@functions_framework.http
def order_enrichment(request: Request) -> Response:
    """
    HTTP Cloud Function entry point for order enrichment.

    Args:
        request: Flask request object

    Returns:
        Flask response object
    """
    try:
        # Parse request data
        request_json = request.get_json(silent=True) or {}
        
        # Process the enrichment pipeline
        response_body, status_code = order_enrichment_pipeline(request_json)
        
        return Response(
            response=response_body,
            status=status_code,
            mimetype="application/json"
        )
        
    except Exception as e:
        logger.error(f"HTTP trigger failed: {str(e)}")
        return Response(
            response='{"status": "error", "message": "Internal server error"}',
            status=500,
            mimetype="application/json"
        )