from sqlalchemy import (
    Column, 
    Integer, 
    String, 
    Float, 
    Boolean, 
    ForeignKey, 
    JSON, 
    Table,
    Text,
    Enum,
    UniqueConstraint,
    Index,
    ARRAY,
    BigInteger
)
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()

# Association table for champion tags (many-to-many)
champion_tags = Table(
    'champion_tags',
    Base.metadata,
    Column('champion_id', String, ForeignKey('champions.id')),
    Column('tag_id', Integer, ForeignKey('tags.id')),
    UniqueConstraint('champion_id', 'tag_id', name='uq_champion_tag')
)

# Association table for item tags (many-to-many)
item_tags = Table(
    'item_tags',
    Base.metadata,
    Column('item_id', String, ForeignKey('items.id')),
    Column('tag_id', Integer, ForeignKey('tags.id')),
    UniqueConstraint('item_id', 'tag_id', name='uq_item_tag')
)

# Association table for item recipes (many-to-many)
item_recipes = Table(
    'item_recipes',
    Base.metadata,
    Column('item_id', String, ForeignKey('items.id'), primary_key=True),
    Column('component_id', String, ForeignKey('items.id'), primary_key=True),
)


class GameVersion(Base):
    """Tracks Data Dragon versions for each entity type"""
    __tablename__ = 'game_versions'
    
    id = Column(Integer, primary_key=True)
    version = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)  # champions, items, runes, etc.
    is_current = Column(Boolean, default=False)
    release_date = Column(String)
    
    # Create unique constraint for version + entity_type
    __table_args__ = (
        UniqueConstraint('version', 'entity_type', name='uq_version_entity'),
        Index('idx_current_version', 'entity_type', 'is_current'),
    )


class Tag(Base):
    """Champion and item tags/categories"""
    __tablename__ = 'tags'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    
    # Relationships
    champions = relationship("Champion", secondary=champion_tags, back_populates="tags")
    items = relationship("Item", secondary=item_tags, back_populates="tags")


class Champion(Base):
    """Champion base information"""
    __tablename__ = 'champions'
    
    # From Data Dragon API
    id = Column(String, primary_key=True)  # Champion ID (e.g., "Aatrox")
    key = Column(String, nullable=False, unique=True)  # Numeric key (e.g., "266")
    name = Column(String, nullable=False)
    title = Column(String)
    blurb = Column(Text)
    lore = Column(Text)
    partype = Column(String)  # Resource type (mana, energy, etc.)
    version = Column(String, nullable=False)
    
    # Base stats
    hp = Column(Float)
    hp_per_level = Column(Float)
    mp = Column(Float)
    mp_per_level = Column(Float)
    move_speed = Column(Float)
    armor = Column(Float)
    armor_per_level = Column(Float)
    spell_block = Column(Float)
    spell_block_per_level = Column(Float)
    attack_range = Column(Float)
    attack_damage = Column(Float)
    attack_damage_per_level = Column(Float)
    attack_speed = Column(Float)
    attack_speed_per_level = Column(Float)
    
    # Difficulty ratings
    attack_rating = Column(Integer)
    defense_rating = Column(Integer)
    magic_rating = Column(Integer)
    difficulty_rating = Column(Integer)
    
    # Image data
    image_full = Column(String)
    image_sprite = Column(String)
    image_group = Column(String)
    
    # Game metadata
    ally_tips = Column(ARRAY(String))
    enemy_tips = Column(ARRAY(String))
    
    # Relationships
    tags = relationship("Tag", secondary=champion_tags, back_populates="champions")
    spells = relationship("Spell", back_populates="champion")
    passive = relationship("ChampionPassive", uselist=False, back_populates="champion")
    skins = relationship("ChampionSkin", back_populates="champion")
    
    # Indexing strategy
    __table_args__ = (
        Index('idx_champion_name', 'name'),
        Index('idx_champion_key', 'key'),
        Index('idx_champion_version', 'version'),
    )


class ChampionSkin(Base):
    """Champion skins"""
    __tablename__ = 'champion_skins'
    
    id = Column(Integer, primary_key=True)
    champion_id = Column(String, ForeignKey('champions.id'), nullable=False)
    skin_id = Column(String, nullable=False)
    skin_num = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    
    # Images
    image_loading = Column(String)  # Loading screen image
    image_splash = Column(String)   # Splash art image
    
    # Additional metadata
    chromas = Column(Boolean, default=False)
    
    # Relationships
    champion = relationship("Champion", back_populates="skins")
    
    # Unique constraint for champion_id + skin_num
    __table_args__ = (
        UniqueConstraint('champion_id', 'skin_num', name='uq_champion_skin'),
    )


class SpellType(enum.Enum):
    Q = "Q"
    W = "W"
    E = "E"
    R = "R"


