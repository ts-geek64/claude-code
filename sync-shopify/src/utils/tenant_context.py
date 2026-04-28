"""Tenant context management for multi-tenant support."""

import logging
from typing import FrozenSet, Optional
from contextvars import ContextVar

logger = logging.getLogger(__name__)


# Context variable to store current tenant prefix
_current_tenant: ContextVar[Optional[str]] = ContextVar("current_tenant", default=None)

# ---------------------------------------------------------------------------
# Per-tenant Shopify update policy
# ---------------------------------------------------------------------------
# Defines which history record types Shopify is allowed to create for each
# tenant prefix. An empty frozenset means Shopify may update nothing; all
# changes for that tenant must come through the Admin Panel.
#
#   'price' → Shopify may create new price history records
#   'cost'  → Shopify may create new cost history records
#
# Milam and Greene enforces strict admin-panel-only control, so both are
# blocked from Shopify for that tenant.
_SHOPIFY_ALLOWED_UPDATES: dict[str, FrozenSet[str]] = {
    "au": frozenset({"price", "cost"}),
    "milam": frozenset(),  # Shopify blocked for price AND cost
    "omnigrowthos": frozenset({"price", "cost"}),
}


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
            base_table: Base table name without prefix (e.g., 'integrations')

        Returns:
            Prefixed table name (e.g., 'au_integrations')
        """
        prefix = TenantContext.get_tenant_prefix()
        return f"{prefix}_{base_table}"

    @staticmethod
    def shopify_can_update(update_type: str) -> bool:
        """
        Return True if the current tenant permits Shopify to create a
        historical record for the given update type.

        Args:
            update_type: Either 'price' or 'cost'.

        Returns:
            True  → Shopify is allowed to write a history record.
            False → Update must be rejected and optionally logged for audit.

        Raises:
            RuntimeError: If tenant context has not been set.
        """
        prefix = TenantContext.get_tenant_prefix()
        allowed: FrozenSet[str] = _SHOPIFY_ALLOWED_UPDATES.get(prefix, frozenset())
        return update_type in allowed


# Global tenant context instance
tenant_context = TenantContext()
