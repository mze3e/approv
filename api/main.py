"""FastAPI application entrypoint."""

import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from approv.db import DatabaseManager, init_db

logger = logging.getLogger(__name__)


async def hourly_backup(db_mgr: DatabaseManager):
    """Background task: backup DB to S3 every hour."""
    while True:
        await asyncio.sleep(3600)
        bucket = os.environ.get("APPROV_S3_BUCKET")
        if not bucket:
            continue
        try:
            key = db_mgr.backup_to_s3(bucket)
            logger.info(f"Hourly backup uploaded: {key}")
        except Exception as e:
            logger.error(f"Hourly backup failed: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database
    config_dir = os.environ.get("APPROV_CONFIG_DIR", "config")
    db_mgr = DatabaseManager()
    init_db(db_mgr, config_dir)
    logger.info("Database initialized")

    # Start hourly backup task if S3 bucket is configured
    backup_task = None
    if os.environ.get("APPROV_S3_BUCKET"):
        backup_task = asyncio.create_task(hourly_backup(db_mgr))
        logger.info("Hourly S3 backup scheduler started")

    yield

    # Cleanup
    if backup_task:
        backup_task.cancel()
        try:
            await backup_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="ApproV API",
    description="Workflow approval engine API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from api.routers import auth_router, workflow_router, form_router, tasks_router, admin_router

app.include_router(auth_router.router, prefix="/auth", tags=["Authentication"])
app.include_router(workflow_router.router, prefix="/workflows", tags=["Workflows"])
app.include_router(form_router.router, prefix="/forms", tags=["Forms"])
app.include_router(tasks_router.router, prefix="/tasks", tags=["Tasks"])
app.include_router(admin_router.router, prefix="/admin", tags=["Administration"])


@app.get("/health")
def health_check():
    return {"status": "ok"}
