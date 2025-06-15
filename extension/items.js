// Items-related functionality for League of Legends Helper extension
// Simplified version with item list only (no item detail)

// Requires utils.js to be loaded first

class ItemsManager {
  constructor() {
    // Get references to DOM elements - Items
    this.itemsList = document.getElementById('items-list');
    this.itemsLoadingElement = document.getElementById('loading-items');
    this.itemsErrorElement = document.getElementById('error-items');
    this.itemsNoResultsElement = document.getElementById('no-results-items');
    this.resetSearchItems = document.getElementById('reset-search-items');
    
    // Initialize state
    this.allItems = []; // Store all items from API
    this.itemsByTier = {}; // Store items grouped by tier
    this.currentTier = 'all'; // Current tier filter for items
    this.API_BASE_URL = window.LOLUtils.API_BASE_URL;
    
    // Initialize filter state
    this.itemFilter = {
      searchText: '',
      activeTags: new Set(),
      activeStats: new Set()
    };
    
    // Set up event handlers
    this._setupEventHandlers();
  }
  
  _setupEventHandlers() {
    // Set up filter tabs
    const filterTabs = document.querySelectorAll('.filter-tab');
    filterTabs.forEach(tab => {
      tab.addEventListener('click', () => {
        // Get the tab ID
        const tabId = tab.getAttribute('data-tab');
        
        // Update active state for tabs
        filterTabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        
        // Update active state for panes
        document.querySelectorAll('.filter-pane').forEach(pane => pane.classList.remove('active'));
        document.getElementById(`${tabId}-pane`).classList.add('active');
      });
    });
    
    // Set up tier filter buttons
    const tierButtons = document.querySelectorAll('.tier-button');
    tierButtons.forEach(button => {
      button.addEventListener('click', () => {
        // Get the tier from the button
        const tier = button.getAttribute('data-tier');
        
        // Update active state
        tierButtons.forEach(btn => btn.classList.remove('active'));
        button.classList.add('active');
        
        // Update current tier and redisplay items
        this.currentTier = tier;
        this.updateActiveFilters();
        this.displayItems();
      });
    });
    
    // Set up stat filter buttons
    const statFilters = document.querySelectorAll('.stat-filter');
    statFilters.forEach(button => {
      button.addEventListener('click', () => {
        // Get the stat from the button
        const stat = button.getAttribute('data-stat');
        
        // Toggle active state
        button.classList.toggle('active');
        
        // Update filter state
        if (this.itemFilter.activeStats.has(stat)) {
          this.itemFilter.activeStats.delete(stat);
        } else {
          this.itemFilter.activeStats.add(stat);
        }
        
        this.updateActiveFilters();
        this.displayItems();
      });
    });
    
    // Set up item search clear button
    const searchClear = document.getElementById('item-search-clear');
    if (searchClear) {
      searchClear.addEventListener('click', () => {
        const searchInput = document.getElementById('item-search-input');
        if (searchInput) {
          searchInput.value = '';
          this.itemFilter.searchText = '';
          searchClear.style.display = 'none';
          
          this.updateActiveFilters();
          this.displayItems();
          
          // Focus back on search input
          searchInput.focus();
        }
      });
    }
    
    // Reset search button for items
    if (this.resetSearchItems) {
      this.resetSearchItems.addEventListener('click', () => {
        this.resetAllFilters();
      });
    }
    
    // Clear all filters button
    const clearFiltersButton = document.getElementById('clear-item-filters');
    if (clearFiltersButton) {
      clearFiltersButton.addEventListener('click', () => {
        this.resetAllFilters();
      });
    }

    // Add search input handler
    const searchInput = document.getElementById('item-search-input');
    if (searchInput) {
      searchInput.addEventListener('input', () => {
        // Update search text filter
        this.itemFilter.searchText = searchInput.value.trim();
        
        // Show/hide clear button
        const searchClear = document.getElementById('item-search-clear');
        if (searchClear) {
          searchClear.style.display = this.itemFilter.searchText ? 'block' : 'none';
        }
        
        // Update filters and display
        this.updateActiveFilters();
        this.displayItems();
      });
    }
  }
  
