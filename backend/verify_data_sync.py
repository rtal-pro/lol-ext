#!/usr/bin/env python3
"""
Script to verify that all Data Dragon data is properly synchronized in the database.
This script checks that each champion, item, and rune in the local Data Dragon files
exists in the database with complete and accurate data.
"""

import asyncio
import json
import os
from pathlib import Path
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Any, Tuple, Set
import time

# Database connection parameters - when running in Docker container
DB_PARAMS = {
    'dbname': 'lol_extension',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'db',  # Use the Docker service name
    'port': 5432   # Default PostgreSQL port inside container
}

# Paths to API response files
API_RESPONSES_DIR = Path(__file__).parent / "api_responses"
CHAMPIONS_FILE = API_RESPONSES_DIR / "champions_15.12.1.json"
ITEMS_FILE = API_RESPONSES_DIR / "items_15.12.1.json"
RUNES_FILE = API_RESPONSES_DIR / "runes_15.12.1.json"
INDIVIDUAL_CHAMPIONS_DIR = API_RESPONSES_DIR / "individual_champions"
INDIVIDUAL_ITEMS_DIR = API_RESPONSES_DIR / "individual_items"

# Report structure
class SyncReport:
    def __init__(self):
        self.champions_total = 0
        self.champions_synced = 0
        self.champions_missing = []
        self.champions_incomplete = []
        
        self.items_total = 0
        self.items_synced = 0
        self.items_missing = []
        self.items_incomplete = []
        
        self.runes_total = 0
        self.runes_synced = 0
        self.runes_missing = []
        self.runes_incomplete = []
        
        self.start_time = time.time()
        self.end_time = None
    
    def finish(self):
        self.end_time = time.time()
    
    def get_duration(self):
        if self.end_time:
            return self.end_time - self.start_time
        return time.time() - self.start_time
    
    def champions_sync_rate(self):
        if self.champions_total == 0:
            return 0
        return (self.champions_synced / self.champions_total) * 100
    
    def items_sync_rate(self):
        if self.items_total == 0:
            return 0
        return (self.items_synced / self.items_total) * 100
    
    def runes_sync_rate(self):
        if self.runes_total == 0:
            return 0
        return (self.runes_synced / self.runes_total) * 100
    
    def overall_sync_rate(self):
        total = self.champions_total + self.items_total + self.runes_total
        if total == 0:
            return 0
        synced = self.champions_synced + self.items_synced + self.runes_synced
        return (synced / total) * 100
    
    def print_report(self):
        print("\n" + "=" * 80)
        print(f"DATA SYNC VERIFICATION REPORT")
        print("=" * 80)
        print(f"Duration: {self.get_duration():.2f} seconds")
        print("\n" + "-" * 80)
        
        print(f"CHAMPIONS: {self.champions_synced}/{self.champions_total} synced ({self.champions_sync_rate():.2f}%)")
        if self.champions_missing:
            print(f"  Missing champions ({len(self.champions_missing)}):")
            for champion in self.champions_missing[:10]:  # Show first 10
                print(f"    - {champion}")
            if len(self.champions_missing) > 10:
                print(f"    ... and {len(self.champions_missing) - 10} more")
        
        if self.champions_incomplete:
            print(f"  Incomplete champions ({len(self.champions_incomplete)}):")
            for champion, fields in self.champions_incomplete[:10]:  # Show first 10
                print(f"    - {champion}: missing {', '.join(fields)}")
            if len(self.champions_incomplete) > 10:
                print(f"    ... and {len(self.champions_incomplete) - 10} more")
        
        print("\n" + "-" * 80)
        print(f"ITEMS: {self.items_synced}/{self.items_total} synced ({self.items_sync_rate():.2f}%)")
        if self.items_missing:
            print(f"  Missing items ({len(self.items_missing)}):")
            for item in self.items_missing[:10]:  # Show first 10
                print(f"    - {item}")
            if len(self.items_missing) > 10:
                print(f"    ... and {len(self.items_missing) - 10} more")
        
        if self.items_incomplete:
            print(f"  Incomplete items ({len(self.items_incomplete)}):")
            for item, fields in self.items_incomplete[:10]:  # Show first 10
                print(f"    - {item}: missing {', '.join(fields)}")
            if len(self.items_incomplete) > 10:
                print(f"    ... and {len(self.items_incomplete) - 10} more")
        
        print("\n" + "-" * 80)
        print(f"RUNES: {self.runes_synced}/{self.runes_total} synced ({self.runes_sync_rate():.2f}%)")
        if self.runes_missing:
            print(f"  Missing runes ({len(self.runes_missing)}):")
            for rune in self.runes_missing[:10]:  # Show first 10
                print(f"    - {rune}")
            if len(self.runes_missing) > 10:
                print(f"    ... and {len(self.runes_missing) - 10} more")
        
        if self.runes_incomplete:
            print(f"  Incomplete runes ({len(self.runes_incomplete)}):")
            for rune, fields in self.runes_incomplete[:10]:  # Show first 10
                print(f"    - {rune}: missing {', '.join(fields)}")
            if len(self.runes_incomplete) > 10:
                print(f"    ... and {len(self.runes_incomplete) - 10} more")
        
        print("\n" + "-" * 80)
        print(f"OVERALL SYNC RATE: {self.overall_sync_rate():.2f}%")
        print("=" * 80)


