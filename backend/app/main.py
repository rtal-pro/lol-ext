import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
from loguru import logger

from app.api.api_v1.api import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.middleware import setup_middleware
from app.db.data_manager import DataDragonManager
from app.db.session import AsyncSessionLocal, get_db
from app.services.scheduler_service import SchedulerService, create_data_sync_tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events (startup and shutdown)
    """
    # Setup logging
    setup_logging()
    logger.info(f"Starting {settings.PROJECT_NAME} in {settings.ENV} environment")
    
    # Initialize scheduler
    scheduler = None
    if settings.ENABLE_SCHEDULED_TASKS and settings.ENV != "test":
        logger.info("Initializing scheduler service")
        scheduler = SchedulerService()
        create_data_sync_tasks(scheduler, get_db)
    
    # Initialize database on startup
    async with AsyncSessionLocal() as session:
        try:
            # Setup initial data if needed
            if settings.ENV != "test":
                # Initialize Data Dragon manager
                data_manager = DataDragonManager(session)
                
                # Check for Data Dragon updates
                updates_needed = await data_manager.check_for_updates()
                if any(updates_needed.values()):
                    logger.info("Data Dragon updates available, will be applied in background")
                    
                    # Apply updates immediately if no scheduler
                    if not scheduler:
                        logger.info("Applying Data Dragon updates now")
                        await data_manager.update_all(force=False)
                        await session.commit()
                
                # Close HTTP client
                await data_manager.close()
            
            logger.info("Application startup complete")
        except Exception as e:
            logger.error(f"Error during application startup: {str(e)}")
            raise
    
    # Start scheduler
    if scheduler:
        logger.info("Starting scheduler service")
        await scheduler.start()
    
    # Yield control back to FastAPI
    yield
    
    # Shutdown scheduler
    if scheduler:
        logger.info("Stopping scheduler service")
        await scheduler.stop()
    
    # Shutdown tasks
    logger.info("Shutting down application")


def create_application() -> FastAPI:
    """
    Create and configure FastAPI application
    
    Returns:
        FastAPI: Configured FastAPI application
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="API for League of Legends Chrome Extension",
        version="0.1.0",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=None,  # Disable default docs
        redoc_url=None,  # Disable default redoc
        lifespan=lifespan,
    )
    
    # Setup middleware
    setup_middleware(app)
    
    # Include API router
    app.include_router(api_router, prefix=settings.API_V1_STR)
    
    # Add 404 exception handler for item endpoints
    @app.exception_handler(404)
    async def item_not_found_handler(request, exc):
        import asyncio
        import logging
        from fastapi.responses import JSONResponse
        
        logger = logging.getLogger(__name__)
        path = request.url.path
        
        # Check if this is an item endpoint that's missing
        if "/items/" in path and "/api/v1/" in path:
            # Extract the item ID from the path
            parts = path.split("/")
            if len(parts) > 2:
                item_id = parts[-1]
                
                # If the item ID seems valid (all digits)
                if item_id.isdigit():
                    logger.warning(f"Item {item_id} not found, triggering background sync of missing components")
                    
                    # Don't run in background task - just trigger a manual sync via API
                    # This way we avoid SQLAlchemy session issues
                    import httpx
                    
                    # Create a task to call our sync endpoint
                    async def call_sync_endpoint():
                        try:
                            # Use httpx to call our own API endpoint for syncing
                            async with httpx.AsyncClient() as client:
                                # Call the sync/missing-components endpoint
                                url = f"http://localhost:{request.url.port}/api/v1/sync/missing-components"
                                logger.info(f"Calling sync endpoint: {url}")
                                
                                # Use background=true to run it in background
                                response = await client.post(
                                    url, 
                                    json={"background": True}
                                )
                                logger.info(f"Sync endpoint response: {response.status_code}")
                        except Exception as e:
                            logger.error(f"Error calling sync endpoint: {str(e)}")
                    
                    # Run the API call in a separate task
                    asyncio.create_task(call_sync_endpoint())
                    
                    # Return a more helpful error message
                    return JSONResponse(
                        status_code=404,
                        content={
                            "detail": f"Item {item_id} not found. A background sync has been triggered to import missing items. Please try again in a few moments."
                        }
                    )
        
        # Return standard 404 for other endpoints
        return JSONResponse(
            status_code=404,
            content={"detail": "Not Found"}
        )
    
    # Custom docs endpoint with authentication if needed
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url=f"{settings.API_V1_STR}/openapi.json",
            title=f"{settings.PROJECT_NAME} - Swagger UI",
        )
    
    return app


app = create_application()