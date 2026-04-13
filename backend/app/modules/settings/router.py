"""AI settings API endpoints -- view system config + manage user AI preferences."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.models.user_settings import DEFAULT_AI_SETTINGS
from app.modules.agents.config import (
    COLLECTION_AGENT_CONFIG,
    EVENT_AGENT_THINKING,
    EVENT_HANDOFF,
    EVENT_PIPELINE_COMPLETE,
    EVENT_PIPELINE_ERROR,
    EVENT_TOOL_COMPLETE,
    EVENT_TOOL_START,
    INVOICE_AGENT_CONFIG,
    NL_QUERY_AGENT_CONFIG,
    SWARM_EXECUTION_TIMEOUT,
    SWARM_MAX_HANDOFFS,
    SWARM_MAX_ITERATIONS,
    SWARM_NODE_TIMEOUT,
    UNDERWRITING_AGENT_CONFIG,
)
from app.modules.auth.dependencies import get_current_user
from app.schemas.ai_settings import (
    AgentInfo,
    AIConfigResponse,
    AISettingsResponse,
    AISettingsUpdateRequest,
    SwarmInfo,
)

router = APIRouter(prefix="/settings", tags=["settings"])


def _agent_to_info(config) -> AgentInfo:
    """Convert an AgentConfig dataclass into an AgentInfo schema."""
    return AgentInfo(
        name=config.name,
        model_id=config.model_id,
        description=config.description,
        temperature=config.inference_params.get("temperature", 0.0),
        max_tokens=config.inference_params.get("max_tokens", 4096),
        top_p=config.inference_params.get("top_p", 1.0),
        timeout=config.timeout,
        max_iterations=config.max_iterations,
        stream_events=config.stream_events,
    )


@router.get("/ai-config", response_model=AIConfigResponse)
async def get_ai_config(
    current_user: User = Depends(get_current_user),
):
    """Get the full AI configuration (system-level, read-only)."""
    agent_configs = [
        INVOICE_AGENT_CONFIG,
        UNDERWRITING_AGENT_CONFIG,
        NL_QUERY_AGENT_CONFIG,
        COLLECTION_AGENT_CONFIG,
    ]

    return AIConfigResponse(
        bedrock_region=settings.BEDROCK_REGION,
        demo_mode=False,
        pipeline_timeout=settings.AGENT_PIPELINE_TIMEOUT,
        max_retries=settings.AGENT_MAX_RETRIES,
        agents=[_agent_to_info(c) for c in agent_configs],
        swarm=SwarmInfo(
            max_handoffs=SWARM_MAX_HANDOFFS,
            max_iterations=SWARM_MAX_ITERATIONS,
            execution_timeout=SWARM_EXECUTION_TIMEOUT,
            node_timeout=SWARM_NODE_TIMEOUT,
            agents=[
                INVOICE_AGENT_CONFIG.name,
                UNDERWRITING_AGENT_CONFIG.name,
            ],
        ),
        event_types=[
            EVENT_TOOL_START,
            EVENT_TOOL_COMPLETE,
            EVENT_AGENT_THINKING,
            EVENT_HANDOFF,
            EVENT_PIPELINE_COMPLETE,
            EVENT_PIPELINE_ERROR,
        ],
    )


@router.get("/ai-preferences", response_model=AISettingsResponse)
async def get_ai_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current user's AI preferences."""
    from sqlalchemy import select

    from app.models.user_settings import UserSettings

    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == current_user.id)
    )
    user_settings = result.scalar_one_or_none()

    if user_settings and user_settings.ai_settings:
        prefs = {**DEFAULT_AI_SETTINGS, **user_settings.ai_settings}
    else:
        prefs = dict(DEFAULT_AI_SETTINGS)

    return AISettingsResponse(**prefs)


@router.put("/ai-preferences", response_model=AISettingsResponse)
async def update_ai_preferences(
    body: AISettingsUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the current user's AI preferences."""
    from sqlalchemy import select

    from app.models.user_settings import UserSettings

    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == current_user.id)
    )
    user_settings = result.scalar_one_or_none()

    if not user_settings:
        user_settings = UserSettings(
            user_id=current_user.id,
            ai_settings=dict(DEFAULT_AI_SETTINGS),
        )
        db.add(user_settings)

    # Merge only provided fields
    current_prefs = user_settings.ai_settings or dict(DEFAULT_AI_SETTINGS)
    updates = body.model_dump(exclude_none=True)
    merged = {**current_prefs, **updates}
    user_settings.ai_settings = merged

    await db.commit()

    return AISettingsResponse(**merged)
