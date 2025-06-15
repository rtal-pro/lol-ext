from typing import Dict, Optional, Any, List
from pydantic import BaseModel, Field


class SyncRequest(BaseModel):
    """
    Request model for sync operations
    """
    force: bool = Field(False, description="Force sync even if already at latest version")
    background: bool = Field(False, description="Run sync in background")


class SyncResponse(BaseModel):
    """
    Response model for sync operations
    """
    status: str = Field(..., description="Status of the sync operation (success, skipped, started, error)")
    message: str = Field(..., description="Detailed message about the operation")
    entity_type: str = Field(..., description="Type of entity that was synced")
    previous_version: Optional[str] = Field(None, description="Previous version before sync")
    current_version: Optional[str] = Field(None, description="Current version after sync")
    latest_version: Optional[str] = Field(None, description="Latest available version")


class EntityStatus(BaseModel):
    """
    Status of a single entity type
    """
    current_version: Optional[str] = Field(None, description="Current version in database")
    latest_version: str = Field(..., description="Latest available version")
    update_available: bool = Field(..., description="Whether an update is available")


class SyncStatusResponse(BaseModel):
    """
    Response model for sync status
    """
    latest_version: str = Field(..., description="Latest available Data Dragon version")
    status: Dict[str, EntityStatus] = Field(..., description="Status for each entity type")