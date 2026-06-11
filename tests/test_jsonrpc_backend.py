"""Tests for the JSON-RPC backend adapter using a mocked HTTP transport."""

from __future__ import annotations

import httpx
import pytest
import respx

from mcp_server.backends.jsonrpc import BackendError, JsonRpcBackend
from mcp_server.config import Settings
from mcp_server.models import InvoiceState

BASE_URL = "http://erp.test"


def _settings(**overrides) -> Settings:
    base = {
        "backend_url": BASE_URL,
        "readonly": True,
        "demo": False,
    }
    base.update(overrides)
    return Settings(**base)


def _ok(result):
    return httpx.Response(200, json={"jsonrpc": "2.0", "id": 1, "result": result})


@respx.mock
async def test_list_invoices_parses_list_result():
    route = respx.post(BASE_URL).mock(
        return_value=_ok(
            [
                {
                    "id": 1,
                    "number": "INV/2026/0001",
                    "partner_id": 1,
                    "partner_name": "Acme",
                    "date": "2026-01-15",
                    "state": "paid",
                    "amount_total": 100.0,
                }
            ]
        )
    )
    backend = JsonRpcBackend(_settings())
    invoices = await backend.list_invoices(partner_id=1, state=InvoiceState.paid, limit=10)

    assert len(invoices) == 1
    assert invoices[0].state is InvoiceState.paid

    sent = route.calls.last.request
    body = httpx.Response(200, content=sent.content).json()
    assert body["method"] == "invoices.list"
    assert body["params"]["partner_id"] == 1
    assert body["params"]["state"] == "paid"
    assert body["params"]["limit"] == 10
    await backend.aclose()


@respx.mock
async def test_list_invoices_parses_wrapped_result():
    respx.post(BASE_URL).mock(
        return_value=_ok(
            {
                "invoices": [
                    {
                        "id": 2,
                        "number": "INV/2026/0002",
                        "partner_id": 2,
                        "partner_name": "Globex",
                        "date": "2026-02-03",
                        "amount_total": 50.0,
                    }
                ]
            }
        )
    )
    backend = JsonRpcBackend(_settings())
    invoices = await backend.list_invoices()
    assert len(invoices) == 1
    assert invoices[0].id == 2
    await backend.aclose()


@respx.mock
async def test_get_partner_found():
    respx.post(BASE_URL).mock(
        return_value=_ok({"id": 7, "name": "Initech", "is_company": True})
    )
    backend = JsonRpcBackend(_settings())
    partner = await backend.get_partner(7)
    assert partner.name == "Initech"
    await backend.aclose()


@respx.mock
async def test_get_partner_empty_result_raises():
    respx.post(BASE_URL).mock(return_value=_ok(None))
    backend = JsonRpcBackend(_settings())
    with pytest.raises(ValueError, match="not found"):
        await backend.get_partner(404)
    await backend.aclose()


@respx.mock
async def test_jsonrpc_error_body_raises_backend_error():
    respx.post(BASE_URL).mock(
        return_value=httpx.Response(
            200,
            json={"jsonrpc": "2.0", "id": 1, "error": {"code": -32000, "message": "boom"}},
        )
    )
    backend = JsonRpcBackend(_settings())
    with pytest.raises(BackendError, match="boom"):
        await backend.search_products(query="x")
    await backend.aclose()


@respx.mock
async def test_http_error_raises_backend_error():
    respx.post(BASE_URL).mock(return_value=httpx.Response(500))
    backend = JsonRpcBackend(_settings())
    with pytest.raises(BackendError, match="request failed"):
        await backend.search_products()
    await backend.aclose()


async def test_readonly_blocks_non_allowlisted_method_before_network():
    # No respx mock: if a request were made it would error differently.
    # enforce_readonly must reject the call first.
    backend = JsonRpcBackend(_settings(readonly=True))
    with pytest.raises(PermissionError):
        await backend.call("invoices.create", {})
    await backend.aclose()


@respx.mock
async def test_api_key_sets_authorization_header_and_param():
    route = respx.post(BASE_URL).mock(return_value=_ok([]))
    backend = JsonRpcBackend(_settings(backend_api_key="secret-token"))
    await backend.list_invoices()

    req = route.calls.last.request
    assert req.headers["Authorization"] == "Bearer secret-token"
    body = httpx.Response(200, content=req.content).json()
    assert body["params"]["api_key"] == "secret-token"
    await backend.aclose()
