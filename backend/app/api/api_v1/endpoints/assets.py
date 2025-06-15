from typing import Optional
import httpx
import logging
import os
import aiofiles
from pathlib import Path
from fastapi import APIRouter, HTTPException, Response, Depends
from fastapi.responses import RedirectResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db.session import get_db
from app.db.repositories.champion_repository import ChampionRepository
from app.db.repositories.item_repository import ItemRepository
from app.db.repositories.rune_repository import RuneRepository
from app.core.config import settings
from app.db.data_manager import DataDragonManager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["assets"])

# Constants
ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)  # Create assets directory if it doesn't exist

# Subdirectories for different asset types
CHAMPION_IMAGES_DIR = os.path.join(ASSETS_DIR, "champion/images")
CHAMPION_SPLASH_DIR = os.path.join(ASSETS_DIR, "champion/splash")
CHAMPION_PASSIVE_DIR = os.path.join(ASSETS_DIR, "champion/passive")
CHAMPION_SPELL_DIR = os.path.join(ASSETS_DIR, "champion/spell")
CHAMPION_LOADING_DIR = os.path.join(ASSETS_DIR, "champion/loading")
ITEM_IMAGES_DIR = os.path.join(ASSETS_DIR, "item/images")
RUNE_IMAGES_DIR = os.path.join(ASSETS_DIR, "rune/images")
SUMMONER_SPELL_DIR = os.path.join(ASSETS_DIR, "summoner_spell")
RANKED_EMBLEMS_DIR = os.path.join(ASSETS_DIR, "ranked/emblems")
RANKED_POSITIONS_DIR = os.path.join(ASSETS_DIR, "ranked/positions")
RANKED_TIERS_DIR = os.path.join(ASSETS_DIR, "ranked/tiers")

# Create all directories
for directory in [
    CHAMPION_IMAGES_DIR,
    CHAMPION_SPLASH_DIR,
    CHAMPION_PASSIVE_DIR,
    CHAMPION_SPELL_DIR,
    CHAMPION_LOADING_DIR,
    ITEM_IMAGES_DIR,
    RUNE_IMAGES_DIR,
    SUMMONER_SPELL_DIR,
    RANKED_EMBLEMS_DIR,
    RANKED_POSITIONS_DIR,
    RANKED_TIERS_DIR
]:
    os.makedirs(directory, exist_ok=True)

async def get_current_version(db: AsyncSession) -> str:
    """Get the current version from the database"""
    data_manager = DataDragonManager(db)
    try:
        # First try to get champions version
        version = await data_manager.get_current_db_version("champions")
        if not version:
            # If not available, get the latest version from Data Dragon
            version = await data_manager.get_latest_version()
        return version
    finally:
        await data_manager.close()


async def fetch_and_save_image(url: str, save_path: str) -> Optional[bytes]:
    """Fetch image from a URL, save it to disk, and return the bytes"""
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # Check if file already exists
        if os.path.exists(save_path):
            # Read from disk
            async with aiofiles.open(save_path, "rb") as f:
                return await f.read()
        
        # Fetch from URL
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            # Save to disk
            async with aiofiles.open(save_path, "wb") as f:
                await f.write(response.content)
                
            logger.info(f"Image saved to {save_path}")
            return response.content
    except Exception as e:
        logger.error(f"Error fetching/saving image from {url} to {save_path}: {str(e)}")
        return None


