"""Invoice request/response schemas."""

from datetime import datetime

from pydantic import BaseModel


class LineItem(BaseModel):
    description: str
    hsn_code: str
    quantity: int
    rate: float
    amount: float


class SellerBuyer(BaseModel):
    name: str
    gstin: str
    address: str | None = None


class ExtractedData(BaseModel):
    seller: SellerBuyer
    buyer: SellerBuyer
    invoice_number: str
    invoice_date: str
    due_date: str
    subtotal: float
    tax_amount: float
    tax_rate: float
    total_amount: float
    line_items: list[LineItem]


class ValidationResult(BaseModel):
    is_valid: bool
    errors: list[str]
    warnings: list[str]


class GSTComplianceResult(BaseModel):
    is_compliant: bool
    details: dict


class FraudLayer(BaseModel):
    name: str
    result: str
    detail: str
    confidence: float


class FraudDetectionResult(BaseModel):
    overall: str
    confidence: float
    flags: list[str]
    layers: list[FraudLayer]


class GSTINVerification(BaseModel):
    verified: bool
    status: str
    details: dict


class BuyerIntel(BaseModel):
    payment_history: str
    avg_days: int
    previous_count: int


class CreditScore(BaseModel):
    score: int
    rating: str


class CompanyInfo(BaseModel):
    status: str
    incorporated: str
    paid_up_capital: float


class RiskAssessment(BaseModel):
    score: int
    level: str
    explanation: str


class UnderwritingResult(BaseModel):
    decision: str
    rule_matched: str | None = None
    cross_validation: str
    reasoning: str


class NFTInfo(BaseModel):
    asset_id: int | None = None
    status: str | None = None
    explorer_url: str | None = None
    metadata: dict | None = None


class InvoiceUploadResponse(BaseModel):
    invoice_id: str
    status: str
    ws_url: str
    created_at: datetime


class InvoiceDetailResponse(BaseModel):
    id: str
    invoice_number: str
    status: str
    created_at: datetime
    extracted_data: ExtractedData | None = None
    validation: ValidationResult | None = None
    gst_compliance: GSTComplianceResult | None = None
    fraud_detection: FraudDetectionResult | None = None
    gstin_verification: GSTINVerification | None = None
    buyer_intel: BuyerIntel | None = None
    credit_score: CreditScore | None = None
    company_info: CompanyInfo | None = None
    risk_assessment: RiskAssessment | None = None
    underwriting: UnderwritingResult | None = None
    nft: NFTInfo | None = None


class InvoiceListItem(BaseModel):
    id: str
    invoice_number: str
    seller_name: str
    amount: float
    risk_score: int | None = None
    status: str
    created_at: datetime


class InvoiceListResponse(BaseModel):
    invoices: list[InvoiceListItem]
    total: int
    page: int
    limit: int
    pages: int


class NFTOptInRequest(BaseModel):
    wallet_address: str


class NFTOptInResponse(BaseModel):
    unsigned_txn: str  # base64-encoded unsigned AssetTransferTxn
    asset_id: int
    message: str


class NFTClaimRequest(BaseModel):
    wallet_address: str
    signed_optin_txn: str  # base64-encoded signed opt-in txn from user's wallet


class NFTClaimResponse(BaseModel):
    asset_id: int
    optin_txn_id: str
    transfer_txn_id: str
    status: str
    explorer_url: str


class ProcessingEvent(BaseModel):
    type: str
    step: int
    step_name: str
    agent: str
    status: str
    detail: str
    result: dict | None = None
    progress: float
    elapsed_ms: int


class PipelineCompleteEvent(BaseModel):
    type: str = "pipeline_complete"
    decision: str
    risk_score: int
    reason: str
    nft_asset_id: int | None = None
    invoice_id: str


class ProcessInvoiceResponse(BaseModel):
    invoice_id: str
    status: str
    ws_url: str
