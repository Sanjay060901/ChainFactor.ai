"""Invoice API endpoints. Upload is real; other endpoints are stubs matching wireframes.md."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Query, UploadFile
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
    RiskAssessment,
    SellerBuyer,
    UnderwritingResult,
    ValidationResult,
)
from app.schemas.audit import (
    AgentTrace,
    AuditStep,
    AuditTrailResponse,
    Handoff,
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
                name="Document Integrity", result="pass", detail="No tampering detected"
            ),
            FraudLayer(
                name="Financial Consistency",
                result="pass",
                detail="All amounts reconcile",
            ),
            FraudLayer(
                name="Pattern Analysis",
                result="pass",
                detail="Consistent with seller history",
            ),
            FraudLayer(
                name="Entity Verification",
                result="pass",
                detail="Both entities verified",
            ),
            FraudLayer(
                name="Cross-Reference",
                result="pass",
                detail="No duplicate invoices found",
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


@router.get("", response_model=InvoiceListResponse)
async def list_invoices(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    status: str | None = None,
    risk_level: str | None = None,
    sort: str = "-created_at",
    search: str | None = None,
):
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


@router.get("/{invoice_id}", response_model=InvoiceDetailResponse)
async def get_invoice(invoice_id: str):
    return STUB_INVOICE_DETAIL


@router.get("/{invoice_id}/stream")
async def stream_invoice_processing(invoice_id: str):
    """SSE fallback for real-time processing events."""
    import asyncio
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
async def nft_opt_in(invoice_id: str, body: NFTOptInRequest):
    return NFTOptInResponse(txn_id="stub_txn_optin_001", status="opted_in")


@router.post("/{invoice_id}/nft/claim", response_model=NFTClaimResponse)
async def nft_claim(invoice_id: str, body: NFTClaimRequest):
    return NFTClaimResponse(
        txn_id="stub_txn_claim_001",
        asset_id=12345678,
        status="claimed",
        explorer_url="https://testnet.explorer.perawallet.app/asset/12345678/",
    )


@router.get("/{invoice_id}/audit-trail", response_model=AuditTrailResponse)
async def get_audit_trail(invoice_id: str):
    return AuditTrailResponse(
        invoice_id=invoice_id,
        total_duration_ms=102000,
        agents=[
            AgentTrace(
                name="Invoice Processing Agent",
                model="sonnet-4.6",
                started_at="2026-03-18T10:00:00Z",
                duration_ms=72000,
                steps=[
                    AuditStep(
                        step_number=1,
                        tool_name="extract_invoice",
                        started_at="2026-03-18T10:00:00Z",
                        duration_ms=3200,
                        input_summary="invoice_march_2026.pdf (1.2 MB)",
                        output_summary="23 fields extracted, 2 line items",
                        result={"fields_count": 23, "confidence": 98.2},
                        status="success",
                    ),
                    AuditStep(
                        step_number=2,
                        tool_name="validate_fields",
                        started_at="2026-03-18T10:00:03Z",
                        duration_ms=1100,
                        input_summary="23 extracted fields",
                        output_summary="All fields valid",
                        result={"valid": 23, "invalid": 0},
                        status="success",
                    ),
                    AuditStep(
                        step_number=3,
                        tool_name="validate_gst_compliance",
                        started_at="2026-03-18T10:00:04Z",
                        duration_ms=800,
                        input_summary="2 HSN codes, 18% rate",
                        output_summary="GST compliant",
                        result={"compliant": True},
                        status="success",
                    ),
                ],
            ),
            AgentTrace(
                name="Underwriting Agent",
                model="sonnet-4.6",
                started_at="2026-03-18T10:01:12Z",
                duration_ms=30000,
                steps=[
                    AuditStep(
                        step_number=11,
                        tool_name="cross_validate_outputs",
                        started_at="2026-03-18T10:01:12Z",
                        duration_ms=2400,
                        input_summary="All tool outputs",
                        output_summary="All consistent",
                        result={"discrepancies": 0},
                        status="success",
                    ),
                    AuditStep(
                        step_number=12,
                        tool_name="underwriting_decision",
                        started_at="2026-03-18T10:01:15Z",
                        duration_ms=1800,
                        input_summary="Risk 82, CIBIL 750, 0 flags",
                        output_summary="AUTO-APPROVED (Rule 2)",
                        result={"decision": "approved", "rule": 2},
                        status="success",
                    ),
                ],
            ),
        ],
        handoffs=[
            Handoff(
                from_agent="Invoice Processing Agent",
                to_agent="Underwriting Agent",
                context_keys=[
                    "extracted_data",
                    "risk_score",
                    "fraud_result",
                    "gst_compliance",
                    "gstin_status",
                    "credit_score",
                    "company_info",
                ],
            ),
        ],
    )
