
from uuid import UUID
from app.models.team import Team
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session


from app.models.sprint import Sprint
from app.models.project import Project


from app.models.organization import Organization
from app.database.repositories.dashboard_metrics_repository import (
    DashboardMetricsRepository,
)
from app.schemas.dashboard_metrics import (
    DashboardMetricsResponse,
    DashboardSprintContext,
    DashboardDelivery,
    DashboardWorkItems,
)


class DashboardMetricsService:

    def __init__(self, db: Session):
        self.db = db
        self.repository = DashboardMetricsRepository(db)

    def get_dashboard_metrics(
        self,
        organization_id: UUID,
        team_id: UUID, 
        sprint_id: UUID,
    ) -> DashboardMetricsResponse:

        # Verify the organization exists.
        organization = self.db.scalar(
            select(Organization).where(
                Organization.id == organization_id
            )
        )

        if organization is None:
            raise HTTPException(
                status_code=404,
                detail="Organization not found",
            )

        # 2. Validate team
        team = self.db.scalar(
            select(Team).where(
                Team.id == team_id,
                Team.organization_id == organization_id,
            )
        )

        if team is None:
            raise HTTPException(
                    status_code=404,
                    detail="Team not found in this organization",
            )

        sprint = self.db.scalar(
            select(Sprint)
            .join(Project, Sprint.project_id == Project.id)
            .where(
                    Sprint.id == sprint_id,
                    Sprint.team_id == team_id,
                    Project.organization_id == organization_id,
            )
        )

        if sprint is None:
            raise HTTPException(
                status_code=404,
                detail="Sprint not found for this team",
            )
        
        # 4. Retrieve sprint-specific metrics
        delivery = self.repository.get_delivery(
            organization_id, team_id,
            sprint_id,
        )

        work_items = self.repository.get_work_item_health(
            organization_id, team_id,
            sprint_id,
        )
        # 5. Build sprint context
        context = DashboardSprintContext(
            organization_id=organization.id,
            team_id=team.id,
            team_name=team.name,
            sprint_id=sprint.id,
            sprint_name=sprint.name,
            sprint_status=sprint.status,
            start_date=sprint.start_date,
            end_date=sprint.end_date,
        )

        return DashboardMetricsResponse(
            context=context,
            delivery=DashboardDelivery(**delivery),
            work_items=DashboardWorkItems(**work_items),
        )
        