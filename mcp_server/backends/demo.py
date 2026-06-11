"""Demo backend.

Loads the bundled ``data/demo_*.json`` files once and serves / filters them
in memory. It never opens a socket, so ``python -m mcp_server --demo`` runs
fully offline.
"""

from __future__ import annotations

import json
from importlib import resources
from typing import Any

from mcp_server.models import Invoice, InvoiceState, Partner, Product


def _load(filename: str) -> list[dict[str, Any]]:
    """Read a bundled JSON dataset from the ``mcp_server.data`` package."""
    data_pkg = resources.files("mcp_server.data")
    with (data_pkg / filename).open("r", encoding="utf-8") as fh:
        return json.load(fh)


class DemoBackend:
    """In-memory backend over the bundled sample dataset."""

    def __init__(self) -> None:
        self._invoices: list[Invoice] = [Invoice(**row) for row in _load("demo_invoices.json")]
        self._partners: dict[int, Partner] = {
            p.id: p for p in (Partner(**row) for row in _load("demo_partners.json"))
        }
        self._products: list[Product] = [Product(**row) for row in _load("demo_products.json")]

    async def list_invoices(
        self,
        *,
        partner_id: int | None = None,
        state: InvoiceState | None = None,
        limit: int = 50,
    ) -> list[Invoice]:
        results = self._invoices
        if partner_id is not None:
            results = [inv for inv in results if inv.partner_id == partner_id]
        if state is not None:
            results = [inv for inv in results if inv.state == state]
        return results[: max(0, limit)]

    async def get_partner(self, partner_id: int) -> Partner:
        partner = self._partners.get(partner_id)
        if partner is None:
            raise ValueError(f"Partner {partner_id} not found.")
        return partner

    async def search_products(
        self,
        *,
        query: str | None = None,
        category: str | None = None,
        limit: int = 50,
    ) -> list[Product]:
        results = self._products
        if query:
            needle = query.casefold()
            results = [
                p
                for p in results
                if needle in p.name.casefold() or needle in p.sku.casefold()
            ]
        if category:
            cat = category.casefold()
            results = [p for p in results if (p.category or "").casefold() == cat]
        return results[: max(0, limit)]

    async def aclose(self) -> None:
        # Nothing to release; present to satisfy the Backend protocol.
        return None
