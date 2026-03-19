"""DB Persistence Helper -- saves individual tool results and agent traces.

Responsibilities:
- Map pipeline step names to Invoice JSONB column names (STEP_TO_COLUMN)
- Persist a single tool result to the appropriate Invoice column (persist_tool_result)
- Create and persist an AgentTrace record (save_agent_trace)

Dependencies:
- Invoice model: JSONB columns per tool, risk_score (Integer), ai_explanation (Text)
- AgentTrace model: agent_name, model, duration_ms, steps, handoff_context
"""

from __future__ import annotations

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_trace import AgentTrace
from app.models.invoice import Invoice

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Step -> Invoice column mapping
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# persist_tool_result
# ---------------------------------------------------------------------------


async def persist_tool_result(
    *,
    db: AsyncSession,
    invoice: Invoice,
    step_name: str,
    result: dict,
) -> None:
    """Persist a single tool result to the invoice's JSONB column.

    Special cases:
    - calculate_risk: also sets invoice.risk_score (denormalized Integer)
    - generate_summary: stores result["summary"] (str) into ai_explanation (Text)
    - Unknown step names: log a warning, do not modify the invoice

    Always calls await db.commit() after handling (even for unknown steps).

    Args:
        db: Async SQLAlchemy session.
        invoice: Invoice ORM instance to update.
        step_name: Name of the completed pipeline step (e.g. "extract_invoice").
        result: Dict returned by the tool.
    """
    column = STEP_TO_COLUMN.get(step_name)

    if column is None:
        logger.warning(
            "persist_tool_result: unknown step '%s' -- no column mapped, skipping",
            step_name,
        )
        await db.commit()
        return

    if step_name == "generate_summary":
        # ai_explanation is a Text column -- store the summary string, not the dict
        setattr(invoice, column, result.get("summary"))
    else:
        setattr(invoice, column, result)

        if step_name == "calculate_risk":
            # Denormalize risk_score for fast queries/sorting
            invoice.risk_score = int(result["score"])

    await db.commit()


# ---------------------------------------------------------------------------
# save_agent_trace
# ---------------------------------------------------------------------------


async def save_agent_trace(
    *,
    db: AsyncSession,
    invoice_id: uuid.UUID,
    agent_name: str,
    model: str,
    duration_ms: int,
    steps: list,
    handoff_context: dict | None = None,
) -> AgentTrace:
    """Create and persist an AgentTrace record.

    Args:
        db: Async SQLAlchemy session.
        invoice_id: UUID of the invoice being processed.
        agent_name: Logical name of the agent (e.g. "invoice_processing_agent").
        model: Bedrock model ID used by the agent.
        duration_ms: Total agent wall-clock time in milliseconds.
        steps: List of step dicts with tool_name, duration_ms, result, etc.
        handoff_context: Optional dict passed to the next agent on handoff.

    Returns:
        The created AgentTrace instance (already committed).
    """
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
