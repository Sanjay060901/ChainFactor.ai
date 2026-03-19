# M2 Backend Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire existing agents, tools, and smart contract into an end-to-end invoice processing pipeline with DB persistence, WebSocket streaming, and real NFT endpoints.

**Architecture:** Direct tool invocation pipeline (no Strands Swarm in Phase 1 -- avoids Bedrock costs during development). Each of the 14 pipeline steps calls the tool's public function directly, persists the result to the invoice's JSONB column, and publishes a WebSocket event via Redis. Demo mode uses `_demo=True` overrides.

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy (async), Redis pub/sub, algosdk v2.11.1, pytest

**Spec:** `docs/superpowers/specs/2026-03-19-m2-backend-integration-design.md`

---

## File Structure

| File | Responsibility |
|------|---------------|
| `backend/app/modules/agents/event_bridge.py` | Map tool results to WebSocket events, publish to Redis |
| `backend/app/modules/agents/persistence.py` | Save tool results to invoice JSONB columns + agent traces |
| `backend/app/modules/agents/pipeline.py` | Orchestrate 14-step pipeline as background task |
| `backend/app/modules/invoices/router.py` | Update process/opt-in/claim endpoints (existing file) |
| `backend/app/schemas/invoice.py` | Add ProcessInvoiceResponse schema (existing file) |
| `backend/tests/test_event_bridge.py` | Event bridge unit tests |
| `backend/tests/test_persistence.py` | Persistence helper unit tests |
| `backend/tests/test_pipeline.py` | Pipeline runner integration tests |
| `backend/tests/test_process_endpoint.py` | Process endpoint API tests |
| `backend/tests/test_nft_optin.py` | NFT opt-in endpoint tests |
| `backend/tests/test_nft_claim.py` | NFT claim endpoint tests |

---

### Task 1: Event Bridge

**Files:**
- Create: `backend/app/modules/agents/event_bridge.py`
- Test: `backend/tests/test_event_bridge.py`

- [ ] **Step 1: Write failing tests for event bridge**

```python
# backend/tests/test_event_bridge.py
"""Tests for the event bridge -- maps tool results to WebSocket events."""

import pytest
from unittest.mock import AsyncMock, patch

from app.modules.agents.event_bridge import build_step_event, publish_step_event

TOTAL_STEPS = 14


class TestBuildStepEvent:
    """Unit tests for build_step_event."""

    def test_returns_dict(self):
        event = build_step_event(
            step=1,
            step_name="extract_invoice",
            agent="invoice_processing",
            result={"fields": 23},
            elapsed_ms=3200,
        )
        assert isinstance(event, dict)

    def test_has_required_keys(self):
        event = build_step_event(
            step=1,
            step_name="extract_invoice",
            agent="invoice_processing",
            result={},
            elapsed_ms=1000,
        )
        required = {"type", "step", "step_name", "agent", "status", "detail", "result", "progress", "elapsed_ms"}
        assert required.issubset(event.keys())

    def test_type_is_step_complete(self):
        event = build_step_event(step=1, step_name="extract_invoice", agent="invoice_processing", result={}, elapsed_ms=0)
        assert event["type"] == "step_complete"

    def test_progress_step_1(self):
        event = build_step_event(step=1, step_name="extract_invoice", agent="invoice_processing", result={}, elapsed_ms=0)
        assert event["progress"] == round(1 / TOTAL_STEPS, 2)

    def test_progress_step_14(self):
        event = build_step_event(step=14, step_name="mint_nft", agent="underwriting", result={}, elapsed_ms=0)
        assert event["progress"] == 1.0

    def test_status_defaults_to_complete(self):
        event = build_step_event(step=1, step_name="extract_invoice", agent="invoice_processing", result={}, elapsed_ms=0)
        assert event["status"] == "complete"

    def test_detail_is_human_readable(self):
        event = build_step_event(step=5, step_name="check_fraud", agent="invoice_processing", result={}, elapsed_ms=0)
        assert isinstance(event["detail"], str)
        assert len(event["detail"]) > 5


class TestBuildPipelineCompleteEvent:
    """Test the pipeline_complete event builder."""

    def test_returns_pipeline_complete(self):
        from app.modules.agents.event_bridge import build_pipeline_complete_event

        event = build_pipeline_complete_event(
            invoice_id="inv-001",
            decision="approved",
            risk_score=82,
            reason="Auto-approved",
            nft_asset_id=12345678,
        )
        assert event["type"] == "pipeline_complete"
        assert event["decision"] == "approved"
        assert event["invoice_id"] == "inv-001"

    def test_nft_asset_id_optional(self):
        from app.modules.agents.event_bridge import build_pipeline_complete_event

        event = build_pipeline_complete_event(
            invoice_id="inv-002",
            decision="rejected",
            risk_score=15,
            reason="Critical fraud detected",
        )
        assert event.get("nft_asset_id") is None


class TestPublishStepEvent:
    """Test that publish_step_event calls Redis correctly."""

    @pytest.mark.asyncio
    async def test_publishes_to_redis(self):
        with patch("app.modules.agents.event_bridge.publish_event", new_callable=AsyncMock) as mock_pub:
            mock_pub.return_value = 1
            await publish_step_event(
                invoice_id="inv-001",
                step=1,
                step_name="extract_invoice",
                agent="invoice_processing",
                result={"fields": 23},
                elapsed_ms=3200,
            )
            mock_pub.assert_called_once()
            args = mock_pub.call_args
            assert args[0][0] == "inv-001"
            assert args[0][1]["type"] == "step_complete"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_event_bridge.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.modules.agents.event_bridge'`

- [ ] **Step 3: Implement event bridge**

