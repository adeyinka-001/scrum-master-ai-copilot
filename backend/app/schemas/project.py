import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from pydantic import BaseModel, Field

from pydantic import BaseModel, Field, ConfigDict

class ProjectResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    project_key: str
    description: str | None
    methodology: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectCreate(BaseModel):
    organization_id: uuid.UUID
    name: str = Field(min_length=2, max_length=200)
    project_key: str = Field(
        min_length=2,
        max_length=30,
        pattern=r"^[A-Z][A-Z0-9_-]*$"
    )
    description: str | None = Field(default=None, max_length=1000)
    methodology: str = Field(default="scrum", max_length=50)





class ProjectUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=200
    )

    description: str | None = Field(
        default=None,
        max_length=1000
    )

    methodology: str | None = Field(
        default=None,
        max_length=50
    )

    status: str | None = Field(
        default=None,
        pattern="^(active|on_hold|completed|archived)$"
    )

    model_config = ConfigDict(extra="forbid")