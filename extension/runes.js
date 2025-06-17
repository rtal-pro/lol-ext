// Runes-related functionality for League of Legends Helper extension

// Requires utils.js to be loaded first

class RunesManager {
  constructor() {
    // Get references to DOM elements
    this.runesList = document.getElementById('runes-list');
    this.loadingElement = document.getElementById('loading-runes');
    this.errorElement = document.getElementById('error-runes');
    this.noResultsElement = document.getElementById('no-results-runes');
    this.runeStyleDetailElement = document.getElementById('rune-style-detail');
    this.runeDetailElement = document.getElementById('rune-detail');
    this.runeBuilderElement = document.getElementById('rune-builder');
    this.backToStylesButton = document.getElementById('back-to-styles-button');
    this.backToStyleButton = document.getElementById('back-to-style-button');
    this.backFromBuilderButton = document.getElementById('back-from-builder-button');
    this.resetSearchRunes = document.getElementById('reset-search-runes');
    
    // Initialize state
    this.runeData = null; // Complete rune data from API (includes paths array)
    this.allStyles = []; // All rune styles from API (the paths array)
    this.allRunes = []; // Flattened array of all runes
    this.runesByStyle = {}; // Runes organized by style
    this.currentStyle = null; // Current rune style being viewed
    this.currentRune = null; // Current rune being viewed
    this.API_BASE_URL = window.LOLUtils.API_BASE_URL;
    
    // Rune page builder state
    this.currentRunePage = {
      primaryStyle: null,
      secondaryStyle: null,
      selectedRunes: [] // Array of selected rune IDs
    };
    
    // Filter state
    this.filter = {
      searchText: '',
      activeStyles: new Set(),
      tags: new Set() // For filtering by gameplay tags extracted from descriptions
    };
    
    // Set up event handlers
    this._setupEventHandlers();
  }
  
  _setupEventHandlers() {
    // Back button from style detail to main list
    if (this.backToStylesButton) {
      this.backToStylesButton.addEventListener('click', () => {
        this.showRunesList();
      });
    }
    
    // Back button from rune detail to style detail
    if (this.backToStyleButton) {
      this.backToStyleButton.addEventListener('click', () => {
        this.showRuneStyleDetail(this.currentStyle);
      });
    }
    
    // Back button from builder to main list
    if (this.backFromBuilderButton) {
      this.backFromBuilderButton.addEventListener('click', () => {
        this.showRunesList();
      });
    }
    
    // Style filter buttons
    const styleFilters = document.querySelectorAll('.style-filter');
    styleFilters.forEach(button => {
      button.addEventListener('click', () => {
        // Get the style from the button
        const style = button.getAttribute('data-style');
        
        // Toggle active state
        button.classList.toggle('active');
        
        // Update filter state
        if (this.filter.activeStyles.has(style)) {
          this.filter.activeStyles.delete(style);
        } else {
          this.filter.activeStyles.add(style);
        }
        
        // Update filters and display
        this.updateActiveFilters();
        this.filterAndDisplayRunes();
      });
    });
    
    // Add search input handler
    const searchInput = document.getElementById('rune-search-input');
    if (searchInput) {
      searchInput.addEventListener('input', () => {
        // Update search text filter
        this.filter.searchText = searchInput.value.trim();
        
        // Show/hide clear button
        const searchClear = document.getElementById('rune-search-clear');
        if (searchClear) {
          searchClear.style.display = this.filter.searchText ? 'block' : 'none';
        }
        
        // Update filters and display
        this.updateActiveFilters();
        this.filterAndDisplayRunes();
      });
    }
    
    // Set up search clear button
    const searchClear = document.getElementById('rune-search-clear');
    if (searchClear) {
      searchClear.addEventListener('click', () => {
        const searchInput = document.getElementById('rune-search-input');
        if (searchInput) {
          searchInput.value = '';
          this.filter.searchText = '';
          searchClear.style.display = 'none';
          
          this.updateActiveFilters();
          this.filterAndDisplayRunes();
          
          // Focus back on search input
          searchInput.focus();
        }
      });
    }
    
    // Reset search button
    if (this.resetSearchRunes) {
      this.resetSearchRunes.addEventListener('click', () => {
        this.resetAllFilters();
      });
    }
    
    // Clear all filters button
    const clearFiltersButton = document.getElementById('clear-rune-filters');
    if (clearFiltersButton) {
      clearFiltersButton.addEventListener('click', () => {
        this.resetAllFilters();
      });
    }
  }
  
  // Update the active filters display
  updateActiveFilters() {
    // Implementation will be added later
    console.log('Updating active filters...');
  }
  
  // Reset all filters
  resetAllFilters() {
    // Reset search input
    const searchInput = document.getElementById('rune-search-input');
    if (searchInput) {
      searchInput.value = '';
    }
    this.filter.searchText = '';
    
    // Reset style filters
    this.filter.activeStyles.clear();
    const styleFilters = document.querySelectorAll('.style-filter');
    styleFilters.forEach(btn => btn.classList.remove('active'));
    
    // Reset tag filters
    this.filter.tags.clear();
    const tagFilters = document.querySelectorAll('.tag-filter');
    tagFilters.forEach(btn => btn.classList.remove('active'));
    
    // Update UI and display
    this.updateActiveFilters();
    this.filterAndDisplayRunes();
  }
  
