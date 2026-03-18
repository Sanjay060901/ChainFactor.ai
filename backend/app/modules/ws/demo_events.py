"""Pre-computed demo events for DEMO_MODE WebSocket streaming.

These events are returned verbatim when settings.DEMO_MODE is True, so the
frontend pipeline visualization works without Redis or Bedrock.

14 step_complete events (steps 1-14) + 1 pipeline_complete event = 15 total.

Steps 1-10 belong to the Invoice Processing Agent.
Steps 11-14 belong to the Underwriting Agent.
"""

from __future__ import annotations

_STEPS = [
    (
        1,
        "extract_invoice",
        "invoice_processing",
        "Extracting data from PDF using Textract...",
    ),
    (2, "validate_fields", "invoice_processing", "Validating 23 extracted fields..."),
    (
        3,
        "validate_gst_compliance",
        "invoice_processing",
        "Checking HSN codes and GST rates...",
    ),
    (4, "verify_gstn", "invoice_processing", "Verifying GSTIN 27AABCU9603R1ZM..."),
    (5, "check_fraud", "invoice_processing", "Running 5-layer fraud detection..."),
    (6, "get_buyer_intel", "invoice_processing", "Analyzing buyer payment history..."),
    (7, "get_credit_score", "invoice_processing", "Checking CIBIL credit score..."),
    (8, "get_company_info", "invoice_processing", "Fetching MCA company data..."),
    (
        9,
        "calculate_risk",
        "invoice_processing",
        "Calculating multi-signal risk score...",
    ),
    (
        10,
        "generate_summary",
        "invoice_processing",
        "Generating invoice summary for handoff...",
    ),
    (
        11,
        "cross_validate_outputs",
        "underwriting",
        "Cross-validating all agent outputs...",
    ),
    (
        12,
        "underwriting_decision",
        "underwriting",
        "Making autonomous approval decision...",
    ),
    (13, "log_decision", "underwriting", "Logging decision and reasoning trace..."),
    (14, "mint_nft", "underwriting", "Minting ARC-69 NFT on Algorand testnet..."),
]

# Total steps used for progress calculation
_TOTAL_STEPS = len(_STEPS)


def build_demo_events(invoice_id: str) -> list[dict]:
    """Return the list of demo events for a given invoice_id.

    All 14 step_complete events are generated first, followed by the
    pipeline_complete event.  Progress values increase monotonically from
    ~0.07 (step 1/14) to 1.00 (step 14/14).

    Args:
        invoice_id: Used in the pipeline_complete event's invoice_id field.

    Returns:
        List of 15 event dicts (14 step_complete + 1 pipeline_complete).
    """
    events: list[dict] = []

    for step_num, step_name, agent, detail in _STEPS:
        progress = round(step_num / _TOTAL_STEPS, 2)
        events.append(
            {
                "type": "step_complete",
                "step": step_num,
                "step_name": step_name,
                "agent": agent,
                "status": "complete",
                "detail": detail,
                "result": {},
                "progress": progress,
                "elapsed_ms": step_num * 7000,
            }
        )

    events.append(
        {
            "type": "pipeline_complete",
            "decision": "approved",
            "risk_score": 82,
            "reason": "Auto-approved: meets Rule 2 criteria",
            "nft_asset_id": 12345678,
            "invoice_id": invoice_id,
        }
    )

    return events
