"""Agent framework configuration: Bedrock models, regions, shared constants."""

from app.config import settings

# Bedrock region -- always us-east-1 for model availability
BEDROCK_REGION: str = settings.BEDROCK_REGION  # "us-east-1"

# Model IDs (from app config, centralized here for agent modules)
SONNET_MODEL_ID: str = settings.BEDROCK_SONNET_MODEL_ID
OPUS_MODEL_ID: str = settings.BEDROCK_OPUS_MODEL_ID
HAIKU_MODEL_ID: str = settings.BEDROCK_HAIKU_MODEL_ID


def get_bedrock_model(model_id: str | None = None):
    """Create a BedrockModel configured for the correct region.

    Args:
        model_id: Override model ID. Defaults to Sonnet.
    """
    from strands.models.bedrock import BedrockModel

    return BedrockModel(
        region_name=BEDROCK_REGION,
        model_id=model_id or SONNET_MODEL_ID,
    )
