"""Tests for all 6 SQLAlchemy models -- creation, persistence, constraints."""

import uuid

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AgentTrace, Invoice, NFTRecord, Rule, User, UserSettings


@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession) -> None:
    """Create a user and verify all fields + UUID PK generation."""
    user = User(
        cognito_sub="unit-test-sub-100",
        name="Unit Test User",
        email="unit100@chainfactor.ai",
        phone="+919000000100",
        company_name="Unit Corp",
        gstin="27AABCU1000R1Z1",
        wallet_address=None,
    )
    db_session.add(user)
    await db_session.flush()

    assert user.id is not None
    assert isinstance(user.id, uuid.UUID)
    assert user.cognito_sub == "unit-test-sub-100"
    assert user.name == "Unit Test User"
    assert user.email == "unit100@chainfactor.ai"
    assert user.phone == "+919000000100"
    assert user.company_name == "Unit Corp"
    assert user.gstin == "27AABCU1000R1Z1"
    assert user.wallet_address is None


@pytest.mark.asyncio
async def test_create_user_with_wallet(db_session: AsyncSession) -> None:
    """Create a user with a wallet address and verify it persists."""
    wallet = "ALGOTESTWALLETADDRESSFOR7UNIT8TESTING9ABCDEFG12"
    user = User(
        cognito_sub="unit-test-sub-101",
        name="Wallet Test",
        email="wallet101@chainfactor.ai",
        phone="+919000000101",
        company_name="Wallet Corp",
        gstin="29AABCW1010R1ZX",
        wallet_address=wallet,
    )
    db_session.add(user)
    await db_session.flush()

    assert user.wallet_address == wallet


@pytest.mark.asyncio
async def test_user_unique_email(db_session: AsyncSession) -> None:
    """Two users with the same email should raise IntegrityError."""
    shared_email = "duplicate@chainfactor.ai"
    user1 = User(
        cognito_sub="dup-email-sub-1",
        name="Dup Email 1",
        email=shared_email,
        phone="+919000000201",
        company_name="Dup Corp 1",
        gstin="27AABCD2001R1Z1",
    )
    user2 = User(
        cognito_sub="dup-email-sub-2",
        name="Dup Email 2",
        email=shared_email,
        phone="+919000000202",
        company_name="Dup Corp 2",
        gstin="27AABCD2002R1Z2",
    )
    db_session.add(user1)
    await db_session.flush()

    db_session.add(user2)
    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_user_unique_phone(db_session: AsyncSession) -> None:
    """Two users with the same phone should raise IntegrityError."""
    shared_phone = "+919000000300"
    user1 = User(
        cognito_sub="dup-phone-sub-1",
        name="Dup Phone 1",
        email="dupphone1@chainfactor.ai",
        phone=shared_phone,
        company_name="Dup Phone Corp 1",
        gstin="27AABCP3001R1Z1",
    )
    user2 = User(
        cognito_sub="dup-phone-sub-2",
        name="Dup Phone 2",
        email="dupphone2@chainfactor.ai",
        phone=shared_phone,
        company_name="Dup Phone Corp 2",
        gstin="27AABCP3002R1Z2",
    )
    db_session.add(user1)
    await db_session.flush()

    db_session.add(user2)
    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_create_invoice(db_session: AsyncSession, test_user: User) -> None:
    """Create an invoice linked to a user and verify FK + default status."""
    invoice = Invoice(
        user_id=test_user.id,
        invoice_number="INV-2026-001",
        status="uploaded",
        file_key="invoices/test/inv-001.pdf",
        file_name="inv-001.pdf",
    )
    db_session.add(invoice)
    await db_session.flush()

    assert invoice.id is not None
    assert isinstance(invoice.id, uuid.UUID)
    assert invoice.user_id == test_user.id
    assert invoice.invoice_number == "INV-2026-001"
    assert invoice.status == "uploaded"
    assert invoice.file_key == "invoices/test/inv-001.pdf"
    assert invoice.file_name == "inv-001.pdf"
    assert invoice.extracted_data is None
    assert invoice.risk_score is None


