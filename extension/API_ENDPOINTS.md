# League of Legends Extension Backend API Documentation

This document provides a comprehensive overview of all backend API endpoints available for the League of Legends Helper extension.

## Base URL

All API endpoints are prefixed with:
```
http://localhost:8001/api/v1
```

## Table of Contents

- [Health Check](#health-check)
- [Champion Endpoints](#champion-endpoints)
- [Item Endpoints](#item-endpoints)
- [Rune Endpoints](#rune-endpoints)
- [Asset Endpoints](#asset-endpoints)
- [Sync Endpoints](#sync-endpoints)
- [Error Responses](#error-responses)

## Health Check

### GET /health

Health check endpoint to verify API and database connectivity.

**Response:**
```json
{
  "status": "ok",
  "api_version": "v1",
  "environment": "development",
  "dependencies": {
    "database": {
      "status": "ok",
      "error": null
    }
  }
}
```

## Champion Endpoints

### GET /champions

Returns a list of all champions with basic information.

**Query Parameters:**
- `name` (optional): Filter champions by name (case-insensitive, partial match)
- `tag` (optional): Filter champions by tag (e.g., "Fighter", "Mage")

**Response:**
```json
[
  {
    "id": "Aatrox",
    "key": "266",
    "name": "Aatrox",
    "title": "the Darkin Blade",
    "image": {
      "full": "Aatrox.png",
      "sprite": "champion0.png",
      "group": "champion",
      "x": null,
      "y": null,
      "w": null,
      "h": null
    },
    "tags": ["Fighter", "Tank"]
  },
  // ...more champions
]
```

### GET /champions/{champion_id}

Returns detailed information about a specific champion.

**Path Parameters:**
- `champion_id`: Champion ID (e.g., 'Aatrox')

**Response:**
```json
{
  "id": "Aatrox",
  "key": "266",
  "name": "Aatrox",
  "title": "the Darkin Blade",
  "lore": "Once honored defenders of Shurima...",
  "blurb": "Once honored defenders of Shurima against the Void...",
  "allyTips": ["Use Darkin Blade to clear waves quickly", "..."],
  "enemyTips": ["Dodge his abilities by moving perpendicularly", "..."],
  "tags": ["Fighter", "Tank"],
  "partype": "Blood Well",
  "info": {
    "attack": 8,
    "defense": 4,
    "magic": 3,
    "difficulty": 4
  },
  "image": {
    "full": "Aatrox.png",
    "sprite": "champion0.png",
    "group": "champion",
    "x": null,
    "y": null,
    "w": null,
    "h": null
  },
  "stats": {
    "hp": 580,
    "hpPerLevel": 90,
    "mp": 0,
    "mpPerLevel": 0,
    "moveSpeed": 345,
    "armor": 38,
    "armorPerLevel": 3.25,
    "spellBlock": 32,
    "spellBlockPerLevel": 1.25,
    "attackRange": 175,
    "attackDamage": 60,
    "attackDamagePerLevel": 5,
    "attackSpeed": 0.651,
    "attackSpeedPerLevel": 2.5
  },
  "spells": [
    {
      "id": "AatroxQ",
      "name": "The Darkin Blade",
      "description": "Aatrox slams his greatsword...",
      "tooltip": "Aatrox slams his greatsword...",
      "maxRank": 5,
      "cooldown": [14, 12, 10, 8, 6],
      "cost": [0, 0, 0, 0, 0],
      "costType": "No Cost",
      "range": [25000, 25000, 25000, 25000, 25000],
      "image": {
        "full": "AatroxQ.png",
        "sprite": "spell0.png",
        "group": "spell",
        "x": null,
        "y": null,
        "w": null,
        "h": null
      },
      "spell_type": "Q"
    },
    // ...more spells (W, E, R)
  ],
  "passive": {
    "name": "Deathbringer Stance",
    "description": "Periodically, Aatrox's next basic attack...",
    "image": {
      "full": "Aatrox_Passive.png",
      "sprite": "passive0.png",
      "group": "passive",
      "x": null,
      "y": null,
      "w": null,
      "h": null
    }
  },
  "skins": [
    {
      "id": "266000",
      "num": 0,
      "name": "default",
      "chromas": false,
      "imageLoading": "https://ddragon.leagueoflegends.com/cdn/img/champion/loading/Aatrox_0.jpg",
      "imageSplash": "https://ddragon.leagueoflegends.com/cdn/img/champion/splash/Aatrox_0.jpg"
    },
    // ...more skins
  ]
}
```

## Item Endpoints

### GET /items

Returns all items grouped by tier.

**Query Parameters:**
- `tag` (optional): Filter items by tag (e.g., "Armor", "SpellDamage")
- `purchasable_only` (optional, default: false): Only include purchasable items
- `limit` (optional, default: 20): Number of items per page (1-100)
- `page` (optional, default: 1): Page number

**Response:**
```json
{
  "tiers": [
    {
      "tier": 1,
      "items": [
        {
          "id": "1001",
          "name": "Boots",
          "description": "Slightly increases Movement Speed",
          "plaintext": "Enhances Movement Speed",
          "tier": 1,
          "image": {
            "full": "1001.png",
            "sprite": "item0.png",
            "group": "item",
            "x": null,
            "y": null,
            "w": null,
            "h": null
          },
          "gold": {
            "base": 300,
            "total": 300,
            "sell": 210,
            "purchasable": true
          },
          "tags": ["Boots"]
        },
        // ...more tier 1 items
      ]
    },
    // ...more tiers
  ],
  "total": 175
}
```

### GET /items/{item_id}

Returns detailed information about a specific item.

**Path Parameters:**
- `item_id`: Item ID (e.g., '1001')

**Response:**
```json
{
  "id": "3006",
  "name": "Berserker's Greaves",
  "description": "<stats>+35% Attack Speed<br>+45 Movement Speed</stats>",
  "plaintext": "Enhances Movement Speed and Attack Speed",
  "tier": 2,
  "image": {
    "full": "3006.png",
    "sprite": "item0.png",
    "group": "item",
    "x": null,
    "y": null,
    "w": null,
    "h": null
  },
  "gold": {
    "base": 500,
    "total": 1100,
    "sell": 770,
    "purchasable": true
  },
  "tags": ["AttackSpeed", "Boots"],
  "stats": {
    "FlatMovementSpeedMod": 45,
    "PercentAttackSpeedMod": 0.35
  },
  "maps": {
    "11": true,
    "12": true,
    "21": true,
    "22": false
  },
  "depth": 2,
  "consumed": false,
  "consumable": false,
  "hideFromAll": false,
  "inStore": true,
  "requiredChampion": null,
  "requiredAlly": null,
  "buildsFrom": [
    {
      "id": "1001",
      "name": "Boots",
      "description": "Slightly increases Movement Speed",
      "tier": 1,
      "gold": {
        "base": 300,
        "total": 300,
        "sell": 210,
        "purchasable": true
      },
      "image": {
        "full": "1001.png",
        "sprite": "item0.png",
        "group": "item",
        "x": null,
        "y": null,
        "w": null,
        "h": null
      }
    },
    // ...other components
  ],
  "buildsInto": [
    // ...items this builds into
  ]
}
```

### GET /items/{item_id}/recipe

Returns an item with its complete recipe tree.

**Path Parameters:**
- `item_id`: Item ID (e.g., '3006')

**Query Parameters:**
- `depth` (optional, default: 2): Recipe depth to follow (1-5)

**Response:**
Same as GET /items/{item_id} but with a more detailed build tree.

## Rune Endpoints

### GET /runes

Returns the complete rune tree structure with all paths and runes.

**Response:**
```json
{
  "paths": [
    {
      "id": 8100,
      "key": "Domination",
      "name": "Domination",
      "icon": "perk-images/Styles/7200_Domination.png",
      "slots": [
        {
          "slotNumber": 0,
          "runes": [
            {
              "id": 8112,
              "key": "Electrocute",
              "name": "Electrocute",
              "shortDesc": "Hitting a champion with 3 separate attacks...",
              "longDesc": "Within 3 seconds, hitting a champion with 3 attacks...",
              "icon": "perk-images/Styles/Domination/Electrocute/Electrocute.png"
            },
            // ...more keystones
          ]
        },
        // ...more slots
      ]
    },
    // ...more paths
  ],
  "version": "13.10.1"
}
```

### GET /runes/paths/{path_id}

Returns a specific rune path with all its slots and runes.

**Path Parameters:**
- `path_id`: Rune path ID (e.g., 8100 for Domination)

**Response:**
```json
{
  "id": 8100,
  "key": "Domination",
  "name": "Domination",
  "icon": "perk-images/Styles/7200_Domination.png",
  "slots": [
    {
      "slotNumber": 0,
      "runes": [
        {
          "id": 8112,
          "key": "Electrocute",
          "name": "Electrocute",
          "shortDesc": "Hitting a champion with 3 separate attacks...",
          "longDesc": "Within 3 seconds, hitting a champion with 3 attacks...",
          "icon": "perk-images/Styles/Domination/Electrocute/Electrocute.png"
        },
        // ...more keystones
      ]
    },
    // ...more slots
  ]
}
```

### GET /runes/search

Search for runes by name or description.

**Query Parameters:**
- `query` (required, min length: 2): Search query
- `path_key` (optional): Filter by path key (e.g., 'Domination')

**Response:**
```json
[
  {
    "id": 8112,
    "key": "Electrocute",
    "name": "Electrocute",
    "shortDesc": "Hitting a champion with 3 separate attacks...",
    "longDesc": "Within 3 seconds, hitting a champion with 3 attacks...",
    "icon": "perk-images/Styles/Domination/Electrocute/Electrocute.png"
  },
  // ...more matching runes
]
```

## Asset Endpoints

### GET /assets/champion/image/{champion_id}

Returns a champion's portrait image.

**Path Parameters:**
- `champion_id`: Champion ID (e.g., 'Aatrox')

**Response:**
Image content (PNG)

### GET /assets/champion/splash/{champion_id}/{skin_num}

Returns a champion's splash art for the specified skin.

**Path Parameters:**
- `champion_id`: Champion ID (e.g., 'Aatrox')
- `skin_num` (optional, default: 0): Skin number (0 for default)

**Response:**
Image content (JPEG)

### GET /assets/champion/loading/{champion_id}/{skin_num}

Returns a champion's loading screen image for the specified skin.

**Path Parameters:**
- `champion_id`: Champion ID (e.g., 'Aatrox')
- `skin_num` (optional, default: 0): Skin number (0 for default)

**Response:**
Image content (JPEG)

### GET /assets/champion/passive/{champion_id}

Returns a champion's passive ability icon.

**Path Parameters:**
- `champion_id`: Champion ID (e.g., 'Aatrox')

**Response:**
Image content (PNG)

### GET /assets/champion/spell/{champion_id}/{spell_index}

Returns a champion's spell icon by index.

**Path Parameters:**
- `champion_id`: Champion ID (e.g., 'Aatrox')
- `spell_index`: Spell index (0-3 for Q,W,E,R)

**Response:**
Image content (PNG)

### GET /assets/item/image/{item_id}

Returns an item's icon.

**Path Parameters:**
- `item_id`: Item ID (e.g., '3006')

**Response:**
Image content (PNG)

### GET /assets/rune/image/{rune_id}

Returns a rune's icon.

**Path Parameters:**
- `rune_id`: Rune ID or key (e.g., '8112' or 'Electrocute')

**Response:**
Image content (PNG)

### GET /assets/version

Returns the current game data version used by the API.

**Response:**
```json
{
  "latest_version": "13.10.1",
  "current_versions": {
    "champions": "13.10.1",
    "items": "13.10.1",
    "runes": "13.10.1",
    "summoner-spells": "13.10.1"
  }
}
```

## Sync Endpoints

### POST /sync/champions

Fetches and updates champion data from the Data Dragon API.

**Request Body:**
```json
{
  "force": false,
  "background": false
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Champions updated to version 13.10.1",
  "entity_type": "champions",
  "previous_version": "13.9.1",
  "current_version": "13.10.1"
}
```

### POST /sync/items

Fetches and updates item data from the Data Dragon API.

**Request Body:**
```json
{
  "force": false,
  "background": false
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Items updated to version 13.10.1",
  "entity_type": "items",
  "previous_version": "13.9.1",
  "current_version": "13.10.1"
}
```

### POST /sync/runes

Fetches and updates rune data from the Data Dragon API.

**Request Body:**
```json
{
  "force": false,
  "background": false
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Runes updated to version 13.10.1",
  "entity_type": "runes",
  "previous_version": "13.9.1",
  "current_version": "13.10.1"
}
```

### POST /sync/all

Fetches and updates all game data from the Data Dragon API.

**Request Body:**
```json
{
  "force": false,
  "background": false
}
```

**Response:**
```json
{
  "status": "success",
  "message": "All data updated to version 13.10.1",
  "entity_type": "all",
  "current_version": "13.10.1"
}
```

### GET /sync/status

Returns current version and update status for game data.

**Response:**
```json
{
  "latest_version": "13.10.1",
  "status": {
    "champions": {
      "current_version": "13.10.1",
      "latest_version": "13.10.1",
      "update_available": false
    },
    "items": {
      "current_version": "13.10.1",
      "latest_version": "13.10.1",
      "update_available": false
    },
    "runes": {
      "current_version": "13.10.1",
      "latest_version": "13.10.1",
      "update_available": false
    },
    "summoner-spells": {
      "current_version": "13.10.1",
      "latest_version": "13.10.1",
      "update_available": false
    }
  }
}
```

## Error Responses

All endpoints can return standard error responses:

```json
{
  "error_code": "CHAMPION_NOT_FOUND",
  "detail": "Champion 'Invalid' not found"
}
```

Common error codes:
- `CHAMPION_NOT_FOUND`: Champion not found
- `ITEM_NOT_FOUND`: Item not found
- `RUNE_PATH_NOT_FOUND`: Rune path not found
- `DATABASE_ERROR`: Error interacting with the database
- `SERVICE_ERROR`: Error in service layer
- `VALIDATION_ERROR`: Input validation error