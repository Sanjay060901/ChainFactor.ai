"""Collection Agent -- proactive overdue invoice monitoring and reminders.

Uses Haiku 4.5 via Bedrock (lightweight model for cost efficiency).

DEFERRED TO ROUND 3 -- This module provides the agent configuration and
creation function but tools are not yet implemented. The agent will be
integrated with scheduled tasks (CloudWatch Events) and on-demand endpoints.

Planned tools (not yet implemented):
- get_overdue_invoices: fetch invoices past payment terms
- get_buyer_history: payment history for a specific buyer
- generate_reminder: create a payment reminder message
- suggest_escalation: recommend escalation actions
- scan_portfolio: daily portfolio-wide overdue scan
"""

from strands import Agent

from app.modules.agents.config import COLLECTION_AGENT_CONFIG, get_model_for_agent

COLLECTION_AGENT_SYSTEM_PROMPT = """You are the Collection Agent for ChainFactor AI, an AI-powered invoice financing platform for Indian SMEs on the Algorand blockchain.

Your role is to proactively monitor the invoice portfolio for overdue payments and assist with collection actions.

CAPABILITIES:
- Scan the portfolio for invoices past their payment terms
- Analyze buyer payment patterns and history
- Generate professional payment reminder messages
- Suggest escalation actions based on overdue duration and buyer behavior
- Prioritize collection actions by amount, age, and risk

RULES:
- Be professional and firm but not aggressive in reminder language
- Consider Indian business customs and payment practices
- Escalation thresholds: 30 days (gentle reminder), 60 days (firm follow-up), 90 days (escalation)
- All amounts in Indian Rupees (INR)
- Always include the invoice number and original due date in reminders
- Flag repeat defaulters for manual review
- Never threaten legal action without explicit human approval"""


def create_collection_agent() -> Agent:
    """Create and return the Collection Agent (Haiku, deferred).

    NOTE: Tools are empty -- this agent is not yet functional.
    It will be activated in Round 3.
    """
    config = COLLECTION_AGENT_CONFIG
    model = get_model_for_agent(config)

    return Agent(
        model=model,
        name=config.name,
        description=config.description,
        system_prompt=COLLECTION_AGENT_SYSTEM_PROMPT,
        tools=[],  # Deferred to Round 3
    )
