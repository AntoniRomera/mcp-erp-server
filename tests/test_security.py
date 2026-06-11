"""Tests for the read-only allowlist enforcement."""

from __future__ import annotations

import pytest

from mcp_server.security import (
    ALLOWED_METHODS,
    READ_ONLY_TOOLS,
    enforce_readonly,
)


@pytest.mark.parametrize("method", sorted(ALLOWED_METHODS))
def test_allowlisted_methods_pass_when_readonly(method):
    # Should not raise.
    enforce_readonly(method, readonly=True)


@pytest.mark.parametrize(
    "method",
    ["invoices.create", "partners.write", "products.unlink", "anything.else"],
)
def test_non_allowlisted_method_rejected_when_readonly(method):
    with pytest.raises(PermissionError):
        enforce_readonly(method, readonly=True)


@pytest.mark.parametrize(
    "method",
    ["invoices.create", "partners.write", "products.unlink"],
)
def test_write_methods_allowed_when_readonly_disabled(method):
    # When readonly is False the allowlist is bypassed entirely.
    enforce_readonly(method, readonly=False)


def test_read_only_tools_set_is_stable():
    assert READ_ONLY_TOOLS == frozenset(
        {"list_invoices", "get_partner", "search_products"}
    )
