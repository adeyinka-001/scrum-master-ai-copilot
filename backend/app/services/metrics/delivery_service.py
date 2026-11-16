from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.work_item import WorkItem
from app.schemas.delivery_summary import DeliverySummaryResponse
from app.services.dashboard_metrics_service import DashboardMetricsService


def get_delivery_summary(
    db: Session, organization_id: UUID, team_id: UUID, sprint_id: UUID
) -> DeliverySummaryResponse:
    # Reuse existing organization/team/sprint authorization and committed-point logic.
    dashboard = DashboardMetricsService(db).get_dashboard_metrics(
        organization_id=organization_id,
        team_id=team_id,
        sprint_id=sprint_id,
    )

    # Fetch current sprint membership only after context validation succeeds.
    items = db.scalars(
        select(WorkItem).where(WorkItem.sprint_id == sprint_id)
    ).all()
    total = sum(float(item.story_points or 0) for item in items)
    completed = sum(
        float(item.story_points or 0)
        for item in items if item.state == "done"
    )

    return DeliverySummaryResponse(
        sprint_id=sprint_id,
        commitment={
            "planned_points": dashboard.delivery.planned_points,
            "completed_committed_points": dashboard.delivery.completed_points,
            "remaining_committed_points": dashboard.delivery.remaining_points,
            "completion_percentage": dashboard.delivery.completion_percentage,
        },
        current_scope={
            "total_points": round(total, 2),
            "completed_points": round(completed, 2),
            "remaining_points": round(total - completed, 2),
            "completion_percentage": round(completed / total * 100, 2) if total > 0 else 0.0,
        },
        work_items={
            "total": dashboard.work_items.total,
            "blocked": dashboard.work_items.blocked,
            "in_progress": dashboard.work_items.in_progress,
            "bugs": dashboard.work_items.bugs,
            "reopened": dashboard.work_items.reopened,
            "aging": dashboard.work_items.aging,
            "scope_added_count": dashboard.work_items.scope_added,
        },
    )
