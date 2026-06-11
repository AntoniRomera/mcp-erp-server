"""Server assembly.

:func:`create_server` instantiates a :class:`FastMCP` server, selects a backend
from the resolved settings, and registers the three read-only tools. Tool
bodies are intentionally backend-agnostic: they just validate inputs and
delegate to the chosen :class:`~mcp_server.backends.Backend`.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from mcp_server.backends import Backend, get_backend
from mcp_server.config import Settings, build_settings
from mcp_server.models import (
    InvoiceListResult,
    InvoiceState,
    Partner,
    ProductSearchResult,
)


def create_server(
    settings: Settings | None = None,
    *,
    backend: Backend | None = None,
) -> FastMCP:
    """Build a configured FastMCP server.

    ``settings`` defaults to env/.env-resolved settings. ``backend`` lets tests
    inject a fake; otherwise it is chosen by :func:`get_backend`.
    """
    settings = settings or build_settings()
    backend = backend or get_backend(settings)

    mode = "demo" if settings.demo else f"live ({settings.backend_url})"
    mcp = FastMCP(
        name="mcp-erp-server",
        instructions=(
            "Read-only access to ERP-style data (invoices, partners, products). "
            f"Currently serving: {mode}."
        ),
    )

    @mcp.tool()
    async def list_invoices(
        partner_id: int | None = None,
        state: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        """List invoices, optionally filtered by partner id and/or state.

        Args:
            partner_id: Restrict to invoices for this partner.
            state: One of ``draft``, ``posted`` or ``paid``.
            limit: Maximum number of invoices to return (1-200).
        """
        parsed_state = _parse_state(state)
        limit = _clamp_limit(limit)
        invoices = await backend.list_invoices(
            partner_id=partner_id, state=parsed_state, limit=limit
        )
        return InvoiceListResult(count=len(invoices), invoices=invoices).model_dump(mode="json")

    @mcp.tool()
    async def get_partner(partner_id: int) -> dict[str, Any]:
        """Fetch a single partner (customer or vendor) by id.

        Args:
            partner_id: The numeric partner identifier.
        """
        try:
            partner = await backend.get_partner(partner_id)
        except ValueError as exc:
            # Surface a clean message to the agent rather than a traceback.
            raise ValueError(str(exc)) from exc
        return Partner.model_validate(partner).model_dump(mode="json")

    @mcp.tool()
    async def search_products(
        query: str | None = None,
        category: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        """Search products by name/SKU and/or category.

        Args:
            query: Case-insensitive substring matched against name and SKU.
            category: Exact (case-insensitive) category filter.
            limit: Maximum number of products to return (1-200).
        """
        limit = _clamp_limit(limit)
        products = await backend.search_products(query=query, category=category, limit=limit)
        return ProductSearchResult(count=len(products), products=products).model_dump(mode="json")

    return mcp


def _parse_state(state: str | None) -> InvoiceState | None:
    """Validate the optional invoice-state filter."""
    if state is None:
        return None
    try:
        return InvoiceState(state.lower())
    except ValueError as exc:
        valid = ", ".join(s.value for s in InvoiceState)
        raise ValueError(f"Invalid state {state!r}. Expected one of: {valid}.") from exc


def _clamp_limit(limit: int) -> int:
    """Keep limit within a sane 1-200 range."""
    return max(1, min(int(limit), 200))
