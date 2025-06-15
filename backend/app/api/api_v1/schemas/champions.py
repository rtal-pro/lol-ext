from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

from app.api.api_v1.schemas.base import PaginatedResponse


class ImageData(BaseModel):
    """Image data for champions, spells, etc."""
    full: Optional[str] = Field(None, description="Full image filename")
    sprite: Optional[str] = Field(None, description="Sprite image filename")
    group: Optional[str] = Field(None, description="Image group")
    x: Optional[int] = Field(None, description="X coordinate in sprite")
    y: Optional[int] = Field(None, description="Y coordinate in sprite")
    w: Optional[int] = Field(None, description="Width in sprite")
    h: Optional[int] = Field(None, description="Height in sprite")
    
    model_config = ConfigDict(from_attributes=True)


class ChampionInfo(BaseModel):
    """Champion difficulty ratings"""
    attack: int = Field(..., description="Attack rating")
    defense: int = Field(..., description="Defense rating")
    magic: int = Field(..., description="Magic rating")
    difficulty: int = Field(..., description="Difficulty rating")
    
    model_config = ConfigDict(from_attributes=True)


class ChampionStats(BaseModel):
    """Champion base stats"""
    hp: float = Field(..., description="Base HP")
    hp_per_level: float = Field(..., description="HP per level", alias="hpPerLevel")
    mp: float = Field(..., description="Base MP/resource")
    mp_per_level: float = Field(..., description="MP per level", alias="mpPerLevel")
    move_speed: float = Field(..., description="Movement speed", alias="moveSpeed")
    armor: float = Field(..., description="Base armor")
    armor_per_level: float = Field(..., description="Armor per level", alias="armorPerLevel")
    spell_block: float = Field(..., description="Base magic resist", alias="spellBlock")
    spell_block_per_level: float = Field(..., description="Magic resist per level", alias="spellBlockPerLevel")
    attack_range: float = Field(..., description="Attack range", alias="attackRange")
    attack_damage: float = Field(..., description="Base attack damage", alias="attackDamage")
    attack_damage_per_level: float = Field(..., description="Attack damage per level", alias="attackDamagePerLevel")
    attack_speed: float = Field(..., description="Base attack speed", alias="attackSpeed")
    attack_speed_per_level: float = Field(..., description="Attack speed per level", alias="attackSpeedPerLevel")
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ChampionSummary(BaseModel):
    """Summary information for a champion"""
    id: str = Field(..., description="Champion ID (e.g., 'Aatrox')")
    key: str = Field(..., description="Champion numeric key (e.g., '266')")
    name: str = Field(..., description="Champion name")
    title: Optional[str] = Field(None, description="Champion title")
    image: ImageData = Field(..., description="Champion image data")
    tags: List[str] = Field(..., description="Champion tags (e.g., ['Fighter', 'Tank'])")
    
    model_config = ConfigDict(from_attributes=True)
    
    @classmethod
    def from_orm(cls, champion):
        """Create from ORM model with computed values"""
        return cls(
            id=champion.id,
            key=champion.key,
            name=champion.name,
            title=champion.title,
            image=ImageData(
                full=champion.image_full,
                sprite=champion.image_sprite,
                group=champion.image_group,
                x=None,
                y=None,
                w=None,
                h=None
            ),
            tags=[tag.name for tag in champion.tags]
        )


class ChampionListResponse(PaginatedResponse[ChampionSummary]):
    """Paginated response for champion list"""
    pass


class SpellType(str, Enum):
    """Champion spell types"""
    Q = "Q"
    W = "W"
    E = "E"
    R = "R"


class ChampionSpell(BaseModel):
    """Champion spell (ability) information"""
    id: str = Field(..., description="Spell ID")
    name: str = Field(..., description="Spell name")
    description: str = Field(..., description="Spell description")
    tooltip: str = Field(..., description="Detailed tooltip")
    max_rank: int = Field(..., description="Maximum spell rank", alias="maxRank")
    cooldown: List[float] = Field(..., description="Cooldown by rank")
    cost: List[int] = Field(..., description="Cost by rank")
    cost_type: str = Field(..., description="Cost type (e.g., 'mana')", alias="costType")
    range: List[int] = Field(..., description="Range by rank")
    image: ImageData = Field(..., description="Spell image data")
    spell_type: SpellType = Field(..., description="Spell type (Q,W,E,R)")
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    
    @classmethod
    def from_orm(cls, spell):
        """Create from ORM model with computed values"""
        return cls(
            id=spell.id,
            name=spell.name,
            description=spell.description,
            tooltip=spell.tooltip,
            maxRank=spell.max_rank,
            cooldown=spell.cooldown,
            cost=spell.cost,
            costType=spell.cost_type,
            range=spell.range,
            image=ImageData(
                full=spell.image_full,
                sprite=spell.image_sprite,
                group=spell.image_group,
                x=None,
                y=None,
                w=None,
                h=None
            ),
            spell_type=spell.spell_type.value
        )


