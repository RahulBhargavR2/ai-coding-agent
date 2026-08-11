from __future__ import annotations

import hashlib
import secrets
import hmac
from datetime import UTC, datetime, timedelta

from app.core.config import settings


class TokenService:
    """Service responsible for refresh token generation and hashing."""

    def generate_refresh_token(self) -> str:
        """
        Generate a cryptographically secure refresh token.

        Returns:
            A URL-safe random string.
        """
        return secrets.token_urlsafe(64)

    def hash_token(self, token: str) -> str:
        """
        Hash a refresh token before storing it.

        Args:
            token: Raw refresh token.

        Returns:
            SHA-256 hash of the token.
        """
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def verify_token(
        self,
        token: str,
        token_hash: str,
    ) -> bool:
        """
        Verify a refresh token against its stored hash.

        Args:
            token: Raw refresh token.
            token_hash: Stored SHA-256 hash.

        Returns:
            True if the token matches.
        """

        return hmac.compare_digest(
            hashlib.sha256(token.encode("utf-8")).hexdigest(),
            token_hash,
        )

    def get_expiration(self) -> datetime:
        """
        Compute the refresh token expiration timestamp.

        Returns:
            UTC datetime when the token expires.
        """
        return datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
