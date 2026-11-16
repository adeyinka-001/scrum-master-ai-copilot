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
