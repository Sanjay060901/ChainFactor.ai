"""Tests for AI agent configuration: runtime parameters, agent configs, callbacks.

Covers:
- AgentConfig dataclass and pre-built configs
- Inference parameters per agent role
- NL Query Agent creation (Opus)
- Collection Agent creation (Haiku, deferred)
- Callback handler event building and tracking
- Swarm configuration constants
- Demo mode flag propagation
"""

import pytest


# ---------------------------------------------------------------------------
# AgentConfig dataclass
# ---------------------------------------------------------------------------


class TestAgentConfig:
    """Test the AgentConfig dataclass and pre-built configurations."""

    def test_agent_config_is_frozen(self):
        from app.modules.agents.config import AgentConfig

        config = AgentConfig(name="test", model_id="test-model", description="test")
        with pytest.raises(AttributeError):
            config.name = "changed"  # type: ignore[misc]

    def test_invoice_agent_config_uses_sonnet(self):
        from app.modules.agents.config import INVOICE_AGENT_CONFIG, SONNET_MODEL_ID

        assert INVOICE_AGENT_CONFIG.model_id == SONNET_MODEL_ID
        assert "sonnet" in INVOICE_AGENT_CONFIG.model_id

    def test_underwriting_agent_config_uses_sonnet(self):
        """Underwriting uses Sonnet -- NOT Opus (cost optimization)."""
        from app.modules.agents.config import (
            OPUS_MODEL_ID,
            UNDERWRITING_AGENT_CONFIG,
            SONNET_MODEL_ID,
        )

        assert UNDERWRITING_AGENT_CONFIG.model_id == SONNET_MODEL_ID
        assert UNDERWRITING_AGENT_CONFIG.model_id != OPUS_MODEL_ID

    def test_nl_query_agent_config_uses_opus(self):
        """NL Query is the ONLY agent that uses Opus."""
        from app.modules.agents.config import NL_QUERY_AGENT_CONFIG, OPUS_MODEL_ID

        assert NL_QUERY_AGENT_CONFIG.model_id == OPUS_MODEL_ID
        assert "opus" in NL_QUERY_AGENT_CONFIG.model_id

    def test_collection_agent_config_uses_haiku(self):
        from app.modules.agents.config import COLLECTION_AGENT_CONFIG, HAIKU_MODEL_ID

        assert COLLECTION_AGENT_CONFIG.model_id == HAIKU_MODEL_ID
        assert "haiku" in COLLECTION_AGENT_CONFIG.model_id

    def test_all_configs_have_names(self):
        from app.modules.agents.config import (
            COLLECTION_AGENT_CONFIG,
            INVOICE_AGENT_CONFIG,
            NL_QUERY_AGENT_CONFIG,
            UNDERWRITING_AGENT_CONFIG,
        )

        configs = [
            INVOICE_AGENT_CONFIG,
            UNDERWRITING_AGENT_CONFIG,
            NL_QUERY_AGENT_CONFIG,
            COLLECTION_AGENT_CONFIG,
        ]
        names = [c.name for c in configs]
        assert len(set(names)) == 4, "Agent names must be unique"
        for c in configs:
            assert c.name
            assert c.description
            assert c.model_id

    def test_all_configs_have_positive_timeouts(self):
        from app.modules.agents.config import (
            COLLECTION_AGENT_CONFIG,
            INVOICE_AGENT_CONFIG,
            NL_QUERY_AGENT_CONFIG,
            UNDERWRITING_AGENT_CONFIG,
        )

        for config in [
            INVOICE_AGENT_CONFIG,
            UNDERWRITING_AGENT_CONFIG,
            NL_QUERY_AGENT_CONFIG,
            COLLECTION_AGENT_CONFIG,
        ]:
            assert config.timeout > 0
            assert config.max_iterations > 0


# ---------------------------------------------------------------------------
# Inference parameters
# ---------------------------------------------------------------------------


