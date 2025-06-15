import time
from typing import Callable, Dict, List, Optional, Union

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.exceptions import APIError


def setup_middleware(app: FastAPI) -> None:
    """Configure middleware for the FastAPI application"""
    
    # Setup CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Setup request logging middleware
    app.add_middleware(RequestLoggingMiddleware)
    
    # Setup error handling middleware
    app.add_middleware(ErrorHandlingMiddleware)
    
    # Add startup event to sync missing components
    @app.on_event("startup")
    async def sync_missing_components():
        import asyncio
        import httpx
        
        logger.info("Starting automatic sync of missing components on startup...")
        try:
            # Wait a bit to ensure the app is fully initialized
            await asyncio.sleep(5)
            
            # Call our API endpoint instead of using the task directly
            # This avoids SQLAlchemy session issues with greenlets
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.post(
                        "http://localhost:8000/api/v1/sync/missing-components",
                        json={"force": True}
                    )
                    logger.info(f"Auto-sync API response: {response.status_code}")
                except Exception as api_error:
                    logger.error(f"Error calling sync API: {str(api_error)}")
                    
            logger.info("Auto-sync of missing components initiated")
        except Exception as e:
            logger.error(f"Error during auto-sync of missing components: {str(e)}")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging request/response details"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Process request and capture any errors
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log request details
            logger.info(
                f"{request.method} {request.url.path} {response.status_code} "
                f"{process_time:.3f}s"
            )
            
            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"{request.method} {request.url.path} 500 {process_time:.3f}s - "
                f"Error: {str(e)}"
            )
            # Let error handling middleware handle the exception
            raise


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for consistent error handling and responses"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except APIError as e:
            # Handle our custom API errors
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": {
                        "code": e.error_code,
                        "message": e.detail,
                    }
                },
                headers=e.headers,
            )
        except Exception as e:
            # Log unexpected errors
            logger.exception(f"Unhandled exception: {str(e)}")
            
            # Return a generic error response
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": "An unexpected error occurred" if not settings.DEBUG else str(e),
                    }
                },
            )