def load_json_file(file_path: Path) -> Any:
    """Load JSON data from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None


def get_db_connection():
    """Get a connection to the database."""
    try:
        conn = psycopg2.connect(**DB_PARAMS, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None


def check_champions(conn, report: SyncReport):
    """Check if all champions in the local files exist in the database."""
    print("Checking champions synchronization...")
    
    # Load champions data from file
    champions_data = load_json_file(CHAMPIONS_FILE)
    if not champions_data or 'data' not in champions_data:
        print("Error: Champions data not found or invalid format")
        return
    
    # Get all champions from database
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, title, key, version 
        FROM champions
    """)
    db_champions = {row['id']: row for row in cursor.fetchall()}
    
    # Get all champion details
    cursor.execute("""
        SELECT champion_id, COUNT(*) as spell_count
        FROM spells
        GROUP BY champion_id
    """)
    champion_spells = {row['champion_id']: row['spell_count'] for row in cursor.fetchall()}
    
    cursor.execute("""
        SELECT champion_id, COUNT(*) as skin_count
        FROM champion_skins
        GROUP BY champion_id
    """)
    champion_skins = {row['champion_id']: row['skin_count'] for row in cursor.fetchall()}
    
    # Check each champion
    file_champions = champions_data['data']
    report.champions_total = len(file_champions)
    
    for champion_id, champion_data in file_champions.items():
        if champion_id not in db_champions:
            report.champions_missing.append(f"{champion_id} ({champion_data.get('name', 'Unknown')})")
            continue
        
        # Check if champion data is complete
        db_champion = db_champions[champion_id]
        missing_fields = []
        
        # Basic checks
        if db_champion['name'] != champion_data.get('name'):
            missing_fields.append(f"name mismatch: {db_champion['name']} vs {champion_data.get('name')}")
        
        if db_champion['title'] != champion_data.get('title'):
            missing_fields.append(f"title mismatch: {db_champion['title']} vs {champion_data.get('title')}")
        
        if db_champion['key'] != champion_data.get('key'):
            missing_fields.append(f"key mismatch: {db_champion['key']} vs {champion_data.get('key')}")
        
        # Check detailed data (we'd need to load individual champion files for this)
        # For now, just check if spells and skins exist
        expected_spells = 4  # Most champions have 4 spells (Q, W, E, R)
        if champion_id not in champion_spells or champion_spells[champion_id] < expected_spells:
            missing_fields.append(f"spells (found {champion_spells.get(champion_id, 0)}, expected at least {expected_spells})")
        
        # Most champions have at least 1 skin (the default)
        if champion_id not in champion_skins or champion_skins[champion_id] < 1:
            missing_fields.append(f"skins (found {champion_skins.get(champion_id, 0)}, expected at least 1)")
        
        if missing_fields:
            report.champions_incomplete.append((f"{champion_id} ({champion_data.get('name', 'Unknown')})", missing_fields))
        else:
            report.champions_synced += 1


