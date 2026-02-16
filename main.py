
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from config import settings
from database import db_manager
from routers import onboarding
from routers import calculations
from routers import auth
from routers import chatbot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    logger.info("Starting up Retirement Goal API")
    # Seed default assumptions if the table is empty
    from services.assumption_service import AssumptionService
    AssumptionService.seed_defaults_if_empty()
    yield
    # Shutdown
    logger.info("Shutting down Retirement Goal API")
    db_manager.close_all()

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="API for Retirement Goal Planning and Management",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    onboarding.router,
    prefix=settings.API_V1_PREFIX
)
app.include_router(
    calculations.router,
    prefix=settings.API_V1_PREFIX
)
app.include_router(
    auth.router,
    prefix=settings.API_V1_PREFIX
)
app.include_router(
    chatbot.router,
    prefix=settings.API_V1_PREFIX
)

@app.get("/")
async def root():
    """Root endpoint - API health check"""
    return {
        "message": "Retirement Goal API",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        with db_manager.get_cursor(commit=False) as cursor:
            cursor.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "database": "disconnected"}
