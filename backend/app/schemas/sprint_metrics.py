import uuid
from datetime import date

from pydantic import BaseModel


class SprintMetricsResponse(BaseModel):
    sprint_id: uuid.UUID
    sprint_name: str
    sprint_status: str
    start_date: date
    end_date: date

    total_work_items: int
    completed_work_items: int
    remaining_work_items: int
    work_in_progress: int

    completion_rate: float

    total_story_points: float
    completed_story_points: float
    remaining_story_points: float
    story_point_completion_rate: float