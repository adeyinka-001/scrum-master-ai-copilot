from dataclasses import dataclass


@dataclass(frozen=True)
class SeedConfig:
    random_seed: int = 42

    organization_count: int = 1
    project_count: int = 5
    team_count: int = 8
    user_count: int = 60

    sprint_count: int = 120
    work_item_count: int = 5000

    historical_months: int = 12

    organization_slug: str = "synthetic-agile-labs"
    project_key_prefix: str = "SYN"

    # Explicit safety control
    development_only: bool = True


SEED_CONFIG = SeedConfig()