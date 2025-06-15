import httpx
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete

from app.db.models import (
    GameVersion, Champion, Spell, ChampionPassive, ChampionSkin,
    Item, Tag, RunePath, RuneSlot, Rune, SummonerSpell,
    champion_tags, item_tags, item_recipes
)

logger = logging.getLogger(__name__)

class DataDragonManager:
    """
    Manages fetching, versioning, and storing Data Dragon content.
    
    Handles:
    - Checking for new Data Dragon versions
    - Fetching and updating game data
    - Managing version transitions
    - Seeding initial data
    """
    
    BASE_URL = "https://ddragon.leagueoflegends.com"
    CDN_URL = f"{BASE_URL}/cdn"
    API_URL = f"{BASE_URL}/api"
    
    def __init__(self, session: AsyncSession, language: str = "en_US"):
        self.db = session
        self.language = language
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        """Close HTTP client when done"""
        await self.http_client.aclose()
    
    async def get_latest_version(self) -> str:
        """Get the latest available Data Dragon version"""
        response = await self.http_client.get(f"{self.API_URL}/versions.json")
        response.raise_for_status()
        versions = response.json()
        return versions[0]  # First item is the latest version
    
    async def get_current_db_version(self, entity_type: str) -> Optional[str]:
        """Get the current version stored in the database for a specific entity type"""
        result = await self.db.execute(
            select(GameVersion.version)
            .where(GameVersion.entity_type == entity_type)
            .where(GameVersion.is_current == True)
        )
        version_row = result.first()
        return version_row[0] if version_row else None
    
    async def set_current_version(self, version: str, entity_type: str):
        """Set a specific version as current for an entity type"""
        # First, unset any current versions
        await self.db.execute(
            update(GameVersion)
            .where(GameVersion.entity_type == entity_type)
            .where(GameVersion.is_current == True)
            .values(is_current=False)
        )
        
        # Check if this version exists
        result = await self.db.execute(
            select(GameVersion)
            .where(GameVersion.entity_type == entity_type)
            .where(GameVersion.version == version)
        )
        version_row = result.first()
        
        if version_row:
            # Update existing version to current
            await self.db.execute(
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
            self.db.add(game_version)
            await self.db.flush()
    
    async def check_for_updates(self) -> Dict[str, bool]:
        """
        Check if updates are available for any data entity types.
        Returns a dictionary of entity types and whether they need updating.
        """
        latest_version = await self.get_latest_version()
        
        entity_types = ["champions", "items", "runes", "summoner-spells"]
        update_status = {}
        
        for entity_type in entity_types:
            current_version = await self.get_current_db_version(entity_type)
            update_status[entity_type] = current_version != latest_version
        
        return update_status

    async def fetch_champion_data(self, version: str, champion_id: Optional[str] = None) -> Dict:
        """
        Fetch champion data from Data Dragon API.
        If champion_id is provided, fetch detailed data for that champion.
        Otherwise, fetch summary data for all champions.
        """
        if champion_id:
            url = f"{self.CDN_URL}/{version}/data/{self.language}/champion/{champion_id}.json"
        else:
            url = f"{self.CDN_URL}/{version}/data/{self.language}/champion.json"
        
        response = await self.http_client.get(url)
        response.raise_for_status()
        return response.json()
    
    async def fetch_item_data(self, version: str) -> Dict:
        """Fetch item data from Data Dragon API"""
        url = f"{self.CDN_URL}/{version}/data/{self.language}/item.json"
        response = await self.http_client.get(url)
        response.raise_for_status()
        return response.json()
    
    async def fetch_rune_data(self, version: str) -> List[Dict]:
        """Fetch rune data from Data Dragon API"""
        url = f"{self.CDN_URL}/{version}/data/{self.language}/runesReforged.json"
        response = await self.http_client.get(url)
        response.raise_for_status()
        return response.json()
    
    async def fetch_summoner_spell_data(self, version: str) -> Dict:
        """Fetch summoner spell data from Data Dragon API"""
        url = f"{self.CDN_URL}/{version}/data/{self.language}/summoner.json"
        response = await self.http_client.get(url)
        response.raise_for_status()
        return response.json()
    
    async def update_all(self, force: bool = False):
        """
        Update all game data to the latest version if needed.
        If force is True, update regardless of version check.
        """
        latest_version = await self.get_latest_version()
        updates_needed = await self.check_for_updates()
        
        # Only update if needed or forced
        if force or any(updates_needed.values()):
            # Process each data type in order
            if force or updates_needed["champions"]:
                await self.update_champions(latest_version)
            
            if force or updates_needed["items"]:
                await self.update_items(latest_version)
            
            if force or updates_needed["runes"]:
                await self.update_runes(latest_version)
            
            if force or updates_needed["summoner-spells"]:
                await self.update_summoner_spells(latest_version)
            
            # Commit all changes
            await self.db.commit()
            return True
        
        return False  # No updates needed
    
    async def get_or_create_tag(self, tag_name: str) -> Tag:
        """Get existing tag or create a new one"""
        result = await self.db.execute(
            select(Tag).where(Tag.name == tag_name)
        )
        tag = result.scalars().first()
        
        if not tag:
            tag = Tag(name=tag_name)
            self.db.add(tag)
            await self.db.flush()
        
        return tag
    
    async def update_champions(self, version: str):
        """Update champion data to the specified version"""
        logger.info(f"Updating champions to version {version}")
        
        try:
            # Fetch summary champion data first
            champion_data = await self.fetch_champion_data(version)
            
            # Get all champion IDs to fetch detailed data
            champion_ids = list(champion_data["data"].keys())
            
            # Fetch detailed data for each champion
            for champion_id in champion_ids:
                try:
                    detailed_data = await self.fetch_champion_data(version, champion_id)
                    champion_info = detailed_data["data"][champion_id]
                    
                    # Check if champion already exists
                    result = await self.db.execute(
                        select(Champion).where(Champion.id == champion_id)
                    )
                    champion = result.scalars().first()
                    
                    # Prepare champion stats
                    stats = champion_info["stats"]
                    info = champion_info["info"]
                    
                    if champion:
                        # Update existing champion
                        champion.key = champion_info["key"]
                        champion.name = champion_info["name"]
                        champion.title = champion_info["title"]
                        champion.blurb = champion_info["blurb"]
                        champion.lore = champion_info.get("lore", "")
                        champion.partype = champion_info["partype"]
                        champion.version = version
                        
                        # Update stats
                        champion.hp = stats.get("hp")
                        champion.hp_per_level = stats.get("hpperlevel")
                        champion.mp = stats.get("mp")
                        champion.mp_per_level = stats.get("mpperlevel")
                        champion.move_speed = stats.get("movespeed")
                        champion.armor = stats.get("armor")
                        champion.armor_per_level = stats.get("armorperlevel")
                        champion.spell_block = stats.get("spellblock")
                        champion.spell_block_per_level = stats.get("spellblockperlevel")
                        champion.attack_range = stats.get("attackrange")
                        champion.attack_damage = stats.get("attackdamage")
                        champion.attack_damage_per_level = stats.get("attackdamageperlevel")
                        champion.attack_speed = stats.get("attackspeed")
                        champion.attack_speed_per_level = stats.get("attackspeedperlevel")
                        
                        # Update ratings
                        champion.attack_rating = info.get("attack")
                        champion.defense_rating = info.get("defense")
                        champion.magic_rating = info.get("magic")
                        champion.difficulty_rating = info.get("difficulty")
                        
                        # Update image data
                        image = champion_info.get("image", {})
                        champion.image_full = image.get("full")
                        champion.image_sprite = image.get("sprite")
                        champion.image_group = image.get("group")
                        
                        # Update tips
                        champion.ally_tips = champion_info.get("allytips", [])
                        champion.enemy_tips = champion_info.get("enemytips", [])
                    else:
                        # Create new champion
                        champion = Champion(
                            id=champion_id,
                            key=champion_info["key"],
                            name=champion_info["name"],
                            title=champion_info["title"],
                            blurb=champion_info["blurb"],
                            lore=champion_info.get("lore", ""),
                            partype=champion_info["partype"],
                            version=version,
                            
                            # Stats
                            hp=stats.get("hp"),
                            hp_per_level=stats.get("hpperlevel"),
                            mp=stats.get("mp"),
                            mp_per_level=stats.get("mpperlevel"),
                            move_speed=stats.get("movespeed"),
                            armor=stats.get("armor"),
                            armor_per_level=stats.get("armorperlevel"),
                            spell_block=stats.get("spellblock"),
                            spell_block_per_level=stats.get("spellblockperlevel"),
                            attack_range=stats.get("attackrange"),
                            attack_damage=stats.get("attackdamage"),
                            attack_damage_per_level=stats.get("attackdamageperlevel"),
                            attack_speed=stats.get("attackspeed"),
                            attack_speed_per_level=stats.get("attackspeedperlevel"),
                            
                            # Ratings
                            attack_rating=info.get("attack"),
                            defense_rating=info.get("defense"),
                            magic_rating=info.get("magic"),
                            difficulty_rating=info.get("difficulty"),
                            
                            # Image data
                            image_full=champion_info.get("image", {}).get("full"),
                            image_sprite=champion_info.get("image", {}).get("sprite"),
                            image_group=champion_info.get("image", {}).get("group"),
                            
                            # Tips
                            ally_tips=champion_info.get("allytips", []),
                            enemy_tips=champion_info.get("enemytips", [])
                        )
                        self.db.add(champion)
                        await self.db.flush()  # Ensure champion is created before adding tags
                    
                    # Clear existing tags by executing a delete query instead of modifying the relationship
                    await self.db.execute(
                        delete(champion_tags).where(champion_tags.c.champion_id == champion_id)
                    )
                    
                    # Add new tags - insert directly into junction table instead of using ORM collections
                    for tag_name in champion_info.get("tags", []):
                        tag = await self.get_or_create_tag(tag_name)
                        # Use direct SQL insert instead of using champion.tags.append()
                        await self.db.execute(
                            champion_tags.insert().values(
                                champion_id=champion_id,
                                tag_id=tag.id
                            )
                        )
                    
                    # Update passive ability
                    passive_data = champion_info.get("passive", {})
                    if passive_data:
                        # Check if passive already exists
                        result = await self.db.execute(
                            select(ChampionPassive).where(ChampionPassive.champion_id == champion_id)
                        )
                        passive = result.scalars().first()
                        
                        if passive:
                            # Update existing passive
                            passive.name = passive_data.get("name", "")
                            passive.description = passive_data.get("description", "")
                            
                            # Update image data
                            image = passive_data.get("image", {})
                            passive.image_full = image.get("full")
                            passive.image_sprite = image.get("sprite")
                            passive.image_group = image.get("group")
                        else:
                            # Create new passive
                            passive = ChampionPassive(
                                id=f"{champion_id}_passive",
                                champion_id=champion_id,
                                name=passive_data.get("name", ""),
                                description=passive_data.get("description", ""),
                                
                                # Image data
                                image_full=passive_data.get("image", {}).get("full"),
                                image_sprite=passive_data.get("image", {}).get("sprite"),
                                image_group=passive_data.get("image", {}).get("group")
                            )
                            self.db.add(passive)
                            await self.db.flush()  # Ensure passive is created before processing spells
                    
                    # Update spells (Q, W, E, R)
                    spells_data = champion_info.get("spells", [])
                    spell_types = ["Q", "W", "E", "R"]
                    
                    for i, spell_data in enumerate(spells_data[:4]):  # Limit to first 4 spells
                        spell_id = spell_data.get("id")
                        if not spell_id:
                            continue
                        
                        # Check if spell already exists
                        result = await self.db.execute(
                            select(Spell).where(Spell.id == spell_id)
                        )
                        spell = result.scalars().first()
                        
                        spell_type = spell_types[i] if i < len(spell_types) else None
                        if not spell_type:
                            continue
                        
                        if spell:
                            # Update existing spell
                            spell.name = spell_data.get("name", "")
                            spell.description = spell_data.get("description", "")
                            spell.tooltip = spell_data.get("tooltip", "")
                            spell.max_rank = spell_data.get("maxrank")
                            
                            # Update costs and cooldowns
                            spell.cooldown = spell_data.get("cooldown", [])
                            spell.cost = spell_data.get("cost", [])
                            spell.cost_type = spell_data.get("costType", "")
                            spell.range = spell_data.get("range", [])
                            
                            # Update image data
                            image = spell_data.get("image", {})
                            spell.image_full = image.get("full")
                            spell.image_sprite = image.get("sprite")
                            spell.image_group = image.get("group")
                            
                            # Update effects and variables
                            spell.effect = spell_data.get("effect", [])
                            spell.variables = spell_data.get("vars", [])
                        else:
                            # Create new spell
                            spell = Spell(
                                id=spell_id,
                                champion_id=champion_id,
                                spell_type=spell_type,
                                name=spell_data.get("name", ""),
                                description=spell_data.get("description", ""),
                                tooltip=spell_data.get("tooltip", ""),
                                max_rank=spell_data.get("maxrank"),
                                
                                # Costs and cooldowns
                                cooldown=spell_data.get("cooldown", []),
                                cost=spell_data.get("cost", []),
                                cost_type=spell_data.get("costType", ""),
                                range=spell_data.get("range", []),
                                
                                # Image data
                                image_full=spell_data.get("image", {}).get("full"),
                                image_sprite=spell_data.get("image", {}).get("sprite"),
                                image_group=spell_data.get("image", {}).get("group"),
                                
                                # Effects and variables
                                effect=spell_data.get("effect", []),
                                variables=spell_data.get("vars", [])
                            )
                            self.db.add(spell)
                            await self.db.flush()  # Ensure spell is created before processing next spell
                    
                    # Update skins
                    skins_data = champion_info.get("skins", [])
                    for skin_data in skins_data:
                        skin_id = skin_data.get("id")
                        skin_num = skin_data.get("num")
                        if not skin_id or skin_num is None:
                            continue
                        
                        # Check if skin already exists
                        result = await self.db.execute(
                            select(ChampionSkin).where(ChampionSkin.champion_id == champion_id)
                            .where(ChampionSkin.skin_num == skin_num)
                        )
                        skin = result.scalars().first()
                        
                        # Prepare image paths
                        image_loading = f"{champion_id}_{skin_num}.jpg"
                        image_splash = f"{champion_id}_{skin_num}.jpg"
                        
                        if skin:
                            # Update existing skin
                            skin.skin_id = skin_id
                            skin.name = skin_data.get("name", "")
                            skin.chromas = skin_data.get("chromas", False)
                            skin.image_loading = image_loading
                            skin.image_splash = image_splash
                        else:
                            # Create new skin
                            skin = ChampionSkin(
                                champion_id=champion_id,
                                skin_id=skin_id,
                                skin_num=skin_num,
                                name=skin_data.get("name", ""),
                                chromas=skin_data.get("chromas", False),
                                image_loading=image_loading,
                                image_splash=image_splash
                            )
                            self.db.add(skin)
                            await self.db.flush()  # Ensure skin is created before proceeding
                except Exception as e:
                    logger.error(f"Error processing champion {champion_id}: {str(e)}")
                    # Rollback the current transaction and start a new one
                    await self.db.rollback()
                    # Don't propagate the exception, continue with next champion
            
            # Update version
            await self.set_current_version(version, "champions")
            # Commit the transaction
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Error in update_champions: {str(e)}")
            # Rollback the transaction on any error
            await self.db.rollback()
            # Re-raise the exception to be handled by the caller
            raise
    
    async def update_items(self, version: str):
        """Update item data to the specified version"""
        logger.info(f"Updating items to version {version}")
        
        try:
            # Fetch item data
            item_data = await self.fetch_item_data(version)
            
            # Process all items
            for item_id, item_info in item_data.get("data", {}).items():
                try:
                    # Check if item already exists
                    result = await self.db.execute(
                        select(Item).where(Item.id == item_id)
                    )
                    item = result.scalars().first()
                    
                    # Get gold data
                    gold = item_info.get("gold", {})
                
                    # Handle required champion validation
                    required_champion_id = item_info.get("requiredChampion")
                    if required_champion_id:
                        # Case-insensitive lookup for champion ID
                        result = await self.db.execute(
                            select(Champion).where(
                                Champion.id.ilike(required_champion_id)
                            )
                        )
                        champion = result.scalars().first()
                        
                        if champion:
                            # Use the actual champion ID from the database (preserves case)
                            required_champion_id = champion.id
                        else:
                            # Log warning and set to None if champion doesn't exist
                            logger.warning(f"Item {item_id} ({item_info.get('name', '')}) requires champion '{required_champion_id}' which does not exist in database. Setting required_champion to null.")
                            required_champion_id = None
                    
                    if item:
                        # Update existing item
                        item.name = item_info.get("name", "")
                        item.description = item_info.get("description", "")
                        item.plain_text = item_info.get("plaintext", "")
                        item.version = version
                        
                        # Update item details with validated champion
                        item.required_champion = required_champion_id
                        item.required_ally = item_info.get("requiredAlly")
                        
                        # Update item economy
                        item.base_gold = gold.get("base")
                        item.total_gold = gold.get("total")
                        item.sell_gold = gold.get("sell")
                        item.purchasable = gold.get("purchasable", True)
                        
                        # Update stats
                        item.stats = item_info.get("stats", {})
                        
                        # Update special attributes
                        item.consumed = item_info.get("consumed", False)
                        item.consumable = item_info.get("consumable", False)
                        item.in_store = item_info.get("inStore", True) 
                        item.hide_from_all = item_info.get("hideFromAll", False)
                        item.special_recipe = item_info.get("specialRecipe")
                        
                        # Update maps availability
                        item.maps = item_info.get("maps", {})
                        
                        # Update image data
                        image = item_info.get("image", {})
                        item.image_full = image.get("full")
                        item.image_sprite = image.get("sprite")
                        item.image_group = image.get("group")
                        
                        # Update depth and tier
                        item.depth = item_info.get("depth", 1)
                        # For tier, derive from depth or from "tier" field if present
                        item.tier = item_info.get("tier", item.depth)
                    else:
                        # Create new item
                        item = Item(
                            id=item_id,
                            name=item_info.get("name", ""),
                            description=item_info.get("description", ""),
                            plain_text=item_info.get("plaintext", ""),
                            version=version,
                            
                            # Item details with validated champion
                            required_champion=required_champion_id,
                            required_ally=item_info.get("requiredAlly"),
                            
                            # Economy
                            base_gold=gold.get("base"),
                            total_gold=gold.get("total"),
                            sell_gold=gold.get("sell"),
                            purchasable=gold.get("purchasable", True),
                            
                            # Stats
                            stats=item_info.get("stats", {}),
                            
                            # Special attributes
                            consumed=item_info.get("consumed", False),
                            consumable=item_info.get("consumable", False),
                            in_store=item_info.get("inStore", True),
                            hide_from_all=item_info.get("hideFromAll", False),
                            special_recipe=item_info.get("specialRecipe"),
                            
                            # Maps availability
                            maps=item_info.get("maps", {}),
                            
                            # Image data
                            image_full=item_info.get("image", {}).get("full"),
                            image_sprite=item_info.get("image", {}).get("sprite"),
                            image_group=item_info.get("image", {}).get("group"),
                            
                            # Depth and tier
                            depth=item_info.get("depth", 1),
                            tier=item_info.get("tier", item_info.get("depth", 1))
                        )
                        self.db.add(item)
                    
                    # Make sure item is created first and flushed to database before adding tags
                    if item:
                        # Update existing item's fields
                        await self.db.execute(
                            update(Item)
                            .where(Item.id == item_id)
                            .values(
                                name=item_info.get("name", ""),
                                description=item_info.get("description", ""),
                                plain_text=item_info.get("plaintext", ""),
                                version=version,
                                required_champion=required_champion_id,
                                required_ally=item_info.get("requiredAlly"),
                                base_gold=gold.get("base"),
                                total_gold=gold.get("total"),
                                sell_gold=gold.get("sell"),
                                purchasable=gold.get("purchasable", True),
                                stats=item_info.get("stats", {}),
                                consumed=item_info.get("consumed", False),
                                consumable=item_info.get("consumable", False),
                                in_store=item_info.get("inStore", True),
                                hide_from_all=item_info.get("hideFromAll", False),
                                special_recipe=item_info.get("specialRecipe"),
                                maps=item_info.get("maps", {}),
                                image_full=item_info.get("image", {}).get("full"),
                                image_sprite=item_info.get("image", {}).get("sprite"),
                                image_group=item_info.get("image", {}).get("group"),
                                depth=item_info.get("depth", 1),
                                tier=item_info.get("tier", item_info.get("depth", 1))
                            )
                        )
                    await self.db.flush()  # Ensure any updates are flushed to DB
                    
                    # First ensure the item exists and is properly flushed to DB
                    item_exists_result = await self.db.execute(select(Item).where(Item.id == item_id))
                    if not item_exists_result.scalars().first():
                        # Skip tag operations for non-existent items
                        continue
                        
                    # Clear existing tags by executing a delete query instead of modifying the relationship
                    await self.db.execute(
                        delete(item_tags).where(item_tags.c.item_id == item_id)
                    )
                    
                    # Add new tags - insert directly into junction table instead of using ORM collections
                    for tag_name in item_info.get("tags", []):
                        tag = await self.get_or_create_tag(tag_name)
                        # Use direct SQL insert instead of using item.tags.append()
                        await self.db.execute(
                            item_tags.insert().values(
                                item_id=item_id,
                                tag_id=tag.id
                            )
                        )
                    
                    # Save to get item ID for recipes
                    await self.db.flush()
                    
                    # Clear existing recipe relationships
                    await self.db.execute(
                        delete(item_recipes).where(item_recipes.c.item_id == item_id)
                    )
                    await self.db.execute(
                        delete(item_recipes).where(item_recipes.c.component_id == item_id)
                    )
                    
                    # First verify the current item exists in the database
                    item_result = await self.db.execute(
                        select(Item).where(Item.id == item_id)
                    )
                    current_item = item_result.scalars().first()
                    
                    if not current_item:
                        # Skip recipe operations for non-existent items
                        continue
                        
                    # Add "builds into" relationships
                    for into_id in item_info.get("into", []):
                        result = await self.db.execute(
                            select(Item).where(Item.id == into_id)
                        )
                        into_item = result.scalars().first()
                        if into_item:
                            # Instead of appending to relationship, insert directly into junction table
                            await self.db.execute(
                                item_recipes.insert().values(
                                    item_id=item_id,            # Current item
                                    component_id=into_id        # Item it builds into
                                )
                            )
                    
                    # Add "built from" relationships
                    for from_id in item_info.get("from", []):
                        result = await self.db.execute(
                            select(Item).where(Item.id == from_id)
                        )
                        from_item = result.scalars().first()
                        if from_item:
                            # Instead of appending to relationship, insert directly into junction table
                            await self.db.execute(
                                item_recipes.insert().values(
                                    component_id=item_id,       # Current item as component
                                    item_id=from_id             # Item it's built from
                                )
                            )
                except Exception as e:
                    logger.error(f"Error processing item {item_id}: {str(e)}")
                    # Rollback the current transaction and start a new one
                    await self.db.rollback()
                    # Don't propagate the exception, continue with next item
            
            # Update version
            await self.set_current_version(version, "items")
            # Commit the transaction
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Error in update_items: {str(e)}")
            # Rollback the transaction on any error
            await self.db.rollback()
            # Re-raise the exception to be handled by the caller
            raise
    
    async def update_runes(self, version: str):
        """Update rune data to the specified version"""
        logger.info(f"Updating runes to version {version}")
        
        # Fetch rune data
        rune_data = await self.fetch_rune_data(version)
        
        # Process all rune paths
        for path_data in rune_data:
            path_id = path_data.get("id")
            if not path_id:
                continue
            
            # Check if path already exists
            result = await self.db.execute(
                select(RunePath).where(RunePath.id == path_id)
            )
            path = result.scalars().first()
            
            if path:
                # Update existing path
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
                self.db.add(path)
                await self.db.flush()  # Ensure path is created before processing slots
            
            # Process slots
            slots_data = path_data.get("slots", [])
            for slot_idx, slot_data in enumerate(slots_data):
                # Check if slot already exists
                result = await self.db.execute(
                    select(RuneSlot)
                    .where(RuneSlot.path_id == path_id)
                    .where(RuneSlot.slot_number == slot_idx)
                )
                slot = result.scalars().first()
                
                if not slot:
                    # Create new slot
                    slot = RuneSlot(
                        path_id=path_id,
                        slot_number=slot_idx
                    )
                    self.db.add(slot)
                    await self.db.flush()
                
                # Process runes in the slot
                runes_data = slot_data.get("runes", [])
                for rune_data in runes_data:
                    rune_id = rune_data.get("id")
                    if not rune_id:
                        continue
                    
                    # Check if rune already exists
                    result = await self.db.execute(
                        select(Rune).where(Rune.id == rune_id)
                    )
                    rune = result.scalars().first()
                    
                    if rune:
                        # Update existing rune using direct SQL update
                        await self.db.execute(
                            update(Rune)
                            .where(Rune.id == rune_id)
                            .values(
                                slot_id=slot.id,
                                key=rune_data.get("key", ""),
                                name=rune_data.get("name", ""),
                                short_desc=rune_data.get("shortDesc", ""),
                                long_desc=rune_data.get("longDesc", ""),
                                icon=rune_data.get("icon", ""),
                                version=version
                            )
                        )
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
                        self.db.add(rune)
                        await self.db.flush()  # Ensure rune is created before proceeding
        
        # Update version
        await self.set_current_version(version, "runes")
    
    async def update_summoner_spells(self, version: str):
        """Update summoner spell data to the specified version"""
        logger.info(f"Updating summoner spells to version {version}")
        
        # Fetch summoner spell data
        spell_data = await self.fetch_summoner_spell_data(version)
        
        # Process all summoner spells
        for spell_id, spell_info in spell_data.get("data", {}).items():
            # Check if spell already exists
            result = await self.db.execute(
                select(SummonerSpell).where(SummonerSpell.id == spell_id)
            )
            spell = result.scalars().first()
            
            if spell:
                # Update existing spell
                spell.key = spell_info.get("key", "")
                spell.name = spell_info.get("name", "")
                spell.description = spell_info.get("description", "")
                spell.tooltip = spell_info.get("tooltip", "")
                spell.max_rank = spell_info.get("maxrank", 1)
                spell.cooldown = spell_info.get("cooldown", [])
                spell.range = spell_info.get("range", [])
                spell.summoner_level = spell_info.get("summonerLevel")
                spell.modes = spell_info.get("modes", [])
                spell.version = version
                
                # Update image data
                image = spell_info.get("image", {})
                spell.image_full = image.get("full")
                spell.image_sprite = image.get("sprite")
                spell.image_group = image.get("group")
            else:
                # Create new spell
                spell = SummonerSpell(
                    id=spell_id,
                    key=spell_info.get("key", ""),
                    name=spell_info.get("name", ""),
                    description=spell_info.get("description", ""),
                    tooltip=spell_info.get("tooltip", ""),
                    max_rank=spell_info.get("maxrank", 1),
                    cooldown=spell_info.get("cooldown", []),
                    range=spell_info.get("range", []),
                    summoner_level=spell_info.get("summonerLevel"),
                    modes=spell_info.get("modes", []),
                    version=version,
                    
                    # Image data
                    image_full=spell_info.get("image", {}).get("full"),
                    image_sprite=spell_info.get("image", {}).get("sprite"),
                    image_group=spell_info.get("image", {}).get("group")
                )
                self.db.add(spell)
                await self.db.flush()  # Ensure summoner spell is created before proceeding
        
        # Update version
        await self.set_current_version(version, "summoner-spells")
    
    async def seed_initial_data(self):
        """Seed the database with initial data from latest version"""
        latest_version = await self.get_latest_version()
        await self.update_all(force=True)
        # Make sure changes are committed
        await self.db.commit()
        return latest_version