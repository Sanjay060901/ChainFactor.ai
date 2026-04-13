"""Agent framework configuration: Bedrock models, regions, runtime parameters.

Centralizes all AI/agent configuration so that agent modules import from here
instead of reaching into app.config directly.  All Bedrock runtime parameters
(temperature, max_tokens, top_p/k) are defined per-role so agents get
consistent, reproducible results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.config import settings

# ---------------------------------------------------------------------------
# Bedrock region & model IDs
# ---------------------------------------------------------------------------

BEDROCK_REGION: str = settings.BEDROCK_REGION  # "us-east-1"

SONNET_MODEL_ID: str = settings.BEDROCK_SONNET_MODEL_ID
OPUS_MODEL_ID: str = settings.BEDROCK_OPUS_MODEL_ID
HAIKU_MODEL_ID: str = settings.BEDROCK_HAIKU_MODEL_ID

# ---------------------------------------------------------------------------
# Bedrock runtime / inference parameters (per-role defaults)
# ---------------------------------------------------------------------------

# Invoice Processing Agent -- deterministic pipeline, low creativity
INVOICE_AGENT_INFERENCE_PARAMS: dict[str, Any] = {
    "temperature": 0.1,
    "max_tokens": 4096,
    "top_p": 0.9,
}

# Underwriting Agent -- needs zero-shot consistency for approve/reject
UNDERWRITING_AGENT_INFERENCE_PARAMS: dict[str, Any] = {
    "temperature": 0.0,
    "max_tokens": 4096,
    "top_p": 1.0,
}

# NL Query Agent (Opus) -- slightly creative for natural language replies
NL_QUERY_AGENT_INFERENCE_PARAMS: dict[str, Any] = {
    "temperature": 0.3,
    "max_tokens": 2048,
    "top_p": 0.95,
}

# Collection Agent (Haiku) -- lightweight, deterministic reminders
COLLECTION_AGENT_INFERENCE_PARAMS: dict[str, Any] = {
    "temperature": 0.1,
    "max_tokens": 2048,
    "top_p": 0.9,
}


# ---------------------------------------------------------------------------
# Agent configuration dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AgentConfig:
    """Immutable configuration bundle for a single Strands Agent."""

    name: str
    model_id: str
    description: str
    inference_params: dict[str, Any] = field(default_factory=dict)
    # Per-agent timeouts (seconds)
    timeout: float = 60.0
    max_iterations: int = 15
    # Callback streaming
    stream_events: bool = True


# Pre-built agent configs (importable by agent modules)
INVOICE_AGENT_CONFIG = AgentConfig(
    name="invoice_processing_agent",
    model_id=SONNET_MODEL_ID,
    description=(
        "Processes uploaded invoices through a 10-step analysis pipeline "
        "including OCR, validation, fraud detection, and risk scoring."
    ),
    inference_params=INVOICE_AGENT_INFERENCE_PARAMS,
    timeout=60.0,
    max_iterations=15,
)

UNDERWRITING_AGENT_CONFIG = AgentConfig(
    name="underwriting_agent",
    model_id=SONNET_MODEL_ID,
    description=(
        "Makes autonomous underwriting decisions (approve/reject/flag) "
        "with cross-validation and full reasoning traces."
    ),
    inference_params=UNDERWRITING_AGENT_INFERENCE_PARAMS,
    timeout=60.0,
    max_iterations=10,
)

NL_QUERY_AGENT_CONFIG = AgentConfig(
    name="nl_query_agent",
    model_id=OPUS_MODEL_ID,
    description=(
        "Standalone natural language query agent for portfolio analysis. "
        "On-demand, low-volume. Uses Opus for deep reasoning."
    ),
    inference_params=NL_QUERY_AGENT_INFERENCE_PARAMS,
    timeout=30.0,
    max_iterations=5,
    stream_events=True,
)

COLLECTION_AGENT_CONFIG = AgentConfig(
    name="collection_agent",
    model_id=HAIKU_MODEL_ID,
    description=(
        "Proactive collection agent for overdue invoice monitoring, "
        "payment reminders, and escalation suggestions. DEFERRED to Round 3."
    ),
    inference_params=COLLECTION_AGENT_INFERENCE_PARAMS,
    timeout=30.0,
    max_iterations=8,
)


# ---------------------------------------------------------------------------
# Swarm configuration
# ---------------------------------------------------------------------------

SWARM_MAX_HANDOFFS: int = 5
SWARM_MAX_ITERATIONS: int = 10
SWARM_EXECUTION_TIMEOUT: float = 120.0  # 2 minutes (hackathon target)
SWARM_NODE_TIMEOUT: float = 60.0  # 1 minute per agent


# ---------------------------------------------------------------------------
# Callback / event hook constants
# ---------------------------------------------------------------------------

# Redis channel prefix for WebSocket streaming
WS_CHANNEL_PREFIX: str = "invoice"

# Event types emitted by agent hooks
EVENT_TOOL_START: str = "tool_start"
EVENT_TOOL_COMPLETE: str = "tool_complete"
EVENT_AGENT_THINKING: str = "agent_thinking"
EVENT_HANDOFF: str = "agent_handoff"
EVENT_PIPELINE_COMPLETE: str = "pipeline_complete"
EVENT_PIPELINE_ERROR: str = "pipeline_error"


# ---------------------------------------------------------------------------
# Factory: get_bedrock_model
# ---------------------------------------------------------------------------


def get_bedrock_model(
    model_id: str | None = None,
    inference_params: dict[str, Any] | None = None,
):
    """Create a BedrockModel configured for the correct region.

    Args:
        model_id: Override model ID. Defaults to Sonnet.
        inference_params: Optional dict of inference parameters
            (temperature, max_tokens, top_p). If None, uses Bedrock defaults.
    """
    from strands.models.bedrock import BedrockModel

    kwargs: dict[str, Any] = {
        "region_name": BEDROCK_REGION,
        "model_id": model_id or SONNET_MODEL_ID,
    }
    if inference_params:
        kwargs["additional_request_fields"] = {
            "inferenceConfig": inference_params,
        }

    return BedrockModel(**kwargs)


def get_model_for_agent(config: AgentConfig):
    """Create a BedrockModel from an AgentConfig instance."""
    return get_bedrock_model(
        model_id=config.model_id,
        inference_params=config.inference_params,
    )
