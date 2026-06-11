"""Allowlist and read-only enforcement.

Two layers of protection:

1. ``READ_ONLY_TOOLS`` names the MCP tools that are safe to expose with no
   mutation risk. The server only registers these in the default configuration.
2. ``ALLOWED_METHODS`` maps each tool to the *single* JSON-RPC method it is
   permitted to invoke. :func:`enforce_readonly` is called by the backend
   adapter before every RPC, so even a misconfigured tool cannot trigger a
   mutating call while ``READONLY`` is true.
"""

from __future__ import annotations

# MCP tools considered read-only and safe to expose by default.
READ_ONLY_TOOLS: frozenset[str] = frozenset(
    {"list_invoices", "get_partner", "search_products"}
)

# The exact JSON-RPC methods each read-only tool is allowed to call.
# Anything outside this set is rejected while READONLY is true.
ALLOWED_METHODS: frozenset[str] = frozenset(
    {
        "invoices.list",
        "partners.get",
        "products.search",
    }
)


def enforce_readonly(method: str, *, readonly: bool) -> None:
    """Raise :class:`PermissionError` if ``method`` is not allowlisted.

    When ``readonly`` is False the check is skipped (write mode is an explicit,
    opt-in escape hatch reserved for future write tools).
    """
    if not readonly:
        return
    if method not in ALLOWED_METHODS:
        raise PermissionError(
            f"Method {method!r} is not in the read-only allowlist; "
            "refusing to call it while READONLY is enabled."
        )
