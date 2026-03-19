"""TDD tests for the Pipeline Runner (Task 3).

Tests cover:
  - PIPELINE_STEPS structure: length, numbering, agent assignments, step names
  - _accumulate_context: correct key mapping for all steps
  - run_invoice_pipeline: orchestration, status transitions, step calls,
    mint_nft skip on rejection, failure handling, underwriting decision routing
  - All mocks at the correct patch path so no real tools are executed
"""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers: fake step results keyed by step_name
# ---------------------------------------------------------------------------

FAKE_EXTRACTED_DATA = {
    "seller": {"name": "Tata Steel", "gstin": "27AABCT1234R1ZM", "address": "Mumbai"},
    "buyer": {"name": "Reliance Infra", "gstin": "07AABCR5678R1ZN", "address": "Delhi"},
    "invoice_number": "INV-2026-0001",
    "invoice_date": "2026-03-01",
    "due_date": "2026-04-01",
    "subtotal": 400000.0,
    "tax_amount": 72000.0,
    "tax_rate": 18.0,
    "total_amount": 472000.0,
    "line_items": [],
    "currency": "INR",
}

FAKE_RISK_ASSESSMENT = {
    "score": 78,
    "level": "medium",
    "breakdown": {"fraud": 0.1, "gstn": 0.0, "credit": 0.2},
}

FAKE_SUMMARY = {
    "summary": "Invoice looks valid. Low risk.",
    "recommendation": "approve",
}

FAKE_CROSS_VALIDATION = {
    "consistent": True,
    "discrepancies": [],
    "confidence": 0.95,
}

FAKE_APPROVED_DECISION = {
    "decision": "approved",
    "invoice_id": "inv-test-001",
    "reason": "Low risk. Meets all criteria.",
    "risk_score": 78,
    "confidence": 0.92,
}

FAKE_REJECTED_DECISION = {
    "decision": "rejected",
    "invoice_id": "inv-test-001",
    "reason": "High fraud risk.",
    "risk_score": 22,
    "fraud_flags": ["duplicate_gstin", "amount_mismatch"],
}

FAKE_FLAGGED_DECISION = {
    "decision": "flagged_for_review",
    "invoice_id": "inv-test-001",
    "reason": "Borderline risk.",
    "discrepancies": ["minor_amount_discrepancy"],
    "risk_score": 55,
}

FAKE_LOG_DECISION = {
    "logged": True,
    "invoice_id": "inv-test-001",
    "decision": "approved",
    "trace_id": "trace-0001",
}

FAKE_MINT_NFT = {
    "success": True,
    "asset_id": 123456789,
    "txn_id": "TXNHASH000111",
    "explorer_url": "https://testnet.explorer.perawallet.app/asset/123456789/",
}


def make_fake_execute(decision: str = "approved"):
    """Return an async callable that returns plausible fake results per step."""

    async def fake_execute(step_name: str, **ctx: Any) -> dict:
        mapping = {
            "extract_invoice": FAKE_EXTRACTED_DATA,
            "validate_fields": {"valid": True, "errors": []},
            "validate_gst_compliance": {"compliant": True, "issues": []},
            "verify_gstn": {"seller_active": True, "buyer_active": True},
            "check_fraud": {"passed": True, "flags": [], "score": 92},
            "get_buyer_intel": {"payment_history": "good", "default_rate": 0.01},
            "get_credit_score": {"cibil_score": 780, "category": "excellent"},
            "get_company_info": {"company_name": "Reliance", "status": "active"},
            "calculate_risk": FAKE_RISK_ASSESSMENT,
            "generate_summary": FAKE_SUMMARY,
            "cross_validate_outputs": FAKE_CROSS_VALIDATION,
            "log_decision": FAKE_LOG_DECISION,
            "mint_nft": FAKE_MINT_NFT,
        }
        # underwriting_decision is determined by pipeline routing logic, not
        # called via _execute_step directly -- but include it just in case
        if step_name == "underwriting_decision":
            if decision == "approved":
                return FAKE_APPROVED_DECISION
            elif decision == "rejected":
                return FAKE_REJECTED_DECISION
            else:
                return FAKE_FLAGGED_DECISION
        return mapping.get(step_name, {"result": f"fake_{step_name}"})

    return fake_execute


