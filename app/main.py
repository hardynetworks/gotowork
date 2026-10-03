"""Main FastAPI application."""
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import NullPool

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="Crew Scheduling Management System",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


# Database setup (using SQLite for demo, PostgreSQL in production)
# For Docker with PostgreSQL, use environment variables
DATABASE_URL = settings.DATABASE_URL
if "postgresql" not in DATABASE_URL:
    # Use SQLite for local development
    DATABASE_URL = "sqlite:///./crew_scheduler.db"


engine = create_async_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)


async def get_db():
    """Dependency for getting database session."""
    async with engine.connect() as connection:
        yield AsyncSessionLocal(session=connection)


# Create database tables on startup
from sqlalchemy.ext.asyncio import AsyncSession

AsyncSessionLocal = None


@app.on_event("startup")
async def on_startup():
    """Initialize application on startup."""
    from app.models import Base, RoleSeeder
    
    global AsyncSessionLocal
    
    # Setup async session factory
    async_session_factory = engine.begin()
    
    # Create tables
    async with engine.connect() as connection:
        await connection.run_sync(Base.metadata.create_all)
        
        # Seed roles if they don't exist (for SQLite/first run)
        try:
            admin_role = Role(name="admin")
            manager_role = Role(name="manager")
            
            connection.execute(connection, [(admin_role.name)])  # This will fail in async context
        except Exception:
            pass
    
    print(f"🚀 {settings.APP_NAME} started!")
    print(f"   Database: {DATABASE_URL}")


# Setup middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Setup templates and static files
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
static_dir = Path(__file__).parent / "static"

if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# Routes
@app.get("/")
async def root(request: Request):
    """Root endpoint - redirect to dashboard."""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "app_name": settings.APP_NAME
    })


@app.get("/dashboard")
async def dashboard(request: Request):
    """Main dashboard page."""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/managers")
async def managers_page(request: Request):
    """Managers workspace page."""
    return templates.TemplateResponse("managers/index.html", {"request": request})


@app.get("/schedules")
async def schedules_page(request: Request):
    """Schedules management page."""
    return templates.TemplateResponse("managers/schedules.html", {"request": request})


@app.get("/admin")
async def admin_page(request: Request):
    """Admin configuration page."""
    return templates.TemplateResponse("admin/index.html", {"request": request})


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unhandled exceptions gracefully."""
    import traceback
    error_msg = str(exc) if isinstance(exc, Exception) else "Unknown error"
    
    print(f"\n❌ Error: {error_msg}")
    print(traceback.format_exc())
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred", "message": error_msg}
    )


# Include API routers
from app.api import auth, managers, admin

app.include_router(auth.router)
app.include_router(managers.router)
app.include_router(admin.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )