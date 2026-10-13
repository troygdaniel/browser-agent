"""Configuration profiles for home and work environments."""

from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel
import yaml


class OllamaConfig(BaseModel):
    """Ollama configuration."""

    base_url: str = "http://localhost:11434"
    model: str = "deepseek-coder:6.7b"
    timeout: int = 120


class BrowserConfig(BaseModel):
    """Browser configuration."""

    headless: bool = False
    max_concurrent_tasks: int = 3
    default_timeout: int = 30
    screenshot_on_error: bool = True


class SecurityConfig(BaseModel):
    """Security and restrictions."""

    allowed_domains: Optional[List[str]] = None
    restricted_filesystem: bool = False
    require_confirmation_for_destructive: bool = True
    audit_logging: bool = False


class Config(BaseModel):
    """Application configuration."""

    profile_name: str = "home"
    ollama: OllamaConfig = OllamaConfig()
    browser: BrowserConfig = BrowserConfig()
    security: SecurityConfig = SecurityConfig()
    data_dir: Path = Path("./data")
    screenshots_dir: Path = Path("./screenshots")
    traces_dir: Path = Path("./traces")


def load_config(profile: str = "home", config_path: Optional[Path] = None) -> Config:
    """Load configuration from file or use defaults."""

    if config_path and config_path.exists():
        with open(config_path) as f:
            data = yaml.safe_load(f)
            return Config(**data)

    # Try to load from configs directory
    default_path = Path(__file__).parent.parent.parent / "configs" / f"{profile}.yaml"
    if default_path.exists():
        with open(default_path) as f:
            data = yaml.safe_load(f)
            return Config(**data)

    # Return defaults
    config = Config(profile_name=profile)

    # Adjust defaults for work profile
    if profile == "work":
        config.security.allowed_domains = [
            "localhost",
            "127.0.0.1",
            # Add your work domains here
        ]
        config.security.restricted_filesystem = True
        config.security.audit_logging = True
        config.browser.headless = True

    return config
