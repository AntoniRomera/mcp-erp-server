"""Integration tests for the assembled MCP server and its tools.

These exercise the tool layer (input validation, clamping, result envelopes)
against a fake in-process backend so no FastMCP transport is required.
"""

from __future__ import annotations

from datetime import date

import pytest

from mcp_server.config import Settings
from mcp_server.models import Invoice, InvoiceState, Partner, Product
from mcp_server.server import _clamp_limit, _parse_state, create_server


class FakeBackend:
    """Records calls and returns canned data, implementing the Backend protocol."""

    def __init__(self):
        self.calls: list[tuple] = []

    async def list_invoices(self, *, partner_id=None, state=None, limit=50):
        self.calls.append(("list_invoices", partner_id, state, limit))
        return [
            Invoice(
                id=1,
                number="INV/2026/0001",
                partner_id=partner_id or 1,
                partner_name="Acme",
                date=date(2026, 1, 15),
                state=state or InvoiceState.draft,
                amount_total=100.0,
            )
        ]

    async def get_partner(self, partner_id):
        self.calls.append(("get_partner", partner_id))
        if partner_id == 404:
            raise ValueError(f"Partner {partner_id} not found.")
        return Partner(id=partner_id, name="Acme", is_company=True)

    async def search_products(self, *, query=None, category=None, limit=50):
        self.calls.append(("search_products", query, category, limit))
        return [Product(id=101, name="Widget", sku="W-1", list_price=9.99)]

    async def aclose(self):
        return None


def _settings() -> Settings:
    return Settings(demo=True)


async def _call_tool(mcp, name, arguments):
    """Invoke a registered FastMCP tool and return its structured dict result.

    ``FastMCP.call_tool`` is the stable public entry point. Across MCP SDK
    versions it returns either ``(content, structured_result)`` or just the
    content blocks; this helper normalises both to the structured payload.
    """
    result = await mcp.call_tool(name, arguments)
    if isinstance(result, tuple):
        # (content_blocks, structured_result)
        return result[1]
    return result


def test_parse_state_valid_and_case_insensitive():
    assert _parse_state("PAID") is InvoiceState.paid
    assert _parse_state(None) is None


def test_parse_state_invalid_raises():
    with pytest.raises(ValueError, match="Invalid state"):
        _parse_state("cancelled")


@pytest.mark.parametrize(
    ("raw", "expected"),
    [(0, 1), (1, 1), (50, 50), (200, 200), (5000, 200), (-3, 1)],
)
def test_clamp_limit(raw, expected):
    assert _clamp_limit(raw) == expected


async def test_create_server_registers_three_tools():
    mcp = create_server(_settings(), backend=FakeBackend())
    tools = await mcp.list_tools()
    names = {t.name for t in tools}
    assert names == {"list_invoices", "get_partner", "search_products"}


async def test_list_invoices_tool_returns_envelope():
    fake = FakeBackend()
    mcp = create_server(_settings(), backend=fake)
    structured = await _call_tool(
        mcp, "list_invoices", {"partner_id": 1, "state": "paid", "limit": 999}
    )
    assert structured["count"] == 1
    assert structured["invoices"][0]["partner_id"] == 1
    # limit must have been clamped to 200 before reaching the backend.
    assert fake.calls[0] == ("list_invoices", 1, InvoiceState.paid, 200)


async def test_get_partner_tool_returns_partner():
    mcp = create_server(_settings(), backend=FakeBackend())
    structured = await _call_tool(mcp, "get_partner", {"partner_id": 3})
    assert structured["id"] == 3
    assert structured["name"] == "Acme"


async def test_search_products_tool_returns_envelope():
    mcp = create_server(_settings(), backend=FakeBackend())
    structured = await _call_tool(mcp, "search_products", {"query": "widget"})
    assert structured["count"] == 1
    assert structured["products"][0]["sku"] == "W-1"
