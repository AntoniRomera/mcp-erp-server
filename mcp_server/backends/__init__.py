"""Backend abstraction.

A :class:`Backend` is anything that can answer the three read operations the
MCP tools delegate to. Two implementations ship with the server:

* :class:`~mcp_server.backends.demo.DemoBackend` - bundled sample data, offline.
* :class:`~mcp_server.backends.jsonrpc.JsonRpcBackend` - live JSON-RPC adapter.

:func:`get_backend` picks the implementation from the resolved settings.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

from mcp_server.models import Invoice, InvoiceState, Partner, Product

if TYPE_CHECKING:
    from mcp_server.config import Settings


@runtime_checkable
class Backend(Protocol):
    """Read-only operations every backend must implement."""

    async def list_invoices(
        self,
        *,
        partner_id: int | None = None,
        state: InvoiceState | None = None,
        limit: int = 50,
    ) -> list[Invoice]:
        """Return invoices, optionally filtered by partner and/or state."""
        ...

    async def get_partner(self, partner_id: int) -> Partner:
        """Return a single partner by id, or raise ``ValueError`` if absent."""
        ...

    async def search_products(
        self,
        *,
        query: str | None = None,
        category: str | None = None,
        limit: int = 50,
    ) -> list[Product]:
        """Return products matching a name/SKU query and/or category."""
        ...

    async def aclose(self) -> None:
        """Release any held resources (e.g. an HTTP client)."""
        ...


def get_backend(settings: Settings) -> Backend:
    """Construct the appropriate backend for the given settings."""
    if settings.demo:
        from mcp_server.backends.demo import DemoBackend

        return DemoBackend()

    from mcp_server.backends.jsonrpc import JsonRpcBackend

    return JsonRpcBackend(settings)


__all__ = ["Backend", "get_backend"]