  // Function to fetch runes data with caching
  async fetchRunes() {
    try {
      // Show loading state
      this.loadingElement.style.display = 'block';
      this.errorElement.style.display = 'none';
      this.noResultsElement.style.display = 'none';
      
      // Check if we have cached runes data
      const runes = await window.LOLUtils.getCachedRunes();
      
      if (runes) {
        // Use cached data
        console.log('Using cached runes data');
        this.runeData = runes; // Store the complete response
        this.allStyles = Array.isArray(runes.paths) ? runes.paths : runes; // Extract paths array if available
        this.processRunes();
        return;
      }
      
      // No cache or expired cache, fetch from API
      console.log('Fetching runes from API');
      try {
        const response = await fetch(`${this.API_BASE_URL}/runes`);
        
        if (!response.ok) {
          throw new Error(`API request failed with status ${response.status}`);
        }
        
        const data = await response.json();
        this.runeData = data; // Store the complete response
        
        console.log('API response received:', typeof data);
        console.log('Has paths property:', data && data.paths ? 'yes' : 'no');
        
        // Log the API response structure for debugging
        console.log('API response structure:', {
          isArray: Array.isArray(data),
          hasPathsProperty: data && data.paths ? true : false,
          topLevelKeys: data ? Object.keys(data) : []
        });
        
        // Handle the RuneTreeResponse format from backend
        if (data && data.paths && Array.isArray(data.paths)) {
          console.log(`API returned proper format with ${data.paths.length} paths`);
          this.allStyles = data.paths;
        } 
        // Handle case where API returns an array directly
        else if (data && Array.isArray(data)) {
          console.log('API returned direct array of styles');
          this.allStyles = data;
        }
        // Handle object response with non-standard structure 
        else if (data && typeof data === 'object') {
          // Try all possible property names that might contain rune paths
          const possibleStylesProperties = ['paths', 'styles', 'runePaths', 'runes', 'data'];
          
          let foundStyles = false;
          
          // Check for known property names that might contain the paths
          for (const prop of possibleStylesProperties) {
            if (data[prop]) {
              if (Array.isArray(data[prop]) && data[prop].length > 0) {
                console.log(`Found paths in '${prop}' property`);
                this.allStyles = data[prop];
                foundStyles = true;
                break;
              } 
              // Check if it's a nested object with paths
              else if (typeof data[prop] === 'object' && data[prop].paths && Array.isArray(data[prop].paths)) {
                console.log(`Found nested paths in '${prop}.paths' property`);
                this.allStyles = data[prop].paths;
                foundStyles = true;
                break;
              }
            }
          }
          
          // If still not found, look for any array property that has rune-like objects
          if (!foundStyles) {
            const possibleArrayProps = Object.keys(data).filter(key => 
              Array.isArray(data[key]) && data[key].length > 0 &&
              data[key][0] && typeof data[key][0] === 'object' &&
              (data[key][0].slots || data[key][0].name || data[key][0].key || data[key][0].id)
            );
            
            if (possibleArrayProps.length > 0) {
              console.log(`Using array from '${possibleArrayProps[0]}' property`);
              this.allStyles = data[possibleArrayProps[0]];
              foundStyles = true;
            }
          }
          
          // Last resort: if the data itself looks like a style object with slots
          if (!foundStyles && data.slots && Array.isArray(data.slots)) {
            console.log('Data itself appears to be a single path, wrapping in array');
            this.allStyles = [data];
            foundStyles = true;
          }
          
          // If we still can't find valid styles, use local data
          if (!foundStyles) {
            console.warn('Could not find valid styles in API response, using local data');
            this.allStyles = this._getLocalRuneData();
          }
        } 
        // If API data is not valid, use local data as fallback
        else {
          console.warn('API data format unexpected, using local data');
          this.allStyles = this._getLocalRuneData();
        }
      } catch (error) {
        // If API request fails, use local data
        console.warn('API request failed, using local rune data:', error);
        this.allStyles = this._getLocalRuneData();
      }
      
      // Hide loading state
      this.loadingElement.style.display = 'none';
      
      // Log final data structure for debugging
      console.log('Final allStyles structure:', 
        Array.isArray(this.allStyles) ? 
        `Array with ${this.allStyles.length} items` : 
        typeof this.allStyles);
      
      if (!Array.isArray(this.allStyles)) {
        console.error('allStyles is still not an array, using local data as fallback');
        this.allStyles = this._getLocalRuneData();
      }
      
      // Save to cache - save the complete response if available
      await window.LOLUtils.cacheRunes(this.runeData || this.allStyles);
      
      // Process and display runes
      this.processRunes();
    } catch (error) {
      console.error('Error fetching runes:', error);
      
      // Hide loading state and show error
      this.loadingElement.style.display = 'none';
      this.errorElement.style.display = 'block';
      this.errorElement.textContent = `Error loading runes: ${error.message}`;
    }
  }
  
  // Process runes data to organize it
  processRunes() {
    // Ensure allStyles is an array
    if (!this.allStyles || !Array.isArray(this.allStyles)) {
      console.error('this.allStyles is not an array:', this.allStyles);
      this.allStyles = [];
      this.errorElement.style.display = 'block';
      this.errorElement.textContent = 'Error processing runes data: Invalid data format';
      this.loadingElement.style.display = 'none';
      return;
    }
    
    // If we have no styles, show error
    if (this.allStyles.length === 0) {
      console.error('No rune styles found in data');
      this.errorElement.style.display = 'block';
      this.errorElement.textContent = 'Error: No rune styles found';
      this.loadingElement.style.display = 'none';
      return;
    }
    
    console.log(`Processing ${this.allStyles.length} rune styles...`);
    
    // Hide loading state
    this.loadingElement.style.display = 'none';
    
    // Ensure the runes list is visible
    if (this.runesList) {
      this.runesList.style.display = 'block';
    }
    
    // Create a flattened array of all runes for searching
    this.allRunes = [];
    this.runesByStyle = {};
    
    // Process each style
    this.allStyles.forEach(style => {
      // Validate that style has the required properties
      if (!style || !style.key || !style.id || !style.name) {
        console.warn('Invalid style object found:', style);
        return; // Skip this style
      }
      
      const styleKey = style.key;
      this.runesByStyle[styleKey] = [];
      
      // Process each slot (row) of runes in the style
      if (style.slots && Array.isArray(style.slots)) {
        style.slots.forEach((slot, slotIndex) => {
          // Check for valid slot
          if (!slot || !slot.runes) {
            console.warn(`Invalid slot in style ${styleKey}:`, slot);
            return; // Skip this slot
          }
          
          if (Array.isArray(slot.runes)) {
            slot.runes.forEach(rune => {
              // Validate rune object
              if (!rune || !rune.id || !rune.name) {
                console.warn(`Invalid rune in style ${styleKey}:`, rune);
                return; // Skip this rune
              }
              
              // Add style and slot information to each rune
              rune.styleId = style.id;
              rune.styleKey = style.key;
              rune.styleName = style.name;
              rune.styleIcon = style.icon;
              rune.slotIndex = slotIndex;
              
              // Make sure required properties exist, even if empty
              rune.shortDesc = rune.shortDesc || '';
              rune.longDesc = rune.longDesc || '';
              
              // Add to the flattened array
              this.allRunes.push(rune);
              
              // Add to style-specific array
              this.runesByStyle[styleKey].push(rune);
            });
          }
        });
      } else {
        console.warn(`Style ${styleKey} has no valid slots array`);
      }
    });
    
    console.log(`Processed ${this.allRunes.length} total runes across ${this.allStyles.length} styles`);
    
    // If we didn't find any runes, show error
    if (this.allRunes.length === 0) {
      console.error('No runes found in the data');
      this.errorElement.style.display = 'block';
      this.errorElement.textContent = 'Error: No runes found in the data';
      return;
    }
    
    // Extract common tags from rune descriptions for filtering
    this.extractRuneTags();
    
    // Display runes
    this.displayRuneStyles();
  }
  
  // Extract common tags from rune descriptions
  extractRuneTags() {
    const tagMap = {};
    const commonTags = [
      'damage', 'heal', 'shield', 'movement', 'cooldown', 'gold',
      'crowd control', 'stun', 'slow', 'immobilize', 'adaptive',
      'attack speed', 'resistances', 'utility'
    ];
    
    // Count occurrences of tags in rune descriptions
    this.allRunes.forEach(rune => {
      const description = (rune.longDesc || rune.shortDesc || '').toLowerCase();
      
      commonTags.forEach(tag => {
        if (description.includes(tag)) {
          tagMap[tag] = (tagMap[tag] || 0) + 1;
        }
      });
    });
    
    // Sort tags by frequency
    const sortedTags = Object.keys(tagMap).sort((a, b) => tagMap[b] - tagMap[a]);
    
    // Take top 8 tags for the UI
    const topTags = sortedTags.slice(0, 8);
    
    // Create tag filter UI
    this.createTagFilters(topTags);
    
    console.log('Extracted tags:', topTags);
  }
  
  // Create tag filter buttons
  createTagFilters(tags) {
    const tagContainer = document.querySelector('.rune-tags-filter');
    if (!tagContainer) return;
    
    // Clear existing tag filters
    tagContainer.innerHTML = '';
    
    // Create tag filter buttons
    tags.forEach(tag => {
      const formattedTag = tag.charAt(0).toUpperCase() + tag.slice(1);
      const button = document.createElement('button');
      button.className = 'tag-filter';
      button.setAttribute('data-tag', tag);
      button.textContent = formattedTag;
      
      // Add click event
      button.addEventListener('click', () => {
        button.classList.toggle('active');
        
        // Update filter state
        if (this.filter.tags.has(tag)) {
          this.filter.tags.delete(tag);
        } else {
          this.filter.tags.add(tag);
        }
        
        // Update display
        this.updateActiveFilters();
        this.filterAndDisplayRunes();
      });
      
      tagContainer.appendChild(button);
    });
  }
  
