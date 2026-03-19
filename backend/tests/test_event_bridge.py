"""Tests for the agent event bridge (Task 1).

Tests cover:
  - build_step_event: all required keys, correct type, progress calculation,
    default status, human-readable detail strings
  - build_pipeline_complete_event: correct type, all fields, optional nft_asset_id
  - publish_step_event: calls publish_event with correct channel data
  - publish_pipeline_complete: calls publish_event with correct channel data
  - Edge cases: step boundary values, unknown step_name, None nft_asset_id
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.modules.agents.event_bridge import (
    TOTAL_STEPS,
    build_pipeline_complete_event,
    build_step_event,
    publish_pipeline_complete,
    publish_step_event,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestTotalSteps:
    """TOTAL_STEPS constant is 14 as per the WebSocket schema."""

    def test_total_steps_is_14(self):
        assert TOTAL_STEPS == 14


# ---------------------------------------------------------------------------
# build_step_event
# ---------------------------------------------------------------------------


class TestBuildStepEvent:
    """Unit tests for build_step_event."""

    def test_returns_dict(self):
        event = build_step_event(
            step=1,
            step_name="extract_invoice",
            agent="invoice_processing",
            result={},
            elapsed_ms=1000,
        )
        assert isinstance(event, dict)

    def test_type_is_step_complete(self):
        event = build_step_event(
            step=1,
            step_name="extract_invoice",
            agent="invoice_processing",
            result={},
            elapsed_ms=1000,
        )
        assert event["type"] == "step_complete"

    def test_all_required_keys_present(self):
        event = build_step_event(
            step=3,
            step_name="validate_gst_compliance",
            agent="invoice_processing",
            result={"valid": True},
            elapsed_ms=2500,
        )
        required_keys = {
            "type",
            "step",
            "step_name",
            "agent",
            "status",
            "detail",
            "result",
            "progress",
            "elapsed_ms",
        }
        assert required_keys.issubset(event.keys())

    def test_fields_round_trip(self):
        result_payload = {"score": 92, "flags": []}
        event = build_step_event(
            step=5,
            step_name="check_fraud",
            agent="invoice_processing",
            result=result_payload,
            elapsed_ms=4200,
        )
        assert event["step"] == 5
        assert event["step_name"] == "check_fraud"
        assert event["agent"] == "invoice_processing"
        assert event["result"] == result_payload
        assert event["elapsed_ms"] == 4200

    def test_status_defaults_to_complete(self):
        event = build_step_event(
            step=2,
            step_name="validate_fields",
            agent="invoice_processing",
            result={},
            elapsed_ms=500,
        )
        assert event["status"] == "complete"

    def test_status_can_be_overridden(self):
        event = build_step_event(
            step=2,
            step_name="validate_fields",
            agent="invoice_processing",
            result={},
            elapsed_ms=500,
            status="error",
        )
        assert event["status"] == "error"

    def test_progress_at_step_1(self):
        event = build_step_event(
            step=1,
            step_name="extract_invoice",
            agent="invoice_processing",
            result={},
            elapsed_ms=100,
        )
        expected = round(1 / 14, 2)
        assert event["progress"] == expected

    def test_progress_at_step_14(self):
        event = build_step_event(
            step=14,
            step_name="mint_nft",
            agent="underwriting",
            result={},
            elapsed_ms=8000,
        )
        assert event["progress"] == 1.0

    def test_progress_at_step_7(self):
        event = build_step_event(
            step=7,
            step_name="get_credit_score",
            agent="invoice_processing",
            result={},
            elapsed_ms=3000,
        )
        expected = round(7 / 14, 2)
        assert event["progress"] == expected

    def test_progress_is_float(self):
        event = build_step_event(
            step=3,
            step_name="validate_gst_compliance",
            agent="invoice_processing",
            result={},
            elapsed_ms=1500,
        )
        assert isinstance(event["progress"], float)

    def test_detail_is_non_empty_string(self):
        event = build_step_event(
            step=1,
            step_name="extract_invoice",
            agent="invoice_processing",
            result={},
            elapsed_ms=100,
        )
        assert isinstance(event["detail"], str)
        assert len(event["detail"]) > 0

    def test_detail_for_extract_invoice(self):
        event = build_step_event(
            step=1,
            step_name="extract_invoice",
            agent="invoice_processing",
            result={},
            elapsed_ms=100,
        )
        assert event["detail"] == "Extracting data from PDF using Textract..."

    def test_detail_for_validate_fields(self):
        event = build_step_event(
            step=2,
            step_name="validate_fields",
            agent="invoice_processing",
            result={},
            elapsed_ms=200,
        )
        assert event["detail"] == "Validating extracted fields..."

    def test_detail_for_validate_gst_compliance(self):
        event = build_step_event(
            step=3,
            step_name="validate_gst_compliance",
            agent="invoice_processing",
            result={},
            elapsed_ms=300,
        )
        assert event["detail"] == "Checking HSN codes and GST rates..."

    def test_detail_for_verify_gstn(self):
        event = build_step_event(
            step=4,
            step_name="verify_gstn",
            agent="invoice_processing",
            result={},
            elapsed_ms=400,
        )
        assert event["detail"] == "Verifying GSTIN against GST portal..."

    def test_detail_for_check_fraud(self):
        event = build_step_event(
            step=5,
            step_name="check_fraud",
            agent="invoice_processing",
            result={},
            elapsed_ms=500,
        )
        assert event["detail"] == "Running 5-layer fraud detection..."

    def test_detail_for_get_buyer_intel(self):
        event = build_step_event(
            step=6,
            step_name="get_buyer_intel",
            agent="invoice_processing",
            result={},
            elapsed_ms=600,
        )
        assert event["detail"] == "Analyzing buyer payment history..."

    def test_detail_for_get_credit_score(self):
        event = build_step_event(
            step=7,
            step_name="get_credit_score",
            agent="invoice_processing",
            result={},
            elapsed_ms=700,
        )
        assert event["detail"] == "Checking CIBIL credit score..."

    def test_detail_for_get_company_info(self):
        event = build_step_event(
            step=8,
            step_name="get_company_info",
            agent="invoice_processing",
            result={},
            elapsed_ms=800,
        )
        assert event["detail"] == "Fetching MCA company data..."

    def test_detail_for_calculate_risk(self):
        event = build_step_event(
            step=9,
            step_name="calculate_risk",
            agent="invoice_processing",
            result={},
            elapsed_ms=900,
        )
        assert event["detail"] == "Calculating multi-signal risk score..."

    def test_detail_for_generate_summary(self):
        event = build_step_event(
            step=10,
            step_name="generate_summary",
            agent="invoice_processing",
            result={},
            elapsed_ms=1000,
        )
        assert event["detail"] == "Generating invoice summary..."

    def test_detail_for_cross_validate_outputs(self):
        event = build_step_event(
            step=11,
            step_name="cross_validate_outputs",
            agent="underwriting",
            result={},
            elapsed_ms=1100,
        )
        assert event["detail"] == "Cross-validating all agent outputs..."

    def test_detail_for_underwriting_decision(self):
        event = build_step_event(
            step=12,
            step_name="underwriting_decision",
            agent="underwriting",
            result={},
            elapsed_ms=1200,
        )
        assert event["detail"] == "Making autonomous approval decision..."

    def test_detail_for_log_decision(self):
        event = build_step_event(
            step=13,
            step_name="log_decision",
            agent="underwriting",
            result={},
            elapsed_ms=1300,
        )
        assert event["detail"] == "Logging decision and reasoning trace..."

    def test_detail_for_mint_nft(self):
        event = build_step_event(
            step=14,
            step_name="mint_nft",
            agent="underwriting",
            result={},
            elapsed_ms=1400,
        )
        assert event["detail"] == "Minting ARC-69 NFT on Algorand testnet..."

    def test_detail_for_unknown_step_name_is_non_empty(self):
        """An unrecognized step_name must still produce a non-empty detail string."""
        event = build_step_event(
            step=3,
            step_name="unknown_tool_xyz",
            agent="invoice_processing",
            result={},
            elapsed_ms=300,
        )
        assert isinstance(event["detail"], str)
        assert len(event["detail"]) > 0

    def test_result_is_preserved_as_given(self):
        complex_result = {
            "field1": "value1",
            "nested": {"key": [1, 2, 3]},
            "flag": True,
        }
        event = build_step_event(
            step=5,
            step_name="check_fraud",
            agent="invoice_processing",
            result=complex_result,
            elapsed_ms=1500,
        )
        assert event["result"] == complex_result

    def test_does_not_mutate_result_dict(self):
        """build_step_event must not modify the passed-in result dict."""
        original = {"key": "value"}
        original_copy = dict(original)
        build_step_event(
            step=1,
            step_name="extract_invoice",
            agent="invoice_processing",
            result=original,
            elapsed_ms=100,
        )
        assert original == original_copy


# ---------------------------------------------------------------------------
# build_pipeline_complete_event
# ---------------------------------------------------------------------------


class TestBuildPipelineCompleteEvent:
    """Unit tests for build_pipeline_complete_event."""

    def test_returns_dict(self):
        event = build_pipeline_complete_event(
            invoice_id="inv_001",
            decision="approved",
            risk_score=85,
            reason="Auto-approved: meets Rule 2 criteria",
        )
        assert isinstance(event, dict)

    def test_type_is_pipeline_complete(self):
        event = build_pipeline_complete_event(
            invoice_id="inv_001",
            decision="approved",
            risk_score=85,
            reason="Auto-approved",
        )
        assert event["type"] == "pipeline_complete"

    def test_all_required_keys_present(self):
        event = build_pipeline_complete_event(
            invoice_id="inv_002",
            decision="rejected",
            risk_score=23,
            reason="High fraud risk",
        )
        required_keys = {
            "type",
            "decision",
            "risk_score",
            "reason",
            "nft_asset_id",
            "invoice_id",
        }
        assert required_keys.issubset(event.keys())

    def test_approved_decision_with_nft_asset_id(self):
        event = build_pipeline_complete_event(
            invoice_id="inv_003",
            decision="approved",
            risk_score=90,
            reason="Meets all criteria",
            nft_asset_id=987654321,
        )
        assert event["decision"] == "approved"
        assert event["risk_score"] == 90
        assert event["reason"] == "Meets all criteria"
        assert event["nft_asset_id"] == 987654321
        assert event["invoice_id"] == "inv_003"

    def test_rejected_decision_nft_asset_id_is_none(self):
        event = build_pipeline_complete_event(
            invoice_id="inv_004",
            decision="rejected",
            risk_score=15,
            reason="GSTIN verification failed",
        )
        assert event["nft_asset_id"] is None

    def test_nft_asset_id_defaults_to_none(self):
        """nft_asset_id should be None when not provided."""
        event = build_pipeline_complete_event(
            invoice_id="inv_005",
            decision="flagged_for_review",
            risk_score=55,
            reason="Manual review required",
        )
        assert event["nft_asset_id"] is None

    def test_flagged_for_review_decision(self):
        event = build_pipeline_complete_event(
            invoice_id="inv_006",
            decision="flagged_for_review",
            risk_score=48,
            reason="Borderline risk profile",
        )
        assert event["decision"] == "flagged_for_review"

    def test_invoice_id_is_preserved(self):
        invoice_id = "inv-uuid-1234-abcd-5678"
        event = build_pipeline_complete_event(
            invoice_id=invoice_id,
            decision="approved",
            risk_score=88,
            reason="Approved",
        )
        assert event["invoice_id"] == invoice_id

    def test_risk_score_boundary_zero(self):
        event = build_pipeline_complete_event(
            invoice_id="inv_007",
            decision="rejected",
            risk_score=0,
            reason="Catastrophic risk",
        )
        assert event["risk_score"] == 0

    def test_risk_score_boundary_100(self):
        event = build_pipeline_complete_event(
            invoice_id="inv_008",
            decision="approved",
            risk_score=100,
            reason="Perfect score",
            nft_asset_id=111222333,
        )
        assert event["risk_score"] == 100


# ---------------------------------------------------------------------------
# publish_step_event (async, mocked Redis)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
class TestPublishStepEvent:
    """Integration tests for publish_step_event -- Redis is mocked."""

    async def test_publish_step_event_calls_publish_event(self):
        mock_publish = AsyncMock(return_value=1)
        with patch("app.modules.agents.event_bridge.publish_event", mock_publish):
            result = await publish_step_event(
                invoice_id="inv_pub_001",
                step=1,
                step_name="extract_invoice",
                agent="invoice_processing",
                result={"pages": 2},
                elapsed_ms=1200,
            )
        mock_publish.assert_called_once()

    async def test_publish_step_event_passes_invoice_id(self):
        mock_publish = AsyncMock(return_value=1)
        with patch("app.modules.agents.event_bridge.publish_event", mock_publish):
            await publish_step_event(
                invoice_id="inv_pub_002",
                step=2,
                step_name="validate_fields",
                agent="invoice_processing",
                result={},
                elapsed_ms=500,
            )
        call_args = mock_publish.call_args
        assert (
            call_args[0][0] == "inv_pub_002"
            or call_args[1].get("invoice_id") == "inv_pub_002"
        )

    async def test_publish_step_event_passes_event_with_correct_type(self):
        mock_publish = AsyncMock(return_value=1)
        with patch("app.modules.agents.event_bridge.publish_event", mock_publish):
            await publish_step_event(
                invoice_id="inv_pub_003",
                step=3,
                step_name="validate_gst_compliance",
                agent="invoice_processing",
                result={},
                elapsed_ms=800,
            )
        call_args = mock_publish.call_args
        event_data = (
            call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("event_data")
        )
        assert event_data["type"] == "step_complete"

    async def test_publish_step_event_returns_subscriber_count(self):
        mock_publish = AsyncMock(return_value=3)
        with patch("app.modules.agents.event_bridge.publish_event", mock_publish):
            result = await publish_step_event(
                invoice_id="inv_pub_004",
                step=5,
                step_name="check_fraud",
                agent="invoice_processing",
                result={},
                elapsed_ms=2000,
            )
        assert result == 3

    async def test_publish_step_event_event_contains_step_number(self):
        mock_publish = AsyncMock(return_value=1)
        with patch("app.modules.agents.event_bridge.publish_event", mock_publish):
            await publish_step_event(
                invoice_id="inv_pub_005",
                step=7,
                step_name="get_credit_score",
                agent="invoice_processing",
                result={"score": 750},
                elapsed_ms=3000,
            )
        call_args = mock_publish.call_args
        event_data = (
            call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("event_data")
        )
        assert event_data["step"] == 7

    async def test_publish_step_event_event_contains_progress(self):
        mock_publish = AsyncMock(return_value=1)
        with patch("app.modules.agents.event_bridge.publish_event", mock_publish):
            await publish_step_event(
                invoice_id="inv_pub_006",
                step=14,
                step_name="mint_nft",
                agent="underwriting",
                result={},
                elapsed_ms=9000,
            )
        call_args = mock_publish.call_args
        event_data = (
            call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("event_data")
        )
        assert event_data["progress"] == 1.0


# ---------------------------------------------------------------------------
# publish_pipeline_complete (async, mocked Redis)
# ---------------------------------------------------------------------------


@pytest.mark.anyio
class TestPublishPipelineComplete:
    """Integration tests for publish_pipeline_complete -- Redis is mocked."""

    async def test_publish_pipeline_complete_calls_publish_event(self):
        mock_publish = AsyncMock(return_value=2)
        with patch("app.modules.agents.event_bridge.publish_event", mock_publish):
            result = await publish_pipeline_complete(
                invoice_id="inv_comp_001",
                decision="approved",
                risk_score=82,
                reason="Auto-approved: meets Rule 2 criteria",
                nft_asset_id=12345678,
            )
        mock_publish.assert_called_once()

    async def test_publish_pipeline_complete_passes_invoice_id(self):
        mock_publish = AsyncMock(return_value=1)
        with patch("app.modules.agents.event_bridge.publish_event", mock_publish):
            await publish_pipeline_complete(
                invoice_id="inv_comp_002",
                decision="rejected",
                risk_score=20,
                reason="High risk",
            )
        call_args = mock_publish.call_args
        assert (
            call_args[0][0] == "inv_comp_002"
            or call_args[1].get("invoice_id") == "inv_comp_002"
        )

    async def test_publish_pipeline_complete_event_type(self):
        mock_publish = AsyncMock(return_value=1)
        with patch("app.modules.agents.event_bridge.publish_event", mock_publish):
            await publish_pipeline_complete(
                invoice_id="inv_comp_003",
                decision="flagged_for_review",
                risk_score=55,
                reason="Manual review",
            )
        call_args = mock_publish.call_args
        event_data = (
            call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("event_data")
        )
        assert event_data["type"] == "pipeline_complete"

    async def test_publish_pipeline_complete_returns_subscriber_count(self):
        mock_publish = AsyncMock(return_value=5)
        with patch("app.modules.agents.event_bridge.publish_event", mock_publish):
            result = await publish_pipeline_complete(
                invoice_id="inv_comp_004",
                decision="approved",
                risk_score=90,
                reason="Approved",
                nft_asset_id=99999,
            )
        assert result == 5

    async def test_publish_pipeline_complete_nft_none_for_rejected(self):
        mock_publish = AsyncMock(return_value=1)
        with patch("app.modules.agents.event_bridge.publish_event", mock_publish):
            await publish_pipeline_complete(
                invoice_id="inv_comp_005",
                decision="rejected",
                risk_score=10,
                reason="Fraud detected",
            )
        call_args = mock_publish.call_args
        event_data = (
            call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("event_data")
        )
        assert event_data["nft_asset_id"] is None

    async def test_publish_pipeline_complete_decision_in_event(self):
        mock_publish = AsyncMock(return_value=1)
        with patch("app.modules.agents.event_bridge.publish_event", mock_publish):
            await publish_pipeline_complete(
                invoice_id="inv_comp_006",
                decision="approved",
                risk_score=88,
                reason="All clear",
                nft_asset_id=555666777,
            )
        call_args = mock_publish.call_args
        event_data = (
            call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("event_data")
        )
        assert event_data["decision"] == "approved"
        assert event_data["nft_asset_id"] == 555666777
        assert event_data["risk_score"] == 88
