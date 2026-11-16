
import os
import random
import uuid

from collections import Counter
from datetime import timedelta

from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.database.connection import SessionLocal
from app.models.work_item import WorkItem
from app.models.work_item_state_history import WorkItemStateHistory


NAMESPACE = uuid.UUID(
    "6d69b010-5f63-4f49-a8c8-934be0a1e750"
)

BATCH_SIZE = 1000

VALID_STATES = {
    "new",
    "in_progress",
    "blocked",
    "done",
}


def synthetic_uuid(entity, number):
    return uuid.uuid5(
        NAMESPACE,
        f"scrum-copilot-synthetic:{entity}:{number}"
    )


def build_sequence(state, rng):
    """
    Generate a plausible transition sequence ending
    in the work item's actual current state.
    """

    if state == "done":
        probability = rng.random()

        if probability < 0.15:
            # Reopened after completion
            return [
                "new",
                "in_progress",
                "done",
                "in_progress",
                "done",
            ]

        if probability < 0.45:
            # Impediment resolved before completion
            return [
                "new",
                "in_progress",
                "blocked",
                "in_progress",
                "done",
            ]

        return [
            "new",
            "in_progress",
            "done",
        ]

    if state == "blocked":
        return [
            "new",
            "in_progress",
            "blocked",
        ]

    if state == "in_progress":
        return [
            "new",
            "in_progress",
        ]

    if state == "new":
        return ["new"]

    raise ValueError(f"Unsupported state: {state}")


def generate_history():

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

        items = db.execute(
            select(WorkItem)
            .where(
                WorkItem.external_id.like("SYN-WI-%")
            )
            .order_by(WorkItem.external_id)
        ).scalars().all()

        if len(items) != 5000:
            raise RuntimeError(
                f"Expected 5000 synthetic items, "
                f"found {len(items)}"
            )

        rng = random.Random(42)

        rows = []
        stats = Counter()

        def flush_batch():
            if not rows:
                return

            statement = pg_insert(
                WorkItemStateHistory
            ).values(rows)

            statement = statement.on_conflict_do_nothing(
                index_elements=["id"]
            )

            db.execute(statement)
            rows.clear()

        for item in items:

            index = int(
                item.external_id.rsplit("-", 1)[1]
            )

            if item.state not in VALID_STATES:
                raise ValueError(
                    f"Invalid state {item.state} "
                    f"for {item.external_id}"
                )

            sequence = build_sequence(
                item.state,
                rng,
            )

            start = item.created_at

            end = (
                item.completed_at
                if item.state == "done"
                else item.updated_at
            )

            if end is None or end < start:
                raise RuntimeError(
                    f"Invalid timestamps for "
                    f"{item.external_id}"
                )

            duration_seconds = (
                end - start
            ).total_seconds()

            previous_changed_at = None
            
            for position, new_state in enumerate(
                sequence,
                start=1,
            ):

                previous_state = (
                    sequence[position - 2]
                    if position > 1
                    else None
                )

                if len(sequence) == 1:
                    fraction = 0
                else:
                    fraction = (
                        (position - 1)
                        / (len(sequence) - 1)
                    )

                changed_at = start + timedelta(
                    seconds=duration_seconds * fraction
                    
                )
                # Ensure events are strictly chronological,
                # even when the original duration is zero.
                if position > 1 and changed_at <= previous_changed_at:
                    changed_at = previous_changed_at + timedelta(seconds=1)

                previous_changed_at = changed_at
                history_id = synthetic_uuid(
                    "state_history",
                    f"{index}:{position}"
                )

                rows.append({
                    "id": history_id,
                    "work_item_id": item.id,
                    "previous_state": previous_state,
                    "new_state": new_state,
                    "changed_at": changed_at,
                    "changed_by": item.assigned_to,
                    "recorded_at": changed_at,
                })

                stats["events"] += 1

                if (
                    previous_state == "done"
                    and new_state == "in_progress"
                ):
                    stats["reopened"] += 1

                if (
                    new_state == "blocked"
                ):
                    stats["blocked_events"] += 1

                if len(rows) >= BATCH_SIZE:
                    flush_batch()

        flush_batch()

        db.commit()

        print("=" * 55)
        print("STATE HISTORY SEEDING COMPLETED")
        print("=" * 55)

        print(
            f"Work items processed: {len(items)}"
        )

        print(
            f"History events: {stats['events']}"
        )

        print(
            f"Reopened items: {stats['reopened']}"
        )

        print(
            f"Blocked events: "
            f"{stats['blocked_events']}"
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    generate_history()
