"""Main entry point for Shopify synchronization pipeline."""

import json
import logging
import sys
from typing import Dict

import functions_framework
from flask import Request, Response

from config.settings import settings
from src.database.database_context import db_context
from src.services.sync_orchestrator import SyncOrchestrator
from src.utils.tenant_context import tenant_context

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
    force=True,
)

# Explicitly set level for the root logger to ensure all logs propagate correctly
logging.getLogger().setLevel(getattr(logging, settings.LOG_LEVEL))

logger = logging.getLogger(__name__)


@functions_framework.http
def sync_shopify(request: Request) -> Response:
    """
    HTTP entry point for Shopify synchronization.

    Args:
        request: Flask Request object

    Returns:
        JSON response with sync results
    """
    logger.info("Starting Shopify sync pipeline")

    try:
        # Parse request body
        request_json = request.get_json(silent=True) or {}

        # Extract tenant ID from request body
        tenant_id = request_json.get("tenant_id")
        if not tenant_id:
            return Response(
                json.dumps(
                    {
                        "status": "error",
                        "code": "ERR_MISSING_TENANT",
                        "message": "tenant_id is required in request body",
                    }
                ),
                status=400,
                mimetype="application/json",
            )

        # Set tenant context
        tenant_context.set_tenant(tenant_id)
        logger.info(f"Processing request for tenant: {tenant_id}")

        # Validate settings
        settings.validate()

        # Initialize database connection pool
        db_context.initialize()

        # Extract integration_ids and full sync flag
        integration_ids = request_json.get("integration_ids")
        sync_from_start = request_json.get("sync_from_start", False)

        if integration_ids:
            logger.info(f"Received request to sync integrations: {integration_ids}")

        if sync_from_start:
            logger.info("Full sync requested: syncing from the start")

        # Execute sync with database connection
        with db_context.get_connection() as conn:
            orchestrator = SyncOrchestrator(conn)
            results = orchestrator.sync_all_integrations(
                integration_ids, sync_from_start=sync_from_start
            )

        logger.info("Sync pipeline completed")
        return Response(
            json.dumps(results, default=str),
            status=200,
            mimetype="application/json",
        )

    except ValueError as e:
        logger.error(f"Invalid tenant: {str(e)}")
        return Response(
            json.dumps(
                {
                    "status": "error",
                    "code": "ERR_INVALID_TENANT",
                    "message": str(e),
                }
            ),
            status=400,
            mimetype="application/json",
        )

    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        return Response(
            json.dumps(
                {
                    "status": "error",
                    "code": "ERR_PIPELINE_FAILED",
                    "message": "Sync pipeline failed",
                    "details": {"error": str(e)},
                }
            ),
            status=500,
            mimetype="application/json",
        )

    finally:
        # Clear tenant context
        tenant_context.clear_tenant()
        # Close database connection pool
        db_context.close()
