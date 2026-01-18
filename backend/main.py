from contextlib import asynccontextmanager

from app.auth.routes import router as auth_router
from app.config import RequestResponseLoggingMiddleware, logger, settings
from app.database import close_mongo_connection, connect_to_mongo
from app.expenses.routes import balance_router
from app.expenses.routes import router as expenses_router
from app.groups.routes import router as groups_router
from app.integrations.router import router as integrations_router
from app.user.routes import router as user_router
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Lifespan: Connecting to MongoDB...")
    await connect_to_mongo()
    logger.info("Lifespan: MongoDB connected.")
    yield
    # Shutdown
    logger.info("Lifespan: Closing MongoDB connection...")
    await close_mongo_connection()
    logger.info("Lifespan: MongoDB connection closed.")


app = FastAPI(
    title="Splitwiser API",
    description="Backend API for Splitwiser expense tracking application",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware - Enhanced configuration for production
allowed_origins = []
if settings.allow_all_origins:
    # Allow all origins in development mode
    allowed_origins = ["*"]
    logger.debug("Development mode: CORS configured to allow all origins")
elif settings.allowed_origins:
    # Use specified origins in production mode
    allowed_origins = [
        origin.strip()
        for origin in settings.allowed_origins.split(",")
        if origin.strip()
    ]
else:
    # Fallback to allow all origins if not specified (not recommended for production)
    allowed_origins = ["*"]

logger.info(f"Allowed CORS origins: {allowed_origins}")

app.add_middleware(RequestResponseLoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Origin",
        "Cache-Control",
        "Pragma",
        "X-CSRFToken",
    ],
    expose_headers=["*"],
    max_age=3600,  # Cache preflight responses for 1 hour
)


# Add a catch-all OPTIONS handler that should work for any path
@app.options("/{path:path}")
async def options_handler(request: Request, path: str):
    """Handle all OPTIONS requests"""
    logger.info(f"OPTIONS request received for path: /{path}")
    logger.info(f"Origin: {request.headers.get('origin', 'No origin header')}")

    response = Response(status_code=200)

    # Manually set CORS headers for debugging
    origin = request.headers.get("origin")
    if origin and (origin in allowed_origins or "*" in allowed_origins):
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = (
            "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH"
        )
        response.headers["Access-Control-Allow-Headers"] = (
            "Accept, Accept-Language, Content-Language, Content-Type, Authorization, X-Requested-With, Origin, Cache-Control, Pragma, X-CSRFToken"
        )
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Max-Age"] = "3600"
    elif "*" in allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = (
            "GET, POST, PUT, DELETE, OPTIONS, HEAD, PATCH"
        )
        response.headers["Access-Control-Allow-Headers"] = (
            "Accept, Accept-Language, Content-Language, Content-Type, Authorization, X-Requested-With, Origin, Cache-Control, Pragma, X-CSRFToken"
        )
        response.headers["Access-Control-Max-Age"] = "3600"

    return response


# Health check
@app.get("/health")
async def health_check():
    """
    Returns the health status of the Splitwiser API service.

    This endpoint can be used for health checks and monitoring.
    """
    return {"status": "healthy", "service": "Splitwiser API"}


# Include routers
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(groups_router)
app.include_router(expenses_router)
app.include_router(balance_router)
app.include_router(integrations_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.debug)