class Spell(Base):
    """Champion abilities (Q, W, E, R)"""
    __tablename__ = 'spells'
    
    id = Column(String, primary_key=True)  # Spell ID
    champion_id = Column(String, ForeignKey('champions.id'), nullable=False)
    spell_type = Column(Enum(SpellType), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    tooltip = Column(Text)
    max_rank = Column(Integer)
    
    # Spell costs and cooldowns
    cooldown = Column(ARRAY(Float))
    cost = Column(ARRAY(Integer))
    cost_type = Column(String)
    range = Column(PG_ARRAY(BigInteger))
    
    # Image data
    image_full = Column(String)
    image_sprite = Column(String)
    image_group = Column(String)
    
    # Additional data
    effect = Column(JSON)  # Nested array of spell effects by level
    variables = Column(JSON)  # Coefficient data for calculations
    
    # Relationships
    champion = relationship("Champion", back_populates="spells")
    
    # Indexing strategy
    __table_args__ = (
        UniqueConstraint('champion_id', 'spell_type', name='uq_champion_spell'),
        Index('idx_spell_champion', 'champion_id'),
    )


class ChampionPassive(Base):
    """Champion passive abilities"""
    __tablename__ = 'champion_passives'
    
    id = Column(String, primary_key=True)  # Generated ID
    champion_id = Column(String, ForeignKey('champions.id'), nullable=False, unique=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    
    # Image data
    image_full = Column(String)
    image_sprite = Column(String)
    image_group = Column(String)
    
    # Relationships
    champion = relationship("Champion", back_populates="passive")


class Item(Base):
    """Game items"""
    __tablename__ = 'items'
    
    id = Column(String, primary_key=True)  # Item ID (e.g., "1001")
    name = Column(String, nullable=False)
    description = Column(Text)
    plain_text = Column(Text)
    version = Column(String, nullable=False)
    
    # Item details
    tier = Column(Integer)
    depth = Column(Integer)  # Recipe depth
    required_champion = Column(String, ForeignKey('champions.id'), nullable=True)
    required_ally = Column(String)
    
    # Economy
    base_gold = Column(Integer)
    total_gold = Column(Integer)
    sell_gold = Column(Integer)
    purchasable = Column(Boolean, default=True)
    
    # Stats provided by item
    stats = Column(JSON)
    
    # Special attributes
    consumed = Column(Boolean, default=False)
    consumable = Column(Boolean, default=False)
    in_store = Column(Boolean, default=True)
    hide_from_all = Column(Boolean, default=False)
    special_recipe = Column(Integer, nullable=True)
    
    # Maps availability
    maps = Column(JSON)  # JSON object with map IDs as keys
    
    # Image data
    image_full = Column(String)
    image_sprite = Column(String)
    image_group = Column(String)
    
    # Relationships
    tags = relationship("Tag", secondary=item_tags, back_populates="items")
    builds_into = relationship(
        "Item",
        secondary=item_recipes,
        primaryjoin=id==item_recipes.c.component_id,
        secondaryjoin=id==item_recipes.c.item_id,
        backref="built_from"
    )
    
    # Indexing strategy
    __table_args__ = (
        Index('idx_item_name', 'name'),
        Index('idx_item_version', 'version'),
        Index('idx_item_tier', 'tier'),
    )


class RunePath(Base):
    """Main rune paths (e.g., Domination, Precision)"""
    __tablename__ = 'rune_paths'
    
    id = Column(Integer, primary_key=True)  # Path ID (e.g., 8100)
    key = Column(String, nullable=False, unique=True)  # Path key (e.g., "Domination")
    name = Column(String, nullable=False)
    icon = Column(String)
    version = Column(String, nullable=False)
    
    # Relationships
    slots = relationship("RuneSlot", back_populates="path")
    
    # Indexing strategy
    __table_args__ = (
        Index('idx_rune_path_key', 'key'),
        Index('idx_rune_path_version', 'version'),
    )


class RuneSlot(Base):
    """Slots within a rune path (e.g., Keystone, row1, row2, etc.)"""
    __tablename__ = 'rune_slots'
    
    id = Column(Integer, primary_key=True)
    path_id = Column(Integer, ForeignKey('rune_paths.id'), nullable=False)
    slot_number = Column(Integer, nullable=False)  # Position in path (0 for keystone, etc.)
    
    # Relationships
    path = relationship("RunePath", back_populates="slots")
    runes = relationship("Rune", back_populates="slot")
    
    # Unique constraint
    __table_args__ = (
        UniqueConstraint('path_id', 'slot_number', name='uq_path_slot'),
    )


class Rune(Base):
    """Individual runes within slots"""
    __tablename__ = 'runes'
    
    id = Column(Integer, primary_key=True)  # Rune ID (e.g., 8112)
    slot_id = Column(Integer, ForeignKey('rune_slots.id'), nullable=False)
    key = Column(String, nullable=False, unique=True)  # Rune key (e.g., "Electrocute")
    name = Column(String, nullable=False)
    short_desc = Column(Text)
    long_desc = Column(Text)
    icon = Column(String)
    version = Column(String, nullable=False)
    
    # Relationships
    slot = relationship("RuneSlot", back_populates="runes")
    
    # Indexing strategy
    __table_args__ = (
        Index('idx_rune_key', 'key'),
        Index('idx_rune_slot', 'slot_id'),
        Index('idx_rune_version', 'version'),
    )


class SummonerSpell(Base):
    """Summoner spells (e.g., Flash, Ignite, etc.)"""
    __tablename__ = 'summoner_spells'
    
    id = Column(String, primary_key=True)  # Spell ID (e.g., "SummonerFlash")
    key = Column(String, nullable=False, unique=True)  # Numeric key (e.g., "4")
    name = Column(String, nullable=False)
    description = Column(Text)
    tooltip = Column(Text)
    max_rank = Column(Integer, default=1)
    cooldown = Column(ARRAY(Float))
    range = Column(PG_ARRAY(BigInteger))
    summoner_level = Column(Integer)
    version = Column(String, nullable=False)
    
    # Game modes where spell is available
    modes = Column(ARRAY(String))
    
    # Image data
    image_full = Column(String)
    image_sprite = Column(String)
    image_group = Column(String)
    
    # Indexing strategy
    __table_args__ = (
        Index('idx_summoner_spell_name', 'name'),
        Index('idx_summoner_spell_key', 'key'),
        Index('idx_summoner_spell_version', 'version'),
    )