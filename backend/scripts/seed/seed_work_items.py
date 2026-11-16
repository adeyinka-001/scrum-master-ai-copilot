
import os
import random
import uuid
from collections import Counter, defaultdict
from datetime import datetime, time, timedelta, timezone
from decimal import Decimal

from sqlalchemy import insert, select

from app.database.connection import SessionLocal
from app.models.project import Project
from app.models.project_team import ProjectTeam
from app.models.sprint import Sprint
from app.models.team_membership import TeamMembership
from app.models.work_item import WorkItem
from scripts.seed.seed_config import SEED_CONFIG
from scripts.seed.seed_database import validate_environment


NAMESPACE = uuid.UUID(
    "6d69b010-5f63-4f49-a8c8-934be0a1e750"
)

TYPE_COUNTS = {
    "epic": 50,
    "feature": 200,
    "user_story": 3000,
    "task": 1000,
    "bug": 750,
}

# Completion probabilities for historical sprints.
# These are synthetic scenario assumptions.
TEAM_COMPLETION_RATES = [
    0.94,  # High performing
    0.87,  # Stable
    0.77,  # Improving
    0.59,  # Struggling
    0.69,  # Unstable
    0.65,  # Scope creep
    0.73,  # Quality issues
    0.56,  # Overloaded
]

STORY_POINTS = [1, 2, 3, 5, 8, 13]


def synthetic_uuid(entity, number):
    return uuid.uuid5(
        NAMESPACE,
        f"scrum-copilot-synthetic:{entity}:{number}",
    )


def as_timestamp(day, hour=10):
    return datetime.combine(
        day,
        time(hour=hour, tzinfo=timezone.utc),
    )


