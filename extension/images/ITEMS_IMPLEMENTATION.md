# Items View Implementation

## Overview

The Items view in the League of Legends Helper extension displays items from the Data Dragon API organized by tiers. This document summarizes the implementation details and key components.

## API Integration

The items are fetched from the backend API endpoint:
```
http://localhost:8001/api/v1/items
```

### API Response Structure
The API returns a response with a nested structure:
```json
{
  "tiers": [
    {
      "tier": 1,
      "items": [/* array of items */]
    },
    {
      "tier": 2,
      "items": [/* array of items */]
    },
    // more tiers...
  ]
}
```

### Item Object Structure
Each item in the API response has the following structure:
```json
{
  "id": "1001",
  "name": "Boots of Speed",
  "description": "Slightly increases Movement Speed",
  "tier": 1,
  "gold": {
    "base": 300,
    "total": 300,
    "sell": 210
  },
  "image": {
    "full": "1001.png"
  },
  "stats": {
    "FlatMovementSpeedMod": 25
  },
  "from": [],
  "into": ["3006", "3047", "3020"]
}
```

## Core Functionality

### Data Fetching and Caching
- Items are fetched from the API using the `fetchItems()` function
- Responses are cached in Chrome Storage for performance
- Cache invalidation occurs after 24 hours

### Item Organization
- Items are categorized by tier using the `organizeItemsByTier()` function
- Tiers are mapped to categories: starter, basic, epic, legendary, mythic
- Both numeric and string tier values are handled

### Item Filtering
- Users can filter items by tier using the tier buttons
- Text search is implemented to filter items by name, description, and stats
- The filter logic is in the `filterItems()` function

### Item Display
- Items are displayed in a grid layout with item cards
- Each card shows the item image, name, and price
- The display logic is in the `displayItems()` function

### Item Detail View
- Clicking an item shows a detailed view
- Details include: name, tier, gold cost, description, stats
- Recipe tree shows components and "builds into" relationships
- Recipe cost calculations are displayed

## UI Components

### Tier Navigation
```html
<div class="tier-buttons">
  <button class="tier-button active" data-tier="all">All</button>
  <button class="tier-button" data-tier="starter">Starter</button>
  <button class="tier-button" data-tier="basic">Basic</button>
  <button class="tier-button" data-tier="epic">Epic</button>
  <button class="tier-button" data-tier="legendary">Legendary</button>
  <button class="tier-button" data-tier="mythic">Mythic</button>
</div>
```

### Item Card
```html
<div class="item-card" data-id="${item.id}">
  <div class="item-image">
    <img src="${imageUrl}" alt="${item.name}">
  </div>
  <div class="item-name">${item.name}</div>
  <div class="item-price">${priceText}</div>
</div>
```

### Item Detail View
The detail view shows:
- Item image and basic info
- Detailed description
- Item stats with icons
- Recipe diagram showing components
- "Builds into" section showing items that use this item

## Key Functions

1. `fetchItems()` - Fetches items data from the API
2. `organizeItemsByTier()` - Categorizes items by tier
3. `filterItems()` - Filters items based on search text and tier
4. `displayItems()` - Renders items in the UI
5. `showItemDetail()` - Shows the detailed view for a specific item
6. `displayItemDetail()` - Renders item details in the UI

## Debugging Features

- Detailed console logging for API responses
- Visual debug information when no items are found
- Tier indicators on item cards

## Styling

Items use a Hextech-inspired design system with:
- Gold accents for borders and highlights
- Dark blue backgrounds
- Hover effects for interactive elements
- Responsive grid layout

## Future Improvements

1. Add item tags/categories for additional filtering
2. Implement item comparison functionality
3. Add recommended champions for each item
4. Improve recipe tree visualization for complex items
5. Add item set creation and export