class ChampionPassive(BaseModel):
    """Champion passive ability information"""
    name: str = Field(..., description="Passive name")
    description: str = Field(..., description="Passive description")
    image: ImageData = Field(..., description="Passive image data")
    
    model_config = ConfigDict(from_attributes=True)
    
    @classmethod
    def from_orm(cls, passive):
        """Create from ORM model with computed values"""
        return cls(
            name=passive.name,
            description=passive.description,
            image=ImageData(
                full=passive.image_full,
                sprite=passive.image_sprite,
                group=passive.image_group,
                x=None,
                y=None,
                w=None,
                h=None
            )
        )


class ChampionSkin(BaseModel):
    """Champion skin information"""
    id: str = Field(..., description="Skin ID")
    num: int = Field(..., description="Skin number")
    name: str = Field(..., description="Skin name")
    chromas: bool = Field(..., description="Has chromas")
    image_loading: str = Field(..., description="Loading screen image URL", alias="imageLoading")
    image_splash: str = Field(..., description="Splash art image URL", alias="imageSplash")
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ChampionDetail(BaseModel):
    """Detailed champion information"""
    id: str = Field(..., description="Champion ID")
    key: str = Field(..., description="Champion numeric key")
    name: str = Field(..., description="Champion name")
    title: Optional[str] = Field(None, description="Champion title")
    lore: Optional[str] = Field(None, description="Champion lore")
    blurb: Optional[str] = Field(None, description="Short champion description")
    ally_tips: List[str] = Field(default_factory=list, description="Tips for playing as this champion", alias="allyTips")
    enemy_tips: List[str] = Field(default_factory=list, description="Tips for playing against this champion", alias="enemyTips")
    tags: List[str] = Field(default_factory=list, description="Champion tags")
    partype: Optional[str] = Field(None, description="Resource type (e.g., 'Mana')")
    info: ChampionInfo = Field(..., description="Champion ratings")
    image: ImageData = Field(..., description="Champion image data")
    stats: ChampionStats = Field(..., description="Champion base stats")
    spells: List[ChampionSpell] = Field(default_factory=list, description="Champion abilities")
    passive: Optional[ChampionPassive] = Field(None, description="Champion passive ability")
    skins: List[ChampionSkin] = Field(default_factory=list, description="Champion skins")
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    
    @classmethod
    def from_orm(cls, champion, base_url: str = ""):
        """Create from ORM model with computed values"""
        # Create info and stats objects
        info = ChampionInfo(
            attack=champion.attack_rating or 0,
            defense=champion.defense_rating or 0,
            magic=champion.magic_rating or 0,
            difficulty=champion.difficulty_rating or 0
        )
        
        stats = ChampionStats(
            hp=champion.hp or 0,
            hpPerLevel=champion.hp_per_level or 0,
            mp=champion.mp or 0,
            mpPerLevel=champion.mp_per_level or 0,
            moveSpeed=champion.move_speed or 0,
            armor=champion.armor or 0,
            armorPerLevel=champion.armor_per_level or 0,
            spellBlock=champion.spell_block or 0,
            spellBlockPerLevel=champion.spell_block_per_level or 0,
            attackRange=champion.attack_range or 0,
            attackDamage=champion.attack_damage or 0,
            attackDamagePerLevel=champion.attack_damage_per_level or 0,
            attackSpeed=champion.attack_speed or 0,
            attackSpeedPerLevel=champion.attack_speed_per_level or 0
        )
        
        # Format skins with full URLs
        skins = []
        for skin in champion.skins:
            skins.append(ChampionSkin(
                id=skin.skin_id,
                num=skin.skin_num,
                name=skin.name,
                chromas=skin.chromas,
                imageLoading=f"{base_url}/img/champion/loading/{skin.image_loading}",
                imageSplash=f"{base_url}/img/champion/splash/{skin.image_splash}"
            ))
        
        # Format spells
        spells = [ChampionSpell.from_orm(spell) for spell in champion.spells]
        
        # Format passive
        passive = ChampionPassive.from_orm(champion.passive) if champion.passive else None
        
        return cls(
            id=champion.id,
            key=champion.key,
            name=champion.name,
            title=champion.title,  # Now optional, can be None
            lore=champion.lore,  # Now optional, can be None
            blurb=champion.blurb,  # Now optional, can be None
            allyTips=champion.ally_tips or [],
            enemyTips=champion.enemy_tips or [],
            tags=[tag.name for tag in champion.tags],
            partype=champion.partype or "None",
            info=info,
            image=ImageData(
                full=champion.image_full or "",
                sprite=champion.image_sprite or "",
                group=champion.image_group or "",
                x=None,
                y=None,
                w=None,
                h=None
            ),
            stats=stats,
            spells=spells,
            passive=passive,
            skins=skins
        )