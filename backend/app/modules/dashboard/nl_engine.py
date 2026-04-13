"""Natural language query engine for portfolio analysis.

Parses user queries into safe DB operations and returns formatted answers.
Uses pattern matching for common query types, with Bedrock Opus fallback
for complex questions when available.

Security:
- All DB access is via SQLAlchemy ORM (parameterized queries only)
- User ID scoping enforced on every query (IDOR prevention)
- No raw SQL execution
- Input length limited to prevent abuse
"""

from __future__ import annotations

import logging
import re
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.invoice import Invoice

logger = logging.getLogger(__name__)

MAX_QUERY_LENGTH = 500


# ---------------------------------------------------------------------------
# Query pattern matchers
# ---------------------------------------------------------------------------

_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"high[- ]?risk", re.I), "high_risk"),
    (re.compile(r"low[- ]?risk", re.I), "low_risk"),
    (re.compile(r"medium[- ]?risk", re.I), "medium_risk"),
    (re.compile(r"approved|approval", re.I), "approved"),
    (re.compile(r"rejected|rejection", re.I), "rejected"),
    (re.compile(r"flagged|review|pending", re.I), "flagged"),
    (re.compile(r"total\s*(value|amount|worth)", re.I), "total_value"),
    (re.compile(r"how many|count|number of", re.I), "count"),
    (re.compile(r"average|avg|mean", re.I), "average_risk"),
    (re.compile(r"recent|latest|newest", re.I), "recent"),
    (re.compile(r"summary|overview|portfolio", re.I), "summary"),
    (re.compile(r"nft|minted|blockchain|on[- ]?chain", re.I), "nft_status"),
    (re.compile(r"seller|from|vendor", re.I), "by_seller"),
    (re.compile(r"risk.*score.*(above|over|greater|>)\s*(\d+)", re.I), "risk_above"),
    (re.compile(r"risk.*score.*(below|under|less|<)\s*(\d+)", re.I), "risk_below"),
    (re.compile(r"amount.*(above|over|greater|>)\s*(\d+)", re.I), "amount_above"),
]


def _classify_query(query: str) -> tuple[str, dict[str, Any]]:
    """Classify a NL query into a query type and extracted params."""
    # Check for risk score threshold patterns first (more specific)
    m = re.search(r"risk.*score.*(above|over|greater|>)\s*(\d+)", query, re.I)
    if m:
        return "risk_above", {"threshold": int(m.group(2))}

    m = re.search(r"risk.*score.*(below|under|less|<)\s*(\d+)", query, re.I)
    if m:
        return "risk_below", {"threshold": int(m.group(2))}

    m = re.search(r"amount.*(above|over|greater|>)\s*(\d+)", query, re.I)
    if m:
        return "amount_above", {"threshold": int(m.group(2))}

    for pattern, query_type in _PATTERNS:
        if pattern.search(query):
            return query_type, {}

    return "general", {}


def _format_amount(v: float) -> str:
    """Format INR amount with lakhs notation."""
    if v >= 10000000:
        return f"₹{v / 10000000:.1f}Cr"
    if v >= 100000:
        return f"₹{v / 100000:.1f}L"
    if v >= 1000:
        return f"₹{v / 1000:.0f}K"
    return f"₹{v:.0f}"


def _risk_label(score: int | None) -> str:
    if score is None:
        return "unscored"
    if score >= 70:
        return "low"
    if score >= 40:
        return "medium"
    return "high"


# ---------------------------------------------------------------------------
# Query executors
# ---------------------------------------------------------------------------


async def _query_invoices(
    db: AsyncSession,
    user_id: UUID,
    *,
    status: str | None = None,
    risk_min: int | None = None,
    risk_max: int | None = None,
    limit: int = 10,
    order_by: str = "created_at_desc",
) -> list[Invoice]:
    """Safe parameterized invoice query scoped to user."""
    q = select(Invoice).where(Invoice.user_id == user_id)

    if status:
        q = q.where(Invoice.status == status)
    if risk_min is not None:
        q = q.where(Invoice.risk_score >= risk_min)
    if risk_max is not None:
        q = q.where(Invoice.risk_score < risk_max)

    if order_by == "risk_asc":
        q = q.order_by(Invoice.risk_score.asc())
    elif order_by == "risk_desc":
        q = q.order_by(Invoice.risk_score.desc())
    else:
        q = q.order_by(Invoice.created_at.desc())

    q = q.limit(limit)
    result = await db.execute(q)
    return list(result.scalars().all())


