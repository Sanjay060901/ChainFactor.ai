/**
 * Demo/fallback data for when the backend is not running.
 * Each page uses these as fallback when API calls fail.
 */

export const DEMO_INVOICES = [
  {
    id: "inv-001",
    invoice_number: "INV-2025-0042",
    seller_name: "Tata Steel Ltd",
    buyer_name: "Reliance Industries",
    amount: 847500,
    risk_score: 82,
    status: "approved",
    created_at: "2025-01-15T10:30:00Z",
  },
  {
    id: "inv-002",
    invoice_number: "INV-2025-0041",
    seller_name: "Infosys Technologies",
    buyer_name: "Wipro Ltd",
    amount: 325000,
    risk_score: 91,
    status: "minted",
    created_at: "2025-01-14T14:20:00Z",
  },
  {
    id: "inv-003",
    invoice_number: "INV-2025-0040",
    seller_name: "Mahindra & Mahindra",
    buyer_name: "Bajaj Auto Ltd",
    amount: 1250000,
    risk_score: 45,
    status: "flagged",
    created_at: "2025-01-13T09:15:00Z",
  },
  {
    id: "inv-004",
    invoice_number: "INV-2025-0039",
    seller_name: "Hindustan Unilever",
    buyer_name: "ITC Limited",
    amount: 562000,
    risk_score: 78,
    status: "approved",
    created_at: "2025-01-12T16:45:00Z",
  },
  {
    id: "inv-005",
    invoice_number: "INV-2025-0038",
    seller_name: "Sun Pharma Industries",
    buyer_name: "Dr. Reddy's Labs",
    amount: 198000,
    risk_score: 25,
    status: "rejected",
    created_at: "2025-01-11T11:00:00Z",
  },
  {
    id: "inv-006",
    invoice_number: "INV-2025-0037",
    seller_name: "Larsen & Toubro",
    buyer_name: "Adani Enterprises",
    amount: 2100000,
    risk_score: 88,
    status: "minted",
    created_at: "2025-01-10T08:30:00Z",
  },
  {
    id: "inv-007",
    invoice_number: "INV-2025-0036",
    seller_name: "Asian Paints Ltd",
    buyer_name: "Berger Paints India",
    amount: 435000,
    risk_score: null,
    status: "processing",
    created_at: "2025-01-09T13:10:00Z",
  },
];

export const DEMO_DASHBOARD = {
  total_value: 5717500,
  active_invoices: 12,
  pending_invoices: 3,
  avg_risk_score: 76,
  approval_rate: 83,
  risk_distribution: { low: 67, medium: 22, high: 11 },
  monthly_volume: [
    { month: "Aug", count: 8, value: 1200000 },
    { month: "Sep", count: 14, value: 2100000 },
    { month: "Oct", count: 11, value: 1800000 },
    { month: "Nov", count: 19, value: 3400000 },
    { month: "Dec", count: 16, value: 2900000 },
    { month: "Jan", count: 12, value: 5717500 },
  ],
};

export function getDemoInvoiceDetail(id: string) {
  const base = DEMO_INVOICES.find((inv) => inv.id === id) || DEMO_INVOICES[0];
  return {
    ...base,
    nft_asset_id: base.status === "minted" ? 48291053 : null,
    risk_score: base.risk_score ?? 82,
    fraud_flags: base.risk_score !== null && base.risk_score < 40
      ? [{ layer: "Financial Consistency", detail: "Amount exceeds historical average by 3.2x" }]
      : [],
    risk_explanation:
      "Based on multi-signal analysis: GSTIN verified and active, CIBIL score 742 (Good), no duplicate invoices detected, HSN codes valid with correct GST rates, buyer payment history is positive. Overall risk assessment indicates a reliable transaction with standard monitoring recommended.",
    underwriting: {
      decision: base.status === "rejected" ? "rejected" : base.status === "flagged" ? "flagged" : "approved",
      reason:
        base.status === "rejected"
          ? "High risk score (25) with financial consistency flag. Recommend manual review before approval."
          : base.status === "flagged"
          ? "Medium risk (45). Amount exceeds typical range for this seller-buyer pair. Flagged for human review."
          : "All validation checks passed. Risk score 82 (Low). Auto-approved per Rule #1.",
      cross_validation: base.status !== "rejected",
    },
    extracted_data: {
      seller_name: base.seller_name,
      seller_gstin: "27AABCT1332L1ZV",
      buyer_name: base.buyer_name || "Reliance Industries",
      buyer_gstin: "27AABCR1718E1ZL",
      invoice_number: base.invoice_number,
      invoice_date: "2025-01-15",
      total_amount: base.amount * 0.85,
      tax_amount: base.amount * 0.15,
      grand_total: base.amount,
      due_date: "2025-02-14",
      risk_score: base.risk_score,
      gst_compliance: {
        compliant: base.status !== "rejected",
        summary: base.status !== "rejected" ? "HSN codes valid, GST rates match (18% IGST)" : "HSN mismatch detected in line item #3",
      },
      gstn_verification: {
        verified: true,
        status: "Active, matched with government records",
      },
      summary:
        "Invoice verified through 14-step AI pipeline. Document integrity confirmed, financial consistency validated, pattern analysis clean, entity verification complete, cross-references matched.",
    },
  };
}

