from typing import Dict, List, Optional, Any, Set, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete, and_, or_, case
from sqlalchemy.orm import aliased
from datetime import datetime
import logging

from app.db.models import Item, Tag, item_recipes
from app.db.repositories.base import RelationshipRepository, TransactionError
from app.db.repositories.champion_repository import ChampionRepository
from app.services.data_dragon_service import Item as ItemSchema

logger = logging.getLogger(__name__)

class ItemRepository(RelationshipRepository[Item]):
    """Repository for Item entities and related data"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Item)
        self.champion_repo = ChampionRepository(session)
    
    async def get_with_relationships(self, item_id: str) -> Optional[Item]:
        """Get an item with its relationships (tags, recipes)"""
        return await super().get_with_relationships(
            item_id, 
            ['tags', 'builds_into', 'built_from']
        )
    
    async def get_by_name(self, name: str) -> List[Item]:
        """Get items by name (case-insensitive)"""
        result = await self.session.execute(
            select(Item).where(Item.name.ilike(f"%{name}%"))
        )
        return result.scalars().all()
    
    async def get_item_tree(self, item_id: str, depth: int = 2) -> Dict[str, Any]:
        """
        Get an item's recipe tree with components and items it builds into
        
        Args:
            item_id: The item ID to get the tree for
            depth: How many levels of recipe to follow (default: 2)
            
        Returns:
            Dict containing the item, its components, and what it builds into
        """
        item = await self.get_with_relationships(item_id)
        if not item:
            return None
        
        result = {
            "item": item,
            "components": [],
            "builds_into": []
        }
        
        # Get components recursively up to specified depth
        if depth > 0 and item.built_from:
            for component in item.built_from:
                component_tree = await self.get_item_tree(component.id, depth - 1)
                if component_tree:
                    result["components"].append(component_tree)
        
        # Get items it builds into recursively up to specified depth
        if depth > 0 and item.builds_into:
            for builds_into in item.builds_into:
                builds_into_tree = await self.get_item_tree(builds_into.id, depth - 1)
                if builds_into_tree:
                    result["builds_into"].append(builds_into_tree)
        
        return result
    
    async def get_or_create_tag(self, tag_name: str) -> Tag:
        """Get an existing tag or create a new one"""
        return await self.champion_repo.get_or_create_tag(tag_name)
    
    async def create_or_update_item_from_api(
        self, 
        item_data: ItemSchema, 
        item_id: str, 
        version: str
    ) -> Item:
        """
        Create or update an item from API data
        
        Args:
            item_data: Parsed item data from the Data Dragon API
            item_id: The item ID
            version: The game data version
            
        Returns:
            Item: The created or updated item entity
        """
        # First check if item exists
        existing = await self.get_by_id(item_id)
        
        # Get gold data
        gold = item_data.gold
        
        if existing:
            # Update existing item
            item = existing
            item.name = item_data.name
            item.description = item_data.description
            item.plain_text = item_data.plaintext
            item.version = version
            
            # Update item details
            item.required_champion = item_data.requiredChampion
            item.required_ally = item_data.requiredAlly
            
            # Update item economy
            item.base_gold = gold.base
            item.total_gold = gold.total
            item.sell_gold = gold.sell
            item.purchasable = gold.purchasable
            
            # Update stats
            item.stats = item_data.stats
            
            # Update special attributes
            item.consumed = item_data.consumed
            item.consumable = item_data.consumeOnFull
            item.in_store = item_data.inStore
            item.hide_from_all = item_data.hideFromAll
            item.special_recipe = item_data.specialRecipe
            
            # Update maps availability
            item.maps = item_data.maps
            
            # Update image data
            image = item_data.image
            item.image_full = image.full
            item.image_sprite = image.sprite
            item.image_group = image.group
            
            # Update depth and tier
            item.depth = item_data.depth or 1
            item.tier = item_data.depth or 1  # Default to depth if tier not specified
        else:
            # Create new item
            item = Item(
                id=item_id,
                name=item_data.name,
                description=item_data.description,
                plain_text=item_data.plaintext,
                version=version,
                
                # Item details
                required_champion=item_data.requiredChampion,
                required_ally=item_data.requiredAlly,
                
                # Economy
                base_gold=gold.base,
                total_gold=gold.total,
                sell_gold=gold.sell,
                purchasable=gold.purchasable,
                
                # Stats
                stats=item_data.stats,
                
                # Special attributes
                consumed=item_data.consumed,
                consumable=item_data.consumeOnFull,
                in_store=item_data.inStore,
                hide_from_all=item_data.hideFromAll,
                special_recipe=item_data.specialRecipe,
                
                # Maps availability
                maps=item_data.maps,
                
                # Image data
                image_full=image.full,
                image_sprite=image.sprite,
                image_group=image.group,
                
                # Depth and tier
                depth=item_data.depth or 1,
                tier=item_data.depth or 1  # Default to depth if tier not specified
            )
            self.session.add(item)
            await self.session.flush()
        
        # Update tags
        item.tags = []
        for tag_name in item_data.tags:
            tag = await self.get_or_create_tag(tag_name)
            item.tags.append(tag)
        
        # Save to get item ID for recipes
        self.session.add(item)
        await self.session.flush()
        
        return item
    
    async def process_item_recipes(
        self, 
        all_items: Dict[str, Item], 
        items_data: Dict[str, ItemSchema]
    ) -> None:
        """
        Process item recipes after all items are created
        
        Args:
            all_items: Dictionary of all items by ID
            items_data: Dictionary of item data from API
        """
        # Clear existing recipe relationships for all items
        await self.session.execute(delete(item_recipes))
        await self.session.flush()
        
        # First pass: Process explicit recipes from the API data
        for item_id, item_data in items_data.items():
            item = all_items.get(item_id)
            if not item:
                continue
            
            # Process "builds into" relationships
            for into_id in item_data.into or []:
                into_item = all_items.get(into_id)
                if into_item:
                    item.builds_into.append(into_item)
            
            # Process "built from" relationships
            for from_id in item_data.from_ or []:
                from_item = all_items.get(from_id)
                if from_item:
                    item.built_from.append(from_item)
        
        # Save first pass changes
        await self.session.flush()
        
        # Second pass: Create a reverse mapping to fix missing "built from" relationships
        builds_from_map = {}
        
        # Build the reverse mapping based on "builds into" relationships
        for item_id, item_data in items_data.items():
            # Extract "into" array
            into_items = item_data.into or []
            
            # For each item this builds into, add this item as a component
            for into_id in into_items:
                if into_id not in builds_from_map:
                    builds_from_map[into_id] = []
                builds_from_map[into_id].append(item_id)
        
        # Apply fixes for items with missing "built from" relationships
        for item_id, components in builds_from_map.items():
            item = all_items.get(item_id)
            if not item:
                continue
                
            # Get the item data from API
            item_data = items_data.get(item_id)
            if not item_data:
                continue
                
            # Check if the item has a "from" array in the API data
            has_from_in_api = hasattr(item_data, 'from_') and item_data.from_
            
            # Special handling for mythic items (typically tier 4)
            is_mythic = False
            
            # Check for mythic status by looking for special mythic-related tags
            if item_data.tags and any(tag.lower() in ["mythic", "legendary"] for tag in item_data.tags):
                is_mythic = True
            # Also check gold value - mythics typically have high gold value
            elif hasattr(item_data, 'gold') and item_data.gold.total > 2500:
                is_mythic = True
            # Check depth/tier as another indicator of mythic status
            elif item_data.depth and item_data.depth >= 3:
                is_mythic = True
                
            # If the item doesn't have explicit "from" components in the API
            # but should have them according to our reverse mapping
            # OR if it's a mythic item that should have components
            if (not has_from_in_api and components and not item.built_from) or (is_mythic and not item.built_from):
                logger.info(f"Fixing missing build components for item {item_id} ({item.name})")
                
                # For each component, add the relationship
                for component_id in components:
                    component = all_items.get(component_id)
                    if component and component not in item.built_from:
                        # Add the component relationship
                        item.built_from.append(component)
            
            # Special handling for mythic items with no build path in reverse mapping
            if is_mythic and not components and not item.built_from:
                logger.warning(f"Mythic item {item_id} ({item.name}) has no components in API. "
                              f"This might indicate an issue with the item data.")
                
                # For mythic items, try to infer components if possible
                # Look for items with similar stats that could be components
                # This is a heuristic approach and may need refinement
                potential_components = []
                for other_id, other_item in all_items.items():
                    # Skip if the item is the same or is a high-tier item itself
                    if other_id == item_id or (other_item.tier and other_item.tier >= 3):
                        continue
                    
                    # If this item has stats and is a basic/intermediate item, consider it
                    if other_item.tier and other_item.tier <= 2:
                        potential_components.append(other_id)
                
                # If we found potential components, use them based on price
                if potential_components:
                    # Sort by total_gold to get the most valuable components first
                    sorted_components = sorted(
                        [(c_id, all_items[c_id]) for c_id in potential_components if c_id in all_items],
                        key=lambda x: x[1].total_gold or 0, 
                        reverse=True
                    )
                    
                    # Take the top 2-3 components that would make sense for this mythic
                    for component_id, component in sorted_components[:3]:
                        if component.total_gold and item.total_gold and component.total_gold < item.total_gold:
                            logger.info(f"Adding inferred component {component_id} ({component.name}) "
                                      f"to mythic item {item_id} ({item.name})")
                            item.built_from.append(component)
        
        # Save all changes
        await self.session.flush()
    
    async def validate_mythic_item_build_paths(self, items: Dict[str, Item]) -> None:
        """
        Validates build paths for mythic items and logs warnings for missing components
        
        Args:
            items: Dictionary of item entities by ID
        """
        mythic_items = []
        
        # Identify mythic items based on tags and attributes
        for item_id, item in items.items():
            is_mythic = False
            
            # Check tags for mythic indicators
            if item.tags and any(tag.name.lower() in ["mythic", "legendary"] for tag in item.tags):
                is_mythic = True
            # Check gold value - mythics typically have high gold value
            elif item.total_gold and item.total_gold > 2500:
                is_mythic = True
            # Check tier/depth as another indicator
            elif item.tier and item.tier >= 3:
                is_mythic = True
                
            if is_mythic:
                mythic_items.append(item)
        
        # Check and log any mythic items without build paths
        for item in mythic_items:
            if not item.built_from:
                logger.warning(
                    f"Mythic item {item.id} ({item.name}) has no build components after synchronization. "
                    f"This might indicate an issue with the item data."
                )
            else:
                component_count = len(item.built_from)
                logger.info(f"Mythic item {item.id} ({item.name}) has {component_count} components")
    
    async def ensure_mythic_item_build_paths(
        self,
        all_items: Dict[str, Item],
        items_data: Dict[str, ItemSchema]
    ) -> None:
        """
        Ensures all mythic items have proper build paths, even if missing in the API data.
        This method runs additional checks and fixes for mythic items specifically.
        
        Args:
            all_items: Dictionary of all item entities by ID
            items_data: Dictionary of item data from API
        """
        mythic_items = []
        
        # Identify mythic items
        for item_id, item in all_items.items():
            # Check if this is a mythic item
            is_mythic = False
            
            # Check tags for mythic indicators
            if item.tags and any(tag.name.lower() in ["mythic", "legendary"] for tag in item.tags):
                is_mythic = True
            # Check gold value - mythics typically have high gold value
            elif item.total_gold and item.total_gold > 2500:
                is_mythic = True
            # Check tier/depth as another indicator
            elif item.tier and item.tier >= 3:
                is_mythic = True
            
            if is_mythic:
                mythic_items.append(item_id)
        
        # Handle mythic items with missing build paths
        for item_id in mythic_items:
            item = all_items[item_id]
            
            # Skip if it already has components
            if item.built_from:
                continue
                
            logger.warning(f"Mythic item {item_id} ({item.name}) has no build components. Attempting to fix...")
            
            # Get the Data Dragon item data
            item_data = items_data.get(item_id)
            if not item_data:
                continue
                
            # First try the from_ field if it exists but wasn't properly processed
            if hasattr(item_data, 'from_') and item_data.from_:
                for component_id in item_data.from_:
                    if component_id in all_items:
                        component = all_items[component_id]
                        logger.info(f"Adding component {component_id} ({component.name}) to {item.name}")
                        item.built_from.append(component)
            else:
                # If no components specified in API, try to infer based on other items
                # that build into similar tier items
                similar_items = []
                
                # Find similar tier items with known components
                for other_id, other_item in all_items.items():
                    if other_id == item_id:
                        continue
                        
                    # If it's a similar tier item with components
                    if (other_item.tier and item.tier and other_item.tier == item.tier and 
                            other_item.built_from):
                        similar_items.append(other_item)
                
                if similar_items:
                    # Use components from similar items as a reference
                    potential_components = set()
                    for similar in similar_items:
                        for component in similar.built_from:
                            potential_components.add(component.id)
                    
                    # Add components that make sense
                    for component_id in potential_components:
                        if component_id in all_items:
                            component = all_items[component_id]
                            # Only add if the gold value makes sense
                            if (component.total_gold and item.total_gold and 
                                    component.total_gold < item.total_gold * 0.6):
                                logger.info(
                                    f"Adding inferred component {component_id} ({component.name}) "
                                    f"to {item.name} based on similar items"
                                )
                                item.built_from.append(component)
                else:
                    # No similar items, use basic components based on gold value
                    basic_components = []
                    for other_id, other_item in all_items.items():
                        # Skip if it's the same item or not a basic/intermediate item
                        if other_id == item_id or not other_item.tier or other_item.tier > 2:
                            continue
                            
                        # Consider basic and intermediate items with appropriate cost
                        if (other_item.total_gold and item.total_gold and 
                                other_item.total_gold < item.total_gold * 0.5):
                            basic_components.append((other_id, other_item))
                    
                    # Sort by total gold to get most valuable components first
                    basic_components.sort(key=lambda x: x[1].total_gold or 0, reverse=True)
                    
                    # Add up to 3 components for a reasonable build path
                    for i, (component_id, component) in enumerate(basic_components[:3]):
                        logger.info(
                            f"Adding basic component {component_id} ({component.name}) "
                            f"to {item.name} based on gold value"
                        )
                        item.built_from.append(component)
                        
                        # If we've added enough value, stop
                        total_component_value = sum(c.total_gold or 0 for c in item.built_from)
                        if total_component_value > item.total_gold * 0.7:
                            break
        
        await self.session.flush()
    
    async def bulk_sync_items(
        self, 
        items_data: Dict[str, ItemSchema], 
        version: str
    ) -> Dict[str, Item]:
        """
        Synchronize multiple items at once
        
        Args:
            items_data: Dictionary of item data from API
            version: The game data version
            
        Returns:
            Dict[str, Item]: Dictionary of updated item entities
        """
        updated_items = {}
        
        try:
            # First pass: Create or update all items
            for item_id, item_data in items_data.items():
                updated_item = await self.create_or_update_item_from_api(
                    item_data, 
                    item_id, 
                    version
                )
                updated_items[item_id] = updated_item
            
            # Second pass: Process recipes
            await self.process_item_recipes(updated_items, items_data)
            
            # Third pass: Validate mythic item build paths
            await self.validate_mythic_item_build_paths(updated_items)
            
            # Fourth pass: Ensure mythic items have build paths
            await self.ensure_mythic_item_build_paths(updated_items, items_data)
            
            # Update the current version for items
            await self.set_current_version(version, "items")
            
            return updated_items
            
        except Exception as e:
            logger.error(f"Error syncing items: {str(e)}")
            raise TransactionError(f"Failed to sync items: {str(e)}")
    
    async def search_items(
        self, 
        name: Optional[str] = None, 
        tags: Optional[List[str]] = None, 
        min_gold: Optional[int] = None,
        max_gold: Optional[int] = None,
        purchasable_only: bool = False,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[Item], int]:
        """
        Search items with filters
        
        Args:
            name: Filter by item name (partial match)
            tags: Filter by item tags
            min_gold: Minimum total gold cost
            max_gold: Maximum total gold cost
            purchasable_only: Only include purchasable items
            limit: Maximum number of results
            offset: Pagination offset
            
        Returns:
            Tuple[List[Item], int]: List of items and total count
        """
        from sqlalchemy import func, text
        
        try:
            # First build a filtered subquery with just the IDs to avoid JSON issues
            id_query = select(Item.id)
            
            # Apply filters to ID query
            if name:
                name_filter = or_(
                    Item.name.ilike(f"%{name}%"),
                    Item.description.ilike(f"%{name}%")
                )
                id_query = id_query.where(name_filter)
            
            if tags:
                # Improved tag filtering with distinct joins
                for tag_name in tags:
                    if not tag_name:  # Skip empty tags
                        continue
                    tag_alias = aliased(Tag)
                    id_query = id_query.join(
                        Item.tags.of_type(tag_alias), 
                        isouter=False
                    ).where(tag_alias.name == tag_name)
            
            if min_gold is not None:
                id_query = id_query.where(Item.total_gold >= min_gold)
            
            if max_gold is not None:
                id_query = id_query.where(Item.total_gold <= max_gold)
            
            if purchasable_only:
                id_query = id_query.where(Item.purchasable == True)
                
            # Apply distinct to ID query and order by ID - using only scalar fields for ordering
            # Avoid using any JSON fields in the ORDER BY clause
            id_query = id_query.distinct().order_by(Item.id)
            
            # Get total count first - using a subquery to avoid nested transaction errors
            count_query = select(func.count()).select_from(
                select(Item.id).distinct().where(id_query.whereclause).subquery()
            )
            count_result = await self.session.execute(count_query)
            total_count = count_result.scalar() or 0
            
            # No items possible based on the count
            if total_count == 0:
                return [], 0
            
            # Apply pagination to the ID query
            paginated_id_query = id_query.limit(limit).offset(offset)
            
            # Get filtered and paginated IDs
            id_result = await self.session.execute(paginated_id_query)
            filtered_ids = [row[0] for row in id_result]
            
            # No items found after pagination
            if not filtered_ids:
                return [], total_count
                
            # Fetch complete items by ID - no JSON ordering here, just a simple IN query
            # Use a position-based ordering to preserve the original order from the ID query
            position_case = case(
                {id_val: i for i, id_val in enumerate(filtered_ids)},
                value=Item.id
            )
            
            items_query = (
                select(Item)
                .where(Item.id.in_(filtered_ids))
                .order_by(position_case)
            )
            
            items_result = await self.session.execute(items_query)
            items = items_result.scalars().all()
            
            return items, total_count
        except Exception as e:
            # Log the specific error but wrap it in a more generic error for the caller
            logger.error(f"Error in search_items repository method: {str(e)}")
            
            # If we have a transaction error or PostgreSQL error related to JSON comparison
            if "json" in str(e).lower() or "transaction" in str(e).lower():
                logger.warning("PostgreSQL JSON comparison error detected, using alternative query approach")
                
                # Fall back to a simpler query that doesn't use any JSON operations
                # This is less efficient but more reliable when there are JSON fields
                basic_query = select(Item.id).order_by(Item.id)
                
                # Apply basic filters that don't involve JSON
                if name:
                    basic_query = basic_query.where(Item.name.ilike(f"%{name}%"))
                
                if purchasable_only:
                    basic_query = basic_query.where(Item.purchasable == True)
                
                # Get a fresh count using the basic query
                try:
                    # Get IDs with pagination
                    basic_result = await self.session.execute(
                        basic_query.limit(limit).offset(offset)
                    )
                    basic_ids = [row[0] for row in basic_result]
                    
                    # Get items by ID
                    if basic_ids:
                        items_result = await self.session.execute(
                            select(Item).where(Item.id.in_(basic_ids)).order_by(Item.id)
                        )
                        items = items_result.scalars().all()
                        
                        # Simple approximate count
                        count_approx = await self.session.execute(
                            select(func.count(Item.id))
                        )
                        count = count_approx.scalar() or 0
                        
                        return items, count
                    
                    return [], 0
                except Exception as fallback_error:
                    # If even the fallback approach fails, log and re-raise
                    logger.error(f"Fallback query also failed: {str(fallback_error)}")
                    raise
            
            # Re-raise for caller to handle
            await self.session.rollback()
            raise TransactionError(f"Failed to search items: {str(e)}")