def make_mock_invoice(
    invoice_id: str = "11111111-1111-1111-1111-111111111111",
) -> MagicMock:
    """Return a mock Invoice ORM instance."""
    invoice = MagicMock()
    invoice.id = uuid.UUID(invoice_id)
    invoice.file_key = "invoices/test/invoice.pdf"
    invoice.user_id = uuid.UUID("22222222-2222-2222-2222-222222222222")
    invoice.status = "pending"
    invoice.processing_started_at = None
    invoice.processing_completed_at = None
    invoice.processing_duration_ms = None
    invoice.underwriting = None
    return invoice


def make_mock_db() -> AsyncMock:
    """Return a mock async SQLAlchemy session."""
    db = AsyncMock()
    db.commit = AsyncMock()
    db.add = MagicMock()
    return db


# ---------------------------------------------------------------------------
# 1. PIPELINE_STEPS structure
# ---------------------------------------------------------------------------


class TestPipelineStepsStructure:
    """Verify PIPELINE_STEPS constant is correctly defined."""

    def test_pipeline_steps_has_14_entries(self):
        """PIPELINE_STEPS must contain exactly 14 entries."""
        from app.modules.agents.pipeline import PIPELINE_STEPS

        assert len(PIPELINE_STEPS) == 14

    def test_steps_are_numbered_1_through_14(self):
        """Steps must be consecutively numbered 1-14, no gaps."""
        from app.modules.agents.pipeline import PIPELINE_STEPS

        numbers = [s["step"] for s in PIPELINE_STEPS]
        assert numbers == list(range(1, 15))

    def test_first_step_is_extract_invoice(self):
        """Step 1 must be extract_invoice."""
        from app.modules.agents.pipeline import PIPELINE_STEPS

        assert PIPELINE_STEPS[0]["step_name"] == "extract_invoice"

    def test_last_step_is_mint_nft(self):
        """Step 14 must be mint_nft."""
        from app.modules.agents.pipeline import PIPELINE_STEPS

        assert PIPELINE_STEPS[13]["step_name"] == "mint_nft"

    def test_steps_1_to_10_are_invoice_processing_agent(self):
        """Steps 1-10 must all belong to invoice_processing agent."""
        from app.modules.agents.pipeline import PIPELINE_STEPS

        for entry in PIPELINE_STEPS[:10]:
            assert entry["agent"] == "invoice_processing", (
                f"Step {entry['step']} ({entry['step_name']}) should be "
                f"invoice_processing, got {entry['agent']}"
            )

    def test_steps_11_to_13_are_underwriting_agent(self):
        """Steps 11-13 must all belong to underwriting agent."""
        from app.modules.agents.pipeline import PIPELINE_STEPS

        for entry in PIPELINE_STEPS[10:13]:
            assert entry["agent"] == "underwriting", (
                f"Step {entry['step']} ({entry['step_name']}) should be "
                f"underwriting, got {entry['agent']}"
            )

    def test_step_14_mint_nft_is_invoice_processing_agent(self):
        """Step 14 (mint_nft) must be invoice_processing agent."""
        from app.modules.agents.pipeline import PIPELINE_STEPS

        assert PIPELINE_STEPS[13]["agent"] == "invoice_processing"

    def test_each_step_has_required_keys(self):
        """Each step dict must have step, step_name, and agent keys."""
        from app.modules.agents.pipeline import PIPELINE_STEPS

        for entry in PIPELINE_STEPS:
            assert "step" in entry, f"Missing 'step' in {entry}"
            assert "step_name" in entry, f"Missing 'step_name' in {entry}"
            assert "agent" in entry, f"Missing 'agent' in {entry}"

    def test_step_names_match_expected_sequence(self):
        """All step_names must appear in the correct order."""
        from app.modules.agents.pipeline import PIPELINE_STEPS

        expected = [
            "extract_invoice",
            "validate_fields",
            "validate_gst_compliance",
            "verify_gstn",
            "check_fraud",
            "get_buyer_intel",
            "get_credit_score",
            "get_company_info",
            "calculate_risk",
            "generate_summary",
            "cross_validate_outputs",
            "underwriting_decision",
            "log_decision",
            "mint_nft",
        ]
        actual = [s["step_name"] for s in PIPELINE_STEPS]
        assert actual == expected