  // Filter runes based on current filters
  filterRunes() {
    // Start with all runes
    let runes = this.allRunes;
    
    // Filter by style if active styles are selected
    if (this.filter.activeStyles.size > 0) {
      runes = runes.filter(rune => {
        return this.filter.activeStyles.has(rune.styleName);
      });
    }
    
    // Filter by search text
    if (this.filter.searchText) {
      const searchText = this.filter.searchText.toLowerCase();
      runes = runes.filter(rune => {
        return rune.name.toLowerCase().includes(searchText) || 
               (rune.shortDesc && rune.shortDesc.toLowerCase().includes(searchText)) ||
               (rune.longDesc && rune.longDesc.toLowerCase().includes(searchText));
      });
    }
    
    // Filter by tags
    if (this.filter.tags.size > 0) {
      runes = runes.filter(rune => {
        const description = ((rune.longDesc || '') + ' ' + (rune.shortDesc || '')).toLowerCase();
        return Array.from(this.filter.tags).some(tag => description.includes(tag));
      });
    }
    
    return runes;
  }
  
  // Display rune styles in the main view - EXACT CHAMPION CARD STYLE
  displayRuneStyles() {
    // Get the runes container
    const runesContainer = this.runesList.querySelector('.runes-container');
    if (!runesContainer) return;
    
    // Clear previous content
    runesContainer.innerHTML = '';
    
    // Create a card for each style - EXACT CHAMPION CARD STYLE
    this.allStyles.forEach(style => {
      const styleCard = document.createElement('div');
      styleCard.className = `rune-style-card rune-style-${style.key.toLowerCase()}`;
      styleCard.setAttribute('data-style-id', style.id);
      styleCard.setAttribute('data-style-key', style.key);
      
      // Create HTML structure exactly like champion cards
      styleCard.innerHTML = `
        <div class="rune-style-icon-container">
          <div class="style-icon-placeholder">
            <span>${style.key.charAt(0)}</span>
          </div>
          <img src="" alt="${style.name}" class="rune-style-icon" style="display: none;">
        </div>
        <div class="rune-style-info">
          <div class="rune-style-name">${style.name}</div>
          <div class="rune-style-desc">${this.getStyleDescription(style.key)}</div>
          <div class="rune-path-badges">
            <span class="rune-style-path-badge path-badge-${style.key.toLowerCase()}">Path</span>
          </div>
        </div>
      `;
      
      // Get the image element and placeholder
      const imgElement = styleCard.querySelector('.rune-style-icon');
      const placeholder = styleCard.querySelector('.style-icon-placeholder');
      
      // Set up successful load handler
      imgElement.addEventListener('load', () => {
        // Hide placeholder and show image when loaded
        placeholder.style.display = 'none';
        imgElement.style.display = 'block';
      });
      
      // Set up error handler
      imgElement.addEventListener('error', () => {
        // Just use the placeholder after an error
        placeholder.style.display = 'flex';
        imgElement.style.display = 'none';
      });
      
      // Use DataDragon CDN directly for rune path images
      const styleIconUrl = `https://ddragon.leagueoflegends.com/cdn/img/${style.icon}`;
      imgElement.src = styleIconUrl;
      
      // Add click event to show style detail
      styleCard.addEventListener('click', () => {
        this.showRuneStyleDetail(style);
      });
      
      // Add card to container
      runesContainer.appendChild(styleCard);
    });
    
    // Add count info
    const countInfo = document.createElement('div');
    countInfo.className = 'pagination-info';
    countInfo.textContent = `Showing ${this.allStyles.length} rune paths`;
    runesContainer.appendChild(countInfo);
  }
  
  // Filter and display runes based on current filters
  filterAndDisplayRunes() {
    const filteredRunes = this.filterRunes();
    console.log(`Filtered to ${filteredRunes.length} runes`);
    
    // Show or hide "no results" message
    if (filteredRunes.length === 0) {
      this.noResultsElement.style.display = 'block';
      this.runesList.style.display = 'none';
    } else {
      this.noResultsElement.style.display = 'none';
      this.runesList.style.display = 'block';
      
      // Display filtered runes or go back to displaying styles
      if (this.filter.activeStyles.size > 0 || this.filter.searchText || this.filter.tags.size > 0) {
        this.displayFilteredRunes(filteredRunes);
      } else {
        this.displayRuneStyles();
      }
    }
  }
  
  // Display filtered runes directly (bypassing styles)
  displayFilteredRunes(runes) {
    // Get the runes container
    const runesContainer = this.runesList.querySelector('.runes-container');
    if (!runesContainer) return;
    
    // Clear previous content
    runesContainer.innerHTML = '';
    
    // Create a card for each rune in the new champion-style layout
    runes.forEach(rune => {
      const runeCard = this.createRuneCard(rune);
      runesContainer.appendChild(runeCard);
    });
    
    // Add count info
    const countInfo = document.createElement('div');
    countInfo.className = 'pagination-info';
    countInfo.textContent = `Showing ${runes.length} of ${this.allRunes.length} runes`;
    
    // If filters are active, add explanation of filter logic
    if (this.filter.activeStyles.size > 0 || this.filter.tags.size > 0 || this.filter.searchText) {
      let filterText = [];
      
      if (this.filter.activeStyles.size > 0) {
        filterText.push(`paths: ${Array.from(this.filter.activeStyles).join(', ')}`);
      }
      
      if (this.filter.tags.size > 0) {
        filterText.push(`tags: ${Array.from(this.filter.tags).join(', ')}`);
      }
      
      if (this.filter.searchText) {
        filterText.push(`search: "${this.filter.searchText}"`);
      }
      
      countInfo.textContent += ` (filtered by ${filterText.join('; ')})`;
    }
    
    runesContainer.appendChild(countInfo);
  }
  
