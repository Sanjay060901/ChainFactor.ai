"""Tests for application configuration (Settings)."""

import pytest

from app.config import settings


@pytest.mark.asyncio
async def test_default_settings() -> None:
    """Verify critical default settings values."""
    assert settings.APP_NAME == "ChainFactor AI"
    assert settings.DEBUG is True
    # AWS_REGION may be overridden by system env var (e.g. AWS_REGION=us-east-1)
    assert isinstance(settings.AWS_REGION, str) and len(settings.AWS_REGION) > 0
    assert settings.BEDROCK_REGION == "us-east-1"
    assert settings.ALGORAND_NETWORK == "testnet"


@pytest.mark.asyncio
async def test_database_url_default() -> None:
    """Verify DATABASE_URL contains the project database name."""
    assert "chainfactor" in settings.DATABASE_URL


@pytest.mark.asyncio
async def test_bedrock_model_ids() -> None:
    """Verify all Bedrock model IDs reference Claude models."""
    assert "claude" in settings.BEDROCK_SONNET_MODEL_ID
    assert "claude" in settings.BEDROCK_OPUS_MODEL_ID
    assert "claude" in settings.BEDROCK_HAIKU_MODEL_ID
