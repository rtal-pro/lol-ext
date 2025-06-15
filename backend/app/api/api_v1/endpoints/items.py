from typing import List, Optional, Dict
import logging
from fastapi import APIRouter, Depends, Query, Path, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_
from itertools import groupby

from app.db.session import get_db
from app.db.repositories.item_repository import ItemRepository
from app.api.api_v1.schemas.items import (
    ItemSummary,
    ItemDetail,
    ItemListResponse,
    ItemListByTier,
    ItemGold,
    ImageData
)
from app.api.api_v1.schemas.base import PaginationParams
from app.core.exceptions import NotFoundError, DatabaseError
from app.db.models import Item, Tag

logger = logging.getLogger(__name__)

router = APIRouter(tags=["items"])


@router.get(
    "",
    response_model=ItemListResponse,
    summary="Get all items",
    description="Returns all items grouped by tier"
)
async def get_items(
    tag: Optional[str] = Query(None, description="Filter by item tag"),
    purchasable_only: bool = Query(False, description="Only include purchasable items"),
    limit: int = Query(20, description="Number of items per page", ge=1, le=100),
    page: int = Query(1, description="Page number", ge=1),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all items grouped by tier with pagination.
    
    Args:
        tag: Filter items by tag (e.g., "Armor", "SpellDamage")
        purchasable_only: Only include purchasable items
        limit: Maximum number of items to return
        page: Page number for pagination
        db: Database session
        
    Returns:
        ItemListResponse: Items grouped by tier
    """
    try:
        # We'll use a safer, two-step approach to avoid JSON comparison issues
        # First, get filtered item IDs
        id_query = select(Item.id).distinct()
        
        # Apply tag filter if specified
        if tag:
            id_query = id_query.join(Item.tags).where(Tag.name == tag)
            
        # Apply purchasable filter if specified
        if purchasable_only:
            id_query = id_query.where(Item.purchasable == True)
        
        # Apply pagination and ordering on the ID query
        offset = (page - 1) * limit
        id_query = id_query.order_by(Item.id).limit(limit).offset(offset)
        
        # Count total items
        count_query = select(func.count(Item.id.distinct()))
        if tag:
            count_query = count_query.join(Item.tags).where(Tag.name == tag)
        if purchasable_only:
            count_query = count_query.where(Item.purchasable == True)
        
        # Execute count query
        count_result = await db.execute(count_query)
        total = count_result.scalar() or 0
        
        # Execute the ID query
        id_result = await db.execute(id_query)
        filtered_ids = [row[0] for row in id_result]
        
        # No items found
        if not filtered_ids:
            return ItemListResponse(tiers=[], total=0)
            
        # Now fetch the complete items by ID
        # This avoids the JSON comparison issue because we're just using the item IDs
        items_query = select(Item).where(Item.id.in_(filtered_ids)).order_by(Item.id)
        items_result = await db.execute(items_query)
        items = items_result.scalars().all()
        
        # Fetch tags for all items in a single query to avoid N+1 problem
        item_ids = [item.id for item in items]
        
        # Build a query to get all tags for all items at once
        tags_query = select(Item.id, Tag.name).join(Item.tags).where(Item.id.in_(item_ids))
        tags_result = await db.execute(tags_query)
        
        # Group tags by item_id
        item_tags = {}
        for item_id, tag_name in tags_result:
            if item_id not in item_tags:
                item_tags[item_id] = []
            item_tags[item_id].append(tag_name)
        
        # Create response items with tags
        item_summaries = []
        for item in items:
            try:
                # Create a summary with proper error handling for null values
                item_summaries.append(ItemSummary(
                    id=item.id,
                    name=item.name,
                    description=item.description,
                    plaintext=item.plain_text,
                    tier=item.tier,
                    image=ImageData(
                        full=item.image_full or "",
                        sprite=item.image_sprite or "",
                        group=item.image_group or "",
                        x=None,
                        y=None,
                        w=None,
                        h=None
                    ),
                    gold=ItemGold(
                        base=item.base_gold or 0,
                        total=item.total_gold or 0,
                        sell=item.sell_gold or 0,
                        purchasable=item.purchasable
                    ),
                    tags=item_tags.get(item.id, [])
                ))
            except Exception as inner_e:
                # Skip items with errors
                logger.error(f"Error processing item {item.id}: {str(inner_e)}")
                continue
        
        # Group by tier
        # Sort by tier first, then group
        item_summaries.sort(key=lambda x: x.tier or 0)
        grouped_items: Dict[int, List[ItemSummary]] = {}
        
        for tier, tier_items in groupby(item_summaries, key=lambda x: x.tier or 0):
            grouped_items[tier] = list(tier_items)
        
        # Convert to list of ItemListByTier
        tiers = [
            ItemListByTier(tier=tier, items=items)
            for tier, items in grouped_items.items()
        ]
        
        # Sort tiers
        tiers.sort(key=lambda x: x.tier)
        
        return ItemListResponse(
            tiers=tiers,
            total=total
        )
    except Exception as e:
        logger.error(f"Error in get_items: {str(e)}")
        # Make sure to rollback the transaction on error
        await db.rollback()
        raise DatabaseError(detail=f"Error fetching items: {str(e)}")


@router.get(
    "/{item_id}",
    response_model=ItemDetail,
    summary="Get item details",
    description="Returns detailed information about a specific item including its recipe"
)
async def get_item_detail(
    item_id: str = Path(..., description="Item ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information about a specific item.
    
    Args:
        item_id: Item ID
        db: Database session
        
    Returns:
        ItemDetail: Detailed item information
        
    Raises:
        NotFoundError: If item is not found
    """
    try:
        repo = ItemRepository(db)
        item = await repo.get_with_relationships(item_id)
        
        if not item:
            raise NotFoundError(
                detail=f"Item '{item_id}' not found",
                error_code="ITEM_NOT_FOUND"
            )
        
        try:
            # Convert to schema with proper error handling
            item_detail = ItemDetail.from_orm(item)
            return item_detail
        except Exception as validation_error:
            # Log validation error and provide better error message
            logger.error(f"Error creating ItemDetail from item {item_id}: {str(validation_error)}")
            # Try to find the exact validation error
            error_detail = f"Validation error for item {item_id}: {str(validation_error)}"
            raise DatabaseError(detail=error_detail)
            
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error in get_item_detail: {str(e)}")
        raise DatabaseError(detail=f"Error fetching item: {str(e)}")


@router.get(
    "/{item_id}/recipe",
    response_model=ItemDetail,
    summary="Get item recipe",
    description="Returns an item with its complete recipe tree"
)
async def get_item_recipe(
    item_id: str = Path(..., description="Item ID"),
    depth: int = Query(2, description="Recipe depth to follow", ge=1, le=5),
    db: AsyncSession = Depends(get_db)
):
    """
    Get an item with its complete recipe tree.
    
    Args:
        item_id: Item ID
        depth: How deep to follow the recipe tree (1-5)
        db: Database session
        
    Returns:
        ItemDetail: Item with recipe information
        
    Raises:
        NotFoundError: If item is not found
    """
    try:
        repo = ItemRepository(db)
        
        # Limit depth to prevent excessive recursive queries
        capped_depth = min(depth, 5)
        
        item_tree = await repo.get_item_tree(item_id, capped_depth)
        
        # If the item doesn't exist at all, return a not found error
        if not item_tree:
            raise NotFoundError(
                detail=f"Item '{item_id}' not found",
                error_code="ITEM_NOT_FOUND"
            )
        
        # Check if this is a mythic/legendary item with missing build path
        item = item_tree["item"]
        is_mythic = any(tag.name.lower() in ["mythic", "legendary"] for tag in item.tags)
        missing_components = is_mythic and not item.built_from
        
        # Log warning for mythic items with missing build paths
        if missing_components:
            logger.warning(
                f"Mythic item {item_id} ({item.name}) has no build path components. "
                f"Consider running the validation script to fix missing build paths."
            )
        
        try:
            # Convert the main item to a response model with error handling
            item_detail = ItemDetail.from_orm(item)
            return item_detail
        except Exception as validation_error:
            # Log validation error and provide better error message
            logger.error(f"Error creating ItemDetail from recipe tree for item {item_id}: {str(validation_error)}")
            error_detail = f"Validation error for item recipe {item_id}: {str(validation_error)}"
            raise DatabaseError(detail=error_detail)
            
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Error in get_item_recipe: {str(e)}")
        raise DatabaseError(detail=f"Error fetching item recipe: {str(e)}")