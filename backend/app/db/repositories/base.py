from typing import TypeVar, Generic, Type, List, Optional, Dict, Any, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete, and_, func
from sqlalchemy.orm import joinedload, selectinload
import logging
from datetime import datetime

from app.db.models import Base

T = TypeVar('T', bound=Base)
logger = logging.getLogger(__name__)

class RepositoryError(Exception):
    """Base exception for repository errors"""
    pass

class EntityNotFoundError(RepositoryError):
    """Raised when an entity is not found"""
    pass

class ValidationError(RepositoryError):
    """Raised when entity validation fails"""
    pass

class TransactionError(RepositoryError):
    """Raised when a transaction operation fails"""
    pass

class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations"""
    
    def __init__(self, session: AsyncSession, model: Type[T]):
        self.session = session
        self.model = model
    
    async def get_by_id(self, entity_id: Any) -> Optional[T]:
        """Get an entity by its ID"""
        result = await self.session.execute(
            select(self.model).where(self.model.id == entity_id)
        )
        return result.scalars().first()
    
    async def get_all(self) -> List[T]:
        """Get all entities"""
        result = await self.session.execute(select(self.model))
        return result.scalars().all()
    
    async def filter_by(self, **kwargs) -> List[T]:
        """Filter entities by attributes"""
        filters = [getattr(self.model, k) == v for k, v in kwargs.items()]
        result = await self.session.execute(
            select(self.model).where(and_(*filters))
        )
        return result.scalars().all()
    
    async def add(self, entity: T) -> T:
        """Add a new entity"""
        self.session.add(entity)
        await self.session.flush()
        return entity
    
    async def add_all(self, entities: List[T]) -> List[T]:
        """Add multiple entities at once"""
        self.session.add_all(entities)
        await self.session.flush()
        return entities
    
    async def update(self, entity: T) -> T:
        """Update an existing entity"""
        self.session.add(entity)
        await self.session.flush()
        return entity
    
    async def delete(self, entity_id: Any) -> bool:
        """Delete an entity by ID"""
        entity = await self.get_by_id(entity_id)
        if not entity:
            return False
        
        await self.session.delete(entity)
        await self.session.flush()
        return True
    
    async def exists(self, entity_id: Any) -> bool:
        """Check if an entity exists"""
        result = await self.session.execute(
            select(self.model).where(self.model.id == entity_id).exists().select()
        )
        return result.scalar()
    
    async def count(self) -> int:
        """Count total entities"""
        result = await self.session.execute(
            select(func.count()).select_from(
                select(self.model.id).distinct().subquery()
            )
        )
        return result.scalar() or 0
    
    @staticmethod
    async def _handle_transaction(func, *args, **kwargs):
        """Execute function within a transaction"""
        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            logger.error(f"Transaction error: {str(e)}")
            raise TransactionError(f"Transaction failed: {str(e)}") from e


class VersionedRepository(BaseRepository[T]):
    """Repository for entities that have version tracking"""
    
    async def get_by_version(self, version: str) -> List[T]:
        """Get all entities for a specific version"""
        result = await self.session.execute(
            select(self.model).where(self.model.version == version)
        )
        return result.scalars().all()
    
    async def get_current_version(self, entity_type: str) -> Optional[str]:
        """Get the current version for a specific entity type"""
        from app.db.models import GameVersion
        
        result = await self.session.execute(
            select(GameVersion.version)
            .where(GameVersion.entity_type == entity_type)
            .where(GameVersion.is_current == True)
        )
        version_row = result.first()
        return version_row[0] if version_row else None
    
    async def set_current_version(self, version: str, entity_type: str) -> None:
        """Set a specific version as current for an entity type"""
        from app.db.models import GameVersion
        
        # First, unset any current versions
        await self.session.execute(
            update(GameVersion)
            .where(GameVersion.entity_type == entity_type)
            .where(GameVersion.is_current == True)
            .values(is_current=False)
        )
        
        # Check if this version exists
        result = await self.session.execute(
            select(GameVersion)
            .where(GameVersion.entity_type == entity_type)
            .where(GameVersion.version == version)
        )
        version_row = result.first()
        
        if version_row:
            # Update existing version to current
            await self.session.execute(
                update(GameVersion)
                .where(GameVersion.id == version_row[0].id)
                .values(is_current=True)
            )
        else:
            # Create new version entry
            game_version = GameVersion(
                version=version,
                entity_type=entity_type,
                is_current=True,
                release_date=datetime.now().isoformat()
            )
            self.session.add(game_version)
            await self.session.flush()


class RelationshipRepository(VersionedRepository[T]):
    """Repository for entities with complex relationships"""
    
    async def get_with_relationships(self, entity_id: Any, relationships: List[str]) -> Optional[T]:
        """Get an entity with its relationships loaded"""
        query = select(self.model).where(self.model.id == entity_id)
        
        for relationship in relationships:
            query = query.options(selectinload(getattr(self.model, relationship)))
        
        result = await self.session.execute(query)
        return result.scalars().first()
    
    async def bulk_upsert(self, entities: List[Dict[str, Any]]) -> List[T]:
        """Insert or update multiple entities at once"""
        results = []
        
        for entity_data in entities:
            entity_id = entity_data.get('id')
            existing = await self.get_by_id(entity_id) if entity_id else None
            
            if existing:
                # Update existing entity
                for key, value in entity_data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                self.session.add(existing)
                results.append(existing)
            else:
                # Create new entity
                new_entity = self.model(**entity_data)
                self.session.add(new_entity)
                results.append(new_entity)
        
        await self.session.flush()
        return results