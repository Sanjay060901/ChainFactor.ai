"""Pipeline Runner -- orchestrates the full 14-step invoice processing pipeline.

Phase 1 implementation: calls each tool's public function directly (no Strands
Agent/Swarm wiring yet). Results are persisted to the DB and WebSocket events
are published after each step.

Pipeline Steps:
    1.  extract_invoice          invoice_processing
    2.  validate_fields          invoice_processing
    3.  validate_gst_compliance  invoice_processing
    4.  verify_gstn              invoice_processing
    5.  check_fraud              invoice_processing
    6.  get_buyer_intel          invoice_processing
    7.  get_credit_score         invoice_processing
    8.  get_company_info         invoice_processing
    9.  calculate_risk           invoice_processing
    10. generate_summary         invoice_processing
    11. cross_validate_outputs   underwriting
    12. underwriting_decision    underwriting  (dispatches approve/reject/flag)
    13. log_decision             underwriting
    14. mint_nft                 invoice_processing  (only when approved)

Entry point: run_invoice_pipeline(invoice=..., db=...)
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.agents.config import SONNET_MODEL_ID
from app.modules.agents.event_bridge import (
    publish_pipeline_complete,
    publish_step_event,
)
from app.modules.agents.persistence import persist_tool_result, save_agent_trace

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pipeline step registry
# ---------------------------------------------------------------------------

PIPELINE_STEPS: list[dict] = [
    {"step": 1, "step_name": "extract_invoice", "agent": "invoice_processing"},
    {"step": 2, "step_name": "validate_fields", "agent": "invoice_processing"},
    {"step": 3, "step_name": "validate_gst_compliance", "agent": "invoice_processing"},
    {"step": 4, "step_name": "verify_gstn", "agent": "invoice_processing"},
    {"step": 5, "step_name": "check_fraud", "agent": "invoice_processing"},
    {"step": 6, "step_name": "get_buyer_intel", "agent": "invoice_processing"},
    {"step": 7, "step_name": "get_credit_score", "agent": "invoice_processing"},
    {"step": 8, "step_name": "get_company_info", "agent": "invoice_processing"},
    {"step": 9, "step_name": "calculate_risk", "agent": "invoice_processing"},
    {"step": 10, "step_name": "generate_summary", "agent": "invoice_processing"},
    {"step": 11, "step_name": "cross_validate_outputs", "agent": "underwriting"},
    {"step": 12, "step_name": "underwriting_decision", "agent": "underwriting"},
    {"step": 13, "step_name": "log_decision", "agent": "underwriting"},
    {"step": 14, "step_name": "mint_nft", "agent": "invoice_processing"},
]

# Context key for each step result -- downstream tools read from these keys
_STEP_CONTEXT_KEY: dict[str, str] = {
    "extract_invoice": "extracted_data",
    "validate_fields": "validation_result",
    "validate_gst_compliance": "gst_compliance",
    "verify_gstn": "gstin_verification",
    "check_fraud": "fraud_result",
    "get_buyer_intel": "buyer_intel",
    "get_credit_score": "credit_score",
    "get_company_info": "company_info",
    "calculate_risk": "risk_assessment",
    "generate_summary": "summary_result",
    "cross_validate_outputs": "cross_validation",
    "mint_nft": "mint_nft_result",
}


# ---------------------------------------------------------------------------
# _accumulate_context
# ---------------------------------------------------------------------------


def _accumulate_context(ctx: dict[str, Any], step_name: str, result: dict) -> None:
    """Map a completed step's result into the shared context dict.

    Mutates *ctx* in place.  Unknown step names are silently ignored.

    Args:
        ctx:       Shared pipeline context dict (mutated in place).
        step_name: Name of the just-completed step.
        result:    Dict returned by the tool.
    """
    key = _STEP_CONTEXT_KEY.get(step_name)
    if key is not None:
        ctx[key] = result


# ---------------------------------------------------------------------------
# _execute_step
# ---------------------------------------------------------------------------


async def _execute_step(step_name: str, **context: Any) -> dict:
    """Dispatch to the correct tool function for the given step name.

    All tool imports are local (inside the function) to:
    - Avoid circular imports at module load time
    - Keep the function easily mockable in unit tests

    Args:
        step_name: Name of the pipeline step to execute.
        **context: Accumulated pipeline context.  Each tool only reads the
                   keys it needs.

    Returns:
        A dict with the tool's result.

    Raises:
        ValueError: If step_name is not a recognized tool.
    """
    invoice_id: str = context.get("invoice_id", "")
    file_key: str = context.get("file_key", "")

    # ------------------------------------------------------------------
    # Steps 1-10: Invoice Processing Agent tools
    # ------------------------------------------------------------------
    if step_name == "extract_invoice":
        from app.agents.tools.extract_invoice import extract_invoice

        bucket = context.get("bucket_name", "")
        return extract_invoice(s3_file_key=file_key, bucket_name=bucket)

    if step_name == "validate_fields":
        from app.agents.tools.validate_fields import validate_fields

        extracted = context.get("extracted_data", {})
        return validate_fields(extracted_data=extracted)

    if step_name == "validate_gst_compliance":
        from app.agents.tools.validate_gst_compliance import validate_gst_compliance

        extracted = context.get("extracted_data", {})
        return validate_gst_compliance(extracted_data=extracted)

    if step_name == "verify_gstn":
        from app.agents.tools.verify_gstn import verify_gstn

        extracted = context.get("extracted_data", {})
        seller_gstin = (extracted.get("seller") or {}).get("gstin", "")
        buyer_gstin = (extracted.get("buyer") or {}).get("gstin", "")
        return verify_gstn(seller_gstin=seller_gstin, buyer_gstin=buyer_gstin)

    if step_name == "check_fraud":
        from app.agents.tools.check_fraud import check_fraud

        extracted = context.get("extracted_data", {})
        gstin_ver = context.get("gstin_verification", {})
        return check_fraud(extracted_data=extracted, gstin_verification=gstin_ver)

    if step_name == "get_buyer_intel":
        from app.agents.tools.get_buyer_intel import get_buyer_intel

        extracted = context.get("extracted_data", {})
        buyer_gstin = (extracted.get("buyer") or {}).get("gstin", "")
        return get_buyer_intel(buyer_gstin=buyer_gstin)

    if step_name == "get_credit_score":
        from app.agents.tools.get_credit_score import get_credit_score

        extracted = context.get("extracted_data", {})
        buyer_gstin = (extracted.get("buyer") or {}).get("gstin", "")
        return get_credit_score(buyer_gstin=buyer_gstin)

    if step_name == "get_company_info":
        from app.agents.tools.get_company_info import get_company_info

        extracted = context.get("extracted_data", {})
        company_gstin = (extracted.get("buyer") or {}).get("gstin", "")
        return get_company_info(company_gstin=company_gstin)

    if step_name == "calculate_risk":
        from app.agents.tools.calculate_risk import calculate_risk

        return calculate_risk(
            extracted_data=context.get("extracted_data", {}),
            validation_result=context.get("validation_result", {}),
            fraud_result=context.get("fraud_result", {}),
            gst_compliance=context.get("gst_compliance", {}),
            buyer_intel=context.get("buyer_intel", {}),
            credit_score=context.get("credit_score", {}),
            company_info=context.get("company_info", {}),
        )

    if step_name == "generate_summary":
        from app.agents.tools.generate_summary import generate_summary

        return generate_summary(
            extracted_data=context.get("extracted_data", {}),
            validation_result=context.get("validation_result", {}),
            fraud_result=context.get("fraud_result", {}),
            gst_compliance=context.get("gst_compliance", {}),
            gstin_verification=context.get("gstin_verification", {}),
            buyer_intel=context.get("buyer_intel", {}),
            credit_score=context.get("credit_score", {}),
            company_info=context.get("company_info", {}),
            risk_assessment=context.get("risk_assessment", {}),
        )

    # ------------------------------------------------------------------
    # Steps 11-13: Underwriting Agent tools
    # ------------------------------------------------------------------
    if step_name == "cross_validate_outputs":
        from app.agents.tools.cross_validate_outputs import _resolve_cross_validate
        from app.config import settings

        return _resolve_cross_validate(
            extracted_data=context.get("extracted_data", {}),
            validation_result=context.get("validation_result", {}),
            fraud_result=context.get("fraud_result", {}),
            gst_compliance=context.get("gst_compliance", {}),
            gstn_verification=context.get("gstin_verification", {}),
            buyer_intel=context.get("buyer_intel", {}),
            credit_score=context.get("credit_score", {}),
            company_info=context.get("company_info", {}),
            risk_assessment=context.get("risk_assessment", {}),
            use_demo=settings.DEMO_MODE,
        )

    if step_name == "underwriting_decision":
        # Routing logic: read signals, call the correct decision tool
        summary_result = context.get("summary_result", {})
        risk_assessment = context.get("risk_assessment", {})
        cross_validation = context.get("cross_validation", {})

        recommendation = summary_result.get("recommendation", "approve")
        risk_level = risk_assessment.get("level", "medium")
        risk_score = int(risk_assessment.get("score", 50))
        is_consistent = cross_validation.get("consistent", True)

        if recommendation == "reject" or risk_level == "critical":
            from app.agents.tools.reject_invoice import reject_invoice

            fraud_result = context.get("fraud_result", {})
            fraud_flags = list(fraud_result.get("flags", []))
            return reject_invoice(
                invoice_id=invoice_id,
                reason=summary_result.get(
                    "summary", "High risk score or critical signals."
                ),
                risk_score=risk_score,
                fraud_flags=fraud_flags,
            )

        if recommendation == "review" or not is_consistent:
            from app.agents.tools.flag_for_review import flag_for_review

            cross_validation_result = context.get("cross_validation", {})
            discrepancies = list(cross_validation_result.get("discrepancies", []))
            return flag_for_review(
                invoice_id=invoice_id,
                reason=summary_result.get("summary", "Manual review required."),
                discrepancies=discrepancies,
                risk_score=risk_score,
            )

        # Default: approve
        from app.agents.tools.approve_invoice import approve_invoice

        confidence = float(cross_validation.get("confidence", 0.90))
        return approve_invoice(
            invoice_id=invoice_id,
            reason=summary_result.get("summary", "Meets all approval criteria."),
            risk_score=risk_score,
            confidence=confidence,
        )

    if step_name == "log_decision":
        from app.agents.tools.log_decision import log_decision

        underwriting_decision = context.get("underwriting_decision", {})
        decision_str = underwriting_decision.get("decision", "unknown")
        all_signals = {
            "risk_assessment": context.get("risk_assessment", {}),
            "fraud_result": context.get("fraud_result", {}),
            "cross_validation": context.get("cross_validation", {}),
        }
        return log_decision(
            invoice_id=invoice_id,
            decision=decision_str,
            reasoning_trace=str(context.get("summary_result", {}).get("summary", "")),
            all_signals=all_signals,
        )

    # ------------------------------------------------------------------
    # Step 14: mint_nft (invoice_processing agent)
    # ------------------------------------------------------------------
    if step_name == "mint_nft":
        from app.agents.tools.mint_nft import mint_nft

        return mint_nft(
            invoice_id=invoice_id,
            extracted_data=context.get("extracted_data", {}),
            risk_assessment=context.get("risk_assessment", {}),
        )

    raise ValueError(f"_execute_step: unknown step_name '{step_name}'")


# ---------------------------------------------------------------------------
# _determine_final_status
# ---------------------------------------------------------------------------


def _determine_final_status(decision: str) -> str:
    """Map an underwriting decision string to the invoice status string.

    Args:
        decision: ``"approved"``, ``"rejected"``, or ``"flagged_for_review"``.

    Returns:
        The corresponding invoice status string.
    """
    mapping = {
        "approved": "approved",
        "rejected": "rejected",
        "flagged_for_review": "flagged_for_review",
    }
    return mapping.get(decision, "flagged_for_review")


# ---------------------------------------------------------------------------
# run_invoice_pipeline
# ---------------------------------------------------------------------------


async def run_invoice_pipeline(*, invoice: Any, db: AsyncSession) -> None:
    """Orchestrate the full 14-step invoice processing pipeline.

    Calls each tool via :func:`_execute_step`, persists results to the DB,
    and publishes WebSocket events after every step.  The ``mint_nft`` step
    is skipped when the underwriting decision is not ``"approved"``.

    On any unhandled exception the invoice status is set to ``"failed"`` and
    the exception is *not* re-raised (the background task must not crash the
    caller).

    Args:
        invoice: An Invoice ORM instance (must have id, file_key, user_id,
                 status, processing_started_at, processing_completed_at,
                 processing_duration_ms, underwriting attributes).
        db:      Async SQLAlchemy session bound to the invoice's database.
    """
    invoice_id_str = str(invoice.id)
    pipeline_start = time.monotonic()

    # ------------------------------------------------------------------
    # 1. Mark invoice as processing
    # ------------------------------------------------------------------
    invoice.status = "processing"
    invoice.processing_started_at = datetime.now(timezone.utc)
    await db.commit()

    # Shared context: seeded with static invoice fields.
    # Each completed step's result is accumulated here so downstream
    # tools can read what they need.
    ctx: dict[str, Any] = {
        "invoice_id": invoice_id_str,
        "file_key": invoice.file_key,
        "seller_id": str(invoice.user_id),
    }

    # Trace accumulator -- one entry per executed step
    step_trace: list[dict] = []

    # Underwriting decision result -- populated when step 12 runs
    decision_result: dict = {}

    # Track the current step name for error reporting
    current_step_name: str = "unknown"

    try:
        for entry in PIPELINE_STEPS:
            step_num = entry["step"]
            step_name = entry["step_name"]
            agent = entry["agent"]
            current_step_name = step_name

            # ----------------------------------------------------------
            # Conditional skip: mint_nft only when approved
            # ----------------------------------------------------------
            if step_name == "mint_nft":
                decision = decision_result.get("decision", "")
                if decision != "approved":
                    logger.info(
                        "Pipeline %s: skipping mint_nft (decision=%s)",
                        invoice_id_str,
                        decision,
                    )
                    continue

            # ----------------------------------------------------------
            # Execute the step and measure wall time
            # ----------------------------------------------------------
            step_start = time.monotonic()
            logger.info(
                "Pipeline %s: executing step %d/%d '%s'",
                invoice_id_str,
                step_num,
                len(PIPELINE_STEPS),
                step_name,
            )

            result = await _execute_step(step_name, **ctx)

            elapsed_ms = int((time.monotonic() - step_start) * 1000)

            # ----------------------------------------------------------
            # Keep track of the underwriting decision for routing
            # ----------------------------------------------------------
            if step_name == "underwriting_decision":
                decision_result = result
                # Store under a context key for log_decision to read
                ctx["underwriting_decision"] = result

            # ----------------------------------------------------------
            # Accumulate result into context for downstream steps
            # ----------------------------------------------------------
            _accumulate_context(ctx, step_name, result)

            # ----------------------------------------------------------
            # Persist to DB
            # ----------------------------------------------------------
            await persist_tool_result(
                db=db,
                invoice=invoice,
                step_name=step_name,
                result=result,
            )

            # ----------------------------------------------------------
            # Publish WebSocket event
            # ----------------------------------------------------------
            await publish_step_event(
                invoice_id=invoice_id_str,
                step=step_num,
                step_name=step_name,
                agent=agent,
                result=result,
                elapsed_ms=elapsed_ms,
            )

            # ----------------------------------------------------------
            # Accumulate step trace
            # ----------------------------------------------------------
            step_trace.append(
                {
                    "step": step_num,
                    "step_name": step_name,
                    "agent": agent,
                    "elapsed_ms": elapsed_ms,
                    "result": result,
                }
            )

        # ------------------------------------------------------------------
        # 2. Finalise invoice record
        # ------------------------------------------------------------------
        decision_str = decision_result.get("decision", "flagged_for_review")
        invoice.status = _determine_final_status(decision_str)
        invoice.underwriting = dict(decision_result)

        completed_at = datetime.now(timezone.utc)
        invoice.processing_completed_at = completed_at
        invoice.processing_duration_ms = int((time.monotonic() - pipeline_start) * 1000)
        await db.commit()

        # ------------------------------------------------------------------
        # 3. Persist agent trace
        # ------------------------------------------------------------------
        risk_assessment = ctx.get("risk_assessment", {})
        risk_score = int(risk_assessment.get("score", 0))
        nft_result = ctx.get("mint_nft_result", {})
        nft_asset_id = (
            nft_result.get("asset_id") if decision_str == "approved" else None
        )

        await save_agent_trace(
            db=db,
            invoice_id=invoice.id,
            agent_name="pipeline_runner",
            model=SONNET_MODEL_ID,
            duration_ms=invoice.processing_duration_ms,
            steps=step_trace,
            handoff_context={
                "decision": decision_str,
                "risk_score": risk_score,
            },
        )

        # ------------------------------------------------------------------
        # 4. Publish pipeline_complete event
        # ------------------------------------------------------------------
        reason = decision_result.get(
            "reason",
            ctx.get("summary_result", {}).get("summary", "Pipeline completed."),
        )
        await publish_pipeline_complete(
            invoice_id=invoice_id_str,
            decision=decision_str,
            risk_score=risk_score,
            reason=str(reason),
            nft_asset_id=nft_asset_id,
        )

        logger.info(
            "Pipeline %s COMPLETE: decision=%s risk_score=%d duration_ms=%d",
            invoice_id_str,
            decision_str,
            risk_score,
            invoice.processing_duration_ms,
        )

    except Exception as exc:  # noqa: BLE001
        logger.exception(
            "Pipeline %s FAILED at step '%s': %s",
            invoice_id_str,
            current_step_name,
            exc,
        )
        invoice.status = "failed"
        invoice.processing_completed_at = datetime.now(timezone.utc)
        invoice.processing_duration_ms = int((time.monotonic() - pipeline_start) * 1000)
        try:
            await db.commit()
        except Exception:  # noqa: BLE001
            logger.exception(
                "Failed to commit 'failed' status for invoice %s", invoice_id_str
            )
        # Do NOT re-raise -- background task must not crash
