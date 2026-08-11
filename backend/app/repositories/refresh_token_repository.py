from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken
from app.repositories.base_repository import BaseRepository


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    """Repository for refresh token operations."""

    def __init__(self, db: Session):
        super().__init__(db, RefreshToken)
    
    def create(self,refresh_token:RefreshToken) -> RefreshToken:
        return self._persist(refresh_token)

    def get_by_token_hash(self, token_hash: str) -> RefreshToken | None:
        """Retrieve a refresh token by its hash."""

        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)

        return self.db.scalar(stmt)

    def get_active_token(self, token_hash: str) -> RefreshToken | None:
        """Retrieve a valid, non-revoked refresh token."""

        stmt = select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.is_revoked.is_(False),
            RefreshToken.expires_at > datetime.now(timezone.utc),
        )

        return self.db.scalar(stmt)

    def revoke(self, token: RefreshToken) -> RefreshToken:
        """Revoke a refresh token."""

        token.is_revoked = True

        self.db.commit()
        self.db.refresh(token)

        return token

    def revoke_all_for_user(self, user_id: UUID) -> None:
        """Revoke all refresh tokens belonging to a user."""

        stmt = (
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .values(is_revoked=True)
        )

        self.db.execute(stmt)
        self.db.commit()

    def delete_expired_tokens(self) -> int:
        """Delete expired refresh tokens."""

        stmt = delete(RefreshToken).where(
            RefreshToken.expires_at < datetime.now(timezone.utc)
        )

        result = self.db.execute(stmt)
        self.db.commit()

        return result.rowcount or 0