@router.get(
    "/champion/image/{champion_id}",
    summary="Get champion portrait image",
    description="Returns a champion's portrait image"
)
async def get_champion_portrait(
    champion_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a champion's portrait image.
    
    Args:
        champion_id: Champion ID (e.g., 'Aatrox')
        db: Database session
        
    Returns:
        Image content or redirect
    """
    try:
        # Get champion to verify it exists and get the image filename
        repo = ChampionRepository(db)
        champion = await repo.get_by_id(champion_id)
        
        if not champion:
            raise HTTPException(status_code=404, detail=f"Champion '{champion_id}' not found")
        
        # Use the image name from DB if available, otherwise default to champion ID
        image_filename = champion.image_full or f"{champion_id}.png"
        
        # Get current version
        version = await get_current_version(db)
        
        # Define local save path
        save_path = os.path.join(CHAMPION_IMAGES_DIR, f"{champion_id}.png")
        
        # Construct URL to Data Dragon
        url = f"{settings.DATA_DRAGON_CDN}/{version}/img/champion/{image_filename}"
        
        # Fetch and save the image
        image_data = await fetch_and_save_image(url, save_path)
        if image_data:
            return Response(content=image_data, media_type="image/png")
        else:
            # Try to serve the file if it exists (even if fetch failed)
            if os.path.exists(save_path):
                return FileResponse(save_path, media_type="image/png")
            # Fallback to redirect if can't fetch
            return RedirectResponse(url=url)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving champion portrait: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error serving image: {str(e)}")


@router.get(
    "/champion/splash/{champion_id}/{skin_num}",
    summary="Get champion splash art",
    description="Returns a champion's splash art for the specified skin"
)
async def get_champion_splash(
    champion_id: str,
    skin_num: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a champion's splash art.
    
    Args:
        champion_id: Champion ID (e.g., 'Aatrox')
        skin_num: Skin number (0 for default)
        db: Database session
        
    Returns:
        Image content or redirect
    """
    try:
        # Verify champion exists
        repo = ChampionRepository(db)
        champion = await repo.get_by_id(champion_id)
        
        if not champion:
            raise HTTPException(status_code=404, detail=f"Champion '{champion_id}' not found")
        
        # Define local save path
        save_path = os.path.join(CHAMPION_SPLASH_DIR, f"{champion_id}_{skin_num}.jpg")
        
        # Construct URL to Data Dragon
        url = f"{settings.DATA_DRAGON_BASE_URL}/cdn/img/champion/splash/{champion_id}_{skin_num}.jpg"
        
        # Fetch and save the image
        image_data = await fetch_and_save_image(url, save_path)
        if image_data:
            return Response(content=image_data, media_type="image/jpeg")
        else:
            # Try to serve the file if it exists (even if fetch failed)
            if os.path.exists(save_path):
                return FileResponse(save_path, media_type="image/jpeg")
            # Fallback to redirect if can't fetch
            return RedirectResponse(url=url)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving champion splash: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error serving image: {str(e)}")


@router.get(
    "/champion/loading/{champion_id}/{skin_num}",
    summary="Get champion loading screen image",
    description="Returns a champion's loading screen image for the specified skin"
)
async def get_champion_loading(
    champion_id: str,
    skin_num: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a champion's loading screen image.
    
    Args:
        champion_id: Champion ID (e.g., 'Aatrox')
        skin_num: Skin number (0 for default)
        db: Database session
        
    Returns:
        Image content or redirect
    """
    try:
        # Verify champion exists
        repo = ChampionRepository(db)
        champion = await repo.get_by_id(champion_id)
        
        if not champion:
            raise HTTPException(status_code=404, detail=f"Champion '{champion_id}' not found")
        
        # Construct URL to Data Dragon
        url = f"{settings.DATA_DRAGON_BASE_URL}/cdn/img/champion/loading/{champion_id}_{skin_num}.jpg"
        
        # Define local save path
        save_path = os.path.join(CHAMPION_LOADING_DIR, f"{champion_id}_{skin_num}.jpg")
        
        # Fetch and save the image
        image_data = await fetch_and_save_image(url, save_path)
        if image_data:
            return Response(content=image_data, media_type="image/jpeg")
        else:
            # Fallback to redirect if can't fetch
            return RedirectResponse(url=url)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving champion loading image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error serving image: {str(e)}")


@router.get(
    "/champion/passive/{champion_id}",
    summary="Get champion passive ability icon",
    description="Returns a champion's passive ability icon"
)
async def get_champion_passive(
    champion_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a champion's passive ability icon.
    
    Args:
        champion_id: Champion ID (e.g., 'Aatrox')
        db: Database session
        
    Returns:
        Image content or redirect
    """
    try:
        # Get champion to verify it exists and get its passive
        repo = ChampionRepository(db)
        champion = await repo.get_with_details(champion_id)
        
        if not champion or not champion.passive:
            raise HTTPException(status_code=404, detail=f"Champion '{champion_id}' or its passive not found")
        
        # Use the image name from DB if available
        image_filename = champion.passive.image_full
        if not image_filename:
            raise HTTPException(status_code=404, detail=f"Passive image for '{champion_id}' not found")
        
        # Get current version
        version = await get_current_version(db)
        
        # Define local save path
        save_path = os.path.join(CHAMPION_PASSIVE_DIR, image_filename)
        
        # Construct URL to Data Dragon
        url = f"{settings.DATA_DRAGON_CDN}/{version}/img/passive/{image_filename}"
        
        # Fetch and save the image
        image_data = await fetch_and_save_image(url, save_path)
        if image_data:
            return Response(content=image_data, media_type="image/png")
        else:
            # Try to serve the file if it exists (even if fetch failed)
            if os.path.exists(save_path):
                return FileResponse(save_path, media_type="image/png")
            # Fallback to redirect if can't fetch
            return RedirectResponse(url=url)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving champion passive: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error serving image: {str(e)}")


@router.get(
    "/champion/spell/{spell_id}",
    summary="Get champion spell icon",
    description="Returns a champion's spell icon"
)
async def get_champion_spell(
    spell_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a champion's spell icon.
    
    Args:
        spell_id: Spell ID
        db: Database session
        
    Returns:
        Image content or redirect
    """
    try:
        # Attempt to find the spell in the database
        query = text(f"SELECT image_full FROM spells WHERE id = '{spell_id}'")
        result = await db.execute(query)
        spell_row = result.fetchone()
        
        if not spell_row or not spell_row[0]:
            # Try using the spell ID directly as the image name
            image_filename = f"{spell_id}.png"
        else:
            image_filename = spell_row[0]
        
        # Get current version
        version = await get_current_version(db)
        
        # Define local save path
        save_path = os.path.join(CHAMPION_SPELL_DIR, image_filename)
        
        # Construct URL to Data Dragon
        url = f"{settings.DATA_DRAGON_CDN}/{version}/img/spell/{image_filename}"
        
        # Fetch and save the image
        image_data = await fetch_and_save_image(url, save_path)
        if image_data:
            return Response(content=image_data, media_type="image/png")
        else:
            # Try to serve the file if it exists (even if fetch failed)
            if os.path.exists(save_path):
                return FileResponse(save_path, media_type="image/png")
            # Fallback to redirect if can't fetch
            return RedirectResponse(url=url)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving champion spell: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error serving image: {str(e)}")


@router.get(
    "/item/image/{item_id}",
    summary="Get item icon",
    description="Returns an item's icon"
)
async def get_item_image(
    item_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get an item's icon.
    
    Args:
        item_id: Item ID
        db: Database session
        
    Returns:
        Image content or redirect
    """
    try:
        # Get item to verify it exists and get the image filename
        repo = ItemRepository(db)
        item = await repo.get_by_id(item_id)
        
        if not item:
            raise HTTPException(status_code=404, detail=f"Item '{item_id}' not found")
        
        # Use the image name from DB if available, otherwise default to item ID
        image_filename = item.image_full or f"{item_id}.png"
        
        # Get current version
        version = await get_current_version(db)
        
        # Define local save path
        save_path = os.path.join(ITEM_IMAGES_DIR, image_filename)
        
        # Construct URL to Data Dragon
        url = f"{settings.DATA_DRAGON_CDN}/{version}/img/item/{image_filename}"
        
        # Fetch and save the image
        image_data = await fetch_and_save_image(url, save_path)
        if image_data:
            return Response(content=image_data, media_type="image/png")
        else:
            # Try to serve the file if it exists (even if fetch failed)
            if os.path.exists(save_path):
                return FileResponse(save_path, media_type="image/png")
            # Fallback to redirect if can't fetch
            return RedirectResponse(url=url)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving item image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error serving image: {str(e)}")


@router.get(
    "/rune/image/{rune_id}",
    summary="Get rune icon",
    description="Returns a rune's icon"
)
async def get_rune_image(
    rune_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a rune's icon.
    
    Args:
        rune_id: Rune ID or key
        db: Database session
        
    Returns:
        Image content or redirect
    """
    try:
        # Create rune directory if it doesn't exist
        rune_dir = os.path.join(ASSETS_DIR, "rune", "images")
        os.makedirs(rune_dir, exist_ok=True)
        
        # Try to find the rune in the database - first check runes table
        query = text(f"SELECT icon FROM runes WHERE id = '{rune_id}' OR key = '{rune_id}'")
        result = await db.execute(query)
        rune_row = result.fetchone()
        
        icon_path = None
        if rune_row and rune_row[0]:
            icon_path = rune_row[0]
        else:
            # If not found in runes, check rune_paths table
            path_query = text(f"SELECT icon FROM rune_paths WHERE id = '{rune_id}' OR key = '{rune_id}'")
            path_result = await db.execute(path_query)
            path_row = path_result.fetchone()
            
            if path_row and path_row[0]:
                icon_path = path_row[0]
        
        if not icon_path:
            # Try to use the rune ID directly as the filename
            icon_filename = f"{rune_id}.png"
        else:
            # Extract filename from the icon path
            icon_filename = os.path.basename(icon_path)
            
        # Get current version
        version = await get_current_version(db)
        
        # Define local save path
        save_path = os.path.join(rune_dir, icon_filename)
        
        # Check if file already exists
        if os.path.exists(save_path):
            return FileResponse(save_path, media_type="image/png")
            
        # Check if we have a standard placeholder for this rune
        # Check for common rune path IDs and keystone runes
        standard_runes = {
            # Paths
            "Precision": (255, 185, 59),
            "Domination": (219, 58, 58),
            "Sorcery": (64, 146, 255),
            "Resolve": (56, 178, 99),
            "Inspiration": (65, 205, 204),
            
            # Common keystones
            "PressTheAttack": (255, 185, 59),
            "LethalTempo": (255, 185, 59), 
            "FleetFootwork": (255, 185, 59),
            "Conqueror": (255, 185, 59),
            "Electrocute": (219, 58, 58),
            "Predator": (219, 58, 58),
            "DarkHarvest": (219, 58, 58),
            "HailOfBlades": (219, 58, 58),
            "SummonAery": (64, 146, 255),
            "ArcaneComet": (64, 146, 255),
            "PhaseRush": (64, 146, 255),
            "GraspOfTheUndying": (56, 178, 99),
            "Aftershock": (56, 178, 99),
            "Guardian": (56, 178, 99),
            "GlacialAugment": (65, 205, 204),
            "UnsealedSpellbook": (65, 205, 204),
            "FirstStrike": (65, 205, 204)
        }
        
        # If we have a standard placeholder, generate it
        if rune_id in standard_runes:
            try:
                # Import PIL if available
                from PIL import Image, ImageDraw, ImageFont
                from io import BytesIO
                
                # Create a placeholder image
                color = standard_runes[rune_id]
                size = (128, 128)
                img = Image.new('RGB', size, color)
                draw = ImageDraw.Draw(img)
                
                # Add text (the rune ID)
                try:
                    font = ImageFont.truetype("DejaVuSans.ttf", 16)
                except IOError:
                    font = ImageFont.load_default()
                
                text = rune_id
                text_width, text_height = draw.textbbox((0, 0), text, font=font)[2:4]
                position = ((size[0] - text_width) // 2, (size[1] - text_height) // 2)
                draw.text(position, text, fill=(255, 255, 255), font=font)
                
                # Save to BytesIO
                img_bytes = BytesIO()
                img.save(img_bytes, format='PNG')
                img_bytes.seek(0)
                
                # Save to disk if possible
                try:
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
                    with open(save_path, 'wb') as f:
                        f.write(img_bytes.getvalue())
                    logger.info(f"Created placeholder: {icon_filename}")
                except Exception as e:
                    logger.warning(f"Couldn't save placeholder to disk: {e}")
                
                # Return the image even if we couldn't save it
                return Response(content=img_bytes.getvalue(), media_type="image/png")
            except ImportError:
                logger.warning("PIL not available, can't create placeholder")
        
        # Try different URL patterns for rune icons
        urls = [
            # Standard paths
            f"{settings.DATA_DRAGON_CDN}/{version}/img/{icon_path}" if icon_path else None,
            f"{settings.DATA_DRAGON_CDN}/{version}/img/perk-images/{icon_path}" if icon_path else None,
            
            # Direct filename paths
            f"{settings.DATA_DRAGON_CDN}/{version}/img/perk-images/{icon_filename}",
            f"{settings.DATA_DRAGON_CDN}/{version}/img/perk-images/Styles/{icon_filename}",
            
            # Base filename without version
            f"{settings.DATA_DRAGON_BASE_URL}/cdn/img/perk-images/{icon_filename}",
            
            # Try with subdirectories
            f"{settings.DATA_DRAGON_CDN}/{version}/img/perk-images/Styles/Domination/{icon_filename}",
            f"{settings.DATA_DRAGON_CDN}/{version}/img/perk-images/Styles/Precision/{icon_filename}",
            f"{settings.DATA_DRAGON_CDN}/{version}/img/perk-images/Styles/Sorcery/{icon_filename}",
            f"{settings.DATA_DRAGON_CDN}/{version}/img/perk-images/Styles/Resolve/{icon_filename}",
            f"{settings.DATA_DRAGON_CDN}/{version}/img/perk-images/Styles/Inspiration/{icon_filename}",
        ]
        
        # Filter out None values
        urls = [url for url in urls if url]
        
        # Try each URL until we find one that works
        image_data = None
        for url in urls:
            logger.debug(f"Trying URL: {url}")
            image_data = await fetch_and_save_image(url, save_path)
            if image_data:
                logger.info(f"Successfully fetched rune image from {url}")
                break
                
        if image_data:
            return Response(content=image_data, media_type="image/png")
        else:
            # Try to serve the file if it exists (even if fetch failed)
            if os.path.exists(save_path):
                return FileResponse(save_path, media_type="image/png")
            # Fallback to redirect if can't fetch
            logger.warning(f"Could not fetch rune image for {rune_id}, redirecting to {urls[0]}")
            return RedirectResponse(url=urls[0])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving rune image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error serving image: {str(e)}")


@router.get(
    "/summoner-spell/image/{spell_id}",
    summary="Get summoner spell icon",
    description="Returns a summoner spell's icon"
)
async def get_summoner_spell_image(
    spell_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a summoner spell's icon.
    
    Args:
        spell_id: Summoner spell ID (e.g., 'SummonerFlash') or key
        db: Database session
        
    Returns:
        Image content or redirect
    """
    try:
        # Try to find the spell in the database
        query = text(f"SELECT id, image_full FROM summoner_spells WHERE id = '{spell_id}' OR key = '{spell_id}'")
        result = await db.execute(query)
        spell_row = result.fetchone()
        
        if not spell_row or not spell_row[1]:
            # Try using the spell ID directly as the image name
            image_filename = f"{spell_id}.png"
        else:
            image_filename = spell_row[1]
        
        # Get current version
        version = await get_current_version(db)
        
        # Define local save path
        save_path = os.path.join(SUMMONER_SPELL_DIR, image_filename)
        
        # Check if file already exists
        if os.path.exists(save_path):
            return FileResponse(save_path, media_type="image/png")
        
        # Construct URL to Data Dragon
        url = f"{settings.DATA_DRAGON_CDN}/{version}/img/spell/{image_filename}"
        
        # Fetch and save the image
        image_data = await fetch_and_save_image(url, save_path)
        if image_data:
            return Response(content=image_data, media_type="image/png")
        else:
            # Try to serve the file if it exists (even if fetch failed)
            if os.path.exists(save_path):
                return FileResponse(save_path, media_type="image/png")
            # Fallback to redirect if can't fetch
            return RedirectResponse(url=url)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving summoner spell image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error serving image: {str(e)}")


@router.get(
    "/ranked/emblem/{rank}/{division}",
    summary="Get ranked emblem",
    description="Returns a ranked emblem image for the specified rank and division"
)
async def get_ranked_emblem(
    rank: str,
    division: str = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a ranked emblem image.
    
    Args:
        rank: Rank name (e.g., 'Iron', 'Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond', 'Master', 'Grandmaster', 'Challenger')
        division: Division number (I, II, III, IV) - not applicable for Master, Grandmaster, Challenger
        db: Database session
        
    Returns:
        Image content or 404
    """
    try:
        # Normalize rank name to match filename format (first letter capitalized)
        rank = rank.upper()
        
        # Determine filename based on rank and division
        if rank in ["MASTER", "GRANDMASTER", "CHALLENGER"]:
            # These ranks don't have divisions
            filename = f"Emblem_{rank.capitalize()}.png"
        else:
            # Validate division for ranks that have divisions
            if not division or division not in ["I", "II", "III", "IV"]:
                raise HTTPException(status_code=400, detail="Invalid division. Must be one of: I, II, III, IV")
            
            filename = f"Emblem_{rank.capitalize()}_{division}.png"
        
        # Define local save path
        save_path = os.path.join(RANKED_EMBLEMS_DIR, filename)
        
        # Check if file exists
        if os.path.exists(save_path):
            return FileResponse(save_path, media_type="image/png")
        
        # Construct URL to Community Dragon
        url = f"https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/content/src/leagueclient/rankedcrestnotification/{filename.lower()}"
        
        # Fetch and save the image
        image_data = await fetch_and_save_image(url, save_path)
        if image_data:
            return Response(content=image_data, media_type="image/png")
        else:
            # Generate a placeholder image
            try:
                # Define colors for different ranks
                rank_colors = {
                    "IRON": (90, 90, 90),       # Dark Gray
                    "BRONZE": (150, 90, 56),    # Bronze
                    "SILVER": (170, 170, 170),  # Silver
                    "GOLD": (218, 165, 32),     # Gold
                    "PLATINUM": (86, 186, 180), # Teal
                    "DIAMOND": (65, 170, 240),  # Light Blue
                    "MASTER": (170, 80, 227),   # Purple
                    "GRANDMASTER": (228, 65, 65), # Red
                    "CHALLENGER": (246, 223, 77)  # Yellow
                }
                
                # Import PIL if available
                from PIL import Image, ImageDraw, ImageFont
                from io import BytesIO
                
                # Create a placeholder image
                color = rank_colors.get(rank, (100, 100, 100))
                size = (128, 128)
                img = Image.new('RGB', size, color)
                draw = ImageDraw.Draw(img)
                
                # Add text (rank and division)
                try:
                    font = ImageFont.truetype("DejaVuSans.ttf", 16)
                except IOError:
                    font = ImageFont.load_default()
                
                text = rank
                if division and rank not in ["MASTER", "GRANDMASTER", "CHALLENGER"]:
                    text += f"\n{division}"
                
                # Calculate text position
                lines = text.split('\n')
                total_height = 0
                
                for line in lines:
                    text_width, text_height = draw.textbbox((0, 0), line, font=font)[2:4]
                    total_height += text_height + 5  # Add some padding
                
                # Draw each line of text
                y = (size[1] - total_height) // 2
                for line in lines:
                    text_width, text_height = draw.textbbox((0, 0), line, font=font)[2:4]
                    position = ((size[0] - text_width) // 2, y)
                    draw.text(position, line, fill=(255, 255, 255), font=font)
                    y += text_height + 5
                
                # Save to BytesIO
                img_bytes = BytesIO()
                img.save(img_bytes, format='PNG')
                img_bytes.seek(0)
                
                # Save to disk if possible
                try:
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
                    with open(save_path, 'wb') as f:
                        f.write(img_bytes.getvalue())
                    logger.info(f"Created placeholder: {filename}")
                except Exception as e:
                    logger.warning(f"Couldn't save placeholder to disk: {e}")
                
                # Return the image even if we couldn't save it
                return Response(content=img_bytes.getvalue(), media_type="image/png")
            except ImportError:
                logger.warning("PIL not available, can't create placeholder")
                raise HTTPException(status_code=404, detail=f"Ranked emblem for {rank} {division if division else ''} not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving ranked emblem: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error serving image: {str(e)}")


@router.get(
    "/ranked/tier/{rank}",
    summary="Get tier icon",
    description="Returns a tier icon for the specified rank"
)
async def get_tier_icon(
    rank: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a tier icon.
    
    Args:
        rank: Rank name (e.g., 'Iron', 'Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond', 'Master', 'Grandmaster', 'Challenger')
        db: Database session
        
    Returns:
        Image content or 404
    """
    try:
        # Normalize rank name to match filename format
        rank = rank.lower()
        
        # Validate rank
        valid_ranks = ["iron", "bronze", "silver", "gold", "platinum", "diamond", "master", "grandmaster", "challenger"]
        if rank not in valid_ranks:
            raise HTTPException(status_code=400, detail=f"Invalid rank. Must be one of: {', '.join(valid_ranks)}")
        
        # Determine filename
        filename = f"tier_icons_{rank}.png"
        
        # Define local save path
        save_path = os.path.join(RANKED_TIERS_DIR, filename)
        
        # Check if file exists
        if os.path.exists(save_path):
            return FileResponse(save_path, media_type="image/png")
        
        # Construct URL to Community Dragon
        url = f"https://raw.communitydragon.org/latest/plugins/rcp-fe-lol-shared-components/global/default/{filename}"
        
        # Fetch and save the image
        image_data = await fetch_and_save_image(url, save_path)
        if image_data:
            return Response(content=image_data, media_type="image/png")
        else:
            # Generate a placeholder image
            try:
                # Define colors for different ranks
                rank_colors = {
                    "iron": (90, 90, 90),       # Dark Gray
                    "bronze": (150, 90, 56),    # Bronze
                    "silver": (170, 170, 170),  # Silver
                    "gold": (218, 165, 32),     # Gold
                    "platinum": (86, 186, 180), # Teal
                    "diamond": (65, 170, 240),  # Light Blue
                    "master": (170, 80, 227),   # Purple
                    "grandmaster": (228, 65, 65), # Red
                    "challenger": (246, 223, 77)  # Yellow
                }
                
                # Import PIL if available
                from PIL import Image, ImageDraw, ImageFont
                from io import BytesIO
                
                # Create a placeholder image
                color = rank_colors.get(rank, (100, 100, 100))
                size = (128, 128)
                img = Image.new('RGB', size, color)
                draw = ImageDraw.Draw(img)
                
                # Add text (rank name)
                try:
                    font = ImageFont.truetype("DejaVuSans.ttf", 16)
                except IOError:
                    font = ImageFont.load_default()
                
                text = rank.upper()
                text_width, text_height = draw.textbbox((0, 0), text, font=font)[2:4]
                position = ((size[0] - text_width) // 2, (size[1] - text_height) // 2)
                draw.text(position, text, fill=(255, 255, 255), font=font)
                
                # Save to BytesIO
                img_bytes = BytesIO()
                img.save(img_bytes, format='PNG')
                img_bytes.seek(0)
                
                # Save to disk if possible
                try:
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
                    with open(save_path, 'wb') as f:
                        f.write(img_bytes.getvalue())
                    logger.info(f"Created placeholder: {filename}")
                except Exception as e:
                    logger.warning(f"Couldn't save placeholder to disk: {e}")
                
                # Return the image even if we couldn't save it
                return Response(content=img_bytes.getvalue(), media_type="image/png")
            except ImportError:
                logger.warning("PIL not available, can't create placeholder")
                raise HTTPException(status_code=404, detail=f"Tier icon for {rank} not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving tier icon: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error serving image: {str(e)}")


@router.get(
    "/ranked/position/{position}",
    summary="Get position icon",
    description="Returns a position icon for the specified role"
)
async def get_position_icon(
    position: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a position icon.
    
    Args:
        position: Position name (e.g., 'Top', 'Jungle', 'Middle', 'Bottom', 'Support')
        db: Database session
        
    Returns:
        Image content or 404
    """
    try:
        # Normalize position name to match filename format
        position = position.upper()
        
        # Validate position
        valid_positions = ["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "SUPPORT"]
        if position not in valid_positions:
            raise HTTPException(status_code=400, detail=f"Invalid position. Must be one of: {', '.join(valid_positions)}")
        
        # Try both filename formats
        filenames = [
            f"position_{position.lower()}.png",  # position_top.png
            f"position-{position.lower()}.png"   # position-top.png
        ]
        
        # Define local save paths
        save_paths = [os.path.join(RANKED_POSITIONS_DIR, filename) for filename in filenames]
        
        # Check if any file exists
        for save_path in save_paths:
            if os.path.exists(save_path):
                return FileResponse(save_path, media_type="image/png")
        
        # If no file exists, try to fetch them
        for i, filename in enumerate(filenames):
            # Construct URL to Community Dragon based on format
            url = None
            if i == 0:  # First format: position_top.png
                url = f"https://raw.communitydragon.org/latest/plugins/rcp-fe-lol-career-stats/global/default/images/position-selector/{filename}"
            else:  # Second format: position-top.png
                url = f"https://raw.communitydragon.org/latest/plugins/rcp-fe-lol-static-assets/global/default/images/ranked-positions/{filename}"
            
            # Fetch and save the image
            image_data = await fetch_and_save_image(url, save_paths[i])
            if image_data:
                return Response(content=image_data, media_type="image/png")
        
        # Generate a placeholder image
        try:
            # Define colors for different positions
            position_colors = {
                "TOP": (255, 100, 100),     # Red
                "JUNGLE": (100, 255, 100),  # Green
                "MIDDLE": (100, 100, 255),  # Blue
                "BOTTOM": (255, 255, 100),  # Yellow
                "SUPPORT": (255, 100, 255)  # Pink
            }
            
            # Import PIL if available
            from PIL import Image, ImageDraw, ImageFont
            from io import BytesIO
            
            # Create a placeholder image
            color = position_colors.get(position, (100, 100, 100))
            size = (128, 128)
            img = Image.new('RGB', size, color)
            draw = ImageDraw.Draw(img)
            
            # Add text (position name)
            try:
                font = ImageFont.truetype("DejaVuSans.ttf", 16)
            except IOError:
                font = ImageFont.load_default()
            
            text = position
            text_width, text_height = draw.textbbox((0, 0), text, font=font)[2:4]
            position_xy = ((size[0] - text_width) // 2, (size[1] - text_height) // 2)
            draw.text(position_xy, text, fill=(255, 255, 255), font=font)
            
            # Save to BytesIO
            img_bytes = BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            # Save to disk if possible
            try:
                os.makedirs(os.path.dirname(save_paths[0]), exist_ok=True)
                with open(save_paths[0], 'wb') as f:
                    f.write(img_bytes.getvalue())
                logger.info(f"Created placeholder: {filenames[0]}")
            except Exception as e:
                logger.warning(f"Couldn't save placeholder to disk: {e}")
            
            # Return the image even if we couldn't save it
            return Response(content=img_bytes.getvalue(), media_type="image/png")
        except ImportError:
            logger.warning("PIL not available, can't create placeholder")
            raise HTTPException(status_code=404, detail=f"Position icon for {position} not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving position icon: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error serving image: {str(e)}")


@router.get(
    "/version",
    summary="Get current game data version",
    description="Returns the current game data version used by the API"
)
async def get_version_info(db: AsyncSession = Depends(get_db)):
    """
    Get the current game data version.
    
    Returns:
        Current version information
    """
    try:
        data_manager = DataDragonManager(db)
        try:
            latest_version = await data_manager.get_latest_version()
            
            # Get versions for all entity types
            versions = {}
            for entity_type in ["champions", "items", "runes", "summoner-spells"]:
                versions[entity_type] = await data_manager.get_current_db_version(entity_type)
            
            return {
                "latest_version": latest_version,
                "current_versions": versions
            }
        finally:
            await data_manager.close()
    except Exception as e:
        logger.error(f"Error getting version info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting version info: {str(e)}")


@router.post(
    "/update_summoner_spells",
    summary="Update summoner spells",
    description="Updates summoner spells if they need updating"
)
async def update_summoner_spells(db: AsyncSession = Depends(get_db)):
    """
    Update summoner spells if needed.
    
    Returns:
        Update status
    """
    try:
        data_manager = DataDragonManager(db)
        try:
            latest_version = await data_manager.get_latest_version()
            current_version = await data_manager.get_current_db_version("summoner-spells")
            
            if current_version != latest_version:
                logger.info(f"Updating summoner spells from {current_version} to {latest_version}")
                await data_manager.update_summoner_spells(latest_version)
                await db.commit()
                return {"status": "updated", "from_version": current_version, "to_version": latest_version}
            else:
                return {"status": "no_update_needed", "version": current_version}
        finally:
            await data_manager.close()
    except Exception as e:
        logger.error(f"Error updating summoner spells: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating summoner spells: {str(e)}")