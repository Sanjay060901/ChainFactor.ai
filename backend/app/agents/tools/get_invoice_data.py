"""get_invoice_data tool: Retrieves invoice data from the database.

Mock implementation: returns deterministic data based on invoice_id.
In production, this would query PostgreSQL via SQLAlchemy.

Mock rules:
    "demo-invoice-001": pre-computed demo invoice (Tata Steel -> Reliance)
    "demo-invoice-002": smaller invoice (Wipro -> Infosys)
    "demo-invoice-003": high-value invoice (Adani -> JSW)
    Others: returns a generic invoice with the given invoice_id

Demo mode: always returns demo-invoice-001 data.

Dependencies:
    - strands (@tool decorator)
    - app.config.settings (DEMO_MODE)
"""

import logging

from strands import tool

from app.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEMO_INVOICES: dict[str, dict] = {
    "demo-invoice-001": {
        "invoice_id": "demo-invoice-001",
        "status": "processing",
        "amount": 501500.00,
        "seller_id": "seller_1_tata",
        "buyer_gstin": "07AABCR5678R1ZN",
        "created_at": "2026-03-01T10:00:00Z",
        "s3_key": "invoices/demo-invoice-001.pdf",
    },
    "demo-invoice-002": {
        "invoice_id": "demo-invoice-002",
        "status": "processing",
        "amount": 150000.00,
        "seller_id": "seller_1_wipro",
        "buyer_gstin": "29AABCW5678R1ZX",
        "created_at": "2026-03-05T14:30:00Z",
        "s3_key": "invoices/demo-invoice-002.pdf",
    },
    "demo-invoice-003": {
        "invoice_id": "demo-invoice-003",
        "status": "processing",
        "amount": 7500000.00,
        "seller_id": "seller_2_adani",
        "buyer_gstin": "27AABCT1234R1ZM",
        "created_at": "2026-03-10T09:15:00Z",
        "s3_key": "invoices/demo-invoice-003.pdf",
    },
}

_DEFAULT_DEMO_ID = "demo-invoice-001"


# ---------------------------------------------------------------------------
# Internal implementation (pure logic, no Strands dependency)
# ---------------------------------------------------------------------------


def _resolve_invoice_data(invoice_id: str, use_demo: bool) -> dict:
    """Core invoice data retrieval logic, separated from the Strands decorator.

    Args:
        invoice_id: Unique identifier for the invoice.
        use_demo: Whether to return the demo (pre-computed) result.

    Returns:
        Dict with invoice_id, status, amount, seller_id, buyer_gstin,
        created_at, s3_key.
    """
    if use_demo:
        logger.info("DEMO_MODE: returning demo invoice data for %s", invoice_id)
        return dict(_DEMO_INVOICES[_DEFAULT_DEMO_ID])

    # Check if the invoice_id matches a known demo invoice
    if invoice_id in _DEMO_INVOICES:
        logger.info("Found known invoice %s in mock data", invoice_id)
        return dict(_DEMO_INVOICES[invoice_id])

    # Return a generic invoice for unknown IDs (mock DB behavior)
    logger.info("Invoice %s not in mock data, returning generic invoice", invoice_id)
    return {
        "invoice_id": invoice_id,
        "status": "processing",
        "amount": 250000.00,
        "seller_id": "seller_unknown",
        "buyer_gstin": "33AABCT9999R1ZZ",
        "created_at": "2026-03-15T12:00:00Z",
        "s3_key": f"invoices/{invoice_id}.pdf",
    }


# ---------------------------------------------------------------------------
# Strands @tool  (registered with the agent; no leading-underscore params)
# ---------------------------------------------------------------------------


@tool
def _get_invoice_data_tool(invoice_id: str) -> dict:
    """Retrieve invoice data from the database by invoice ID.

    Returns the invoice record including status, amount, seller/buyer info,
    and S3 key for the uploaded document.

    Args:
        invoice_id: Unique identifier for the invoice.
    """
    return _resolve_invoice_data(invoice_id, use_demo=settings.DEMO_MODE)


# ---------------------------------------------------------------------------
# Public callable (used by tests and by agent tool list)
# ---------------------------------------------------------------------------


def get_invoice_data(invoice_id: str, _demo: bool = None) -> dict:
    """Retrieve invoice data from the database by invoice ID.

    Wraps _get_invoice_data_tool with a _demo override for testability.

    Args:
        invoice_id: Unique identifier for the invoice.
        _demo: Override for DEMO_MODE. True forces demo, False forces real, None defers.

    Returns:
        Dict with invoice_id, status, amount, seller_id, buyer_gstin,
        created_at, s3_key.
    """
    use_demo = settings.DEMO_MODE if _demo is None else _demo
    return _resolve_invoice_data(invoice_id, use_demo=use_demo)
