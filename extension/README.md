# League of Legends Helper Chrome Extension

A Chrome extension that provides information about League of Legends champions, items, and runes with Hextech styling.

## Project Structure

The extension is organized into modular JavaScript files:

- `utils.js` - Utility functions for caching, image error handling, and shared utilities
- `tab-navigation.js` - Handles tab navigation between champions/items and within detail views
- `search-handler.js` - Manages search functionality across the extension
- `champions.js` - Champions-specific functionality (fetching, displaying, filtering)
- `items.js` - Items-specific functionality (fetching, displaying, filtering, detail view)
- `stat-filters.js` - DOM-based filtering for item stats
- `popup.js` - Main initialization and coordination between modules
- `background.js` - Background service worker
- `manifest.json` - Extension configuration
- `popup.html` - Main popup interface
- `styles.css` - Basic Hextech styling
- `item-styles.css` - Additional styles for item components
- `images/` - Icon assets

## Loading Order

The scripts must be loaded in the correct order to ensure dependencies are met:

1. `utils.js` - Base utilities required by all other modules
2. `tab-navigation.js` - Navigation system required by other UI modules
3. `search-handler.js` - Search functionality required by feature modules
4. `champions.js` - Champions feature module
5. `items.js` - Items feature module
6. `stat-filters.js` - Additional item filtering functionality
7. `popup.js` - Main initialization module

## Module Responsibilities

- **utils.js**: Provides core utilities like caching, API handling, image error fallbacks
- **tab-navigation.js**: Manages navigation between main views and tab panels
- **search-handler.js**: Handles search input, filtering, and coordination with feature modules
- **champions.js**: Manages champion data, display, filtering, and detail view
- **items.js**: Manages item data, display, filtering, and detail view
- **stat-filters.js**: Provides DOM-based filtering for items by stats
- **popup.js**: Initializes all modules and handles coordination between them

## Development Setup

### Requirements
- Chrome browser
- Basic knowledge of HTML, CSS, and JavaScript

### Loading the Extension in Chrome
1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (toggle in the top right)
3. Click "Load unpacked" button
4. Select the extension directory containing the manifest.json file
5. The extension should appear in your toolbar

### Debugging
- Click on the "Service Worker" link on the extension card to debug the background script
- Right-click on the extension popup and select "Inspect" to debug the popup

## API Integration

The extension connects to a backend API at `http://localhost:8001/api/v1` to fetch:

- Champion data
- Item data
- Game version
- Asset images (champion splash art, ability icons, item icons)

## Caching Strategy

Data is cached in Chrome's local storage to improve performance:
- Champion and item data is cached for 24 hours
- Individual champion details are cached separately
- Images are handled by the browser's standard caching

## Event System

The extension uses custom events for communication between modules:
- `viewChanged` - Fired when switching between champions and items views
- `championDetailShown` - Fired when a champion's detail view is displayed
- `itemDetailShown` - Fired when an item's detail view is displayed