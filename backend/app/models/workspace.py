from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import BaseModel


class Workspace(BaseModel):
    """Represents a user's workspace."""

    __tablename__='workspaces'

    user_id : Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id",ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    name:Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    is_default: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        back_populates="workspaces",
    )

    projects: Mapped[list["Project"]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
    )
    
