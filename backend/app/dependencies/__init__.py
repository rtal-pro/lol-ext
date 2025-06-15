from app.dependencies.database import get_object_by_id
from app.dependencies.repositories import (
    get_repository,
    get_champion_repository,
    get_item_repository,
    get_rune_repository
)

__all__ = [
    'get_object_by_id',
    'get_repository',
    'get_champion_repository',
    'get_item_repository',
    'get_rune_repository'
]