from datetime import date
from uuid import UUID
from pydantic import BaseModel


class SprintHistoricalVelocity(BaseModel):
    sprint_id: UUID
    sprint_name: str
    start_date: date
    end_date: date
    committed_points: float
    completed_points: float
    velocity: float
    predictability: float | None
    unknown_points: float
    unknown_item_count: int


class DeliveryVelocityResponse(BaseModel):
    project_id: UUID
    team_id: UUID | None
    sprint_count: int
    average_velocity: float | None
    average_predictability: float | None
    data_complete: bool
    note: str
    sprints: list[SprintHistoricalVelocity]
