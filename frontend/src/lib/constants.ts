/**
 * Application-wide constants.
 */

export const APP_NAME = "ChainFactor AI";

export const PERA_EXPLORER_BASE = "https://testnet.explorer.perawallet.app";

export const ALGORAND_NETWORK = "testnet";

export const RISK_LEVELS = {
  LOW: { min: 70, label: "Low Risk", color: "text-green-600" },
  MEDIUM: { min: 40, label: "Medium Risk", color: "text-yellow-600" },
  HIGH: { min: 0, label: "High Risk", color: "text-red-600" },
} as const;

export const INVOICE_STATUSES = {
  processing: { label: "Processing", color: "bg-blue-100 text-blue-800" },
  approved: { label: "Approved", color: "bg-green-100 text-green-800" },
  rejected: { label: "Rejected", color: "bg-red-100 text-red-800" },
  flagged: { label: "Flagged", color: "bg-yellow-100 text-yellow-800" },
  minted: { label: "Minted", color: "bg-purple-100 text-purple-800" },
  claimed: { label: "Claimed", color: "bg-indigo-100 text-indigo-800" },
} as const;

export const PROCESSING_STEPS = [
  { step: 1, name: "extract_invoice", label: "Extract Invoice Data", agent: "invoice_processing" },
  { step: 2, name: "validate_fields", label: "Validate Fields", agent: "invoice_processing" },
  { step: 3, name: "validate_gst_compliance", label: "GST Compliance Check", agent: "invoice_processing" },
  { step: 4, name: "verify_gstn", label: "GSTIN Verification", agent: "invoice_processing" },
  { step: 5, name: "check_fraud", label: "Fraud Detection (5-Layer)", agent: "invoice_processing" },
  { step: 6, name: "get_buyer_intel", label: "Buyer Intelligence", agent: "invoice_processing" },
  { step: 7, name: "get_credit_score", label: "CIBIL Credit Score", agent: "invoice_processing" },
  { step: 8, name: "get_company_info", label: "MCA Company Info", agent: "invoice_processing" },
  { step: 9, name: "calculate_risk", label: "Risk Calculation", agent: "invoice_processing" },
  { step: 10, name: "generate_summary", label: "Generate Summary", agent: "invoice_processing" },
  { step: 11, name: "cross_validate_outputs", label: "Cross-Validation", agent: "underwriting" },
  { step: 12, name: "underwriting_decision", label: "Underwriting Decision", agent: "underwriting" },
  { step: 13, name: "log_decision", label: "Log Decision", agent: "underwriting" },
  { step: 14, name: "mint_nft", label: "Mint NFT", agent: "invoice_processing" },
] as const;
