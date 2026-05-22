"""
API Key Manager
Save to: backend/security/api_key_manager.py

Responsibilities:
- Validate the Anthropic API key on startup
- Mask keys in logs (never expose full key)
- Provide a single access point for the key throughout the app
- Warn if key is missing, malformed, or using a placeholder value
- Warn if .env file is not in .gitignore (prevents accidental GitHub exposure)
"""
import os
import re
from pathlib import Path
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
        self._check_gitignore()          # ← NEW: warn if .env is exposed
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

    def _check_gitignore(self) -> None:
        """
        Walk up from the current working directory to find .gitignore.
        Warn loudly if .env is not listed — prevents accidental key exposure on GitHub.
        """
        cwd = Path.cwd()
        gitignore_path = None

        # Search up to 4 levels up for .gitignore
        for parent in [cwd, *cwd.parents[:3]]:
            candidate = parent / ".gitignore"
            if candidate.exists():
                gitignore_path = candidate
                break

        if gitignore_path is None:
            logger.warning(
                "SECURITY WARNING: No .gitignore file found. "
                "Create one immediately and add '.env' to it before pushing to GitHub. "
                "Your ANTHROPIC_API_KEY will be exposed if .env is committed."
            )
            return

        try:
            content = gitignore_path.read_text(encoding="utf-8")
        except OSError:
            logger.warning(f"Could not read {gitignore_path} — unable to verify .env is ignored.")
            return

        # Check that .env (not just .env.example or .env.local) is ignored
        # Matches lines like: .env  |  /.env  |  **/.env
        env_ignored = any(
            re.match(r"^[/*]*\.env\s*$", line.strip())
            for line in content.splitlines()
            if not line.strip().startswith("#")
        )

        if not env_ignored:
            logger.warning(
                "SECURITY WARNING: '.env' is not listed in %s. "
                "Add the following line to your .gitignore immediately:\n\n"
                "    .env\n\n"
                "If .env is pushed to GitHub, your ANTHROPIC_API_KEY will be exposed "
                "and should be rotated immediately at https://console.anthropic.com/",
                gitignore_path,
            )
        else:
            logger.info(f".gitignore check passed — .env is protected ({gitignore_path})")

    @staticmethod
    def _mask(value: str) -> str:
        """Show first 12 chars and last 4 chars, mask the rest."""
        if len(value) <= 16:
            return "****"
        return value[:12] + "****" + value[-4:]


# Singleton — import and use this instance everywhere
api_key_manager = APIKeyManager()
