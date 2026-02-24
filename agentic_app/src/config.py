"""Configuration module for the agentic app."""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class Config:
    """Application configuration."""
    
    # API settings
    api_key: Optional[str] = None
    base_url: str = "https://api.sambanova.ai/v1"
    model: str = "MiniMax-M2.5"
    timeout: int = 120
    
    # Memory settings
    memory_storage_dir: str = "~/.codex/agent_memory"
    max_context_tokens: int = 4000
    
    # Tool settings
    execute_code_timeout: int = 30
    run_command_timeout: int = 30
    allowed_commands: Optional[list] = None  # None means all commands allowed
    
    # Logging
    log_level: str = "INFO"
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create config from environment variables."""
        return cls(
            api_key=os.environ.get("OPENAI_API_KEY_CODEX"),
            base_url=os.environ.get("SAMBANOVA_BASE_URL", "https://api.sambanova.ai/v1"),
            model=os.environ.get("SAMBANOVA_MODEL", "MiniMax-M2.5"),
            timeout=int(os.environ.get("SAMBANOVA_TIMEOUT", "120")),
            memory_storage_dir=os.environ.get("MEMORY_STORAGE_DIR", "~/.codex/agent_memory"),
            max_context_tokens=int(os.environ.get("MAX_CONTEXT_TOKENS", "4000")),
            execute_code_timeout=int(os.environ.get("EXECUTE_CODE_TIMEOUT", "30")),
            run_command_timeout=int(os.environ.get("RUN_COMMAND_TIMEOUT", "30")),
            log_level=os.environ.get("LOG_LEVEL", "INFO")
        )


# Default config instance
default_config = Config.from_env()


# Constants for tool calls and memory commands
TOOL_CALL_START = "<tool_call>"
TOOL_CALL_END = "</tool_call>"

MEMORY_COMMANDS = {
    "REMEMBER": "remember:",
    "RECALL": "recall:",
    "SEARCH": "search:"
}
