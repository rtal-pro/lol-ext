from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime


class TaskInfo(BaseModel):
    """
    Information about a scheduled task
    """
    name: str = Field(..., description="Task name")
    interval_hours: int = Field(..., description="Interval in hours between runs")
    last_run: Optional[str] = Field(None, description="ISO-formatted timestamp of last run")
    next_run: Optional[str] = Field(None, description="ISO-formatted timestamp of next scheduled run")
    enabled: bool = Field(..., description="Whether the task is enabled")
    running: bool = Field(..., description="Whether the task is currently running")
    error: Optional[str] = Field(None, description="Last error message, if any")


class TaskCreateRequest(BaseModel):
    """
    Request model for creating a new scheduled task
    """
    name: str = Field(..., description="Task name")
    interval_hours: int = Field(..., description="Interval in hours between runs")
    enabled: bool = Field(True, description="Whether the task is enabled")


class TaskUpdateRequest(BaseModel):
    """
    Request model for updating a scheduled task
    """
    interval_hours: Optional[int] = Field(None, description="Interval in hours between runs")
    enabled: Optional[bool] = Field(None, description="Whether the task is enabled")


class TaskListResponse(BaseModel):
    """
    Response model for listing scheduled tasks
    """
    tasks: List[TaskInfo] = Field(..., description="List of scheduled tasks")


class SchedulerStatusResponse(BaseModel):
    """
    Response model for scheduler status
    """
    running: bool = Field(..., description="Whether the scheduler is running")
    tasks_count: int = Field(..., description="Number of registered tasks")
    poll_interval: int = Field(..., description="Scheduler poll interval in seconds")