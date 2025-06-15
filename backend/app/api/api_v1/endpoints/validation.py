from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.db.session import get_db
from app.services.validation_service import ValidationService, ValidationResult
from app.core.exceptions import ServiceError, DatabaseError
from app.api.api_v1.schemas.validation import (
    ValidationResponse,
    ValidationSummaryResponse
)

# Set up logging
logger = logging.getLogger(__name__)

# Router
router = APIRouter(tags=["validation"])


@router.post(
    "/champions",
    response_model=ValidationResponse,
    summary="Validate champion data",
    description="Validates the integrity of champion data"
)
async def validate_champions(
    background_tasks: BackgroundTasks = None,
    run_in_background: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    Validate champion data integrity
    
    Args:
        background_tasks: FastAPI background tasks
        run_in_background: Whether to run validation in background
        db: Database session
        
    Returns:
        ValidationResponse: Validation results
    """
    try:
        if run_in_background and background_tasks:
            background_tasks.add_task(_validate_champions_task, db)
            return ValidationResponse(
                entity_type="champions",
                status="started",
                message="Champion validation started in background"
            )
        else:
            # Run validation synchronously
            validation_service = ValidationService(db)
            result = await validation_service.validate_champions()
            
            return ValidationResponse(
                entity_type="champions",
                status="completed",
                is_valid=result.is_valid(),
                total_count=result.total_count,
                valid_count=result.valid_count,
                errors_count=len(result.errors),
                warnings_count=len(result.warnings),
                duration_ms=result.duration_ms,
                errors=result.errors[:20],  # Limit to first 20 errors
                warnings=result.warnings[:20]  # Limit to first 20 warnings
            )
    except Exception as e:
        logger.error(f"Error validating champions: {str(e)}", exc_info=True)
        raise ServiceError(detail=f"Error validating champions: {str(e)}")


@router.post(
    "/items",
    response_model=ValidationResponse,
    summary="Validate item data",
    description="Validates the integrity of item data"
)
async def validate_items(
    background_tasks: BackgroundTasks = None,
    run_in_background: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    Validate item data integrity
    
    Args:
        background_tasks: FastAPI background tasks
        run_in_background: Whether to run validation in background
        db: Database session
        
    Returns:
        ValidationResponse: Validation results
    """
    try:
        if run_in_background and background_tasks:
            background_tasks.add_task(_validate_items_task, db)
            return ValidationResponse(
                entity_type="items",
                status="started",
                message="Item validation started in background"
            )
        else:
            # Run validation synchronously
            validation_service = ValidationService(db)
            result = await validation_service.validate_items()
            
            return ValidationResponse(
                entity_type="items",
                status="completed",
                is_valid=result.is_valid(),
                total_count=result.total_count,
                valid_count=result.valid_count,
                errors_count=len(result.errors),
                warnings_count=len(result.warnings),
                duration_ms=result.duration_ms,
                errors=result.errors[:20],
                warnings=result.warnings[:20]
            )
    except Exception as e:
        logger.error(f"Error validating items: {str(e)}", exc_info=True)
        raise ServiceError(detail=f"Error validating items: {str(e)}")


@router.post(
    "/runes",
    response_model=ValidationResponse,
    summary="Validate rune data",
    description="Validates the integrity of rune data"
)
async def validate_runes(
    background_tasks: BackgroundTasks = None,
    run_in_background: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    Validate rune data integrity
    
    Args:
        background_tasks: FastAPI background tasks
        run_in_background: Whether to run validation in background
        db: Database session
        
    Returns:
        ValidationResponse: Validation results
    """
    try:
        if run_in_background and background_tasks:
            background_tasks.add_task(_validate_runes_task, db)
            return ValidationResponse(
                entity_type="runes",
                status="started",
                message="Rune validation started in background"
            )
        else:
            # Run validation synchronously
            validation_service = ValidationService(db)
            result = await validation_service.validate_runes()
            
            return ValidationResponse(
                entity_type="runes",
                status="completed",
                is_valid=result.is_valid(),
                total_count=result.total_count,
                valid_count=result.valid_count,
                errors_count=len(result.errors),
                warnings_count=len(result.warnings),
                duration_ms=result.duration_ms,
                errors=result.errors[:20],
                warnings=result.warnings[:20]
            )
    except Exception as e:
        logger.error(f"Error validating runes: {str(e)}", exc_info=True)
        raise ServiceError(detail=f"Error validating runes: {str(e)}")


@router.post(
    "/all",
    response_model=ValidationSummaryResponse,
    summary="Validate all data",
    description="Validates the integrity of all game data"
)
async def validate_all(
    background_tasks: BackgroundTasks = None,
    run_in_background: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    Validate all data integrity
    
    Args:
        background_tasks: FastAPI background tasks
        run_in_background: Whether to run validation in background
        db: Database session
        
    Returns:
        ValidationSummaryResponse: Summary of validation results
    """
    try:
        if run_in_background and background_tasks:
            background_tasks.add_task(_validate_all_task, db)
            return ValidationSummaryResponse(
                status="started",
                message="All data validation started in background",
                results={}
            )
        else:
            # Run validation synchronously
            validation_service = ValidationService(db)
            results = await validation_service.validate_all()
            
            # Convert results to API format
            api_results = {}
            all_valid = True
            
            for entity_type, result in results.items():
                api_results[entity_type] = {
                    "is_valid": result.is_valid(),
                    "total_count": result.total_count,
                    "valid_count": result.valid_count,
                    "errors_count": len(result.errors),
                    "warnings_count": len(result.warnings)
                }
                all_valid = all_valid and result.is_valid()
            
            return ValidationSummaryResponse(
                status="completed",
                is_valid=all_valid,
                message="All data validation completed",
                results=api_results
            )
    except Exception as e:
        logger.error(f"Error validating all data: {str(e)}", exc_info=True)
        raise ServiceError(detail=f"Error validating all data: {str(e)}")


# Background task functions
async def _validate_champions_task(db: AsyncSession):
    """Background task for validating champion data"""
    async with db.begin():
        try:
            validation_service = ValidationService(db)
            result = await validation_service.validate_champions()
            logger.info(
                f"Background champion validation completed: "
                f"{result.valid_count}/{result.total_count} valid, "
                f"{len(result.errors)} errors"
            )
        except Exception as e:
            logger.error(f"Background task error validating champions: {str(e)}", exc_info=True)


async def _validate_items_task(db: AsyncSession):
    """Background task for validating item data"""
    async with db.begin():
        try:
            validation_service = ValidationService(db)
            result = await validation_service.validate_items()
            logger.info(
                f"Background item validation completed: "
                f"{result.valid_count}/{result.total_count} valid, "
                f"{len(result.errors)} errors"
            )
        except Exception as e:
            logger.error(f"Background task error validating items: {str(e)}", exc_info=True)


async def _validate_runes_task(db: AsyncSession):
    """Background task for validating rune data"""
    async with db.begin():
        try:
            validation_service = ValidationService(db)
            result = await validation_service.validate_runes()
            logger.info(
                f"Background rune validation completed: "
                f"{result.valid_count}/{result.total_count} valid, "
                f"{len(result.errors)} errors"
            )
        except Exception as e:
            logger.error(f"Background task error validating runes: {str(e)}", exc_info=True)


async def _validate_all_task(db: AsyncSession):
    """Background task for validating all data"""
    async with db.begin():
        try:
            validation_service = ValidationService(db)
            results = await validation_service.validate_all()
            
            # Log summary
            for entity_type, result in results.items():
                logger.info(
                    f"Background {entity_type} validation completed: "
                    f"{result.valid_count}/{result.total_count} valid, "
                    f"{len(result.errors)} errors"
                )
        except Exception as e:
            logger.error(f"Background task error validating all data: {str(e)}", exc_info=True)