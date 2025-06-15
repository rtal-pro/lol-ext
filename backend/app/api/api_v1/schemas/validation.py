from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ValidationError(BaseModel):
    """
    Validation error or warning
    """
    message: str = Field(..., description="Error message")
    entity_id: Optional[str] = Field(None, description="ID of the entity with the error")


class ValidationResponse(BaseModel):
    """
    Response model for validation operations
    """
    entity_type: str = Field(..., description="Type of entity that was validated")
    status: str = Field(..., description="Status of the validation (started, completed, failed)")
    message: Optional[str] = Field(None, description="Additional message about validation")
    is_valid: Optional[bool] = Field(None, description="Whether validation passed")
    total_count: Optional[int] = Field(None, description="Total entities checked")
    valid_count: Optional[int] = Field(None, description="Count of valid entities")
    errors_count: Optional[int] = Field(None, description="Count of errors found")
    warnings_count: Optional[int] = Field(None, description="Count of warnings found")
    duration_ms: Optional[float] = Field(None, description="Duration of validation in milliseconds")
    errors: Optional[List[ValidationError]] = Field(None, description="List of validation errors")
    warnings: Optional[List[ValidationError]] = Field(None, description="List of validation warnings")


class EntityValidationSummary(BaseModel):
    """
    Summary of entity validation
    """
    is_valid: bool = Field(..., description="Whether validation passed")
    total_count: int = Field(..., description="Total entities checked")
    valid_count: int = Field(..., description="Count of valid entities")
    errors_count: int = Field(..., description="Count of errors found")
    warnings_count: int = Field(..., description="Count of warnings found")


class ValidationSummaryResponse(BaseModel):
    """
    Response model for validating all data
    """
    status: str = Field(..., description="Status of the validation (started, completed, failed)")
    message: str = Field(..., description="Message about validation")
    is_valid: Optional[bool] = Field(None, description="Whether all validations passed")
    results: Dict[str, EntityValidationSummary] = Field(..., description="Validation results by entity type")