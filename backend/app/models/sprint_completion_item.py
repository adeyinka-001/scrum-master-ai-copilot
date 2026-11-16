import uuid
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class SprintCompletionItem(Base):
    __tablename__ = "sprint_completion_items"

    __table_args__ = (
        UniqueConstraint(
            "snapshot_id",
            "work_item_id",
            name="uq_sprint_completion_item"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "sprint_completion_snapshots.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    work_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("work_items.id"),
        nullable=False,
        index=True
    )

    committed_story_points: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )

    state_at_completion: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    was_completed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False
    )