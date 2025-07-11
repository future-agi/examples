from dataclasses import dataclass, field
import os

@dataclass
class OpenAISettings:
    api_key: str = os.getenv("OPENAI_API_KEY", "")
    organization: str | None = os.getenv("OPENAI_ORG")
    timeout: int = int(os.getenv("OPENAI_TIMEOUT", "30"))
    temperature: float = float(os.getenv("OPENAI_TEMPERATURE", "0.1"))

@dataclass
class Settings:
    openai: OpenAISettings = field(default_factory=OpenAISettings)
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: str = os.getenv("LOG_FILE", "trading.log")

# Export a singleton-like config object
config = Settings() 