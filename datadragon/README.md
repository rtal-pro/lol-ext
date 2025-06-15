# Data Dragon API Fetcher

This tool fetches and saves League of Legends Data Dragon API data to local JSON files.

## Features

- Fetches all major Data Dragon API endpoints
- Saves responses as organized JSON files
- Supports fetching specific game versions
- Allows fetching detailed champion data for selected champions
- Extracts individual item data into separate files

## Usage

```bash
# Basic usage (fetches latest version and limited champion data)
./fetch_datadragon.py

# Fetch with a specific version
./fetch_datadragon.py --version 15.12.1

# Fetch detailed data for all champions
./fetch_datadragon.py --all-champions

# Fetch detailed data for a specific champion
./fetch_datadragon.py --champion Aatrox

# Fetch detailed data for first N champions
./fetch_datadragon.py --max-champions 20

# Extract individual items from the main items file
./extract_items.py ./api_responses/items_15.12.1.json ./api_responses/individual_items
```

## Output Files

All files are saved in the `api_responses` directory with clear naming:

### Main Data Files
- `versions.json` - List of all available game versions
- `languages.json` - List of all available languages
- `items_{version}.json` - All item data for specified version
- `champions_{version}.json` - Basic champion data for specified version
- `runes_{version}.json` - Rune data for specified version
- `summoner_spells_{version}.json` - Summoner spell data for specified version
- `profile_icons_{version}.json` - Profile icon data for specified version

### Individual Entity Files
- `individual_champions/champion_{name}_{version}.json` - Detailed data for each champion
- `individual_items/item_{id}_{name}_{version}.json` - Detailed data for each item

## Directory Structure

```
api_responses/
├── main data files (.json)
├── individual_champions/
│   ├── champion_Aatrox_15.12.1.json
│   ├── champion_Ahri_15.12.1.json
│   └── ...
└── individual_items/
    ├── item_1001_Boots_15.12.1.json
    ├── item_3078_Trinity_Force_15.12.1.json
    └── ...
```

## Requirements

- Python 3.6+
- Required packages: `requests`

Install dependencies:
```bash
pip install requests
```