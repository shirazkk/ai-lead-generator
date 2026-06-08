from contextlib import asynccontextmanager
from typing import Dict, Any
import logging

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from config import settings
from routers import search, leads, outreach
from routers import status as status_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(_app: FastAPI):
    """
    Application lifespan manager for startup and shutdown operations.

    Startup:
    - Validate configuration
    - Initialize service connections
    - Install Playwright browsers (if needed)

    Shutdown:
    - Close open connections
    - Clean up resources
    """
    # Startup
    logger.info("Starting AI Lead Generation Backend...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Port: {settings.port}")
    logger.info(f"Allowed Origins: {settings.allowed_origins}")

    # Validate required API keys are present
    required_keys = {
        "Gemini AI API": settings.gemini_api_key,
        "OpenRoute API": settings.openrouter_api_key,
        "Supabase URL": settings.supabase_url,
        "Supabase Key": settings.supabase_key,
        "Resend API": settings.resend_api_key,
    }

    for key_name, key_value in required_keys.items():
        if not key_value or key_value.startswith("your_"):
            logger.error(f"{key_name} not configured properly - application cannot start")
            raise RuntimeError(
                f"Missing or invalid configuration: {key_name}. "
                f"Please check your .env file and ensure all API keys are properly set."
            )

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down AI Lead Generation Backend...")
    logger.info("Cleanup complete")


# Initialize FastAPI application
app = FastAPI(
    title="AI Lead Generation Agent API",
    description="Automated lead discovery, enrichment, analysis, and personalized outreach",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# CORS Middleware Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle HTTP exceptions with consistent JSON response format."""
    logger.error(f"HTTP error: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "type": "http_error",
                "message": exc.detail,
                "status_code": exc.status_code,
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request validation errors with detailed error messages."""
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "type": "validation_error",
                "message": "Request validation failed",
                "details": exc.errors(),
            }
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions with generic error response."""
    logger.exception(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "type": "internal_error",
                "message": "An unexpected error occurred",
                "detail": str(exc) if settings.environment == "development" else None,
            }
        },
    )


# Router Registration
app.include_router(search.router)
app.include_router(leads.router)
app.include_router(outreach.router)
app.include_router(status_router.router)


# Health Check Endpoint
@app.get("/health", tags=["System"])
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint for monitoring and container orchestration.

    Returns:
        dict: Service health status and configuration info
    """
    return {
        "success": True,
        "status": "healthy",
        "service": "ai-lead-generation-backend",
        "version": "1.0.0",
        "environment": settings.environment,
    }


# Root Endpoint
@app.get("/", tags=["System"])
async def root() -> Dict[str, Any]:
    """
    Root endpoint with API information.

    Returns:
        dict: API welcome message and documentation links
    """
    return {
        "success": True,
        "message": "AI Lead Generation Agent API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.environment == "development",
        log_level="info",
    )