async def _get_stats(db: AsyncSession, user_id: UUID) -> dict:
    """Get aggregate stats for user's portfolio."""
    result = await db.execute(select(Invoice).where(Invoice.user_id == user_id))
    invoices = list(result.scalars().all())

    if not invoices:
        return {"total": 0, "total_value": 0, "avg_risk": 0, "approved": 0, "rejected": 0, "flagged": 0, "processing": 0, "uploaded": 0}

    total_value = sum((inv.extracted_data or {}).get("total_amount", 0) for inv in invoices)
    risk_scores = [inv.risk_score for inv in invoices if inv.risk_score is not None]
    avg_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0

    return {
        "total": len(invoices),
        "total_value": total_value,
        "avg_risk": round(avg_risk, 1),
        "approved": sum(1 for i in invoices if i.status == "approved"),
        "rejected": sum(1 for i in invoices if i.status == "rejected"),
        "flagged": sum(1 for i in invoices if i.status in ("flagged_for_review", "flagged")),
        "processing": sum(1 for i in invoices if i.status == "processing"),
        "uploaded": sum(1 for i in invoices if i.status == "uploaded"),
    }


def _format_invoice_list(invoices: list[Invoice]) -> tuple[str, list[dict]]:
    """Format a list of invoices into answer text and data rows."""
    if not invoices:
        return "No invoices found matching your criteria.", []

    lines = []
    data = []
    for inv in invoices:
        amount = (inv.extracted_data or {}).get("total_amount", 0)
        seller = (inv.extracted_data or {}).get("seller", {}).get("name", "Unknown")
        lines.append(
            f"• **{inv.invoice_number}** — {seller} — {_format_amount(amount)} "
            f"— Risk: {inv.risk_score or '—'} ({_risk_label(inv.risk_score)}) — Status: {inv.status}"
        )
        data.append({
            "invoice_id": str(inv.id),
            "invoice_number": inv.invoice_number,
            "seller": seller,
            "amount": amount,
            "risk_score": inv.risk_score,
            "status": inv.status,
        })

    return "\n".join(lines), data


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


