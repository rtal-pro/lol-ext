from typing import Dict, Any

from fastapi import APIRouter, Depends, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import text

from app.core.config import settings
from app.db.session import get_db

router = APIRouter(tags=["health"])


@router.get(
    "/health", 
    status_code=status.HTTP_200_OK,
    summary="Health check endpoint",
    description="Returns the health status of the API and its dependencies",
)
async def health_check(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Health check endpoint to verify API and database connectivity.
    
    Returns:
        Dict: Health status of the API and its dependencies
    """
    # Check database connection
    db_status = "ok"
    db_error = None
    
    try:
        # Execute a simple query to check the database connection
        await db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        db_status = "error"
        db_error = str(e) if settings.DEBUG else "Database connection error"
    
    # Build response
    return {
        "status": "ok" if db_status == "ok" else "error",
        "api_version": settings.API_V1_STR,
        "environment": settings.ENV,
        "dependencies": {
            "database": {
                "status": db_status,
                "error": db_error,
            },
        },
    }