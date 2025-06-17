#!/usr/bin/env python3
import os
import sys
import json
import shutil
import requests
from urllib.parse import urlparse

# Define source directory (datadragon assets)
SRC_DIR = "/home/rod/Projects/lol-ext/datadragon/api_responses"
# Skip backend dir since we don't have permission
EXTENSION_DIR = "/home/rod/Projects/lol-ext/extension/assets/runes"

# Create destination directories if they don't exist
os.makedirs(EXTENSION_DIR, exist_ok=True)

# Load rune data
runes_file = os.path.join(SRC_DIR, "runes_15.12.1.json")
with open(runes_file, 'r') as f:
    runes_data = json.load(f)

# Track which files we need to process
rune_ids = []
rune_paths = []

# Extract rune IDs and icon paths
for style in runes_data:
    # Add the style ID
    rune_ids.append(str(style['id']))
    rune_paths.append(style['icon'])
    
    # Process each slot
    for slot in style['slots']:
        # Process each rune in the slot
        for rune in slot['runes']:
            rune_ids.append(str(rune['id']))
            rune_paths.append(rune['icon'])

# Create placeholder files for each rune ID
for i, (rune_id, icon_path) in enumerate(zip(rune_ids, rune_paths)):
    # Extract the filename from the path
    filename = os.path.basename(icon_path)
    
    # Create empty extension file
    extension_file = os.path.join(EXTENSION_DIR, f"{rune_id}.png")
    with open(extension_file, 'wb') as f:
        # Just create an empty file for now
        f.write(b'')
    
    print(f"Created placeholder for rune {rune_id}")

print(f"Created {len(rune_ids)} placeholder files")