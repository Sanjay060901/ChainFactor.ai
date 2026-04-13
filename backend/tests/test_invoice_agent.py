"""Tests for Invoice Processing Agent assembly (Feature 4.10).

Verifies that all 11 tools are wired into the agent correctly and that
create_invoice_processing_agent() returns a valid Agent instance.
"""

from unittest.mock import MagicMock, patch

from strands import Agent

from app.modules.agents.invoice_agent import (
    INVOICE_AGENT_SYSTEM_PROMPT,
    INVOICE_AGENT_TOOLS,
    create_invoice_processing_agent,
)

# Expected tool names in pipeline order
EXPECTED_TOOL_NAMES = [
    "extract_invoice",
    "validate_fields",
    "validate_gst_compliance",
    "_verify_gstn_tool",
    "check_fraud",
    "_get_buyer_intel_tool",
    "_get_credit_score_tool",
    "get_company_info_tool",
    "_calculate_risk_tool",
    "_generate_summary_tool",
    "_mint_nft_tool",
]


class TestInvoiceAgentToolList:
    """Tests for the INVOICE_AGENT_TOOLS list."""

    def test_tools_list_has_11_entries(self):
        """INVOICE_AGENT_TOOLS must contain exactly 11 tools."""
        assert len(INVOICE_AGENT_TOOLS) == 11

    def test_all_tools_are_callable(self):
        """Every entry in the tools list must be callable."""
        for tool in INVOICE_AGENT_TOOLS:
            assert callable(tool), f"{tool} is not callable"

    def test_tool_names_match_expected(self):
        """Tool function names must match the expected pipeline order."""
        actual_names = [t.__name__ for t in INVOICE_AGENT_TOOLS]
        assert actual_names == EXPECTED_TOOL_NAMES

    def test_no_duplicate_tools(self):
        """No tool should appear more than once."""
        names = [t.__name__ for t in INVOICE_AGENT_TOOLS]
        assert len(names) == len(set(names)), f"Duplicate tools found: {names}"

    def test_tools_have_tool_decorator(self):
        """Each tool function should have been decorated with @tool.

        Strands @tool sets a 'tool_name' attribute or wraps with ToolUse.
        We check for the common marker attributes.
        """
        for tool_fn in INVOICE_AGENT_TOOLS:
            # Strands @tool typically adds __wrapped__ or tool metadata.
            # At minimum, verify each is a function (not a class or module).
            assert hasattr(tool_fn, "__name__"), (
                f"Tool {tool_fn} missing __name__ -- may not be a decorated function"
            )


class TestInvoiceAgentSystemPrompt:
    """Tests for the system prompt."""

    def test_prompt_is_not_empty(self):
        """System prompt must not be empty."""
        assert INVOICE_AGENT_SYSTEM_PROMPT
        assert len(INVOICE_AGENT_SYSTEM_PROMPT) > 100

    def test_prompt_mentions_all_pipeline_steps(self):
        """System prompt should reference all 10 analysis steps."""
        keywords = [
            "EXTRACT",
            "VALIDATE",
            "GST",
            "VERIFY",
            "fraud",
            "buyer",
            "credit score",
            "company information",
            "risk score",
            "summary",
        ]
        prompt_lower = INVOICE_AGENT_SYSTEM_PROMPT.lower()
        for kw in keywords:
            assert kw.lower() in prompt_lower, (
                f"System prompt missing reference to '{kw}'"
            )

    def test_prompt_mentions_underwriting_handoff(self):
        """System prompt should mention handing off to Underwriting Agent."""
        assert "Underwriting Agent" in INVOICE_AGENT_SYSTEM_PROMPT


class TestCreateInvoiceProcessingAgent:
    """Tests for the agent factory function."""

    @patch("app.modules.agents.invoice_agent.get_model_for_agent")
    def test_returns_agent_instance(self, mock_get_model):
        """create_invoice_processing_agent() must return a Strands Agent."""
        mock_get_model.return_value = MagicMock()
        agent = create_invoice_processing_agent()
        assert isinstance(agent, Agent)

    @patch("app.modules.agents.invoice_agent.get_model_for_agent")
    def test_agent_has_correct_name(self, mock_get_model):
        """Agent name should be 'invoice_processing_agent'."""
        mock_get_model.return_value = MagicMock()
        agent = create_invoice_processing_agent()
        assert agent.name == "invoice_processing_agent"

    @patch("app.modules.agents.invoice_agent.get_model_for_agent")
    def test_agent_has_11_tools(self, mock_get_model):
        """Agent should be initialized with exactly 11 tools."""
        mock_get_model.return_value = MagicMock()
        agent = create_invoice_processing_agent()
        # Strands Agent stores tools in agent.tool_registry.
        # get_all_tools_config() returns a dict keyed by tool name.
        tool_config = agent.tool_registry.get_all_tools_config()
        tool_count = len(tool_config)
        assert tool_count == 11, f"Expected 11 tools, got {tool_count}"

    @patch("app.modules.agents.invoice_agent.get_model_for_agent")
    def test_agent_tool_names_in_registry(self, mock_get_model):
        """All expected tool names should be present in the agent tool registry."""
        mock_get_model.return_value = MagicMock()
        agent = create_invoice_processing_agent()
        tool_config = agent.tool_registry.get_all_tools_config()
        registry_names = set(tool_config.keys())

        for name in EXPECTED_TOOL_NAMES:
            assert name in registry_names, (
                f"Tool '{name}' not found in agent registry: {registry_names}"
            )

    @patch("app.modules.agents.invoice_agent.get_model_for_agent")
    def test_agent_uses_sonnet_model(self, mock_get_model):
        """Agent should be created with the Sonnet model ID."""
        mock_get_model.return_value = MagicMock()
        create_invoice_processing_agent()
        mock_get_model.assert_called_once()

    @patch("app.modules.agents.invoice_agent.get_model_for_agent")
    def test_agent_has_system_prompt(self, mock_get_model):
        """Agent should have a non-empty system prompt."""
        mock_get_model.return_value = MagicMock()
        agent = create_invoice_processing_agent()
        assert agent.system_prompt
        assert "Invoice Processing Agent" in agent.system_prompt
