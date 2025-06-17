// Search functionality for League of Legends Helper extension

// Requires utils.js to be loaded first

class SearchHandler {
  constructor() {
    // Get references to DOM elements - Search
    this.searchInput = document.getElementById('search-input');
    this.searchClear = document.getElementById('search-clear');
    this.clearFiltersButton = document.getElementById('clear-filters');
    this.itemSearchInput = document.getElementById('item-search-input');
    this.itemSearchClear = document.getElementById('item-search-clear');
    
    // Track current view
    this.currentView = 'champions';
    
    // References to manager instances
    this.championsManager = null;
    this.itemsManager = null;
    this.runesManager = null;
    
    // Set up event listeners
    this._setupEventHandlers();
    
    // Listen for view changes
    var self = this;
    document.addEventListener('viewChanged', function(e) {
      if (e && e.detail) {
        self.currentView = e.detail.view;
      }
    });
  }
  
  // Register managers
  registerManagers(championsManager, itemsManager, runesManager) {
    this.championsManager = championsManager;
    this.itemsManager = itemsManager;
    this.runesManager = runesManager;
  }
  
  _setupEventHandlers() {
    var self = this;
    
    // Set up search input handler
    this.searchInput.addEventListener('input', function() {
      var searchValue = self.searchInput.value.trim();
      console.log('Raw input value: "' + self.searchInput.value + '", Trimmed: "' + searchValue + '"');
      
      // Show/hide clear button
      self.searchClear.style.display = searchValue ? 'block' : 'none';
      
      // Apply the filter based on current view
      if (self.currentView === 'champions' && self.championsManager) {
        self.championsManager.currentFilter.searchText = searchValue;
        self.championsManager.filterAndDisplayChampions();
      }
    });
    
    // Also handle keyup for immediate feedback
    this.searchInput.addEventListener('keyup', function(e) {
      console.log('Keyup event, key: ' + e.key + ', current value: "' + self.searchInput.value + '"');
      
      // Special handling for Enter key
      if (e.key === 'Enter' && self.championsManager) {
        self.championsManager.filterAndDisplayChampions();
      }
    });
    
    // Set up search clear button
    this.searchClear.addEventListener('click', function() {
      console.log('Search clear button clicked');
      self.searchInput.value = '';
      self.searchClear.style.display = 'none';
      
      // Re-filter based on current view
      if (self.currentView === 'champions' && self.championsManager) {
        self.championsManager.currentFilter.searchText = '';
        self.championsManager.filterAndDisplayChampions();
      } else if (self.currentView === 'items' && self.itemsManager) {
        self.itemsManager.itemFilter.searchText = '';
        self.itemsManager.displayItems();
      }
      
      // Focus back on search input
      self.searchInput.focus();
    });
    
    // Set up clear filters button
    this.clearFiltersButton.addEventListener('click', function() {
      if (self.championsManager) {
        self.championsManager.resetAllFilters();
      }
    });
    
    // Set up item search handlers
    if (this.itemSearchInput) {
      this.itemSearchInput.addEventListener('input', function() {
        var searchValue = self.itemSearchInput.value.trim();
        
        // Show/hide clear button
        if (self.itemSearchClear) {
          self.itemSearchClear.style.display = searchValue ? 'block' : 'none';
        }
        
        // Update item filter
        if (self.itemsManager) {
          self.itemsManager.itemFilter.searchText = searchValue;
          self.itemsManager.updateActiveFilters();
          self.itemsManager.displayItems();
        }
      });
    }
    
    // Set up rune search handlers
    const runeSearchInput = document.getElementById('rune-search-input');
    const runeSearchClear = document.getElementById('rune-search-clear');
    
    if (runeSearchInput) {
      runeSearchInput.addEventListener('input', function() {
        var searchValue = runeSearchInput.value.trim();
        
        // Show/hide clear button
        if (runeSearchClear) {
          runeSearchClear.style.display = searchValue ? 'block' : 'none';
        }
        
        // Update rune filter
        if (self.runesManager) {
          self.runesManager.filter.searchText = searchValue;
          self.runesManager.updateActiveFilters();
          self.runesManager.filterAndDisplayRunes();
        }
      });
    }
    
    // Set up item search clear button
    if (this.itemSearchClear) {
      this.itemSearchClear.addEventListener('click', function() {
        if (self.itemSearchInput) {
          self.itemSearchInput.value = '';
          self.itemSearchClear.style.display = 'none';
          
          // Update item filter
          if (self.itemsManager) {
            self.itemsManager.itemFilter.searchText = '';
            self.itemsManager.updateActiveFilters();
            self.itemsManager.displayItems();
          }
          
          // Focus back on search input
          self.itemSearchInput.focus();
        }
      });
    }
    
    // Set up rune search clear button
    if (runeSearchClear) {
      runeSearchClear.addEventListener('click', function() {
        if (runeSearchInput) {
          runeSearchInput.value = '';
          runeSearchClear.style.display = 'none';
          
          // Update rune filter
          if (self.runesManager) {
            self.runesManager.filter.searchText = '';
            self.runesManager.updateActiveFilters();
            self.runesManager.filterAndDisplayRunes();
          }
          
          // Focus back on search input
          runeSearchInput.focus();
        }
      });
    }
  }
}

// Export the class
window.SearchHandler = SearchHandler;