import os
from typing import Optional
from functools import lru_cache


class Settings:
    """
    Application settings and configuration.
    """
    
    def __init__(self):
        try:
            # Gemini API Configuration
            self.GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
            self.GEMINI_MODEL: str = os.environ.get("GEMINI_MODEL", "gemini-2.5-pro")
            self.GEMINI_FALLBACK_MODEL: str = os.environ.get("GEMINI_FALLBACK_MODEL", "gemini-2.5-pro")
            
            # Model Configuration
            self.MAX_TOKENS: int = int(os.environ.get("MAX_TOKENS", "50000"))
            self.TEMPERATURE: float = float(os.environ.get("TEMPERATURE", "0.2"))
            self.THINKING_BUDGET: int = int(os.environ.get("THINKING_BUDGET", "15000"))
            
            # Feature Flags
            self.USE_GROUNDING: bool = os.environ.get("USE_GROUNDING", "true").lower() == "true"
            self.USE_THINKING: bool = os.environ.get("USE_THINKING", "true").lower() == "true"
            
            # Validate API key
            if not self.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY environment variable is not set")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize settings: {str(e)}")


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings instance.
    
    Returns:
        Settings instance
    """
    return Settings()

