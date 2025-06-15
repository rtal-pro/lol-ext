/**
 * Direct DOM-based stat filtering for items
 * This implementation doesn't rely on any specific data structure from popup.js,
 * it works directly with the elements in the DOM.
 */
document.addEventListener('DOMContentLoaded', function() {
  console.log('Initializing stat filters');
  
  // Initialize the stat filters when the items tab is clicked or when items are loaded
  var itemsNavButton = document.getElementById('items-nav');
  if (itemsNavButton) {
    itemsNavButton.addEventListener('click', function() {
      console.log('Items tab clicked, checking for items to filter...');
      // Add small delay to ensure DOM updates
      setTimeout(checkAndSetupFilters, 300);
    });
  }
  
  // Also try to set up filters when the page loads
  setTimeout(checkAndSetupFilters, 500);
  
  // Function to check for items and set up filters if available
  function checkAndSetupFilters() {
    var itemCards = document.querySelectorAll('.item-card');
    if (itemCards.length > 0) {
      console.log(`Items found (${itemCards.length}), setting up filters`);
      setupStatFilters();
    } else {
      console.log('No items found yet, waiting for items to load');
      
      // Wait for items view to be shown
      var observer = new MutationObserver(function(mutations) {
        for (var i = 0; i < mutations.length; i++) {
          var mutation = mutations[i];
          // Look for added nodes that might be item cards
          if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
            // Check if items list has any children now
            var itemCards = document.querySelectorAll('.item-card');
            if (itemCards.length > 0) {
              console.log('Items loaded (' + itemCards.length + '), setting up filters');
              observer.disconnect();
              setupStatFilters();
              return;
            }
          }
          
          // Also check style changes on the items view
          if (mutation.type === 'attributes' && 
              mutation.attributeName === 'style') {
            var itemsView = document.querySelector('#items-view');
            if (itemsView && itemsView.style.display !== 'none') {
              // Check if items are loaded
              var itemCards = document.querySelectorAll('.item-card');
              if (itemCards.length > 0) {
                console.log('Items loaded (' + itemCards.length + '), setting up filters');
                observer.disconnect();
                setupStatFilters();
                return;
              }
            }
          }
        }
      });
      
      // Start observing items list for both style changes and child additions
      var itemsList = document.querySelector('#items-list');
      var itemsView = document.querySelector('#items-view');
      
      if (itemsList) {
        observer.observe(itemsList, {
          childList: true,
          subtree: true
        });
      }
      
      if (itemsView) {
        observer.observe(itemsView, {
          attributes: true,
          attributeFilter: ['style']
        });
      }
    }
  }
  
  // Main setup function for stat filters
  function setupStatFilters() {
    // Track active stat filters
    var activeStats = [];
    
    // Find all stat filter buttons
    var statButtons = document.querySelectorAll('.stat-category-filter');
    console.log(`Found ${statButtons.length} stat filter buttons`);
    
    // Make sure we start with a clean state
    for (var i = 0; i < statButtons.length; i++) {
      statButtons[i].classList.remove('active');
    }
    
    // Direct event handling setup - no cloning
    for (var j = 0; j < statButtons.length; j++) {
      var button = statButtons[j];
      // First, remove all existing click event listeners
      var oldButton = button;
      var newButton = oldButton.cloneNode(true);
      
      if (oldButton.parentNode) {
        console.log(`Setting up click handler for stat button: ${newButton.getAttribute('data-stat')}`);
        oldButton.parentNode.replaceChild(newButton, oldButton);
        
        // Add direct inline onclick handler for maximum compatibility
        newButton.onclick = function(event) {
          event.preventDefault();
          event.stopPropagation();
          
          const stat = this.getAttribute('data-stat');
          console.log(`Stat filter clicked: ${stat}`);
          
          // Toggle active state
          if (this.classList.contains('active')) {
            // Remove stat from active filters
            this.classList.remove('active');
            activeStats = activeStats.filter(s => s !== stat);
          } else {
            // Add stat to active filters
            this.classList.add('active');
            activeStats.push(stat);
            
            // Add visual feedback
            this.style.animation = 'none';
            var animButton = this;
            setTimeout(function() {
              animButton.style.animation = 'pulse 0.3s';
            }, 10);
          }
          
          console.log(`Active stat filters: ${activeStats.join(', ')}`);
          
          // Apply filters
          applyStatFilters(activeStats);
          
          // Return false to prevent any default behavior
          return false;
        };
      } else {
        console.error(`Button has no parent node: ${button.getAttribute('data-stat')}`);
      }
    });
    
    // Set up clear button
    const clearButton = document.getElementById('clear-item-filters');
    if (clearButton) {
      // Remove existing event listeners
      const newClearButton = clearButton.cloneNode(true);
      clearButton.parentNode.replaceChild(newClearButton, clearButton);
      
      // Add direct inline onclick handler for maximum compatibility
      newClearButton.onclick = function(event) {
        event.preventDefault();
        event.stopPropagation();
        
        console.log('Clearing all stat filters');
        
        // Reset active stats
        activeStats = [];
        
        // Reset all stat buttons
        document.querySelectorAll('.stat-category-filter').forEach(btn => 
          btn.classList.remove('active')
        );
        
        // Show all items
        applyStatFilters([]);
        
        // Return false to prevent any default behavior
        return false;
      };
    }
    
    // Make sure tier buttons re-apply stat filters when clicked
    const tierButtons = document.querySelectorAll('.tier-button');
    tierButtons.forEach(button => {
      // Store old onclick handler if it exists
      const oldOnClick = button.onclick;
      
      // Replace with new handler that calls the old one and then reapplies filters
      button.onclick = function(event) {
        // Call original handler if it exists
        if (typeof oldOnClick === 'function') {
          oldOnClick.call(this, event);
        }
        
        // Give the original tier filter time to work
        setTimeout(() => {
          console.log('Tier changed, reapplying stat filters');
          applyStatFilters(activeStats);
        }, 100);
      };
    });
  }
  
  // Apply stat filters to items
  function applyStatFilters(activeStats) {
    console.log(`Applying stat filters: ${activeStats.join(', ')}`);
    
    // Get all visible item cards (respecting current tier filter)
    const itemsList = document.getElementById('items-list');
    if (!itemsList) {
      console.error('Items list container not found');
      return;
    }
    
    // First get all item cards
    const allItemCards = itemsList.querySelectorAll('.item-card');
    console.log(`Total item cards: ${allItemCards.length}`);
    
    // If no active stat filters, show all items
    if (activeStats.length === 0) {
      allItemCards.forEach(card => {
        card.style.display = '';
      });
      
      // Update category visibility
      updateCategoryVisibility();
      return;
    }
    
    // Process each item
    let matchCount = 0;
    allItemCards.forEach(card => {
      // Check if this item has any of the active stats
      const hasMatchingStat = cardHasAnyStat(card, activeStats);
      
      // Show/hide based on match
      if (hasMatchingStat) {
        card.style.display = '';
        matchCount++;
      } else {
        card.style.display = 'none';
      }
    });
    
    console.log(`Found ${matchCount} items matching the active stat filters`);
    
    // Update category visibility
    updateCategoryVisibility();
  }
  
  // Check if a card has any of the specified stats
  function cardHasAnyStat(card, stats) {
    // If no stats specified, always show the item
    if (!stats || stats.length === 0) {
      return true;
    }
    
    // Get all stat indicators on this card
    const indicators = card.querySelectorAll('.stat-indicator');
    if (indicators.length === 0) {
      return false;
    }
    
    // Check each requested stat
    for (const stat of stats) {
      // Get the CSS class for this stat
      const cssClass = getStatClass(stat);
      if (!cssClass) continue;
      
      // Check if any indicator has this class
      for (const indicator of indicators) {
        if (indicator.classList.contains(cssClass)) {
          return true;
        }
      }
    }
    
    // No matching stats found
    return false;
  }
  
  // Get the CSS class for a stat
  function getStatClass(stat) {
    const statClasses = {
      'ad': 'has-ad',
      'ap': 'has-ap',
      'armor': 'has-armor',
      'mr': 'has-mr',
      'hp': 'has-hp',
      'mana': 'has-mana',
      'as': 'has-as',
      'crit': 'has-crit',
      'ms': 'has-ms',
      'utility': 'has-utility'
    };
    
    return statClasses[stat] || '';
  }
  
  // Update category visibility based on visible items
  function updateCategoryVisibility() {
    var categories = document.querySelectorAll('.item-category');
    
    for (var i = 0; i < categories.length; i++) {
      var category = categories[i];
      // Get all items in this category
      var items = category.querySelectorAll('.item-card');
      
      // Count visible items
      var visibleItems = [];
      for (var j = 0; j < items.length; j++) {
        if (items[j].style.display !== 'none') {
          visibleItems.push(items[j]);
        }
      }
      
      // Update the category count
      var countElement = category.querySelector('.category-count');
      if (countElement) {
        countElement.textContent = visibleItems.length + ' items';
      }
      
      // Show/hide the category based on whether it has visible items
      if (visibleItems.length === 0) {
        category.style.display = 'none';
      } else {
        category.style.display = '';
      }
    };
  }
});