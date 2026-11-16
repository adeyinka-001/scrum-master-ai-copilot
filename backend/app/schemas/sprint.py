import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from typing import Literal


class SprintCreate(BaseModel):
    project_id: uuid.UUID
    team_id: uuid.UUID
    name: str = Field(min_length=2, max_length=200)
    goal: str | None = None
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date < self.start_date:
            raise ValueError(
                "Sprint end date cannot be before start date"
            )
        return self


class SprintResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    team_id: uuid.UUID
    name: str
    goal: str | None
    start_date: date
    end_date: date
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)



class SprintUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=200
    )
    goal: str | None = None
    start_date: date | None = None
    end_date: date | None = None

    model_config = ConfigDict(extra="forbid")