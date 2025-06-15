from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Path, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.repositories.rune_repository import RuneRepository
from app.api.api_v1.schemas.runes import (
    RuneDetail,
    RunePath,
    RuneTreeResponse
)
from app.core.exceptions import NotFoundError, DatabaseError

router = APIRouter(tags=["runes"])


@router.get(
    "",
    response_model=RuneTreeResponse,
    summary="Get all runes",
    description="Returns the complete rune tree structure with all paths and runes"
)
async def get_runes(
    db: AsyncSession = Depends(get_db)
):
    """
    Get the complete rune tree structure.
    
    Args:
        db: Database session
        
    Returns:
        RuneTreeResponse: Complete rune tree
    """
    from sqlalchemy import select, text
    from app.db.models import RunePath, RuneSlot, Rune, GameVersion
    
    try:
        # Get current version first - using raw SQL to avoid any nested await issues
        version_result = await db.execute(
            text("SELECT version FROM game_versions WHERE entity_type = 'runes' AND is_current = true LIMIT 1")
        )
        version_row = version_result.first()
        version = version_row[0] if version_row else "latest"
        
        # Fetch all the data at once with a single SQL query to avoid nested awaits
        result = await db.execute(
            text("""
            WITH paths AS (
                SELECT id, key, name, icon, version 
                FROM rune_paths
                ORDER BY id
            ),
            slots AS (
                SELECT id, path_id, slot_number
                FROM rune_slots
                WHERE path_id IN (SELECT id FROM paths)
                ORDER BY path_id, slot_number
            ),
            runes AS (
                SELECT id, slot_id, key, name, short_desc, long_desc, icon, version
                FROM runes
                WHERE slot_id IN (SELECT id FROM slots)
                ORDER BY slot_id, id
            )
            SELECT 
                p.id as path_id, p.key as path_key, p.name as path_name, p.icon as path_icon, p.version as path_version,
                s.id as slot_id, s.path_id, s.slot_number,
                r.id as rune_id, r.slot_id as rune_slot_id, r.key as rune_key, r.name as rune_name, 
                r.short_desc, r.long_desc, r.icon as rune_icon, r.version as rune_version
            FROM paths p
            LEFT JOIN slots s ON p.id = s.path_id
            LEFT JOIN runes r ON s.id = r.slot_id
            ORDER BY p.id, s.slot_number, r.id
            """)
        )
        
        rows = result.all()
        
        # Process the results into the needed structure
        path_map = {}
        slot_map = {}
        
        for row in rows:
            path_id = row.path_id
            slot_id = row.slot_id
            
            # Process path
            if path_id not in path_map:
                path_map[path_id] = {
                    "id": path_id,
                    "key": row.path_key,
                    "name": row.path_name,
                    "icon": row.path_icon,
                    "slots": []
                }
            
            # Skip if no slot (shouldn't happen with proper data)
            if not slot_id:
                continue
                
            # Process slot
            slot_key = f"{path_id}_{slot_id}"
            if slot_key not in slot_map:
                slot = {
                    "id": slot_id,
                    "slotNumber": row.slot_number,
                    "runes": []
                }
                slot_map[slot_key] = slot
                path_map[path_id]["slots"].append(slot)
            
            # Process rune
            if row.rune_id:
                rune = {
                    "id": row.rune_id,
                    "key": row.rune_key,
                    "name": row.rune_name,
                    "shortDesc": row.short_desc,
                    "longDesc": row.long_desc,
                    "icon": row.rune_icon
                }
                slot_map[slot_key]["runes"].append(rune)
        
        # Build the response
        paths = [path for _, path in path_map.items()]
        paths.sort(key=lambda p: p["id"])
        
        return RuneTreeResponse(
            paths=paths,
            version=version
        )
    except Exception as e:
        raise DatabaseError(detail=f"Error fetching runes: {str(e)}")


