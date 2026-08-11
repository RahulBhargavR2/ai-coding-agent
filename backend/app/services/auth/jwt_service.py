from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any


from jose import jwt, JWTError


from app.core.config import settings
from app.core.exceptions import InvalidToken


class JWTService:
    """Service responsible for JWT creation and validation."""

    def __init__(self) -> None:
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM

    def create_access_token(
        self,
        subject: str,
        expires_delta: timedelta | None = None,
        additional_claims: dict[str, Any] | None = None,
    ) -> str:

        """
        Create a signed JWT access token.
        """
        expire = datetime.now(UTC) + (
            expires_delta
            or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        payload : dict[str,Any] = {
            "sub": subject,
            "exp":expire,
            "type":"access"
        }

        if additional_claims:
            payload.update(additional_claims)

        return jwt.encode(
            payload,
            self.secret_key,
            algorithm=self.algorithm
        )

    def decode_token(self, token:str) -> dict[str,Any]:
        """Decode and veryfy token"""

        try:
            return jwt.decode(
                token,
                self.secret_key,
                algorithms=self.algorithm
            )
        except JWTError as exc:
            raise InvalidToken("Invalid or expired token.") from exc

    def get_subjects(self,token:str) -> str:
        """
        Extract the subject from a JWT.
        """

        payload = self.decode_token(token)

        subject = payload.get("sub")

        if subject is None:
            raise InvalidToken("Token subject is missing")
        return subject
    

    def is_access_token(self,token:str) -> bool:

        """Verify that the token is an access token"""

        payload = self.decode_token(token)

        return payload.get("type") == 'access'
    

    
