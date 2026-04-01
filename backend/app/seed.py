"""Seed the database with demo user and sample invoices with full pipeline data."""

import asyncio
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.models.agent_trace import AgentTrace
from app.models.invoice import Invoice
from app.models.nft_record import NFTRecord
from app.models.user import User


def _hash(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


DEMO_PASSWORD = "Demo@1234"

# Four invoices with different statuses and risk levels
INVOICES = [
    {
        "invoice_number": "INV-2026-001",
        "status": "approved",
        "file_key": "invoices/demo/inv-001/invoice_acme.pdf",
        "file_name": "invoice_acme.pdf",
        "risk_score": 82,
        "extracted_data": {
            "seller": {"name": "Acme Technologies Pvt Ltd", "gstin": "27AABCU9603R1ZM", "address": "Mumbai, MH"},
            "buyer": {"name": "TechBuild Solutions", "gstin": "29AABCT1234R1ZX", "address": "Bangalore, KA"},
            "invoice_number": "INV-2026-001",
            "invoice_date": "2026-03-15",
            "due_date": "2026-04-14",
            "subtotal": 520000.0,
            "tax_amount": 93600.0,
            "tax_rate": 18.0,
            "total_amount": 613600.0,
            "line_items": [
                {"description": "Cloud Server Hosting", "hsn_code": "998314", "quantity": 12, "rate": 25000, "amount": 300000},
                {"description": "Technical Support Hours", "hsn_code": "998313", "quantity": 40, "rate": 5500, "amount": 220000},
            ],
        },
        "validation_result": {"is_valid": True, "errors": [], "warnings": []},
        "gst_compliance": {"is_compliant": True, "details": {"hsn_valid": True, "rate_match": True, "e_invoice": True}},
        "fraud_detection": {
            "overall": "pass", "confidence": 97.0, "flags": [],
            "layers": [
                {"name": "Document Integrity", "result": "pass", "detail": "No tampering detected", "confidence": 98.5},
                {"name": "Financial Consistency", "result": "pass", "detail": "All amounts reconcile", "confidence": 97.0},
                {"name": "Pattern Analysis", "result": "pass", "detail": "Consistent with seller history", "confidence": 95.0},
                {"name": "Entity Verification", "result": "pass", "detail": "Both entities verified", "confidence": 99.0},
                {"name": "Cross-Reference", "result": "pass", "detail": "No duplicate invoices found", "confidence": 96.0},
            ],
        },
        "gstin_verification": {"verified": True, "status": "active", "details": {"trade_name": "Acme Technologies", "state": "Maharashtra"}},
        "buyer_intel": {"payment_history": "reliable", "avg_days": 28, "previous_count": 8},
        "credit_score": {"score": 750, "rating": "good"},
        "company_info": {"status": "active", "incorporated": "2015", "paid_up_capital": 100000000.0},
        "risk_assessment": {
            "score": 82, "level": "low",
            "explanation": "Low risk. Active GSTIN, CIBIL 750, 8 invoices paid on time. All fraud checks passed.",
        },
        "underwriting": {
            "decision": "approved",
            "rule_matched": "Auto-approve: risk > 80, CIBIL > 700, 0 fraud flags",
            "cross_validation": "passed",
            "reasoning": "Invoice meets all auto-approval criteria. Risk score 82 > threshold 80.",
        },
        "nft": {"asset_id": 757705537, "status": "minted"},
    },
    {
        "invoice_number": "INV-2026-002",
        "status": "flagged",
        "file_key": "invoices/demo/inv-002/invoice_techco.pdf",
        "file_name": "invoice_techco.pdf",
        "risk_score": 45,
        "extracted_data": {
            "seller": {"name": "TechCo Solutions", "gstin": "29AADCT5678R1Z2", "address": "Bangalore, KA"},
            "buyer": {"name": "MetroRetail India", "gstin": "07AAACM9876R1ZP", "address": "New Delhi, DL"},
            "invoice_number": "INV-2026-002",
            "invoice_date": "2026-03-20",
            "due_date": "2026-04-19",
            "subtotal": 262712.0,
            "tax_amount": 47288.0,
            "tax_rate": 18.0,
            "total_amount": 310000.0,
            "line_items": [
                {"description": "Custom Software Development", "hsn_code": "998314", "quantity": 1, "rate": 262712, "amount": 262712},
            ],
        },
        "validation_result": {"is_valid": True, "errors": [], "warnings": ["Single line item for large amount"]},
        "gst_compliance": {"is_compliant": True, "details": {"hsn_valid": True, "rate_match": True, "e_invoice": False}},
        "fraud_detection": {
            "overall": "warning", "confidence": 68.0, "flags": ["Buyer GSTIN inactive (Delhi prefix 07)"],
            "layers": [
                {"name": "Document Integrity", "result": "pass", "detail": "No tampering", "confidence": 95.0},
                {"name": "Financial Consistency", "result": "pass", "detail": "Amounts reconcile", "confidence": 90.0},
                {"name": "Pattern Analysis", "result": "warning", "detail": "First invoice from this seller", "confidence": 55.0},
                {"name": "Entity Verification", "result": "warning", "detail": "Buyer GSTIN inactive", "confidence": 40.0},
                {"name": "Cross-Reference", "result": "pass", "detail": "No duplicates", "confidence": 92.0},
            ],
        },
        "gstin_verification": {"verified": False, "status": "inactive", "details": {"trade_name": "MetroRetail India", "state": "Delhi", "issue": "Buyer GSTIN inactive"}},
        "buyer_intel": {"payment_history": "limited", "avg_days": 45, "previous_count": 2},
        "credit_score": {"score": 580, "rating": "fair"},
        "company_info": {"status": "active", "incorporated": "2020", "paid_up_capital": 5000000.0},
        "risk_assessment": {
            "score": 45, "level": "medium",
            "explanation": "Medium risk. Buyer GSTIN inactive, limited payment history, CIBIL 580. Flagged for manual review.",
        },
        "underwriting": {
            "decision": "flagged_for_review",
            "rule_matched": "Flag: risk 40-70 with inactive GSTIN",
            "cross_validation": "partial",
            "reasoning": "Buyer GSTIN inactive. Insufficient payment history. Manual review required.",
        },
        "nft": None,
    },
    {
        "invoice_number": "INV-2026-003",
        "status": "minted",
        "file_key": "invoices/demo/inv-003/invoice_buildright.pdf",
        "file_name": "invoice_buildright.pdf",
        "risk_score": 91,
        "extracted_data": {
            "seller": {"name": "BuildRight Infra Pvt Ltd", "gstin": "09AABCB5432R1ZK", "address": "Noida, UP"},
            "buyer": {"name": "GovContracts India", "gstin": "27AAACG7654R1ZM", "address": "Mumbai, MH"},
            "invoice_number": "INV-2026-003",
            "invoice_date": "2026-03-10",
            "due_date": "2026-04-09",
            "subtotal": 677966.0,
            "tax_amount": 122034.0,
            "tax_rate": 18.0,
            "total_amount": 800000.0,
            "line_items": [
                {"description": "Steel Reinforcement Bars", "hsn_code": "7213", "quantity": 50, "rate": 8000, "amount": 400000},
                {"description": "Cement (OPC 53 Grade)", "hsn_code": "2523", "quantity": 200, "rate": 389.83, "amount": 77966},
                {"description": "Construction Labour", "hsn_code": "9954", "quantity": 1, "rate": 200000, "amount": 200000},
            ],
        },
        "validation_result": {"is_valid": True, "errors": [], "warnings": []},
        "gst_compliance": {"is_compliant": True, "details": {"hsn_valid": True, "rate_match": True, "e_invoice": True}},
        "fraud_detection": {
            "overall": "pass", "confidence": 98.5, "flags": [],
            "layers": [
                {"name": "Document Integrity", "result": "pass", "detail": "No tampering detected", "confidence": 99.0},
                {"name": "Financial Consistency", "result": "pass", "detail": "All amounts reconcile", "confidence": 98.0},
                {"name": "Pattern Analysis", "result": "pass", "detail": "Consistent with industry norms", "confidence": 97.0},
                {"name": "Entity Verification", "result": "pass", "detail": "Both entities verified and active", "confidence": 99.5},
                {"name": "Cross-Reference", "result": "pass", "detail": "No duplicate invoices found", "confidence": 99.0},
            ],
        },
        "gstin_verification": {"verified": True, "status": "active", "details": {"trade_name": "BuildRight Infra", "state": "Uttar Pradesh"}},
        "buyer_intel": {"payment_history": "excellent", "avg_days": 15, "previous_count": 22},
        "credit_score": {"score": 820, "rating": "excellent"},
        "company_info": {"status": "active", "incorporated": "2010", "paid_up_capital": 500000000.0},
        "risk_assessment": {
            "score": 91, "level": "low",
            "explanation": "Excellent risk profile. CIBIL 820, 22 previous invoices paid in avg 15 days. Government buyer.",
        },
        "underwriting": {
            "decision": "approved",
            "rule_matched": "Auto-approve: risk > 80, CIBIL > 700, 0 fraud flags",
            "cross_validation": "passed",
            "reasoning": "Excellent creditworthiness. All checks passed with high confidence.",
        },
        "nft": {"asset_id": 757705538, "status": "minted"},
    },
    {
        "invoice_number": "INV-2026-004",
        "status": "rejected",
        "file_key": "invoices/demo/inv-004/invoice_fakecorp.pdf",
        "file_name": "invoice_fakecorp.pdf",
        "risk_score": 12,
        "extracted_data": {
            "seller": {"name": "FakeCorp Ltd", "gstin": "07AABCF1111R1ZF", "address": "Delhi, DL"},
            "buyer": {"name": "ShellBuy Enterprises", "gstin": "07AABCS2222R1ZX", "address": "Delhi, DL"},
            "invoice_number": "INV-2026-004",
            "invoice_date": "2026-03-25",
            "due_date": "2026-04-24",
            "subtotal": 177966.0,
            "tax_amount": 32034.0,
            "tax_rate": 18.0,
            "total_amount": 210000.0,
            "line_items": [
                {"description": "Consulting Services", "hsn_code": "998311", "quantity": 1, "rate": 177966, "amount": 177966},
            ],
        },
        "validation_result": {"is_valid": False, "errors": ["Seller GSTIN inactive", "Buyer GSTIN inactive"], "warnings": ["Single vague line item"]},
        "gst_compliance": {"is_compliant": False, "details": {"hsn_valid": True, "rate_match": True, "e_invoice": False, "issue": "Both GSTINs inactive"}},
        "fraud_detection": {
            "overall": "fail", "confidence": 25.0, "flags": ["Both GSTINs inactive", "Shell company indicators", "Round amount suspicious"],
            "layers": [
                {"name": "Document Integrity", "result": "warning", "detail": "Metadata anomalies detected", "confidence": 45.0},
                {"name": "Financial Consistency", "result": "warning", "detail": "Round amount, single vague line item", "confidence": 35.0},
                {"name": "Pattern Analysis", "result": "fail", "detail": "No previous transaction history", "confidence": 15.0},
                {"name": "Entity Verification", "result": "fail", "detail": "Both entities have inactive GSTINs", "confidence": 10.0},
                {"name": "Cross-Reference", "result": "warning", "detail": "Similar invoice pattern flagged", "confidence": 30.0},
            ],
        },
        "gstin_verification": {"verified": False, "status": "inactive", "details": {"trade_name": "FakeCorp Ltd", "state": "Delhi", "issue": "GSTIN cancelled"}},
        "buyer_intel": {"payment_history": "no_history", "avg_days": 0, "previous_count": 0},
        "credit_score": {"score": 350, "rating": "poor"},
        "company_info": {"status": "struck_off", "incorporated": "2024", "paid_up_capital": 100000.0},
        "risk_assessment": {
            "score": 12, "level": "high",
            "explanation": "High risk. Both GSTINs inactive, company struck off, no payment history, CIBIL 350. Multiple fraud indicators.",
        },
        "underwriting": {
            "decision": "rejected",
            "rule_matched": "Auto-reject: risk < 30 or fraud flags > 2",
            "cross_validation": "failed",
            "reasoning": "Multiple fraud indicators. Both GSTINs inactive. Company struck off MCA registry.",
        },
        "nft": None,
    },
]

# Agent trace data for each invoice
AGENT_TRACES = {
    "INV-2026-001": [
        {
            "agent_name": "Invoice Processing Agent",
            "model": "claude-sonnet-4.6",
            "duration_ms": 72000,
            "steps": [
                {"step_number": 1, "tool_name": "extract_invoice", "started_at": "2026-03-18T10:00:00Z", "duration_ms": 3200, "input_summary": "invoice_acme.pdf (1.2 MB)", "output_summary": "23 fields extracted, 2 line items", "result": {"fields_count": 23, "confidence": 98.2}, "status": "success"},
                {"step_number": 2, "tool_name": "validate_fields", "started_at": "2026-03-18T10:00:03Z", "duration_ms": 1100, "input_summary": "23 extracted fields", "output_summary": "All fields valid", "result": {"valid": 23, "invalid": 0}, "status": "success"},
                {"step_number": 3, "tool_name": "validate_gst_compliance", "started_at": "2026-03-18T10:00:04Z", "duration_ms": 800, "input_summary": "2 HSN codes, 18% rate", "output_summary": "GST compliant", "result": {"compliant": True}, "status": "success"},
                {"step_number": 4, "tool_name": "verify_gstn", "started_at": "2026-03-18T10:00:05Z", "duration_ms": 1500, "input_summary": "27AABCU9603R1ZM, 29AABCT1234R1ZX", "output_summary": "Both verified active", "result": {"verified": True}, "status": "success"},
                {"step_number": 5, "tool_name": "check_fraud", "started_at": "2026-03-18T10:00:07Z", "duration_ms": 4500, "input_summary": "5-layer analysis", "output_summary": "All layers pass, 97% confidence", "result": {"overall": "pass", "flags": 0}, "status": "success"},
                {"step_number": 6, "tool_name": "get_buyer_intel", "started_at": "2026-03-18T10:00:11Z", "duration_ms": 2000, "input_summary": "29AABCT1234R1ZX", "output_summary": "Reliable, avg 28 days, 8 invoices", "result": {"reliability": "high"}, "status": "success"},
                {"step_number": 7, "tool_name": "get_credit_score", "started_at": "2026-03-18T10:00:13Z", "duration_ms": 1800, "input_summary": "27AABCU9603R1ZM", "output_summary": "CIBIL 750 (good)", "result": {"score": 750}, "status": "success"},
                {"step_number": 8, "tool_name": "get_company_info", "started_at": "2026-03-18T10:00:15Z", "duration_ms": 1500, "input_summary": "27AABCU9603R1ZM", "output_summary": "Active, est. 2015", "result": {"status": "active"}, "status": "success"},
                {"step_number": 9, "tool_name": "calculate_risk", "started_at": "2026-03-18T10:00:17Z", "duration_ms": 2200, "input_summary": "All signals", "output_summary": "Risk 82/100 (low)", "result": {"score": 82, "level": "low"}, "status": "success"},
                {"step_number": 10, "tool_name": "generate_summary", "started_at": "2026-03-18T10:00:19Z", "duration_ms": 3000, "input_summary": "Complete analysis", "output_summary": "Recommendation: approve", "result": {"recommendation": "approve"}, "status": "success"},
            ],
            "handoff_context": {"from_agent": "Invoice Processing Agent", "to_agent": "Underwriting Agent", "context_keys": ["extracted_data", "risk_score", "fraud_result", "gst_compliance", "gstin_status", "credit_score", "company_info"]},
        },
        {
            "agent_name": "Underwriting Agent",
            "model": "claude-sonnet-4.6",
            "duration_ms": 30000,
            "steps": [
                {"step_number": 11, "tool_name": "cross_validate_outputs", "started_at": "2026-03-18T10:01:12Z", "duration_ms": 2400, "input_summary": "All tool outputs", "output_summary": "All consistent", "result": {"discrepancies": 0}, "status": "success"},
                {"step_number": 12, "tool_name": "underwriting_decision", "started_at": "2026-03-18T10:01:15Z", "duration_ms": 1800, "input_summary": "Risk 82, CIBIL 750, 0 flags", "output_summary": "AUTO-APPROVED (Rule 2)", "result": {"decision": "approved", "rule": 2}, "status": "success"},
                {"step_number": 13, "tool_name": "log_decision", "started_at": "2026-03-18T10:01:17Z", "duration_ms": 500, "input_summary": "Decision: approved", "output_summary": "Logged to DB", "result": {"logged": True}, "status": "success"},
                {"step_number": 14, "tool_name": "mint_nft", "started_at": "2026-03-18T10:01:18Z", "duration_ms": 8000, "input_summary": "INV-2026-001, risk 82", "output_summary": "ASA 757705537 minted", "result": {"asset_id": 757705537}, "status": "success"},
            ],
            "handoff_context": None,
        },
    ],
}


async def seed_database():
    """Seed the database with demo data."""
    async with async_session() as db:
        # Check if demo user already exists
        result = await db.execute(select(User).where(User.email == "demo@chainfactor.ai"))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            updated = False
            if not existing_user.password_hash:
                existing_user.password_hash = _hash(DEMO_PASSWORD)
                updated = True
                print("Updated demo user password hash.")
            # Check if invoices exist
            inv_result = await db.execute(select(Invoice).where(Invoice.user_id == existing_user.id))
            if inv_result.scalars().first():
                if updated:
                    await db.commit()
                print("Demo user and invoices already exist. Skipping seed.")
                return
            # Invoices missing — seed them for existing user
            if updated:
                await db.commit()
            user = existing_user
            print(f"Demo user exists (id={user.id}). Seeding invoices...")
        else:
            user = User(
                cognito_sub="local-demo-user-seed",
                name="Demo User",
                email="demo@chainfactor.ai",
                phone="+919876543210",
                company_name="Acme Technologies Pvt Ltd",
                gstin="27AABCU9603R1ZM",
                password_hash=_hash(DEMO_PASSWORD),
            )
            db.add(user)
            await db.flush()
            print(f"Created demo user: {user.id} (email: demo@chainfactor.ai, password: {DEMO_PASSWORD})")

        # Create invoices
        for i, inv_data in enumerate(INVOICES):
            inv_id = uuid.uuid4()
            now = datetime.now(timezone.utc)
            created = now - timedelta(days=15 - i * 3)

            invoice = Invoice(
                id=inv_id,
                user_id=user.id,
                invoice_number=inv_data["invoice_number"],
                status=inv_data["status"],
                file_key=inv_data["file_key"],
                file_name=inv_data["file_name"],
                risk_score=inv_data["risk_score"],
                extracted_data=inv_data["extracted_data"],
                validation_result=inv_data["validation_result"],
                gst_compliance=inv_data["gst_compliance"],
                fraud_detection=inv_data["fraud_detection"],
                gstin_verification=inv_data["gstin_verification"],
                buyer_intel=inv_data["buyer_intel"],
                credit_score=inv_data["credit_score"],
                company_info=inv_data["company_info"],
                risk_assessment=inv_data["risk_assessment"],
                underwriting=inv_data["underwriting"],
                ai_explanation=inv_data["risk_assessment"]["explanation"],
                processing_started_at=created,
                processing_completed_at=created + timedelta(seconds=102),
                processing_duration_ms=102000,
            )
            invoice.created_at = created
            db.add(invoice)
            await db.flush()
            print(f"Created invoice: {inv_data['invoice_number']} ({inv_data['status']}, risk={inv_data['risk_score']})")

            # Create NFT record if applicable
            nft_data = inv_data.get("nft")
            if nft_data:
                nft = NFTRecord(
                    invoice_id=inv_id,
                    asset_id=nft_data["asset_id"],
                    mint_txn_id=f"SEED_TXN_{inv_data['invoice_number']}",
                    status=nft_data["status"],
                    arc69_metadata={
                        "standard": "arc69",
                        "description": f"ChainFactor AI verified invoice {inv_data['invoice_number']}",
                        "properties": {
                            "invoice_number": inv_data["invoice_number"],
                            "seller": inv_data["extracted_data"]["seller"]["name"],
                            "buyer": inv_data["extracted_data"]["buyer"]["name"],
                            "amount": inv_data["extracted_data"]["total_amount"],
                            "risk_score": inv_data["risk_score"],
                        },
                    },
                )
                db.add(nft)
                print(f"  NFT minted: ASA {nft_data['asset_id']}")

            # Create agent traces
            traces = AGENT_TRACES.get(inv_data["invoice_number"], [])
            for trace_data in traces:
                trace = AgentTrace(
                    invoice_id=inv_id,
                    agent_name=trace_data["agent_name"],
                    model=trace_data["model"],
                    duration_ms=trace_data["duration_ms"],
                    steps=trace_data["steps"],
                    handoff_context=trace_data["handoff_context"],
                )
                db.add(trace)

        await db.commit()
        print("\nSeed complete! Login with: demo@chainfactor.ai / Demo@1234")


if __name__ == "__main__":
    asyncio.run(seed_database())
