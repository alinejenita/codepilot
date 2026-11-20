"""Configuration settings for CodePilot loaded from environment and .env file."""

from pathlib import Path
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5-coder:7b"
    ollama_context_length: int = 8192
    ollama_temperature: float = 0.2
    ollama_keep_alive: str = "10m"

    workspace_root: str = "./workspace"
    max_agent_iterations: int = 8
    command_timeout_seconds: int = 30
    login_username: str = Field(default="", validation_alias="CODEPILOT_LOGIN_USERNAME")
    login_password: SecretStr = Field(
        default=SecretStr(""),
        validation_alias="CODEPILOT_LOGIN_PASSWORD",
    )
    session_secret: SecretStr = Field(
        default=SecretStr(""),
        validation_alias="CODEPILOT_SESSION_SECRET",
    )
    cookie_secure: bool = Field(default=False, validation_alias="CODEPILOT_COOKIE_SECURE")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def resolved_workspace_root(self) -> Path:
        return Path(self.workspace_root).resolve()

    @property
    def login_configured(self) -> bool:
        login_password = self.login_password.get_secret_value()
        session_secret = self.session_secret.get_secret_value()
        return bool(
            self.login_username.strip()
            and len(login_password) >= 12
            and len(session_secret.encode("utf-8")) >= 32
        )


settings = Settings()
