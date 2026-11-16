import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class SprintCommitmentResponse(BaseModel):
    id: uuid.UUID
    sprint_id: uuid.UUID
    work_item_id: uuid.UUID
    committed_story_points: Decimal
    committed_at: datetime

    model_config = ConfigDict(from_attributes=True)