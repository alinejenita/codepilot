"""Configuration settings for CodePilot loaded from environment and .env file."""

from pathlib import Path
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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def resolved_workspace_root(self) -> Path:
        return Path(self.workspace_root).resolve()


settings = Settings()
