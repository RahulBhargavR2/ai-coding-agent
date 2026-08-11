from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import settings
from app.database.session import init_db
from app.middleware.logging import LoggingMiddleware

from app.core.exception_handlers import register_exception_handlers



@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""

    init_db()

    yield

    # Cleanup resources here


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# Register middleware
app.add_middleware(LoggingMiddleware)

# Register exception handlers
register_exception_handlers(app)

# Register routers
app.include_router(api_router)


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
    }
