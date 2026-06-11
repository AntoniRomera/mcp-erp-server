"""Tests for the in-memory demo backend over the bundled dataset."""

from __future__ import annotations

import pytest

from mcp_server.backends.demo import DemoBackend
from mcp_server.models import InvoiceState


@pytest.fixture
def backend() -> DemoBackend:
    return DemoBackend()


async def test_loads_bundled_dataset(backend: DemoBackend):
    invoices = await backend.list_invoices()
    # The bundled dataset has six invoices.
    assert len(invoices) == 6
    assert all(inv.number.startswith("INV/2026/") for inv in invoices)


async def test_list_invoices_filter_by_partner(backend: DemoBackend):
    invoices = await backend.list_invoices(partner_id=1)
    assert len(invoices) == 2
    assert {inv.partner_id for inv in invoices} == {1}


async def test_list_invoices_filter_by_state(backend: DemoBackend):
    paid = await backend.list_invoices(state=InvoiceState.paid)
    assert len(paid) == 2
    assert all(inv.state is InvoiceState.paid for inv in paid)


async def test_list_invoices_combined_filters(backend: DemoBackend):
    res = await backend.list_invoices(partner_id=1, state=InvoiceState.paid)
    assert len(res) == 2
    assert all(inv.partner_id == 1 and inv.state is InvoiceState.paid for inv in res)


async def test_list_invoices_limit(backend: DemoBackend):
    assert len(await backend.list_invoices(limit=2)) == 2
    assert len(await backend.list_invoices(limit=0)) == 0


async def test_get_partner_found(backend: DemoBackend):
    partner = await backend.get_partner(4)
    assert partner.name == "Maria Sol Garcia"
    assert partner.is_company is False
    assert partner.country == "ES"


async def test_get_partner_missing_raises(backend: DemoBackend):
    with pytest.raises(ValueError, match="not found"):
        await backend.get_partner(99999)


async def test_search_products_by_name_case_insensitive(backend: DemoBackend):
    results = await backend.search_products(query="WIDGET")
    assert len(results) == 2
    assert all("widget" in p.name.lower() for p in results)


async def test_search_products_by_sku(backend: DemoBackend):
    results = await backend.search_products(query="gad-pro")
    assert len(results) == 1
    assert results[0].sku == "GAD-PRO-011"


async def test_search_products_by_category(backend: DemoBackend):
    results = await backend.search_products(category="services")
    assert len(results) == 2
    assert all(p.category == "Services" for p in results)


async def test_search_products_no_match_returns_empty(backend: DemoBackend):
    assert await backend.search_products(query="nonexistent-thing") == []


async def test_aclose_is_noop(backend: DemoBackend):
    assert await backend.aclose() is None
