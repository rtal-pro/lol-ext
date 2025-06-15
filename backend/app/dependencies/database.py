from typing import AsyncGenerator, Callable, Type

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import declarative_base, sessionmaker

from app.db.models import Base
from app.db.session import get_db


# Function to create a dependency that gets a specific model by ID
def get_object_by_id(model: Type[Base]):
    """
    Creates a dependency that fetches a database object by ID
    
    Args:
        model: SQLAlchemy model class
        
    Returns:
        Callable: Dependency function that fetches the object
    """
    
    async def _get_object(
        id: str, 
        db: AsyncSession = Depends(get_db)
    ) -> Base:
        """
        Get object by ID from database
        
        Args:
            id: Object ID
            db: Database session
            
        Returns:
            Base: Database object
            
        Raises:
            HTTPException: If object not found
        """
        from app.core.exceptions import NotFoundError
        
        result = await db.execute(select(model).where(model.id == id))
        obj = result.scalars().first()
        
        if not obj:
            raise NotFoundError(
                detail=f"{model.__name__} with ID {id} not found",
                error_code=f"{model.__name__.upper()}_NOT_FOUND"
            )
        
        return obj
    
    return _get_object