#!/usr/bin/env python3
"""
Edit the items.js file to replace the fetchItems method with our updated version
that can fetch items across multiple pages.
"""

import re
import sys
import os

def update_fetch_items():
    # Read the original items.js file
    with open('items.js', 'r') as f:
        content = f.read()
    
    # Read the new fetchItems method
    with open('update_fetch_items.js', 'r') as f:
        new_fetch_items = f.read()
    
    # Replace the fetchItems method in the original content
    # Using a regex pattern to find the method
    pattern = r'async fetchItems\(\) \{.*?^\s*\}'
    replacement = new_fetch_items
    
    # Use regex with DOTALL to match across multiple lines
    updated_content = re.sub(pattern, replacement, content, flags=re.DOTALL | re.MULTILINE)
    
    # Check if the replacement was successful
    if content == updated_content:
        print("Error: Could not find the fetchItems method in items.js")
        return False
    
    # Create a backup of the original file
    backup_file = 'items.js.bak'
    with open(backup_file, 'w') as f:
        f.write(content)
    print(f"Created backup at {backup_file}")
    
    # Write the updated content
    with open('items.js', 'w') as f:
        f.write(updated_content)
    
    print("Successfully updated items.js with the new fetchItems method")
    return True

if __name__ == "__main__":
    update_fetch_items()