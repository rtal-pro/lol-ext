from typing import Dict, List, Optional, Any, Set, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from datetime import datetime
import logging

from app.db.models import (
    Champion, 
    ChampionPassive, 
    Spell, 
    ChampionSkin, 
    Tag,
    SpellType
)
from app.db.repositories.base import RelationshipRepository, TransactionError
from app.services.data_dragon_service import ChampionDetail, ChampionSummary

logger = logging.getLogger(__name__)

class ChampionRepository(RelationshipRepository[Champion]):
    """Repository for Champion entities and related data"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Champion)
    
    async def get_with_details(self, champion_id: str) -> Optional[Champion]:
        """Get a champion with all related data (passive, spells, skins)"""
        return await self.get_with_relationships(
            champion_id, 
            ['passive', 'spells', 'skins', 'tags']
        )
    
    async def get_by_key(self, key: str) -> Optional[Champion]:
        """Get a champion by its numeric key"""
        result = await self.session.execute(
            select(Champion).where(Champion.key == key)
        )
        return result.scalars().first()
    
    async def get_by_name(self, name: str) -> Optional[Champion]:
        """Get a champion by name (case-insensitive)"""
        result = await self.session.execute(
            select(Champion).where(Champion.name.ilike(f"%{name}%"))
        )
        return result.scalars().first()
    
    async def get_or_create_tag(self, tag_name: str) -> Tag:
        """Get an existing tag or create a new one"""
        result = await self.session.execute(
            select(Tag).where(Tag.name == tag_name)
        )
        tag = result.scalars().first()
        
        if not tag:
            tag = Tag(name=tag_name)
            self.session.add(tag)
            await self.session.flush()
        
        return tag
    
    async def create_or_update_champion_from_api(
        self, 
        champion_data: ChampionDetail, 
        version: str
    ) -> Champion:
        """
        Create or update a champion and all related entities from API data
        
        Args:
            champion_data: Parsed champion data from the Data Dragon API
            version: The game data version
            
        Returns:
            Champion: The created or updated champion entity
        """
        # First check if champion exists
        champion_id = champion_data.id
        existing = await self.get_by_id(champion_id)
        
        # Prepare champion stats
        stats = champion_data.stats
        info = champion_data.info
        
        if existing:
            # Update existing champion
            champion = existing
            champion.key = champion_data.key
            champion.name = champion_data.name
            champion.title = champion_data.title
            champion.blurb = champion_data.blurb
            champion.lore = champion_data.lore
            champion.partype = champion_data.partype
            champion.version = version
            
            # Update stats
            champion.hp = stats.hp
            champion.hp_per_level = stats.hpperlevel
            champion.mp = stats.mp
            champion.mp_per_level = stats.mpperlevel
            champion.move_speed = stats.movespeed
            champion.armor = stats.armor
            champion.armor_per_level = stats.armorperlevel
            champion.spell_block = stats.spellblock
            champion.spell_block_per_level = stats.spellblockperlevel
            champion.attack_range = stats.attackrange
            champion.attack_damage = stats.attackdamage
            champion.attack_damage_per_level = stats.attackdamageperlevel
            champion.attack_speed = stats.attackspeed
            champion.attack_speed_per_level = stats.attackspeedperlevel
            
            # Update ratings
            champion.attack_rating = info.attack
            champion.defense_rating = info.defense
            champion.magic_rating = info.magic
            champion.difficulty_rating = info.difficulty
            
            # Update image data
            image = champion_data.image
            champion.image_full = image.full
            champion.image_sprite = image.sprite
            champion.image_group = image.group
            
            # Update tips
            champion.ally_tips = champion_data.allytips
            champion.enemy_tips = champion_data.enemytips
        else:
            # Create new champion
            champion = Champion(
                id=champion_id,
                key=champion_data.key,
                name=champion_data.name,
                title=champion_data.title,
                blurb=champion_data.blurb,
                lore=champion_data.lore,
                partype=champion_data.partype,
                version=version,
                
                # Stats
                hp=stats.hp,
                hp_per_level=stats.hpperlevel,
                mp=stats.mp,
                mp_per_level=stats.mpperlevel,
                move_speed=stats.movespeed,
                armor=stats.armor,
                armor_per_level=stats.armorperlevel,
                spell_block=stats.spellblock,
                spell_block_per_level=stats.spellblockperlevel,
                attack_range=stats.attackrange,
                attack_damage=stats.attackdamage,
                attack_damage_per_level=stats.attackdamageperlevel,
                attack_speed=stats.attackspeed,
                attack_speed_per_level=stats.attackspeedperlevel,
                
                # Ratings
                attack_rating=info.attack,
                defense_rating=info.defense,
                magic_rating=info.magic,
                difficulty_rating=info.difficulty,
                
                # Image data
                image_full=image.full,
                image_sprite=image.sprite,
                image_group=image.group,
                
                # Tips
                ally_tips=champion_data.allytips,
                enemy_tips=champion_data.enemytips
            )
            self.session.add(champion)
            await self.session.flush()
        
        # Update tags
        champion.tags = []
        for tag_name in champion_data.tags:
            tag = await self.get_or_create_tag(tag_name)
            champion.tags.append(tag)
        
        # Update passive ability
        passive_data = champion_data.passive
        if passive_data:
            await self._update_champion_passive(champion, passive_data)
        
        # Update spells (Q, W, E, R)
        spell_types = [SpellType.Q, SpellType.W, SpellType.E, SpellType.R]
        spells_data = champion_data.spells
        
        for i, spell_data in enumerate(spells_data[:4]):  # Limit to first 4 spells
            if i >= len(spell_types):
                break
                
            spell_id = spell_data.id
            spell_type = spell_types[i]
            
            await self._update_champion_spell(champion, spell_data, spell_type)
        
        # Update skins
        skins_data = champion_data.skins
        await self._update_champion_skins(champion, skins_data)
        
        # Save changes
        self.session.add(champion)
        await self.session.flush()
        
        return champion
    
    async def _update_champion_passive(
        self, 
        champion: Champion, 
        passive_data: Any
    ) -> ChampionPassive:
        """Update or create champion passive ability"""
        
        # Check if passive already exists
        result = await self.session.execute(
            select(ChampionPassive).where(ChampionPassive.champion_id == champion.id)
        )
        passive = result.scalars().first()
        
        # Prepare image data
        image = passive_data.image
        
        if passive:
            # Update existing passive
            passive.name = passive_data.name
            passive.description = passive_data.description
            
            # Update image data
            passive.image_full = image.full
            passive.image_sprite = image.sprite
            passive.image_group = image.group
        else:
            # Create new passive
            passive = ChampionPassive(
                id=f"{champion.id}_passive",
                champion_id=champion.id,
                name=passive_data.name,
                description=passive_data.description,
                
                # Image data
                image_full=image.full,
                image_sprite=image.sprite,
                image_group=image.group
            )
            self.session.add(passive)
        
        return passive
    
    async def _update_champion_spell(
        self, 
        champion: Champion, 
        spell_data: Any, 
        spell_type: SpellType
    ) -> Spell:
        """Update or create champion spell"""
        
        spell_id = spell_data.id
        
        # Check if spell already exists
        result = await self.session.execute(
            select(Spell)
            .where(Spell.champion_id == champion.id)
            .where(Spell.spell_type == spell_type)
        )
        spell = result.scalars().first()
        
        # Prepare image data
        image = spell_data.image
        
        if spell:
            # Update existing spell
            spell.id = spell_id
            spell.name = spell_data.name
            spell.description = spell_data.description
            spell.tooltip = spell_data.tooltip
            spell.max_rank = spell_data.maxrank
            
            # Update costs and cooldowns
            spell.cooldown = spell_data.cooldown
            spell.cost = spell_data.cost
            spell.cost_type = spell_data.costType
            spell.range = spell_data.range
            
            # Update image data
            spell.image_full = image.full
            spell.image_sprite = image.sprite
            spell.image_group = image.group
            
            # Update effects and variables
            spell.effect = spell_data.effect or []
            spell.variables = spell_data.vars or []
        else:
            # Create new spell
            spell = Spell(
                id=spell_id,
                champion_id=champion.id,
                spell_type=spell_type,
                name=spell_data.name,
                description=spell_data.description,
                tooltip=spell_data.tooltip,
                max_rank=spell_data.maxrank,
                
                # Costs and cooldowns
                cooldown=spell_data.cooldown,
                cost=spell_data.cost,
                cost_type=spell_data.costType,
                range=spell_data.range,
                
                # Image data
                image_full=image.full,
                image_sprite=image.sprite,
                image_group=image.group,
                
                # Effects and variables
                effect=spell_data.effect or [],
                variables=spell_data.vars or []
            )
            self.session.add(spell)
        
        return spell
    
    async def _update_champion_skins(
        self, 
        champion: Champion, 
        skins_data: List[Any]
    ) -> List[ChampionSkin]:
        """Update or create champion skins"""
        
        # Get existing skins to check against
        result = await self.session.execute(
            select(ChampionSkin).where(ChampionSkin.champion_id == champion.id)
        )
        existing_skins = {skin.skin_num: skin for skin in result.scalars().all()}
        
        # Track updated skins
        updated_skins = []
        
        for skin_data in skins_data:
            skin_id = skin_data.id
            skin_num = skin_data.num
            
            # Prepare image paths
            image_loading = f"{champion.id}_{skin_num}.jpg"
            image_splash = f"{champion.id}_{skin_num}.jpg"
            
            if skin_num in existing_skins:
                # Update existing skin
                skin = existing_skins[skin_num]
                skin.skin_id = skin_id
                skin.name = skin_data.name
                skin.chromas = skin_data.chromas
                skin.image_loading = image_loading
                skin.image_splash = image_splash
            else:
                # Create new skin
                skin = ChampionSkin(
                    champion_id=champion.id,
                    skin_id=skin_id,
                    skin_num=skin_num,
                    name=skin_data.name,
                    chromas=skin_data.chromas,
                    image_loading=image_loading,
                    image_splash=image_splash
                )
                self.session.add(skin)
            
            updated_skins.append(skin)
        
        # Delete skins that no longer exist
        updated_skin_nums = {skin.skin_num for skin in updated_skins}
        for skin_num, skin in existing_skins.items():
            if skin_num not in updated_skin_nums:
                await self.session.delete(skin)
        
        return updated_skins
    
    async def bulk_sync_champions(
        self, 
        champions_data: Dict[str, ChampionDetail], 
        version: str
    ) -> Dict[str, Champion]:
        """
        Synchronize multiple champions at once
        
        Args:
            champions_data: Dictionary of champion data from API
            version: The game data version
            
        Returns:
            Dict[str, Champion]: Dictionary of updated champion entities
        """
        updated_champions = {}
        
        try:
            # Start transaction for all updates
            for champion_id, champion_data in champions_data.items():
                updated_champion = await self.create_or_update_champion_from_api(
                    champion_data, 
                    version
                )
                updated_champions[champion_id] = updated_champion
            
            # Update the current version for champions
            await self.set_current_version(version, "champions")
            
            return updated_champions
            
        except Exception as e:
            logger.error(f"Error syncing champions: {str(e)}")
            raise TransactionError(f"Failed to sync champions: {str(e)}")
    
    async def search_champions(
        self, 
        name: Optional[str] = None, 
        tags: Optional[List[str]] = None, 
        difficulty: Optional[int] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[Champion], int]:
        """
        Search champions with filters
        
        Args:
            name: Filter by champion name (partial match)
            tags: Filter by champion tags
            difficulty: Filter by difficulty level
            limit: Maximum number of results
            offset: Pagination offset
            
        Returns:
            Tuple[List[Champion], int]: List of champions and total count
        """
        from sqlalchemy import func
        
        # Build the main query
        query = select(Champion)
        
        # Apply filters to main query
        if name:
            query = query.where(Champion.name.ilike(f"%{name}%"))
        
        if tags:
            for tag_name in tags:
                tag_subquery = (
                    select(Tag.id)
                    .where(Tag.name == tag_name)
                    .scalar_subquery()
                )
                query = query.join(Champion.tags).where(Tag.id == tag_subquery)
        
        if difficulty is not None:
            query = query.where(Champion.difficulty_rating <= difficulty)
        
        # Build the count query
        count_query = select(func.count()).select_from(
            query.with_only_columns(Champion.id).distinct().subquery()
        )
        
        # Execute queries
        result = await self.session.execute(query.limit(limit).offset(offset))
        count_result = await self.session.execute(count_query)
        
        champions = result.scalars().all()
        total_count = count_result.scalar() or 0
        
        return champions, total_count