class TestInferenceParams:
    """Test Bedrock runtime parameters per agent role."""

    def test_invoice_agent_low_temperature(self):
        """Invoice processing should be deterministic (low temp)."""
        from app.modules.agents.config import INVOICE_AGENT_INFERENCE_PARAMS

        assert INVOICE_AGENT_INFERENCE_PARAMS["temperature"] <= 0.2

    def test_underwriting_agent_zero_temperature(self):
        """Underwriting decisions must be fully deterministic."""
        from app.modules.agents.config import UNDERWRITING_AGENT_INFERENCE_PARAMS

        assert UNDERWRITING_AGENT_INFERENCE_PARAMS["temperature"] == 0.0

    def test_nl_query_agent_moderate_temperature(self):
        """NL query can be slightly creative for natural answers."""
        from app.modules.agents.config import NL_QUERY_AGENT_INFERENCE_PARAMS

        temp = NL_QUERY_AGENT_INFERENCE_PARAMS["temperature"]
        assert 0.1 <= temp <= 0.5

    def test_all_params_have_max_tokens(self):
        from app.modules.agents.config import (
            COLLECTION_AGENT_INFERENCE_PARAMS,
            INVOICE_AGENT_INFERENCE_PARAMS,
            NL_QUERY_AGENT_INFERENCE_PARAMS,
            UNDERWRITING_AGENT_INFERENCE_PARAMS,
        )

        for params in [
            INVOICE_AGENT_INFERENCE_PARAMS,
            UNDERWRITING_AGENT_INFERENCE_PARAMS,
            NL_QUERY_AGENT_INFERENCE_PARAMS,
            COLLECTION_AGENT_INFERENCE_PARAMS,
        ]:
            assert "max_tokens" in params
            assert params["max_tokens"] > 0

    def test_all_params_have_top_p(self):
        from app.modules.agents.config import (
            COLLECTION_AGENT_INFERENCE_PARAMS,
            INVOICE_AGENT_INFERENCE_PARAMS,
            NL_QUERY_AGENT_INFERENCE_PARAMS,
            UNDERWRITING_AGENT_INFERENCE_PARAMS,
        )

        for params in [
            INVOICE_AGENT_INFERENCE_PARAMS,
            UNDERWRITING_AGENT_INFERENCE_PARAMS,
            NL_QUERY_AGENT_INFERENCE_PARAMS,
            COLLECTION_AGENT_INFERENCE_PARAMS,
        ]:
            assert "top_p" in params
            assert 0 < params["top_p"] <= 1.0


# ---------------------------------------------------------------------------
# Swarm configuration constants
# ---------------------------------------------------------------------------


class TestSwarmConfig:
    """Test swarm-level configuration constants."""

    def test_swarm_execution_timeout(self):
        from app.modules.agents.config import SWARM_EXECUTION_TIMEOUT

        assert SWARM_EXECUTION_TIMEOUT == 120.0  # 2 minutes

    def test_swarm_node_timeout(self):
        from app.modules.agents.config import SWARM_NODE_TIMEOUT

        assert SWARM_NODE_TIMEOUT == 60.0  # 1 minute per agent

    def test_swarm_max_handoffs(self):
        from app.modules.agents.config import SWARM_MAX_HANDOFFS

        assert SWARM_MAX_HANDOFFS >= 3  # at least invoice -> underwriting -> invoice

    def test_swarm_max_iterations(self):
        from app.modules.agents.config import SWARM_MAX_ITERATIONS

        assert SWARM_MAX_ITERATIONS >= 5


# ---------------------------------------------------------------------------
# Event hook constants
# ---------------------------------------------------------------------------


class TestEventConstants:
    """Test event type constants for WebSocket streaming."""

    def test_event_types_defined(self):
        from app.modules.agents.config import (
            EVENT_AGENT_THINKING,
            EVENT_HANDOFF,
            EVENT_PIPELINE_COMPLETE,
            EVENT_PIPELINE_ERROR,
            EVENT_TOOL_COMPLETE,
            EVENT_TOOL_START,
        )

        events = [
            EVENT_TOOL_START,
            EVENT_TOOL_COMPLETE,
            EVENT_AGENT_THINKING,
            EVENT_HANDOFF,
            EVENT_PIPELINE_COMPLETE,
            EVENT_PIPELINE_ERROR,
        ]
        # All unique
        assert len(set(events)) == 6
        # All non-empty strings
        for e in events:
            assert isinstance(e, str)
            assert len(e) > 0

    def test_ws_channel_prefix(self):
        from app.modules.agents.config import WS_CHANNEL_PREFIX

        assert WS_CHANNEL_PREFIX == "invoice"


# ---------------------------------------------------------------------------
# NL Query Agent creation
# ---------------------------------------------------------------------------


class TestNLQueryAgent:
    """Test NL Query Agent creation (Opus, standalone)."""

    def test_create_nl_query_agent(self):
        from app.modules.agents.nl_query_agent import create_nl_query_agent

        agent = create_nl_query_agent()
        assert agent is not None
        assert agent.name == "nl_query_agent"

    def test_nl_query_agent_has_system_prompt(self):
        from app.modules.agents.nl_query_agent import create_nl_query_agent

        agent = create_nl_query_agent()
        assert agent.system_prompt is not None
        assert "portfolio" in agent.system_prompt.lower()

    @pytest.mark.skip(reason="Strands Swarm API restructured in v0.1.9 — Phase 2")
    def test_nl_query_agent_not_in_swarm(self):
        """NL Query Agent should NOT be in the Swarm pipeline."""
        pytest.importorskip("a2a", reason="a2a optional dependency not installed")
        from app.modules.agents.swarm import create_invoice_swarm

        swarm = create_invoice_swarm()
        agent_names = [n.name for n in swarm.nodes]
        assert "nl_query_agent" not in agent_names


# ---------------------------------------------------------------------------
# Collection Agent creation
# ---------------------------------------------------------------------------


