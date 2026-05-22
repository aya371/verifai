"""
Encryption Utilities
Save to: backend/security/encryption.py

Provides:
- Symmetric encryption for sensitive data at rest (Fernet / AES-128-CBC)
- Hash utilities for non-reversible data (tokens, fingerprints)
- Safe comparison to prevent timing attacks

This module uses Python's standard `cryptography` library.
Install if needed: pip install cryptography

Design decisions:
- Fernet is used for reversible encryption (AES-128-CBC + HMAC-SHA256)
- SHA-256 is used for one-way hashing (audit fingerprints, token IDs)
- hmac.compare_digest is used for all comparisons to prevent timing attacks
"""
import os
import hmac
import base64
import hashlib
import secrets
from typing import Optional
from backend.utils.logger import logger


# ── Attempt to import cryptography library ────────────────────────────────
try:
    from cryptography.fernet import Fernet, InvalidToken
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    _CRYPTO_AVAILABLE = True
except ImportError:
    _CRYPTO_AVAILABLE = False
    logger.warning(
        "cryptography library not installed. "
        "Encryption features disabled. "
        "Run: pip install cryptography"
    )


class EncryptionManager:
    """
    Symmetric encryption and hashing utilities.

    Encryption key is derived from the ENCRYPTION_KEY environment variable.
    If not set, a session-only key is generated (data cannot be decrypted
    after restart — suitable for temporary sensitive data only).
    """

    def __init__(self):
        self._fernet = None
        if _CRYPTO_AVAILABLE:
            self._fernet = self._load_or_generate_key()
            logger.info("EncryptionManager initialized (cryptography library available)")
        else:
            logger.warning("EncryptionManager initialized in DEGRADED mode (no cryptography library)")

    # ── Symmetric Encryption (Fernet = AES-128-CBC + HMAC-SHA256) ────────

    def encrypt(self, plaintext: str) -> Optional[str]:
        """
        Encrypt a string and return a base64-encoded ciphertext.
        Returns None if encryption is unavailable.

        Use for: storing sensitive fields that must be retrieved later
        (e.g. API tokens, personal data fields).
        """
        if not self._fernet:
            logger.warning("encrypt() called but cryptography library is not available")
            return None
        try:
            token = self._fernet.encrypt(plaintext.encode("utf-8"))
            return base64.urlsafe_b64encode(token).decode("utf-8")
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            return None

    def decrypt(self, ciphertext: str) -> Optional[str]:
        """
        Decrypt a base64-encoded ciphertext.
        Returns None if decryption fails (wrong key, tampered data, expired token).

        Never raises — returns None on any failure so callers
        can handle gracefully without exposing error details.
        """
        if not self._fernet:
            return None
        try:
            raw = base64.urlsafe_b64decode(ciphertext.encode("utf-8"))
            return self._fernet.decrypt(raw).decode("utf-8")
        except (InvalidToken, Exception) as e:
            logger.warning(f"Decryption failed (invalid token or wrong key): {type(e).__name__}")
            return None

    # ── One-Way Hashing ───────────────────────────────────────────────────

    def hash_value(self, value: str, salt: str = "") -> str:
        """
        Produce a SHA-256 hex digest of a value.
        Used for: audit log fingerprints, token IDs, non-reversible identifiers.

        Not for passwords — use bcrypt for passwords (auth_manager.py).
        """
        combined = (salt + value).encode("utf-8")
        return hashlib.sha256(combined).hexdigest()

    def hash_token(self, token: str) -> str:
        """
        Hash a session token for safe storage in audit logs.
        The full token is never logged — only its hash.
        """
        return self.hash_value(token, salt="verifai_token_")[:16]

    # ── Safe Comparison ───────────────────────────────────────────────────

    def safe_compare(self, a: str, b: str) -> bool:
        """
        Constant-time string comparison to prevent timing attacks.
        Use instead of == when comparing secrets, tokens, or hashes.
        """
        return hmac.compare_digest(
            a.encode("utf-8"),
            b.encode("utf-8")
        )

    # ── Token Generation ──────────────────────────────────────────────────

    @staticmethod
    def generate_token(length: int = 32) -> str:
        """
        Generate a cryptographically secure random token.
        Uses os.urandom via secrets — suitable for session tokens, CSRF tokens.
        """
        return secrets.token_urlsafe(length)

    @staticmethod
    def generate_salt(length: int = 16) -> str:
        """Generate a random salt for use with hash_value()."""
        return secrets.token_hex(length)

    # ── Key Management ────────────────────────────────────────────────────

    def _load_or_generate_key(self):
        """
        Load encryption key from environment or generate a session-only key.

        For persistent encryption (data survives restart):
            Set ENCRYPTION_KEY in .env to a Fernet key.
            Generate one with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

        For session-only encryption (current default):
            A new key is generated each startup. Encrypted data from previous
            sessions cannot be decrypted. Suitable for temporary sensitive data.
        """
        key_str = os.getenv("ENCRYPTION_KEY", "").strip()

        if key_str:
            try:
                key = key_str.encode("utf-8")
                fernet = Fernet(key)
                logger.info("Encryption key loaded from ENCRYPTION_KEY environment variable")
                return fernet
            except Exception:
                logger.warning(
                    "ENCRYPTION_KEY in .env is invalid. "
                    "Falling back to session-only key. "
                    "Generate a valid key with: "
                    "python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
                )

        # No key in env — generate session-only key
        key = Fernet.generate_key()
        logger.warning(
            "No ENCRYPTION_KEY set — using session-only encryption key. "
            "Encrypted data will not persist across restarts. "
            "Add ENCRYPTION_KEY to .env for persistent encryption."
        )
        return Fernet(key)


# Singleton
encryption_manager = EncryptionManager()
