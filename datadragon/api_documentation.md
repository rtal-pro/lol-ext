# Data Dragon API Documentation

This document contains URLs for League of Legends Data Dragon API and descriptions of what each endpoint provides.

## Base URLs
- CDN Base: `https://ddragon.leagueoflegends.com/cdn/`
- API Base: `https://ddragon.leagueoflegends.com/api/`

## Version Information
- **URL**: `https://ddragon.leagueoflegends.com/api/versions.json`
- **Description**: Returns a list of all available game versions in descending order (newest first)
- **Local File**: `versions.json`

## Item Data
- **URL**: `https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/item.json`
- **Description**: Contains information about all game items including stats, passives, actives, costs, build paths
- **Local File**: `items_{version}.json`
- **Example**: `https://ddragon.leagueoflegends.com/cdn/15.12.1/data/en_US/item.json`

## Champion Data
- **URL**: `https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/champion.json`
- **Description**: Contains basic information about all champions
- **Local File**: `champions_{version}.json`
- **Example**: `https://ddragon.leagueoflegends.com/cdn/15.12.1/data/en_US/champion.json`

## Detailed Champion Data
- **URL**: `https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/champion/{championName}.json`
- **Description**: Contains detailed information about a specific champion including abilities, stats, and lore
- **Example**: `https://ddragon.leagueoflegends.com/cdn/15.12.1/data/en_US/champion/Aatrox.json`

## Runes Data
- **URL**: `https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/runesReforged.json`
- **Description**: Contains information about all runes and rune paths
- **Local File**: `runes_{version}.json`
- **Example**: `https://ddragon.leagueoflegends.com/cdn/15.12.1/data/en_US/runesReforged.json`

## Summoner Spells
- **URL**: `https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/summoner.json`
- **Description**: Contains information about all summoner spells
- **Example**: `https://ddragon.leagueoflegends.com/cdn/15.12.1/data/en_US/summoner.json`

## Profile Icons
- **URL**: `https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/profileicon.json`
- **Description**: Contains information about all profile icons
- **Example**: `https://ddragon.leagueoflegends.com/cdn/15.12.1/data/en_US/profileicon.json`

## Languages
- **URL**: `https://ddragon.leagueoflegends.com/cdn/languages.json`
- **Description**: Returns a list of all available languages
- **Example**: `https://ddragon.leagueoflegends.com/cdn/languages.json`

## Asset URLs

### Champion Images
- **URL**: `https://ddragon.leagueoflegends.com/cdn/{version}/img/champion/{championName}.png`
- **Description**: Champion square images
- **Example**: `https://ddragon.leagueoflegends.com/cdn/15.12.1/img/champion/Aatrox.png`

### Item Images
- **URL**: `https://ddragon.leagueoflegends.com/cdn/{version}/img/item/{itemId}.png`
- **Description**: Item images
- **Example**: `https://ddragon.leagueoflegends.com/cdn/15.12.1/img/item/3078.png` (Trinity Force)

### Rune Images
- **URL**: `https://ddragon.leagueoflegends.com/cdn/img/{runePathType}/{runeId}.png`
- **Description**: Rune images
- **Example**: `https://ddragon.leagueoflegends.com/cdn/img/perk-images/Styles/Precision/PressTheAttack/PressTheAttack.png`

### Champion Splash Art
- **URL**: `https://ddragon.leagueoflegends.com/cdn/img/champion/splash/{championName}_{skinId}.jpg`
- **Description**: Champion splash art
- **Example**: `https://ddragon.leagueoflegends.com/cdn/img/champion/splash/Aatrox_0.jpg`

### Champion Loading Screen Art
- **URL**: `https://ddragon.leagueoflegends.com/cdn/img/champion/loading/{championName}_{skinId}.jpg`
- **Description**: Champion loading screen art
- **Example**: `https://ddragon.leagueoflegends.com/cdn/img/champion/loading/Aatrox_0.jpg`

## Notes
- Replace `{version}` with the desired game version (e.g., "15.12.1")
- Replace `{championName}` with the champion's name (e.g., "Aatrox")
- Replace `{itemId}` with the item's ID (e.g., "3078" for Trinity Force)
- Replace `{skinId}` with the skin ID (0 is the default skin)