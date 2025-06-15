import asyncio
import json
from app.services.data_dragon_service import DataDragonService

async def test_data_dragon_service():
    """Test the DataDragonService class with actual API calls"""
    
    # Initialize service
    service = DataDragonService()
    
    try:
        # Test get_latest_version
        print("Testing get_latest_version()...")
        version = await service.get_latest_version()
        print(f"Latest version: {version}")
        print()
        
        # Test fetch_champions_data
        print("Testing fetch_champions_data()...")
        champions = await service.fetch_champions_data(version)
        print(f"Fetched {len(champions)} champions")
        # Print first champion as an example
        first_champion = next(iter(champions.values()))
        print(f"Sample champion: {first_champion.name} ({first_champion.id})")
        print()
        
        # Test fetch_champion_detail
        print("Testing fetch_champion_detail()...")
        champion_detail = await service.fetch_champion_detail("Aatrox", version)
        print(f"Champion detail: {champion_detail.name}")
        print(f"Lore: {champion_detail.lore[:100]}...")
        print(f"Spells: {[spell.name for spell in champion_detail.spells]}")
        print()
        
        # Test fetch_items_data
        print("Testing fetch_items_data()...")
        items = await service.fetch_items_data(version)
        print(f"Fetched {len(items)} items")
        # Print first item as an example
        first_item = next(iter(items.values()))
        print(f"Sample item: {first_item.name}")
        print()
        
        # Test fetch_runes_data
        print("Testing fetch_runes_data()...")
        rune_paths = await service.fetch_runes_data(version)
        print(f"Fetched {len(rune_paths)} rune paths")
        # Print first rune path as an example
        first_path = rune_paths[0]
        print(f"Sample rune path: {first_path.name}")
        print(f"First rune in path: {first_path.slots[0].runes[0]['name']}")
        print()
        
        # Test URL helpers
        print("Testing URL helper methods...")
        print(f"Champion icon URL: {service.get_champion_icon_url('Aatrox', version)}")
        print(f"Champion splash URL: {service.get_champion_splash_url('Aatrox', 0)}")
        print(f"Champion loading URL: {service.get_champion_loading_url('Aatrox', 0)}")
        print(f"Item icon URL: {service.get_item_icon_url('1001', version)}")
        
        print("\nAll tests completed successfully!")
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
    finally:
        # Close the HTTP client
        await service.close()

if __name__ == "__main__":
    asyncio.run(test_data_dragon_service())