  // Update the active filters display
  updateActiveFilters() {
    const activeFiltersList = document.getElementById('active-filters-list');
    if (!activeFiltersList) return;
    
    // Build list of active filters
    const activeFilters = [];
    
    // Add tier filter
    if (this.currentTier !== 'all') {
      activeFilters.push(`Tier: ${this.getTierDisplayName(this.currentTier).replace(' Items', '')}`);
    }
    
    // Add stat filters
    if (this.itemFilter.activeStats.size > 0) {
      const statNames = {
        'ad': 'Attack Damage',
        'ap': 'Ability Power',
        'armor': 'Armor',
        'mr': 'Magic Resist',
        'hp': 'Health',
        'mana': 'Mana',
        'as': 'Attack Speed',
        'crit': 'Critical',
        'ms': 'Movement',
        'utility': 'Utility'
      };
      
      this.itemFilter.activeStats.forEach(stat => {
        activeFilters.push(`Stat: ${statNames[stat] || stat}`);
      });
    }
    
    // Add search text
    if (this.itemFilter.searchText) {
      activeFilters.push(`Search: "${this.itemFilter.searchText}"`);
    }
    
    // Update the display
    if (activeFilters.length > 0) {
      activeFiltersList.innerHTML = activeFilters.map(filter => 
        `<span class="filter-tag">${filter}</span>`
      ).join('');
    } else {
      activeFiltersList.innerHTML = 'None';
    }
  }
  
  // Reset all filters
  resetAllFilters() {
    // Reset search input
    const searchInput = document.getElementById('item-search-input');
    if (searchInput) {
      searchInput.value = '';
    }
    this.itemFilter.searchText = '';
    
    // Reset tier filter
    const tierButtons = document.querySelectorAll('.tier-button');
    tierButtons.forEach(btn => btn.classList.remove('active'));
    const allTierButton = document.querySelector('.tier-button[data-tier="all"]');
    if (allTierButton) {
      allTierButton.classList.add('active');
    }
    this.currentTier = 'all';
    
    // Reset stat filters
    this.itemFilter.activeStats.clear();
    const statFilters = document.querySelectorAll('.stat-filter');
    statFilters.forEach(btn => btn.classList.remove('active'));
    
    // Update UI and display
    this.updateActiveFilters();
    this.displayItems();
  }
  
  // No _setupObserver needed in the simplified version

  // Function to fetch items data with caching
  async fetchItems() {
    try {
      // Show loading state
      this.itemsLoadingElement.style.display = 'block';
      this.itemsErrorElement.style.display = 'none';
      this.itemsNoResultsElement.style.display = 'none';
      
      // Check if we have cached items data
      const items = await window.LOLUtils.getCachedItems();
      
      if (items) {
        // Use cached data
        console.log('Using cached items data');
        this.allItems = items;
        this.processItems();
        return;
      }
      
      // No cache or expired cache, fetch from API
      console.log('Fetching items from API (all pages)');
      
      // Fetch the first page to get total count
      const firstPageResponse = await fetch(`${this.API_BASE_URL}/items?limit=100&page=1`);
      
      if (!firstPageResponse.ok) {
        throw new Error(`API request failed with status ${firstPageResponse.status}`);
      }
      
      const firstPageData = await firstPageResponse.json();
      const totalItems = firstPageData.total || 0;
      
      // Calculate how many pages we need to fetch
      const itemsPerPage = 100;
      const totalPages = Math.ceil(totalItems / itemsPerPage);
      
      console.log(`Total items: ${totalItems}, pages needed: ${totalPages}`);
      
      // Start with items from first page
      let allItemsAcrossPages = [];
      
      // Add items from first page
      if (firstPageData && firstPageData.tiers) {
        allItemsAcrossPages = firstPageData.tiers.flatMap(tier => tier.items || []);
      }
      
      // Fetch additional pages if needed
      const additionalPagePromises = [];
      for (let page = 2; page <= totalPages; page++) {
        console.log(`Fetching page ${page} of ${totalPages}`);
        additionalPagePromises.push(
          fetch(`${this.API_BASE_URL}/items?limit=100&page=${page}`)
            .then(response => {
              if (!response.ok) {
                throw new Error(`API request for page ${page} failed with status ${response.status}`);
              }
              return response.json();
            })
            .then(pageData => {
              if (pageData && pageData.tiers) {
                // Extract items from this page
                const pageItems = pageData.tiers.flatMap(tier => tier.items || []);
                return pageItems;
              }
              return [];
            })
        );
      }
      
      // Wait for all additional pages to load
      const additionalPagesResults = await Promise.all(additionalPagePromises);
      
      // Combine all items from all pages
      additionalPagesResults.forEach(pageItems => {
        allItemsAcrossPages = allItemsAcrossPages.concat(pageItems);
      });
      
      // Hide loading state
      this.itemsLoadingElement.style.display = 'none';
      
      // Store all items
      this.allItems = allItemsAcrossPages;
      
      console.log(`Processed ${this.allItems.length} items from all API pages`);
      
      // Process and display items
      this.processItems();
      
      // Save to cache
      await window.LOLUtils.cacheItems(this.allItems);
    } catch (error) {
      console.error('Error fetching items:', error);
      
      // Hide loading state and show error
      this.itemsLoadingElement.style.display = 'none';
      this.itemsErrorElement.style.display = 'block';
      this.itemsErrorElement.textContent = `Error loading items: ${error.message}`;
    }
  }
  
