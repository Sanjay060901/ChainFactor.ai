"""Underwriting Agent -- makes autonomous approval/rejection decisions.

Uses Sonnet 4.6 via Bedrock (NOT Opus -- Opus is reserved for NL query only).

This agent handles steps 11-14 of the pipeline:
11. cross_validate_outputs (verify consistency across all tool results)
12. underwriting_decision (approve/reject/flag based on rules + AI judgment)
13. log_decision (persist reasoning trace)
14. Hands back to Invoice Processing Agent for mint_nft (if approved)
"""

from strands import Agent

from app.agents.tools.approve_invoice import approve_invoice
from app.agents.tools.cross_validate_outputs import _cross_validate_outputs_tool
from app.agents.tools.flag_for_review import flag_for_review
from app.agents.tools.get_invoice_data import _get_invoice_data_tool
from app.agents.tools.get_seller_rules import _get_seller_rules_tool
from app.agents.tools.log_decision import log_decision
from app.agents.tools.reject_invoice import reject_invoice
from app.modules.agents.config import SONNET_MODEL_ID, get_bedrock_model

UNDERWRITING_AGENT_SYSTEM_PROMPT = """You are the Underwriting Agent for ChainFactor AI, an AI-powered invoice financing platform for Indian SMEs.

You receive the complete analysis context from the Invoice Processing Agent and make an autonomous underwriting decision.

Your role:
1. CROSS-VALIDATE all outputs from the Invoice Processing Agent for consistency
   - Do extracted amounts match validation results?
   - Does the GSTIN verification align with company info?
   - Are fraud detection results consistent with risk signals?
   - Flag any discrepancies

2. APPLY seller-defined rules (auto-approve/reject/flag thresholds)
   - Check invoice amount against seller's configured limits
   - Check risk score against seller's threshold
   - Check CIBIL score against seller's minimum
   - Check fraud flag count against seller's tolerance

3. MAKE a decision:
   - APPROVE: All rules pass, risk score above threshold, no fraud flags
   - REJECT: Critical fraud detected, very low risk score, failed GSTIN verification
   - FLAG FOR REVIEW: Borderline cases, minor discrepancies, seller rule conflicts

4. LOG the decision with full reasoning trace for auditability

IMPORTANT RULES:
- Use Sonnet for underwriting decisions (NOT Opus -- cost optimization)
- Every decision must include a reasoning trace explaining WHY
- Cross-validation must check at least 3 independent signals
- If cross-validation finds discrepancies, always FLAG FOR REVIEW (never auto-approve)
- After approval, hand back to the Invoice Processing Agent for NFT minting
- All decision logs must be persisted to the agent_traces table"""

UNDERWRITING_AGENT_TOOLS: list = [
    _cross_validate_outputs_tool,
    _get_seller_rules_tool,
    _get_invoice_data_tool,
    approve_invoice,
    reject_invoice,
    flag_for_review,
    log_decision,
]


def create_underwriting_agent() -> Agent:
    """Create and return the Underwriting Agent."""
    model = get_bedrock_model(SONNET_MODEL_ID)

    return Agent(
        model=model,
        name="underwriting_agent",
        description="Makes autonomous underwriting decisions (approve/reject/flag) with cross-validation and full reasoning traces.",
        system_prompt=UNDERWRITING_AGENT_SYSTEM_PROMPT,
        tools=UNDERWRITING_AGENT_TOOLS,
    )
