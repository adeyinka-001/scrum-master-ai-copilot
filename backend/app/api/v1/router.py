from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.v1.projects import router as projects_router

from app.database.connection import get_db

from app.api.v1.sprints import router as sprints_router

from app.api.v1.work_items import router as work_items_router

from app.api.v1.metrics import router as metrics_router



api_router = APIRouter()

api_router.include_router(projects_router)

@api_router.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "application": "Scrum Master AI Copilot",
        "version": "1.0.0"
    }


@api_router.get("/health/database", tags=["Health"])
def database_health(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT 1")).scalar_one()

        return {
            "status": "connected",
            "database": "PostgreSQL",
            "query_result": result
        }

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Database connection unavailable"
        )


api_router.include_router(sprints_router)

api_router.include_router(work_items_router)

api_router.include_router(metrics_router)