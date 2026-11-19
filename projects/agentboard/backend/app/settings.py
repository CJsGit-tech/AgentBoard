from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://agentboard:agentboard@localhost:5432/agentboard"
    agentboard_origin: str = "http://localhost:5173"
    browser_token_file: str | None = Field(default=None, validation_alias="AGENTBOARD_BROWSER_TOKEN_FILE")
    mcp_token_file: str | None = Field(default=None, validation_alias="AGENTBOARD_MCP_TOKEN_FILE")
    max_request_bytes: int = 1_048_576
    codex_sdk_enabled: bool = Field(default=False, validation_alias="AGENTBOARD_CODEX_SDK_ENABLED")
    claude_agent_sdk_enabled: bool = Field(default=False, validation_alias="AGENTBOARD_CLAUDE_AGENT_SDK_ENABLED")
    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    anthropic_api_key: str | None = Field(default=None, validation_alias="ANTHROPIC_API_KEY")


settings = Settings()
