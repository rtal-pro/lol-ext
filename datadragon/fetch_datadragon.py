#!/usr/bin/env python3
"""
Script to fetch and save all League of Legends Data Dragon API endpoints to JSON files.
"""

import os
import json
import requests
import time
import argparse
from concurrent.futures import ThreadPoolExecutor

# Create output directory if it doesn't exist
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "api_responses")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Base URLs
CDN_BASE = "https://ddragon.leagueoflegends.com/cdn/"
API_BASE = "https://ddragon.leagueoflegends.com/api/"

def fetch_json(url, file_path):
    """Fetch JSON data from URL and save to file."""
    try:
        print(f"Fetching {url}...")
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Saved to {file_path}")
        return data
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def fetch_versions():
    """Fetch and save versions.json data."""
    url = f"{API_BASE}versions.json"
    file_path = os.path.join(OUTPUT_DIR, "versions.json")
    data = fetch_json(url, file_path)
    return data[0] if data else None  # Return latest version

def fetch_item_data(version):
    """Fetch and save item.json data."""
    url = f"{CDN_BASE}{version}/data/en_US/item.json"
    file_path = os.path.join(OUTPUT_DIR, f"items_{version}.json")
    fetch_json(url, file_path)

def fetch_champion_data(version):
    """Fetch and save champion.json data."""
    url = f"{CDN_BASE}{version}/data/en_US/champion.json"
    file_path = os.path.join(OUTPUT_DIR, f"champions_{version}.json")
    champions_data = fetch_json(url, file_path)
    return champions_data

def fetch_detailed_champion_data(version, champion_name):
    """Fetch and save detailed champion data."""
    url = f"{CDN_BASE}{version}/data/en_US/champion/{champion_name}.json"
    file_path = os.path.join(OUTPUT_DIR, f"champion_{champion_name}_{version}.json")
    fetch_json(url, file_path)

def fetch_runes_data(version):
    """Fetch and save runesReforged.json data."""
    url = f"{CDN_BASE}{version}/data/en_US/runesReforged.json"
    file_path = os.path.join(OUTPUT_DIR, f"runes_{version}.json")
    fetch_json(url, file_path)

def fetch_summoner_spells(version):
    """Fetch and save summoner.json data."""
    url = f"{CDN_BASE}{version}/data/en_US/summoner.json"
    file_path = os.path.join(OUTPUT_DIR, f"summoner_spells_{version}.json")
    fetch_json(url, file_path)

def fetch_profile_icons(version):
    """Fetch and save profileicon.json data."""
    url = f"{CDN_BASE}{version}/data/en_US/profileicon.json"
    file_path = os.path.join(OUTPUT_DIR, f"profile_icons_{version}.json")
    fetch_json(url, file_path)

def fetch_languages():
    """Fetch and save languages.json data."""
    url = f"{CDN_BASE}languages.json"
    file_path = os.path.join(OUTPUT_DIR, "languages.json")
    fetch_json(url, file_path)

def main():
    """Main function to fetch all data."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Fetch League of Legends Data Dragon API data')
    parser.add_argument('--version', type=str, help='Specific game version to use (e.g., "15.12.1")')
    parser.add_argument('--all-champions', action='store_true', help='Fetch detailed data for all champions')
    parser.add_argument('--champion', type=str, help='Fetch detailed data for a specific champion')
    parser.add_argument('--max-champions', type=int, default=10, help='Maximum number of champions to fetch detailed data for')
    args = parser.parse_args()
    
    # Fetch versions first to get latest version if not specified
    print("Starting to fetch Data Dragon API data...")
    
    if args.version:
        version_to_use = args.version
        print(f"Using specified version: {version_to_use}")
    else:
        latest_version = fetch_versions()
        if not latest_version:
            print("Failed to fetch versions. Exiting.")
            return
        version_to_use = latest_version
        print(f"Using latest version: {version_to_use}")
    
    # Fetch general data
    fetch_languages()
    fetch_item_data(version_to_use)
    fetch_runes_data(version_to_use)
    fetch_summoner_spells(version_to_use)
    fetch_profile_icons(version_to_use)
    
    # Handle champion data fetching based on arguments
    if args.champion:
        # Fetch detailed data for a specific champion
        print(f"Fetching detailed data for champion: {args.champion}")
        fetch_detailed_champion_data(version_to_use, args.champion)
    else:
        # Fetch basic champion data
        champions_data = fetch_champion_data(version_to_use)
        
        if champions_data and 'data' in champions_data:
            champion_names = list(champions_data['data'].keys())
            
            # Determine how many champions to fetch detailed data for
            if args.all_champions:
                champions_to_fetch = champion_names
                print(f"Fetching detailed data for all {len(champions_to_fetch)} champions...")
            else:
                max_champions = min(args.max_champions, len(champion_names))
                champions_to_fetch = champion_names[:max_champions]
                print(f"Fetching detailed data for {len(champions_to_fetch)} champions...")
            
            # Use ThreadPoolExecutor to fetch champion data in parallel
            # Limit to 5 workers to avoid overwhelming the API
            with ThreadPoolExecutor(max_workers=5) as executor:
                for champion_name in champions_to_fetch:
                    executor.submit(fetch_detailed_champion_data, version_to_use, champion_name)
                    # Sleep briefly to avoid rate limiting
                    time.sleep(0.2)
    
    print("All data fetched successfully!")

if __name__ == "__main__":
    main()