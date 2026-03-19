"""Event bridge: maps tool execution results to WebSocket-compatible events.

Provides:
  build_step_event(...)            -- builds a step_complete event dict
  build_pipeline_complete_event(...)-- builds a pipeline_complete event dict
  publish_step_event(...)          -- builds + publishes step event to Redis
  publish_pipeline_complete(...)   -- builds + publishes pipeline complete event

The event schemas are consumed by the frontend pipeline visualization component.
All channel publishing is delegated to
``app.modules.ws.redis_bridge.publish_event``.
"""

from __future__ import annotations

import logging
from typing import Any

from app.modules.ws.redis_bridge import publish_event

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TOTAL_STEPS: int = 14

# Human-readable detail strings for each tool step.
# Keys match the step_name values passed in from the pipeline runner.
_STEP_DETAILS: dict[str, str] = {
    "extract_invoice": "Extracting data from PDF using Textract...",
    "validate_fields": "Validating extracted fields...",
    "validate_gst_compliance": "Checking HSN codes and GST rates...",
    "verify_gstn": "Verifying GSTIN against GST portal...",
    "check_fraud": "Running 5-layer fraud detection...",
    "get_buyer_intel": "Analyzing buyer payment history...",
    "get_credit_score": "Checking CIBIL credit score...",
    "get_company_info": "Fetching MCA company data...",
    "calculate_risk": "Calculating multi-signal risk score...",
    "generate_summary": "Generating invoice summary...",
    "cross_validate_outputs": "Cross-validating all agent outputs...",
    "underwriting_decision": "Making autonomous approval decision...",
    "log_decision": "Logging decision and reasoning trace...",
    "mint_nft": "Minting ARC-69 NFT on Algorand testnet...",
}

_FALLBACK_DETAIL = "Processing step..."


# ---------------------------------------------------------------------------
# Event builders (pure functions -- no I/O)
# ---------------------------------------------------------------------------


def build_step_event(
    *,
    step: int,
    step_name: str,
    agent: str,
    result: dict[str, Any],
    elapsed_ms: int,
    status: str = "complete",
) -> dict[str, Any]:
    """Build a ``step_complete`` event dict matching the WebSocket schema.

    Args:
        step:       Step number (1-14).
        step_name:  Name of the tool that completed (e.g. ``"extract_invoice"``).
        agent:      Agent identifier (``"invoice_processing"`` or ``"underwriting"``).
        result:     Tool result payload to embed verbatim.  Not mutated.
        elapsed_ms: Wall-clock milliseconds the step took.
        status:     Event status string.  Defaults to ``"complete"``.

    Returns:
        A new dict with all required step_complete fields.
    """
    detail = _STEP_DETAILS.get(step_name, _FALLBACK_DETAIL)
    progress = round(step / TOTAL_STEPS, 2)

    return {
        "type": "step_complete",
        "step": step,
        "step_name": step_name,
        "agent": agent,
        "status": status,
        "detail": detail,
        "result": dict(result),  # shallow copy -- never mutate caller's dict
        "progress": progress,
        "elapsed_ms": elapsed_ms,
    }


def build_pipeline_complete_event(
    *,
    invoice_id: str,
    decision: str,
    risk_score: int,
    reason: str,
    nft_asset_id: int | None = None,
) -> dict[str, Any]:
    """Build a ``pipeline_complete`` event dict matching the WebSocket schema.

    Args:
        invoice_id:   Invoice identifier (propagated to the frontend).
        decision:     Underwriting outcome: ``"approved"``, ``"rejected"``, or
                      ``"flagged_for_review"``.
        risk_score:   Final composite risk score (0-100).
        reason:       Human-readable explanation of the decision.
        nft_asset_id: Algorand ASA ID of the minted NFT, or ``None`` when no
                      NFT was minted (e.g. rejected invoices).

    Returns:
        A new dict with all required pipeline_complete fields.
    """
    return {
        "type": "pipeline_complete",
        "decision": decision,
        "risk_score": risk_score,
        "reason": reason,
        "nft_asset_id": nft_asset_id,
        "invoice_id": invoice_id,
    }


# ---------------------------------------------------------------------------
# Publishers (async -- delegate to redis_bridge.publish_event)
# ---------------------------------------------------------------------------


async def publish_step_event(
    *,
    invoice_id: str,
    step: int,
    step_name: str,
    agent: str,
    result: dict[str, Any],
    elapsed_ms: int,
) -> int:
    """Build a step_complete event and publish it to the Redis channel.

    Combines :func:`build_step_event` and
    :func:`~app.modules.ws.redis_bridge.publish_event` so callers do not need
    to manage the event dict themselves.

    Args:
        invoice_id: Invoice identifier (used to derive the Redis channel name).
        step:       Step number (1-14).
        step_name:  Name of the completed tool.
        agent:      Agent identifier string.
        result:     Tool result payload.
        elapsed_ms: Wall-clock time the step took in milliseconds.

    Returns:
        Number of Redis subscribers that received the message.
    """
    event = build_step_event(
        step=step,
        step_name=step_name,
        agent=agent,
        result=result,
        elapsed_ms=elapsed_ms,
    )
    logger.debug(
        "Publishing step_complete event: invoice=%s step=%d/%d tool=%s",
        invoice_id,
        step,
        TOTAL_STEPS,
        step_name,
    )
    return await publish_event(invoice_id, event)


async def publish_pipeline_complete(
    *,
    invoice_id: str,
    decision: str,
    risk_score: int,
    reason: str,
    nft_asset_id: int | None = None,
) -> int:
    """Build a pipeline_complete event and publish it to the Redis channel.

    Combines :func:`build_pipeline_complete_event` and
    :func:`~app.modules.ws.redis_bridge.publish_event`.

    Args:
        invoice_id:   Invoice identifier.
        decision:     Underwriting decision string.
        risk_score:   Final risk score (0-100).
        reason:       Decision explanation.
        nft_asset_id: ASA ID of the minted NFT, or ``None``.

    Returns:
        Number of Redis subscribers that received the message.
    """
    event = build_pipeline_complete_event(
        invoice_id=invoice_id,
        decision=decision,
        risk_score=risk_score,
        reason=reason,
        nft_asset_id=nft_asset_id,
    )
    logger.debug(
        "Publishing pipeline_complete event: invoice=%s decision=%s risk=%d",
        invoice_id,
        decision,
        risk_score,
    )
    return await publish_event(invoice_id, event)