  // Create a rune card element - EXACT CHAMPION CARD STYLE
  createRuneCard(rune) {
    const runeCard = document.createElement('div');
    runeCard.className = 'rune-card';
    runeCard.setAttribute('data-rune-id', rune.id);
    runeCard.setAttribute('data-rune-key', rune.key);
    runeCard.setAttribute('data-style-key', rune.styleKey);
    
    // Get style-specific class
    const styleClass = `rune-${rune.styleKey.toLowerCase()}`;
    runeCard.classList.add(styleClass);
    
    // Format the short description without HTML tags
    const shortDesc = rune.shortDesc ? this.stripHtmlTags(rune.shortDesc) : '';
    
    // Get slot/tier name
    const slotNames = ['Keystone', 'Tier 1', 'Tier 2', 'Tier 3'];
    const slotName = slotNames[rune.slotIndex] || `Tier ${rune.slotIndex + 1}`;
    
    // Create EXACT champion card style layout
    runeCard.innerHTML = `
      <div class="rune-icon-container">
        <div class="rune-icon-placeholder">
          <span>${rune.name ? rune.name.charAt(0) : '?'}</span>
        </div>
        <img src="" alt="${rune.name}" class="rune-icon" style="display: none;">
      </div>
      <div class="rune-info">
        <div class="rune-name">${rune.name}</div>
        <div class="rune-tooltip">${shortDesc}</div>
        <div class="rune-tags">
          <span class="rune-style-path-badge path-badge-${rune.styleKey.toLowerCase()}">${rune.styleKey}</span>
          <span class="rune-slot-badge">${slotName}</span>
        </div>
      </div>
    `;
    
    // Now set up the actual image with load handling
    const imgElement = runeCard.querySelector('.rune-icon');
    const placeholder = runeCard.querySelector('.rune-icon-placeholder');
    
    // Set up successful load handler
    imgElement.addEventListener('load', () => {
      // Hide placeholder and show image when loaded
      placeholder.style.display = 'none';
      imgElement.style.display = 'block';
    });
    
    // Set up error handler
    imgElement.addEventListener('error', () => {
      // Just use the placeholder after an error
      placeholder.style.display = 'flex';
      imgElement.style.display = 'none';
    });
    
    // Use DataDragon CDN directly for rune images
    const runeIconUrl = rune.icon ? `https://ddragon.leagueoflegends.com/cdn/img/${rune.icon}` : `assets/runes/${rune.id}.png`;
    imgElement.src = runeIconUrl;
    
    // Add click event to show rune detail
    runeCard.addEventListener('click', () => {
      this.showRuneDetail(rune);
    });
    
    return runeCard;
  }
  
  // Show rune style detail
  showRuneStyleDetail(style) {
    // Set current style
    this.currentStyle = style;
    
    // Hide runes list, show style detail
    this.runesList.style.display = 'none';
    this.runeStyleDetailElement.style.display = 'block';
    this.runeDetailElement.style.display = 'none';
    this.runeBuilderElement.style.display = 'none';
    
    // Hide the search container in detail view
    const searchContainer = document.getElementById('runes-search-container');
    if (searchContainer) searchContainer.style.display = 'none';
    
    // Set style name and image
    const styleNameElement = this.runeStyleDetailElement.querySelector('.style-name');
    if (styleNameElement) styleNameElement.textContent = style.name;
    
    // Set style description with detailed information
    const styleDescElement = this.runeStyleDetailElement.querySelector('.style-description');
    if (styleDescElement) {
      const detailedDescription = this.getDetailedStyleDescription(style.key);
      styleDescElement.textContent = detailedDescription;
    }
    const styleIconElement = this.runeStyleDetailElement.querySelector('.style-icon');
    
    // Replace the image with a container that has both placeholder and image
    const styleIconContainer = styleIconElement.parentElement;
    styleIconContainer.innerHTML = `
      <div class="style-detail-placeholder" style="
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background-color: ${this.getStyleColor(style.key)}40;
        display: flex;
        align-items: center;
        justify-content: center;
        color: ${this.getStyleColor(style.key)};
        font-weight: bold;
        font-size: 24px;
      ">
        <span>${style.name.charAt(0)}</span>
      </div>
      <img src="" alt="${style.name}" class="style-icon" style="display: none;">
    `;
    
    // Get the new image element and placeholder
    const newIconElement = styleIconContainer.querySelector('.style-icon');
    const placeholder = styleIconContainer.querySelector('.style-detail-placeholder');
    
    // Set up successful load handler
    newIconElement.addEventListener('load', () => {
      // Hide placeholder and show image when loaded
      placeholder.style.display = 'none';
      newIconElement.style.display = 'block';
    });
    
    // Set up error handler
    newIconElement.addEventListener('error', () => {
      // Just use the placeholder
      placeholder.style.display = 'flex';
      newIconElement.style.display = 'none';
    });
    
    // Use DataDragon CDN directly for style images
    const styleIconUrl = style.icon ? 
      `https://ddragon.leagueoflegends.com/cdn/img/${style.icon}` : 
      `assets/runes/${style.id}.png`;
    newIconElement.src = styleIconUrl;
    
    // Add back button style reference
    if (this.backToStylesButton) {
      const backArrow = this.backToStylesButton.querySelector('span');
      const backText = this.backToStylesButton.querySelector('span + span');
      
      if (backArrow) backArrow.textContent = '←';
      if (backText) backText.textContent = 'Back to Rune Styles';
    }
    
    // Fill each slot (row) with its runes
    if (style.slots && Array.isArray(style.slots)) {
      style.slots.forEach((slot, slotIndex) => {
        // Get the appropriate row container
        let rowContainer;
        if (slotIndex === 0) {
          rowContainer = this.runeStyleDetailElement.querySelector('.keystones-row');
        } else {
          rowContainer = this.runeStyleDetailElement.querySelector(`.minor-row-${slotIndex}`);
        }
        
        // Clear previous content
        if (rowContainer) {
          rowContainer.innerHTML = '';
          
          // Add runes to the row
          if (slot.runes && Array.isArray(slot.runes)) {
            slot.runes.forEach(rune => {
              // Add style info to the rune object
              rune.styleId = style.id;
              rune.styleKey = style.key;
              rune.styleName = style.name;
              rune.styleIcon = style.icon;
              rune.slotIndex = slotIndex;
              
              // Create rune card
              const runeCard = this.createRuneCard(rune);
              rowContainer.appendChild(runeCard);
            });
          }
        }
      });
    }
    
    // Adjust style-specific colors and theming
    this.applyStyleTheming(style);
  }
  
  // Apply style-specific colors and theming
  applyStyleTheming(style) {
    // Get style key in lowercase
    const styleKey = style.key.toLowerCase();
    
    // Get style-specific variables
    const styleVars = {
      domination: {
        color: '#ca3e3f',
        light: '#e16364',
        dark: '#9e2c2d'
      },
      inspiration: {
        color: '#49aab9',
        light: '#7ccad5',
        dark: '#32818e'
      },
      precision: {
        color: '#c8aa6e',
        light: '#e0c893',
        dark: '#9e8654'
      },
      resolve: {
        color: '#4d8b7c',
        light: '#75b3a2',
        dark: '#37665b'
      },
      sorcery: {
        color: '#9e7cc9',
        light: '#bca1dd',
        dark: '#7859a0'
      }
    };
    
    // Get colors for current style
    const colors = styleVars[styleKey] || styleVars.precision;
    
    // Apply to style detail elements
    const styleHeader = this.runeStyleDetailElement.querySelector('.rune-style-header');
    if (styleHeader) {
      styleHeader.style.borderLeft = `4px solid ${colors.color}`;
      styleHeader.style.boxShadow = `0 0 10px ${colors.color}40`;
    }
    
    // Apply to slot containers
    const keystoneSlot = this.runeStyleDetailElement.querySelector('.keystone-slot');
    if (keystoneSlot) {
      keystoneSlot.style.borderLeft = `4px solid ${colors.color}`;
    }
    
    const minorSlots = this.runeStyleDetailElement.querySelectorAll('.minor-slot');
    minorSlots.forEach(slot => {
      slot.style.borderLeft = `3px solid ${colors.light}`;
    });
  }
  
