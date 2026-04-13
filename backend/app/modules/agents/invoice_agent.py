"""Invoice Processing Agent -- extracts, validates, and analyzes invoices.

Uses Sonnet 4.6 via Bedrock. Tools are registered in app/agents/tools/ and
added to the agent in create_invoice_processing_agent().

This agent handles steps 1-10 of the pipeline:
1. extract_invoice (Textract + Claude OCR)
2. validate_fields
3. validate_gst_compliance
4. verify_gstn
5. check_fraud (5-layer)
6. get_buyer_intel
7. get_credit_score (mock CIBIL)
8. get_company_info (mock MCA)
9. calculate_risk
10. generate_summary
11. mint_nft (ARC-69 NFT on Algorand testnet)
"""

from strands import Agent

from app.agents.tools.calculate_risk import _calculate_risk_tool
from app.agents.tools.check_fraud import check_fraud
from app.agents.tools.extract_invoice import extract_invoice
from app.agents.tools.generate_summary import _generate_summary_tool
from app.agents.tools.get_buyer_intel import _get_buyer_intel_tool
from app.agents.tools.get_company_info import get_company_info_tool
from app.agents.tools.get_credit_score import _get_credit_score_tool
from app.agents.tools.mint_nft import _mint_nft_tool
from app.agents.tools.validate_fields import validate_fields
from app.agents.tools.validate_gst_compliance import validate_gst_compliance
from app.agents.tools.verify_gstn import _verify_gstn_tool
from app.modules.agents.config import INVOICE_AGENT_CONFIG, get_model_for_agent

INVOICE_AGENT_SYSTEM_PROMPT = """You are the Invoice Processing Agent for ChainFactor AI, an AI-powered invoice financing platform for Indian SMEs on the Algorand blockchain.

Your role is to process uploaded invoices through a comprehensive analysis pipeline:

1. EXTRACT invoice data from PDF using OCR (Textract + Claude vision fallback)
2. VALIDATE all extracted fields (math checks, format validation, completeness)
3. CHECK GST compliance (HSN codes, tax rates, e-invoice requirements)
4. VERIFY seller and buyer GSTINs against the GST portal
5. DETECT fraud across 5 layers (document integrity, financial consistency, pattern analysis, entity verification, cross-reference)
6. GATHER buyer intelligence (payment history, average payment days)
7. CHECK credit score (CIBIL score for the buyer entity)
8. FETCH company information (MCA registration, incorporation status, paid-up capital)
9. CALCULATE multi-signal risk score (0-100, combining all signals)
10. GENERATE a summary of findings for the Underwriting Agent

IMPORTANT RULES:
- Process steps sequentially -- each step depends on previous outputs
- Always use the provided tools -- never fabricate data
- If a tool fails, report the failure clearly and continue with remaining steps
- Risk score must be between 0 (highest risk) and 100 (lowest risk)
- All amounts are in Indian Rupees (INR)
- GSTINs follow the format: 2-digit state code + 10-char PAN + 1-char entity + Z + check digit

After completing all 10 steps, hand off to the Underwriting Agent with the complete analysis context."""

# Pipeline tools in execution order (11 tools total).
# For tools with a 3-layer wrapper pattern, we register the @tool-decorated
# private function -- Strands needs the @tool decorator for registration.
INVOICE_AGENT_TOOLS: list = [
    extract_invoice,  # 1. OCR extraction (Textract + Claude fallback)
    validate_fields,  # 2. Field validation (math, format, completeness)
    validate_gst_compliance,  # 3. GST compliance (HSN, rates, e-invoice)
    _verify_gstn_tool,  # 4. GSTIN verification (mock GST portal)
    check_fraud,  # 5. 5-layer fraud detection
    _get_buyer_intel_tool,  # 6. Buyer payment history
    _get_credit_score_tool,  # 7. CIBIL credit score (mock)
    get_company_info_tool,  # 8. MCA company info (mock)
    _calculate_risk_tool,  # 9. Multi-signal risk scoring
    _generate_summary_tool,  # 10. Summary for Underwriting Agent
    _mint_nft_tool,  # 11. ARC-69 NFT minting on Algorand testnet
]


def create_invoice_processing_agent() -> Agent:
    """Create and return the Invoice Processing Agent."""
    config = INVOICE_AGENT_CONFIG
    model = get_model_for_agent(config)

    return Agent(
        model=model,
        name=config.name,
        description=config.description,
        system_prompt=INVOICE_AGENT_SYSTEM_PROMPT,
        tools=INVOICE_AGENT_TOOLS,
    )
