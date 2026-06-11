"""Typed domain models and tool I/O schemas.

These are clean-room, generic ERP entities — not derived from any employer
schema. Demo JSON files mirror these fields exactly, so demo mode and live
mode return identical shapes.
"""

from __future__ import annotations

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, Field


class InvoiceState(StrEnum):
    """Lifecycle state of an invoice."""

    draft = "draft"
    posted = "posted"
    paid = "paid"


class Partner(BaseModel):
    """A customer or vendor."""

    id: int
    name: str
    email: str | None = None
    phone: str | None = None
    is_company: bool = False
    country: str | None = None


class Product(BaseModel):
    """A sellable / purchasable product."""

    id: int
    name: str
    sku: str
    list_price: float
    qty_available: float = 0.0
    category: str | None = None


class InvoiceLine(BaseModel):
    """A single line item on an invoice."""

    product_id: int
    description: str
    quantity: float
    unit_price: float

    @property
    def subtotal(self) -> float:
        return round(self.quantity * self.unit_price, 2)


class Invoice(BaseModel):
    """A customer invoice."""

    id: int
    number: str
    partner_id: int
    partner_name: str
    date: date
    due_date: date | None = None
    state: InvoiceState = InvoiceState.draft
    amount_total: float
    currency: str = "USD"
    lines: list[InvoiceLine] = Field(default_factory=list)


# --- Tool result envelopes -------------------------------------------------


class InvoiceListResult(BaseModel):
    """Result of ``list_invoices``."""

    count: int
    invoices: list[Invoice]


class ProductSearchResult(BaseModel):
    """Result of ``search_products``."""

    count: int
    products: list[Product]
