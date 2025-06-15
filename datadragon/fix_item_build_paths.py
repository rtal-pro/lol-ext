#!/usr/bin/env python3
"""
Script to fix item build paths by populating the item_components and item_builds_into tables.
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
    'host': 'localhost',  # Connect from host to Docker container
    'port': 5433   # Port exposed by Docker for PostgreSQL
}

# Path to items data file
ITEMS_FILE = Path(__file__).parent / "api_responses" / "items_15.12.1.json"

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

def clear_existing_relationships(conn):
    """Clear existing item relationships."""
    cursor = conn.cursor()
    
    try:
        print("Clearing existing item build path relationships...")
        cursor.execute("DELETE FROM item_recipes")
        conn.commit()
        print("Existing relationships cleared successfully.")
    except Exception as e:
        conn.rollback()
        print(f"Error clearing relationships: {e}")

def populate_item_relationships(conn, items_data):
    """Populate item_recipes table with build path data."""
    cursor = conn.cursor()
    
    relationship_count = 0
    
    try:
        # Process each item
        for item_id, item_data in items_data['data'].items():
            # Add components (from -> item)
            if 'from' in item_data and item_data['from']:
                for component_id in item_data['from']:
                    try:
                        # In the item_recipes table:
                        # item_id is the item being built
                        # component_id is the item used as a component
                        cursor.execute("""
                            INSERT INTO item_recipes (item_id, component_id)
                            VALUES (%s, %s)
                            ON CONFLICT (item_id, component_id) DO NOTHING
                        """, (item_id, component_id))
                        relationship_count += 1
                    except Exception as e:
                        print(f"Error adding component {component_id} to {item_id}: {e}")
        
        conn.commit()
        print(f"Successfully added {relationship_count} item recipe relationships.")
    except Exception as e:
        conn.rollback()
        print(f"Error populating item relationships: {e}")

def fix_item_build_paths():
    """Main function to fix item build paths."""
    print("Starting to fix item build paths...")
    
    # Load item data
    items_data = load_json_file(ITEMS_FILE)
    if not items_data or 'data' not in items_data:
        print("Error: Items data not found or invalid format")
        return
    
    # Connect to database
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to database. Exiting.")
        return
    
    try:
        # Clear existing relationships
        clear_existing_relationships(conn)
        
        # Populate relationships
        populate_item_relationships(conn, items_data)
        
        # Verify Trinity Force build path
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.component_id, i.name
            FROM item_recipes r
            JOIN items i ON r.component_id = i.id
            WHERE r.item_id = '3078'
        """)
        
        components = cursor.fetchall()
        if components:
            print("\nTrinity Force (3078) builds from:")
            for component in components:
                print(f"  - {component['component_id']}: {component['name']}")
        else:
            print("\nWarning: Trinity Force (3078) has no components in the database.")
        
        cursor.execute("""
            SELECT r.item_id, i.name
            FROM item_recipes r
            JOIN items i ON r.item_id = i.id
            WHERE r.component_id = '3057'
        """)
        
        builds_into = cursor.fetchall()
        if builds_into:
            print("\nSheen (3057) builds into:")
            for item in builds_into:
                print(f"  - {item['item_id']}: {item['name']}")
        else:
            print("\nWarning: Sheen (3057) doesn't build into any items in the database.")
        
    finally:
        conn.close()

if __name__ == "__main__":
    fix_item_build_paths()