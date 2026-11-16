import uuid
import random

from datetime import datetime, timezone, timedelta

from faker import Faker
from sqlalchemy import select

from app.database.connection import SessionLocal

from app.models.organization import Organization
from app.models.user import User
from app.models.organization_membership import OrganizationMembership
from app.models.team import Team
from app.models.team_membership import TeamMembership
from app.models.project import Project
from app.models.project_team import ProjectTeam

from scripts.seed.seed_config import SEED_CONFIG


NAMESPACE = uuid.UUID("6d69b010-5f63-4f49-a8c8-934be0a1e750")


def synthetic_uuid(entity, number):
    return uuid.uuid5(
        NAMESPACE,
        f"scrum-copilot-synthetic:{entity}:{number}"
    )


def seed_foundation():
    random.seed(SEED_CONFIG.random_seed)
    Faker.seed(SEED_CONFIG.random_seed)

    fake = Faker("en_CA")
    now = datetime.now(timezone.utc)

    db = SessionLocal()

    try:
        # -------------------------------------------------
        # 1. ORGANIZATION
        # -------------------------------------------------

        org_id = synthetic_uuid("organization", 1)

        organization = db.get(Organization, org_id)

        if organization is None:
            organization = Organization(
                id=org_id,
                name="Synthetic Agile Labs",
                slug=SEED_CONFIG.organization_slug,
                description="Synthetic organization for Agile analytics testing",
                created_at=now - timedelta(days=365),
            )

            db.add(organization)
        db.flush()
        # -------------------------------------------------
        # 2. USERS
        # -------------------------------------------------

        users = []

        for i in range(1, SEED_CONFIG.user_count + 1):
            user_id = synthetic_uuid("user", i)

            user = db.get(User, user_id)

            if user is None:
                user = User(
                    id=user_id,
                    email=f"synthetic.user{i:03d}@example.invalid",
                    password_hash="!synthetic-login-disabled",
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    is_active=False,
                    created_at=now - timedelta(days=365),
                    updated_at=now,
                )
                db.add(user)

            users.append(user)

        # Insert users before referencing them
        db.flush()

        # -------------------------------------------------
        # 2B. ORGANIZATION MEMBERSHIPS
        # -------------------------------------------------

        for i, user in enumerate(users, start=1):
            membership_id = synthetic_uuid(
                "organization_membership", i
            )

            if db.get(OrganizationMembership, membership_id) is None:
                db.add(
                    OrganizationMembership(
                        id=membership_id,
                        user_id=user.id,
                        organization_id=org_id,
                        role="member",
                        created_at=now - timedelta(days=365),
                    )
                )

        db.flush()

        # -------------------------------------------------
        # 3. TEAMS
        # -------------------------------------------------

        team_names = [
            "Platform Engineering",
            "Digital Experience",
            "Payments",
            "Data Engineering",
            "Cloud Infrastructure",
            "Customer Solutions",
            "Quality Engineering",
            "Integration Services",
        ]

        teams = []

        for i, name in enumerate(team_names, start=1):
            team_id = synthetic_uuid("team", i)

            team = db.get(Team, team_id)

            if team is None:
                team = Team(
                    id=team_id,
                    organization_id=org_id,
                    name=f"Synthetic {name}",
                    description=f"Agile delivery team for {name}",
                    team_type="scrum",
                    status="active",
                    created_at=now - timedelta(days=365),
                )

                db.add(team)

            teams.append(team)

        # IMPORTANT: Persist teams before creating references
        db.flush()
        # -------------------------------------------------
        # 4. TEAM MEMBERSHIPS
        # -------------------------------------------------

        for i, user in enumerate(users):
            team_index = i % len(teams)
            team = teams[team_index]

            membership_id = synthetic_uuid(
                "team_membership", i + 1
            )

            if db.get(TeamMembership, membership_id) is None:
                role = (
                    "scrum_master" if i < 8
                    else "product_owner" if i < 16
                    else "developer"
                )

                db.add(
                    TeamMembership(
                        id=membership_id,
                        team_id=team.id,
                        user_id=user.id,
                        role=role,
                        joined_at=now - timedelta(days=300),
                        left_at=None,
                    )
                )
        db.flush()
        # -------------------------------------------------
        # 5. PROJECTS
        # -------------------------------------------------

        project_names = [
            "Digital Banking Transformation",
            "Customer Experience Platform",
            "Enterprise Data Modernization",
            "Cloud Migration Program",
            "Payment Services Modernization",
        ]

        projects = []

        for i, name in enumerate(project_names, start=1):
            project_id = synthetic_uuid("project", i)

            project = db.get(Project, project_id)

            if project is None:
                project = Project(
                    id=project_id,
                    organization_id=org_id,
                    name=f"Synthetic {name}",
                    project_key=f"{SEED_CONFIG.project_key_prefix}{i:02d}",
                    description=f"Synthetic Agile project: {name}",
                    methodology="scrum",
                    status="active",
                    created_at=now - timedelta(days=365),
                    updated_at=now,
                )

                db.add(project)

            projects.append(project)
        db.flush()
        # -------------------------------------------------
        # 6. PROJECT-TEAM ASSOCIATIONS
        # -------------------------------------------------

        for i, team in enumerate(teams):
            project = projects[i % len(projects)]

            association_id = synthetic_uuid(
                "project_team", i + 1
            )

            if db.get(ProjectTeam, association_id) is None:
                db.add(
                    ProjectTeam(
                        id=association_id,
                        project_id=project.id,
                        team_id=team.id,
                        created_at=now - timedelta(days=300),
                    )
                )
        db.flush()
        # -------------------------------------------------
        # 7. COMMIT
        # -------------------------------------------------

        db.commit()

        print("Synthetic foundation seeding completed.")
        print(f"Organization: {org_id}")
        print(f"Users: {len(users)}")
        print(f"Teams: {len(teams)}")
        print(f"Projects: {len(projects)}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_foundation()