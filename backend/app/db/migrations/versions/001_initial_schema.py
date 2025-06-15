"""Initial database schema

Revision ID: 001
Revises: 
Create Date: 2025-06-07

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Game versions table
    op.create_table(
        'game_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('version', sa.String(), nullable=False),
        sa.Column('entity_type', sa.String(), nullable=False),
        sa.Column('is_current', sa.Boolean(), default=False),
        sa.Column('release_date', sa.String()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('version', 'entity_type', name='uq_version_entity')
    )
    op.create_index('idx_current_version', 'game_versions', ['entity_type', 'is_current'])
    
    # Tags table
    op.create_table(
        'tags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Champions table
    op.create_table(
        'champions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('title', sa.String()),
        sa.Column('blurb', sa.Text()),
        sa.Column('lore', sa.Text()),
        sa.Column('partype', sa.String()),
        sa.Column('version', sa.String(), nullable=False),
        sa.Column('hp', sa.Float()),
        sa.Column('hp_per_level', sa.Float()),
        sa.Column('mp', sa.Float()),
        sa.Column('mp_per_level', sa.Float()),
        sa.Column('move_speed', sa.Float()),
        sa.Column('armor', sa.Float()),
        sa.Column('armor_per_level', sa.Float()),
        sa.Column('spell_block', sa.Float()),
        sa.Column('spell_block_per_level', sa.Float()),
        sa.Column('attack_range', sa.Float()),
        sa.Column('attack_damage', sa.Float()),
        sa.Column('attack_damage_per_level', sa.Float()),
        sa.Column('attack_speed', sa.Float()),
        sa.Column('attack_speed_per_level', sa.Float()),
        sa.Column('attack_rating', sa.Integer()),
        sa.Column('defense_rating', sa.Integer()),
        sa.Column('magic_rating', sa.Integer()),
        sa.Column('difficulty_rating', sa.Integer()),
        sa.Column('image_full', sa.String()),
        sa.Column('image_sprite', sa.String()),
        sa.Column('image_group', sa.String()),
        sa.Column('ally_tips', sa.ARRAY(sa.String())),
        sa.Column('enemy_tips', sa.ARRAY(sa.String())),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key')
    )
    op.create_index('idx_champion_name', 'champions', ['name'])
    op.create_index('idx_champion_key', 'champions', ['key'])
    op.create_index('idx_champion_version', 'champions', ['version'])
    
    # Champion Tags association table
    op.create_table(
        'champion_tags',
        sa.Column('champion_id', sa.String(), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['champion_id'], ['champions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('champion_id', 'tag_id', name='uq_champion_tag')
    )
    
    # Champion Skins table
    op.create_table(
        'champion_skins',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('champion_id', sa.String(), nullable=False),
        sa.Column('skin_id', sa.String(), nullable=False),
        sa.Column('skin_num', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('image_loading', sa.String()),
        sa.Column('image_splash', sa.String()),
        sa.Column('chromas', sa.Boolean(), default=False),
        sa.ForeignKeyConstraint(['champion_id'], ['champions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('champion_id', 'skin_num', name='uq_champion_skin')
    )
    
    # Champion Passives table
    op.create_table(
        'champion_passives',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('champion_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('image_full', sa.String()),
        sa.Column('image_sprite', sa.String()),
        sa.Column('image_group', sa.String()),
        sa.ForeignKeyConstraint(['champion_id'], ['champions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('champion_id')
    )
    
    # Create enum type for spell types
    spell_type_enum = sa.Enum('Q', 'W', 'E', 'R', name='spelltype')
    spell_type_enum.create(op.get_bind())
    
    # Spells table
    op.create_table(
        'spells',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('champion_id', sa.String(), nullable=False),
        sa.Column('spell_type', spell_type_enum, nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('tooltip', sa.Text()),
        sa.Column('max_rank', sa.Integer()),
        sa.Column('cooldown', sa.ARRAY(sa.Float())),
        sa.Column('cost', sa.ARRAY(sa.Integer())),
        sa.Column('cost_type', sa.String()),
        sa.Column('range', sa.ARRAY(sa.Integer())),
        sa.Column('image_full', sa.String()),
        sa.Column('image_sprite', sa.String()),
        sa.Column('image_group', sa.String()),
        sa.Column('effect', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('variables', postgresql.JSON(astext_type=sa.Text())),
        sa.ForeignKeyConstraint(['champion_id'], ['champions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('champion_id', 'spell_type', name='uq_champion_spell')
    )
    op.create_index('idx_spell_champion', 'spells', ['champion_id'])
    
    # Items table
    op.create_table(
        'items',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('plain_text', sa.Text()),
        sa.Column('version', sa.String(), nullable=False),
        sa.Column('tier', sa.Integer()),
        sa.Column('depth', sa.Integer()),
        sa.Column('required_champion', sa.String()),
        sa.Column('required_ally', sa.String()),
        sa.Column('base_gold', sa.Integer()),
        sa.Column('total_gold', sa.Integer()),
        sa.Column('sell_gold', sa.Integer()),
        sa.Column('purchasable', sa.Boolean(), default=True),
        sa.Column('stats', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('consumed', sa.Boolean(), default=False),
        sa.Column('consumable', sa.Boolean(), default=False),
        sa.Column('in_store', sa.Boolean(), default=True),
        sa.Column('hide_from_all', sa.Boolean(), default=False),
        sa.Column('special_recipe', sa.Integer()),
        sa.Column('maps', postgresql.JSON(astext_type=sa.Text())),
        sa.Column('image_full', sa.String()),
        sa.Column('image_sprite', sa.String()),
        sa.Column('image_group', sa.String()),
        sa.ForeignKeyConstraint(['required_champion'], ['champions.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_item_name', 'items', ['name'])
    op.create_index('idx_item_version', 'items', ['version'])
    op.create_index('idx_item_tier', 'items', ['tier'])
    
    # Item Tags association table
    op.create_table(
        'item_tags',
        sa.Column('item_id', sa.String(), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['item_id'], ['items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('item_id', 'tag_id', name='uq_item_tag')
    )
    
    # Item Recipes association table
    op.create_table(
        'item_recipes',
        sa.Column('item_id', sa.String(), nullable=False),
        sa.Column('component_id', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['item_id'], ['items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['component_id'], ['items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('item_id', 'component_id')
    )
    
    # Rune Paths table
    op.create_table(
        'rune_paths',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('icon', sa.String()),
        sa.Column('version', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key')
    )
    op.create_index('idx_rune_path_key', 'rune_paths', ['key'])
    op.create_index('idx_rune_path_version', 'rune_paths', ['version'])
    
    # Rune Slots table
    op.create_table(
        'rune_slots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('path_id', sa.Integer(), nullable=False),
        sa.Column('slot_number', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['path_id'], ['rune_paths.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('path_id', 'slot_number', name='uq_path_slot')
    )
    
    # Runes table
    op.create_table(
        'runes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('slot_id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('short_desc', sa.Text()),
        sa.Column('long_desc', sa.Text()),
        sa.Column('icon', sa.String()),
        sa.Column('version', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['slot_id'], ['rune_slots.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key')
    )
    op.create_index('idx_rune_key', 'runes', ['key'])
    op.create_index('idx_rune_slot', 'runes', ['slot_id'])
    op.create_index('idx_rune_version', 'runes', ['version'])
    
    # Summoner Spells table
    op.create_table(
        'summoner_spells',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('tooltip', sa.Text()),
        sa.Column('max_rank', sa.Integer(), default=1),
        sa.Column('cooldown', sa.ARRAY(sa.Float())),
        sa.Column('range', sa.ARRAY(sa.Integer())),
        sa.Column('summoner_level', sa.Integer()),
        sa.Column('version', sa.String(), nullable=False),
        sa.Column('modes', sa.ARRAY(sa.String())),
        sa.Column('image_full', sa.String()),
        sa.Column('image_sprite', sa.String()),
        sa.Column('image_group', sa.String()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key')
    )
    op.create_index('idx_summoner_spell_name', 'summoner_spells', ['name'])
    op.create_index('idx_summoner_spell_key', 'summoner_spells', ['key'])
    op.create_index('idx_summoner_spell_version', 'summoner_spells', ['version'])


def downgrade() -> None:
    # Drop tables in reverse order to respect foreign key constraints
    op.drop_table('summoner_spells')
    op.drop_table('runes')
    op.drop_table('rune_slots')
    op.drop_table('rune_paths')
    op.drop_table('item_recipes')
    op.drop_table('item_tags')
    op.drop_table('items')
    op.drop_table('spells')
    
    # Drop enum type
    sa.Enum(name='spelltype').drop(op.get_bind())
    
    op.drop_table('champion_passives')
    op.drop_table('champion_skins')
    op.drop_table('champion_tags')
    op.drop_table('champions')
    op.drop_table('tags')
    op.drop_table('game_versions')