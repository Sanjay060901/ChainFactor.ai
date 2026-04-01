"""Application configuration. Reads from environment variables, falls back to defaults."""

import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "ChainFactor AI"
    APP_ENV: str = "development"
    DEBUG: bool = True
    DEMO_MODE: bool = False

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # Database
    DATABASE_URL: str = (
        "postgresql+asyncpg://chainfactor:chainfactor@localhost:5432/chainfactor"
    )

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # WebSocket
    WS_HEARTBEAT_INTERVAL_SECONDS: int = (
        30  # Ping interval to keep ALB connection alive
    )

    # AWS (primary region for all services except Bedrock)
    AWS_REGION: str = "ap-south-1"

    # Cognito
    COGNITO_USER_POOL_ID: str = ""
    COGNITO_APP_CLIENT_ID: str = ""

    # S3
    S3_BUCKET_NAME: str = ""
    S3_INVOICE_PREFIX: str = "invoices/"

    # Bedrock
    BEDROCK_REGION: str = "us-east-1"
    BEDROCK_SONNET_MODEL_ID: str = "us.anthropic.claude-sonnet-4-6-v1"
    BEDROCK_OPUS_MODEL_ID: str = "us.anthropic.claude-opus-4-6-v1"
    BEDROCK_HAIKU_MODEL_ID: str = "us.anthropic.claude-haiku-4-5-20251001"

    # Algorand
    ALGORAND_NETWORK: str = "testnet"
    ALGORAND_ALGOD_URL: str = "https://testnet-api.algonode.cloud"
    ALGORAND_INDEXER_URL: str = "https://testnet-idx.algonode.cloud"
    ALGORAND_APP_WALLET_MNEMONIC: str = ""
    ALGORAND_APP_ID: int = 0

    # Pera Explorer
    PERA_EXPLORER_BASE_URL: str = "https://testnet.explorer.perawallet.app"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }

    def get_database_url(self) -> str:
        """Return DATABASE_URL with DB_PASSWORD injected if present (ECS Secrets Manager)."""
        db_password = os.environ.get("DB_PASSWORD")
        if db_password and "PLACEHOLDER" in self.DATABASE_URL:
            return self.DATABASE_URL.replace("PLACEHOLDER", db_password)
        return self.DATABASE_URL


settings = Settings()