def check_items(conn, report: SyncReport):
    """Check if all items in the local files exist in the database."""
    print("Checking items synchronization...")
    
    # Load items data from file
    items_data = load_json_file(ITEMS_FILE)
    if not items_data or 'data' not in items_data:
        print("Error: Items data not found or invalid format")
        return
    
    # Get all items from database
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, description, plain_text, version 
        FROM items
    """)
    db_items = {row['id']: row for row in cursor.fetchall()}
    
    # Get item tags
    cursor.execute("""
        SELECT item_id, COUNT(*) as tag_count
        FROM item_tags
        GROUP BY item_id
    """)
    item_tags = {row['item_id']: row['tag_count'] for row in cursor.fetchall()}
    
    # Check each item
    file_items = items_data['data']
    report.items_total = len(file_items)
    
    for item_id, item_data in file_items.items():
        if item_id not in db_items:
            report.items_missing.append(f"{item_id} ({item_data.get('name', 'Unknown')})")
            continue
        
        # Check if item data is complete
        db_item = db_items[item_id]
        missing_fields = []
        
        # Basic checks
        if db_item['name'] != item_data.get('name'):
            missing_fields.append(f"name mismatch: {db_item['name']} vs {item_data.get('name')}")
        
        # Check if tags exist
        if 'tags' in item_data and len(item_data['tags']) > 0:
            if item_id not in item_tags or item_tags[item_id] < len(item_data['tags']):
                missing_fields.append(f"tags (found {item_tags.get(item_id, 0)}, expected {len(item_data['tags'])})")
        
        if missing_fields:
            report.items_incomplete.append((f"{item_id} ({item_data.get('name', 'Unknown')})", missing_fields))
        else:
            report.items_synced += 1


def check_runes(conn, report: SyncReport):
    """Check if all runes in the local files exist in the database."""
    print("Checking runes synchronization...")
    
    # Load runes data from file
    runes_data = load_json_file(RUNES_FILE)
    if not runes_data:
        print("Error: Runes data not found or invalid format")
        return
    
    # Get all rune paths from database
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, key, name, icon, version 
        FROM rune_paths
    """)
    db_rune_paths = {str(row['id']): row for row in cursor.fetchall()}
    
    # Get all runes from database
    cursor.execute("""
        SELECT id, key, name, short_desc, long_desc, version 
        FROM runes
    """)
    db_runes = {str(row['id']): row for row in cursor.fetchall()}
    
    # Count total runes in file
    total_runes = 0
    rune_path_map = {}  # Map rune path IDs to names
    
    for rune_path in runes_data:
        rune_path_id = str(rune_path.get('id', ''))
        rune_path_map[rune_path_id] = rune_path.get('name', 'Unknown')
        total_runes += 1  # Count the path itself
        
        # Count runes in slots
        for slot in rune_path.get('slots', []):
            for rune in slot.get('runes', []):
                total_runes += 1
    
    report.runes_total = total_runes
    
    # Check rune paths
    for rune_path in runes_data:
        rune_path_id = str(rune_path.get('id', ''))
        
        if rune_path_id not in db_rune_paths:
            report.runes_missing.append(f"Path {rune_path_id} ({rune_path.get('name', 'Unknown')})")
            continue
        
        # Rune path exists, count it as synced
        report.runes_synced += 1
        
        # Check runes in each slot
        for slot_index, slot in enumerate(rune_path.get('slots', [])):
            for rune in slot.get('runes', []):
                rune_id = str(rune.get('id', ''))
                
                if rune_id not in db_runes:
                    report.runes_missing.append(f"Rune {rune_id} ({rune.get('name', 'Unknown')}) in path {rune_path.get('name', 'Unknown')}")
                    continue
                
                # Check if rune data is complete
                db_rune = db_runes[rune_id]
                missing_fields = []
                
                # Basic checks
                if db_rune['name'] != rune.get('name'):
                    missing_fields.append(f"name mismatch: {db_rune['name']} vs {rune.get('name')}")
                
                if db_rune['key'] != rune.get('key'):
                    missing_fields.append(f"key mismatch: {db_rune['key']} vs {rune.get('key')}")
                
                if missing_fields:
                    report.runes_incomplete.append((f"{rune_id} ({rune.get('name', 'Unknown')})", missing_fields))
                else:
                    report.runes_synced += 1


def main():
    """Main function to verify data synchronization."""
    print("Starting Data Dragon to Database synchronization verification...")
    
    report = SyncReport()
    
    # Connect to database
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to database. Exiting.")
        return
    
    try:
        # Check champions
        check_champions(conn, report)
        
        # Check items
        check_items(conn, report)
        
        # Check runes
        check_runes(conn, report)
        
    except Exception as e:
        print(f"Error during verification: {e}")
    finally:
        conn.close()
    
    # Generate report
    report.finish()
    report.print_report()


if __name__ == "__main__":
    main()