  // Show individual rune detail
  showRuneDetail(rune) {
    // Set current rune
    this.currentRune = rune;
    
    // Hide other views, show rune detail
    this.runesList.style.display = 'none';
    this.runeStyleDetailElement.style.display = 'none';
    this.runeDetailElement.style.display = 'block';
    this.runeBuilderElement.style.display = 'none';
    
    // Set rune name and image
    this.runeDetailElement.querySelector('.rune-detail-name').textContent = rune.name;
    
    // Create a placeholder first
    const runeDetailImageContainer = this.runeDetailElement.querySelector('.rune-detail-image');
    runeDetailImageContainer.innerHTML = `
      <div class="rune-img-placeholder" style="
        width: 100%; 
        height: 100%; 
        background-color: ${this.getStyleColor(rune.styleKey)}80;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        font-size: 28px;
      ">
        <span>${rune.name ? rune.name.charAt(0) : '?'}</span>
      </div>
      <img src="" alt="${rune.name}" class="rune-img" style="display: none;">
    `;
    
    // Get the image element
    const runeImgElement = runeDetailImageContainer.querySelector('.rune-img');
    const placeholder = runeDetailImageContainer.querySelector('.rune-img-placeholder');
    
    // Set up successful load handler
    runeImgElement.addEventListener('load', () => {
      // Hide placeholder and show image when loaded
      placeholder.style.display = 'none';
      runeImgElement.style.display = 'block';
    });
    
    // Set up error handler
    runeImgElement.addEventListener('error', () => {
      // Just use the placeholder
      placeholder.style.display = 'flex';
      runeImgElement.style.display = 'none';
    });
    
    // Use DataDragon CDN directly for rune images
    const runeIconUrl = rune.icon ? `https://ddragon.leagueoflegends.com/cdn/img/${rune.icon}` : `assets/runes/${rune.id}.png`;
    runeImgElement.src = runeIconUrl;
    
    // Find the style object to get its icon
    const style = this.allStyles.find(s => s.id === rune.styleId);
    
    // Set style indicator
    const styleIndicator = this.runeDetailElement.querySelector('.rune-style-indicator');
    styleIndicator.innerHTML = `
      <div class="style-indicator-placeholder" style="
        width: 100%; 
        height: 100%; 
        background-color: ${this.getStyleColor(rune.styleKey)};
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
      "></div>
      <img src="" 
           alt="${rune.styleName}" 
           style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: none;">
    `;
    
    // Add handler for style indicator image
    const styleImgElement = styleIndicator.querySelector('img');
    const stylePlaceholder = styleIndicator.querySelector('.style-indicator-placeholder');
    
    if (styleImgElement) {
      // Set up successful load handler
      styleImgElement.addEventListener('load', () => {
        stylePlaceholder.style.display = 'none';
        styleImgElement.style.display = 'block';
      });
      
      // Set up error handler
      styleImgElement.addEventListener('error', () => {
        stylePlaceholder.style.display = 'flex';
        styleImgElement.style.display = 'none';
      });
      
      // Use DataDragon CDN directly for style images
      const styleIconUrl = style && style.icon ? 
        `https://ddragon.leagueoflegends.com/cdn/img/${style.icon}` : 
        `assets/runes/${rune.styleId}.png`;
      styleImgElement.src = styleIconUrl;
    }
    
    // Set style badge
    const styleBadge = this.runeDetailElement.querySelector('.rune-style-badge');
    if (styleBadge) {
      styleBadge.textContent = rune.styleName;
      styleBadge.style.backgroundColor = this.getStyleColor(rune.styleKey);
    }
    
    // Set slot badge
    const slotBadge = this.runeDetailElement.querySelector('.rune-slot-badge');
    if (slotBadge) {
      const slotNames = ['Keystone', 'Tier 1', 'Tier 2', 'Tier 3'];
      slotBadge.textContent = slotNames[rune.slotIndex] || `Slot ${rune.slotIndex + 1}`;
    }
    
    // Update back button to reference style
    if (this.backToStyleButton) {
      const styleNameElement = this.backToStyleButton.querySelector('.style-name');
      if (styleNameElement) {
        styleNameElement.textContent = rune.styleName;
      }
    }
    
    // Set rune descriptions
    const shortDescElement = this.runeDetailElement.querySelector('.rune-short-desc');
    if (shortDescElement) {
      shortDescElement.innerHTML = this.formatRuneDescription(rune.shortDesc || '');
    }
    
    const longDescElement = this.runeDetailElement.querySelector('.rune-long-desc');
    if (longDescElement) {
      longDescElement.innerHTML = this.formatRuneDescription(rune.longDesc || '');
    }
    
    // Find similar runes and champions that use this rune
    this.populateSimilarRunes(rune);
    this.populateRelatedChampions(rune);
    
    // Dispatch event to notify that rune detail view is shown
    document.dispatchEvent(new CustomEvent('runeDetailShown', {
      detail: { runeId: rune.id }
    }));
  }
  
  // Format rune description with highlighting and icons
  formatRuneDescription(description) {
    if (!description) return '';
    
    // Replace HTML tags with appropriate formatting
    let formatted = description;
    
    // Replace adaptive damage
    formatted = formatted.replace(/<lol-uikit-tooltipped-keyword key='LinkTooltip_Description_AdaptiveDmg'>(.+?)<\/lol-uikit-tooltipped-keyword>/g, '<span class="adaptive-damage">$1</span>');
    
    // Replace other tooltipped keywords
    formatted = formatted.replace(/<lol-uikit-tooltipped-keyword key='[^']+'>(.+?)<\/lol-uikit-tooltipped-keyword>/g, '<span class="keyword">$1</span>');
    
    // Replace damage types and values
    formatted = formatted.replace(/(\d+(?:\.\d+)?(?:%)?(?:\s+to\s+\d+(?:\.\d+)?(?:%)?)?)\s+(physical damage|Physical Damage)/gi, '<span class="physical-damage">$1 physical damage</span>');
    formatted = formatted.replace(/(\d+(?:\.\d+)?(?:%)?(?:\s+to\s+\d+(?:\.\d+)?(?:%)?)?)\s+(magic damage|Magic Damage)/gi, '<span class="magic-damage">$1 magic damage</span>');
    formatted = formatted.replace(/(\d+(?:\.\d+)?(?:%)?(?:\s+to\s+\d+(?:\.\d+)?(?:%)?)?)\s+(true damage|True Damage)/gi, '<span class="true-damage">$1 true damage</span>');
    
    // Highlight stat keywords
    formatted = formatted.replace(/\b(health|armor|magic resist|attack damage|ability power|attack speed|move speed|movement speed)\b/gi, '<span class="keyword">$1</span>');
    
    // Replace font tags with spans
    formatted = formatted.replace(/<font color='([^']+)'>(.+?)<\/font>/g, '<span style="color: $1">$2</span>');
    
