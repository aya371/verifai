"""
API Key Manager
Save to: backend/security/api_key_manager.py

Responsibilities:
- Validate the Anthropic API key on startup
- Mask keys in logs (never expose full key)
- Provide a single access point for the key throughout the app
- Warn if key is missing, malformed, or using a placeholder value
"""
import os
import re
from typing import Optional
from backend.utils.logger import logger


class APIKeyManager:
    """
    Centralized API key access and validation.

    Usage:
        from backend.security.api_key_manager import api_key_manager
        key = api_key_manager.get_key("ANTHROPIC_API_KEY")
    """

    # Known placeholder values that should never reach production
    _PLACEHOLDER_VALUES = {
        "your-api-key-here",
        "sk-ant-api03-your-key",
        "YOUR_API_KEY",
        "placeholder",
        "test",
        "changeme",
        "",
    }

    # Expected prefix for Anthropic keys
    _ANTHROPIC_PREFIX = "sk-ant-"

    def __init__(self):
        self._validated: dict = {}
        logger.info("APIKeyManager initialized")

    def get_key(self, key_name: str) -> Optional[str]:
        """
        Retrieve and validate an API key from environment variables.
        Returns the key if valid, raises ValueError if missing or malformed.
        """
        value = os.getenv(key_name, "").strip()

        if not value or value in self._PLACEHOLDER_VALUES:
            raise ValueError(
                f"API key '{key_name}' is missing or set to a placeholder value. "
                f"Please set it in your .env file."
            )

        # Anthropic-specific validation
        if key_name == "ANTHROPIC_API_KEY":
            self._validate_anthropic_key(value)

        # Log masked version only — never log the real key
        masked = self._mask(value)
        if key_name not in self._validated:
            logger.info(f"API key '{key_name}' loaded: {masked}")
            self._validated[key_name] = True

        return value

    def validate_all(self) -> dict:
        """
        Check all expected API keys on startup.
        Returns a status dict — does not raise, just reports.
        """
        results = {}
        keys_to_check = ["ANTHROPIC_API_KEY"]

        for key_name in keys_to_check:
            try:
                self.get_key(key_name)
                results[key_name] = "ok"
            except ValueError as e:
                results[key_name] = f"error: {e}"
                logger.warning(f"API key validation failed: {e}")

        return results

    def mask(self, key_name: str) -> str:
        """Return a masked version of a key for safe display in logs or UI."""
        value = os.getenv(key_name, "")
        return self._mask(value) if value else "[not set]"

    # ── Private helpers ───────────────────────────────────────────────────

    def _validate_anthropic_key(self, value: str) -> None:
        """Validate format of an Anthropic API key."""
        if not value.startswith(self._ANTHROPIC_PREFIX):
            raise ValueError(
                f"ANTHROPIC_API_KEY does not start with '{self._ANTHROPIC_PREFIX}'. "
                f"Check that you copied the full key from console.anthropic.com."
            )
        # Minimum length check (real keys are ~100+ chars)
        if len(value) < 40:
            raise ValueError(
                "ANTHROPIC_API_KEY appears too short. "
                "Ensure the full key is in your .env file."
            )

    @staticmethod
    def _mask(value: str) -> str:
        """Show first 12 chars and last 4 chars, mask the rest."""
        if len(value) <= 16:
            return "****"
        return value[:12] + "****" + value[-4:]


# Singleton — import and use this instance everywhere
api_key_manager = APIKeyManager()