@router.get(
    "/paths/{path_id}",
    response_model=RunePath,
    summary="Get rune path",
    description="Returns a specific rune path with all its slots and runes"
)
async def get_rune_path(
    path_id: int = Path(..., description="Rune path ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific rune path with all its slots and runes.
    
    Args:
        path_id: Rune path ID
        db: Database session
        
    Returns:
        RunePath: Rune path with all slots and runes
        
    Raises:
        NotFoundError: If rune path is not found
    """
    from sqlalchemy import text
    
    try:
        # Use a single SQL query to get everything at once
        result = await db.execute(
            text("""
            WITH path AS (
                SELECT id, key, name, icon, version 
                FROM rune_paths
                WHERE id = :path_id
            ),
            slots AS (
                SELECT id, path_id, slot_number
                FROM rune_slots
                WHERE path_id = :path_id
                ORDER BY slot_number
            ),
            runes AS (
                SELECT id, slot_id, key, name, short_desc, long_desc, icon, version
                FROM runes
                WHERE slot_id IN (SELECT id FROM slots)
                ORDER BY slot_id, id
            )
            SELECT 
                p.id as path_id, p.key as path_key, p.name as path_name, p.icon as path_icon, p.version as path_version,
                s.id as slot_id, s.path_id, s.slot_number,
                r.id as rune_id, r.slot_id as rune_slot_id, r.key as rune_key, r.name as rune_name, 
                r.short_desc, r.long_desc, r.icon as rune_icon, r.version as rune_version
            FROM path p
            LEFT JOIN slots s ON p.id = s.path_id
            LEFT JOIN runes r ON s.id = r.slot_id
            ORDER BY s.slot_number, r.id
            """),
            {"path_id": path_id}
        )
        
        rows = result.all()
        
        # Check if path exists
        if not rows:
            raise NotFoundError(
                detail=f"Rune path '{path_id}' not found",
                error_code="RUNE_PATH_NOT_FOUND"
            )
        
        # Process the results into the needed structure
        first_row = rows[0]
        path = {
            "id": first_row.path_id,
            "key": first_row.path_key,
            "name": first_row.path_name,
            "icon": first_row.path_icon,
            "slots": []
        }
        
        # Process slots and runes
        slot_map = {}
        
        for row in rows:
            slot_id = row.slot_id
            
            # Skip if no slot
            if not slot_id:
                continue
                
            # Process slot
            if slot_id not in slot_map:
                slot = {
                    "slotNumber": row.slot_number,
                    "runes": []
                }
                slot_map[slot_id] = slot
                path["slots"].append(slot)
            
            # Process rune
            if row.rune_id:
                rune = {
                    "id": row.rune_id,
                    "key": row.rune_key,
                    "name": row.rune_name,
                    "shortDesc": row.short_desc,
                    "longDesc": row.long_desc,
                    "icon": row.rune_icon
                }
                slot_map[slot_id]["runes"].append(rune)
        
        return path
    except NotFoundError:
        raise
    except Exception as e:
        raise DatabaseError(detail=f"Error fetching rune path: {str(e)}")


@router.get(
    "/search",
    response_model=List[RuneDetail],
    summary="Search runes",
    description="Search for runes by name or description"
)
async def search_runes(
    query: str = Query(..., min_length=2, description="Search query"),
    path_key: Optional[str] = Query(None, description="Filter by path key (e.g., 'Domination')"),
    db: AsyncSession = Depends(get_db)
):
    """
    Search for runes by name or description.
    
    Args:
        query: Search query
        path_key: Filter by path key
        db: Database session
        
    Returns:
        List[RuneDetail]: Matching runes
    """
    try:
        repo = RuneRepository(db)
        
        # Search runes
        runes, _ = await repo.search_runes(
            name=query,
            path_key=path_key,
            limit=50
        )
        
        # Convert to response models
        return [RuneDetail.from_orm(rune) for rune in runes]
    except Exception as e:
        raise DatabaseError(detail=f"Error searching runes: {str(e)}")