  // Process items data to organize it
  processItems() {
    console.log(`Processing ${this.allItems.length} items...`);
    
    // Hide loading state
    this.itemsLoadingElement.style.display = 'none';
    
    // Ensure the items list is visible
    if (this.itemsList) {
      this.itemsList.style.display = 'block';
    }
    
    // Group items by tier
    this.itemsByTier = {
      all: this.allItems,
      starter: [],
      basic: [],
      epic: [],
      legendary: [],
      mythic: []
    };
    
    // Group items by tier
    this.allItems.forEach(item => {
      // Determine tier from various properties
      let tier = 'basic'; // Default tier
      
      if (item.tier) {
        // Check if tier is a number or string
        if (typeof item.tier === 'number') {
          // Map numeric tiers to names
          switch(item.tier) {
            case 4: tier = 'mythic'; break;
            case 3: tier = 'legendary'; break;
            case 2: tier = 'epic'; break;
            case 1: tier = 'basic'; break;
            default: tier = 'basic';
          }
        } else if (typeof item.tier === 'string') {
          // Convert string tier to lowercase for consistency
          const tierLower = item.tier.toLowerCase();
          
          if (tierLower.includes('mythic')) {
            tier = 'mythic';
          } else if (tierLower.includes('legendary')) {
            tier = 'legendary';
          } else if (tierLower.includes('epic')) {
            tier = 'epic';
          } else if (tierLower.includes('basic')) {
            tier = 'basic';
          } else if (tierLower.includes('starter')) {
            tier = 'starter';
          }
        }
      } else {
        // If no tier specified, use gold cost as a proxy
        if (item.gold && item.gold.total) {
          const cost = item.gold.total;
          
          if (cost >= 3000) {
            tier = 'mythic';
          } else if (cost >= 2000) {
            tier = 'legendary';
          } else if (cost >= 1000) {
            tier = 'epic';
          } else if (cost <= 500 && item.gold.purchasable !== false) {
            tier = 'starter';
          }
        }
        
        // Check for mythic/legendary in description
        if (item.description) {
          if (item.description.toLowerCase().includes('mythic')) {
            tier = 'mythic';
          } else if (item.description.toLowerCase().includes('legendary')) {
            tier = 'legendary';
          }
        }
      }
      
      // Add to appropriate tier array
      if (this.itemsByTier[tier]) {
        this.itemsByTier[tier].push(item);
      }
    });
    
    // Sort each tier by gold cost
    for (const tier in this.itemsByTier) {
      this.itemsByTier[tier].sort((a, b) => {
        const costA = a.gold && a.gold.total ? a.gold.total : 0;
        const costB = b.gold && b.gold.total ? b.gold.total : 0;
        return costB - costA; // Sort from highest to lowest cost
      });
    }
    
    // Log item counts by tier
    console.log('Items by tier:');
    for (const tier in this.itemsByTier) {
      console.log(`- ${tier}: ${this.itemsByTier[tier].length} items`);
    }
    
    // Display items
    this.displayItems();
  }
  
