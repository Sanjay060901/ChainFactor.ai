"""Invoice API endpoints. Upload is real; other endpoints are stubs matching wireframes.md."""

import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import StreamingResponse

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.modules.auth.dependencies import get_current_user
from app.modules.invoices.service import (
    create_invoice_record,
    upload_to_s3,
    validate_upload,
)
from app.schemas.audit import (
    AgentTrace,
    AuditStep,
    AuditTrailResponse,
    Handoff,
)
from app.schemas.invoice import (
    BuyerIntel,
    CompanyInfo,
    CreditScore,
    ExtractedData,
    FraudDetectionResult,
    FraudLayer,
    GSTComplianceResult,
    GSTINVerification,
    InvoiceDetailResponse,
    InvoiceListItem,
    InvoiceListResponse,
    InvoiceUploadResponse,
    LineItem,
    NFTClaimRequest,
    NFTClaimResponse,
    NFTInfo,
    NFTOptInRequest,
    NFTOptInResponse,
    ProcessInvoiceResponse,
    RiskAssessment,
    SellerBuyer,
    UnderwritingResult,
    ValidationResult,
)

router = APIRouter(prefix="/invoices", tags=["invoices"])

STUB_NOW = datetime(2026, 3, 18, 10, 0, 0, tzinfo=timezone.utc)

STUB_EXTRACTED = ExtractedData(
    seller=SellerBuyer(
        name="Acme Technologies Pvt Ltd", gstin="27AABCU9603R1ZM", address="Mumbai, MH"
    ),
    buyer=SellerBuyer(
        name="TechBuild Solutions", gstin="29AABCT1234R1ZX", address="Bangalore, KA"
    ),
    invoice_number="INV-2026-001",
    invoice_date="2026-03-15",
    due_date="2026-04-14",
    subtotal=520000.0,
    tax_amount=93600.0,
    tax_rate=18.0,
    total_amount=613600.0,
    line_items=[
        LineItem(
            description="Cloud Server Hosting",
            hsn_code="998314",
            quantity=12,
            rate=25000,
            amount=300000,
        ),
        LineItem(
            description="Technical Support Hours",
            hsn_code="998313",
            quantity=40,
            rate=5500,
            amount=220000,
        ),
    ],
)

STUB_INVOICE_DETAIL = InvoiceDetailResponse(
    id="inv_stub_001",
    invoice_number="INV-2026-001",
    status="approved",
    created_at=STUB_NOW,
    extracted_data=STUB_EXTRACTED,
    validation=ValidationResult(is_valid=True, errors=[], warnings=[]),
    gst_compliance=GSTComplianceResult(
        is_compliant=True,
        details={"hsn_valid": True, "rate_match": True, "e_invoice": True},
    ),
    fraud_detection=FraudDetectionResult(
        overall="pass",
        confidence=97.0,
        flags=[],
        layers=[
            FraudLayer(
                name="Document Integrity",
                result="pass",
                detail="No tampering detected",
                confidence=98.5,
            ),
            FraudLayer(
                name="Financial Consistency",
                result="pass",
                detail="All amounts reconcile",
                confidence=97.0,
            ),
            FraudLayer(
                name="Pattern Analysis",
                result="pass",
                detail="Consistent with seller history",
                confidence=95.0,
            ),
            FraudLayer(
                name="Entity Verification",
                result="pass",
                detail="Both entities verified",
                confidence=99.0,
            ),
            FraudLayer(
                name="Cross-Reference",
                result="pass",
                detail="No duplicate invoices found",
                confidence=96.0,
            ),
        ],
    ),
    gstin_verification=GSTINVerification(
        verified=True,
        status="active",
        details={"trade_name": "Acme Technologies", "state": "Maharashtra"},
    ),
    buyer_intel=BuyerIntel(payment_history="reliable", avg_days=28, previous_count=8),
    credit_score=CreditScore(score=750, rating="good"),
    company_info=CompanyInfo(
        status="active", incorporated="2015", paid_up_capital=100000000.0
    ),
    risk_assessment=RiskAssessment(
        score=82,
        level="low",
        explanation="This invoice presents low risk. The seller has an active GSTIN with consistent filing history. The buyer has a CIBIL score of 750 and has paid all 8 previous invoices on time. GST rates match the applicable slab for HSN 998314. No fraud indicators detected across all 5 layers.",
    ),
    underwriting=UnderwritingResult(
        decision="approved",
        rule_matched="Approve invoices under 10L with risk score > 80",
        cross_validation="passed",
        reasoning="Invoice meets Rule 2 criteria. Risk score of 82 exceeds threshold of 80. CIBIL score 750 exceeds threshold. All fraud checks passed.",
    ),
    nft=NFTInfo(
        asset_id=12345678,
        status="minted",
        explorer_url="https://testnet.explorer.perawallet.app/asset/12345678/",
        metadata={"standard": "arc69", "invoice_id": "inv_stub_001", "risk_score": 82},
    ),
)


