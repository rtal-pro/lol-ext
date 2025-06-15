from typing import Type, TypeVar, Callable, Dict, Any
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.models import Base
from app.db.repositories.base import BaseRepository
from app.db.repositories.champion_repository import ChampionRepository
from app.db.repositories.item_repository import ItemRepository
from app.db.repositories.rune_repository import RuneRepository

# Type variable for repository types
RepoType = TypeVar('RepoType', bound=BaseRepository)


def get_repository(repo_class: Type[RepoType]) -> Callable[[AsyncSession], RepoType]:
    """
    Factory function to create repository dependency
    
    Args:
        repo_class: Repository class to instantiate
        
    Returns:
        Callable: Dependency function that returns repository instance
    """
    def _get_repo(db: AsyncSession = Depends(get_db)) -> RepoType:
        return repo_class(db)
    
    return _get_repo


# Repository dependencies
get_champion_repository = get_repository(ChampionRepository)
get_item_repository = get_repository(ItemRepository)
get_rune_repository = get_repository(RuneRepository)