  // Filter items based on current filters
  filterItems() {
    // Start with items from the current tier
    let items = this.itemsByTier[this.currentTier] || [];
    
    // If we have search text, filter by name and description
    if (this.itemFilter.searchText) {
      const searchText = this.itemFilter.searchText.toLowerCase();
      
      items = items.filter(item => {
        // Check name
        if (item.name && item.name.toLowerCase().includes(searchText)) {
          return true;
        }
        
        // Check description
        if (item.description && item.description.toLowerCase().includes(searchText)) {
          return true;
        }
        
        // Check plaintext
        if (item.plaintext && item.plaintext.toLowerCase().includes(searchText)) {
          return true;
        }
        
        return false;
      });
    }
    
    // If we have active stat filters, apply them
    if (this.itemFilter.activeStats.size > 0) {
      items = items.filter(item => {
        // Check if item has any of the selected stats
        return Array.from(this.itemFilter.activeStats).some(stat => {
          // Check description for the stat
          if (item.description) {
            const description = item.description.toLowerCase();
            
            switch (stat) {
              case 'ad':
                return description.includes('attack damage') || description.includes('+ad');
              case 'ap':
                return description.includes('ability power') || description.includes('+ap');
              case 'armor':
                return description.includes('armor');
              case 'mr':
                return description.includes('magic resist') || description.includes('magic resistance');
              case 'hp':
                return description.includes('health') && !description.includes('health regen');
              case 'mana':
                return description.includes('mana') && !description.includes('mana regen');
              case 'as':
                return description.includes('attack speed');
              case 'crit':
                return description.includes('critical') || description.includes('crit');
              case 'ms':
                return description.includes('movement speed');
              case 'utility':
                return description.includes('active') || 
                       description.includes('cooldown reduction') ||
                       description.includes('ability haste');
              default:
                return false;
            }
          }
          
          return false;
        });
      });
    }
    
    return items;
  }
  
  // Display items in the UI
  displayItems() {
    // Get items based on current filter
    const items = this.filterItems();
    
    // Show or hide "no results" message
    if (items.length === 0) {
      this.itemsNoResultsElement.style.display = 'block';
      this.itemsList.style.display = 'none';
    } else {
      this.itemsNoResultsElement.style.display = 'none';
      this.itemsList.style.display = 'block';
    }
    
    // Get the items container element
    const itemsContainer = this.itemsList.querySelector('.items-container');
    if (!itemsContainer) {
      return;
    }
    
    // Clear previous content
    itemsContainer.innerHTML = '';
    
    // If we have a current tier filter other than 'all', use a single category
    if (this.currentTier !== 'all') {
      const categoryTitle = document.createElement('h3');
      categoryTitle.className = 'item-category-title';
      categoryTitle.textContent = this.getTierDisplayName(this.currentTier);
      itemsContainer.appendChild(categoryTitle);
      
      const categoryItems = document.createElement('div');
      categoryItems.className = 'item-category';
      
      // Create item cards
      items.forEach(item => {
        const itemCard = this.createItemCard(item);
        categoryItems.appendChild(itemCard);
      });
      
      itemsContainer.appendChild(categoryItems);
    } else {
      // Otherwise, create categories for each tier
      const tiers = ['mythic', 'legendary', 'epic', 'basic', 'starter'];
      
      tiers.forEach(tier => {
        const tierItems = items.filter(item => {
          const itemTier = this.getItemTier(item);
          return itemTier === tier;
        });
        
        if (tierItems.length > 0) {
          const categoryTitle = document.createElement('h3');
          categoryTitle.className = 'item-category-title';
          categoryTitle.textContent = this.getTierDisplayName(tier);
          itemsContainer.appendChild(categoryTitle);
          
          const categoryItems = document.createElement('div');
          categoryItems.className = 'item-category';
          
          // Create item cards
          tierItems.forEach(item => {
            const itemCard = this.createItemCard(item);
            categoryItems.appendChild(itemCard);
          });
          
          itemsContainer.appendChild(categoryItems);
        }
      });
    }
  }
  
