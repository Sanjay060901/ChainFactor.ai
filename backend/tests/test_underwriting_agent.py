"""TDD tests for Feature 4.11: Underwriting Agent configuration.

Verifies that the Underwriting Agent is properly configured with:
  - 7 registered tools
  - A non-empty system prompt
  - Correct agent instantiation
"""

from unittest.mock import MagicMock, patch

from app.modules.agents.underwriting_agent import (
    UNDERWRITING_AGENT_SYSTEM_PROMPT,
    UNDERWRITING_AGENT_TOOLS,
    create_underwriting_agent,
)


class TestUnderwritingAgentConfig:
    """Verify Underwriting Agent static configuration."""

    def test_system_prompt_is_not_empty(self):
        """System prompt must contain meaningful instructions."""
        assert len(UNDERWRITING_AGENT_SYSTEM_PROMPT) > 100

    def test_system_prompt_mentions_cross_validate(self):
        """System prompt should reference cross-validation."""
        assert "CROSS-VALIDATE" in UNDERWRITING_AGENT_SYSTEM_PROMPT

    def test_system_prompt_mentions_approve(self):
        """System prompt should reference approval decisions."""
        assert "APPROVE" in UNDERWRITING_AGENT_SYSTEM_PROMPT

    def test_tools_list_has_7_tools(self):
        """Underwriting agent must have exactly 7 tools registered."""
        assert len(UNDERWRITING_AGENT_TOOLS) == 7

    def test_tools_are_callable(self):
        """All registered tools must be callable."""
        for t in UNDERWRITING_AGENT_TOOLS:
            assert callable(t), f"Tool {t} is not callable"


class TestUnderwritingAgentCreation:
    """Verify create_underwriting_agent() returns a properly configured Agent."""

    @patch("app.modules.agents.underwriting_agent.get_model_for_agent")
    def test_create_returns_agent(self, mock_get_model):
        """create_underwriting_agent() should return a Strands Agent instance."""
        mock_get_model.return_value = MagicMock()
        agent = create_underwriting_agent()
        # Strands Agent has a name attribute
        assert agent.name == "underwriting_agent"

    @patch("app.modules.agents.underwriting_agent.get_model_for_agent")
    def test_agent_has_system_prompt(self, mock_get_model):
        """Agent should have a non-empty system_prompt."""
        mock_get_model.return_value = MagicMock()
        agent = create_underwriting_agent()
        assert agent.system_prompt is not None
        assert len(agent.system_prompt) > 0

    @patch("app.modules.agents.underwriting_agent.get_model_for_agent")
    def test_agent_has_tool_caller(self, mock_get_model):
        """Agent should have a tool attribute (Strands _ToolCaller) after creation."""
        mock_get_model.return_value = MagicMock()
        agent = create_underwriting_agent()
        # Strands Agent wraps tools in a _ToolCaller; verify it exists
        assert hasattr(agent, "tool")
        assert agent.tool is not None