# ---------------------------------------------------------------------------
# 2. _accumulate_context
# ---------------------------------------------------------------------------


class TestAccumulateContext:
    """Unit tests for _accumulate_context helper."""

    def test_extract_invoice_maps_to_extracted_data(self):
        from app.modules.agents.pipeline import _accumulate_context

        ctx: dict = {}
        _accumulate_context(ctx, "extract_invoice", {"amount": 100})
        assert "extracted_data" in ctx
        assert ctx["extracted_data"] == {"amount": 100}

    def test_validate_fields_maps_to_validation_result(self):
        from app.modules.agents.pipeline import _accumulate_context

        ctx: dict = {}
        _accumulate_context(ctx, "validate_fields", {"valid": True})
        assert ctx["validation_result"] == {"valid": True}

    def test_validate_gst_compliance_maps_to_gst_compliance(self):
        from app.modules.agents.pipeline import _accumulate_context

        ctx: dict = {}
        _accumulate_context(ctx, "validate_gst_compliance", {"compliant": True})
        assert ctx["gst_compliance"] == {"compliant": True}

    def test_verify_gstn_maps_to_gstin_verification(self):
        from app.modules.agents.pipeline import _accumulate_context

        ctx: dict = {}
        _accumulate_context(ctx, "verify_gstn", {"active": True})
        assert ctx["gstin_verification"] == {"active": True}

    def test_check_fraud_maps_to_fraud_result(self):
        from app.modules.agents.pipeline import _accumulate_context

        ctx: dict = {}
        _accumulate_context(ctx, "check_fraud", {"passed": True})
        assert ctx["fraud_result"] == {"passed": True}

    def test_get_buyer_intel_maps_to_buyer_intel(self):
        from app.modules.agents.pipeline import _accumulate_context

        ctx: dict = {}
        _accumulate_context(ctx, "get_buyer_intel", {"payment_history": "good"})
        assert ctx["buyer_intel"] == {"payment_history": "good"}

    def test_get_credit_score_maps_to_credit_score(self):
        from app.modules.agents.pipeline import _accumulate_context

        ctx: dict = {}
        _accumulate_context(ctx, "get_credit_score", {"cibil_score": 780})
        assert ctx["credit_score"] == {"cibil_score": 780}

    def test_get_company_info_maps_to_company_info(self):
        from app.modules.agents.pipeline import _accumulate_context

        ctx: dict = {}
        _accumulate_context(ctx, "get_company_info", {"status": "active"})
        assert ctx["company_info"] == {"status": "active"}

    def test_calculate_risk_maps_to_risk_assessment(self):
        from app.modules.agents.pipeline import _accumulate_context

        ctx: dict = {}
        _accumulate_context(ctx, "calculate_risk", {"score": 78})
        assert ctx["risk_assessment"] == {"score": 78}

    def test_generate_summary_maps_to_summary_result(self):
        from app.modules.agents.pipeline import _accumulate_context

        ctx: dict = {}
        _accumulate_context(ctx, "generate_summary", {"summary": "ok"})
        assert ctx["summary_result"] == {"summary": "ok"}

    def test_cross_validate_outputs_maps_to_cross_validation(self):
        from app.modules.agents.pipeline import _accumulate_context

        ctx: dict = {}
        _accumulate_context(ctx, "cross_validate_outputs", {"consistent": True})
        assert ctx["cross_validation"] == {"consistent": True}

    def test_mint_nft_maps_to_mint_nft_result(self):
        from app.modules.agents.pipeline import _accumulate_context

        ctx: dict = {}
        _accumulate_context(ctx, "mint_nft", {"asset_id": 999})
        assert ctx["mint_nft_result"] == {"asset_id": 999}

    def test_unknown_step_is_silently_ignored(self):
        """Unknown step names must not raise an error."""
        from app.modules.agents.pipeline import _accumulate_context

        ctx: dict = {}
        _accumulate_context(ctx, "nonexistent_step_xyz", {"data": 1})
        # No exception and no unexpected key added
        assert "nonexistent_step_xyz" not in ctx

    def test_context_is_mutated_in_place(self):
        """_accumulate_context modifies the ctx dict directly (no return value)."""
        from app.modules.agents.pipeline import _accumulate_context

        ctx: dict = {"invoice_id": "abc"}
        result = _accumulate_context(ctx, "extract_invoice", {"amount": 100})
        assert result is None  # No return value
        assert ctx["extracted_data"] == {"amount": 100}
        assert ctx["invoice_id"] == "abc"  # Existing keys preserved


