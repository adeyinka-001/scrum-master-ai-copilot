from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.router import api_router

from app.api.metric_routes.delivery import router as delivery_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered Scrum Master Copilot API",
    docs_url="/docs",
    redoc_url="/redoc"
)


# Allow requests from the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
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