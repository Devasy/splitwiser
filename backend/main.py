from contextlib import asynccontextmanager

from app.auth.routes import router as auth_router
from app.config import settings
from app.database import close_mongo_connection, connect_to_mongo
from app.expenses.routes import balance_router
from app.expenses.routes import router as expenses_router
from app.groups.routes import router as groups_router
from app.user.routes import router as user_router
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()
    yield
    # Shutdown
    await close_mongo_connection()


app = FastAPI(
    title="Splitwiser API",
    description="Backend API for Splitwiser expense tracking application",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; object-src 'none';"
    )
    return response


# CORS middleware
allowed_origins = []
if settings.allow_all_origins:
    allowed_origins = ["*"]
elif settings.allowed_origins:
    allowed_origins = [origin.strip() for origin in settings.allowed_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


app.include_router(auth_router)
app.include_router(user_router)
app.include_router(groups_router)
app.include_router(expenses_router)
app.include_router(balance_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.debug)
