from typing import Dict, List, Optional, Any, Set, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete, and_, or_
from datetime import datetime
import logging

from app.db.models import RunePath, RuneSlot, Rune
from app.db.repositories.base import RelationshipRepository, TransactionError

logger = logging.getLogger(__name__)

class RuneRepository(RelationshipRepository[RunePath]):
    """Repository for Rune entities and related data"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, RunePath)
    
    async def get_rune_tree(self, path_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a complete rune tree with all slots and runes
        
        Args:
            path_id: The rune path ID
            
        Returns:
            Dict containing the rune path, slots, and runes
        """
        path = await self.get_by_id(path_id)
        if not path:
            return None
        
        # Get slots with their runes in a single query
        slots_result = await self.session.execute(
            select(RuneSlot)
            .where(RuneSlot.path_id == path_id)
            .order_by(RuneSlot.slot_number)
        )
        slots = slots_result.scalars().all()
        
        if not slots:
            return {
                "path": path,
                "slots": []
            }
        
        # Get all slot IDs
        slot_ids = [slot.id for slot in slots]
        
        # Get all runes for all slots in a single query
        runes_result = await self.session.execute(
            select(Rune)
            .where(Rune.slot_id.in_(slot_ids))
            .order_by(Rune.slot_id, Rune.id)
        )
        all_runes = runes_result.scalars().all()
        
        # Group runes by slot_id
        runes_by_slot = {}
        for rune in all_runes:
            if rune.slot_id not in runes_by_slot:
                runes_by_slot[rune.slot_id] = []
            runes_by_slot[rune.slot_id].append(rune)
        
        # Assign runes to their slots
        for slot in slots:
            slot.runes = runes_by_slot.get(slot.id, [])
        
        return {
            "path": path,
            "slots": slots
        }
    
    async def get_all_rune_trees(self) -> List[Dict[str, Any]]:
        """
        Get all rune trees with their slots and runes
        
        Returns:
            List of dicts containing rune paths, slots, and runes
        """
        # Get all paths in a single query
        result = await self.session.execute(
            select(RunePath)
            .order_by(RunePath.id)
        )
        paths = result.scalars().all()
        
        if not paths:
            return []
        
        # Get all slots for all paths in a single query
        path_ids = [path.id for path in paths]
        slots_result = await self.session.execute(
            select(RuneSlot)
            .where(RuneSlot.path_id.in_(path_ids))
            .order_by(RuneSlot.path_id, RuneSlot.slot_number)
        )
        all_slots = slots_result.scalars().all()
        
        # Group slots by path_id
        slots_by_path = {}
        for slot in all_slots:
            if slot.path_id not in slots_by_path:
                slots_by_path[slot.path_id] = []
            slots_by_path[slot.path_id].append(slot)
        
        # Get all slot IDs
        slot_ids = [slot.id for slot in all_slots]
        
        # Get all runes for all slots in a single query
        if slot_ids:
            runes_result = await self.session.execute(
                select(Rune)
                .where(Rune.slot_id.in_(slot_ids))
                .order_by(Rune.slot_id, Rune.id)
            )
            all_runes = runes_result.scalars().all()
            
            # Group runes by slot_id
            runes_by_slot = {}
            for rune in all_runes:
                if rune.slot_id not in runes_by_slot:
                    runes_by_slot[rune.slot_id] = []
                runes_by_slot[rune.slot_id].append(rune)
            
            # Assign runes to their slots
            for slot in all_slots:
                slot.runes = runes_by_slot.get(slot.id, [])
        
        # Build tree for each path
        trees = []
        for path in paths:
            trees.append({
                "path": path,
                "slots": slots_by_path.get(path.id, [])
            })
        
        return trees
    
    async def get_rune_by_key(self, key: str) -> Optional[Rune]:
        """Get a rune by its key"""
        result = await self.session.execute(
            select(Rune).where(Rune.key == key)
        )
        return result.scalars().first()
    
    async def get_path_by_key(self, key: str) -> Optional[RunePath]:
        """Get a rune path by its key"""
        result = await self.session.execute(
            select(RunePath).where(RunePath.key == key)
        )
        return result.scalars().first()
    
    async def create_or_update_rune_path(
        self, 
        path_data: Dict[str, Any], 
        version: str
    ) -> Tuple[RunePath, List[RuneSlot]]:
        """
        Create or update a rune path and its slots
        
        Args:
            path_data: Rune path data from API
            version: The game data version
            
        Returns:
            Tuple of the path and its slots
        """
        path_id = path_data.get("id")
        if not path_id:
            raise ValueError("Rune path ID is required")
        
        # Check if path already exists
        existing_path = await self.get_by_id(path_id)
        
        if existing_path:
            # Update existing path
            path = existing_path
            path.key = path_data.get("key", "")
            path.name = path_data.get("name", "")
            path.icon = path_data.get("icon", "")
            path.version = version
        else:
            # Create new path
            path = RunePath(
                id=path_id,
                key=path_data.get("key", ""),
                name=path_data.get("name", ""),
                icon=path_data.get("icon", ""),
                version=version
            )
            self.session.add(path)
            await self.session.flush()
        
        # Process slots
        slots = []
        slots_data = path_data.get("slots", [])
        
        for slot_idx, slot_data in enumerate(slots_data):
            # Check if slot already exists
            result = await self.session.execute(
                select(RuneSlot)
                .where(RuneSlot.path_id == path_id)
                .where(RuneSlot.slot_number == slot_idx)
            )
            existing_slot = result.scalars().first()
            
            if not existing_slot:
                # Create new slot
                slot = RuneSlot(
                    path_id=path_id,
                    slot_number=slot_idx
                )
                self.session.add(slot)
                await self.session.flush()
            else:
                slot = existing_slot
            
            slots.append(slot)
        
        return path, slots
    
    async def create_or_update_runes(
        self, 
        slot: RuneSlot, 
        runes_data: List[Dict[str, Any]], 
        version: str
    ) -> List[Rune]:
        """
        Create or update runes in a slot
        
        Args:
            slot: The slot to add runes to
            runes_data: List of rune data from API
            version: The game data version
            
        Returns:
            List of created or updated runes
        """
        updated_runes = []
        existing_rune_ids = set()
        
        # Get existing runes in this slot
        result = await self.session.execute(
            select(Rune).where(Rune.slot_id == slot.id)
        )
        existing_runes = {rune.id: rune for rune in result.scalars().all()}
        
        # Process each rune
        for rune_data in runes_data:
            rune_id = rune_data.get("id")
            if not rune_id:
                continue
                
            existing_rune_ids.add(rune_id)
            
            if rune_id in existing_runes:
                # Update existing rune
                rune = existing_runes[rune_id]
                rune.slot_id = slot.id
                rune.key = rune_data.get("key", "")
                rune.name = rune_data.get("name", "")
                rune.short_desc = rune_data.get("shortDesc", "")
                rune.long_desc = rune_data.get("longDesc", "")
                rune.icon = rune_data.get("icon", "")
                rune.version = version
            else:
                # Create new rune
                rune = Rune(
                    id=rune_id,
                    slot_id=slot.id,
                    key=rune_data.get("key", ""),
                    name=rune_data.get("name", ""),
                    short_desc=rune_data.get("shortDesc", ""),
                    long_desc=rune_data.get("longDesc", ""),
                    icon=rune_data.get("icon", ""),
                    version=version
                )
                self.session.add(rune)
            
            updated_runes.append(rune)
        
        # Delete runes that no longer exist
        for rune_id, rune in existing_runes.items():
            if rune_id not in existing_rune_ids:
                await self.session.delete(rune)
        
        await self.session.flush()
        return updated_runes
    
    async def sync_rune_tree(
        self, 
        path_data: Dict[str, Any], 
        version: str
    ) -> Dict[str, Any]:
        """
        Sync a complete rune tree with its slots and runes
        
        Args:
            path_data: Rune path data from API
            version: The game data version
            
        Returns:
            Dict containing the updated path, slots, and runes
        """
        # Create or update path and slots
        path, slots = await self.create_or_update_rune_path(path_data, version)
        
        # Process runes in each slot
        slots_data = path_data.get("slots", [])
        for i, (slot, slot_data) in enumerate(zip(slots, slots_data)):
            runes_data = slot_data.get("runes", [])
            runes = await self.create_or_update_runes(slot, runes_data, version)
            slot.runes = runes
        
        return {
            "path": path,
            "slots": slots
        }
    
    async def bulk_sync_runes(
        self, 
        rune_data: List[Dict[str, Any]], 
        version: str
    ) -> List[Dict[str, Any]]:
        """
        Synchronize multiple rune trees at once
        
        Args:
            rune_data: List of rune path data from API
            version: The game data version
            
        Returns:
            List of updated rune trees
        """
        updated_trees = []
        
        try:
            # Process each rune path
            for path_data in rune_data:
                tree = await self.sync_rune_tree(path_data, version)
                updated_trees.append(tree)
            
            # Update the current version for runes
            await self.set_current_version(version, "runes")
            
            return updated_trees
            
        except Exception as e:
            logger.error(f"Error syncing runes: {str(e)}")
            raise TransactionError(f"Failed to sync runes: {str(e)}")
    
    async def search_runes(
        self, 
        name: Optional[str] = None, 
        path_key: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[Rune], int]:
        """
        Search runes with filters
        
        Args:
            name: Filter by rune name or description (partial match)
            path_key: Filter by path key (e.g., "Domination")
            limit: Maximum number of results
            offset: Pagination offset
            
        Returns:
            Tuple[List[Rune], int]: List of runes and total count
        """
        from sqlalchemy import func
        
        query = select(Rune)
        
        # Apply filters
        if name:
            name_filter = or_(
                Rune.name.ilike(f"%{name}%"),
                Rune.short_desc.ilike(f"%{name}%"),
                Rune.long_desc.ilike(f"%{name}%")
            )
            query = query.where(name_filter)
        
        if path_key:
            # Join through RuneSlot to RunePath
            query = query.join(RuneSlot).join(RunePath)
            query = query.where(RunePath.key == path_key)
        
        # Create a separate count query based on the same filters
        count_query = select(func.count()).select_from(
            select(Rune.id).distinct().where(query.whereclause).subquery()
        )
            
        # Add pagination to main query
        paginated_query = query.limit(limit).offset(offset)
        
        # Execute queries
        result = await self.session.execute(paginated_query)
        count_result = await self.session.execute(count_query)
        
        runes = result.scalars().all()
        total_count = count_result.scalar() or 0
        
        return runes, total_count