export const DEMO_AUDIT_TRACES = [
  { step: 1, tool_name: "extract_invoice", name: "Extract Invoice Data", duration: 3.2, input: "PDF upload (847KB)", output: "Extracted 10 fields, 4 line items" },
  { step: 2, tool_name: "validate_fields", name: "Validate Fields", duration: 0.8, input: "10 extracted fields", output: "All mandatory fields present, formats valid" },
  { step: 3, tool_name: "validate_gst_compliance", name: "GST Compliance Check", duration: 1.1, input: "HSN: 7206, Rate: 18%", output: "HSN valid, GST rate matches (18% IGST)" },
  { step: 4, tool_name: "verify_gstn", name: "GSTIN Verification", duration: 2.4, input: "GSTIN: 27AABCT1332L1ZV", output: "Active, trade name matches, filing up to date" },
  { step: 5, tool_name: "check_fraud", name: "Fraud Detection (5-Layer)", duration: 4.7, input: "Invoice + historical data", output: "0 flags detected across 5 layers" },
  { step: 6, tool_name: "get_buyer_intel", name: "Buyer Intelligence", duration: 1.9, input: "Buyer GSTIN: 27AABCR1718E1ZL", output: "Payment history: 94% on-time, avg 12 days" },
  { step: 7, tool_name: "get_credit_score", name: "CIBIL Credit Score", duration: 2.1, input: "Seller PAN: AABCT1332L", output: "CIBIL: 742 (Good), credit utilization: 34%" },
  { step: 8, tool_name: "get_company_info", name: "MCA Company Info", duration: 1.6, input: "CIN: L27100MH1907PLC000260", output: "Active, incorporated 1907, authorized cap: ₹810Cr" },
  { step: 9, tool_name: "calculate_risk", name: "Risk Calculation", duration: 0.9, input: "5 signal inputs", output: "Composite score: 82/100 (Low Risk)" },
  { step: 10, tool_name: "generate_summary", name: "Generate Summary", duration: 1.4, input: "All processing results", output: "Summary generated with AI explanation" },
  { step: 11, tool_name: "cross_validate_outputs", name: "Cross-Validation", duration: 3.8, input: "10 tool outputs", output: "All outputs consistent, no contradictions" },
  { step: 12, tool_name: "underwriting_decision", name: "Underwriting Decision", duration: 2.2, input: "Risk: 82, Flags: 0, CIBIL: 742", output: "Decision: APPROVED (auto, Rule #1)" },
  { step: 13, tool_name: "log_decision", name: "Log Decision", duration: 0.3, input: "Decision payload", output: "Logged to audit trail, notified via WebSocket" },
  { step: 14, tool_name: "mint_nft", name: "Mint NFT", duration: 5.1, input: "ARC-69 metadata", output: "ASA #48291053 created on Algorand Testnet" },
];

export const DEMO_RULES = [
  {
    id: "rule-001",
    conditions: [
      { field: "risk_score", operator: ">", value: 70 },
      { field: "fraud_flags", operator: "==", value: 0 },
    ],
    action: "auto_approve",
    is_active: true,
    created_at: "2025-01-05T10:00:00Z",
  },
  {
    id: "rule-002",
    conditions: [
      { field: "invoice_amount", operator: ">", value: 2000000 },
    ],
    action: "flag_for_review",
    is_active: true,
    created_at: "2025-01-05T10:05:00Z",
  },
  {
    id: "rule-003",
    conditions: [
      { field: "cibil_score", operator: "<", value: 500 },
    ],
    action: "auto_reject",
    is_active: false,
    created_at: "2025-01-06T14:30:00Z",
  },
];

export const DEMO_NL_RESPONSES: Record<string, string> = {
  default:
    "Based on your portfolio: 12 active invoices worth ₹57.2L total. 83% approval rate with an average risk score of 76 (Low). 3 invoices pending review. Top seller: Tata Steel Ltd (₹8.5L). No high-risk flags in the last 7 days.",
  risk:
    "You have 1 high-risk invoice (INV-2025-0038 from Sun Pharma, risk score 25) that was rejected. 1 medium-risk invoice (INV-2025-0040 from Mahindra & Mahindra, risk score 45) is flagged for review. The remaining 5 invoices are low-risk (score > 70).",
  approved:
    "4 invoices approved this month: INV-2025-0042 (Tata Steel, ₹8.5L), INV-2025-0041 (Infosys, ₹3.3L), INV-2025-0039 (HUL, ₹5.6L), INV-2025-0037 (L&T, ₹21L). Combined value: ₹38.4L.",
};