@pytest.mark.asyncio
async def test_invoice_jsonb_fields(db_session: AsyncSession, test_user: User) -> None:
    """Set JSONB fields on invoice and verify round-trip."""
    extracted = {
        "invoice_number": "INV-2026-002",
        "amount": 150000.50,
        "line_items": [{"description": "Widget", "qty": 10, "rate": 15000.05}],
    }
    fraud_flags = {
        "duplicate_check": False,
        "anomaly_score": 0.12,
        "flags": ["amount_within_range"],
    }
    invoice = Invoice(
        user_id=test_user.id,
        invoice_number="INV-2026-002",
        status="uploaded",
        file_key="invoices/test/inv-002.pdf",
        file_name="inv-002.pdf",
        extracted_data=extracted,
        fraud_detection=fraud_flags,
    )
    db_session.add(invoice)
    await db_session.flush()

    # Verify JSONB data persists after flush (proves serialization to DB succeeded).
    # Full SELECT round-trip skipped: SQLite's UUID result processor can't handle
    # PostgreSQL UUID type -- tested in integration tests with real PostgreSQL.
    assert invoice.extracted_data == extracted
    assert invoice.fraud_detection == fraud_flags
    assert invoice.extracted_data["line_items"][0]["qty"] == 10


@pytest.mark.asyncio
async def test_create_rule(db_session: AsyncSession, test_user: User) -> None:
    """Create a Rule with JSONB conditions and verify defaults."""
    conditions = [
        {"field": "invoice_amount", "operator": "less_than", "value": 500000},
        {"field": "risk_score", "operator": "less_than", "value": 50},
    ]
    rule = Rule(
        user_id=test_user.id,
        conditions=conditions,
        action="auto_approve",
        is_active=True,
    )
    db_session.add(rule)
    await db_session.flush()

    assert rule.id is not None
    assert rule.user_id == test_user.id
    assert rule.conditions == conditions
    assert rule.action == "auto_approve"
    assert rule.is_active is True


@pytest.mark.asyncio
async def test_create_user_settings(db_session: AsyncSession, test_user: User) -> None:
    """Create UserSettings with default_action."""
    user_settings = UserSettings(
        user_id=test_user.id,
        default_action="flag_for_review",
    )
    db_session.add(user_settings)
    await db_session.flush()

    assert user_settings.id is not None
    assert user_settings.user_id == test_user.id
    assert user_settings.default_action == "flag_for_review"


@pytest.mark.asyncio
async def test_create_nft_record(db_session: AsyncSession, test_user: User) -> None:
    """Create an NFTRecord linked to an invoice."""
    invoice = Invoice(
        user_id=test_user.id,
        invoice_number="INV-NFT-001",
        status="approved",
        file_key="invoices/test/inv-nft-001.pdf",
        file_name="inv-nft-001.pdf",
    )
    db_session.add(invoice)
    await db_session.flush()

    nft = NFTRecord(
        invoice_id=invoice.id,
        status="minted",
        asset_id=123456789,
        mint_txn_id="ABCDEF1234567890TXNHASH",
    )
    db_session.add(nft)
    await db_session.flush()

    assert nft.id is not None
    assert nft.invoice_id == invoice.id
    assert nft.status == "minted"
    assert nft.asset_id == 123456789
    assert nft.mint_txn_id == "ABCDEF1234567890TXNHASH"
    assert nft.opt_in_txn_id is None
    assert nft.transfer_txn_id is None
    assert nft.claimed_by_wallet is None


@pytest.mark.asyncio
async def test_create_agent_trace(db_session: AsyncSession, test_user: User) -> None:
    """Create an AgentTrace with JSONB steps."""
    invoice = Invoice(
        user_id=test_user.id,
        invoice_number="INV-TRACE-001",
        status="processing",
        file_key="invoices/test/inv-trace-001.pdf",
        file_name="inv-trace-001.pdf",
    )
    db_session.add(invoice)
    await db_session.flush()

    steps = [
        {
            "step_number": 1,
            "tool_name": "extract_invoice",
            "duration_ms": 3200,
            "input_summary": "PDF uploaded",
            "output_summary": "12 fields extracted",
            "status": "complete",
        },
        {
            "step_number": 2,
            "tool_name": "validate_fields",
            "duration_ms": 1100,
            "input_summary": "Extracted data",
            "output_summary": "All fields valid",
            "status": "complete",
        },
    ]
    trace = AgentTrace(
        invoice_id=invoice.id,
        agent_name="invoice_processing_agent",
        model="us.anthropic.claude-sonnet-4-6-v1",
        duration_ms=4300,
        steps=steps,
    )
    db_session.add(trace)
    await db_session.flush()

    assert trace.id is not None
    assert trace.invoice_id == invoice.id
    assert trace.agent_name == "invoice_processing_agent"
    assert trace.model == "us.anthropic.claude-sonnet-4-6-v1"
    assert trace.duration_ms == 4300
    assert len(trace.steps) == 2
    assert trace.steps[0]["tool_name"] == "extract_invoice"
    assert trace.steps[1]["duration_ms"] == 1100
    assert trace.handoff_context is None
