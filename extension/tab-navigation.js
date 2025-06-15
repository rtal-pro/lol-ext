// Tab navigation functionality for League of Legends Helper extension

// Requires utils.js to be loaded first

class TabNavigationManager {
  constructor() {
    // Initialize navigation 
    this.setupGlobalNavigation();
    this.setupDetailTabNavigation();
  }

  // Set up main navigation between champions and items views
  setupGlobalNavigation() {
    console.log('Setting up global navigation');
    
    // Get references to DOM elements - Navigation
    this.championNavButton = document.getElementById('champions-nav');
    this.itemsNavButton = document.getElementById('items-nav');
    this.championsView = document.getElementById('champions-view');
    this.itemsView = document.getElementById('items-view');
    this.championsSearchContainer = document.getElementById('champions-search-container');
    this.itemsSearchContainer = document.getElementById('item-filters-container');
    
    // Track current view
    this.currentView = 'champions';
    
    // Set up navigation events
    var self = this;
    this.championNavButton.addEventListener('click', function() {
      self.switchView('champions');
    });
    this.itemsNavButton.addEventListener('click', function() {
      self.switchView('items');
    });
  }

  // Function to switch between main views (champions and items)
  switchView(viewName) {
    console.log(`Switching view to: ${viewName}`);
    
    // Update current view
    this.currentView = viewName;
    
    // Update active nav button
    this.championNavButton.classList.toggle('active', viewName === 'champions');
    this.itemsNavButton.classList.toggle('active', viewName === 'items');
    
    // Toggle the appropriate search containers
    if (viewName === 'champions') {
      // Show champions search container, hide items search container
      if (this.championsSearchContainer) this.championsSearchContainer.style.display = 'block';
      if (this.itemsSearchContainer) this.itemsSearchContainer.style.display = 'none';
    } else {
      // Show items search container, hide champions search container
      if (this.championsSearchContainer) this.championsSearchContainer.style.display = 'none';
      if (this.itemsSearchContainer) this.itemsSearchContainer.style.display = 'block';
    }
    
    // Update visible section
    this.championsView.style.display = viewName === 'champions' ? 'block' : 'none';
    this.itemsView.style.display = viewName === 'items' ? 'block' : 'none';
    
    // Make sure the class toggles are also applied
    this.championsView.classList.toggle('active', viewName === 'champions');
    this.itemsView.classList.toggle('active', viewName === 'items');
    
    // Update search placeholder
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
      searchInput.placeholder = viewName === 'champions' 
        ? 'Search champions...' 
        : 'Search items...';
    }
    
    // Reset any item detail view if switching to items view
    if (viewName === 'items') {
      const itemDetail = document.getElementById('item-detail');
      const itemsList = document.getElementById('items-list');
      
      if (itemDetail) itemDetail.style.display = 'none';
      if (itemsList) itemsList.style.display = 'grid';
      
      // Force the "all" tier to be selected to show all items
      const itemTierButtons = document.querySelectorAll('.tier-button');
      itemTierButtons.forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-tier') === 'all');
      });
    }
    
    // Trigger view-specific initialization through custom event
    const event = new CustomEvent('viewChanged', { 
      detail: { view: viewName } 
    });
    document.dispatchEvent(event);
  }
  
  // Set up tab navigation for detail views
  setupDetailTabNavigation() {
    console.log("Setting up detail tab navigation handlers");
    
    var self = this;
    
    // Set up champions tab navigation
    document.addEventListener('championDetailShown', function() {
      window.LOLUtils.setupTabNavigation();
    });
    
    // Set up items tab navigation
    document.addEventListener('itemDetailShown', function() {
      self.setupItemTabNavigation();
    });
    
    // Handle mutations to detect when item detail is shown
    var observer = new MutationObserver(function(mutations) {
      mutations.forEach(function(mutation) {
        if (mutation.target.id === 'item-detail' && 
            window.getComputedStyle(mutation.target).display === 'block') {
          console.log("Item detail displayed - fixing tabs");
          window.LOLUtils.fixItemDetailTabs();
        }
      });
    });
    
    // Start observing the item detail element
    const itemDetailElement = document.getElementById('item-detail');
    if (itemDetailElement) {
      observer.observe(itemDetailElement, { 
        attributes: true,
        attributeFilter: ['style']
      });
      console.log("Observer set up for item detail");
    }
  }
  
  // Function to set up item tab navigation
  setupItemTabNavigation() {
    console.log("Setting up item tab navigation");
    
    var tabButtons = document.querySelectorAll('.item-tab-button');
    var tabPanes = document.querySelectorAll('.item-tab-pane');
    
    console.log("Found tab buttons:", tabButtons.length);
    console.log("Found tab panes:", tabPanes.length);
    
    for (var i = 0; i < tabButtons.length; i++) {
      var button = tabButtons[i];
      var tabId = button.getAttribute('data-tab');
      console.log('Setting up click handler for tab:', tabId);
      
      // Using an IIFE to create a closure for tabId
      (function(currentTabId, currentButton) {
        currentButton.addEventListener('click', function() {
          console.log('Tab clicked:', currentTabId);
          
          // Remove active class from all buttons and panes
          for (var j = 0; j < tabButtons.length; j++) {
            tabButtons[j].classList.remove('active');
          }
          
          for (var k = 0; k < tabPanes.length; k++) {
            tabPanes[k].classList.remove('active');
          }
          
          // Add active class to current button
          currentButton.classList.add('active');
          
          // Get tab id and activate corresponding pane
          var targetPane = document.getElementById(currentTabId + '-tab');
          console.log('Target pane for ' + currentTabId + ':', targetPane);
          
          if (targetPane) {
            targetPane.classList.add('active');
            
            // Special handling for stats tab
            if (currentTabId === 'stats') {
              var statsElement = targetPane.querySelector('.item-stats');
              if (statsElement && statsElement.children.length <= 1) {
                console.log("Stats tab clicked but still empty, force adding stats");
                
                // Add default stats directly
                window.LOLUtils.forceDefaultStats(statsElement);
              }
            }
          } else {
            console.error('Tab pane not found for tab: ' + currentTabId);
          }
        });
      })(tabId, button);
    }
    
    // Force activate the stats tab button on initialization
    var statsButton = document.querySelector('.item-tab-button[data-tab="stats"]');
    if (statsButton) {
      console.log("Force activating stats tab button");
      setTimeout(function() {
        statsButton.click();
      }, 100);
    }
  }
}

// Export the class
window.TabNavigationManager = TabNavigationManager;