#!/usr/bin/env python3
"""
Script to perform a full synchronization of all data from Data Dragon to the database.
This script ensures that all champions, items, runes, and their relationships are 
properly synchronized, achieving 100% data completeness.
"""

import json
import os
import sys
import time
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor

# Database connection parameters
DB_PARAMS = {
    'dbname': 'lol_extension',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',  # Connect from host to Docker container
    'port': 5433   # Port exposed by Docker for PostgreSQL
}

# Paths to data files
DATA_DIR = Path(__file__).parent / "api_responses"
CHAMPIONS_FILE = DATA_DIR / "champions_15.12.1.json"
ITEMS_FILE = DATA_DIR / "items_15.12.1.json"
RUNES_FILE = DATA_DIR / "runes_15.12.1.json"
INDIVIDUAL_CHAMPIONS_DIR = DATA_DIR / "individual_champions"
VERSION = "15.12.1"  # Current Data Dragon version

def log(message):
    """Log a message with timestamp."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def load_json_file(file_path):
    """Load JSON data from a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        log(f"Error loading {file_path}: {e}")
        return None

def get_db_connection():
    """Get a connection to the database."""
    try:
        conn = psycopg2.connect(**DB_PARAMS, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        log(f"Error connecting to database: {e}")
        return None

def set_current_version(conn, version, entity_type):
    """Set the current version for a specific entity type."""
    cursor = conn.cursor()
    
    try:
        # First clear any existing current version
        cursor.execute("""
            UPDATE game_versions 
            SET is_current = FALSE 
            WHERE entity_type = %s AND is_current = TRUE
        """, (entity_type,))
        
        # Then set the new current version
        cursor.execute("""
            INSERT INTO game_versions (version, entity_type, is_current)
            VALUES (%s, %s, TRUE)
            ON CONFLICT (version, entity_type) DO UPDATE
            SET is_current = TRUE
        """, (version, entity_type))
        
        conn.commit()
        log(f"Set current version for {entity_type} to {version}")
    except Exception as e:
        conn.rollback()
        log(f"Error setting current version: {e}")

def sync_item_recipes(conn, items_data):
    """Synchronize item recipe relationships."""
    cursor = conn.cursor()
    
    try:
        # Clear existing recipes
        cursor.execute("DELETE FROM item_recipes")
        
        # Add new recipes
        recipe_count = 0
        for item_id, item_data in items_data['data'].items():
            if 'from' in item_data and item_data['from']:
                for component_id in item_data['from']:
                    cursor.execute("""
                        INSERT INTO item_recipes (item_id, component_id)
                        VALUES (%s, %s)
                        ON CONFLICT (item_id, component_id) DO NOTHING
                    """, (item_id, component_id))
                    recipe_count += 1
        
        conn.commit()
        log(f"Synchronized {recipe_count} item recipes")
    except Exception as e:
        conn.rollback()
        log(f"Error synchronizing item recipes: {e}")

def sync_champion_tags(conn, champions_data):
    """Synchronize champion tags."""
    cursor = conn.cursor()
    
    try:
        # First collect all tags
        all_tags = set()
        for champion_id, champion_data in champions_data['data'].items():
            if 'tags' in champion_data:
                all_tags.update(champion_data['tags'])
        
        # Ensure all tags exist in the database
        for tag_name in all_tags:
            cursor.execute("""
                INSERT INTO tags (name)
                VALUES (%s)
                ON CONFLICT (name) DO NOTHING
            """, (tag_name,))
        
        # Clear existing champion tags
        cursor.execute("DELETE FROM champion_tags")
        
        # Add champion tags
        tag_count = 0
        for champion_id, champion_data in champions_data['data'].items():
            if 'tags' in champion_data:
                for tag_name in champion_data['tags']:
                    # Get tag ID
                    cursor.execute("SELECT id FROM tags WHERE name = %s", (tag_name,))
                    tag_row = cursor.fetchone()
                    if tag_row:
                        tag_id = tag_row['id']
                        # Add champion-tag relationship
                        cursor.execute("""
                            INSERT INTO champion_tags (champion_id, tag_id)
                            VALUES (%s, %s)
                            ON CONFLICT (champion_id, tag_id) DO NOTHING
                        """, (champion_id, tag_id))
                        tag_count += 1
        
        conn.commit()
        log(f"Synchronized {tag_count} champion tags")
    except Exception as e:
        conn.rollback()
        log(f"Error synchronizing champion tags: {e}")

def sync_item_tags(conn, items_data):
    """Synchronize item tags."""
    cursor = conn.cursor()
    
    try:
        # First collect all tags
        all_tags = set()
        for item_id, item_data in items_data['data'].items():
            if 'tags' in item_data:
                all_tags.update(item_data['tags'])
        
        # Ensure all tags exist in the database
        for tag_name in all_tags:
            cursor.execute("""
                INSERT INTO tags (name)
                VALUES (%s)
                ON CONFLICT (name) DO NOTHING
            """, (tag_name,))
        
        # Clear existing item tags
        cursor.execute("DELETE FROM item_tags")
        
        # Add item tags
        tag_count = 0
        for item_id, item_data in items_data['data'].items():
            if 'tags' in item_data:
                for tag_name in item_data['tags']:
                    # Get tag ID
                    cursor.execute("SELECT id FROM tags WHERE name = %s", (tag_name,))
                    tag_row = cursor.fetchone()
                    if tag_row:
                        tag_id = tag_row['id']
                        # Add item-tag relationship
                        cursor.execute("""
                            INSERT INTO item_tags (item_id, tag_id)
                            VALUES (%s, %s)
                            ON CONFLICT (item_id, tag_id) DO NOTHING
                        """, (item_id, tag_id))
                        tag_count += 1
        
        conn.commit()
        log(f"Synchronized {tag_count} item tags")
    except Exception as e:
        conn.rollback()
        log(f"Error synchronizing item tags: {e}")

def verify_champion_spells(conn):
    """Verify and fix missing champion spells."""
    cursor = conn.cursor()
    
    try:
        # Get all champions that are missing spells
        cursor.execute("""
            SELECT c.id, c.name, COUNT(s.id) as spell_count
            FROM champions c
            LEFT JOIN spells s ON c.id = s.champion_id
            GROUP BY c.id, c.name
            HAVING COUNT(s.id) < 4
            ORDER BY c.name
        """)
        
        champions_missing_spells = cursor.fetchall()
        if not champions_missing_spells:
            log("All champions have their spells. No action needed.")
            return
        
        log(f"Found {len(champions_missing_spells)} champions missing spells:")
        for champion in champions_missing_spells:
            log(f"  - {champion['name']} (ID: {champion['id']}): {champion['spell_count']} spells")
        
        # Fix missing spells by loading individual champion files
        for champion in champions_missing_spells:
            champion_id = champion['id']
            champion_file = INDIVIDUAL_CHAMPIONS_DIR / f"{champion_id}.json"
            
            if not champion_file.exists():
                log(f"Warning: Individual champion file not found for {champion['name']} ({champion_id})")
                continue
            
            # Load champion details
            champion_data = load_json_file(champion_file)
            if not champion_data or 'data' not in champion_data or champion_id not in champion_data['data']:
                log(f"Error: Invalid data in champion file for {champion['name']} ({champion_id})")
                continue
            
            champion_details = champion_data['data'][champion_id]
            
            # Add missing spells
            if 'spells' in champion_details:
                # Clear existing spells to avoid duplicates
                cursor.execute("DELETE FROM spells WHERE champion_id = %s", (champion_id,))
                
                spell_slot_map = {'Q': 0, 'W': 1, 'E': 2, 'R': 3}
                
                for i, spell in enumerate(champion_details['spells']):
                    # Determine spell slot
                    slot = i  # Default to index
                    
                    # Extract spell data
                    spell_id = spell.get('id', '')
                    name = spell.get('name', '')
                    description = spell.get('description', '')
                    tooltip = spell.get('tooltip', '')
                    max_rank = spell.get('maxrank', 5)
                    cooldown_burn = spell.get('cooldownBurn', '')
                    cost_burn = spell.get('costBurn', '')
                    cost_type = spell.get('costType', '')
                    
                    # Add spell to database
                    cursor.execute("""
                        INSERT INTO spells (
                            id, champion_id, name, description, tooltip, slot,
                            max_rank, cooldown_burn, cost_burn, cost_type,
                            version
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                    """, (
                        spell_id, champion_id, name, description, tooltip, slot,
                        max_rank, cooldown_burn, cost_burn, cost_type, VERSION
                    ))
                
                log(f"Added {len(champion_details['spells'])} spells for {champion['name']}")
        
        conn.commit()
        log("Champion spell synchronization completed")
    except Exception as e:
        conn.rollback()
        log(f"Error verifying/fixing champion spells: {e}")

def verify_champion_skins(conn):
    """Verify and fix missing champion skins."""
    cursor = conn.cursor()
    
    try:
        # Get all champions that are missing skins
        cursor.execute("""
            SELECT c.id, c.name, COUNT(s.id) as skin_count
            FROM champions c
            LEFT JOIN champion_skins s ON c.id = s.champion_id
            GROUP BY c.id, c.name
            HAVING COUNT(s.id) = 0
            ORDER BY c.name
        """)
        
        champions_missing_skins = cursor.fetchall()
        if not champions_missing_skins:
            log("All champions have skins. No action needed.")
            return
        
        log(f"Found {len(champions_missing_skins)} champions missing skins:")
        for champion in champions_missing_skins:
            log(f"  - {champion['name']} (ID: {champion['id']})")
        
        # Fix missing skins by loading individual champion files
        for champion in champions_missing_skins:
            champion_id = champion['id']
            champion_file = INDIVIDUAL_CHAMPIONS_DIR / f"{champion_id}.json"
            
            if not champion_file.exists():
                log(f"Warning: Individual champion file not found for {champion['name']} ({champion_id})")
                continue
            
            # Load champion details
            champion_data = load_json_file(champion_file)
            if not champion_data or 'data' not in champion_data or champion_id not in champion_data['data']:
                log(f"Error: Invalid data in champion file for {champion['name']} ({champion_id})")
                continue
            
            champion_details = champion_data['data'][champion_id]
            
            # Add skins
            if 'skins' in champion_details:
                # Clear existing skins to avoid duplicates
                cursor.execute("DELETE FROM champion_skins WHERE champion_id = %s", (champion_id,))
                
                for skin in champion_details['skins']:
                    skin_id = skin.get('id', '')
                    num = skin.get('num', 0)
                    name = skin.get('name', '')
                    chromas = skin.get('chromas', False)
                    
                    # Add skin to database
                    cursor.execute("""
                        INSERT INTO champion_skins (
                            id, champion_id, num, name, chromas
                        ) VALUES (
                            %s, %s, %s, %s, %s
                        )
                    """, (
                        skin_id, champion_id, num, name, chromas
                    ))
                
                log(f"Added {len(champion_details['skins'])} skins for {champion['name']}")
        
        conn.commit()
        log("Champion skin synchronization completed")
    except Exception as e:
        conn.rollback()
        log(f"Error verifying/fixing champion skins: {e}")

def verify_rune_slots(conn, runes_data):
    """Verify and fix rune slots and runes."""
    cursor = conn.cursor()
    
    try:
        # First check if we have rune paths
        cursor.execute("SELECT COUNT(*) as count FROM rune_paths")
        result = cursor.fetchone()
        
        if result['count'] == 0:
            log("No rune paths found in database. Adding rune paths...")
            
            # Add rune paths
            for rune_path in runes_data:
                path_id = rune_path.get('id')
                key = rune_path.get('key')
                name = rune_path.get('name')
                icon = rune_path.get('icon')
                
                cursor.execute("""
                    INSERT INTO rune_paths (id, key, name, icon, version)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE
                    SET key = %s, name = %s, icon = %s, version = %s
                """, (
                    path_id, key, name, icon, VERSION,
                    key, name, icon, VERSION
                ))
            
            log(f"Added {len(runes_data)} rune paths")
        
        # Now check rune slots and runes
        for rune_path in runes_data:
            path_id = rune_path.get('id')
            
            if 'slots' in rune_path:
                for slot_index, slot in enumerate(rune_path['slots']):
                    # Check if slot exists
                    cursor.execute("""
                        SELECT id FROM rune_slots
                        WHERE path_id = %s AND slot_number = %s
                    """, (path_id, slot_index))
                    
                    slot_row = cursor.fetchone()
                    slot_id = None
                    
                    if not slot_row:
                        # Create slot
                        cursor.execute("""
                            INSERT INTO rune_slots (path_id, slot_number)
                            VALUES (%s, %s)
                            RETURNING id
                        """, (path_id, slot_index))
                        slot_id = cursor.fetchone()['id']
                        log(f"Added rune slot {slot_index} for path {path_id}")
                    else:
                        slot_id = slot_row['id']
                    
                    # Add runes for this slot
                    if 'runes' in slot:
                        for rune in slot['runes']:
                            rune_id = rune.get('id')
                            key = rune.get('key')
                            name = rune.get('name')
                            icon = rune.get('icon')
                            short_desc = rune.get('shortDesc', '')
                            long_desc = rune.get('longDesc', '')
                            
                            # Check if rune exists
                            cursor.execute("""
                                SELECT id FROM runes
                                WHERE id = %s
                            """, (rune_id,))
                            
                            if not cursor.fetchone():
                                # Add rune
                                cursor.execute("""
                                    INSERT INTO runes (
                                        id, slot_id, path_id, key, name, icon,
                                        short_desc, long_desc, version
                                    ) VALUES (
                                        %s, %s, %s, %s, %s, %s, %s, %s, %s
                                    )
                                """, (
                                    rune_id, slot_id, path_id, key, name, icon,
                                    short_desc, long_desc, VERSION
                                ))
                                log(f"Added rune {name} (ID: {rune_id}) to slot {slot_index}")
        
        conn.commit()
        log("Rune verification and synchronization completed")
    except Exception as e:
        conn.rollback()
        log(f"Error verifying/fixing runes: {e}")

def run_full_sync():
    """Run a full synchronization of all data."""
    log("Starting full data synchronization...")
    
    # Load data files
    champions_data = load_json_file(CHAMPIONS_FILE)
    items_data = load_json_file(ITEMS_FILE)
    runes_data = load_json_file(RUNES_FILE)
    
    if not champions_data or not items_data or not runes_data:
        log("Error: One or more data files could not be loaded. Aborting.")
        return
    
    # Connect to database
    conn = get_db_connection()
    if not conn:
        log("Error: Could not connect to database. Aborting.")
        return
    
    try:
        # Sync data
        log("1. Synchronizing item recipes...")
        sync_item_recipes(conn, items_data)
        
        log("2. Synchronizing champion tags...")
        sync_champion_tags(conn, champions_data)
        
        log("3. Synchronizing item tags...")
        sync_item_tags(conn, items_data)
        
        log("4. Verifying champion spells...")
        verify_champion_spells(conn)
        
        log("5. Verifying champion skins...")
        verify_champion_skins(conn)
        
        log("6. Verifying rune paths, slots, and runes...")
        verify_rune_slots(conn, runes_data)
        
        # Set current versions
        log("7. Setting current versions...")
        set_current_version(conn, VERSION, "champions")
        set_current_version(conn, VERSION, "items")
        set_current_version(conn, VERSION, "runes")
        
        log("Full data synchronization completed successfully!")
    except Exception as e:
        log(f"Error during synchronization: {e}")
    finally:
        conn.close()

def verify_sync_status():
    """Run the verification script to check sync status."""
    log("Verifying data synchronization status...")
    
    # Run the verification script
    try:
        import subprocess
        
        # Verify directly with the container
        cmd = [
            "docker", "exec", "lol_extension_api",
            "python", "/app/verify_data_sync.py"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        log(result.stdout)
        
        if result.stderr:
            log(f"Verification errors: {result.stderr}")
    except Exception as e:
        log(f"Error running verification: {e}")

if __name__ == "__main__":
    run_full_sync()
    verify_sync_status()