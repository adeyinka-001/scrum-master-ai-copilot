from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.delivery_summary import DeliverySummaryResponse
from app.services.metrics.delivery_service import get_delivery_summary

router = APIRouter(prefix="/metrics/delivery", tags=["Delivery Intelligence"])


@router.get("/summary", response_model=DeliverySummaryResponse)
def delivery_summary(
    organization_id: UUID,
    team_id: UUID,
    sprint_id: UUID,
    db: Session = Depends(get_db),
):
    return get_delivery_summary(db, organization_id, team_id, sprint_id)


from app.schemas.delivery_velocity import DeliveryVelocityResponse
from app.services.metrics.velocity_service import get_historical_velocity


@router.get("/velocity", response_model=DeliveryVelocityResponse)
def delivery_velocity(
    organization_id: UUID,
    project_id: UUID,
    team_id: UUID | None = None,
    db: Session = Depends(get_db),
):
    return get_historical_velocity(db, organization_id, project_id, team_id)
