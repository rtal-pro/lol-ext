#!/usr/bin/env python3
"""
Script to identify and fix missing items in the database by directly inserting them.
"""

import json
import os
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor
import time

# Database connection parameters - when running in Docker container
DB_PARAMS = {
    'dbname': 'lol_extension',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'db',  # Use the Docker service name
    'port': 5432   # Default PostgreSQL port inside container
}

# Path to items data file
API_RESPONSES_DIR = Path(__file__).parent / "api_responses"
ITEMS_FILE = API_RESPONSES_DIR / "items_15.12.1.json"
VERSION = "15.12.1"  # Current Data Dragon version

def load_json_file(file_path):
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

def create_required_tables(conn):
    """Create any required tables that might be missing."""
    cursor = conn.cursor()
    
    try:
        # Check if item_components table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'item_components'
            )
        """)
        
        if not cursor.fetchone()['exists']:
            print("Creating item_components table...")
            cursor.execute("""
                CREATE TABLE item_components (
                    item_id VARCHAR(255) NOT NULL,
                    component_id VARCHAR(255) NOT NULL,
                    PRIMARY KEY (item_id, component_id),
                    CONSTRAINT fk_item FOREIGN KEY (item_id) REFERENCES items (id) ON DELETE CASCADE,
                    CONSTRAINT fk_component FOREIGN KEY (component_id) REFERENCES items (id) ON DELETE CASCADE
                )
            """)
            conn.commit()
            print("item_components table created successfully.")
        
        # Check if item_builds_into table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'item_builds_into'
            )
        """)
        
        if not cursor.fetchone()['exists']:
            print("Creating item_builds_into table...")
            cursor.execute("""
                CREATE TABLE item_builds_into (
                    item_id VARCHAR(255) NOT NULL,
                    builds_into_id VARCHAR(255) NOT NULL,
                    PRIMARY KEY (item_id, builds_into_id),
                    CONSTRAINT fk_item FOREIGN KEY (item_id) REFERENCES items (id) ON DELETE CASCADE,
                    CONSTRAINT fk_builds_into FOREIGN KEY (builds_into_id) REFERENCES items (id) ON DELETE CASCADE
                )
            """)
            conn.commit()
            print("item_builds_into table created successfully.")
    
    except Exception as e:
        conn.rollback()
        print(f"Error creating tables: {e}")

def get_db_items(conn):
    """Get all items from the database."""
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM items")
    return {row['id'] for row in cursor.fetchall()}

def get_file_items():
    """Get all items from the data file."""
    items_data = load_json_file(ITEMS_FILE)
    if not items_data or 'data' not in items_data:
        print("Error: Items data not found or invalid format")
        return set()
    
    return set(items_data['data'].keys())

def insert_item(conn, item_id, item_data):
    """Insert an item into the database."""
    cursor = conn.cursor()
    
    # Extract basic item data
    name = item_data.get('name', '')
    description = item_data.get('description', '')
    plain_text = item_data.get('plaintext', '')
    
    # Handle gold data
    gold_data = item_data.get('gold', {})
    base_gold = gold_data.get('base', 0)
    total_gold = gold_data.get('total', 0)
    sell_gold = gold_data.get('sell', 0)
    purchasable = gold_data.get('purchasable', False)
    
    # Handle image data
    image_data = item_data.get('image', {})
    image_full = image_data.get('full', '')
    image_sprite = image_data.get('sprite', '')
    image_group = image_data.get('group', '')
    
    # Handle maps data
    maps_data = item_data.get('maps', {})
    maps_json = json.dumps(maps_data)
    
    # Handle stats data
    stats_data = item_data.get('stats', {})
    stats_json = json.dumps(stats_data)
    
    # Get other attributes
    consumed = item_data.get('consumed', False)
    consumable = item_data.get('consumable', False)
    in_store = item_data.get('inStore', True)
    hide_from_all = item_data.get('hideFromAll', False)
    required_champion = item_data.get('requiredChampion', None)
    required_ally = item_data.get('requiredAlly', None)
    tier = item_data.get('tier', None)
    depth = item_data.get('depth', None)
    
    try:
        # Insert the item
        cursor.execute("""
            INSERT INTO items (
                id, name, description, plain_text, base_gold, total_gold, sell_gold, 
                purchasable, consumed, consumable, in_store, hide_from_all,
                required_champion, required_ally, image_full, image_sprite, image_group,
                maps, stats, version, tier, depth
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) ON CONFLICT (id) DO NOTHING
            RETURNING id
        """, (
            item_id, name, description, plain_text, base_gold, total_gold, sell_gold,
            purchasable, consumed, consumable, in_store, hide_from_all,
            required_champion, required_ally, image_full, image_sprite, image_group,
            maps_json, stats_json, VERSION, tier, depth
        ))
        
        item_result = cursor.fetchone()
        if not item_result:
            print(f"Item {item_id} ({name}) already exists or failed to insert.")
            return False
        
        # Add tags
        if 'tags' in item_data:
            for tag_name in item_data['tags']:
                # First make sure tag exists
                cursor.execute("""
                    INSERT INTO tags (name) VALUES (%s)
                    ON CONFLICT (name) DO NOTHING
                    RETURNING id
                """, (tag_name,))
                
                tag_result = cursor.fetchone()
                if tag_result:
                    tag_id = tag_result['id']
                else:
                    # Get the existing tag ID
                    cursor.execute("SELECT id FROM tags WHERE name = %s", (tag_name,))
                    tag_row = cursor.fetchone()
                    if tag_row:
                        tag_id = tag_row['id']
                    else:
                        print(f"Warning: Could not find or create tag '{tag_name}'")
                        continue
                
                # Link item to tag
                cursor.execute("""
                    INSERT INTO item_tags (item_id, tag_id) VALUES (%s, %s)
                    ON CONFLICT (item_id, tag_id) DO NOTHING
                """, (item_id, tag_id))
        
        conn.commit()
        print(f"Successfully inserted item {item_id} ({name})")
        return True
    
    except Exception as e:
        conn.rollback()
        print(f"Error inserting item {item_id} ({name}): {e}")
        return False

def fix_missing_items():
    """Identify and fix missing items."""
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to database. Exiting.")
        return
    
    try:
        # Create required tables
        create_required_tables(conn)
        
        db_items = get_db_items(conn)
        file_items = get_file_items()
        
        missing_items = file_items - db_items
        print(f"Found {len(missing_items)} missing items.")
        
        if not missing_items:
            print("No missing items to fix.")
            return
        
        # Load the items data
        items_data = load_json_file(ITEMS_FILE)
        if not items_data or 'data' not in items_data:
            print("Error: Items data not found or invalid format")
            return
        
        # Insert missing items
        success_count = 0
        for item_id in missing_items:
            item_data = items_data['data'].get(item_id)
            if not item_data:
                print(f"Warning: No data found for item {item_id}")
                continue
            
            success = insert_item(conn, item_id, item_data)
            if success:
                success_count += 1
            
            # Add a small delay to prevent overloading the database
            time.sleep(0.01)
        
        print(f"Successfully inserted {success_count} of {len(missing_items)} missing items.")
    
    finally:
        conn.close()

if __name__ == "__main__":
    fix_missing_items()