import logging
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime

from app.db.models import (
    Champion, Item, RunePath, GameVersion,
    Spell, ChampionPassive, ChampionSkin,
    RuneSlot, Rune
)

# Set up logging
logger = logging.getLogger(__name__)


class ValidationResult:
    """Class to hold data validation results"""
    
    def __init__(self, entity_type: str):
        self.entity_type = entity_type
        self.total_count = 0
        self.valid_count = 0
        self.errors = []
        self.warnings = []
        self.start_time = datetime.now()
        self.end_time = None
        self.duration_ms = None
    
    def add_error(self, message: str, entity_id: str = None):
        """Add a validation error"""
        error = {
            "message": message,
            "entity_id": entity_id
        }
        self.errors.append(error)
        logger.error(f"Validation error: {message} - Entity: {entity_id}")
    
    def add_warning(self, message: str, entity_id: str = None):
        """Add a validation warning"""
        warning = {
            "message": message,
            "entity_id": entity_id
        }
        self.warnings.append(warning)
        logger.warning(f"Validation warning: {message} - Entity: {entity_id}")
    
    def finish(self):
        """Complete the validation and calculate duration"""
        self.end_time = datetime.now()
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
        
        logger.info(
            f"Validation complete for {self.entity_type}: "
            f"{self.valid_count}/{self.total_count} valid, "
            f"{len(self.errors)} errors, {len(self.warnings)} warnings, "
            f"took {self.duration_ms:.2f}ms"
        )
    
    def is_valid(self) -> bool:
        """Check if validation passed with no errors"""
        return len(self.errors) == 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert validation result to dictionary for API responses"""
        return {
            "entity_type": self.entity_type,
            "total_count": self.total_count,
            "valid_count": self.valid_count,
            "errors_count": len(self.errors),
            "warnings_count": len(self.warnings),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_ms": self.duration_ms,
            "is_valid": self.is_valid(),
            "errors": self.errors[:100],  # Limit to first 100 errors
            "warnings": self.warnings[:100]  # Limit to first 100 warnings
        }


class ValidationService:
    """Service for validating data integrity"""
    
    def __init__(self, session: AsyncSession):
        self.db = session
    
    async def validate_champions(self) -> ValidationResult:
        """Validate champion data integrity"""
        result = ValidationResult("champions")
        
        # Get current version for champions
        current_version = await self._get_current_version("champions")
        if not current_version:
            result.add_error("No current version found for champions")
            result.finish()
            return result
        
        # Get all champions for current version
        query = select(Champion).where(Champion.version == current_version)
        champions = await self.db.execute(query)
        champions = champions.scalars().all()
        
        result.total_count = len(champions)
        
        # Validate each champion
        for champion in champions:
            champion_valid = True
            
            # Check required fields
            if not champion.name:
                result.add_error("Champion name is missing", champion.id)
                champion_valid = False
                
            if not champion.key:
                result.add_error("Champion key is missing", champion.id)
                champion_valid = False
            
            # Check related data
            # 1. Passive ability
            passive_query = select(ChampionPassive).where(ChampionPassive.champion_id == champion.id)
            passive = await self.db.execute(passive_query)
            passive = passive.scalars().first()
            
            if not passive:
                result.add_error("Champion has no passive ability", champion.id)
                champion_valid = False
            
            # 2. Abilities
            spells_query = select(Spell).where(Spell.champion_id == champion.id)
            spells = await self.db.execute(spells_query)
            spells = spells.scalars().all()
            
            spell_types = [spell.spell_type for spell in spells]
            expected_types = ["Q", "W", "E", "R"]
            
            for expected_type in expected_types:
                if expected_type not in [str(t) for t in spell_types]:
                    result.add_error(f"Champion is missing {expected_type} ability", champion.id)
                    champion_valid = False
            
            # 3. Check at least one skin
            skins_query = select(ChampionSkin).where(ChampionSkin.champion_id == champion.id)
            skins_count = await self.db.execute(select(ChampionSkin).where(
                ChampionSkin.champion_id == champion.id
            ).with_only_columns([ChampionSkin.id]).count())
            skins_count = skins_count.scalar()
            
            if skins_count < 1:
                result.add_error("Champion has no skins", champion.id)
                champion_valid = False
            
            # Add warnings for potential issues
            if not champion.lore:
                result.add_warning("Champion has no lore", champion.id)
            
            if not champion.tags or len(champion.tags) == 0:
                result.add_warning("Champion has no tags", champion.id)
            
            # Increment valid count if all checks passed
            if champion_valid:
                result.valid_count += 1
        
        result.finish()
        return result
    
    async def validate_items(self) -> ValidationResult:
        """Validate item data integrity"""
        result = ValidationResult("items")
        
        # Get current version for items
        current_version = await self._get_current_version("items")
        if not current_version:
            result.add_error("No current version found for items")
            result.finish()
            return result
        
        # Get all items for current version
        query = select(Item).where(Item.version == current_version)
        items = await self.db.execute(query)
        items = items.scalars().all()
        
        result.total_count = len(items)
        
        # Validate each item
        for item in items:
            item_valid = True
            
            # Check required fields
            if not item.name:
                result.add_error("Item name is missing", item.id)
                item_valid = False
            
            # Check for recipe inconsistencies
            if item.built_from and not item.depth:
                result.add_warning("Item has components but no depth", item.id)
            
            if item.depth and item.depth > 1 and not item.built_from:
                result.add_error("Item has depth > 1 but no components", item.id)
                item_valid = False
            
            # Add warnings for potential issues
            if not item.description:
                result.add_warning("Item has no description", item.id)
            
            if not item.tags or len(item.tags) == 0:
                result.add_warning("Item has no tags", item.id)
            
            # Increment valid count if all checks passed
            if item_valid:
                result.valid_count += 1
        
        result.finish()
        return result
    
    async def validate_runes(self) -> ValidationResult:
        """Validate rune data integrity"""
        result = ValidationResult("runes")
        
        # Get current version for runes
        current_version = await self._get_current_version("runes")
        if not current_version:
            result.add_error("No current version found for runes")
            result.finish()
            return result
        
        # Get all rune paths for current version
        query = select(RunePath).where(RunePath.version == current_version)
        paths = await self.db.execute(query)
        paths = paths.scalars().all()
        
        result.total_count = len(paths)
        
        # Validate each rune path
        for path in paths:
            path_valid = True
            
            # Check required fields
            if not path.name:
                result.add_error("Rune path name is missing", str(path.id))
                path_valid = False
                
            if not path.key:
                result.add_error("Rune path key is missing", str(path.id))
                path_valid = False
            
            # Check for slots
            slots_query = select(RuneSlot).where(RuneSlot.path_id == path.id)
            slots = await self.db.execute(slots_query)
            slots = slots.scalars().all()
            
            if not slots:
                result.add_error("Rune path has no slots", str(path.id))
                path_valid = False
            
            # Check each slot has runes
            for slot in slots:
                runes_query = select(Rune).where(Rune.slot_id == slot.id)
                runes_count = await self.db.execute(select(Rune).where(
                    Rune.slot_id == slot.id
                ).with_only_columns([Rune.id]).count())
                runes_count = runes_count.scalar()
                
                if runes_count < 1:
                    result.add_error(f"Rune slot {slot.slot_number} has no runes", str(path.id))
                    path_valid = False
            
            # Increment valid count if all checks passed
            if path_valid:
                result.valid_count += 1
        
        result.finish()
        return result
    
    async def validate_all(self) -> Dict[str, ValidationResult]:
        """Validate all data types"""
        results = {}
        
        # Validate champions
        results["champions"] = await self.validate_champions()
        
        # Validate items
        results["items"] = await self.validate_items()
        
        # Validate runes
        results["runes"] = await self.validate_runes()
        
        return results
    
    async def _get_current_version(self, entity_type: str) -> Optional[str]:
        """Get current version for an entity type"""
        result = await self.db.execute(
            select(GameVersion.version)
            .where(GameVersion.entity_type == entity_type)
            .where(GameVersion.is_current == True)
        )
        version_row = result.first()
        return version_row[0] if version_row else None