```python
# backend/app/modules/agents/event_bridge.py
"""Event bridge -- maps tool execution results to WebSocket events.

Publishes step_complete and pipeline_complete events to Redis pub/sub
using the existing redis_bridge module.
"""

from __future__ import annotations

from app.modules.ws.redis_bridge import publish_event

# Step details for human-readable descriptions
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

TOTAL_STEPS = 14


def build_step_event(
    *,
    step: int,
    step_name: str,
    agent: str,
    result: dict,
    elapsed_ms: int,
    status: str = "complete",
) -> dict:
    """Build a step_complete event matching the WebSocket schema."""
    return {
        "type": "step_complete",
        "step": step,
        "step_name": step_name,
        "agent": agent,
        "status": status,
        "detail": _STEP_DETAILS.get(step_name, f"Processing {step_name}..."),
        "result": result,
        "progress": round(step / TOTAL_STEPS, 2),
        "elapsed_ms": elapsed_ms,
    }


def build_pipeline_complete_event(
    *,
    invoice_id: str,
    decision: str,
    risk_score: int,
    reason: str,
    nft_asset_id: int | None = None,
) -> dict:
    """Build a pipeline_complete event."""
    return {
        "type": "pipeline_complete",
        "decision": decision,
        "risk_score": risk_score,
        "reason": reason,
        "nft_asset_id": nft_asset_id,
        "invoice_id": invoice_id,
    }


async def publish_step_event(
    *,
    invoice_id: str,
    step: int,
    step_name: str,
    agent: str,
    result: dict,
    elapsed_ms: int,
) -> int:
    """Build and publish a step_complete event to Redis."""
    event = build_step_event(
        step=step,
        step_name=step_name,
        agent=agent,
        result=result,
        elapsed_ms=elapsed_ms,
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
    """Build and publish a pipeline_complete event to Redis."""
    event = build_pipeline_complete_event(
        invoice_id=invoice_id,
        decision=decision,
        risk_score=risk_score,
        reason=reason,
        nft_asset_id=nft_asset_id,
    )
    return await publish_event(invoice_id, event)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_event_bridge.py -v`
Expected: All 10 tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/modules/agents/event_bridge.py backend/tests/test_event_bridge.py
git commit -m "feat: event bridge for WebSocket step events (M2 pipeline)"
```

---

### Task 2: DB Persistence Helper

**Files:**
- Create: `backend/app/modules/agents/persistence.py`
- Test: `backend/tests/test_persistence.py`

- [ ] **Step 1: Write failing tests**

```python
# backend/tests/test_persistence.py
"""Tests for pipeline DB persistence -- saving tool results and agent traces."""

import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.modules.agents.persistence import (
    STEP_TO_COLUMN,
    persist_tool_result,
    save_agent_trace,
)


class TestStepToColumnMapping:
    """Verify the mapping from step names to invoice model columns."""

    def test_all_10_invoice_steps_mapped(self):
        invoice_steps = [
            "extract_invoice", "validate_fields", "validate_gst_compliance",
            "verify_gstn", "check_fraud", "get_buyer_intel", "get_credit_score",
            "get_company_info", "calculate_risk", "generate_summary",
        ]
        for step in invoice_steps:
            assert step in STEP_TO_COLUMN, f"{step} not in STEP_TO_COLUMN"

    def test_extract_invoice_maps_to_extracted_data(self):
        assert STEP_TO_COLUMN["extract_invoice"] == "extracted_data"

    def test_calculate_risk_maps_to_risk_assessment(self):
        assert STEP_TO_COLUMN["calculate_risk"] == "risk_assessment"

    def test_generate_summary_maps_to_ai_explanation(self):
        assert STEP_TO_COLUMN["generate_summary"] == "ai_explanation"


class TestPersistToolResult:
    """Test persisting individual tool results to invoice JSONB columns."""

    @pytest.mark.asyncio
    async def test_sets_attribute_on_invoice(self):
        mock_invoice = MagicMock()
        mock_invoice.extracted_data = None
        mock_db = AsyncMock()

        await persist_tool_result(
            db=mock_db,
            invoice=mock_invoice,
            step_name="extract_invoice",
            result={"seller": {"name": "Acme"}},
        )
        assert mock_invoice.extracted_data == {"seller": {"name": "Acme"}}

    @pytest.mark.asyncio
    async def test_sets_risk_score_for_calculate_risk(self):
        mock_invoice = MagicMock()
        mock_invoice.risk_assessment = None
        mock_invoice.risk_score = None
        mock_db = AsyncMock()

        await persist_tool_result(
            db=mock_db,
            invoice=mock_invoice,
            step_name="calculate_risk",
            result={"score": 82, "level": "low", "explanation": "Low risk"},
        )
        assert mock_invoice.risk_assessment == {"score": 82, "level": "low", "explanation": "Low risk"}
        assert mock_invoice.risk_score == 82

    @pytest.mark.asyncio
    async def test_sets_ai_explanation_as_string(self):
        mock_invoice = MagicMock()
        mock_invoice.ai_explanation = None
        mock_db = AsyncMock()

        await persist_tool_result(
            db=mock_db,
            invoice=mock_invoice,
            step_name="generate_summary",
            result={"summary": "Invoice OK", "highlights": [], "recommendation": "approve"},
        )
        assert mock_invoice.ai_explanation == "Invoice OK"

    @pytest.mark.asyncio
    async def test_unknown_step_does_not_crash(self):
        mock_invoice = MagicMock()
        mock_db = AsyncMock()

        # Should not raise
        await persist_tool_result(
            db=mock_db,
            invoice=mock_invoice,
            step_name="unknown_step",
            result={"data": "whatever"},
        )

    @pytest.mark.asyncio
    async def test_commits_after_persist(self):
        mock_invoice = MagicMock()
        mock_db = AsyncMock()

        await persist_tool_result(
            db=mock_db,
            invoice=mock_invoice,
            step_name="extract_invoice",
            result={},
        )
        mock_db.commit.assert_awaited_once()


class TestSaveAgentTrace:
    """Test saving agent trace records."""

    @pytest.mark.asyncio
    async def test_adds_trace_to_session(self):
        mock_db = AsyncMock()
        invoice_id = uuid.uuid4()

        await save_agent_trace(
            db=mock_db,
            invoice_id=invoice_id,
            agent_name="invoice_processing_agent",
            model="us.anthropic.claude-sonnet-4-6-v1",
            duration_ms=45000,
            steps=[{"step_number": 1, "tool_name": "extract_invoice", "status": "complete"}],
            handoff_context={"risk_score": 82},
        )
        mock_db.add.assert_called_once()
        mock_db.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_trace_has_correct_fields(self):
        mock_db = AsyncMock()
        invoice_id = uuid.uuid4()

        # Capture the object passed to db.add
        added_objects = []
        mock_db.add.side_effect = lambda obj: added_objects.append(obj)

        await save_agent_trace(
            db=mock_db,
            invoice_id=invoice_id,
            agent_name="underwriting_agent",
            model="us.anthropic.claude-sonnet-4-6-v1",
            duration_ms=30000,
            steps=[],
            handoff_context=None,
        )
        trace = added_objects[0]
        assert trace.agent_name == "underwriting_agent"
        assert trace.duration_ms == 30000
        assert trace.invoice_id == invoice_id
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_persistence.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement persistence helper**

