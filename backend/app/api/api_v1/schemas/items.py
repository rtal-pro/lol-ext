from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, ConfigDict

from app.api.api_v1.schemas.base import PaginatedResponse
from app.api.api_v1.schemas.champions import ImageData


class ItemStats(BaseModel):
    """Item stats"""
    model_config = ConfigDict(extra="allow")


class ItemGold(BaseModel):
    """Item gold information"""
    base: int = Field(..., description="Base cost")
    total: int = Field(..., description="Total cost")
    sell: int = Field(..., description="Sell value")
    purchasable: bool = Field(..., description="Can be purchased")
    
    model_config = ConfigDict(from_attributes=True)
    
    @classmethod
    def from_orm(cls, item):
        """Create from ORM model"""
        return cls(
            base=item.base_gold or 0,
            total=item.total_gold or 0,
            sell=item.sell_gold or 0,
            purchasable=item.purchasable
        )


class ItemSummary(BaseModel):
    """Summary information for an item"""
    id: str = Field(..., description="Item ID")
    name: str = Field(..., description="Item name")
    description: str = Field(..., description="Item description")
    plain_text: Optional[str] = Field(None, description="Plain text description", alias="plaintext")
    tier: Optional[int] = Field(None, description="Item tier")
    image: ImageData = Field(..., description="Item image data")
    gold: ItemGold = Field(..., description="Item gold information")
    tags: List[str] = Field(..., description="Item tags")
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    
    @classmethod
    def from_orm(cls, item):
        """Create from ORM model with computed values"""
        return cls(
            id=item.id,
            name=item.name,
            description=item.description,
            plaintext=item.plain_text,
            tier=item.tier,
            image=ImageData(
                full=item.image_full,
                sprite=item.image_sprite,
                group=item.image_group,
                x=None,
                y=None,
                w=None,
                h=None
            ),
            gold=ItemGold.from_orm(item),
            tags=[tag.name for tag in item.tags]
        )


class ItemListByTier(BaseModel):
    """Items grouped by tier"""
    tier: int = Field(..., description="Item tier")
    items: List[ItemSummary] = Field(..., description="Items in this tier")


class ItemListResponse(BaseModel):
    """Response for item list"""
    tiers: List[ItemListByTier] = Field(..., description="Items grouped by tier")
    total: int = Field(..., description="Total number of items")


class RecipeItem(BaseModel):
    """Item in a recipe"""
    id: str = Field(..., description="Item ID")
    name: str = Field(..., description="Item name")
    description: str = Field(..., description="Item description")
    tier: Optional[int] = Field(None, description="Item tier")
    gold: ItemGold = Field(..., description="Item gold information")
    image: ImageData = Field(..., description="Item image data")
    
    model_config = ConfigDict(from_attributes=True)
    
    @classmethod
    def from_orm(cls, item):
        """Create from ORM model with computed values"""
        return cls(
            id=item.id,
            name=item.name,
            description=item.description,
            tier=item.tier,
            gold=ItemGold.from_orm(item),
            image=ImageData(
                full=item.image_full,
                sprite=item.image_sprite,
                group=item.image_group,
                x=None,
                y=None,
                w=None,
                h=None
            )
        )


class ItemDetail(BaseModel):
    """Detailed item information"""
    id: str = Field(..., description="Item ID")
    name: str = Field(..., description="Item name")
    description: str = Field(..., description="Item description")
    plain_text: Optional[str] = Field(None, description="Plain text description", alias="plaintext")
    tier: Optional[int] = Field(None, description="Item tier")
    image: ImageData = Field(..., description="Item image data")
    gold: ItemGold = Field(..., description="Item gold information")
    tags: List[str] = Field(..., description="Item tags")
    stats: Dict[str, Any] = Field(..., description="Item stats")
    maps: Dict[str, bool] = Field(..., description="Maps where item is available")
    depth: Optional[int] = Field(None, description="Item recipe depth")
    consumed: Optional[bool] = Field(None, description="Item is consumed on use")
    consumable: Optional[bool] = Field(None, description="Item is consumable")
    hide_from_all: Optional[bool] = Field(None, description="Item is hidden", alias="hideFromAll")
    in_store: Optional[bool] = Field(None, description="Item is available in store", alias="inStore")
    required_champion: Optional[str] = Field(None, description="Required champion", alias="requiredChampion")
    required_ally: Optional[str] = Field(None, description="Required ally", alias="requiredAlly")
    builds_from: List[RecipeItem] = Field([], description="Components used to build this item", alias="buildsFrom")
    builds_into: List[RecipeItem] = Field([], description="Items this builds into", alias="buildsInto")
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    
    @classmethod
    def from_orm(cls, item):
        """Create from ORM model with computed values"""
        builds_from = [RecipeItem.from_orm(component) for component in item.built_from]
        builds_into = [RecipeItem.from_orm(component) for component in item.builds_into]
        
        return cls(
            id=item.id,
            name=item.name,
            description=item.description,
            plaintext=item.plain_text,
            tier=item.tier,
            image=ImageData(
                full=item.image_full,
                sprite=item.image_sprite,
                group=item.image_group,
                x=None,
                y=None,
                w=None,
                h=None
            ),
            gold=ItemGold.from_orm(item),
            tags=[tag.name for tag in item.tags],
            stats=item.stats or {},
            maps=item.maps or {},
            depth=item.depth,
            consumed=item.consumed,
            consumable=item.consumable,
            hideFromAll=item.hide_from_all,
            inStore=item.in_store,
            requiredChampion=item.required_champion,
            requiredAlly=item.required_ally,
            buildsFrom=builds_from,
            buildsInto=builds_into
        )