import httpx
import json
import logging
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, ValidationError, Field, validator
from functools import wraps

# Set up logging
logger = logging.getLogger(__name__)


# Pydantic models for data validation
class ImageData(BaseModel):
    full: str = ""
    sprite: str = ""
    group: str = ""
    x: Optional[int] = None
    y: Optional[int] = None
    w: Optional[int] = None
    h: Optional[int] = None


class ChampionInfo(BaseModel):
    attack: int
    defense: int
    magic: int
    difficulty: int


class ChampionStats(BaseModel):
    hp: float
    hpperlevel: float
    mp: float
    mpperlevel: float
    movespeed: float
    armor: float
    armorperlevel: float
    spellblock: float
    spellblockperlevel: float
    attackrange: float
    hpregen: float
    hpregenperlevel: float
    mpregen: float
    mpregenperlevel: float
    crit: float
    critperlevel: float
    attackdamage: float
    attackdamageperlevel: float
    attackspeedperlevel: float
    attackspeed: float


class ChampionSummary(BaseModel):
    version: str
    id: str
    key: str
    name: str
    title: str
    blurb: str
    info: ChampionInfo
    image: ImageData
    tags: List[str]
    partype: str
    stats: ChampionStats


class ChampionSpellData(BaseModel):
    id: str
    name: str
    description: str
    tooltip: str
    maxrank: int
    cooldown: List[float]
    cost: List[int]
    datavalues: Dict = Field(default_factory=dict)
    effect: Optional[List[Optional[List[float]]]] = None
    effectBurn: Optional[List[Optional[str]]] = None
    vars: List[Dict] = Field(default_factory=list)
    costType: str
    maxammo: Optional[str] = None
    range: List[int]
    rangeBurn: str
    image: ImageData
    resource: Optional[str] = None


class ChampionPassiveData(BaseModel):
    name: str
    description: str
    image: ImageData


class ChampionSkinData(BaseModel):
    id: str
    num: int
    name: str
    chromas: bool


class ChampionDetail(ChampionSummary):
    lore: str
    allytips: List[str] = Field(default_factory=list)
    enemytips: List[str] = Field(default_factory=list)
    spells: List[ChampionSpellData]
    passive: ChampionPassiveData
    skins: List[ChampionSkinData] = Field(default_factory=list)
    recommended: List[Dict] = Field(default_factory=list)


class ItemGold(BaseModel):
    base: int
    purchasable: bool
    total: int
    sell: int


class Item(BaseModel):
    name: str
    description: str
    colloq: str = ""
    plaintext: str = ""
    from_: Optional[List[str]] = Field(default_factory=list, alias="from")
    into: Optional[List[str]] = Field(default_factory=list)
    image: ImageData
    gold: ItemGold
    tags: List[str] = Field(default_factory=list)
    maps: Dict[str, bool] = Field(default_factory=dict)
    stats: Dict[str, float] = Field(default_factory=dict)
    depth: Optional[int] = None
    consumed: Optional[bool] = None
    consumeOnFull: Optional[bool] = None
    inStore: Optional[bool] = True
    hideFromAll: Optional[bool] = None
    requiredChampion: Optional[str] = None
    requiredAlly: Optional[str] = None
    specialRecipe: Optional[int] = None

    class Config:
        populate_by_name = True  # Support field alias "from_" for "from"


class RuneSlot(BaseModel):
    runes: List[Dict[str, Any]]


class RunePath(BaseModel):
    id: int
    key: str
    icon: str
    name: str
    slots: List[RuneSlot]