# ---------------------------------------------------------------------------
# 3. run_invoice_pipeline -- orchestration tests (mocked _execute_step)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
class TestRunInvoicePipelineOrchestration:
    """Integration-style tests for run_invoice_pipeline.

    _execute_step, persist_tool_result, publish_step_event,
    publish_pipeline_complete, and save_agent_trace are all mocked.
    """

    def _patches(self, execute_side_effect=None):
        """Return a dict of patch targets for the pipeline module."""
        if execute_side_effect is None:
            execute_side_effect = make_fake_execute("approved")
        return {
            "execute": patch(
                "app.modules.agents.pipeline._execute_step",
                side_effect=execute_side_effect,
            ),
            "persist": patch(
                "app.modules.agents.pipeline.persist_tool_result",
                new_callable=AsyncMock,
            ),
            "publish_step": patch(
                "app.modules.agents.pipeline.publish_step_event",
                new_callable=AsyncMock,
            ),
            "publish_complete": patch(
                "app.modules.agents.pipeline.publish_pipeline_complete",
                new_callable=AsyncMock,
            ),
            "save_trace": patch(
                "app.modules.agents.pipeline.save_agent_trace",
                new_callable=AsyncMock,
            ),
        }

    async def test_all_14_steps_called_on_approval(self):
        """run_invoice_pipeline calls _execute_step exactly 14 times on approval."""
        invoice = make_mock_invoice()
        db = make_mock_db()

        execute_mock = AsyncMock(side_effect=make_fake_execute("approved"))
        patches = self._patches(execute_mock)

        with (
            patches["execute"] as mock_exec,
            patches["persist"],
            patches["publish_step"],
            patches["publish_complete"],
            patches["save_trace"],
        ):
            from app.modules.agents.pipeline import run_invoice_pipeline

            await run_invoice_pipeline(invoice=invoice, db=db)

        assert mock_exec.call_count == 14

    async def test_mint_nft_skipped_on_rejection(self):
        """mint_nft step is skipped when decision is rejected (only 13 steps called)."""
        invoice = make_mock_invoice()
        db = make_mock_db()

        # Override summary, risk AND underwriting_decision to drive rejection path
        async def fake_rejected(step_name: str, **ctx: Any) -> dict:
            base = make_fake_execute("approved")
            result = await base(step_name, **ctx)
            if step_name == "generate_summary":
                return {"summary": "High risk.", "recommendation": "reject"}
            if step_name == "calculate_risk":
                return {"score": 20, "level": "critical", "breakdown": {}}
            if step_name == "underwriting_decision":
                return FAKE_REJECTED_DECISION
            return result

        execute_mock = AsyncMock(side_effect=fake_rejected)
        patches = self._patches(execute_mock)

        with (
            patches["execute"] as mock_exec,
            patches["persist"],
            patches["publish_step"],
            patches["publish_complete"],
            patches["save_trace"],
        ):
            from app.modules.agents.pipeline import run_invoice_pipeline

            await run_invoice_pipeline(invoice=invoice, db=db)

        called_step_names = [c.args[0] for c in mock_exec.call_args_list]
        assert "mint_nft" not in called_step_names
        assert mock_exec.call_count == 13

    async def test_status_set_to_processing_at_start(self):
        """invoice.status must be set to 'processing' before any steps run."""
        invoice = make_mock_invoice()
        db = make_mock_db()

        status_at_first_call = []

        async def capture_status(step_name: str, **ctx: Any) -> dict:
            # Capture status on very first call
            if not status_at_first_call:
                status_at_first_call.append(invoice.status)
            return await make_fake_execute("approved")(step_name, **ctx)

        patches = self._patches(capture_status)

        with (
            patches["execute"],
            patches["persist"],
            patches["publish_step"],
            patches["publish_complete"],
            patches["save_trace"],
        ):
            from app.modules.agents.pipeline import run_invoice_pipeline

            await run_invoice_pipeline(invoice=invoice, db=db)

        assert status_at_first_call[0] == "processing"

    async def test_final_status_approved(self):
        """invoice.status must be 'approved' after a successful approval run."""
        invoice = make_mock_invoice()
        db = make_mock_db()

        patches = self._patches(make_fake_execute("approved"))

        with (
            patches["execute"],
            patches["persist"],
            patches["publish_step"],
            patches["publish_complete"],
            patches["save_trace"],
        ):
            from app.modules.agents.pipeline import run_invoice_pipeline

            await run_invoice_pipeline(invoice=invoice, db=db)

        assert invoice.status == "approved"

    async def test_final_status_rejected(self):
        """invoice.status must be 'rejected' when decision is rejected."""
        invoice = make_mock_invoice()
        db = make_mock_db()

        async def fake_reject(step_name: str, **ctx: Any) -> dict:
            result = await make_fake_execute("approved")(step_name, **ctx)
            if step_name == "generate_summary":
                return {"summary": "Fraud detected.", "recommendation": "reject"}
            if step_name == "calculate_risk":
                return {"score": 15, "level": "critical", "breakdown": {}}
            if step_name == "underwriting_decision":
                return FAKE_REJECTED_DECISION
            return result

        patches = self._patches(fake_reject)

        with (
            patches["execute"],
            patches["persist"],
            patches["publish_step"],
            patches["publish_complete"],
            patches["save_trace"],
        ):
            from app.modules.agents.pipeline import run_invoice_pipeline

            await run_invoice_pipeline(invoice=invoice, db=db)

        assert invoice.status == "rejected"

    async def test_final_status_flagged(self):
        """invoice.status must be 'flagged_for_review' when decision is flagged."""
        invoice = make_mock_invoice()
        db = make_mock_db()

        async def fake_flag(step_name: str, **ctx: Any) -> dict:
            result = await make_fake_execute("approved")(step_name, **ctx)
            if step_name == "generate_summary":
                return {"summary": "Borderline.", "recommendation": "review"}
            if step_name == "cross_validate_outputs":
                return {
                    "consistent": False,
                    "discrepancies": ["minor issue"],
                    "confidence": 0.6,
                }
            if step_name == "underwriting_decision":
                return FAKE_FLAGGED_DECISION
            return result

        patches = self._patches(fake_flag)

        with (
            patches["execute"],
            patches["persist"],
            patches["publish_step"],
            patches["publish_complete"],
            patches["save_trace"],
        ):
            from app.modules.agents.pipeline import run_invoice_pipeline

            await run_invoice_pipeline(invoice=invoice, db=db)

        assert invoice.status == "flagged_for_review"

    async def test_status_set_to_failed_on_exception(self):
        """invoice.status must be 'failed' when an exception is raised mid-pipeline."""
        invoice = make_mock_invoice()
        db = make_mock_db()

        async def boom(step_name: str, **ctx: Any) -> dict:
            if step_name == "validate_fields":
                raise RuntimeError("Simulated tool failure")
            return await make_fake_execute("approved")(step_name, **ctx)

        patches = self._patches(boom)

        with (
            patches["execute"],
            patches["persist"],
            patches["publish_step"],
            patches["publish_complete"],
            patches["save_trace"],
        ):
            from app.modules.agents.pipeline import run_invoice_pipeline

            # Must NOT re-raise the exception
            await run_invoice_pipeline(invoice=invoice, db=db)

        assert invoice.status == "failed"

    async def test_exception_does_not_propagate(self):
        """run_invoice_pipeline must not re-raise exceptions to the caller."""
        invoice = make_mock_invoice()
        db = make_mock_db()

        async def boom(step_name: str, **ctx: Any) -> dict:
            raise ValueError("Catastrophic failure")

        patches = self._patches(boom)

        with (
            patches["execute"],
            patches["persist"],
            patches["publish_step"],
            patches["publish_complete"],
            patches["save_trace"],
        ):
            from app.modules.agents.pipeline import run_invoice_pipeline

            try:
                await run_invoice_pipeline(invoice=invoice, db=db)
            except Exception as exc:
                pytest.fail(f"run_invoice_pipeline re-raised an exception: {exc}")

    async def test_persist_tool_result_called_per_step(self):
        """persist_tool_result must be called for each completed step."""
        invoice = make_mock_invoice()
        db = make_mock_db()

        patches = self._patches(make_fake_execute("approved"))

        with (
            patches["execute"],
            patches["persist"] as mock_persist,
            patches["publish_step"],
            patches["publish_complete"],
            patches["save_trace"],
        ):
            from app.modules.agents.pipeline import run_invoice_pipeline

            await run_invoice_pipeline(invoice=invoice, db=db)

        # Must be called once per step (14 total for approved)
        assert mock_persist.call_count == 14

    async def test_publish_step_event_called_per_step(self):
        """publish_step_event must be called for each completed step."""
        invoice = make_mock_invoice()
        db = make_mock_db()

        patches = self._patches(make_fake_execute("approved"))

        with (
            patches["execute"],
            patches["persist"],
            patches["publish_step"] as mock_pub,
            patches["publish_complete"],
            patches["save_trace"],
        ):
            from app.modules.agents.pipeline import run_invoice_pipeline

            await run_invoice_pipeline(invoice=invoice, db=db)

        assert mock_pub.call_count == 14

    async def test_publish_pipeline_complete_called_once(self):
        """publish_pipeline_complete must be called exactly once at pipeline end."""
        invoice = make_mock_invoice()
        db = make_mock_db()

        patches = self._patches(make_fake_execute("approved"))

        with (
            patches["execute"],
            patches["persist"],
            patches["publish_step"],
            patches["publish_complete"] as mock_complete,
            patches["save_trace"],
        ):
            from app.modules.agents.pipeline import run_invoice_pipeline

            await run_invoice_pipeline(invoice=invoice, db=db)

        mock_complete.assert_called_once()

    async def test_save_agent_trace_called_once(self):
        """save_agent_trace must be called exactly once at pipeline end."""
        invoice = make_mock_invoice()
        db = make_mock_db()

        patches = self._patches(make_fake_execute("approved"))

        with (
            patches["execute"],
            patches["persist"],
            patches["publish_step"],
            patches["publish_complete"],
            patches["save_trace"] as mock_trace,
        ):
            from app.modules.agents.pipeline import run_invoice_pipeline

            await run_invoice_pipeline(invoice=invoice, db=db)

        mock_trace.assert_called_once()

    async def test_processing_started_at_is_set(self):
        """processing_started_at must be set before the first step."""
        invoice = make_mock_invoice()
        db = make_mock_db()

        patches = self._patches(make_fake_execute("approved"))

        with (
            patches["execute"],
            patches["persist"],
            patches["publish_step"],
            patches["publish_complete"],
            patches["save_trace"],
        ):
            from app.modules.agents.pipeline import run_invoice_pipeline

            await run_invoice_pipeline(invoice=invoice, db=db)

        assert invoice.processing_started_at is not None

    async def test_processing_completed_at_is_set(self):
        """processing_completed_at must be set after the last step."""
        invoice = make_mock_invoice()
        db = make_mock_db()

        patches = self._patches(make_fake_execute("approved"))

        with (
            patches["execute"],
            patches["persist"],
            patches["publish_step"],
            patches["publish_complete"],
            patches["save_trace"],
        ):
            from app.modules.agents.pipeline import run_invoice_pipeline

            await run_invoice_pipeline(invoice=invoice, db=db)

        assert invoice.processing_completed_at is not None

    async def test_processing_duration_ms_is_set(self):
        """processing_duration_ms must be set and be a non-negative integer."""
        invoice = make_mock_invoice()
        db = make_mock_db()

        patches = self._patches(make_fake_execute("approved"))

        with (
            patches["execute"],
            patches["persist"],
            patches["publish_step"],
            patches["publish_complete"],
            patches["save_trace"],
        ):
            from app.modules.agents.pipeline import run_invoice_pipeline

            await run_invoice_pipeline(invoice=invoice, db=db)

        assert invoice.processing_duration_ms is not None
        assert isinstance(invoice.processing_duration_ms, int)
        assert invoice.processing_duration_ms >= 0

    async def test_underwriting_jsonb_set_on_completion(self):
        """invoice.underwriting JSONB must be set with the decision dict."""
        invoice = make_mock_invoice()
        db = make_mock_db()

        patches = self._patches(make_fake_execute("approved"))

        with (
            patches["execute"],
            patches["persist"],
            patches["publish_step"],
            patches["publish_complete"],
            patches["save_trace"],
        ):
            from app.modules.agents.pipeline import run_invoice_pipeline

            await run_invoice_pipeline(invoice=invoice, db=db)

        assert invoice.underwriting is not None
        assert isinstance(invoice.underwriting, dict)

    async def test_mint_nft_step_called_when_approved(self):
        """mint_nft step must be called when decision is approved."""
        invoice = make_mock_invoice()
        db = make_mock_db()

        execute_mock = AsyncMock(side_effect=make_fake_execute("approved"))
        patches = self._patches(execute_mock)

        with (
            patches["execute"] as mock_exec,
            patches["persist"],
            patches["publish_step"],
            patches["publish_complete"],
            patches["save_trace"],
        ):
            from app.modules.agents.pipeline import run_invoice_pipeline

            await run_invoice_pipeline(invoice=invoice, db=db)

        called_step_names = [c.args[0] for c in mock_exec.call_args_list]
        assert "mint_nft" in called_step_names

    async def test_db_commit_called_at_completion(self):
        """db.commit() must be called at least once during the pipeline."""
        invoice = make_mock_invoice()
        db = make_mock_db()

        patches = self._patches(make_fake_execute("approved"))

        with (
            patches["execute"],
            patches["persist"],
            patches["publish_step"],
            patches["publish_complete"],
            patches["save_trace"],
        ):
            from app.modules.agents.pipeline import run_invoice_pipeline

            await run_invoice_pipeline(invoice=invoice, db=db)

        assert db.commit.call_count >= 1

    async def test_publish_complete_receives_correct_decision(self):
        """publish_pipeline_complete must be called with the correct decision."""
        invoice = make_mock_invoice()
        db = make_mock_db()

        patches = self._patches(make_fake_execute("approved"))

        with (
            patches["execute"],
            patches["persist"],
            patches["publish_step"],
            patches["publish_complete"] as mock_complete,
            patches["save_trace"],
        ):
            from app.modules.agents.pipeline import run_invoice_pipeline

            await run_invoice_pipeline(invoice=invoice, db=db)

        call_kwargs = mock_complete.call_args.kwargs
        assert call_kwargs.get("decision") == "approved"
