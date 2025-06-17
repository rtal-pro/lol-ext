# Runes Module Documentation

This document provides information about the runes functionality in the League of Legends Helper extension.

## Overview

The runes module allows users to browse League of Legends rune paths, view detailed information about individual runes, and understand how they work. It features a responsive UI with hextech-styled elements and proper fallback mechanisms for image loading.

## Key Files

- `runes.js` - Main JavaScript file containing the `RunesManager` class and all rune-related functionality
- `rune-styles.css` - CSS styles for runes display
- `test_rune_images.js` - Test script for verifying rune image loading
- `test_rune_images.html` - HTML page for running the rune image test

## Image Loading Strategy

Rune images are loaded directly from the Riot Games Data Dragon CDN using the path information in the rune data. This ensures that images are always up-to-date and don't require manual downloads.

The image loading process follows this cascade:

1. First attempt: Load directly from Data Dragon CDN using the rune's `icon` property
   ```javascript
   const runeIconUrl = rune.icon ? `https://ddragon.leagueoflegends.com/cdn/img/${rune.icon}` : `assets/runes/${rune.id}.png`;
   ```

2. Fallback: If the CDN request fails, try loading from the backend API
   ```javascript
   const apiUrl = `${this.API_BASE_URL}/assets/rune/image/${rune.id}`;
   ```

3. Final fallback: If both CDN and API fail, use a styled placeholder with the rune's initial
   ```html
   <div class="rune-icon-placeholder" style="background-color: ${this.getStyleColor(rune.styleKey)}80">
     <span>${rune.name ? rune.name.charAt(0) : '?'}</span>
   </div>
   ```

## Rune Styles/Paths

The five rune paths are:

1. **Precision** (yellow) - For champions who want to excel at sustained damage and take down even the toughest opponents
2. **Domination** (red) - For champions who want to hunt and eliminate squishy high-priority targets
3. **Sorcery** (purple) - For champions who want to empower their abilities and use spell combos
4. **Resolve** (green) - For champions who want to stand strong in the face of opposition
5. **Inspiration** (teal) - For champions who want to break the rules and use creative tools

Each path has its own color scheme that is applied to style its UI elements.

## Testing

You can test rune image loading by opening the `test_rune_images.html` file in your browser. This will:

1. Fetch rune data from the API
2. Try loading each rune image from the Data Dragon CDN
3. Display the results in a table showing success/failure status
4. Show a preview of successfully loaded images

## Troubleshooting

If images fail to load:

1. Check your internet connection
2. Verify that the Data Dragon CDN is accessible
3. Check the browser console for specific error messages
4. Ensure the backend API is running (for API fallback)
5. Verify that the rune data contains valid `icon` properties

## Implementation Notes

- The rune data is cached to reduce API calls
- Placeholders are shown while images are loading
- Detailed error handling is implemented for all image loading attempts
- Style-specific colors are used for placeholders and styling elements
- Local fallback data is provided in case the API is unavailable