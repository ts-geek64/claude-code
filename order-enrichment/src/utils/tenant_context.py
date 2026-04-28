"""Tenant context management for multi-tenant support."""

import logging
from typing import Optional
from contextvars import ContextVar

logger = logging.getLogger(__name__)


# Context variable to store current tenant prefix
_current_tenant: ContextVar[Optional[str]] = ContextVar("current_tenant", default=None)


class TenantContext:
    """Manage tenant-specific context and table name resolution."""

    VALID_TENANTS = ["au_vodka", "milam_and_greene", "omnigrowthos"]

    @staticmethod
    def set_tenant(tenant_id: str) -> None:
        """
        Set the current tenant context.

        Args:
            tenant_id: Full tenant identifier (e.g., 'au_vodka')

        Raises:
            ValueError: If tenant_id is invalid
        """
        if not tenant_id:
            raise ValueError("Tenant ID cannot be empty")

        if tenant_id not in TenantContext.VALID_TENANTS:
            raise ValueError(
                f"Invalid tenant ID: {tenant_id}. Must be one of {TenantContext.VALID_TENANTS}"
            )

        # Map full tenant ID to prefix
        if tenant_id == "au_vodka":
            prefix = "au"
        elif tenant_id == "milam_and_greene":
            prefix = "milam"
        elif tenant_id == "omnigrowthos":
            prefix = "omnigrowthos"
        else:
            prefix = tenant_id.split("_")[0]

        _current_tenant.set(prefix)
        logger.info(f"Tenant context set to: {tenant_id} (prefix: {prefix})")

    @staticmethod
    def get_tenant_prefix() -> str:
        """
        Get the current tenant prefix.

        Returns:
            Tenant prefix (e.g., 'au', 'milam', 'omnigrowthos')

        Raises:
            RuntimeError: If tenant context is not set
        """
        prefix = _current_tenant.get()
        if prefix is None:
            raise RuntimeError(
                "Tenant context not set. Call TenantContext.set_tenant() first."
            )
        return prefix

    @staticmethod
    def clear_tenant() -> None:
        """Clear the current tenant context."""
        _current_tenant.set(None)
        logger.info("Tenant context cleared")

    @staticmethod
    def get_table_name(base_table: str) -> str:
        """
        Get tenant-prefixed table name.

        Args:
            base_table: Base table name without prefix (e.g., 'order_enrichments')

        Returns:
            Prefixed table name (e.g., 'au_order_enrichments')
        """
        prefix = TenantContext.get_tenant_prefix()
        return f"{prefix}_{base_table}"


# Global tenant context instance
tenant_context = TenantContext()