async def execute_nl_query(
    *,
    query: str,
    user_id: UUID,
    db: AsyncSession,
) -> dict[str, Any]:
    """Execute a natural language query and return formatted results.

    Returns:
        Dict with "answer" (str) and optional "data" (list[dict]).
    """
    if len(query) > MAX_QUERY_LENGTH:
        return {"answer": "Query too long. Please keep it under 500 characters."}

    query_type, params = _classify_query(query)

    # --- Portfolio summary ---
    if query_type == "summary":
        stats = await _get_stats(db, user_id)
        if stats["total"] == 0:
            return {"answer": "Your portfolio is empty. Upload your first invoice to get started!"}
        return {
            "answer": (
                f"**Portfolio Summary:**\n"
                f"• Total invoices: {stats['total']}\n"
                f"• Total value: {_format_amount(stats['total_value'])}\n"
                f"• Average risk score: {stats['avg_risk']}\n"
                f"• Approved: {stats['approved']} | Rejected: {stats['rejected']} | Flagged: {stats['flagged']}\n"
                f"• Approval rate: {round(stats['approved'] / stats['total'] * 100, 1)}%"
            ),
            "data": [stats],
        }

    # --- Count queries ---
    if query_type == "count":
        stats = await _get_stats(db, user_id)
        return {
            "answer": f"You have **{stats['total']}** invoices in total: {stats['approved']} approved, {stats['rejected']} rejected, {stats['flagged']} flagged, {stats['processing']} processing, {stats['uploaded']} uploaded.",
            "data": [stats],
        }

    # --- Total value ---
    if query_type == "total_value":
        stats = await _get_stats(db, user_id)
        return {"answer": f"Your total portfolio value is **{_format_amount(stats['total_value'])}** across {stats['total']} invoices."}

    # --- Average risk ---
    if query_type == "average_risk":
        stats = await _get_stats(db, user_id)
        label = _risk_label(int(stats["avg_risk"]) if stats["avg_risk"] else None)
        return {"answer": f"Your average risk score is **{stats['avg_risk']}** ({label} risk)."}

    # --- High risk invoices ---
    if query_type == "high_risk":
        invoices = await _query_invoices(db, user_id, risk_max=40, order_by="risk_asc")
        text, data = _format_invoice_list(invoices)
        count = len(invoices)
        return {
            "answer": f"Found **{count}** high-risk invoice{'s' if count != 1 else ''} (risk score < 40):\n{text}" if count else "No high-risk invoices found. Your portfolio looks healthy!",
            "data": data or None,
        }

    # --- Low risk invoices ---
    if query_type == "low_risk":
        invoices = await _query_invoices(db, user_id, risk_min=70, order_by="risk_desc")
        text, data = _format_invoice_list(invoices)
        count = len(invoices)
        return {
            "answer": f"Found **{count}** low-risk invoice{'s' if count != 1 else ''} (risk score >= 70):\n{text}" if count else "No low-risk invoices found yet.",
            "data": data or None,
        }

    # --- Medium risk invoices ---
    if query_type == "medium_risk":
        invoices = await _query_invoices(db, user_id, risk_min=40, risk_max=70, order_by="risk_asc")
        text, data = _format_invoice_list(invoices)
        count = len(invoices)
        return {
            "answer": f"Found **{count}** medium-risk invoice{'s' if count != 1 else ''} (risk 40-69):\n{text}" if count else "No medium-risk invoices found.",
            "data": data or None,
        }

    # --- Status-based queries ---
    if query_type in ("approved", "rejected", "flagged"):
        status_map = {"approved": "approved", "rejected": "rejected", "flagged": "flagged_for_review"}
        invoices = await _query_invoices(db, user_id, status=status_map[query_type])
        text, data = _format_invoice_list(invoices)
        count = len(invoices)
        return {
            "answer": f"Found **{count}** {query_type} invoice{'s' if count != 1 else ''}:\n{text}" if count else f"No {query_type} invoices found.",
            "data": data or None,
        }

    # --- Recent invoices ---
    if query_type == "recent":
        invoices = await _query_invoices(db, user_id, limit=5)
        text, data = _format_invoice_list(invoices)
        return {
            "answer": f"**Recent invoices:**\n{text}" if invoices else "No invoices found. Upload your first one!",
            "data": data or None,
        }

    # --- Risk score threshold queries ---
    if query_type == "risk_above":
        threshold = params["threshold"]
        invoices = await _query_invoices(db, user_id, risk_min=threshold, order_by="risk_desc")
        text, data = _format_invoice_list(invoices)
        count = len(invoices)
        return {
            "answer": f"Found **{count}** invoice{'s' if count != 1 else ''} with risk score >= {threshold}:\n{text}" if count else f"No invoices with risk score >= {threshold}.",
            "data": data or None,
        }

    if query_type == "risk_below":
        threshold = params["threshold"]
        invoices = await _query_invoices(db, user_id, risk_max=threshold, order_by="risk_asc")
        text, data = _format_invoice_list(invoices)
        count = len(invoices)
        return {
            "answer": f"Found **{count}** invoice{'s' if count != 1 else ''} with risk score < {threshold}:\n{text}" if count else f"No invoices with risk score < {threshold}.",
            "data": data or None,
        }

    # --- Amount threshold queries ---
    if query_type == "amount_above":
        threshold = params["threshold"]
        # Need to filter by JSONB total_amount — fetch and filter in Python
        all_inv = await _query_invoices(db, user_id, limit=100)
        matching = [
            inv for inv in all_inv
            if (inv.extracted_data or {}).get("total_amount", 0) > threshold
        ]
        text, data = _format_invoice_list(matching[:10])
        count = len(matching)
        return {
            "answer": f"Found **{count}** invoice{'s' if count != 1 else ''} with amount > {_format_amount(threshold)}:\n{text}" if count else f"No invoices with amount > {_format_amount(threshold)}.",
            "data": data or None,
        }

    # --- NFT status ---
    if query_type == "nft_status":
        invoices = await _query_invoices(db, user_id, limit=50)
        with_nft = [inv for inv in invoices if getattr(inv, "nft_record", None)]
        minted = [inv for inv in with_nft if inv.nft_record.status == "minted"]
        claimed = [inv for inv in with_nft if inv.nft_record.status == "claimed"]
        return {
            "answer": (
                f"**NFT Status:**\n"
                f"• Total NFTs: {len(with_nft)}\n"
                f"• Minted (awaiting claim): {len(minted)}\n"
                f"• Claimed (in your wallet): {len(claimed)}\n"
                f"• Invoices without NFT: {len(invoices) - len(with_nft)}"
            ),
        }

    # --- General / unrecognized ---
    # Provide a helpful response with examples
    stats = await _get_stats(db, user_id)
    return {
        "answer": (
            f"I found **{stats['total']}** invoices in your portfolio "
            f"(avg risk: {stats['avg_risk']}). Try asking:\n"
            f"• \"Show me high-risk invoices\"\n"
            f"• \"How many approved invoices do I have?\"\n"
            f"• \"What's my total portfolio value?\"\n"
            f"• \"Invoices with risk score above 60\"\n"
            f"• \"Give me a portfolio summary\"\n"
            f"• \"Show recent invoices\"\n"
            f"• \"NFT status\""
        ),
    }