  // Helper to create a cutting-edge item card with better text handling
  createItemCard(item) {
    const itemCard = document.createElement('div');
    itemCard.className = 'item-card';
    itemCard.setAttribute('data-id', item.id);
    
    // Determine item tier and add tier-specific class and data attribute
    const tier = this.getItemTier(item);
    itemCard.classList.add(`tier-${tier}`);
    itemCard.setAttribute('data-tier', tier);
    
    // Add item description as data attribute for filter matching
    if (item.description) {
      itemCard.setAttribute('data-description', item.description);
    }
    
    // Create image URL with fallback
    const imageUrl = item.image && item.image.full 
      ? `${this.API_BASE_URL}/assets/item/image/${item.id}`
      : 'images/champion-placeholder.png';
    
    // Format the name for display and add title attribute for hover tooltip
    const itemName = item.name || 'Unknown Item';
    
    // Create cost display with gold icon
    const costDisplay = item.gold && item.gold.total 
      ? `<div class="item-cost">${item.gold.total}</div>`
      : '';
    
    // Set card HTML with improved structure
    itemCard.innerHTML = `
      <div class="item-image">
        <img src="${imageUrl}" alt="${itemName}" class="item-img">
      </div>
      <div class="item-info">
        <div class="item-name-wrapper">
          <span class="item-name" title="${itemName}">${itemName}</span>
        </div>
        ${costDisplay}
      </div>
    `;
    
    // Add error handler to the image
    const imgElement = itemCard.querySelector('.item-img');
    imgElement.addEventListener('error', function() {
      window.LOLUtils.handleImageError(this);
    });
    
    // Add loading effect to image
    imgElement.style.opacity = '0';
    imgElement.addEventListener('load', function() {
      this.style.transition = 'opacity 0.3s ease';
      this.style.opacity = '1';
    });
    
    // Add special effect for mythic items
    if (tier === 'mythic') {
      itemCard.classList.add('mythic-item');
      const shimmer = document.createElement('div');
      shimmer.className = 'mythic-shimmer';
      itemCard.appendChild(shimmer);
    }
    
    // Add click handler to show item detail
    itemCard.addEventListener('click', () => {
      const itemId = item.id;
      console.log(`Item card clicked: ${itemId} (${itemName})`);
      
      // Dispatch an event that the ItemDetailManager will listen for
      document.dispatchEvent(new CustomEvent('itemSelected', {
        detail: { itemId }
      }));
    });
    
    return itemCard;
  }
  
  // Helper to get an item's tier
  getItemTier(item) {
    // Default tier
    let tier = 'basic';
    
    // Check different tier representations
    if (item.tier) {
      if (typeof item.tier === 'number') {
        // Map numeric tiers
        switch(item.tier) {
          case 4: tier = 'mythic'; break;
          case 3: tier = 'legendary'; break;
          case 2: tier = 'epic'; break;
          case 1: tier = 'basic'; break;
          default: tier = 'basic';
        }
      } else if (typeof item.tier === 'string') {
        // Parse string tier
        const tierLower = item.tier.toLowerCase();
        
        if (tierLower.includes('mythic')) {
          tier = 'mythic';
        } else if (tierLower.includes('legendary')) {
          tier = 'legendary';
        } else if (tierLower.includes('epic')) {
          tier = 'epic';
        } else if (tierLower.includes('basic')) {
          tier = 'basic';
        } else if (tierLower.includes('starter')) {
          tier = 'starter';
        }
      }
    } else {
      // Infer from gold cost if tier not specified
      if (item.gold && item.gold.total) {
        const cost = item.gold.total;
        
        if (cost >= 3000) {
          tier = 'mythic';
        } else if (cost >= 2000) {
          tier = 'legendary';
        } else if (cost >= 1000) {
          tier = 'epic';
        } else if (cost <= 500 && item.gold.purchasable !== false) {
          tier = 'starter';
        }
      }
      
      // Check description for tier hints
      if (item.description) {
        if (item.description.toLowerCase().includes('mythic')) {
          tier = 'mythic';
        } else if (item.description.toLowerCase().includes('legendary')) {
          tier = 'legendary';
        }
      }
    }
    
    return tier;
  }
  
  // Helper to get display name for a tier
  getTierDisplayName(tier) {
    switch(tier) {
      case 'mythic': return 'Mythic Items';
      case 'legendary': return 'Legendary Items';
      case 'epic': return 'Epic Items';
      case 'basic': return 'Basic Items';
      case 'starter': return 'Starter Items';
      default: return 'All Items';
    }
  }
}

// Export the class to make it globally available
window.ItemsManager = ItemsManager;

// Also create an instance and attach it to the window for direct access
document.addEventListener('DOMContentLoaded', function() {
  console.log('ItemsManager: Initializing global instance');
  if (!window.itemsManager && window.ItemsManager) {
    try {
      // Only create the instance if one doesn't already exist
      window.itemsManager = new window.ItemsManager();
      console.log('ItemsManager: Global instance created successfully');
    } catch (error) {
      console.error('Error creating ItemsManager instance:', error);
    }
  }
});
