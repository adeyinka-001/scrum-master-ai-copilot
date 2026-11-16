import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class WorkItem(Base):
    __tablename__ = "work_items"

    __table_args__ = (
        CheckConstraint(
            "story_points IS NULL OR story_points >= 0",
            name="ck_work_item_story_points_nonnegative"
        ),
        Index(
            "ix_work_items_project_sprint",
            "project_id",
            "sprint_id"
        ),
        Index(
            "ix_work_items_sprint_state",
            "sprint_id",
            "state"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    sprint_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sprints.id", ondelete="SET NULL"),
        nullable=True
    )

    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("work_items.id", ondelete="SET NULL"),
        nullable=True
    )

    external_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    work_item_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    state: Mapped[str] = mapped_column(
        String(50),
        default="new",
        nullable=False
    )

    priority: Mapped[int | None] = mapped_column(
        nullable=True
    )

    story_points: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 2),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )