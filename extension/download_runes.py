import os
import sys
import urllib.request

# Create target directory
os.makedirs('/home/rod/Projects/lol-ext/extension/assets/runes', exist_ok=True)

# List of rune IDs to download
rune_ids = [
    # Paths
    8000, 8100, 8200, 8300, 8400,
    
    # Precision keystones and runes
    8005, 8008, 8021, 8010, 9101, 9111, 8009, 9104, 9105, 9103, 8014, 8017, 8299,
    
    # Domination keystones and runes
    8112, 8128, 9923, 8126, 8139, 8143, 8137, 8140, 8141, 8135, 8105, 8106,
    
    # Sorcery keystones and runes
    8214, 8229, 8230, 8224, 8226, 8275, 8210, 8234, 8233, 8237, 8232, 8236,
    
    # Inspiration keystones and runes
    8351, 8360, 8369, 8306, 8304, 8321, 8313, 8352, 8345, 8347, 8410, 8316,
    
    # Resolve keystones and runes
    8437, 8439, 8465, 8446, 8463, 8401, 8429, 8444, 8473, 8451, 8453, 8242
]

# API base URL
api_base_url = 'http://localhost:8001/api/v1'

# Download each rune image
for rune_id in rune_ids:
    url = f'{api_base_url}/assets/rune/image/{rune_id}'
    filename = f'/home/rod/Projects/lol-ext/extension/assets/runes/{rune_id}.png'
    
    try:
        print(f'Downloading rune {rune_id}...')
        urllib.request.urlretrieve(url, filename)
        print(f'Downloaded rune {rune_id}')
    except Exception as e:
        print(f'Error downloading rune {rune_id}: {str(e)}')

print('Download complete!')