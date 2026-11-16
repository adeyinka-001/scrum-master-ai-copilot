import uuid

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select

from app.database.connection import SessionLocal
from app.models.sprint import Sprint
from app.models.project_team import ProjectTeam
from app.models.project import Project

from scripts.seed.seed_config import SEED_CONFIG


NAMESPACE = uuid.UUID(
    "6d69b010-5f63-4f49-a8c8-934be0a1e750"
)


def synthetic_uuid(entity, number):
    return uuid.uuid5(
        NAMESPACE,
        f"scrum-copilot-synthetic:{entity}:{number}"
    )


def seed_sprints():
    db = SessionLocal()

    try:
        # Safety: require the synthetic foundation
        org_id = synthetic_uuid("organization", 1)

        associations = db.execute(
            select(ProjectTeam)
            .join(Project, Project.id == ProjectTeam.project_id)
            .where(Project.organization_id == org_id)
            .order_by(ProjectTeam.team_id)
        ).scalars().all()

        if len(associations) != SEED_CONFIG.team_count:
            raise RuntimeError(
                f"Expected {SEED_CONFIG.team_count} synthetic "
                f"project-team associations, found {len(associations)}."
            )

        # Fixed reference date makes the generated dataset reproducible
        reference_date = date(2026, 11, 2)

        sprint_duration_days = 14
        sprints_per_team = (
            SEED_CONFIG.sprint_count // SEED_CONFIG.team_count
        )

        if (
            SEED_CONFIG.sprint_count
            % SEED_CONFIG.team_count != 0
        ):
            raise RuntimeError(
                "Sprint count must be divisible by team count."
            )

        created = 0
        skipped = 0

        for team_index, association in enumerate(
            associations, start=1
        ):
            for sprint_number in range(
                1, sprints_per_team + 1
            ):
                global_index = (
                    (team_index - 1) * sprints_per_team
                    + sprint_number
                )

                sprint_id = synthetic_uuid(
                    "sprint", global_index
                )

                if db.get(Sprint, sprint_id) is not None:
                    skipped += 1
                    continue

                # 15 consecutive 14-day sprints.
                # Sprint 15 starts on reference_date.
                start_date = (
                    reference_date
                    - timedelta(
                        days=(
                            sprints_per_team - sprint_number
                        ) * sprint_duration_days
                    )
                )

                end_date = (
                    start_date
                    + timedelta(days=sprint_duration_days - 1)
                )

                status = (
                    "active"
                    if sprint_number == sprints_per_team
                    else "completed"
                )

                created_at = datetime.combine(
                    start_date - timedelta(days=7),
                    datetime.min.time(),
                    tzinfo=timezone.utc,
                )

                updated_at = datetime.combine(
                    start_date,
                    datetime.min.time(),
                    tzinfo=timezone.utc,
                )

                sprint = Sprint(
                    id=sprint_id,
                    project_id=association.project_id,
                    team_id=association.team_id,
                    name=f"Synthetic Sprint {sprint_number:02d}",
                    goal=(
                        f"Deliver planned sprint outcomes "
                        f"for iteration {sprint_number}"
                    ),
                    start_date=start_date,
                    end_date=end_date,
                    status=status,
                    created_at=created_at,
                    updated_at=updated_at,
                )

                db.add(sprint)
                created += 1

        db.commit()

        print("=" * 55)
        print("HISTORICAL SPRINT SEEDING COMPLETED")
        print("=" * 55)
        print(f"Created: {created}")
        print(f"Skipped existing: {skipped}")
        print(
            f"Expected total synthetic sprints: "
            f"{SEED_CONFIG.sprint_count}"
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_sprints()