# ---------------------------------------------------------------------------
# Helper: load invoice and verify ownership (IDOR prevention)
# ---------------------------------------------------------------------------


async def _get_invoice_for_user(db: AsyncSession, invoice_id: str, user_id):
    """Load invoice from DB and verify it belongs to the requesting user.

    Args:
        db:         Async SQLAlchemy session.
        invoice_id: Invoice UUID string from the URL path parameter.
        user_id:    UUID of the authenticated user (from JWT).

    Returns:
        The Invoice ORM instance.

    Raises:
        HTTPException 404: If the invoice does not exist or belongs to a
                           different user (IDOR prevention -- same response
                           for both cases to avoid enumeration).
    """
    from sqlalchemy import select

    from app.models.invoice import Invoice

    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id, Invoice.user_id == user_id)
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


# ---------------------------------------------------------------------------
# Upload endpoint
# ---------------------------------------------------------------------------


@router.post("/upload", response_model=InvoiceUploadResponse)
async def upload_invoice(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a PDF invoice. Validates, stores in S3, creates DB record."""
    # DEMO_MODE: return stub response (no S3, no DB write)
    if settings.DEMO_MODE:
        return InvoiceUploadResponse(
            invoice_id="inv_stub_001",
            status="uploaded",
            ws_url="/ws/processing/inv_stub_001",
            created_at=STUB_NOW,
        )

    # Validate file (PDF only, max 5MB)
    file_bytes = await validate_upload(file)

    # Build S3 key: invoices/{user_id}/{invoice_id}/{filename}
    import uuid as _uuid

    invoice_id = _uuid.uuid4()
    s3_key = (
        f"{settings.S3_INVOICE_PREFIX}{current_user.id}/{invoice_id}/{file.filename}"
    )
    await upload_to_s3(file_bytes, s3_key=s3_key)

    # Create DB record
    invoice = await create_invoice_record(
        db=db,
        user=current_user,
        file_name=file.filename or "unknown.pdf",
        s3_key=s3_key,
    )

    return InvoiceUploadResponse(
        invoice_id=str(invoice.id),
        status="uploaded",
        ws_url=f"/ws/processing/{invoice.id}",
        created_at=invoice.created_at,
    )


# ---------------------------------------------------------------------------
# List invoices
# ---------------------------------------------------------------------------


@router.get("", response_model=InvoiceListResponse)
async def list_invoices(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    status: str | None = None,
    risk_level: str | None = None,
    sort: str = "-created_at",
    search: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if settings.DEMO_MODE:
        stub_invoices = [
            InvoiceListItem(
                id="inv_stub_001",
                invoice_number="INV-2026-001",
                seller_name="Acme Technologies",
                amount=613600,
                risk_score=82,
                status="approved",
                created_at=STUB_NOW,
            ),
            InvoiceListItem(
                id="inv_stub_002",
                invoice_number="INV-2026-002",
                seller_name="TechCo Solutions",
                amount=310000,
                risk_score=45,
                status="flagged",
                created_at=STUB_NOW,
            ),
            InvoiceListItem(
                id="inv_stub_003",
                invoice_number="INV-2026-003",
                seller_name="BuildRight Infra",
                amount=800000,
                risk_score=91,
                status="minted",
                created_at=STUB_NOW,
            ),
            InvoiceListItem(
                id="inv_stub_004",
                invoice_number="INV-2026-004",
                seller_name="FakeCorp Ltd",
                amount=210000,
                risk_score=12,
                status="rejected",
                created_at=STUB_NOW,
            ),
        ]
        return InvoiceListResponse(
            invoices=stub_invoices,
            total=4,
            page=page,
            limit=limit,
            pages=1,
        )

    # Real DB query path
    import math

    from sqlalchemy import func, select

    from app.models.invoice import Invoice

    # Base query: only current user's invoices (IDOR prevention)
    query = select(Invoice).where(Invoice.user_id == current_user.id)
    count_query = (
        select(func.count())
        .select_from(Invoice)
        .where(Invoice.user_id == current_user.id)
    )

    # Filter by status
    if status:
        query = query.where(Invoice.status == status)
        count_query = count_query.where(Invoice.status == status)

    # Filter by risk_level: low>=70, medium 40-69, high<40
    if risk_level:
        if risk_level == "low":
            query = query.where(Invoice.risk_score >= 70)
            count_query = count_query.where(Invoice.risk_score >= 70)
        elif risk_level == "medium":
            query = query.where(Invoice.risk_score >= 40, Invoice.risk_score < 70)
            count_query = count_query.where(
                Invoice.risk_score >= 40, Invoice.risk_score < 70
            )
        elif risk_level == "high":
            query = query.where(Invoice.risk_score < 40)
            count_query = count_query.where(Invoice.risk_score < 40)

    # Search by invoice_number (case-insensitive)
    if search:
        query = query.where(Invoice.invoice_number.ilike(f"%{search}%"))
        count_query = count_query.where(Invoice.invoice_number.ilike(f"%{search}%"))

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    pages = math.ceil(total / limit) if total > 0 else 0

    # Sorting
    descending = sort.startswith("-")
    sort_field = sort.lstrip("-")
    sort_column = getattr(Invoice, sort_field, Invoice.created_at)
    if descending:
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    invoices = result.scalars().all()

    items = [
        InvoiceListItem(
            id=str(inv.id),
            invoice_number=inv.invoice_number,
            seller_name=(inv.extracted_data or {})
            .get("seller", {})
            .get("name", "Unknown"),
            amount=(inv.extracted_data or {}).get("total_amount", 0.0),
            risk_score=inv.risk_score,
            status=inv.status,
            created_at=inv.created_at,
        )
        for inv in invoices
    ]

    return InvoiceListResponse(
        invoices=items,
        total=total,
        page=page,
        limit=limit,
        pages=pages,
    )


# ---------------------------------------------------------------------------
# Process endpoint -- must come BEFORE /{invoice_id} to avoid route shadowing
# ---------------------------------------------------------------------------


@router.post(
    "/{invoice_id}/process", response_model=ProcessInvoiceResponse, status_code=202
)
async def process_invoice(
    invoice_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger AI pipeline processing for an uploaded invoice.

    Returns 202 Accepted immediately and launches the 14-step pipeline as a
    background task.  The client should connect to ws_url to receive real-time
    progress events.

    Raises:
        HTTPException 404: Invoice not found or belongs to another user.
        HTTPException 409: Invoice is not in 'uploaded' state (already
                           processing, approved, rejected, etc.).
    """
    invoice = await _get_invoice_for_user(db, invoice_id, current_user.id)

    if invoice.status != "uploaded":
        raise HTTPException(
            status_code=409,
            detail=f"Invoice cannot be processed (current status: {invoice.status})",
        )

    # Launch pipeline as a non-blocking background task.
    # asyncio.create_task schedules the coroutine on the running event loop
    # without awaiting it, so this endpoint returns immediately.
    from app.modules.agents.pipeline import run_invoice_pipeline

    asyncio.create_task(run_invoice_pipeline(invoice=invoice, db=db))

    return ProcessInvoiceResponse(
        invoice_id=str(invoice.id),
        status="processing",
        ws_url=f"/ws/processing/{invoice.id}",
    )


# ---------------------------------------------------------------------------
# Invoice detail (stub -- real DB query comes in a future task)
# ---------------------------------------------------------------------------


@router.get("/{invoice_id}", response_model=InvoiceDetailResponse)
async def get_invoice(
    invoice_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get invoice detail from DB with IDOR prevention."""
    invoice = await _get_invoice_for_user(db, invoice_id, current_user.id)

    # Build response from DB columns (JSONB fields populated by pipeline)
    extracted = invoice.extracted_data or {}
    seller_data = extracted.get("seller", {})
    buyer_data = extracted.get("buyer", {})

    extracted_data = ExtractedData(
        seller=SellerBuyer(
            name=seller_data.get("name", "Unknown"),
            gstin=seller_data.get("gstin", ""),
            address=seller_data.get("address", ""),
        ),
        buyer=SellerBuyer(
            name=buyer_data.get("name", "Unknown"),
            gstin=buyer_data.get("gstin", ""),
            address=buyer_data.get("address", ""),
        ),
        invoice_number=extracted.get("invoice_number", invoice.invoice_number),
        invoice_date=extracted.get("invoice_date", ""),
        due_date=extracted.get("due_date", ""),
        subtotal=extracted.get("subtotal", 0),
        tax_amount=extracted.get("tax_amount", 0),
        tax_rate=extracted.get("tax_rate", 0),
        total_amount=extracted.get("total_amount", 0),
        line_items=[
            LineItem(**item) for item in extracted.get("line_items", [])
        ],
    )

    # Validation
    val = invoice.validation_result or {}
    validation = ValidationResult(
        is_valid=val.get("is_valid", True),
        errors=val.get("errors", []),
        warnings=val.get("warnings", []),
    )

    # GST Compliance
    gst = invoice.gst_compliance or {}
    gst_compliance = GSTComplianceResult(
        is_compliant=gst.get("is_compliant", True),
        details=gst.get("details", {}),
    )

    # Fraud Detection
    fraud = invoice.fraud_detection or {}
    fraud_layers = [
        FraudLayer(
            name=layer.get("name", ""),
            result=layer.get("result", "pass"),
            detail=layer.get("detail", ""),
            confidence=layer.get("confidence", 0),
        )
        for layer in fraud.get("layers", [])
    ]
    fraud_detection = FraudDetectionResult(
        overall=fraud.get("overall", "pass"),
        confidence=fraud.get("confidence", 0),
        flags=fraud.get("flags", []),
        layers=fraud_layers,
    )

    # GSTIN Verification
    gstn = invoice.gstin_verification or {}
    gstin_verification = GSTINVerification(
        verified=gstn.get("verified", False),
        status=gstn.get("status", "unknown"),
        details=gstn.get("details", {}),
    )

    # Buyer Intel
    bi = invoice.buyer_intel or {}
    buyer_intel = BuyerIntel(
        payment_history=bi.get("payment_history", "unknown"),
        avg_days=bi.get("avg_days", 0),
        previous_count=bi.get("previous_count", 0),
    )

    # Credit Score
    cs = invoice.credit_score or {}
    credit_score = CreditScore(
        score=cs.get("score", 0),
        rating=cs.get("rating", "unknown"),
    )

    # Company Info
    ci = invoice.company_info or {}
    company_info = CompanyInfo(
        status=ci.get("status", "unknown"),
        incorporated=ci.get("incorporated", ""),
        paid_up_capital=ci.get("paid_up_capital", 0),
    )

    # Risk Assessment
    ra = invoice.risk_assessment or {}
    risk_assessment = RiskAssessment(
        score=ra.get("score", invoice.risk_score or 0),
        level=ra.get("level", "unknown"),
        explanation=ra.get("explanation", invoice.ai_explanation or ""),
    )

    # Underwriting
    uw = invoice.underwriting or {}
    underwriting = UnderwritingResult(
        decision=uw.get("decision", invoice.status),
        rule_matched=uw.get("rule_matched", ""),
        cross_validation=uw.get("cross_validation", ""),
        reasoning=uw.get("reasoning", ""),
    )

    # NFT Info
    nft_info = None
    if invoice.nft_record:
        nft = invoice.nft_record
        nft_info = NFTInfo(
            asset_id=nft.asset_id,
            status=nft.status,
            explorer_url=f"{settings.PERA_EXPLORER_BASE_URL}/asset/{nft.asset_id}/" if nft.asset_id else "",
            metadata=nft.arc69_metadata or {},
        )

    return InvoiceDetailResponse(
        id=str(invoice.id),
        invoice_number=invoice.invoice_number,
        status=invoice.status,
        created_at=invoice.created_at,
        extracted_data=extracted_data,
        validation=validation,
        gst_compliance=gst_compliance,
        fraud_detection=fraud_detection,
        gstin_verification=gstin_verification,
        buyer_intel=buyer_intel,
        credit_score=credit_score,
        company_info=company_info,
        risk_assessment=risk_assessment,
        underwriting=underwriting,
        nft=nft_info,
    )


# ---------------------------------------------------------------------------
# SSE stream (stub)
# ---------------------------------------------------------------------------


@router.get("/{invoice_id}/stream")
async def stream_invoice_processing(invoice_id: str):
    """SSE fallback for real-time processing events."""
    import json

    async def event_generator():
        steps = [
            {
                "step": 1,
                "step_name": "extract_invoice",
                "detail": "Extracting data from PDF using Textract...",
            },
            {
                "step": 2,
                "step_name": "validate_fields",
                "detail": "Validating 23 extracted fields...",
            },
            {
                "step": 3,
                "step_name": "validate_gst_compliance",
                "detail": "Checking HSN codes and GST rates...",
            },
            {
                "step": 4,
                "step_name": "verify_gstn",
                "detail": "Verifying GSTIN 27AABCU9603R1ZM...",
            },
            {
                "step": 5,
                "step_name": "check_fraud",
                "detail": "Running 5-layer fraud detection...",
            },
            {
                "step": 6,
                "step_name": "get_buyer_intel",
                "detail": "Analyzing buyer payment history...",
            },
            {
                "step": 7,
                "step_name": "get_credit_score",
                "detail": "Checking CIBIL credit score...",
            },
            {
                "step": 8,
                "step_name": "get_company_info",
                "detail": "Fetching MCA company data...",
            },
            {
                "step": 9,
                "step_name": "calculate_risk",
                "detail": "Calculating multi-signal risk score...",
            },
            {
                "step": 10,
                "step_name": "generate_summary",
                "detail": "Generating invoice summary for NFT...",
            },
            {
                "step": 11,
                "step_name": "cross_validate_outputs",
                "detail": "Cross-validating all agent outputs...",
            },
            {
                "step": 12,
                "step_name": "underwriting_decision",
                "detail": "Making autonomous approval decision...",
            },
            {
                "step": 13,
                "step_name": "log_decision",
                "detail": "Logging decision and reasoning trace...",
            },
            {
                "step": 14,
                "step_name": "mint_nft",
                "detail": "Minting ARC-69 NFT on Algorand testnet...",
            },
        ]
        for s in steps:
            event = {
                "type": "step_complete",
                "step": s["step"],
                "step_name": s["step_name"],
                "agent": "invoice_processing" if s["step"] <= 10 else "underwriting",
                "status": "complete",
                "detail": s["detail"],
                "result": {},
                "progress": round(s["step"] / 14, 2),
                "elapsed_ms": s["step"] * 7000,
            }
            yield f"data: {json.dumps(event)}\n\n"
            await asyncio.sleep(0.5)

        final = {
            "type": "pipeline_complete",
            "decision": "approved",
            "risk_score": 82,
            "reason": "Auto-approved: meets Rule 2 criteria",
            "nft_asset_id": 12345678,
            "invoice_id": invoice_id,
        }
        yield f"data: {json.dumps(final)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/{invoice_id}/nft/opt-in", response_model=NFTOptInResponse)
async def nft_opt_in(
    invoice_id: str,
    body: NFTOptInRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return unsigned ASA opt-in transaction for the user to sign.

    The client must sign the returned transaction and submit it to the
    Algorand network before claiming the NFT.

    Args:
        invoice_id:   Invoice UUID from the URL path.
        body:         Request body containing the user's wallet address.
        current_user: Authenticated user (injected by Cognito JWT middleware).
        db:           Async database session.

    Returns:
        NFTOptInResponse with base64 unsigned_txn, asset_id, and a message.

    Raises:
        HTTPException 404: Invoice not found or belongs to another user.
        HTTPException 409: Invoice is not yet approved.
        HTTPException 404: NFT not yet minted for this invoice.
    """
    invoice = await _get_invoice_for_user(db, invoice_id, current_user.id)

    if invoice.status != "approved":
        raise HTTPException(
            status_code=409,
            detail="Invoice must be approved before opt-in",
        )

    nft = invoice.nft_record
    if not nft or not nft.asset_id:
        raise HTTPException(
            status_code=404,
            detail="NFT not yet minted for this invoice",
        )

    from app.modules.invoices.nft_service import build_optin_txn

    unsigned_txn = build_optin_txn(
        wallet_address=body.wallet_address,
        asset_id=nft.asset_id,
    )

    return NFTOptInResponse(
        unsigned_txn=unsigned_txn,
        asset_id=nft.asset_id,
        message=(
            f"Sign this transaction to opt-in to ASA {nft.asset_id}. "
            "This requires 0.1 ALGO MBR."
        ),
    )


@router.post("/{invoice_id}/nft/claim", response_model=NFTClaimResponse)
async def nft_claim(
    invoice_id: str,
    body: NFTClaimRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit signed opt-in txn, then transfer NFT to user wallet.

    Args:
        invoice_id:   Invoice UUID from the URL path.
        body:         Request body with wallet_address and signed_optin_txn.
        current_user: Authenticated user (injected by Cognito JWT middleware).
        db:           Async database session.

    Returns:
        NFTClaimResponse with asset_id, optin_txn_id, transfer_txn_id, status,
        and explorer_url.

    Raises:
        HTTPException 404: Invoice not found or belongs to another user.
        HTTPException 409: NFT not available (not yet minted or already claimed).
    """
    from app.modules.invoices.nft_service import submit_signed_txn, transfer_nft

    invoice = await _get_invoice_for_user(db, invoice_id, current_user.id)

    nft = invoice.nft_record
    if not nft or nft.status != "minted":
        raise HTTPException(status_code=409, detail="NFT not available for claim")

    # 1. Submit user's signed opt-in transaction
    optin_txid = await submit_signed_txn(body.signed_optin_txn)
    nft.opt_in_txn_id = optin_txid
    nft.status = "opt_in_pending"
    await db.commit()

    # 2. Transfer ASA from app wallet to user wallet
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


@router.get("/{invoice_id}/audit-trail", response_model=AuditTrailResponse)
async def get_audit_trail(
    invoice_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get audit trail from DB agent_traces table."""
    from sqlalchemy import select as sa_select
    from app.models.agent_trace import AgentTrace as AgentTraceModel

    invoice = await _get_invoice_for_user(db, invoice_id, current_user.id)

    result = await db.execute(
        sa_select(AgentTraceModel)
        .where(AgentTraceModel.invoice_id == invoice.id)
        .order_by(AgentTraceModel.created_at)
    )
    traces = result.scalars().all()

    agents = []
    total_duration = 0
    for trace in traces:
        steps_data = trace.steps or []
        audit_steps = [
            AuditStep(
                step_number=s.get("step_number", i + 1),
                tool_name=s.get("tool_name", ""),
                started_at=s.get("started_at", ""),
                duration_ms=s.get("duration_ms", 0),
                input_summary=s.get("input_summary", ""),
                output_summary=s.get("output_summary", ""),
                result=s.get("result", {}),
                status=s.get("status", "success"),
            )
            for i, s in enumerate(steps_data)
        ]
        agents.append(
            AgentTrace(
                name=trace.agent_name,
                model=trace.model or "sonnet-4.6",
                started_at=str(trace.created_at) if trace.created_at else "",
                duration_ms=trace.duration_ms or 0,
                steps=audit_steps,
            )
        )
        total_duration += trace.duration_ms or 0

    handoff_data = []
    for trace in traces:
        hc = trace.handoff_context
        if hc and isinstance(hc, dict) and hc.get("from_agent"):
            handoff_data.append(
                Handoff(
                    from_agent=hc.get("from_agent", ""),
                    to_agent=hc.get("to_agent", ""),
                    context_keys=hc.get("context_keys", []),
                )
            )

    return AuditTrailResponse(
        invoice_id=invoice_id,
        total_duration_ms=total_duration,
        agents=agents,
        handoffs=handoff_data,
    )