class TestCollectionAgent:
    """Test Collection Agent creation (Haiku, deferred)."""

    def test_create_collection_agent(self):
        from app.modules.agents.collection_agent import create_collection_agent

        agent = create_collection_agent()
        assert agent is not None
        assert agent.name == "collection_agent"

    def test_collection_agent_has_system_prompt(self):
        from app.modules.agents.collection_agent import create_collection_agent

        agent = create_collection_agent()
        assert agent.system_prompt is not None
        assert "collection" in agent.system_prompt.lower()

    @pytest.mark.skip(reason="Strands Swarm API restructured in v0.1.9 — Phase 2")
    def test_collection_agent_not_in_swarm(self):
        """Collection Agent should NOT be in the Swarm (deferred)."""
        pytest.importorskip("a2a", reason="a2a optional dependency not installed")
        from app.modules.agents.swarm import create_invoice_swarm

        swarm = create_invoice_swarm()
        agent_names = [n.name for n in swarm.nodes]
        assert "collection_agent" not in agent_names


# ---------------------------------------------------------------------------
# Callback handler
# ---------------------------------------------------------------------------


class TestCallbackHandler:
    """Test the AgentCallbackHandler event tracking."""

    def test_create_callback_handler(self):
        from app.modules.agents.callbacks import create_agent_callback_handler

        handler = create_agent_callback_handler(invoice_id="inv_test_001")
        assert handler.invoice_id == "inv_test_001"
        assert handler.channel == "invoice:inv_test_001"
        assert handler.step_counter == 0
        assert handler.events == []

    @pytest.mark.asyncio
    async def test_on_tool_start_increments_step(self):
        from app.modules.agents.callbacks import AgentCallbackHandler

        handler = AgentCallbackHandler(invoice_id="inv_test_002")
        # Patch _publish to avoid Redis dependency
        handler._publish = _noop_publish

        await handler.on_tool_start("extract_invoice", "invoice_processing")
        assert handler.step_counter == 1

        await handler.on_tool_start("validate_fields", "invoice_processing")
        assert handler.step_counter == 2

    @pytest.mark.asyncio
    async def test_on_tool_complete_records_event(self):
        from app.modules.agents.callbacks import AgentCallbackHandler

        handler = AgentCallbackHandler(invoice_id="inv_test_003")
        handler._publish = _noop_publish

        await handler.on_tool_start("check_fraud", "invoice_processing")
        await handler.on_tool_complete(
            "check_fraud", "invoice_processing", result={"score": 85}
        )

        events = handler.events
        assert len(events) == 2
        assert events[0]["type"] == "tool_start"
        assert events[1]["type"] == "tool_complete"
        assert events[1]["tool_name"] == "check_fraud"

    @pytest.mark.asyncio
    async def test_on_tool_error_records_error_events(self):
        from app.modules.agents.callbacks import AgentCallbackHandler

        handler = AgentCallbackHandler(invoice_id="inv_test_004")
        handler._publish = _noop_publish

        await handler.on_tool_start("verify_gstn", "invoice_processing")
        await handler.on_tool_error(
            "verify_gstn", "invoice_processing", error="API timeout"
        )

        events = handler.events
        # tool_start + tool_complete(error) + pipeline_error
        assert len(events) == 3
        assert events[1]["status"] == "error"
        assert events[2]["type"] == "pipeline_error"

    @pytest.mark.asyncio
    async def test_on_handoff_records_event(self):
        from app.modules.agents.callbacks import AgentCallbackHandler

        handler = AgentCallbackHandler(invoice_id="inv_test_005")
        handler._publish = _noop_publish

        await handler.on_handoff(
            from_agent="invoice_processing",
            to_agent="underwriting",
            context_keys=["extracted_data", "risk_assessment"],
        )

        events = handler.events
        assert len(events) == 1
        assert events[0]["type"] == "agent_handoff"
        assert events[0]["from_agent"] == "invoice_processing"
        assert events[0]["to_agent"] == "underwriting"

    @pytest.mark.asyncio
    async def test_on_thinking_truncates_long_content(self):
        from app.modules.agents.callbacks import AgentCallbackHandler

        handler = AgentCallbackHandler(invoice_id="inv_test_006")
        handler._publish = _noop_publish

        long_content = "x" * 1000
        await handler.on_thinking("invoice_processing", long_content)

        events = handler.events
        assert len(events) == 1
        assert len(events[0]["content"]) == 500  # Truncated


# ---------------------------------------------------------------------------
# get_model_for_agent
# ---------------------------------------------------------------------------


class TestModelFactory:
    """Test Bedrock model factory functions."""

    def test_get_bedrock_model_default_sonnet(self):
        from app.modules.agents.config import SONNET_MODEL_ID, get_bedrock_model

        model = get_bedrock_model()
        assert model is not None
        assert model.config["model_id"] == SONNET_MODEL_ID

    def test_get_bedrock_model_override(self):
        from app.modules.agents.config import OPUS_MODEL_ID, get_bedrock_model

        model = get_bedrock_model(model_id=OPUS_MODEL_ID)
        assert model.config["model_id"] == OPUS_MODEL_ID

    def test_get_model_for_agent_config(self):
        from app.modules.agents.config import (
            INVOICE_AGENT_CONFIG,
            get_model_for_agent,
        )

        model = get_model_for_agent(INVOICE_AGENT_CONFIG)
        assert model is not None
        assert model.config["model_id"] == INVOICE_AGENT_CONFIG.model_id


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _noop_publish(event: dict) -> None:
    """No-op publish for tests that don't need Redis."""
    pass
