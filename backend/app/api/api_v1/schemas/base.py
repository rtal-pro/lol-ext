from typing import Generic, TypeVar, List, Optional, Dict, Any
from pydantic import BaseModel, Field
import math

T = TypeVar('T')

class ErrorResponse(BaseModel):
    """Standard error response model"""
    error_code: str = Field(..., description="Error code for programmatic handling")
    detail: str = Field(..., description="Human-readable error message")


class PaginationParams(BaseModel):
    """Common pagination parameters"""
    page: int = Field(1, description="Page number (1-indexed)", ge=1)
    limit: int = Field(20, description="Number of items per page", ge=1, le=100)
    
    def get_skip(self) -> int:
        """Calculate items to skip for pagination"""
        return (self.page - 1) * self.limit


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response with metadata"""
    items: List[T] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")
    pages: int = Field(..., description="Total number of pages")
    
    @classmethod
    def create(cls, items: List[T], total: int, params: PaginationParams) -> 'PaginatedResponse[T]':
        """Create a paginated response from items and pagination parameters"""
        return cls(
            items=items,
            total=total,
            page=params.page,
            limit=params.limit,
            pages=math.ceil(total / params.limit) if total > 0 else 0
        )


class SuccessResponse(BaseModel):
    """Standard success response"""
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Optional response data")