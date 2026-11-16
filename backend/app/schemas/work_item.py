import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

WorkItemType = Literal["user_story", "task", "bug", "epic", "feature"]


class WorkItemCreate(BaseModel):
    project_id: uuid.UUID
    sprint_id: uuid.UUID | None = None
    assigned_to: uuid.UUID | None = None
    parent_id: uuid.UUID | None = None

    title: str = Field(min_length=2, max_length=255)
    description: str | None = None

    work_item_type: WorkItemType = "user_story"
    priority: int = Field(default=3, ge=1, le=5)
    story_points: Decimal | None = Field(default=None, ge=0)


class WorkItemResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    sprint_id: uuid.UUID | None
    assigned_to: uuid.UUID | None
    parent_id: uuid.UUID | None

    title: str
    description: str | None
    work_item_type: str
    state: str
    priority: int
    story_points: Decimal | None

    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)





WorkItemState = Literal[
    "new",
    "in_progress",
    "blocked",
    "done"
]


class WorkItemUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=2,
        max_length=255
    )
    description: str | None = None
    priority: int | None = Field(
        default=None,
        ge=1,
        le=5
    )
    story_points: Decimal | None = Field(
        default=None,
        ge=0
    )

    model_config = ConfigDict(extra="forbid")


class WorkItemTransition(BaseModel):
    new_state: WorkItemState
    changed_by: uuid.UUID | None = None


class WorkItemStateHistoryResponse(BaseModel):
    id: uuid.UUID
    work_item_id: uuid.UUID
    previous_state: str | None
    new_state: str
    changed_at: datetime
    changed_by: uuid.UUID | None

    model_config = ConfigDict(from_attributes=True)

class WorkItemSprintAssignment(BaseModel):
    sprint_id: uuid.UUID | None