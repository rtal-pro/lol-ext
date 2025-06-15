from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, ConfigDict

from app.api.api_v1.schemas.base import PaginatedResponse


class RuneDetail(BaseModel):
    """Detailed rune information"""
    id: int = Field(..., description="Rune ID")
    key: str = Field(..., description="Rune key")
    name: str = Field(..., description="Rune name")
    short_desc: str = Field(..., description="Short description", alias="shortDesc")
    long_desc: str = Field(..., description="Long description", alias="longDesc")
    icon: str = Field(..., description="Rune icon path")
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    
    @classmethod
    def from_orm(cls, rune):
        """Create from ORM model"""
        return cls(
            id=rune.id,
            key=rune.key,
            name=rune.name,
            shortDesc=rune.short_desc,
            longDesc=rune.long_desc,
            icon=rune.icon
        )


class RuneSlot(BaseModel):
    """Rune slot in a path"""
    slot_number: int = Field(..., description="Slot position (0 for keystone)", alias="slotNumber")
    runes: List[RuneDetail] = Field(..., description="Runes in this slot")
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
    
    @classmethod
    def from_orm(cls, slot):
        """Create from ORM model with sorted runes"""
        return cls(
            slotNumber=slot.slot_number,
            runes=[RuneDetail.from_orm(rune) for rune in slot.runes]
        )


class RunePath(BaseModel):
    """Complete rune path"""
    id: int = Field(..., description="Path ID")
    key: str = Field(..., description="Path key")
    name: str = Field(..., description="Path name")
    icon: str = Field(..., description="Path icon")
    slots: List[RuneSlot] = Field(..., description="Slots in this path")
    
    model_config = ConfigDict(from_attributes=True)
    
    @classmethod
    def from_orm(cls, path_data):
        """Create from repository data"""
        path = path_data["path"]
        slots = path_data["slots"]
        
        return cls(
            id=path.id,
            key=path.key,
            name=path.name,
            icon=path.icon,
            slots=[RuneSlot.from_orm(slot) for slot in slots]
        )


class RuneTreeResponse(BaseModel):
    """Complete rune tree response"""
    paths: List[RunePath] = Field(..., description="All rune paths")
    version: str = Field(..., description="Data version")