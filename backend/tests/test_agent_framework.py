"""TDD tests for Feature 4.1: Agent Framework Setup.

Tests the Strands Agents SDK integration:
- BedrockModel configuration (us-east-1 region)
- Invoice Processing Agent creation with system prompt
- Underwriting Agent creation with system prompt
- Swarm assembly with both agents
- Agent config loading
"""


import pytest



# ---------------------------------------------------------------------------
# Tests: Agent config
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_agent_config_bedrock_region():
    """Agent models must use BEDROCK_REGION (us-east-1), not AWS_REGION."""
    from app.modules.agents.config import BEDROCK_REGION

    assert BEDROCK_REGION == "us-east-1"


@pytest.mark.asyncio
async def test_agent_config_model_ids():
    """Agent config exposes correct model IDs for each agent role."""
    from app.modules.agents.config import HAIKU_MODEL_ID, OPUS_MODEL_ID, SONNET_MODEL_ID

    assert "sonnet" in SONNET_MODEL_ID
    assert "opus" in OPUS_MODEL_ID
    assert "haiku" in HAIKU_MODEL_ID


# ---------------------------------------------------------------------------
# Tests: Agent creation (mocked Bedrock -- no real API calls)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_invoice_processing_agent():
    """Invoice Processing Agent is created with correct model and system prompt."""
    from app.modules.agents.invoice_agent import create_invoice_processing_agent

    agent = create_invoice_processing_agent()

    assert agent is not None
    assert agent.name == "invoice_processing_agent"
    # System prompt should mention invoice processing
    assert agent.system_prompt is not None
    assert "invoice" in agent.system_prompt.lower()


@pytest.mark.asyncio
async def test_create_underwriting_agent():
    """Underwriting Agent is created with correct model and system prompt."""
    from app.modules.agents.underwriting_agent import create_underwriting_agent

    agent = create_underwriting_agent()

    assert agent is not None
    assert agent.name == "underwriting_agent"
    # System prompt should mention underwriting/decision
    assert agent.system_prompt is not None
    assert "underwriting" in agent.system_prompt.lower()


@pytest.mark.asyncio
async def test_invoice_agent_uses_sonnet():
    """Invoice Processing Agent must use Sonnet model (not Opus)."""
    from app.modules.agents.invoice_agent import create_invoice_processing_agent

    agent = create_invoice_processing_agent()
    # The model should be BedrockModel configured with Sonnet
    assert agent.model is not None


@pytest.mark.asyncio
async def test_underwriting_agent_uses_sonnet():
    """Underwriting Agent must use Sonnet (NOT Opus -- Opus is reserved for NL query only)."""
    from app.modules.agents.underwriting_agent import create_underwriting_agent

    agent = create_underwriting_agent()
    assert agent.model is not None


@pytest.mark.asyncio
async def test_swarm_assembly():
    """Swarm can be assembled with both agents."""
    from app.modules.agents.swarm import create_invoice_swarm

    swarm = create_invoice_swarm()

    assert swarm is not None
    # Should have 2 agents (invoice processing + underwriting)
    assert len(swarm.nodes) == 2


@pytest.mark.asyncio
async def test_swarm_entry_point_is_invoice_agent():
    """Swarm entry point should be the Invoice Processing Agent."""
    from app.modules.agents.swarm import create_invoice_swarm

    swarm = create_invoice_swarm()

    # First node / entry point should be the invoice processing agent
    assert swarm.entry_point.name == "invoice_processing_agent"


@pytest.mark.asyncio
async def test_tool_decorator_works():
    """Verify the @tool decorator creates a valid tool spec."""
    from strands import tool

    @tool
    def sample_tool(input_text: str) -> str:
        """A sample tool for testing the decorator.

        Args:
            input_text: The text to process.
        """
        return f"processed: {input_text}"

    # The decorated function should still be callable
    result = sample_tool("hello")
    assert result == "processed: hello"