```python
# backend/app/modules/agents/persistence.py
"""DB persistence for pipeline tool results and agent traces.

Each tool result is persisted to the corresponding JSONB column on the
Invoice model. Agent traces are saved as separate AgentTrace records.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_trace import AgentTrace

logger = logging.getLogger(__name__)

# Maps pipeline step names to Invoice model column names.
STEP_TO_COLUMN: dict[str, str] = {
    "extract_invoice": "extracted_data",
    "validate_fields": "validation_result",
    "validate_gst_compliance": "gst_compliance",
    "verify_gstn": "gstin_verification",
    "check_fraud": "fraud_detection",
    "get_buyer_intel": "buyer_intel",
    "get_credit_score": "credit_score",
    "get_company_info": "company_info",
    "calculate_risk": "risk_assessment",
    "generate_summary": "ai_explanation",
}


async def persist_tool_result(
    *,
    db: AsyncSession,
    invoice: Any,
    step_name: str,
    result: dict,
) -> None:
    """Persist a single tool result to the invoice model.

    Special cases:
      - calculate_risk: also sets invoice.risk_score (denormalized int)
      - generate_summary: stores result["summary"] as text in ai_explanation
    """
    column = STEP_TO_COLUMN.get(step_name)
    if column is None:
        logger.warning("No column mapping for step %s, skipping persist", step_name)
        await db.commit()
        return

    if step_name == "generate_summary":
        setattr(invoice, column, result.get("summary", ""))
    else:
        setattr(invoice, column, result)

    # Denormalize risk_score for fast queries
    if step_name == "calculate_risk" and "score" in result:
        invoice.risk_score = result["score"]

    await db.commit()


async def save_agent_trace(
    *,
    db: AsyncSession,
    invoice_id: uuid.UUID,
    agent_name: str,
    model: str,
    duration_ms: int,
    steps: list[dict],
    handoff_context: dict | None = None,
) -> AgentTrace:
    """Save an agent execution trace to the database."""
    trace = AgentTrace(
        invoice_id=invoice_id,
        agent_name=agent_name,
        model=model,
        duration_ms=duration_ms,
        steps=steps,
        handoff_context=handoff_context,
    )
    db.add(trace)
    await db.commit()
    return trace
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_persistence.py -v`
Expected: All 9 tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/modules/agents/persistence.py backend/tests/test_persistence.py
git commit -m "feat: DB persistence helper for pipeline tool results (M2)"
```

---

### Task 3: Pipeline Runner

**Files:**
- Create: `backend/app/modules/agents/pipeline.py`
- Test: `backend/tests/test_pipeline.py`

This is the core orchestrator. It calls each tool's public function directly (not via Strands Agent), persists results, and publishes events.

- [ ] **Step 1: Write failing tests for pipeline step definitions**

```python
# backend/tests/test_pipeline.py
"""Tests for the invoice processing pipeline runner."""

import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from datetime import datetime, timezone

from app.modules.agents.pipeline import (
    PIPELINE_STEPS,
    run_invoice_pipeline,
)


class TestPipelineStepDefinitions:
    """Verify pipeline step configuration."""

    def test_has_14_steps(self):
        assert len(PIPELINE_STEPS) == 14

    def test_steps_numbered_1_to_14(self):
        step_nums = [s["step"] for s in PIPELINE_STEPS]
        assert step_nums == list(range(1, 15))

    def test_first_step_is_extract_invoice(self):
        assert PIPELINE_STEPS[0]["step_name"] == "extract_invoice"

    def test_last_step_is_mint_nft(self):
        assert PIPELINE_STEPS[-1]["step_name"] == "mint_nft"

    def test_steps_1_to_10_are_invoice_processing(self):
        for s in PIPELINE_STEPS[:10]:
            assert s["agent"] == "invoice_processing", f"Step {s['step']} wrong agent"

    def test_steps_11_to_13_are_underwriting(self):
        for s in PIPELINE_STEPS[10:13]:
            assert s["agent"] == "underwriting", f"Step {s['step']} wrong agent"

    def test_step_14_mint_nft_agent(self):
        assert PIPELINE_STEPS[13]["agent"] == "invoice_processing"

    def test_each_step_has_required_keys(self):
        for s in PIPELINE_STEPS:
            assert "step" in s
            assert "step_name" in s
            assert "agent" in s


