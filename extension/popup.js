// Main JavaScript for the League of Legends Helper extension
// This file initializes the app and handles shared functionality

document.addEventListener('DOMContentLoaded', function() {
  console.log('League of Legends Helper extension loaded');
  
  // Initialize managers
  let championsManager = null;
  let itemsManager = null;
  let runesManager = null;
  let tabNavigationManager = null;
  let searchHandler = null;
  
  // Initialize the app
  function initializeUI() {
    // Fetch current game version
    window.LOLUtils.fetchGameVersion();
    
    // Initialize tab navigation manager
    tabNavigationManager = new window.TabNavigationManager();
    
    // Initialize search handler
    searchHandler = new window.SearchHandler();
    
    // Initialize the champions manager first since that's the default view
    championsManager = new window.ChampionsManager();
    championsManager.fetchChampions();
    
    // Register managers with search handler
    searchHandler.registerManagers(championsManager, itemsManager, runesManager);
    
    // Listen for view changes to initialize managers as needed
    document.addEventListener('viewChanged', function(e) {
      if (!e || !e.detail) {
        console.error('Invalid event or missing detail property');
        return;
      }
        
      const viewName = e.detail.view;
      console.log(`View changed to: ${viewName}`);
      
      // Load data if needed
      if (viewName === 'champions') {
        // Initialize champions manager if needed
        if (!championsManager) {
          championsManager = new window.ChampionsManager();
          championsManager.fetchChampions();
          searchHandler.registerManagers(championsManager, itemsManager);
        }
      } else if (viewName === 'items') {
        // Check if we already have a global instance
        if (window.itemsManager) {
          console.log('Using existing global ItemsManager instance');
          itemsManager = window.itemsManager;
          
          // Make sure items are loaded
          if (itemsManager.allItems && itemsManager.allItems.length > 0) {
            // Items already loaded, just re-display
            itemsManager.displayItems();
          } else {
            // Items not loaded yet, fetch them
            itemsManager.fetchItems();
          }
          
          searchHandler.registerManagers(championsManager, itemsManager, runesManager);
        } 
        // Initialize items manager if needed and not already available globally
        else if (!itemsManager) {
          try {
            console.log('Creating new ItemsManager instance');
            itemsManager = new window.ItemsManager();
            window.itemsManager = itemsManager; // Share it globally
            itemsManager.fetchItems();
            searchHandler.registerManagers(championsManager, itemsManager, runesManager);
          } catch (error) {
            console.error('Error creating ItemsManager:', error);
          }
        } else {
          // Re-display items whenever we switch to the items view
          itemsManager.displayItems();
        }
        
        // Setup stat filters when switching to items view
        if (itemsManager) {
          setTimeout(function() {
            if (itemsManager.setupStatFilters) {
              itemsManager.setupStatFilters();
            }
          }, 300);
        }
      } else if (viewName === 'runes') {
        // Check if we already have a global instance
        if (window.runesManager) {
          console.log('Using existing global RunesManager instance');
          runesManager = window.runesManager;
          
          // Make sure runes are loaded
          if (runesManager.allStyles && runesManager.allStyles.length > 0) {
            // Runes already loaded, just re-display
            runesManager.displayRuneStyles();
          } else {
            // Runes not loaded yet, fetch them
            runesManager.fetchRunes();
          }
          
          searchHandler.registerManagers(championsManager, itemsManager, runesManager);
        } 
        // Initialize runes manager if needed and not already available globally
        else if (!runesManager) {
          try {
            console.log('Creating new RunesManager instance');
            runesManager = new window.RunesManager();
            window.runesManager = runesManager; // Share it globally
            runesManager.fetchRunes();
            searchHandler.registerManagers(championsManager, itemsManager, runesManager);
          } catch (error) {
            console.error('Error creating RunesManager:', error);
          }
        } else {
          // Re-display runes whenever we switch to the runes view
          runesManager.displayRuneStyles();
        }
      }
    });
  }
  
  // Start the app
  initializeUI();
});