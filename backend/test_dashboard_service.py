from uuid import UUID

from app.database.connection import SessionLocal
from app.services.dashboard_metrics_service import DashboardMetricsService


db = SessionLocal()

try:
    service = DashboardMetricsService(db)

    organization_id = UUID(
        "7b801da2-9083-56fc-8fd6-70ed2911bfab"
    )

    result = service.get_dashboard_metrics(
        organization_id=organization_id
    )

    print(result.model_dump_json(indent=2))

finally:
    db.close()