class TestRunInvoicePipeline:
    """Integration tests for the full pipeline execution."""

    def _mock_invoice(self):
        inv = MagicMock()
        inv.id = uuid.uuid4()
        inv.file_key = "invoices/user1/inv1/test.pdf"
        inv.user_id = uuid.uuid4()
        inv.status = "uploaded"
        inv.extracted_data = None
        inv.validation_result = None
        inv.gst_compliance = None
        inv.gstin_verification = None
        inv.fraud_detection = None
        inv.buyer_intel = None
        inv.credit_score = None
        inv.company_info = None
        inv.risk_assessment = None
        inv.risk_score = None
        inv.ai_explanation = None
        inv.underwriting = None
        inv.processing_started_at = None
        inv.processing_completed_at = None
        inv.processing_duration_ms = None
        return inv

    @pytest.mark.asyncio
    async def test_sets_status_to_processing(self):
        mock_db = AsyncMock()
        inv = self._mock_invoice()

        with patch("app.modules.agents.pipeline._execute_step", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = {}
            with patch("app.modules.agents.pipeline.persist_tool_result", new_callable=AsyncMock):
                with patch("app.modules.agents.pipeline.publish_step_event", new_callable=AsyncMock):
                    with patch("app.modules.agents.pipeline.publish_pipeline_complete", new_callable=AsyncMock):
                        with patch("app.modules.agents.pipeline.save_agent_trace", new_callable=AsyncMock):
                            await run_invoice_pipeline(invoice=inv, db=mock_db)

        # Status should have been set to processing at the start
        # (then updated to approved/rejected/flagged at the end)
        assert inv.status in ("approved", "rejected", "flagged")

    @pytest.mark.asyncio
    async def test_calls_all_14_steps(self):
        mock_db = AsyncMock()
        inv = self._mock_invoice()

        call_log = []

        async def fake_execute(step_name, **kwargs):
            call_log.append(step_name)
            if step_name == "extract_invoice":
                return {"seller": {"name": "Acme", "gstin": "27AABCA1234R1ZM"}, "buyer": {"name": "Beta", "gstin": "29AABCB5678R1ZX"}, "invoice_number": "INV-001", "invoice_date": "2026-03-15", "due_date": "2026-04-14", "subtotal": 100000, "tax_amount": 18000, "tax_rate": 18, "total_amount": 118000, "line_items": []}
            if step_name == "validate_fields":
                return {"is_valid": True, "errors": [], "warnings": []}
            if step_name == "validate_gst_compliance":
                return {"is_compliant": True, "details": {}}
            if step_name == "verify_gstn":
                return {"verified": True, "status": "active", "details": {}}
            if step_name == "check_fraud":
                return {"overall": "pass", "confidence": 95, "flags": [], "layers": []}
            if step_name == "get_buyer_intel":
                return {"payment_history": "reliable", "avg_days": 28, "previous_count": 8}
            if step_name == "get_credit_score":
                return {"score": 750, "rating": "good"}
            if step_name == "get_company_info":
                return {"status": "active", "incorporated": "2015", "paid_up_capital": 100000000}
            if step_name == "calculate_risk":
                return {"score": 82, "level": "low", "explanation": "Low risk"}
            if step_name == "generate_summary":
                return {"summary": "OK", "highlights": [], "recommendation": "approve"}
            if step_name == "cross_validate_outputs":
                return {"consistent": True, "discrepancies": [], "confidence": 0.95}
            if step_name == "underwriting_decision":
                return {"decision": "approved", "invoice_id": str(inv.id), "reason": "Low risk", "risk_score": 82, "confidence": 0.95, "timestamp": "2026-03-19T10:00:00Z"}
            if step_name == "log_decision":
                return {"logged": True, "trace_id": "abc-123", "timestamp": "2026-03-19T10:00:00Z"}
            if step_name == "mint_nft":
                return {"asset_id": 123456789, "txn_id": "DEMO_TXN", "explorer_url": "https://testnet.explorer.perawallet.app/asset/123456789/", "metadata": {}}
            return {}

        with patch("app.modules.agents.pipeline._execute_step", side_effect=fake_execute):
            with patch("app.modules.agents.pipeline.persist_tool_result", new_callable=AsyncMock):
                with patch("app.modules.agents.pipeline.publish_step_event", new_callable=AsyncMock):
                    with patch("app.modules.agents.pipeline.publish_pipeline_complete", new_callable=AsyncMock):
                        with patch("app.modules.agents.pipeline.save_agent_trace", new_callable=AsyncMock):
                            await run_invoice_pipeline(invoice=inv, db=mock_db)

        assert len(call_log) == 14

    @pytest.mark.asyncio
    async def test_skips_mint_nft_on_rejection(self):
        mock_db = AsyncMock()
        inv = self._mock_invoice()

        call_log = []

        async def fake_execute(step_name, **kwargs):
            call_log.append(step_name)
            if step_name == "underwriting_decision":
                return {"decision": "rejected", "invoice_id": str(inv.id), "reason": "Fraud", "risk_score": 10, "fraud_flags": ["critical"], "timestamp": "2026-03-19T10:00:00Z"}
            if step_name == "calculate_risk":
                return {"score": 10, "level": "critical", "explanation": "Critical risk"}
            if step_name == "check_fraud":
                return {"overall": "fail", "confidence": 90, "flags": ["critical"], "layers": []}
            if step_name == "generate_summary":
                return {"summary": "High risk", "highlights": ["fraud"], "recommendation": "reject"}
            if step_name == "cross_validate_outputs":
                return {"consistent": True, "discrepancies": [], "confidence": 0.9}
            if step_name == "log_decision":
                return {"logged": True, "trace_id": "def-456", "timestamp": "2026-03-19T10:00:00Z"}
            return {"is_valid": True, "errors": [], "warnings": [], "is_compliant": True, "details": {}, "verified": True, "status": "active", "payment_history": "reliable", "avg_days": 28, "previous_count": 8, "score": 450, "rating": "poor", "incorporated": "2015", "paid_up_capital": 100000000, "seller": {"name": "A", "gstin": "27AABCA1234R1ZM"}, "buyer": {"name": "B", "gstin": "29AABCB5678R1ZX"}, "invoice_number": "INV-001", "invoice_date": "2026-03-15", "due_date": "2026-04-14", "subtotal": 100000, "tax_amount": 18000, "tax_rate": 18, "total_amount": 118000, "line_items": []}

        with patch("app.modules.agents.pipeline._execute_step", side_effect=fake_execute):
            with patch("app.modules.agents.pipeline.persist_tool_result", new_callable=AsyncMock):
                with patch("app.modules.agents.pipeline.publish_step_event", new_callable=AsyncMock):
                    with patch("app.modules.agents.pipeline.publish_pipeline_complete", new_callable=AsyncMock):
                        with patch("app.modules.agents.pipeline.save_agent_trace", new_callable=AsyncMock):
                            await run_invoice_pipeline(invoice=inv, db=mock_db)

        assert "mint_nft" not in call_log
        assert inv.status == "rejected"

    @pytest.mark.asyncio
    async def test_sets_failed_on_exception(self):
        mock_db = AsyncMock()
        inv = self._mock_invoice()

        async def failing_execute(step_name, **kwargs):
            if step_name == "extract_invoice":
                raise RuntimeError("Textract exploded")
            return {}

        with patch("app.modules.agents.pipeline._execute_step", side_effect=failing_execute):
            with patch("app.modules.agents.pipeline.persist_tool_result", new_callable=AsyncMock):
                with patch("app.modules.agents.pipeline.publish_step_event", new_callable=AsyncMock):
                    with patch("app.modules.agents.pipeline.publish_pipeline_complete", new_callable=AsyncMock):
                        with patch("app.modules.agents.pipeline.save_agent_trace", new_callable=AsyncMock):
                            await run_invoice_pipeline(invoice=inv, db=mock_db)

        assert inv.status == "failed"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && python -m pytest tests/test_pipeline.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement pipeline runner**

```python
# backend/app/modules/agents/pipeline.py
"""Invoice processing pipeline runner.

Orchestrates the 14-step pipeline: calls each tool's public function,
persists results to DB, and publishes WebSocket events.

Phase 1: Direct tool invocation (no Strands Agent/Swarm).
Phase 2: Swap to Strands Swarm.stream_async() with hook-based event bridge.
"""

from __future__ import annotations

import logging
import time
import uuid
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
# Pipeline step definitions
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


# ---------------------------------------------------------------------------
# Tool dispatch
# ---------------------------------------------------------------------------


async def _execute_step(step_name: str, **context: Any) -> dict:
    """Dispatch a pipeline step to the appropriate tool function.

    All tool imports are local to avoid circular imports and to keep the
    module testable (tests patch this function).
    """
    from app.agents.tools.extract_invoice import extract_invoice
    from app.agents.tools.validate_fields import validate_fields
    from app.agents.tools.validate_gst_compliance import validate_gst_compliance
    from app.agents.tools.verify_gstn import verify_gstn
    from app.agents.tools.check_fraud import check_fraud
    from app.agents.tools.get_buyer_intel import get_buyer_intel
    from app.agents.tools.get_credit_score import get_credit_score
    from app.agents.tools.get_company_info import get_company_info
    from app.agents.tools.calculate_risk import calculate_risk
    from app.agents.tools.generate_summary import generate_summary
    from app.agents.tools.mint_nft import mint_nft
    from app.agents.tools.cross_validate_outputs import cross_validate_outputs
    from app.agents.tools.get_seller_rules import get_seller_rules
    from app.agents.tools.approve_invoice import approve_invoice
    from app.agents.tools.reject_invoice import reject_invoice
    from app.agents.tools.flag_for_review import flag_for_review
    from app.agents.tools.log_decision import log_decision

    extracted = context.get("extracted_data", {})
    validation = context.get("validation_result", {})
    fraud = context.get("fraud_result", {})
    gst = context.get("gst_compliance", {})
    gstin = context.get("gstin_verification", {})
    buyer = context.get("buyer_intel", {})
    credit = context.get("credit_score", {})
    company = context.get("company_info", {})
    risk = context.get("risk_assessment", {})
    summary = context.get("summary_result", {})
    cross_val = context.get("cross_validation", {})
    invoice_id = context.get("invoice_id", "")
    file_key = context.get("file_key", "")
    seller_id = context.get("seller_id", "")

    if step_name == "extract_invoice":
        return extract_invoice(s3_file_key=file_key, bucket_name="chainfactor-invoices")
    if step_name == "validate_fields":
        return validate_fields(extracted_data=extracted)
    if step_name == "validate_gst_compliance":
        return validate_gst_compliance(extracted_data=extracted)
    if step_name == "verify_gstn":
        seller_gstin = extracted.get("seller", {}).get("gstin", "")
        buyer_gstin = extracted.get("buyer", {}).get("gstin", "")
        return verify_gstn(seller_gstin=seller_gstin, buyer_gstin=buyer_gstin)
    if step_name == "check_fraud":
        return check_fraud(extracted_data=extracted, gstin_verification=gstin)
    if step_name == "get_buyer_intel":
        buyer_gstin = extracted.get("buyer", {}).get("gstin", "")
        return get_buyer_intel(buyer_gstin=buyer_gstin)
    if step_name == "get_credit_score":
        buyer_gstin = extracted.get("buyer", {}).get("gstin", "")
        return get_credit_score(buyer_gstin=buyer_gstin)
    if step_name == "get_company_info":
        buyer_gstin = extracted.get("buyer", {}).get("gstin", "")
        return get_company_info(company_gstin=buyer_gstin)
    if step_name == "calculate_risk":
        return calculate_risk(
            extracted_data=extracted,
            validation_result=validation,
            fraud_result=fraud,
            gst_compliance=gst,
            buyer_intel=buyer,
            credit_score=credit,
            company_info=company,
        )
    if step_name == "generate_summary":
        return generate_summary(
            extracted_data=extracted,
            validation_result=validation,
            fraud_result=fraud,
            gst_compliance=gst,
            gstin_verification=gstin,
            buyer_intel=buyer,
            credit_score=credit,
            company_info=company,
            risk_assessment=risk,
        )
    if step_name == "cross_validate_outputs":
        return cross_validate_outputs(
            extracted_data=extracted,
            validation_result=validation,
            fraud_result=fraud,
            gst_compliance=gst,
            gstin_verification=gstin,
            buyer_intel=buyer,
            credit_score=credit,
            company_info=company,
            risk_assessment=risk,
        )
    if step_name == "underwriting_decision":
        # Decide based on risk + summary recommendation
        recommendation = summary.get("recommendation", "review")
        fraud_flags = fraud.get("flags", [])
        risk_score = risk.get("score", 0)
        confidence = cross_val.get("confidence", 0.0)

        if recommendation == "reject" or risk.get("level") == "critical":
            return reject_invoice(
                invoice_id=invoice_id,
                reason=f"Risk level: {risk.get('level', 'unknown')}. {summary.get('summary', '')}",
                risk_score=risk_score,
                fraud_flags=fraud_flags,
            )
        if recommendation == "review" or not cross_val.get("consistent", True):
            discrepancies = cross_val.get("discrepancies", [])
            return flag_for_review(
                invoice_id=invoice_id,
                reason=f"Requires manual review. {summary.get('summary', '')}",
                discrepancies=discrepancies,
                risk_score=risk_score,
            )
        return approve_invoice(
            invoice_id=invoice_id,
            reason=f"Auto-approved. {summary.get('summary', '')}",
            risk_score=risk_score,
            confidence=confidence,
        )
    if step_name == "log_decision":
        decision_result = context.get("decision_result", {})
        return log_decision(
            invoice_id=invoice_id,
            decision=decision_result.get("decision", "unknown"),
            reasoning_trace=decision_result.get("reason", ""),
            all_signals={
                "risk": risk,
                "fraud": fraud,
                "cross_validation": cross_val,
                "summary": summary,
            },
        )
    if step_name == "mint_nft":
        return mint_nft(
            invoice_id=invoice_id,
            extracted_data=extracted,
            risk_assessment=risk,
        )

    raise ValueError(f"Unknown pipeline step: {step_name}")


# ---------------------------------------------------------------------------
# Pipeline runner
# ---------------------------------------------------------------------------


async def run_invoice_pipeline(
    *,
    invoice: Any,
    db: AsyncSession,
) -> None:
    """Execute the full 14-step invoice processing pipeline.

    Updates invoice status, persists each tool result, publishes WebSocket
    events, and saves agent traces. On failure, sets status=failed.
    """
    invoice_id = str(invoice.id)
    pipeline_start = time.monotonic()
    trace_steps: list[dict] = []

    # Context accumulator -- each tool result feeds into subsequent tools
    ctx: dict[str, Any] = {
        "invoice_id": invoice_id,
        "file_key": invoice.file_key,
        "seller_id": str(invoice.user_id),
    }

    try:
        invoice.status = "processing"
        invoice.processing_started_at = datetime.now(timezone.utc)
        await db.commit()

        decision_result: dict = {}

        for step_def in PIPELINE_STEPS:
            step_num = step_def["step"]
            step_name = step_def["step_name"]
            agent = step_def["agent"]

            # Skip mint_nft if not approved
            if step_name == "mint_nft" and decision_result.get("decision") != "approved":
                continue

            step_start = time.monotonic()
            result = await _execute_step(step_name, **ctx)
            elapsed_ms = int((time.monotonic() - step_start) * 1000)

            # Track for agent trace
            trace_steps.append({
                "step_number": step_num,
                "tool_name": step_name,
                "duration_ms": elapsed_ms,
                "status": "complete",
                "result_summary": _summarize(result),
            })

            # Persist to DB
            await persist_tool_result(
                db=db, invoice=invoice, step_name=step_name, result=result,
            )

            # Publish WebSocket event
            await publish_step_event(
                invoice_id=invoice_id,
                step=step_num,
                step_name=step_name,
                agent=agent,
                result=result,
                elapsed_ms=elapsed_ms,
            )

            # Accumulate context for downstream tools
            _accumulate_context(ctx, step_name, result)

            # Capture decision for mint_nft gate
            if step_name == "underwriting_decision":
                decision_result = result
                ctx["decision_result"] = result

        # Final status
        decision = decision_result.get("decision", "flagged")
        status_map = {"approved": "approved", "rejected": "rejected"}
        invoice.status = status_map.get(decision, "flagged")
        invoice.processing_completed_at = datetime.now(timezone.utc)
        invoice.processing_duration_ms = int(
            (time.monotonic() - pipeline_start) * 1000
        )

        # Persist underwriting decision to JSONB
        if decision_result:
            invoice.underwriting = {
                "decision": decision_result.get("decision"),
                "reason": decision_result.get("reason", ""),
                "confidence": decision_result.get("confidence"),
                "cross_validation": ctx.get("cross_validation", {}).get("consistent"),
            }

        await db.commit()

        # Save agent trace
        total_ms = int((time.monotonic() - pipeline_start) * 1000)
        await save_agent_trace(
            db=db,
            invoice_id=invoice.id,
            agent_name="pipeline_runner",
            model=SONNET_MODEL_ID,
            duration_ms=total_ms,
            steps=trace_steps,
            handoff_context=None,
        )

        # Publish pipeline complete
        nft_asset_id = ctx.get("mint_nft_result", {}).get("asset_id")
        await publish_pipeline_complete(
            invoice_id=invoice_id,
            decision=decision,
            risk_score=ctx.get("risk_assessment", {}).get("score", 0),
            reason=decision_result.get("reason", ""),
            nft_asset_id=nft_asset_id,
        )

    except Exception:
        logger.exception("Pipeline failed for invoice %s", invoice_id)
        invoice.status = "failed"
        invoice.processing_completed_at = datetime.now(timezone.utc)
        invoice.processing_duration_ms = int(
            (time.monotonic() - pipeline_start) * 1000
        )
        await db.commit()


def _accumulate_context(ctx: dict, step_name: str, result: dict) -> None:
    """Add tool result to the running context for downstream tools."""
    mapping = {
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
    key = mapping.get(step_name)
    if key:
        ctx[key] = result


def _summarize(result: dict) -> str:
    """Create a brief summary of a tool result for the trace log."""
    if "decision" in result:
        return f"Decision: {result['decision']}"
    if "score" in result:
        return f"Score: {result['score']}"
    if "overall" in result:
        return f"Overall: {result['overall']}"
    if "is_valid" in result:
        return f"Valid: {result['is_valid']}"
    if "is_compliant" in result:
        return f"Compliant: {result['is_compliant']}"
    if "verified" in result:
        return f"Verified: {result['verified']}"
    if "asset_id" in result:
        return f"NFT: {result['asset_id']}"
    return str(result)[:100]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_pipeline.py -v`
Expected: All 8 tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/modules/agents/pipeline.py backend/tests/test_pipeline.py
git commit -m "feat: pipeline runner orchestrating 14-step invoice processing (M2)"
```

---

### Task 4: Process Endpoint

**Files:**
- Modify: `backend/app/modules/invoices/router.py` (add process endpoint)
- Modify: `backend/app/schemas/invoice.py` (add ProcessInvoiceResponse)
- Test: `backend/tests/test_process_endpoint.py`

- [ ] **Step 1: Add ProcessInvoiceResponse schema**

Add to `backend/app/schemas/invoice.py`:
```python
class ProcessInvoiceResponse(BaseModel):
    invoice_id: str
    status: str
    ws_url: str
```

- [ ] **Step 2: Write failing tests**

```python
# backend/tests/test_process_endpoint.py
"""Tests for POST /invoices/{id}/process endpoint."""

import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = uuid.uuid4()
    user.wallet_address = "A" * 58
    return user


@pytest.fixture
def mock_invoice(mock_user):
    inv = MagicMock()
    inv.id = uuid.uuid4()
    inv.user_id = mock_user.id
    inv.status = "uploaded"
    inv.file_key = "invoices/user/inv/test.pdf"
    return inv


class TestProcessEndpoint:
    """Test the process invoice endpoint."""

    @pytest.mark.asyncio
    async def test_returns_202_with_ws_url(self, mock_user, mock_invoice):
        with patch("app.modules.invoices.router.get_current_user", return_value=mock_user):
            with patch("app.modules.invoices.router.get_db") as mock_get_db:
                mock_db = AsyncMock()
                mock_get_db.return_value = mock_db

                with patch("app.modules.invoices.router._get_invoice_for_user", new_callable=AsyncMock) as mock_get:
                    mock_get.return_value = mock_invoice

                    with patch("app.modules.invoices.router.asyncio") as mock_asyncio:
                        transport = ASGITransport(app=app)
                        async with AsyncClient(transport=transport, base_url="http://test") as client:
                            resp = await client.post(f"/invoices/{mock_invoice.id}/process")

                        assert resp.status_code == 202

    @pytest.mark.asyncio
    async def test_rejects_already_processing(self, mock_user, mock_invoice):
        mock_invoice.status = "processing"

        with patch("app.modules.invoices.router.get_current_user", return_value=mock_user):
            with patch("app.modules.invoices.router.get_db") as mock_get_db:
                mock_db = AsyncMock()
                mock_get_db.return_value = mock_db

                with patch("app.modules.invoices.router._get_invoice_for_user", new_callable=AsyncMock) as mock_get:
                    mock_get.return_value = mock_invoice

                    transport = ASGITransport(app=app)
                    async with AsyncClient(transport=transport, base_url="http://test") as client:
                        resp = await client.post(f"/invoices/{mock_invoice.id}/process")

                    assert resp.status_code == 409
```

- [ ] **Step 3: Implement process endpoint**

Add to `backend/app/modules/invoices/router.py`:

```python
import asyncio
from fastapi import BackgroundTasks, HTTPException

from app.modules.agents.pipeline import run_invoice_pipeline
from app.schemas.invoice import ProcessInvoiceResponse


async def _get_invoice_for_user(
    db: AsyncSession, invoice_id: str, user_id: uuid.UUID
) -> Any:
    """Load invoice, verify ownership (IDOR prevention)."""
    from sqlalchemy import select
    from app.models.invoice import Invoice

    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id, Invoice.user_id == user_id)
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.post("/{invoice_id}/process", response_model=ProcessInvoiceResponse, status_code=202)
async def process_invoice(
    invoice_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger AI pipeline processing for an uploaded invoice."""
    invoice = await _get_invoice_for_user(db, invoice_id, current_user.id)

    if invoice.status != "uploaded":
        raise HTTPException(
            status_code=409,
            detail=f"Invoice cannot be processed (current status: {invoice.status})",
        )

    # Launch pipeline as background task
    asyncio.create_task(run_invoice_pipeline(invoice=invoice, db=db))

    return ProcessInvoiceResponse(
        invoice_id=str(invoice.id),
        status="processing",
        ws_url=f"/ws/processing/{invoice.id}",
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_process_endpoint.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/modules/invoices/router.py backend/app/schemas/invoice.py backend/tests/test_process_endpoint.py
git commit -m "feat: POST /invoices/{id}/process triggers pipeline (M2)"
```

---

### Task 5: NFT Opt-In Endpoint

**Files:**
- Modify: `backend/app/modules/invoices/router.py`
- Modify: `backend/app/schemas/invoice.py`
- Test: `backend/tests/test_nft_optin.py`

- [ ] **Step 1: Update schemas for opt-in flow**

Update `NFTOptInRequest` and `NFTOptInResponse` in `backend/app/schemas/invoice.py`:

```python
class NFTOptInRequest(BaseModel):
    wallet_address: str


class NFTOptInResponse(BaseModel):
    unsigned_txn: str  # base64-encoded unsigned AssetTransferTxn
    asset_id: int
    message: str
```

- [ ] **Step 2: Write failing tests**

```python
# backend/tests/test_nft_optin.py
"""Tests for NFT opt-in endpoint."""

import pytest
from unittest.mock import MagicMock, patch

from app.modules.invoices.nft_service import build_optin_txn


class TestBuildOptinTxn:
    """Test unsigned opt-in transaction builder."""

    def test_returns_base64_string(self):
        with patch("app.modules.invoices.nft_service.algosdk") as mock_sdk:
            mock_txn = MagicMock()
            mock_txn.dictify.return_value = b"txn_bytes"
            mock_sdk.transaction.AssetTransferTxn.return_value = mock_txn
            mock_sdk.transaction.get_suggested_params.return_value = MagicMock()
            mock_sdk.encoding.msgpack_encode.return_value = b"encoded"

            import base64
            with patch("base64.b64encode", return_value=b"dHhuX2J5dGVz"):
                result = build_optin_txn(
                    wallet_address="A" * 58,
                    asset_id=123456789,
                )
                assert isinstance(result, str)

    def test_txn_is_zero_amount_self_transfer(self):
        with patch("app.modules.invoices.nft_service.algosdk") as mock_sdk:
            mock_sdk.transaction.get_suggested_params.return_value = MagicMock()
            mock_txn = MagicMock()
            mock_sdk.transaction.AssetTransferTxn.return_value = mock_txn
            mock_sdk.encoding.msgpack_encode.return_value = b"x"

            build_optin_txn(wallet_address="A" * 58, asset_id=123456789)

            call_kwargs = mock_sdk.transaction.AssetTransferTxn.call_args
            # sender == receiver (self-transfer for opt-in)
            assert call_kwargs.kwargs.get("sender") == call_kwargs.kwargs.get("receiver")
            # amount == 0
            assert call_kwargs.kwargs.get("amt") == 0
```

- [ ] **Step 3: Create NFT service and update endpoint**

Create `backend/app/modules/invoices/nft_service.py`:

```python
"""NFT service -- builds Algorand transactions for opt-in and claim flows."""

from __future__ import annotations

import base64
import logging

import algosdk
from algosdk.v2client.algod import AlgodClient

from app.config import settings

logger = logging.getLogger(__name__)


def _get_algod_client() -> AlgodClient:
    return AlgodClient("", settings.ALGORAND_ALGOD_URL)


def build_optin_txn(*, wallet_address: str, asset_id: int) -> str:
    """Build an unsigned ASA opt-in transaction (base64-encoded).

    Opt-in = 0-amount AssetTransferTxn where sender == receiver.
    """
    client = _get_algod_client()
    params = client.suggested_params()

    txn = algosdk.transaction.AssetTransferTxn(
        sender=wallet_address,
        receiver=wallet_address,
        amt=0,
        index=asset_id,
        sp=params,
    )

    encoded = algosdk.encoding.msgpack_encode(txn)
    return base64.b64encode(encoded.encode() if isinstance(encoded, str) else encoded).decode()


def transfer_nft(*, asset_id: int, receiver_address: str) -> dict:
    """Transfer ASA from application wallet to user wallet.

    The app wallet must be the clawback address on the ASA.
    """
    client = _get_algod_client()
    params = client.suggested_params()

    private_key = algosdk.mnemonic.to_private_key(settings.ALGORAND_APP_WALLET_MNEMONIC)
    sender = algosdk.account.address_from_private_key(private_key)

    txn = algosdk.transaction.AssetTransferTxn(
        sender=sender,
        receiver=receiver_address,
        amt=1,
        index=asset_id,
        sp=params,
    )

    signed_txn = txn.sign(private_key)
    txid = client.send_transaction(signed_txn)
    result = algosdk.transaction.wait_for_confirmation(client, txid, 4)

    return {
        "txn_id": txid,
        "asset_id": asset_id,
        "confirmed_round": result.get("confirmed-round", 0),
    }
```

Update opt-in endpoint in `router.py`:

```python
@router.post("/{invoice_id}/nft/opt-in", response_model=NFTOptInResponse)
async def nft_opt_in(
    invoice_id: str,
    body: NFTOptInRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return unsigned ASA opt-in transaction for the user to sign."""
    invoice = await _get_invoice_for_user(db, invoice_id, current_user.id)

    if invoice.status != "approved":
        raise HTTPException(status_code=409, detail="Invoice must be approved before opt-in")

    nft = invoice.nft_record
    if not nft or not nft.asset_id:
        raise HTTPException(status_code=404, detail="NFT not yet minted for this invoice")

    from app.modules.invoices.nft_service import build_optin_txn

    unsigned_txn = build_optin_txn(
        wallet_address=body.wallet_address,
        asset_id=nft.asset_id,
    )

    return NFTOptInResponse(
        unsigned_txn=unsigned_txn,
        asset_id=nft.asset_id,
        message=f"Sign this transaction to opt-in to ASA {nft.asset_id}. This requires 0.1 ALGO MBR.",
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_nft_optin.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/modules/invoices/nft_service.py backend/app/modules/invoices/router.py backend/app/schemas/invoice.py backend/tests/test_nft_optin.py
git commit -m "feat: NFT opt-in endpoint with unsigned ASA txn builder (M2)"
```

---

### Task 6: NFT Claim Endpoint

**Files:**
- Modify: `backend/app/modules/invoices/router.py`
- Modify: `backend/app/schemas/invoice.py`
- Test: `backend/tests/test_nft_claim.py`

- [ ] **Step 1: Update schemas for claim flow**

Update `NFTClaimRequest` and `NFTClaimResponse`:

```python
class NFTClaimRequest(BaseModel):
    wallet_address: str
    signed_optin_txn: str  # base64-encoded signed opt-in txn


class NFTClaimResponse(BaseModel):
    asset_id: int
    optin_txn_id: str
    transfer_txn_id: str
    status: str
    explorer_url: str
```

- [ ] **Step 2: Write failing tests**

```python
# backend/tests/test_nft_claim.py
"""Tests for NFT claim endpoint -- submit opt-in + transfer ASA."""

import pytest
from unittest.mock import MagicMock, patch

from app.modules.invoices.nft_service import transfer_nft


class TestTransferNft:
    """Test ASA transfer from app wallet to user."""

    def test_returns_txn_id_and_asset_id(self):
        with patch("app.modules.invoices.nft_service._get_algod_client") as mock_client_fn:
            mock_client = MagicMock()
            mock_client.suggested_params.return_value = MagicMock()
            mock_client.send_transaction.return_value = "TXN_TRANSFER_001"
            mock_client_fn.return_value = mock_client

            with patch("app.modules.invoices.nft_service.algosdk") as mock_sdk:
                mock_sdk.mnemonic.to_private_key.return_value = "fake_key"
                mock_sdk.account.address_from_private_key.return_value = "A" * 58
                mock_txn = MagicMock()
                mock_txn.sign.return_value = MagicMock()
                mock_sdk.transaction.AssetTransferTxn.return_value = mock_txn
                mock_sdk.transaction.wait_for_confirmation.return_value = {"confirmed-round": 100}

                result = transfer_nft(asset_id=123456789, receiver_address="B" * 58)

                assert result["txn_id"] == "TXN_TRANSFER_001"
                assert result["asset_id"] == 123456789

    def test_transfer_amount_is_1(self):
        with patch("app.modules.invoices.nft_service._get_algod_client") as mock_client_fn:
            mock_client = MagicMock()
            mock_client.suggested_params.return_value = MagicMock()
            mock_client.send_transaction.return_value = "TXN_002"
            mock_client_fn.return_value = mock_client

            with patch("app.modules.invoices.nft_service.algosdk") as mock_sdk:
                mock_sdk.mnemonic.to_private_key.return_value = "fake_key"
                mock_sdk.account.address_from_private_key.return_value = "A" * 58
                mock_txn = MagicMock()
                mock_txn.sign.return_value = MagicMock()
                mock_sdk.transaction.AssetTransferTxn.return_value = mock_txn
                mock_sdk.transaction.wait_for_confirmation.return_value = {"confirmed-round": 101}

                transfer_nft(asset_id=99, receiver_address="B" * 58)

                call_kwargs = mock_sdk.transaction.AssetTransferTxn.call_args.kwargs
                assert call_kwargs["amt"] == 1
```

- [ ] **Step 3: Implement claim endpoint**

Update claim endpoint in `router.py`:

```python
@router.post("/{invoice_id}/nft/claim", response_model=NFTClaimResponse)
async def nft_claim(
    invoice_id: str,
    body: NFTClaimRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit signed opt-in txn, then transfer NFT to user wallet."""
    invoice = await _get_invoice_for_user(db, invoice_id, current_user.id)

    nft = invoice.nft_record
    if not nft or nft.status != "minted":
        raise HTTPException(status_code=409, detail="NFT not available for claim")

    from app.modules.invoices.nft_service import submit_signed_txn, transfer_nft

    # 1. Submit user's signed opt-in transaction
    optin_txid = await submit_signed_txn(body.signed_optin_txn)
    nft.opt_in_txn_id = optin_txid
    nft.status = "opt_in_pending"
    await db.commit()

    # 2. Transfer ASA from app wallet to user
    transfer_result = transfer_nft(
        asset_id=nft.asset_id,
        receiver_address=body.wallet_address,
    )
    nft.transfer_txn_id = transfer_result["txn_id"]
    nft.claimed_by_wallet = body.wallet_address
    nft.status = "claimed"
    await db.commit()

    explorer_url = f"{settings.PERA_EXPLORER_BASE_URL}/asset/{nft.asset_id}/"

    return NFTClaimResponse(
        asset_id=nft.asset_id,
        optin_txn_id=optin_txid,
        transfer_txn_id=transfer_result["txn_id"],
        status="claimed",
        explorer_url=explorer_url,
    )
```

Add `submit_signed_txn` to `nft_service.py`:

```python
async def submit_signed_txn(signed_txn_b64: str) -> str:
    """Submit a base64-encoded signed transaction to Algorand testnet."""
    import base64
    client = _get_algod_client()
    raw = base64.b64decode(signed_txn_b64)
    txid = client.send_raw_transaction(raw)
    algosdk.transaction.wait_for_confirmation(client, txid, 4)
    return txid
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_nft_claim.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/modules/invoices/nft_service.py backend/app/modules/invoices/router.py backend/app/schemas/invoice.py backend/tests/test_nft_claim.py
git commit -m "feat: NFT claim endpoint with ASA transfer (M2)"
```

---

### Task 7: Full Verification

**Files:** All

- [ ] **Step 1: Run full test suite**

Run: `cd backend && python -m pytest -v --tb=short`
Expected: 321 existing + ~40 new tests = ~360+ tests, all PASS

- [ ] **Step 2: Fix any failures**

If failures: fix and re-run. Do not modify existing passing tests unless the change is justified.

- [ ] **Step 3: Update tasks/todo.md**

Mark M2 features complete. Update test count.

- [ ] **Step 4: Update tasks/lessons.md if needed**

Add any new gotchas or corrections discovered during implementation.

- [ ] **Step 5: Commit all**

```bash
git add -A
git commit -m "feat: M2 backend integration complete -- pipeline, events, persistence, NFT endpoints"
```
