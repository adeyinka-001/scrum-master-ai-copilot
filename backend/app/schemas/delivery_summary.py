from uuid import UUID
from pydantic import BaseModel


class CommitmentSummary(BaseModel):
    planned_points: float
    completed_committed_points: float
    remaining_committed_points: float
    completion_percentage: float


class CurrentScopeSummary(BaseModel):
    total_points: float
    completed_points: float
    remaining_points: float
    completion_percentage: float


class WorkItemSummary(BaseModel):
    total: int
    blocked: int
    in_progress: int
    bugs: int
    reopened: int
    aging: int
    scope_added_count: int


class DeliverySummaryResponse(BaseModel):
    sprint_id: UUID
    commitment: CommitmentSummary
    current_scope: CurrentScopeSummary
    work_items: WorkItemSummary
