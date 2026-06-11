"""Tests for the typed domain models."""

from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from mcp_server.models import (
    Invoice,
    InvoiceLine,
    InvoiceState,
    Partner,
    Product,
)


def test_invoice_line_subtotal_rounds_to_two_places():
    line = InvoiceLine(
        product_id=101,
        description="Standard Widget",
        quantity=3,
        unit_price=19.99,
    )
    assert line.subtotal == 59.97


def test_invoice_defaults_state_and_currency():
    inv = Invoice(
        id=1,
        number="INV/2026/0001",
        partner_id=1,
        partner_name="Acme",
        date=date(2026, 1, 15),
        amount_total=100.0,
    )
    assert inv.state is InvoiceState.draft
    assert inv.currency == "USD"
    assert inv.lines == []
    assert inv.due_date is None


def test_invoice_state_enum_accepts_string():
    inv = Invoice(
        id=1,
        number="INV/1",
        partner_id=1,
        partner_name="Acme",
        date=date(2026, 1, 15),
        state="paid",
        amount_total=10.0,
    )
    assert inv.state is InvoiceState.paid


def test_invoice_rejects_unknown_state():
    with pytest.raises(ValidationError):
        Invoice(
            id=1,
            number="INV/1",
            partner_id=1,
            partner_name="Acme",
            date=date(2026, 1, 15),
            state="cancelled",
            amount_total=10.0,
        )


def test_partner_optional_fields_default_to_none():
    p = Partner(id=1, name="Acme")
    assert p.email is None
    assert p.phone is None
    assert p.is_company is False
    assert p.country is None


def test_product_requires_sku_and_price():
    with pytest.raises(ValidationError):
        Product(id=1, name="Widget")  # missing sku + list_price


def test_product_qty_available_defaults_to_zero():
    p = Product(id=1, name="Widget", sku="W-1", list_price=9.99)
    assert p.qty_available == 0.0
