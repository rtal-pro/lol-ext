from typing import List, Optional
import logging
from fastapi import APIRouter, Depends, Query, Path, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.db.session import get_db
from app.db.repositories.champion_repository import ChampionRepository
from app.api.api_v1.schemas.champions import (
    ChampionSummary, 
    ChampionDetail,
    ChampionListResponse,
    ImageData
)
from app.api.api_v1.schemas.base import PaginationParams
from app.core.exceptions import NotFoundError, DatabaseError
from app.core.config import settings
from app.db.models import Champion, Tag

logger = logging.getLogger(__name__)

router = APIRouter(tags=["champions"])


@router.get(
    "",
    response_model=List[ChampionSummary],
    summary="Get all champions",
    description="Returns a list of all champions with basic information"
)
async def get_champions(
    name: Optional[str] = Query(None, description="Filter by champion name"),
    tag: Optional[str] = Query(None, description="Filter by champion tag"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a list of all champions with optional filtering.
    
    Args:
        name: Filter champions by name (case-insensitive, partial match)
        tag: Filter champions by tag (e.g., "Fighter", "Mage")
        db: Database session
        
    Returns:
        List[ChampionSummary]: List of all champions
    """
    try:
        # Build query with filters
        query = select(Champion)
        if name:
            query = query.where(Champion.name.ilike(f"%{name}%"))
        
        # Add tag filtering if specified
        if tag:
            query = query.join(Champion.tags).where(Tag.name == tag)
            
        # Execute query to get all champions (no pagination)
        result = await db.execute(query)
        champions = result.scalars().all()
        
        # Fetch tags for all champions in a single query to avoid N+1 problem
        champion_ids = [champion.id for champion in champions]
        if champion_ids:
            # Build a query to get all tags for all champions at once
            tags_query = select(Champion.id, Tag.name).join(Champion.tags).where(Champion.id.in_(champion_ids))
            tags_result = await db.execute(tags_query)
            
            # Group tags by champion_id
            champion_tags = {}
            for champion_id, tag_name in tags_result:
                if champion_id not in champion_tags:
                    champion_tags[champion_id] = []
                champion_tags[champion_id].append(tag_name)
        else:
            champion_tags = {}
        
        # Create response items with tags
        items = []
        for champion in champions:
            try:
                # Handle potential null/None values gracefully
                title = champion.title if champion.title else None
                items.append(ChampionSummary(
                    id=champion.id,
                    key=champion.key,
                    name=champion.name,
                    title=title,
                    image=ImageData(
                        full=champion.image_full or "",
                        sprite=champion.image_sprite or "",
                        group=champion.image_group or "",
                        x=None,
                        y=None,
                        w=None,
                        h=None
                    ),
                    tags=champion_tags.get(champion.id, [])
                ))
            except Exception as inner_e:
                # Log detailed error but continue processing other champions
                logger.error(f"Error processing champion {champion.id}: {str(inner_e)}")
                logger.debug(f"Champion data causing error: id={champion.id}, name={champion.name}, title={champion.title}")
                continue
        
        return items
    except Exception as e:
        raise DatabaseError(detail=f"Error fetching champions: {str(e)}")


@router.get(
    "/{champion_id}",
    response_model=ChampionDetail,
    summary="Get champion details",
    description="Returns detailed information about a specific champion including abilities, stats, and skins"
)
async def get_champion_detail(
    champion_id: str = Path(..., description="Champion ID (e.g., 'Aatrox')"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information about a specific champion.
    
    Args:
        champion_id: Champion ID (e.g., 'Aatrox')
        db: Database session
        
    Returns:
        ChampionDetail: Detailed champion information
        
    Raises:
        NotFoundError: If champion is not found
    """
    try:
        repo = ChampionRepository(db)
        champion = await repo.get_with_details(champion_id)
        
        if not champion:
            raise NotFoundError(
                detail=f"Champion '{champion_id}' not found",
                error_code="CHAMPION_NOT_FOUND"
            )
        
        # Get base URL for asset links
        base_url = settings.DATA_DRAGON_CDN
        
        try:
            return ChampionDetail.from_orm(champion, base_url)
        except Exception as e:
            logger.error(f"Error creating ChampionDetail for {champion_id}: {str(e)}")
            # Try to create a minimal valid response
            logger.info(f"Attempting to create minimal valid response for {champion_id}")
            return ChampionDetail.from_orm(champion, base_url)
    except NotFoundError:
        raise
    except Exception as e:
        raise DatabaseError(detail=f"Error fetching champion: {str(e)}")