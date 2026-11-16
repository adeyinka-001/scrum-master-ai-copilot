from uuid import UUID
from datetime import date, datetime

from pydantic import BaseModel, Field


class DashboardSprintContext(BaseModel):
    organization_id: UUID
    team_id: UUID
    team_name: str
    sprint_id: UUID
    sprint_name: str
    sprint_status: str
    start_date: date | datetime
    end_date: date | datetime


class DashboardDelivery(BaseModel):
    planned_points: float = 0.0
    completed_points: float = 0.0
    remaining_points: float = 0.0

    completion_percentage: float = Field(
        default=0.0,
        ge=0,
        le=100,
    )


class DashboardWorkItems(BaseModel):
    total: int = 0
    blocked: int = 0
    in_progress: int = 0
    bugs: int = 0
    reopened: int = 0
    aging: int = 0
    scope_added: int = 0


class DashboardMetricsResponse(BaseModel):
    context: DashboardSprintContext
    delivery: DashboardDelivery
    work_items: DashboardWorkItems