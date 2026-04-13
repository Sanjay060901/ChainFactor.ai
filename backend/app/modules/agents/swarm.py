"""Strands Swarm: orchestrates Invoice Processing + Underwriting agents.

The swarm auto-injects handoff_to_agent tools so agents can hand off
to each other. Agents do NOT share conversation history -- context must
be passed explicitly via the handoff.

Usage:
    swarm = create_invoice_swarm()
    result = await swarm.stream_async("Process invoice INV-2026-001")
"""

from strands.multiagent.swarm import Swarm

from app.modules.agents.config import (
    SWARM_EXECUTION_TIMEOUT,
    SWARM_MAX_HANDOFFS,
    SWARM_MAX_ITERATIONS,
    SWARM_NODE_TIMEOUT,
)
from app.modules.agents.invoice_agent import create_invoice_processing_agent
from app.modules.agents.underwriting_agent import create_underwriting_agent


def create_invoice_swarm() -> Swarm:
    """Create a 2-agent swarm for the invoice processing pipeline.

    Flow: Invoice Processing Agent -> Underwriting Agent -> back for NFT mint
    """
    invoice_agent = create_invoice_processing_agent()
    underwriting_agent = create_underwriting_agent()

    return Swarm(
        nodes=[invoice_agent, underwriting_agent],
        entry_point=invoice_agent,
        max_handoffs=SWARM_MAX_HANDOFFS,
        max_iterations=SWARM_MAX_ITERATIONS,
        execution_timeout=SWARM_EXECUTION_TIMEOUT,
        node_timeout=SWARM_NODE_TIMEOUT,
    )
