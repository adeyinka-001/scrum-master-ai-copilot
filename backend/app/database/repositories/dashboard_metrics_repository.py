from uuid import UUID
from sqlalchemy import select

from datetime import datetime, timedelta, timezone

from sqlalchemy import cast, DateTime

from sqlalchemy import select, func, case, distinct
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.team import Team
from app.models.sprint import Sprint
from app.models.work_item import WorkItem
from app.models.work_item_state_history import WorkItemStateHistory
from app.models.sprint_commitment import SprintCommitment

from sqlalchemy import (
    select,
    func,
    case,
    distinct,
    cast,
    DateTime,
    text,
)

def get_selected_sprint_ids(
    self,
    organization_id: UUID,
    team_id: UUID,
    sprint_id: UUID,
):
    return (
        select(Sprint.id)
        .join(Project, Sprint.project_id == Project.id)
        .where(
            Project.organization_id == organization_id,
            Sprint.team_id == team_id,
            Sprint.id == sprint_id,
        )
    )

class DashboardMetricsRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_selected_sprint_ids(
        self,
        organization_id: UUID,
        team_id: UUID,
        sprint_id: UUID,
    ):
        """
        Return the selected sprint ID, ensuring it belongs
        to the specified team and organization.
        """
        return (
            select(Sprint.id)
            .join(
                Project,
                Sprint.project_id == Project.id,
            )
            .where(
                Project.organization_id == organization_id,
                Sprint.team_id == team_id,
                Sprint.id == sprint_id,
            )
        )


    def get_summary(self, organization_id: UUID, team_id: UUID, sprint_id: UUID,):

        total_projects = self.db.scalar(
            select(func.count(Project.id))
            .where(Project.organization_id == organization_id)
        ) or 0

        active_teams = self.db.scalar(
            select(func.count(Team.id))
            .where(
                Team.organization_id == organization_id,
                Team.status == "active",
            )
        ) or 0

        active_sprints = self.db.scalar(
            select(func.count(Sprint.id))
            .join(Project, Sprint.project_id == Project.id)
            .where(
                Project.organization_id == organization_id,
                Sprint.status == "active",
            )
        ) or 0

        return {
            "total_projects": total_projects,
            "active_teams": active_teams,
            "active_sprints": active_sprints,
        }

    def get_delivery(self, organization_id: UUID, team_id: UUID, sprint_id: UUID,):

        # Only current active sprints
        active_sprint_ids = self.get_selected_sprint_ids(
            organization_id=organization_id,
            team_id=team_id,
            sprint_id=sprint_id,
        )
        if team_id is not None:
            active_sprint_ids = active_sprint_ids.where(
                Sprint.team_id == team_id
            )
        planned_points = self.db.scalar(
            select(
                func.coalesce(
                    func.sum(
                        SprintCommitment.committed_story_points
                    ),
                    0,
                )
            )
            .where(
                SprintCommitment.sprint_id.in_(
                    active_sprint_ids
                )
            )
        ) or 0

        completed_points = self.db.scalar(
            select(
                func.coalesce(
                    func.sum(
                        SprintCommitment.committed_story_points
                    ),
                    0,
                )
            )
            .join(
                WorkItem,
                WorkItem.id == SprintCommitment.work_item_id,
            )
            .where(
                SprintCommitment.sprint_id.in_(
                    active_sprint_ids
                ),
                WorkItem.state == "done",
            )
        ) or 0

        planned = float(planned_points)
        completed = float(completed_points)

        remaining = max(planned - completed, 0.0)

        percentage = (
            round((completed / planned) * 100, 2)
            if planned > 0
            else 0.0
        )

        return {
            "planned_points": planned,
            "completed_points": completed,
            "remaining_points": remaining,
            "completion_percentage": percentage,
        }

    def get_work_item_health(self, organization_id: UUID, team_id: UUID, sprint_id: UUID,):

        active_sprint_ids = self.get_selected_sprint_ids(
            organization_id=organization_id,
            team_id=team_id,
            sprint_id=sprint_id,
        )
        if team_id is not None:
            active_sprint_ids = active_sprint_ids.where(
                Sprint.team_id == team_id
            )
        # Use only work items in active sprints.
        base_filters = [
            WorkItem.sprint_id.in_(active_sprint_ids)
        ]

        now = datetime.now(timezone.utc)
        aging_cutoff = now - timedelta(days=14)

        stats = self.db.execute(
            select(
                func.count(WorkItem.id).label("total"),

                func.sum(
                    case(
                        (WorkItem.state == "blocked", 1),
                        else_=0,
                    )
                ).label("blocked"),

                func.sum(
                    case(
                        (WorkItem.state == "in_progress", 1),
                        else_=0,
                    )
                ).label("in_progress"),

                func.sum(
                    case(
                        (
                            WorkItem.work_item_type == "bug",
                            1,
                        ),
                        else_=0,
                    )
                ).label("bugs"),

                func.sum(
                    case(
                        (
                            (WorkItem.state != "done")
                            & (WorkItem.created_at < aging_cutoff),
                            1,
                        ),
                        else_=0,
                    )
                ).label("aging"),
            )
            .where(*base_filters)
        ).one()

        reopened = self.db.scalar(
            select(
                func.count(
                    distinct(
                        WorkItemStateHistory.work_item_id
                    )
                )
            )
            .join(
                WorkItem,
                WorkItem.id == WorkItemStateHistory.work_item_id,
            )
            .where(
                *base_filters,
                WorkItemStateHistory.previous_state == "done",
                WorkItemStateHistory.new_state == "in_progress",
            )
        ) or 0

       # =========================================================
        # SCOPE ADDED AFTER SPRINT START
        # =========================================================

        sprint_start_utc = func.timezone(
            "UTC",
            cast(Sprint.start_date, DateTime())
            + text("INTERVAL '12 hours'")
        )

        scope_added = self.db.scalar(
            select(func.count(WorkItem.id))
            .join(
                Sprint,
                Sprint.id == WorkItem.sprint_id,
            )
            .where(
                Sprint.id.in_(active_sprint_ids),

                WorkItem.work_item_type == "user_story",

                # Created after the sprint planning baseline
                WorkItem.created_at > sprint_start_utc,

                # Not part of the original commitment
                ~select(SprintCommitment.id)
                .where(
                    SprintCommitment.sprint_id == Sprint.id,
                    SprintCommitment.work_item_id == WorkItem.id,
                )
                .exists(),
            )
        ) or 0

        return {
            "total": stats.total or 0,
            "blocked": stats.blocked or 0,
            "in_progress": stats.in_progress or 0,
            "bugs": stats.bugs or 0,
            "reopened": reopened,
            "aging": stats.aging or 0,
            "scope_added": scope_added,
        }

   