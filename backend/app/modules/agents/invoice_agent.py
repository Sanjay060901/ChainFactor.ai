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
"""

from strands import Agent

from app.modules.agents.config import SONNET_MODEL_ID, get_bedrock_model

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

# Tools will be added as they are implemented in Features 4.4-4.9
INVOICE_AGENT_TOOLS: list = []


def create_invoice_processing_agent() -> Agent:
    """Create and return the Invoice Processing Agent."""
    model = get_bedrock_model(SONNET_MODEL_ID)

    return Agent(
        model=model,
        name="invoice_processing_agent",
        description="Processes uploaded invoices through a 10-step analysis pipeline including OCR, validation, fraud detection, and risk scoring.",
        system_prompt=INVOICE_AGENT_SYSTEM_PROMPT,
        tools=INVOICE_AGENT_TOOLS,
    )
