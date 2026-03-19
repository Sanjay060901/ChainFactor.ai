"""TDD tests for DB Persistence Helper (Task 2).

Tests persist_tool_result() and save_agent_trace() in isolation using mocks.
No real database is required -- all SQLAlchemy interactions are mocked.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.modules.agents.persistence import (
    STEP_TO_COLUMN,
    persist_tool_result,
    save_agent_trace,
)


# ---------------------------------------------------------------------------
# STEP_TO_COLUMN mapping tests
# ---------------------------------------------------------------------------


class TestStepToColumnMapping:
    """Verify the STEP_TO_COLUMN mapping is complete and correct."""

    def test_mapping_has_all_10_invoice_steps(self):
        """STEP_TO_COLUMN must map exactly the 10 pipeline steps."""
        expected_steps = {
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
        }
        assert set(STEP_TO_COLUMN.keys()) == expected_steps

    def test_extract_invoice_maps_to_extracted_data(self):
        assert STEP_TO_COLUMN["extract_invoice"] == "extracted_data"

    def test_validate_fields_maps_to_validation_result(self):
        assert STEP_TO_COLUMN["validate_fields"] == "validation_result"

    def test_validate_gst_compliance_maps_to_gst_compliance(self):
        assert STEP_TO_COLUMN["validate_gst_compliance"] == "gst_compliance"

    def test_verify_gstn_maps_to_gstin_verification(self):
        assert STEP_TO_COLUMN["verify_gstn"] == "gstin_verification"

    def test_check_fraud_maps_to_fraud_detection(self):
        assert STEP_TO_COLUMN["check_fraud"] == "fraud_detection"

    def test_get_buyer_intel_maps_to_buyer_intel(self):
        assert STEP_TO_COLUMN["get_buyer_intel"] == "buyer_intel"

    def test_get_credit_score_maps_to_credit_score(self):
        assert STEP_TO_COLUMN["get_credit_score"] == "credit_score"

    def test_get_company_info_maps_to_company_info(self):
        assert STEP_TO_COLUMN["get_company_info"] == "company_info"

    def test_calculate_risk_maps_to_risk_assessment(self):
        assert STEP_TO_COLUMN["calculate_risk"] == "risk_assessment"

    def test_generate_summary_maps_to_ai_explanation(self):
        assert STEP_TO_COLUMN["generate_summary"] == "ai_explanation"


# ---------------------------------------------------------------------------
# persist_tool_result tests
# ---------------------------------------------------------------------------


class TestPersistToolResult:
    """Unit tests for persist_tool_result() using mock DB session and invoice."""

    def _make_invoice(self) -> MagicMock:
        """Return a mock invoice with all JSONB columns set to None."""
        invoice = MagicMock()
        invoice.extracted_data = None
        invoice.validation_result = None
        invoice.gst_compliance = None
        invoice.gstin_verification = None
        invoice.fraud_detection = None
        invoice.buyer_intel = None
        invoice.credit_score = None
        invoice.company_info = None
        invoice.risk_assessment = None
        invoice.risk_score = None
        invoice.ai_explanation = None
        return invoice

    def _make_db(self) -> AsyncMock:
        """Return a mock async DB session."""
        db = AsyncMock()
        db.commit = AsyncMock()
        return db

    @pytest.mark.anyio
    async def test_sets_attribute_on_invoice_for_standard_step(self):
        """persist_tool_result sets the correct JSONB column on the invoice."""
        invoice = self._make_invoice()
        db = self._make_db()
        result = {"invoice_number": "INV-001", "amount": 50000}

        await persist_tool_result(
            db=db,
            invoice=invoice,
            step_name="extract_invoice",
            result=result,
        )

        assert invoice.extracted_data == result

    @pytest.mark.anyio
    async def test_sets_validate_fields_column(self):
        invoice = self._make_invoice()
        db = self._make_db()
        result = {"valid": True, "errors": []}

        await persist_tool_result(
            db=db, invoice=invoice, step_name="validate_fields", result=result
        )

        assert invoice.validation_result == result

    @pytest.mark.anyio
    async def test_sets_risk_score_for_calculate_risk(self):
        """calculate_risk also denormalizes risk_score as an integer."""
        invoice = self._make_invoice()
        db = self._make_db()
        result = {"score": 72, "breakdown": {"fraud": 0.2}}

        await persist_tool_result(
            db=db, invoice=invoice, step_name="calculate_risk", result=result
        )

        assert invoice.risk_assessment == result
        assert invoice.risk_score == 72

    @pytest.mark.anyio
    async def test_calculate_risk_score_is_integer(self):
        """risk_score must be stored as int even if result score is float-like."""
        invoice = self._make_invoice()
        db = self._make_db()
        result = {"score": 85, "breakdown": {}}

        await persist_tool_result(
            db=db, invoice=invoice, step_name="calculate_risk", result=result
        )

        assert isinstance(invoice.risk_score, int)

    @pytest.mark.anyio
    async def test_generate_summary_stores_summary_string_not_dict(self):
        """generate_summary stores result['summary'] (a string) to ai_explanation."""
        invoice = self._make_invoice()
        db = self._make_db()
        result = {
            "summary": "Invoice is valid with low risk. Recommend approval.",
            "recommendation": "approve",
        }

        await persist_tool_result(
            db=db, invoice=invoice, step_name="generate_summary", result=result
        )

        # ai_explanation must hold the string, NOT the dict
        assert (
            invoice.ai_explanation
            == "Invoice is valid with low risk. Recommend approval."
        )
        assert isinstance(invoice.ai_explanation, str)

    @pytest.mark.anyio
    async def test_generate_summary_does_not_store_full_dict(self):
        """ai_explanation must not accidentally contain the full result dict."""
        invoice = self._make_invoice()
        db = self._make_db()
        result = {"summary": "Low risk invoice.", "recommendation": "approve"}

        await persist_tool_result(
            db=db, invoice=invoice, step_name="generate_summary", result=result
        )

        assert invoice.ai_explanation != result
        assert not isinstance(invoice.ai_explanation, dict)

    @pytest.mark.anyio
    async def test_unknown_step_does_not_crash(self):
        """Unknown step names must log a warning and not raise an exception."""
        invoice = self._make_invoice()
        db = self._make_db()
        result = {"data": "some value"}

        # Must not raise
        await persist_tool_result(
            db=db,
            invoice=invoice,
            step_name="unknown_step_xyz",
            result=result,
        )

    @pytest.mark.anyio
    async def test_unknown_step_does_not_modify_invoice(self):
        """Unknown step must not modify any invoice attributes."""
        invoice = self._make_invoice()
        db = self._make_db()

        await persist_tool_result(
            db=db,
            invoice=invoice,
            step_name="nonexistent_tool",
            result={"x": 1},
        )

        # None of the known columns should have been set
        assert invoice.extracted_data is None
        assert invoice.risk_score is None
        assert invoice.ai_explanation is None

    @pytest.mark.anyio
    async def test_calls_db_commit_after_persist(self):
        """db.commit() must always be called after persisting."""
        invoice = self._make_invoice()
        db = self._make_db()

        await persist_tool_result(
            db=db,
            invoice=invoice,
            step_name="extract_invoice",
            result={"amount": 1000},
        )

        db.commit.assert_called_once()

    @pytest.mark.anyio
    async def test_calls_db_commit_even_for_unknown_step(self):
        """db.commit() must be called even when step is unknown."""
        invoice = self._make_invoice()
        db = self._make_db()

        await persist_tool_result(
            db=db,
            invoice=invoice,
            step_name="unknown_step",
            result={"x": 1},
        )

        db.commit.assert_called_once()

    @pytest.mark.anyio
    async def test_all_non_special_steps_store_full_result_dict(self):
        """All steps except generate_summary store the full result dict."""
        non_special_steps = [
            ("extract_invoice", "extracted_data"),
            ("validate_fields", "validation_result"),
            ("validate_gst_compliance", "gst_compliance"),
            ("verify_gstn", "gstin_verification"),
            ("check_fraud", "fraud_detection"),
            ("get_buyer_intel", "buyer_intel"),
            ("get_credit_score", "credit_score"),
            ("get_company_info", "company_info"),
        ]
        for step_name, column_name in non_special_steps:
            invoice = self._make_invoice()
            db = self._make_db()
            result = {"step": step_name, "value": 42}

            await persist_tool_result(
                db=db, invoice=invoice, step_name=step_name, result=result
            )

            assert getattr(invoice, column_name) == result, (
                f"Step '{step_name}' should set column '{column_name}'"
            )


# ---------------------------------------------------------------------------
# save_agent_trace tests
# ---------------------------------------------------------------------------


class TestSaveAgentTrace:
    """Unit tests for save_agent_trace() using mock DB session."""

    def _make_db(self) -> AsyncMock:
        db = AsyncMock()
        db.add = MagicMock()  # synchronous
        db.commit = AsyncMock()
        return db

    @pytest.mark.anyio
    async def test_adds_trace_to_session(self):
        """save_agent_trace must call db.add() with an AgentTrace instance."""
        from app.models.agent_trace import AgentTrace

        db = self._make_db()
        invoice_id = uuid.uuid4()

        trace = await save_agent_trace(
            db=db,
            invoice_id=invoice_id,
            agent_name="invoice_processing_agent",
            model="us.anthropic.claude-sonnet-4-6-20250514-v1:0",
            duration_ms=5200,
            steps=[{"step_number": 1, "tool_name": "extract_invoice"}],
        )

        db.add.assert_called_once()
        added_obj = db.add.call_args[0][0]
        assert isinstance(added_obj, AgentTrace)

    @pytest.mark.anyio
    async def test_trace_has_correct_agent_name(self):
        db = self._make_db()

        trace = await save_agent_trace(
            db=db,
            invoice_id=uuid.uuid4(),
            agent_name="underwriting_agent",
            model="us.anthropic.claude-sonnet-4-6-20250514-v1:0",
            duration_ms=3100,
            steps=[],
        )

        assert trace.agent_name == "underwriting_agent"

    @pytest.mark.anyio
    async def test_trace_has_correct_duration_ms(self):
        db = self._make_db()

        trace = await save_agent_trace(
            db=db,
            invoice_id=uuid.uuid4(),
            agent_name="invoice_processing_agent",
            model="us.anthropic.claude-sonnet-4-6-20250514-v1:0",
            duration_ms=8750,
            steps=[],
        )

        assert trace.duration_ms == 8750

    @pytest.mark.anyio
    async def test_trace_has_correct_model(self):
        db = self._make_db()
        model_id = "us.anthropic.claude-sonnet-4-6-20250514-v1:0"

        trace = await save_agent_trace(
            db=db,
            invoice_id=uuid.uuid4(),
            agent_name="invoice_processing_agent",
            model=model_id,
            duration_ms=1000,
            steps=[],
        )

        assert trace.model == model_id

    @pytest.mark.anyio
    async def test_trace_has_correct_invoice_id(self):
        db = self._make_db()
        invoice_id = uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")

        trace = await save_agent_trace(
            db=db,
            invoice_id=invoice_id,
            agent_name="invoice_processing_agent",
            model="us.anthropic.claude-sonnet-4-6-20250514-v1:0",
            duration_ms=1000,
            steps=[],
        )

        assert trace.invoice_id == invoice_id

    @pytest.mark.anyio
    async def test_trace_persists_steps_list(self):
        db = self._make_db()
        steps = [
            {"step_number": 1, "tool_name": "extract_invoice", "duration_ms": 3200},
            {"step_number": 2, "tool_name": "validate_fields", "duration_ms": 800},
        ]

        trace = await save_agent_trace(
            db=db,
            invoice_id=uuid.uuid4(),
            agent_name="invoice_processing_agent",
            model="us.anthropic.claude-sonnet-4-6-20250514-v1:0",
            duration_ms=4000,
            steps=steps,
        )

        assert trace.steps == steps

    @pytest.mark.anyio
    async def test_trace_handoff_context_defaults_to_none(self):
        """handoff_context is optional and defaults to None."""
        db = self._make_db()

        trace = await save_agent_trace(
            db=db,
            invoice_id=uuid.uuid4(),
            agent_name="invoice_processing_agent",
            model="us.anthropic.claude-sonnet-4-6-20250514-v1:0",
            duration_ms=1000,
            steps=[],
        )

        assert trace.handoff_context is None

    @pytest.mark.anyio
    async def test_trace_stores_handoff_context_when_provided(self):
        """handoff_context is stored when explicitly provided."""
        db = self._make_db()
        handoff = {"risk_score": 72, "recommendation": "approve"}

        trace = await save_agent_trace(
            db=db,
            invoice_id=uuid.uuid4(),
            agent_name="invoice_processing_agent",
            model="us.anthropic.claude-sonnet-4-6-20250514-v1:0",
            duration_ms=1000,
            steps=[],
            handoff_context=handoff,
        )

        assert trace.handoff_context == handoff

    @pytest.mark.anyio
    async def test_save_agent_trace_calls_db_commit(self):
        """save_agent_trace must commit after adding the trace."""
        db = self._make_db()

        await save_agent_trace(
            db=db,
            invoice_id=uuid.uuid4(),
            agent_name="invoice_processing_agent",
            model="us.anthropic.claude-sonnet-4-6-20250514-v1:0",
            duration_ms=1000,
            steps=[],
        )

        db.commit.assert_called_once()

    @pytest.mark.anyio
    async def test_save_agent_trace_returns_agent_trace_instance(self):
        """save_agent_trace must return the created AgentTrace instance."""
        from app.models.agent_trace import AgentTrace

        db = self._make_db()

        trace = await save_agent_trace(
            db=db,
            invoice_id=uuid.uuid4(),
            agent_name="invoice_processing_agent",
            model="us.anthropic.claude-sonnet-4-6-20250514-v1:0",
            duration_ms=1000,
            steps=[],
        )

        assert isinstance(trace, AgentTrace)