    return formatted;
  }
  
  // Populate similar runes section
  populateSimilarRunes(rune) {
    const similarRunesGrid = this.runeDetailElement.querySelector('.similar-runes-grid');
    if (!similarRunesGrid) return;
    
    // Clear previous content
    similarRunesGrid.innerHTML = '';
    
    // Find similar runes (from same slot, or with similar keywords)
    const similarRunes = this.findSimilarRunes(rune);
    
    // Create elements for similar runes
    similarRunes.forEach(similarRune => {
      const runeElement = document.createElement('div');
      runeElement.className = 'similar-rune-icon';
      runeElement.setAttribute('data-rune-id', similarRune.id);
      runeElement.setAttribute('title', similarRune.name);
      
      // Create a styled placeholder with the rune's initial
      const bgColor = this.getStyleColor(similarRune.styleKey || rune.styleKey);
      
      runeElement.innerHTML = `
        <div class="similar-rune-placeholder" style="
          width: 100%; 
          height: 100%; 
          background-color: ${bgColor}80;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-weight: bold;
        ">
          <span>${similarRune.name.charAt(0)}</span>
        </div>
        <img src="" 
             alt="${similarRune.name}" 
             style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border-radius: 50%; display: none;">
      `;
      
      // Handle image loading errors
      const imgElement = runeElement.querySelector('img');
      const placeholder = runeElement.querySelector('.similar-rune-placeholder');
      
      // Set up successful load handler
      imgElement.addEventListener('load', () => {
        // Hide placeholder when image loads
        placeholder.style.display = 'none';
        imgElement.style.display = 'block';
      });
      
      // Set up error handler
      imgElement.addEventListener('error', () => {
        // Just use the placeholder
        placeholder.style.display = 'flex';
        imgElement.style.display = 'none';
      });
      
      // Use DataDragon CDN directly for rune images
      const runeIconUrl = similarRune.icon ? `https://ddragon.leagueoflegends.com/cdn/img/${similarRune.icon}` : `assets/runes/${similarRune.id}.png`;
      imgElement.src = runeIconUrl;
      
      // Add click event to navigate to this rune
      runeElement.addEventListener('click', () => {
        this.showRuneDetail(similarRune);
      });
      
      similarRunesGrid.appendChild(runeElement);
    });
    
    // If no similar runes found, show a message
    if (similarRunes.length === 0) {
      similarRunesGrid.innerHTML = '<p>No similar runes found.</p>';
    }
  }
  
  // Find similar runes based on slot, style, and keywords
  findSimilarRunes(rune) {
    // Get runes from the same style and slot (excluding the current rune)
    const sameSlotRunes = this.allRunes.filter(r => 
      r.id !== rune.id && 
      r.styleKey === rune.styleKey && 
      r.slotIndex === rune.slotIndex
    );
    
    // If we have at least 2 runes from the same slot, return those
    if (sameSlotRunes.length >= 2) {
      return sameSlotRunes.slice(0, 4);
    }
    
    // Otherwise, find runes with similar keywords or function
    const runeDesc = (rune.shortDesc || '') + ' ' + (rune.longDesc || '');
    
    // Extract key functionality words
    const keywords = this.extractKeywords(runeDesc);
    
    // Find runes with similar keywords
    const similarKeywordRunes = this.allRunes.filter(r => {
      if (r.id === rune.id) return false;
      
      const rDesc = (r.shortDesc || '') + ' ' + (r.longDesc || '');
      const rKeywords = this.extractKeywords(rDesc);
      
      // Count matching keywords
      const matches = keywords.filter(k => rKeywords.includes(k)).length;
      
      // Consider similar if at least 2 keywords match
      return matches >= 2;
    });
    
    // Return top 4 similar runes
    return similarKeywordRunes.slice(0, 4);
  }
  
  // Extract keywords from rune description
  extractKeywords(description) {
    const keywords = [];
    const text = this.stripHtmlTags(description).toLowerCase();
    
    // Check for common functionality keywords
    const functionKeywords = [
      'damage', 'heal', 'shield', 'movement', 'speed', 'cooldown', 
      'gold', 'stun', 'slow', 'immobilize', 'adaptive', 'attack', 
      'ability', 'power', 'health', 'mana', 'armor', 'magic resist'
    ];
    
    functionKeywords.forEach(keyword => {
      if (text.includes(keyword)) {
        keywords.push(keyword);
      }
    });
    
    return keywords;
  }
  
  // Populate related champions section
  populateRelatedChampions(rune) {
    const championsGrid = this.runeDetailElement.querySelector('.rune-champions-grid');
    if (!championsGrid) return;
    
    // Clear previous content
    championsGrid.innerHTML = '';
    
    // For now, we'll just show placeholder text since we don't have champion-rune associations
    championsGrid.innerHTML = `
      <p>Champion data will be added in a future update.</p>
    `;
    
    // Note: In a full implementation, we would fetch champion-rune associations
    // from the API or a local database and display relevant champions here
  }
  
  // Show runes list (main view)
  showRunesList() {
    // Reset current selections
    this.currentStyle = null;
    this.currentRune = null;
    
    // Show runes list, hide other views
    this.runesList.style.display = 'block';
    this.runeStyleDetailElement.style.display = 'none';
    this.runeDetailElement.style.display = 'none';
    this.runeBuilderElement.style.display = 'none';
    
    // Show the search container
    document.getElementById('runes-search-container').style.display = 'block';
  }
  
  // Helper function to strip HTML tags
  stripHtmlTags(html) {
    const temp = document.createElement('div');
    temp.innerHTML = html;
    return temp.textContent || temp.innerText || '';
  }
  
  // Get color for a rune style
  getStyleColor(styleKey) {
    const styleColors = {
      Domination: '#ca3e3f',
      Inspiration: '#49aab9',
      Precision: '#c8aa6e',
      Resolve: '#4d8b7c',
      Sorcery: '#9e7cc9'
    };
    
    return styleColors[styleKey] || '#c8aa6e';
  }
  
  // Get short descriptive text for a rune style
  getStyleDescription(styleKey) {
    const styleDescriptions = {
      Domination: 'Hunt and eliminate targets with burst damage and access',
      Inspiration: 'Creative tools and rule-bending to outsmart opponents',
      Precision: 'Sustained damage and improved attacks for extended fights',
      Resolve: 'Durability and crowd control to lock down opponents',
      Sorcery: 'Empowered abilities and resource manipulation'
    };
    
    return styleDescriptions[styleKey] || `Path of ${styleKey}`;
  }
  
  // Get detailed description for a rune style
  getDetailedStyleDescription(styleKey) {
    const detailedDescriptions = {
      Domination: "The Path of Domination focuses on hunting down prey and bursting them down. Champions who excel with this path are those who want to aggressively seek out and eliminate priority targets. It provides tools for quick access to enemies and the means to take them down swiftly. Perfect for assassins and burst mages.",
      
      Inspiration: "The Path of Inspiration breaks the conventional rules of League of Legends with creative tools and unique mechanics. Champions who choose this path gain access to unconventional advantages like item upgrades, summoner spell swapping, and enhanced consumables. This path encourages creative and unpredictable playstyles that outsmart opponents rather than overpower them.",
      
      Precision: "The Path of Precision enhances attacks and sustained damage output. Champions who benefit most from this path are those who rely on consistent damage through auto attacks and frequent ability usage. It offers improved attack speed, damage amplification against low health targets, and tools for extended combat situations. Ideal for marksmen, fighters, and auto-attack focused champions.",
      
      Resolve: "The Path of Resolve provides durability and staying power in fights. Champions who choose this path gain access to improved defenses, healing, and crowd control. It excels at allowing champions to withstand punishment and lock down opponents, perfect for tanks and frontliners who want to absorb damage for their team while maintaining battlefield presence.",
      
      Sorcery: "The Path of Sorcery empowers abilities and helps manage resources. Champions who benefit from this path are typically ability-focused, valuing cooldown reduction, mana management, and increased spell effects. This path provides tools for mages and ability-dependent champions to maximize their impact through enhanced spellcasting and resource manipulation."
    };
    
    return detailedDescriptions[styleKey] || `The Path of ${styleKey} provides unique benefits to champions who specialize in its particular playstyle.`;
  }
  
  // Handle rune image loading errors with better fallback
  _handleRuneImageError(imgElement, rune) {
    console.warn(`Rune image load failed for ${rune.name} (${rune.id})`);
    
    try {
      // First, try to use the DataDragon CDN if we have an icon path
      if (rune.icon) {
        const dataDragonUrl = `https://ddragon.leagueoflegends.com/cdn/img/${rune.icon}`;
        
        // Only retry if the URL is different from the current one
        if (imgElement.src !== dataDragonUrl) {
          console.log(`Retrying with DataDragon URL: ${dataDragonUrl}`);
          
          // Set up a one-time error handler for the retry
          imgElement.onerror = () => {
            // If DataDragon fails, try the API URL
            const apiUrl = `${this.API_BASE_URL}/assets/rune/image/${rune.id}`;
            
            // Set up another one-time error handler
            imgElement.onerror = () => {
              // If both retries fail, use fallback
              this._createFallbackRuneImage(imgElement, rune);
              // Remove the error handler to prevent loops
              imgElement.onerror = null;
            };
            
            // Try the API URL
            imgElement.src = apiUrl;
          };
          
          // Try the DataDragon URL
          imgElement.src = dataDragonUrl;
        } else {
          // Try the API URL as a fallback
          const apiUrl = `${this.API_BASE_URL}/assets/rune/image/${rune.id}`;
          
          if (imgElement.src !== apiUrl) {
            imgElement.onerror = () => {
              this._createFallbackRuneImage(imgElement, rune);
              imgElement.onerror = null;
            };
            
            imgElement.src = apiUrl;
          } else {
            // If we've tried both URLs, go directly to fallback
            this._createFallbackRuneImage(imgElement, rune);
          }
        }
      } else {
        // If we don't have an icon path, try the API URL
        const apiUrl = `${this.API_BASE_URL}/assets/rune/image/${rune.id}`;
        
        if (imgElement.src !== apiUrl) {
          imgElement.onerror = () => {
            this._createFallbackRuneImage(imgElement, rune);
            imgElement.onerror = null;
          };
          
          imgElement.src = apiUrl;
        } else {
          // If we've already tried the API URL, go directly to fallback
          this._createFallbackRuneImage(imgElement, rune);
        }
      }
    } catch (error) {
      console.error('Error creating fallback rune image:', error);
      this._createFallbackRuneImage(imgElement, rune);
    }
  }
  
  // Handle fallback for rune images
  _createFallbackRuneImage(imgElement, rune) {
    try {
      // Set a fallback image path based on the Data Dragon format
      const styleKey = rune.styleKey || 'Precision';
      
      // Use a specific image path pattern based on the type of rune
      let fallbackPath = '';
      
      // Check if this is a style path (like Domination, Precision, etc.)
      if (rune.slots && Array.isArray(rune.slots)) {
        // This is a style/path
        // Try to generate a path based on the style name
        if (styleKey) {
          const styleName = styleKey.toLowerCase();
          // Create a colored circle with initial
          const parentElement = imgElement.parentElement;
          if (parentElement) {
            const placeholder = parentElement.querySelector('.style-icon-placeholder') || 
                                parentElement.querySelector('.style-detail-placeholder');
            if (placeholder) {
              // Placeholder already exists and is visible
              imgElement.style.display = 'none';
              placeholder.style.display = 'flex';
              return; // Exit early, no need to set src
            }
          }
        }
        fallbackPath = `images/champion-placeholder.png`;
      } else {
        // This is a regular rune
        // Look for an existing placeholder
        const parentElement = imgElement.parentElement;
        if (parentElement) {
          const placeholder = parentElement.querySelector('.rune-icon-placeholder') || 
                             parentElement.querySelector('.rune-img-placeholder') ||
                             parentElement.querySelector('.similar-rune-placeholder');
          if (placeholder) {
            // Placeholder already exists and is visible
            imgElement.style.display = 'none';
            placeholder.style.display = 'flex';
            return; // Exit early, no need to set src
          }
        }
        fallbackPath = `images/item-placeholder.png`;
      }
      
      // Set the fallback image
      imgElement.src = fallbackPath;
      imgElement.classList.add('fallback-image');
    } catch (error) {
      console.error('Error setting fallback for rune:', error);
      // Ultimate fallback - just use item placeholder
      imgElement.src = 'images/item-placeholder.png';
      imgElement.classList.add('fallback-image');
    }
  }
  
  _getLocalRuneData() {
    // Simplified rune data structure with just the essential elements
    return [
      {
        id: 8100,
        key: "Domination",
        name: "Domination",
        icon: "perk-images/Styles/7200_Domination.png",
        slots: [
          {
            runes: [
              {
                id: 8112,
                key: "Electrocute",
                name: "Electrocute",
                icon: "perk-images/Styles/Domination/Electrocute/Electrocute.png",
                shortDesc: "Hitting a champion with 3 separate attacks or abilities deals bonus adaptive damage.",
                longDesc: "Hitting a champion with 3 separate attacks or abilities within 3s deals bonus adaptive damage. Damage: 40-80 based on level, plus 40% bonus AD, and 25% AP. Cooldown: 25-20s based on level."
              },
              {
                id: 8124,
                key: "Predator",
                name: "Predator",
                icon: "perk-images/Styles/Domination/Predator/Predator.png",
                shortDesc: "Enchants boots with the active effect 'Predator'.",
                longDesc: "Enchants boots with the active effect 'Predator'. When activated, grants a large boost of movement speed and damage on the next attack. Cooldown: 150-100s based on level."
              }
            ]
          },
          {
            runes: [
              {
                id: 8126,
                key: "CheapShot",
                name: "Cheap Shot",
                icon: "perk-images/Styles/Domination/CheapShot/CheapShot.png",
                shortDesc: "Deal bonus true damage to enemies with impaired movement or actions.",
                longDesc: "Deal 10-45 bonus true damage (based on level) to enemies with impaired movement or actions. Cooldown: 4s."
              }
            ]
          },
          {
            runes: [
              {
                id: 8136,
                key: "ZombieWard",
                name: "Zombie Ward",
                icon: "perk-images/Styles/Domination/ZombieWard/ZombieWard.png",
                shortDesc: "After killing an enemy ward, a friendly Zombie Ward is raised in its place.",
                longDesc: "After killing an enemy ward, a friendly Zombie Ward is raised in its place. Zombie Wards are visible, last for 120s and don't count towards your ward limit."
              }
            ]
          },
          {
            runes: [
              {
                id: 8134,
                key: "IngeniousHunter",
                name: "Ingenious Hunter",
                icon: "perk-images/Styles/Domination/IngeniousHunter/IngeniousHunter.png",
                shortDesc: "Gain active item haste. Unique takedowns grant permanent bonus active item haste.",
                longDesc: "Gain 20 active item haste plus 10 per Bounty Hunter stack. Bounty Hunter stacks are earned the first time you get a takedown on each enemy champion."
              }
            ]
          }
        ]
      },
      {
        id: 8300,
        key: "Inspiration",
        name: "Inspiration",
        icon: "perk-images/Styles/7203_Whimsy.png",
        slots: [
          {
            runes: [
              {
                id: 8351,
                key: "GlacialAugment",
                name: "Glacial Augment",
                icon: "perk-images/Styles/Inspiration/GlacialAugment/GlacialAugment.png",
                shortDesc: "Your first attack against a champion slows them.",
                longDesc: "Basic attacking a champion slows them for 2s. The slow increases in strength over its duration, from 15% to 40%. Ranged: Duration halved to 1s."
              }
            ]
          },
          {
            runes: [
              {
                id: 8306,
                key: "HextechFlashtraption",
                name: "Hextech Flashtraption",
                icon: "perk-images/Styles/Inspiration/HextechFlashtraption/HextechFlashtraption.png",
                shortDesc: "While Flash is on cooldown, it is replaced by Hexflash.",
                longDesc: "While Flash is on cooldown, it is replaced by Hexflash. Hexflash: Channel for 2s to blink to a new location. Cooldown: 20s. Goes on a 10s cooldown when you enter champion combat."
              }
            ]
          },
          {
            runes: [
              {
                id: 8345,
                key: "BiscuitDelivery",
                name: "Biscuit Delivery",
                icon: "perk-images/Styles/Inspiration/BiscuitDelivery/BiscuitDelivery.png",
                shortDesc: "Gain a free Biscuit at 2 min, until 6 min.",
                longDesc: "Gain a free Biscuit every 2 mins, until 6 mins. Biscuits restore health and mana and permanently increase mana by 50."
              }
            ]
          },
          {
            runes: [
              {
                id: 8347,
                key: "CosmicInsight",
                name: "Cosmic Insight",
                icon: "perk-images/Styles/Inspiration/CosmicInsight/CosmicInsight.png",
                shortDesc: "Gain Summoner Spell and Item Haste.",
                longDesc: "Gain 18 Summoner Spell Haste and 10 Item Haste."
              }
            ]
          }
        ]
      },
      {
        id: 8000,
        key: "Precision",
        name: "Precision",
        icon: "perk-images/Styles/7201_Precision.png",
        slots: [
          {
            runes: [
              {
                id: 8005,
                key: "PressTheAttack",
                name: "Press the Attack",
                icon: "perk-images/Styles/Precision/PressTheAttack/PressTheAttack.png",
                shortDesc: "Hitting a champion 3 consecutive times makes them vulnerable.",
                longDesc: "Hitting a champion with 3 consecutive basic attacks deals bonus damage and makes them vulnerable, increasing the damage they take for 6s."
              }
            ]
          },
          {
            runes: [
              {
                id: 9111,
                key: "Triumph",
                name: "Triumph",
                icon: "perk-images/Styles/Precision/Triumph.png",
                shortDesc: "Takedowns restore health and grant gold.",
                longDesc: "Takedowns restore 12% of your missing health and grant an additional 20 gold."
              }
            ]
          },
          {
            runes: [
              {
                id: 9104,
                key: "LegendAlacrity",
                name: "Legend: Alacrity",
                icon: "perk-images/Styles/Precision/LegendAlacrity/LegendAlacrity.png",
                shortDesc: "Takedowns grant permanent Attack Speed.",
                longDesc: "Gain 3% attack speed plus an additional 1.5% for every Legend stack (max 10 stacks)."
              }
            ]
          },
          {
            runes: [
              {
                id: 8014,
                key: "CoupDeGrace",
                name: "Coup de Grace",
                icon: "perk-images/Styles/Precision/CoupDeGrace/CoupDeGrace.png",
                shortDesc: "Deal more damage to low health champions.",
                longDesc: "Deal 8% more damage to champions who have less than 40% health."
              }
            ]
          }
        ]
      },
      {
        id: 8400,
        key: "Resolve",
        name: "Resolve",
        icon: "perk-images/Styles/7204_Resolve.png",
        slots: [
          {
            runes: [
              {
                id: 8437,
                key: "GraspOfTheUndying",
                name: "Grasp of the Undying",
                icon: "perk-images/Styles/Resolve/GraspOfTheUndying/GraspOfTheUndying.png",
                shortDesc: "Every 4s your next attack on a champion deals bonus damage and heals you.",
                longDesc: "Every 4s in combat, your next attack on a champion deals bonus magic damage equal to 4% of your max health, heals you for 2% of your max health, and permanently increases your health by 5."
              }
            ]
          },
          {
            runes: [
              {
                id: 8446,
                key: "Demolish",
                name: "Demolish",
                icon: "perk-images/Styles/Resolve/Demolish/Demolish.png",
                shortDesc: "Charge up a powerful attack against a tower.",
                longDesc: "Charge up a powerful attack against a tower over 3s, while within 600 range of it. The charged attack deals 100 (+35% of your max health) bonus physical damage."
              }
            ]
          },
          {
            runes: [
              {
                id: 8429,
                key: "Conditioning",
                name: "Conditioning",
                icon: "perk-images/Styles/Resolve/Conditioning/Conditioning.png",
                shortDesc: "After 12 min gain bonus Armor and Magic Resist.",
                longDesc: "After 12 min gain +9 Armor and +9 Magic Resist and increase your Armor and Magic Resist by 5%."
              }
            ]
          },
          {
            runes: [
              {
                id: 8451,
                key: "Overgrowth",
                name: "Overgrowth",
                icon: "perk-images/Styles/Resolve/Overgrowth/Overgrowth.png",
                shortDesc: "Gain permanent health when minions or monsters die near you.",
                longDesc: "Gain permanent health when minions or monsters die near you, +3 health per 8 monsters or minions. After 120 monsters or minions, gain an additional 3.5% max health."
              }
            ]
          }
        ]
      },
      {
        id: 8200,
        key: "Sorcery",
        name: "Sorcery",
        icon: "perk-images/Styles/7202_Sorcery.png",
        slots: [
          {
            runes: [
              {
                id: 8214,
                key: "SummonAery",
                name: "Summon Aery",
                icon: "perk-images/Styles/Sorcery/SummonAery/SummonAery.png",
                shortDesc: "Your attacks and abilities send Aery to damage enemies or shield allies.",
                longDesc: "Damaging champions sends Aery to damage them. Shielding or healing allies sends Aery to shield them. Aery returns to you after damaging or shielding."
              }
            ]
          },
          {
            runes: [
              {
                id: 8226,
                key: "ManaflowBand",
                name: "Manaflow Band",
                icon: "perk-images/Styles/Sorcery/ManaflowBand/ManaflowBand.png",
                shortDesc: "Hitting an enemy champion with an ability permanently increases your max mana.",
                longDesc: "Hitting an enemy champion with an ability permanently increases your maximum mana by 25, up to 250 mana. After reaching 250 bonus mana, restore 1% of your missing mana every 5 seconds."
              }
            ]
          },
          {
            runes: [
              {
                id: 8210,
                key: "Transcendence",
                name: "Transcendence",
                icon: "perk-images/Styles/Sorcery/Transcendence/Transcendence.png",
                shortDesc: "Gain CDR at level 5 and 8. CDR over cap becomes AP or AD.",
                longDesc: "Gain +5 Ability Haste at level 5 and +5 at level 8. At level 11, gain an additional effect: When you score a champion takedown, reduce your basic ability cooldowns by 20%."
              }
            ]
          },
          {
            runes: [
              {
                id: 8237,
                key: "Scorch",
                name: "Scorch",
                icon: "perk-images/Styles/Sorcery/Scorch/Scorch.png",
                shortDesc: "Your first ability hit every 10s burns champions.",
                longDesc: "Your next damaging ability hit sets champions on fire, dealing 15-35 bonus magic damage after 1s. Cooldown: 10s."
              }
            ]
          }
        ]
      }
    ];
  }
}

// Export the class to make it globally available
window.RunesManager = RunesManager;

// Create an instance when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  console.log('RunesManager: Initializing global instance');
  if (!window.runesManager && window.RunesManager) {
    try {
      window.runesManager = new window.RunesManager();
      console.log('RunesManager: Global instance created successfully');
    } catch (error) {
      console.error('Error creating RunesManager instance:', error);
    }
  }
});