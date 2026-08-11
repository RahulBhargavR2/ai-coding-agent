from __future__ import annotations

import uuid

from sqlalchemy import String,ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import BaseModel
from app.models.enums import ProjectStatus

class Project(BaseModel):
    """Represents a software project within a workspace."""

    __tablename__='projects'



    __table_args__ = (
        UniqueConstraint(
            "workspace_id",
            "name",
            name="uq_workspace_project_name",
        ),
    )

    workspace_id :Mapped[uuid.UUID] = mapped_column(
        ForeignKey('workspaces.id',ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    name:Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    description:Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True
    )

    primary_language : Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus),
        default=ProjectStatus.ACTIVE,
        nullable=False,
    )

    workspace: Mapped["Workspace"] = relationship(
        back_populates="projects",
    )

    repositories: Mapped[list["Repository"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