def handle_errors(func):
    """Decorator to handle common HTTP and parsing errors"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
            raise DataDragonServiceError(f"HTTP error: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error(f"Request error occurred: {str(e)}")
            raise DataDragonServiceError(f"Request error: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            raise DataDragonServiceError(f"JSON parsing error: {str(e)}")
        except ValidationError as e:
            logger.error(f"Data validation error: {str(e)}")
            raise DataDragonServiceError(f"Data validation error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise DataDragonServiceError(f"Unexpected error: {str(e)}")
    return wrapper


class DataDragonServiceError(Exception):
    """Exception raised for errors in the DataDragonService"""
    pass


class DataDragonService:
    """
    Service for fetching and processing data from Riot's Data Dragon API.
    
    This service provides methods to retrieve game data such as champions,
    items, runes, and other game assets from the Data Dragon CDN.
    
    It handles:
    - Fetching the latest game version
    - Retrieving champion data (summary and detailed)
    - Fetching item information
    - Getting runes data
    - Error handling and data validation
    """
    
    BASE_URL = "https://ddragon.leagueoflegends.com"
    CDN_URL = f"{BASE_URL}/cdn"
    API_URL = f"{BASE_URL}/api"
    
    def __init__(self, language: str = "en_US", timeout: float = 30.0):
        """
        Initialize the Data Dragon service
        
        Args:
            language: Language code for data (default: "en_US")
            timeout: HTTP timeout in seconds (default: 30.0)
        """
        self.language = language
        self.http_client = httpx.AsyncClient(timeout=timeout)
        self._latest_version = None
    
    async def close(self):
        """Close HTTP client when done"""
        await self.http_client.aclose()
    
    @handle_errors
    async def get_latest_version(self) -> str:
        """
        Get the latest available Data Dragon version
        
        Returns:
            str: Latest version string (e.g., "15.11.1")
        
        Raises:
            DataDragonServiceError: If there's an error fetching or parsing the version
        """
        if self._latest_version:
            return self._latest_version
            
        response = await self.http_client.get(f"{self.API_URL}/versions.json")
        response.raise_for_status()
        versions = response.json()
        
        if not versions or not isinstance(versions, list):
            raise DataDragonServiceError("Invalid version data format")
            
        self._latest_version = versions[0]
        return self._latest_version
    
    @handle_errors
    async def fetch_champions_data(self, version: Optional[str] = None) -> Dict[str, ChampionSummary]:
        """
        Fetch summary data for all champions
        
        Args:
            version: Game data version (default: latest version)
            
        Returns:
            Dict[str, ChampionSummary]: Dictionary of champions by ID
            
        Raises:
            DataDragonServiceError: If there's an error fetching or parsing champion data
        """
        if not version:
            version = await self.get_latest_version()
            
        url = f"{self.CDN_URL}/{version}/data/{self.language}/champion.json"
        response = await self.http_client.get(url)
        response.raise_for_status()
        data = response.json()
        
        champions = {}
        for champion_id, champion_data in data.get("data", {}).items():
            try:
                champions[champion_id] = ChampionSummary(**champion_data)
            except ValidationError as e:
                logger.warning(f"Validation error for champion {champion_id}: {str(e)}")
                # Still include the champion but with raw data
                champions[champion_id] = champion_data
                
        return champions
    
    @handle_errors
    async def fetch_champion_detail(self, champion_id: str, version: Optional[str] = None) -> ChampionDetail:
        """
        Fetch detailed data for a specific champion
        
        Args:
            champion_id: Champion identifier (e.g., "Aatrox")
            version: Game data version (default: latest version)
            
        Returns:
            ChampionDetail: Detailed champion data
            
        Raises:
            DataDragonServiceError: If there's an error fetching or parsing champion data
        """
        if not version:
            version = await self.get_latest_version()
            
        url = f"{self.CDN_URL}/{version}/data/{self.language}/champion/{champion_id}.json"
        response = await self.http_client.get(url)
        response.raise_for_status()
        data = response.json()
        
        champion_data = data.get("data", {}).get(champion_id)
        if not champion_data:
            raise DataDragonServiceError(f"Champion {champion_id} not found")
            
        return ChampionDetail(**champion_data)
    
    @handle_errors
    async def fetch_items_data(self, version: Optional[str] = None) -> Dict[str, Item]:
        """
        Fetch data for all items
        
        Args:
            version: Game data version (default: latest version)
            
        Returns:
            Dict[str, Item]: Dictionary of items by ID
            
        Raises:
            DataDragonServiceError: If there's an error fetching or parsing item data
        """
        if not version:
            version = await self.get_latest_version()
            
        url = f"{self.CDN_URL}/{version}/data/{self.language}/item.json"
        response = await self.http_client.get(url)
        response.raise_for_status()
        data = response.json()
        
        items = {}
        for item_id, item_data in data.get("data", {}).items():
            try:
                items[item_id] = Item(**item_data)
            except ValidationError as e:
                logger.warning(f"Validation error for item {item_id}: {str(e)}")
                # Still include the item but with raw data
                items[item_id] = item_data
                
        return items
    
    @handle_errors
    async def fetch_runes_data(self, version: Optional[str] = None) -> List[RunePath]:
        """
        Fetch data for all rune paths and runes
        
        Args:
            version: Game data version (default: latest version)
            
        Returns:
            List[RunePath]: List of rune paths with their runes
            
        Raises:
            DataDragonServiceError: If there's an error fetching or parsing rune data
        """
        if not version:
            version = await self.get_latest_version()
            
        url = f"{self.CDN_URL}/{version}/data/{self.language}/runesReforged.json"
        response = await self.http_client.get(url)
        response.raise_for_status()
        data = response.json()
        
        rune_paths = []
        for path_data in data:
            try:
                rune_paths.append(RunePath(**path_data))
            except ValidationError as e:
                logger.warning(f"Validation error for rune path {path_data.get('id')}: {str(e)}")
                # Still include the path but with raw data
                rune_paths.append(path_data)
                
        return rune_paths
    
    def get_champion_icon_url(self, champion_name: str, version: Optional[str] = None) -> str:
        """
        Get the URL for a champion's square icon
        
        Args:
            champion_name: Champion name (e.g., "Aatrox")
            version: Game data version (default: latest version)
            
        Returns:
            str: URL to the champion's square icon
        """
        if not version:
            # Use latest version if we have it cached, otherwise use a placeholder
            version = self._latest_version or "latest"
            
        return f"{self.CDN_URL}/{version}/img/champion/{champion_name}.png"
    
    def get_champion_splash_url(self, champion_name: str, skin_num: int = 0) -> str:
        """
        Get the URL for a champion's splash art
        
        Args:
            champion_name: Champion name (e.g., "Aatrox")
            skin_num: Skin number (default: 0 for base skin)
            
        Returns:
            str: URL to the champion's splash art
        """
        return f"{self.CDN_URL}/img/champion/splash/{champion_name}_{skin_num}.jpg"
    
    def get_champion_loading_url(self, champion_name: str, skin_num: int = 0) -> str:
        """
        Get the URL for a champion's loading screen image
        
        Args:
            champion_name: Champion name (e.g., "Aatrox")
            skin_num: Skin number (default: 0 for base skin)
            
        Returns:
            str: URL to the champion's loading screen image
        """
        return f"{self.CDN_URL}/img/champion/loading/{champion_name}_{skin_num}.jpg"
    
    def get_spell_icon_url(self, spell_id: str, version: Optional[str] = None) -> str:
        """
        Get the URL for a spell icon
        
        Args:
            spell_id: Spell identifier
            version: Game data version (default: latest version)
            
        Returns:
            str: URL to the spell icon
        """
        if not version:
            version = self._latest_version or "latest"
            
        return f"{self.CDN_URL}/{version}/img/spell/{spell_id}.png"
    
    def get_passive_icon_url(self, passive_id: str, version: Optional[str] = None) -> str:
        """
        Get the URL for a passive ability icon
        
        Args:
            passive_id: Passive identifier
            version: Game data version (default: latest version)
            
        Returns:
            str: URL to the passive ability icon
        """
        if not version:
            version = self._latest_version or "latest"
            
        return f"{self.CDN_URL}/{version}/img/passive/{passive_id}.png"
    
    def get_item_icon_url(self, item_id: str, version: Optional[str] = None) -> str:
        """
        Get the URL for an item icon
        
        Args:
            item_id: Item identifier
            version: Game data version (default: latest version)
            
        Returns:
            str: URL to the item icon
        """
        if not version:
            version = self._latest_version or "latest"
            
        return f"{self.CDN_URL}/{version}/img/item/{item_id}.png"