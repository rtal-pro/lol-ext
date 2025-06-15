from typing import Any, Dict, Optional

from fastapi import HTTPException, status


class APIError(HTTPException):
    """Base API error class with consistent error response structure"""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code or str(status_code)


class NotFoundError(APIError):
    """Resource not found error"""
    
    def __init__(
        self, 
        detail: str = "Resource not found", 
        error_code: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            error_code=error_code or "NOT_FOUND",
            headers=headers,
        )


class BadRequestError(APIError):
    """Bad request error"""
    
    def __init__(
        self, 
        detail: str = "Bad request", 
        error_code: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code=error_code or "BAD_REQUEST",
            headers=headers,
        )


class UnauthorizedError(APIError):
    """Unauthorized error"""
    
    def __init__(
        self, 
        detail: str = "Not authenticated", 
        error_code: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code=error_code or "UNAUTHORIZED",
            headers=headers,
        )


class ForbiddenError(APIError):
    """Forbidden error"""
    
    def __init__(
        self, 
        detail: str = "Not enough permissions", 
        error_code: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code=error_code or "FORBIDDEN",
            headers=headers,
        )


class InternalServerError(APIError):
    """Internal server error"""
    
    def __init__(
        self, 
        detail: str = "Internal server error", 
        error_code: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code=error_code or "INTERNAL_SERVER_ERROR",
            headers=headers,
        )


class DatabaseError(APIError):
    """Database error"""
    
    def __init__(
        self, 
        detail: str = "Database error", 
        error_code: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code=error_code or "DATABASE_ERROR",
            headers=headers,
        )


class ServiceUnavailableError(APIError):
    """Service unavailable error"""
    
    def __init__(
        self, 
        detail: str = "Service unavailable", 
        error_code: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
            error_code=error_code or "SERVICE_UNAVAILABLE",
            headers=headers,
        )


class RiotAPIError(APIError):
    """Riot API error"""
    
    def __init__(
        self, 
        detail: str = "Riot API error", 
        error_code: Optional[str] = None,
        status_code: int = status.HTTP_503_SERVICE_UNAVAILABLE,
        headers: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            status_code=status_code,
            detail=detail,
            error_code=error_code or "RIOT_API_ERROR",
            headers=headers,
        )


class ServiceError(APIError):
    """Service layer error"""
    
    def __init__(
        self, 
        detail: str = "Service error", 
        error_code: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code=error_code or "SERVICE_ERROR",
            headers=headers,
        )