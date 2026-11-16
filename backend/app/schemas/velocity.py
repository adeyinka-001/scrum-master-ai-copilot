import uuid
from datetime import date

from pydantic import BaseModel


class SprintVelocityResponse(BaseModel):
    sprint_id: uuid.UUID
    sprint_name: str
    start_date: date
    end_date: date

    committed_points: float
    completed_points: float
    velocity: float
    predictability: float


class ProjectVelocityResponse(BaseModel):
    project_id: uuid.UUID
    sprint_count: int
    average_velocity: float
    average_predictability: float
    sprints: list[SprintVelocityResponse]