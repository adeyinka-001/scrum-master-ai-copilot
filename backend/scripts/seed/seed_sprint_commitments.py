
import os
import uuid
from collections import Counter
from datetime import datetime, time, timezone
from decimal import Decimal

from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.database.connection import SessionLocal
from app.models.project import Project
from app.models.sprint import Sprint
from app.models.work_item import WorkItem
from app.models.sprint_commitment import SprintCommitment

from scripts.seed.seed_config import SEED_CONFIG


NAMESPACE = uuid.UUID(
    "6d69b010-5f63-4f49-a8c8-934be0a1e750"
)

BATCH_SIZE = 500


def synthetic_uuid(entity, identifier):
    return uuid.uuid5(
        NAMESPACE,
        f"scrum-copilot-synthetic:{entity}:{identifier}"
    )


def sprint_start_timestamp(start_date):
    # Synthetic sprint planning occurs at noon UTC
    # on the sprint start date.
    return datetime.combine(
        start_date,
        time(12, 0),
        tzinfo=timezone.utc,
    )


def seed_commitments():

    if os.getenv("APP_ENV", "").lower() not in {
        "development",
        "test",
    }:
        raise RuntimeError(
            "Synthetic seeding is restricted to development/test."
        )

    db = SessionLocal()

    try:
        database_name = db.execute(
            select(func.current_database())
        ).scalar_one()

        if database_name != "scrum_copilot":
            raise RuntimeError(
                f"Unexpected database: {database_name}"
            )

        org_id = synthetic_uuid("organization", 1)

        sprints = db.execute(
            select(Sprint)
            .join(
                Project,
                Sprint.project_id == Project.id,
            )
            .where(
                Project.organization_id == org_id,
                Sprint.name.like("Synthetic Sprint %"),
            )
            .order_by(
                Sprint.team_id,
                Sprint.start_date,
            )
        ).scalars().all()

        if len(sprints) != SEED_CONFIG.sprint_count:
            raise RuntimeError(
                f"Expected {SEED_CONFIG.sprint_count} "
                f"synthetic sprints, found {len(sprints)}"
            )

        rows = []
        stats = Counter()

        for sprint in sprints:

            committed_at = sprint_start_timestamp(
                sprint.start_date
            )

            stories = db.execute(
                select(WorkItem)
                .where(
                    WorkItem.sprint_id == sprint.id,
                    WorkItem.project_id == sprint.project_id,
                    WorkItem.work_item_type == "user_story",
                    WorkItem.external_id.like("SYN-WI-%"),
                )
                .order_by(WorkItem.external_id)
            ).scalars().all()

            stats["sprints"] += 1

            for story in stories:

                # The existing work-item seeder creates
                # late-added stories after sprint start.
                if story.created_at > committed_at:
                    stats["scope_added"] += 1
                    continue

                points = (
                    Decimal(str(story.story_points))
                    if story.story_points is not None
                    else Decimal("0")
                )

                if points < 0:
                    raise RuntimeError(
                        f"Negative story points: "
                        f"{story.external_id}"
                    )

                commitment_id = synthetic_uuid(
                    "sprint_commitment",
                    f"{sprint.id}:{story.id}",
                )

                rows.append({
                    "id": commitment_id,
                    "sprint_id": sprint.id,
                    "work_item_id": story.id,
                    "committed_story_points": points,
                    "committed_at": committed_at,
                })

                stats["committed_stories"] += 1
                stats["committed_points"] += points

        # PostgreSQL UNIQUE(sprint_id, work_item_id)
        # ensures that reruns cannot duplicate commitments.
        for offset in range(0, len(rows), BATCH_SIZE):
            batch = rows[offset:offset + BATCH_SIZE]

            statement = pg_insert(
                SprintCommitment
            ).values(batch)

            statement = statement.on_conflict_do_nothing(
                index_elements=[
                    "sprint_id",
                    "work_item_id",
                ]
            )

            db.execute(statement)

        db.commit()

        print("=" * 55)
        print("SPRINT COMMITMENT SEEDING COMPLETED")
        print("=" * 55)
        print(f"Sprints processed: {stats['sprints']}")
        print(
            f"Eligible committed stories: "
            f"{stats['committed_stories']}"
        )
        print(
            f"Eligible committed points: "
            f"{stats['committed_points']}"
        )
        print(
            f"Stories added after sprint start: "
            f"{stats['scope_added']}"
        )
        print("Conflict-safe inserts enabled")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_commitments()
