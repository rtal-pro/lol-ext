from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.scheduler_service import SchedulerService
from app.core.exceptions import ServiceError
from app.api.api_v1.schemas.scheduler import (
    SchedulerStatusResponse,
    TaskInfo,
    TaskListResponse,
    TaskCreateRequest,
    TaskUpdateRequest
)

router = APIRouter(tags=["scheduler"])


@router.get(
    "/status",
    response_model=SchedulerStatusResponse,
    summary="Get scheduler status",
    description="Returns the current status of the scheduler service"
)
async def get_scheduler_status():
    """
    Get the current status of the scheduler service
    
    Returns:
        SchedulerStatusResponse: Status of the scheduler
    """
    try:
        scheduler = SchedulerService()
        
        return SchedulerStatusResponse(
            running=scheduler.running,
            tasks_count=len(scheduler.tasks),
            poll_interval=scheduler.poll_interval
        )
    except Exception as e:
        raise ServiceError(detail=f"Error getting scheduler status: {str(e)}")


@router.get(
    "/tasks",
    response_model=TaskListResponse,
    summary="Get all scheduled tasks",
    description="Returns a list of all scheduled tasks"
)
async def get_scheduled_tasks():
    """
    Get all scheduled tasks
    
    Returns:
        TaskListResponse: List of scheduled tasks
    """
    try:
        scheduler = SchedulerService()
        tasks = scheduler.get_all_tasks()
        
        return TaskListResponse(
            tasks=[TaskInfo(**task.to_dict()) for task in tasks]
        )
    except Exception as e:
        raise ServiceError(detail=f"Error getting scheduled tasks: {str(e)}")


@router.post(
    "/tasks/{task_name}/run",
    response_model=TaskInfo,
    summary="Run a specific task",
    description="Runs a scheduled task immediately"
)
async def run_task(task_name: str):
    """
    Run a scheduled task immediately
    
    Args:
        task_name: Name of the task to run
        
    Returns:
        TaskInfo: Updated task information
    """
    try:
        scheduler = SchedulerService()
        task = scheduler.get_task(task_name)
        
        if not task:
            raise ServiceError(detail=f"Task {task_name} not found", error_code="TASK_NOT_FOUND")
        
        success = await scheduler.run_task(task_name)
        if not success:
            raise ServiceError(detail=f"Failed to run task {task_name}", error_code="TASK_EXECUTION_FAILED")
        
        return TaskInfo(**task.to_dict())
    except ServiceError:
        raise
    except Exception as e:
        raise ServiceError(detail=f"Error running task: {str(e)}")


@router.post(
    "/start",
    response_model=SchedulerStatusResponse,
    summary="Start the scheduler",
    description="Starts the scheduler service"
)
async def start_scheduler():
    """
    Start the scheduler service
    
    Returns:
        SchedulerStatusResponse: Updated scheduler status
    """
    try:
        scheduler = SchedulerService()
        
        if not scheduler.running:
            await scheduler.start()
        
        return SchedulerStatusResponse(
            running=scheduler.running,
            tasks_count=len(scheduler.tasks),
            poll_interval=scheduler.poll_interval
        )
    except Exception as e:
        raise ServiceError(detail=f"Error starting scheduler: {str(e)}")


@router.post(
    "/stop",
    response_model=SchedulerStatusResponse,
    summary="Stop the scheduler",
    description="Stops the scheduler service"
)
async def stop_scheduler():
    """
    Stop the scheduler service
    
    Returns:
        SchedulerStatusResponse: Updated scheduler status
    """
    try:
        scheduler = SchedulerService()
        
        if scheduler.running:
            await scheduler.stop()
        
        return SchedulerStatusResponse(
            running=scheduler.running,
            tasks_count=len(scheduler.tasks),
            poll_interval=scheduler.poll_interval
        )
    except Exception as e:
        raise ServiceError(detail=f"Error stopping scheduler: {str(e)}")


@router.patch(
    "/tasks/{task_name}",
    response_model=TaskInfo,
    summary="Update a scheduled task",
    description="Updates a scheduled task's configuration"
)
async def update_task(
    task_name: str,
    update_data: TaskUpdateRequest
):
    """
    Update a scheduled task
    
    Args:
        task_name: Name of the task to update
        update_data: New task configuration
        
    Returns:
        TaskInfo: Updated task information
    """
    try:
        scheduler = SchedulerService()
        task = scheduler.get_task(task_name)
        
        if not task:
            raise ServiceError(detail=f"Task {task_name} not found", error_code="TASK_NOT_FOUND")
        
        # Update task properties
        if update_data.enabled is not None:
            task.enabled = update_data.enabled
        
        if update_data.interval_hours is not None:
            task.interval_hours = update_data.interval_hours
        
        return TaskInfo(**task.to_dict())
    except ServiceError:
        raise
    except Exception as e:
        raise ServiceError(detail=f"Error updating task: {str(e)}")