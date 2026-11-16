import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.router import api_router

from app.api.v1 import copilot

from app.api.metric_routes.delivery import router as delivery_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered Scrum Master Copilot API",
    docs_url="/docs",
    redoc_url="/redoc"
)

frontend_url = os.getenv(
    "FRONTEND_URL",
    "http://localhost:5173"
)

# Allow requests from the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        frontend_url,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register API routes
app.include_router(
    api_router,
    prefix=settings.API_V1_PREFIX
)

app.include_router(
    delivery_router,
    prefix=settings.API_V1_PREFIX
)


@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Welcome to Scrum Master AI Copilot API",
        "status": "running"
    }

app.include_router(
    copilot.router,
    prefix="/api/v1"
)