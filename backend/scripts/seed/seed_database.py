

import os
import random

from faker import Faker
from sqlalchemy import text
from sqlalchemy.engine import make_url

from app.database.connection import SessionLocal
from app.core.config import settings

from scripts.seed.seed_config import SEED_CONFIG


def validate_environment():
    environment = os.getenv(
        "APP_ENV",
        "development"
    ).lower()

    if environment not in {"development", "test"}:
        raise RuntimeError(
            "Synthetic data seeding is only allowed "
            "in development or test environments."
        )

    database_url = make_url(settings.DATABASE_URL)

    if database_url.get_backend_name() != "postgresql":
        raise RuntimeError(
            "Expected a PostgreSQL database."
        )

    if database_url.database != "scrum_copilot":
        raise RuntimeError(
            "Unexpected database name. "
            "Seeding has been stopped."
        )

    if database_url.host not in {
        "localhost",
        "127.0.0.1",
        "postgres"
    }:
        raise RuntimeError(
            "Seeding is restricted to the local "
            "development PostgreSQL instance."
        )

    print(f"Environment: {environment}")
    print(f"Database: {database_url.database}")
    print(f"Host: {database_url.host}")


def initialize_random_generators():
    random.seed(SEED_CONFIG.random_seed)

    Faker.seed(SEED_CONFIG.random_seed)

    return Faker("en_CA")


def test_database_connection():
    with SessionLocal() as db:
        result = db.execute(
            text("SELECT current_database()")
        ).scalar_one()

        print(f"Connected to PostgreSQL: {result}")


def main():
    print("=" * 55)
    print("SCRUM MASTER AI COPILOT — SYNTHETIC DATA SEEDER")
    print("=" * 55)

    validate_environment()

    fake = initialize_random_generators()

    print(f"Random seed: {SEED_CONFIG.random_seed}")
    print(f"Faker initialized: {fake.name()}")

    test_database_connection()

    print()
    print("Configuration:")
    print(f"Organizations: {SEED_CONFIG.organization_count}")
    print(f"Projects: {SEED_CONFIG.project_count}")
    print(f"Teams: {SEED_CONFIG.team_count}")
    print(f"Users: {SEED_CONFIG.user_count}")
    print(f"Sprints: {SEED_CONFIG.sprint_count}")
    print(f"Work items: {SEED_CONFIG.work_item_count}")

    print()
    print("Seeder infrastructure ready.")
    print("No records have been inserted.")


if __name__ == "__main__":
    main()