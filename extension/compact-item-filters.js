/**
 * Compact Item Filters - Direct DOM-based filtering for League of Legends Helper extension
 */
document.addEventListener('DOMContentLoaded', function() {
  console.log('Initializing compact item filters');
  
  // Initialize the filters when the items tab is clicked
  var itemsNavButton = document.getElementById('items-nav');
  if (itemsNavButton) {
    itemsNavButton.addEventListener('click', function() {
      console.log('Items tab clicked, initializing filters');
      setTimeout(initializeFilters, 300);
    });
  }
  
  // Also initialize on page load
  setTimeout(initializeFilters, 500);
  
  // Main initialization function
  function initializeFilters() {
    // Set up tier filter buttons
    setupTierFilters();
    
    // Set up stat filter buttons
    setupStatFilters();
    
    // Set up clear filters button
    setupClearFiltersButton();
  }
  
  // Set up tier filter buttons
  function setupTierFilters() {
    const tierButtons = document.querySelectorAll('.tier-filter');
    if (tierButtons.length === 0) {
      console.log('No tier filter buttons found');
      return;
    }
    
    console.log(`Found ${tierButtons.length} tier filter buttons`);
    
    tierButtons.forEach(button => {
      // Remove any existing click listeners
      const newButton = button.cloneNode(true);
      if (button.parentNode) {
        button.parentNode.replaceChild(newButton, button);
      }
      
      // Add new click listener
      newButton.addEventListener('click', function() {
        // Get the tier
        const tier = this.getAttribute('data-tier');
        console.log(`Tier filter clicked: ${tier}`);
        
        // Update active state on buttons
        document.querySelectorAll('.tier-filter').forEach(btn => {
          btn.classList.remove('active');
        });
        this.classList.add('active');
        
        // Call the ItemsManager's changeTier method if it exists
        if (window.itemsManager && window.itemsManager.changeTier) {
          window.itemsManager.changeTier(tier);
        } else {
          console.log('ItemsManager not available, using direct DOM filtering');
          filterItemsByTier(tier);
        }
      });
    });
  }
  
  // Set up stat filter buttons
  function setupStatFilters() {
    const statButtons = document.querySelectorAll('.stat-filter');
    if (statButtons.length === 0) {
      console.log('No stat filter buttons found');
      return;
    }
    
    console.log(`Found ${statButtons.length} stat filter buttons`);
    
    // Active stats set
    const activeStats = new Set();
    
    statButtons.forEach(button => {
      // Ensure the button has a data-stat attribute
      if (!button.hasAttribute('data-stat')) {
        const buttonId = button.id || '';
        if (buttonId.includes('-ad')) button.setAttribute('data-stat', 'ad');
        else if (buttonId.includes('-ap')) button.setAttribute('data-stat', 'ap');
        else if (buttonId.includes('-armor')) button.setAttribute('data-stat', 'armor');
        else if (buttonId.includes('-mr')) button.setAttribute('data-stat', 'mr');
        else if (buttonId.includes('-hp')) button.setAttribute('data-stat', 'hp');
        else if (buttonId.includes('-mana')) button.setAttribute('data-stat', 'mana');
        else if (buttonId.includes('-as')) button.setAttribute('data-stat', 'as');
        else if (buttonId.includes('-crit')) button.setAttribute('data-stat', 'crit');
        else if (buttonId.includes('-ms')) button.setAttribute('data-stat', 'ms');
        else if (buttonId.includes('-utility')) button.setAttribute('data-stat', 'utility');
      }
      
      // Remove any existing click listeners
      const newButton = button.cloneNode(true);
      if (button.parentNode) {
        button.parentNode.replaceChild(newButton, button);
      }
      
      // Add new click listener
      newButton.addEventListener('click', function() {
        // Get the stat
        const stat = this.getAttribute('data-stat');
        console.log(`Stat filter clicked: ${stat}`);
        
        // Toggle active state
        if (this.classList.contains('active')) {
          this.classList.remove('active');
          activeStats.delete(stat);
        } else {
          this.classList.add('active');
          activeStats.add(stat);
        }
        
        // Update active filters display
        updateActiveFiltersDisplay(activeStats);
        
        // Call the ItemsManager's toggleStatFilter method if it exists
        if (window.itemsManager && window.itemsManager.toggleStatFilter) {
          window.itemsManager.toggleStatFilter(stat);
        } else {
          console.log('ItemsManager not available, using direct DOM filtering');
          filterItemsByStats(Array.from(activeStats));
        }
      });
    });
  }
  
  // Set up clear filters button
  function setupClearFiltersButton() {
    const clearButton = document.getElementById('clear-item-filters');
    if (!clearButton) {
      console.log('Clear filters button not found');
      return;
    }
    
    // Remove any existing click listeners
    const newButton = clearButton.cloneNode(true);
    if (clearButton.parentNode) {
      clearButton.parentNode.replaceChild(newButton, clearButton);
    }
    
    // Add new click listener
    newButton.addEventListener('click', function() {
      console.log('Clear filters button clicked');
      
      // Reset tier buttons
      document.querySelectorAll('.tier-filter').forEach(btn => {
        if (btn.getAttribute('data-tier') === 'all') {
          btn.classList.add('active');
        } else {
          btn.classList.remove('active');
        }
      });
      
      // Reset stat buttons
      document.querySelectorAll('.stat-filter').forEach(btn => {
        btn.classList.remove('active');
      });
      
      // Clear active filters display
      updateActiveFiltersDisplay(new Set());
      
      // Call the ItemsManager's clearFilters method if it exists
      if (window.itemsManager && window.itemsManager.clearFilters) {
        window.itemsManager.clearFilters();
      } else {
        console.log('ItemsManager not available, using direct DOM filtering');
        // Reset to 'all' tier
        filterItemsByTier('all');
      }
    });
  }
  
  // Update active filters display
  function updateActiveFiltersDisplay(activeStats) {
    const filtersList = document.getElementById('active-filters-list');
    if (!filtersList) return;
    
    // Clear current filters
    filtersList.innerHTML = '';
    
    // Skip if no active filters
    if (activeStats.size === 0) return;
    
    // Add filter tags for each active stat
    activeStats.forEach(stat => {
      const filterTag = document.createElement('span');
      filterTag.classList.add('filter-tag');
      filterTag.setAttribute('data-stat', stat);
      
      // Find the button for this stat to get its text
      const statButton = document.querySelector(`.stat-filter[data-stat="${stat}"]`);
      filterTag.textContent = statButton ? statButton.textContent : stat;
      
      // Add click handler to remove this filter
      filterTag.addEventListener('click', function() {
        // Find and deactivate the corresponding button
        const button = document.querySelector(`.stat-filter[data-stat="${stat}"]`);
        if (button) {
          button.classList.remove('active');
          // Trigger click event on the button to update filters
          button.click();
        }
      });
      
      filtersList.appendChild(filterTag);
    });
  }
  
  // Direct DOM filtering by tier (fallback if ItemsManager not available)
  function filterItemsByTier(tier) {
    console.log(`Direct DOM filtering by tier: ${tier}`);
    
    // Make API call to refresh items with selected tier
    if (tier === 'all') {
      // Show all items for 'all' tier
      refreshItemDisplay();
      return;
    }
    
    // Handle tier mapping
    const numericTier = getNumericTier(tier);
    
    // Refresh the item display with the selected tier filter
    refreshItemDisplay(tier, numericTier);
  }
  
  // Get numeric tier value from tier name
  function getNumericTier(tier) {
    switch(tier) {
      case 'mythic': return 4;
      case 'legendary': return 3;
      case 'epic': return 2;
      case 'basic': return 1;
      case 'starter': return 0;
      default: return -1; // All tiers
    }
  }
  
  // Direct DOM filtering by stats (fallback if ItemsManager not available)
  function filterItemsByStats(stats) {
    console.log(`Direct DOM filtering by stats: ${stats.join(', ')}`);
    
    // Get current active tier
    const activeTierButton = document.querySelector('.tier-filter.active');
    const tier = activeTierButton ? activeTierButton.getAttribute('data-tier') : 'all';
    
    // Refresh with both tier and stats
    refreshItemDisplay(tier, getNumericTier(tier), stats);
  }
  
  // Helper to refresh the item display with filters
  function refreshItemDisplay(tier = 'all', numericTier = -1, stats = []) {
    // First get all item cards
    const allItems = document.querySelectorAll('.item-card');
    
    // Set visibility of each item card based on filters
    allItems.forEach(item => {
      let visible = true;
      
      // Apply tier filter if not 'all'
      if (tier !== 'all') {
        // Check for tier class
        if (!item.classList.contains(`tier-${tier}`)) {
          // Check data attributes
          const itemTier = item.getAttribute('data-tier') || 
                           item.getAttribute('data-item-tier');
          
          // If no match in class or data attributes, hide this item
          if (itemTier !== tier && parseInt(itemTier) !== numericTier) {
            visible = false;
          }
        }
      }
      
      // Apply stat filters if any are active
      if (visible && stats.length > 0) {
        // Check if the item has any of the selected stats
        const hasMatchingStat = stats.some(stat => {
          // Try to find by data attribute
          if (item.hasAttribute(`data-${stat}`)) {
            return true;
          }
          
          // Try to find stat in description
          const description = item.getAttribute('data-description') || '';
          const itemName = item.querySelector('.item-name')?.textContent || '';
          const itemText = (description + ' ' + itemName).toLowerCase();
          
          // Check for stat keywords
          const keywords = getStatKeywords(stat);
          return keywords.some(keyword => itemText.includes(keyword));
        });
        
        if (!hasMatchingStat) {
          visible = false;
        }
      }
      
      // Apply visibility
      item.style.display = visible ? '' : 'none';
    });
    
    // Update category visibility
    updateCategoryVisibility();
  }
  
  // Get keywords for a stat
  function getStatKeywords(stat) {
    const statKeywords = {
      'ad': ['attack damage', 'ad', 'physical damage'],
      'ap': ['ability power', 'ap', 'magic damage'],
      'armor': ['armor'],
      'mr': ['magic resist', 'mr', 'magic resistance'],
      'hp': ['health', 'hp'],
      'mana': ['mana', 'mp'],
      'as': ['attack speed'],
      'crit': ['critical', 'crit'],
      'ms': ['movement speed', 'move speed'],
      'utility': ['cooldown', 'cdr', 'heal', 'shield', 'active']
    };
    
    return statKeywords[stat] || [];
  }
  
  // Update category visibility based on visible items
  function updateCategoryVisibility() {
    // Get all item categories
    const categories = document.querySelectorAll('.item-category');
    
    // For each category
    categories.forEach(category => {
      // Get all items in this category
      const items = category.querySelectorAll('.item-card');
      
      // Count visible items
      let visibleCount = 0;
      items.forEach(item => {
        if (item.style.display !== 'none') {
          visibleCount++;
        }
      });
      
      // Update count in category title if present
      const countElement = category.parentElement.querySelector('.category-count');
      if (countElement) {
        countElement.textContent = `${visibleCount} items`;
      }
      
      // Show/hide category based on visible items
      if (visibleCount > 0) {
        category.style.display = '';
        if (category.parentElement) {
          const title = category.parentElement.querySelector('.item-category-title');
          if (title) title.style.display = '';
        }
      } else {
        category.style.display = 'none';
        if (category.parentElement) {
          const title = category.parentElement.querySelector('.item-category-title');
          if (title) title.style.display = 'none';
        }
      }
    });
    
    // Check if any categories are visible
    let visibleCategories = 0;
    categories.forEach(category => {
      if (category.style.display !== 'none') {
        visibleCategories++;
      }
    });
    
    // Show/hide no results message
    const noResultsElement = document.getElementById('no-results-items');
    const itemsListElement = document.getElementById('items-list');
    
    if (visibleCategories === 0) {
      if (noResultsElement) noResultsElement.style.display = 'block';
      if (itemsListElement) itemsListElement.style.display = 'none';
    } else {
      if (noResultsElement) noResultsElement.style.display = 'none';
      if (itemsListElement) itemsListElement.style.display = 'block';
    }
  }
});

// When the page loads, store a reference to the ItemsManager if it exists
window.addEventListener('load', function() {
  // Wait for popup.js to initialize the ItemsManager
  setTimeout(function() {
    if (window.ItemsManager) {
      // Try to find the ItemsManager instance
      const itemsView = document.getElementById('items-view');
      if (itemsView && itemsView.__itemsManager) {
        window.itemsManager = itemsView.__itemsManager;
        console.log('Found ItemsManager instance');
      }
    }
  }, 1000);
});