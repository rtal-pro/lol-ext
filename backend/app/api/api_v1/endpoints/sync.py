from typing import Dict, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.db.session import get_db
from app.db.data_manager import DataDragonManager
from app.services.data_dragon_service import DataDragonService
from app.db.repositories.champion_repository import ChampionRepository
from app.db.repositories.item_repository import ItemRepository
from app.db.repositories.rune_repository import RuneRepository
from app.api.api_v1.schemas.sync import (
    SyncResponse,
    SyncRequest,
    SyncStatusResponse
)
from app.core.exceptions import DatabaseError, ServiceError

# Set up logging
logger = logging.getLogger(__name__)

# Router
router = APIRouter(tags=["sync"])


@router.post(
    "/champions",
    response_model=SyncResponse,
    summary="Sync champion data",
    description="Fetches and updates champion data from the Data Dragon API"
)
async def sync_champions(
    request: SyncRequest = SyncRequest(),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Synchronize champion data with the latest version from Data Dragon API.
    
    Args:
        request: Sync request parameters
        background_tasks: FastAPI background tasks
        db: Database session
        
    Returns:
        SyncResponse: Status of the sync operation
    """
    try:
        force = request.force
        run_in_background = request.background and background_tasks is not None
        
        if run_in_background:
            # Only pass the force parameter, not the db session
            background_tasks.add_task(_sync_champions_task, force)
            return SyncResponse(
                status="started",
                message="Champion sync started in background",
                entity_type="champions"
            )
        else:
            # Run synchronously
            data_manager = DataDragonManager(db)
            
            try:
                latest_version = await data_manager.get_latest_version()
                current_version = await data_manager.get_current_db_version("champions")
                
                if current_version == latest_version and not force:
                    return SyncResponse(
                        status="skipped",
                        message=f"Champions already at latest version {latest_version}",
                        entity_type="champions",
                        current_version=current_version,
                        latest_version=latest_version
                    )
                
                logger.info(f"Syncing champions from version {current_version} to {latest_version}")
                await data_manager.update_champions(latest_version)
                await db.commit()
                
                return SyncResponse(
                    status="success",
                    message=f"Champions updated to version {latest_version}",
                    entity_type="champions",
                    previous_version=current_version,
                    current_version=latest_version
                )
            finally:
                await data_manager.close()
    except Exception as e:
        logger.error(f"Error syncing champions: {str(e)}", exc_info=True)
        raise ServiceError(detail=f"Error syncing champions: {str(e)}")


@router.post(
    "/items",
    response_model=SyncResponse,
    summary="Sync item data",
    description="Fetches and updates item data from the Data Dragon API"
)
async def sync_items(
    request: SyncRequest = SyncRequest(),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Synchronize item data with the latest version from Data Dragon API.
    
    Args:
        request: Sync request parameters
        background_tasks: FastAPI background tasks
        db: Database session
        
    Returns:
        SyncResponse: Status of the sync operation
    """
    try:
        force = request.force
        run_in_background = request.background and background_tasks is not None
        
        if run_in_background:
            # Only pass the force parameter, not the db session
            background_tasks.add_task(_sync_items_task, force)
            return SyncResponse(
                status="started",
                message="Item sync started in background",
                entity_type="items"
            )
        else:
            # Run synchronously
            data_manager = DataDragonManager(db)
            
            try:
                latest_version = await data_manager.get_latest_version()
                current_version = await data_manager.get_current_db_version("items")
                
                if current_version == latest_version and not force:
                    return SyncResponse(
                        status="skipped",
                        message=f"Items already at latest version {latest_version}",
                        entity_type="items",
                        current_version=current_version,
                        latest_version=latest_version
                    )
                
                logger.info(f"Syncing items from version {current_version} to {latest_version}")
                await data_manager.update_items(latest_version)
                await db.commit()
                
                return SyncResponse(
                    status="success",
                    message=f"Items updated to version {latest_version}",
                    entity_type="items",
                    previous_version=current_version,
                    current_version=latest_version
                )
            finally:
                await data_manager.close()
    except Exception as e:
        logger.error(f"Error syncing items: {str(e)}", exc_info=True)
        raise ServiceError(detail=f"Error syncing items: {str(e)}")


@router.post(
    "/runes",
    response_model=SyncResponse,
    summary="Sync rune data",
    description="Fetches and updates rune data from the Data Dragon API"
)
async def sync_runes(
    request: SyncRequest = SyncRequest(),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Synchronize rune data with the latest version from Data Dragon API.
    
    Args:
        request: Sync request parameters
        background_tasks: FastAPI background tasks
        db: Database session
        
    Returns:
        SyncResponse: Status of the sync operation
    """
    try:
        force = request.force
        run_in_background = request.background and background_tasks is not None
        
        if run_in_background:
            # Only pass the force parameter, not the db session
            background_tasks.add_task(_sync_runes_task, force)
            return SyncResponse(
                status="started",
                message="Rune sync started in background",
                entity_type="runes"
            )
        else:
            # Run synchronously
            data_manager = DataDragonManager(db)
            
            try:
                latest_version = await data_manager.get_latest_version()
                current_version = await data_manager.get_current_db_version("runes")
                
                if current_version == latest_version and not force:
                    return SyncResponse(
                        status="skipped",
                        message=f"Runes already at latest version {latest_version}",
                        entity_type="runes",
                        current_version=current_version,
                        latest_version=latest_version
                    )
                
                logger.info(f"Syncing runes from version {current_version} to {latest_version}")
                await data_manager.update_runes(latest_version)
                await db.commit()
                
                return SyncResponse(
                    status="success",
                    message=f"Runes updated to version {latest_version}",
                    entity_type="runes",
                    previous_version=current_version,
                    current_version=latest_version
                )
            finally:
                await data_manager.close()
    except Exception as e:
        logger.error(f"Error syncing runes: {str(e)}", exc_info=True)
        raise ServiceError(detail=f"Error syncing runes: {str(e)}")


@router.post(
    "/all",
    response_model=SyncResponse,
    summary="Sync all game data",
    description="Fetches and updates all game data from the Data Dragon API"
)
async def sync_all(
    request: SyncRequest = SyncRequest(),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Synchronize all game data with the latest version from Data Dragon API.
    
    Args:
        request: Sync request parameters
        background_tasks: FastAPI background tasks
        db: Database session
        
    Returns:
        SyncResponse: Status of the sync operation
    """
    try:
        force = request.force
        run_in_background = request.background and background_tasks is not None
        
        if run_in_background:
            # Only pass the force parameter, not the db session
            background_tasks.add_task(_sync_all_task, force)
            return SyncResponse(
                status="started",
                message="Full data sync started in background",
                entity_type="all"
            )
        else:
            # Run synchronously
            data_manager = DataDragonManager(db)
            
            try:
                latest_version = await data_manager.get_latest_version()
                updates_needed = await data_manager.check_for_updates()
                
                if not any(updates_needed.values()) and not force:
                    return SyncResponse(
                        status="skipped",
                        message=f"All data already at latest version {latest_version}",
                        entity_type="all",
                        current_version=latest_version,
                        latest_version=latest_version
                    )
                
                logger.info(f"Syncing all data to version {latest_version}")
                await data_manager.update_all(force=force)
                await db.commit()
                
                return SyncResponse(
                    status="success",
                    message=f"All data updated to version {latest_version}",
                    entity_type="all",
                    current_version=latest_version
                )
            finally:
                await data_manager.close()
    except Exception as e:
        logger.error(f"Error syncing all data: {str(e)}", exc_info=True)
        raise ServiceError(detail=f"Error syncing all data: {str(e)}")


@router.post(
    "/missing-components",
    response_model=SyncResponse,
    summary="Sync missing component items",
    description="Identifies and synchronizes missing component items referenced in build paths"
)
async def sync_missing_components(
    request: SyncRequest = SyncRequest(),
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Synchronize missing component items that are referenced in item build paths
    but don't exist in the database.
    
    Args:
        request: Sync request parameters
        background_tasks: FastAPI background tasks
        db: Database session
        
    Returns:
        SyncResponse: Status of the sync operation
    """
    try:
        run_in_background = request.background and background_tasks is not None
        
        if run_in_background:
            background_tasks.add_task(_sync_missing_components_task)
            return SyncResponse(
                status="started",
                message="Missing components sync started in background",
                entity_type="components"
            )
        else:
            # Run synchronously
            from app.db.models import Item
            from app.services.data_dragon_service import DataDragonService
            from sqlalchemy.future import select
            
            # Initialize services
            data_manager = DataDragonManager(db)
            dd_service = DataDragonService()
            
            try:
                # Get the latest version
                latest_version = await dd_service.get_latest_version()
                
                # Get all items from Data Dragon
                dragon_items = await dd_service.fetch_items_data(latest_version)
                
                # Get all items in the database
                result = await db.execute(select(Item))
                db_items = {item.id: item for item in result.scalars().all()}
                
                # Extract all component IDs referenced in build paths
                referenced_component_ids = set()
                for item in db_items.values():
                    if item.built_from:
                        for component in item.built_from:
                            referenced_component_ids.add(component.id)
                
                # Find component IDs that don't exist in the database
                existing_ids = set(db_items.keys())
                missing_component_ids = referenced_component_ids - existing_ids
                
                if not missing_component_ids:
                    return SyncResponse(
                        status="skipped",
                        message="No missing components found",
                        entity_type="components",
                        current_version=latest_version
                    )
                
                logger.warning(f"Found {len(missing_component_ids)} missing components: {missing_component_ids}")
                
                # Create repository for sync
                repo = ItemRepository(db)
                
                # Synchronize missing components
                missing_items_data = {}
                for item_id in missing_component_ids:
                    if item_id in dragon_items:
                        missing_items_data[item_id] = dragon_items[item_id]
                        logger.info(f"Will sync item {item_id}: {dragon_items[item_id].name}")
                    else:
                        logger.warning(f"Item {item_id} not found in Data Dragon API")
                
                if missing_items_data:
                    logger.info(f"Synchronizing {len(missing_items_data)} missing components...")
                    updated_items = await repo.bulk_sync_items(missing_items_data, latest_version)
                    
                    # Build list of synchronized items
                    synced_items = [f"{item_id} ({item.name})" for item_id, item in updated_items.items()]
                    
                    await db.commit()
                    
                    return SyncResponse(
                        status="success",
                        message=f"Synchronized {len(updated_items)} missing components: {', '.join(synced_items)}",
                        entity_type="components",
                        current_version=latest_version
                    )
                else:
                    return SyncResponse(
                        status="skipped",
                        message="No missing components to synchronize",
                        entity_type="components",
                        current_version=latest_version
                    )
            finally:
                await data_manager.close()
                await dd_service.close()
    except Exception as e:
        logger.error(f"Error syncing missing components: {str(e)}", exc_info=True)
        raise ServiceError(detail=f"Error syncing missing components: {str(e)}")


@router.get(
    "/status",
    response_model=SyncStatusResponse,
    summary="Get sync status",
    description="Returns current version and update status for game data"
)
async def get_sync_status(
    db: AsyncSession = Depends(get_db)
):
    """
    Get the current sync status of all data types.
    
    Args:
        db: Database session
        
    Returns:
        SyncStatusResponse: Status of all data types
    """
    try:
        data_manager = DataDragonManager(db)
        
        try:
            latest_version = await data_manager.get_latest_version()
            updates_needed = await data_manager.check_for_updates()
            
            status = {}
            for entity_type in updates_needed:
                current_version = await data_manager.get_current_db_version(entity_type)
                status[entity_type] = {
                    "current_version": current_version,
                    "latest_version": latest_version,
                    "update_available": updates_needed[entity_type]
                }
            
            return SyncStatusResponse(
                latest_version=latest_version,
                status=status
            )
        finally:
            await data_manager.close()
    except Exception as e:
        logger.error(f"Error getting sync status: {str(e)}", exc_info=True)
        raise ServiceError(detail=f"Error getting sync status: {str(e)}")


# Background task functions
async def _sync_champions_task(force: bool = False):
    """Background task for syncing champion data"""
    from app.db.session import AsyncSessionLocal
    
    # Create a new database session specifically for this background task
    async with AsyncSessionLocal() as db:
        try:
            data_manager = DataDragonManager(db)
            try:
                latest_version = await data_manager.get_latest_version()
                current_version = await data_manager.get_current_db_version("champions")
                
                if current_version != latest_version or force:
                    logger.info(f"Background task: Syncing champions from version {current_version} to {latest_version}")
                    await data_manager.update_champions(latest_version)
                    await db.commit()
                    logger.info(f"Background task: Champions updated to version {latest_version}")
            except Exception as e:
                logger.error(f"Background task error syncing champions: {str(e)}", exc_info=True)
                await db.rollback()
                raise
            finally:
                await data_manager.close()
        except Exception as e:
            logger.error(f"Unhandled error in _sync_champions_task: {str(e)}", exc_info=True)


async def _sync_items_task(force: bool = False):
    """Background task for syncing item data"""
    from app.db.session import AsyncSessionLocal
    
    # Create a new database session specifically for this background task
    async with AsyncSessionLocal() as db:
        try:
            data_manager = DataDragonManager(db)
            try:
                latest_version = await data_manager.get_latest_version()
                current_version = await data_manager.get_current_db_version("items")
                
                if current_version != latest_version or force:
                    logger.info(f"Background task: Syncing items from version {current_version} to {latest_version}")
                    await data_manager.update_items(latest_version)
                    await db.commit()
                    logger.info(f"Background task: Items updated to version {latest_version}")
            except Exception as e:
                logger.error(f"Background task error syncing items: {str(e)}", exc_info=True)
                await db.rollback()
                raise
            finally:
                await data_manager.close()
        except Exception as e:
            logger.error(f"Unhandled error in _sync_items_task: {str(e)}", exc_info=True)


async def _sync_runes_task(force: bool = False):
    """Background task for syncing rune data"""
    from app.db.session import AsyncSessionLocal
    
    # Create a new database session specifically for this background task
    async with AsyncSessionLocal() as db:
        try:
            data_manager = DataDragonManager(db)
            try:
                latest_version = await data_manager.get_latest_version()
                current_version = await data_manager.get_current_db_version("runes")
                
                if current_version != latest_version or force:
                    logger.info(f"Background task: Syncing runes from version {current_version} to {latest_version}")
                    await data_manager.update_runes(latest_version)
                    await db.commit()
                    logger.info(f"Background task: Runes updated to version {latest_version}")
            except Exception as e:
                logger.error(f"Background task error syncing runes: {str(e)}", exc_info=True)
                await db.rollback()
                raise
            finally:
                await data_manager.close()
        except Exception as e:
            logger.error(f"Unhandled error in _sync_runes_task: {str(e)}", exc_info=True)


async def _sync_all_task(force: bool = False):
    """Background task for syncing all data"""
    from app.db.session import AsyncSessionLocal
    
    # Create a new database session specifically for this background task
    async with AsyncSessionLocal() as db:
        try:
            data_manager = DataDragonManager(db)
            try:
                latest_version = await data_manager.get_latest_version()
                updates_needed = await data_manager.check_for_updates()
                
                if any(updates_needed.values()) or force:
                    logger.info(f"Background task: Syncing all data to version {latest_version}")
                    await data_manager.update_all(force=force)
                    await db.commit()
                    logger.info(f"Background task: All data updated to version {latest_version}")
                    
                    # After updating all data, also check for missing components
                    await _sync_missing_components_task()
            except Exception as e:
                logger.error(f"Background task error syncing all data: {str(e)}", exc_info=True)
                await db.rollback()
                raise
            finally:
                await data_manager.close()
        except Exception as e:
            logger.error(f"Unhandled error in _sync_all_task: {str(e)}", exc_info=True)


async def _sync_missing_components_task():
    """Background task for syncing missing component items"""
    from app.db.session import AsyncSessionLocal
    from app.db.models import Item
    from app.services.data_dragon_service import DataDragonService
    from sqlalchemy.future import select
    
    # Create a new database session specifically for this background task
    async with AsyncSessionLocal() as db:
        try:
            # Initialize services
            data_manager = DataDragonManager(db)
            dd_service = DataDragonService()
            
            try:
                # Get the latest version
                latest_version = await dd_service.get_latest_version()
                
                # Get all items from Data Dragon
                logger.info("Background task: Fetching items from Data Dragon API...")
                dragon_items = await dd_service.fetch_items_data(latest_version)
                
                # Get all items in the database
                result = await db.execute(select(Item))
                db_items = {item.id: item for item in result.scalars().all()}
                
                # Extract all component IDs referenced in build paths
                referenced_component_ids = set()
                for item in db_items.values():
                    if item.built_from:
                        for component in item.built_from:
                            referenced_component_ids.add(component.id)
                
                # Find component IDs that don't exist in the database
                existing_ids = set(db_items.keys())
                missing_component_ids = referenced_component_ids - existing_ids
                
                if not missing_component_ids:
                    logger.info("Background task: No missing components found")
                    return
                
                logger.warning(f"Background task: Found {len(missing_component_ids)} missing components: {missing_component_ids}")
                
                # Create repository for sync
                repo = ItemRepository(db)
                
                # Synchronize missing components
                missing_items_data = {}
                for item_id in missing_component_ids:
                    if item_id in dragon_items:
                        missing_items_data[item_id] = dragon_items[item_id]
                        logger.info(f"Background task: Will sync item {item_id}: {dragon_items[item_id].name}")
                    else:
                        logger.warning(f"Background task: Item {item_id} not found in Data Dragon API")
                
                if missing_items_data:
                    logger.info(f"Background task: Synchronizing {len(missing_items_data)} missing components...")
                    updated_items = await repo.bulk_sync_items(missing_items_data, latest_version)
                    
                    # Build list of synchronized items
                    synced_items = [f"{item_id} ({item.name})" for item_id, item in updated_items.items()]
                    
                    await db.commit()
                    logger.info(f"Background task: Successfully synchronized {len(updated_items)} missing components: {', '.join(synced_items)}")
                else:
                    logger.info("Background task: No missing components to synchronize")
            except Exception as e:
                logger.error(f"Background task error syncing missing components: {str(e)}", exc_info=True)
                await db.rollback()
                raise
            finally:
                await data_manager.close()
                await dd_service.close()
        except Exception as e:
            logger.error(f"Unhandled error in _sync_missing_components_task: {str(e)}", exc_info=True)