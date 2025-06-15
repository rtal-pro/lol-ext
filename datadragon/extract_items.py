#!/usr/bin/env python3
"""
Script to extract individual items from the Data Dragon item.json file
and save each item as a separate JSON file.
"""

import os
import json
import sys

def extract_items(items_file_path, output_dir):
    """Extract individual items from the items.json file."""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Load the items JSON file
    with open(items_file_path, 'r', encoding='utf-8') as f:
        items_data = json.load(f)
    
    if 'data' not in items_data:
        print(f"Error: No 'data' field found in {items_file_path}")
        return
    
    # Get the version from the file
    version = items_data.get('version', 'unknown')
    
    # Extract individual items
    items_count = 0
    for item_id, item_data in items_data['data'].items():
        # Create a new JSON object with the item data
        item_json = {
            "type": "item",
            "version": version,
            "data": {
                item_id: item_data
            }
        }
        
        # Create output file path
        item_name = item_data.get('name', '').replace(' ', '_').replace('/', '_')
        if not item_name:
            item_name = f"Item_{item_id}"
        
        output_file = os.path.join(output_dir, f"item_{item_id}_{item_name}_{version}.json")
        
        # Write the item data to a file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(item_json, f, indent=2, ensure_ascii=False)
        
        items_count += 1
    
    print(f"Extracted {items_count} items to {output_dir}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_items.py <items_file_path> [output_directory]")
        sys.exit(1)
    
    items_file_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(items_file_path), "individual_items")
    
    extract_items(items_file_path, output_dir)