def main():
    validate_environment()

    if os.getenv("APP_ENV", "").lower() not in {
        "development", "test"
    }:
        raise RuntimeError("Development/test only.")

    if sum(TYPE_COUNTS.values()) != SEED_CONFIG.work_item_count:
        raise RuntimeError("Work-item configuration mismatch.")

    rng = random.Random(SEED_CONFIG.random_seed)
    db = SessionLocal()

    try:
        org_id = synthetic_uuid("organization", 1)

        associations = db.execute(
            select(ProjectTeam)
            .join(
                Project,
                Project.id == ProjectTeam.project_id,
            )
            .where(Project.organization_id == org_id)
            .order_by(ProjectTeam.team_id)
        ).scalars().all()

        if len(associations) != SEED_CONFIG.team_count:
            raise RuntimeError(
                "Synthetic project-team foundation is incomplete."
            )

        teams = []

        for association in associations:
            sprints = db.execute(
                select(Sprint)
                .where(
                    Sprint.project_id == association.project_id,
                    Sprint.team_id == association.team_id,
                    Sprint.name.like("Synthetic Sprint %"),
                )
                .order_by(Sprint.start_date)
            ).scalars().all()

            members = db.execute(
                select(TeamMembership)
                .where(
                    TeamMembership.team_id == association.team_id,
                    TeamMembership.left_at.is_(None),
                )
                .order_by(TeamMembership.user_id)
            ).scalars().all()

            if len(sprints) != 15 or not members:
                raise RuntimeError(
                    f"Incomplete sprint/member data for "
                    f"team {association.team_id}"
                )

            teams.append({
                "project_id": association.project_id,
                "team_id": association.team_id,
                "sprints": sprints,
                "members": [m.user_id for m in members],
            })

        # Existing synthetic work-item IDs.
        # This supports safe reruns and partial recovery.
        existing_ids = set(
            db.execute(
                select(WorkItem.id)
                .where(
                    WorkItem.external_id.like("SYN-WI-%")
                )
            ).scalars().all()
        )

        type_sequence = []

        for item_type, count in TYPE_COUNTS.items():
            type_sequence.extend([item_type] * count)

        rng.shuffle(type_sequence)

        # Prepare metadata first so parent IDs are known.
        specs = []
        parent_ids = defaultdict(
            lambda: {"epic": [], "feature": []}
        )

        for index, item_type in enumerate(type_sequence, 1):
            team_index = (index - 1) % len(teams)
            team = teams[team_index]

            # Distribute work across all 15 sprints.
            sprint_index = ((index - 1) // len(teams)) % 15
            sprint = team["sprints"][sprint_index]

            item_id = synthetic_uuid("work_item", index)

            spec = {
                "index": index,
                "id": item_id,
                "type": item_type,
                "team_index": team_index,
                "team": team,
                "sprint": sprint,
            }

            specs.append(spec)

            if item_type in {"epic", "feature"}:
                parent_ids[team["project_id"]][item_type].append(
                    item_id
                )

        now = datetime.now(timezone.utc)
        records_by_type = defaultdict(list)
        counts = Counter()

        for spec in specs:
            index = spec["index"]
            item_type = spec["type"]
            team = spec["team"]
            sprint = spec["sprint"]
            team_index = spec["team_index"]

            project_id = team["project_id"]

            # Epics and features are project-level backlog
            # items. Stories, tasks and bugs belong to sprints.
            sprint_id = (
                None
                if item_type in {"epic", "feature"}
                else sprint.id
            )

            # Some work is introduced after sprint start.
            is_scope_added = (
                sprint_id is not None
                and rng.random() < 0.15
            )

            if is_scope_added:
                created_day = (
                    sprint.start_date
                    + timedelta(days=rng.randint(1, 7))
                )
            else:
                created_day = (
                    sprint.start_date
                    - timedelta(days=rng.randint(1, 14))
                )

            created_at = as_timestamp(created_day)

            # Historical sprint outcomes.
            if sprint.status == "completed":
                completion_rate = TEAM_COMPLETION_RATES[
                    team_index
                ]
                is_done = rng.random() < completion_rate
            elif sprint.status == "active":
                is_done = rng.random() < 0.30
            else:
                is_done = False

            if item_type in {"epic", "feature"}:
                # Parent records are kept in backlog initially.
                is_done = False
                state = "backlog"
            elif is_done:
                state = "done"
            else:
                state = rng.choice(
                    ["todo", "in_progress", "backlog"]
                )

            completed_at = None

            if state == "done":
                latest_day = min(
                    sprint.end_date,
                    now.date(),
                )

                earliest_day = max(
                    sprint.start_date,
                    created_day,
                )

                if earliest_day <= latest_day:
                    days_available = (
                        latest_day - earliest_day
                    ).days

                    completed_day = (
                        earliest_day
                        + timedelta(
                            days=rng.randint(0, days_available)
                        )
                    )

                    completed_at = as_timestamp(
                        completed_day, hour=16
                    )
                else:
                    state = "in_progress"

            updated_at = completed_at or max(
                created_at,
                as_timestamp(
                    min(sprint.end_date, now.date()),
                    hour=16,
                ),
            )

            # Parent relationships are limited to the
            # same project, avoiding cross-project links.
            parent_id = None

            if item_type == "feature":
                candidates = parent_ids[project_id]["epic"]
                if candidates:
                    parent_id = rng.choice(candidates)

            elif item_type in {"user_story", "task", "bug"}:
                candidates = parent_ids[project_id]["feature"]
                if candidates:
                    parent_id = rng.choice(candidates)

            if item_type == "user_story":
                story_points = Decimal(
                    rng.choice(STORY_POINTS)
                )
            elif item_type == "bug":
                story_points = Decimal(
                    rng.choice([1, 2, 3, 5])
                )
            elif item_type == "task":
                story_points = Decimal(
                    rng.choice([1, 2, 3])
                )
            else:
                story_points = None

            title_prefix = {
                "epic": "Strategic delivery initiative",
                "feature": "Business capability",
                "user_story": "Implement user requirement",
                "task": "Engineering implementation task",
                "bug": "Resolve application defect",
            }[item_type]

            record = {
                "id": spec["id"],
                "project_id": project_id,
                "sprint_id": sprint_id,
                "assigned_to": rng.choice(team["members"]),
                "parent_id": parent_id,
                "external_id": f"SYN-WI-{index:05d}",
                "title": f"{title_prefix} {index:05d}",
                "description": (
                    f"Synthetic {item_type} for Agile delivery "
                    f"analytics and Scrum Master AI Copilot testing."
                ),
                "work_item_type": item_type,
                "state": state,
                "priority": rng.randint(1, 4),
                "story_points": story_points,
                "created_at": created_at,
                "updated_at": updated_at,
                "completed_at": completed_at,
            }

            if spec["id"] not in existing_ids:
                records_by_type[item_type].append(record)
                counts[item_type] += 1

        # Explicit parent-before-child insertion.
        # Avoids foreign-key ordering problems.
        for item_type in [
            "epic",
            "feature",
            "user_story",
            "task",
            "bug",
        ]:
            rows = records_by_type[item_type]

            for offset in range(0, len(rows), 500):
                batch = rows[offset:offset + 500]

                if batch:
                    db.execute(
                        insert(WorkItem),
                        batch,
                    )

            db.flush()

        db.commit()

        print("=" * 55)
        print("SYNTHETIC WORK-ITEM SEEDING COMPLETED")
        print("=" * 55)

        for item_type in TYPE_COUNTS:
            print(f"{item_type}: {counts[item_type]} created")

        print(f"Total created: {sum(counts.values())}")
        print(f"Previously existing: {len(existing_ids)}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()
