"""JSON-RPC backend adapter.

Implements the three read operations against any JSON-RPC 2.0 endpoint using
httpx. Every call is gated by :func:`mcp_server.security.enforce_readonly`, so
a misconfigured tool cannot reach a mutating method while ``READONLY`` is true.
"""

from __future__ import annotations

import itertools
from typing import Any

import httpx

from mcp_server.config import Settings
from mcp_server.models import Invoice, InvoiceState, Partner, Product
from mcp_server.security import enforce_readonly


class BackendError(RuntimeError):
    """Raised when the backend returns a JSON-RPC error or is unreachable."""


class JsonRpcBackend:
    """Async JSON-RPC 2.0 client implementing the read operations."""

    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None) -> None:
        self._settings = settings
        self._ids = itertools.count(1)
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if settings.backend_api_key:
            headers["Authorization"] = f"Bearer {settings.backend_api_key}"
        self._client = client or httpx.AsyncClient(
            base_url=settings.backend_url,
            timeout=settings.request_timeout,
            headers=headers,
        )

    # --- transport ---------------------------------------------------------

    def _auth_params(self) -> dict[str, Any]:
        """Auth fields forwarded as JSON-RPC params (generic, no vendor scheme)."""
        params: dict[str, Any] = {}
        s = self._settings
        if s.backend_api_key:
            params["api_key"] = s.backend_api_key
        if s.backend_username:
            params["username"] = s.backend_username
        if s.backend_password:
            params["password"] = s.backend_password
        if s.backend_database:
            params["database"] = s.backend_database
        return params

    async def call(self, method: str, params: dict[str, Any]) -> Any:
        """Execute one allowlist-checked JSON-RPC call and return its result."""
        enforce_readonly(method, readonly=self._settings.readonly)

        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": {**self._auth_params(), **params},
            "id": next(self._ids),
        }
        try:
            response = await self._client.post("", json=payload)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise BackendError(f"Backend request failed for {method!r}: {exc}") from exc

        body = response.json()
        if isinstance(body, dict) and body.get("error"):
            err = body["error"]
            message = err.get("message", err) if isinstance(err, dict) else err
            raise BackendError(f"Backend returned an error for {method!r}: {message}")
        return body.get("result") if isinstance(body, dict) else body

    # --- operations --------------------------------------------------------

    async def list_invoices(
        self,
        *,
        partner_id: int | None = None,
        state: InvoiceState | None = None,
        limit: int = 50,
    ) -> list[Invoice]:
        params: dict[str, Any] = {"limit": limit}
        if partner_id is not None:
            params["partner_id"] = partner_id
        if state is not None:
            params["state"] = state.value
        result = await self.call("invoices.list", params)
        rows = result if isinstance(result, list) else result.get("invoices", [])
        return [Invoice(**row) for row in rows]

    async def get_partner(self, partner_id: int) -> Partner:
        result = await self.call("partners.get", {"id": partner_id})
        if not result:
            raise ValueError(f"Partner {partner_id} not found.")
        return Partner(**result)

    async def search_products(
        self,
        *,
        query: str | None = None,
        category: str | None = None,
        limit: int = 50,
    ) -> list[Product]:
        params: dict[str, Any] = {"limit": limit}
        if query:
            params["query"] = query
        if category:
            params["category"] = category
        result = await self.call("products.search", params)
        rows = result if isinstance(result, list) else result.get("products", [])
        return [Product(**row) for row in rows]

    async def aclose(self) -> None:
        await self._client.aclose()
