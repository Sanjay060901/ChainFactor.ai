"""AI settings request/response schemas."""

from pydantic import BaseModel, Field


class AgentInfo(BaseModel):
    """Read-only info about a configured agent."""

    name: str
    model_id: str
    description: str
    temperature: float
    max_tokens: int
    top_p: float
    timeout: float
    max_iterations: int
    stream_events: bool


class SwarmInfo(BaseModel):
    """Read-only info about the swarm configuration."""

    max_handoffs: int
    max_iterations: int
    execution_timeout: float
    node_timeout: float
    agents: list[str]


class AIConfigResponse(BaseModel):
    """Full AI configuration response -- read-only system info + user-configurable settings."""

    # System info (read-only)
    bedrock_region: str
    demo_mode: bool
    pipeline_timeout: int
    max_retries: int

    # Agent roster
    agents: list[AgentInfo]

    # Swarm config
    swarm: SwarmInfo

    # Event types for WebSocket streaming
    event_types: list[str]


class AISettingsUpdateRequest(BaseModel):
    """User-configurable AI settings (per-user overrides)."""

    pipeline_timeout: int | None = Field(
        None, ge=30, le=300, description="Pipeline timeout in seconds (30-300)"
    )
    auto_process: bool | None = Field(
        None, description="Automatically start processing after upload"
    )
    enable_ws_streaming: bool | None = Field(
        None, description="Enable real-time WebSocket event streaming"
    )
    risk_threshold_low: int | None = Field(
        None, ge=0, le=100, description="Risk score threshold for low risk (0-100)"
    )
    risk_threshold_high: int | None = Field(
        None, ge=0, le=100, description="Risk score threshold for high risk (0-100)"
    )
    enable_nft_auto_mint: bool | None = Field(
        None, description="Auto-mint NFT on approval (vs manual trigger)"
    )


class AISettingsResponse(BaseModel):
    """Current user's AI settings."""

    pipeline_timeout: int
    auto_process: bool
    enable_ws_streaming: bool
    risk_threshold_low: int
    risk_threshold_high: int
    enable_nft_auto_mint: bool
