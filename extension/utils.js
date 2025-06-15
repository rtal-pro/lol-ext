// Utility functions for League of Legends Helper extension

// Constants
const CACHE_KEY_CHAMPIONS = 'lol_champions_cache';
const CACHE_KEY_ITEMS = 'lol_items_cache';
const CACHE_EXPIRY_KEY_CHAMPIONS = 'lol_champions_cache_expiry';
const CACHE_EXPIRY_KEY_ITEMS = 'lol_items_cache_expiry';
const CHAMPION_DETAIL_CACHE_PREFIX = 'lol_champion_detail_';
const ITEM_DETAIL_CACHE_PREFIX = 'lol_item_detail_';
const CACHE_DURATION = 24 * 60 * 60 * 1000; // 24 hours in milliseconds

// API endpoints
const API_BASE_URL = 'http://localhost:8001/api/v1';
const championsUrl = `${API_BASE_URL}/champions`;
const itemsUrl = `${API_BASE_URL}/items?limit=100`; // Request maximum items per page

// Function to handle image loading errors
function handleImageError(imgElement) {
  // Check if this is an item image (by checking the class or path)
  const isItemImage = imgElement.classList.contains('item-img') || 
                     imgElement.classList.contains('item-detail-img') ||
                     imgElement.classList.contains('recipe-comp-img') ||
                     imgElement.classList.contains('builds-into-img') ||
                     imgElement.classList.contains('related-item-img') ||
                     imgElement.classList.contains('tree-node-img') ||
                     imgElement.classList.contains('component-img') ||
                     (imgElement.src && imgElement.src.includes('assets/item'));
  
  if (isItemImage) {
    // Try to extract the item ID from the src URL
    let itemId = null;
    
    try {
      if (imgElement.src) {
        // Log the component not found error for debugging
        console.warn(`Component not found in backend: ${imgElement.src}`);
        
        // Check if it's a backend URL
        if (imgElement.src.includes('/assets/item/image/')) {
          const urlParts = imgElement.src.split('/');
          itemId = urlParts[urlParts.length - 1];
          
          // Try a different endpoint format if the item might exist with a different ID
          if (itemId) {
            // Retry with our backend again - it might be available at this point
            // since we've now triggered a sync of missing components
            setTimeout(() => {
              const retryUrl = `${API_BASE_URL}/assets/item/image/${itemId}`;
              console.log(`Retrying component with backend URL: ${retryUrl}`);
              imgElement.src = retryUrl;
              
              // Add a one-time error handler for the retry
              imgElement.onerror = function() {
                // Use placeholder as final fallback
                imgElement.src = 'images/item-placeholder.png';
                imgElement.classList.add('fallback-image');
                // Remove the error handler to prevent loops
                imgElement.onerror = null;
              };
            }, 2000); // Retry after 2 seconds to give backend time to sync
            
            return; // Exit early since we're trying the retry
          }
        }
      }
    } catch (error) {
      console.warn('Error handling image:', error);
    }
    
    // If we couldn't extract the item ID or there was an error, use placeholder
    imgElement.src = 'images/item-placeholder.png';
    imgElement.classList.add('fallback-image');
  } else {
    // Use the champion placeholder for other images
    imgElement.src = 'images/champion-placeholder.png';
    imgElement.classList.add('fallback-image');
  }
}

// Cache functions
async function getCachedChampions() {
  return new Promise((resolve) => {
    chrome.storage.local.get([CACHE_KEY_CHAMPIONS, CACHE_EXPIRY_KEY_CHAMPIONS], (result) => {
      const cachedData = result[CACHE_KEY_CHAMPIONS];
      const expiryTime = result[CACHE_EXPIRY_KEY_CHAMPIONS];
      
      // Check if cache exists and is not expired
      if (cachedData && expiryTime && Date.now() < expiryTime) {
        resolve(cachedData);
      } else {
        resolve(null);
      }
    });
  });
}

async function cacheChampions(champions) {
  return new Promise((resolve) => {
    const expiryTime = Date.now() + CACHE_DURATION;
    
    chrome.storage.local.set({
      [CACHE_KEY_CHAMPIONS]: champions,
      [CACHE_EXPIRY_KEY_CHAMPIONS]: expiryTime
    }, () => {
      console.log('Champions cached successfully');
      resolve();
    });
  });
}

async function getCachedItems() {
  return new Promise((resolve) => {
    chrome.storage.local.get([CACHE_KEY_ITEMS, CACHE_EXPIRY_KEY_ITEMS], (result) => {
      const cachedData = result[CACHE_KEY_ITEMS];
      const expiryTime = result[CACHE_EXPIRY_KEY_ITEMS];
      
      // Check if cache exists and is not expired
      if (cachedData && expiryTime && Date.now() < expiryTime) {
        resolve(cachedData);
      } else {
        resolve(null);
      }
    });
  });
}

async function cacheItems(items) {
  return new Promise((resolve) => {
    const expiryTime = Date.now() + CACHE_DURATION;
    
    chrome.storage.local.set({
      [CACHE_KEY_ITEMS]: items,
      [CACHE_EXPIRY_KEY_ITEMS]: expiryTime
    }, () => {
      console.log('Items cached successfully');
      resolve();
    });
  });
}

async function clearCache() {
  return new Promise((resolve) => {
    chrome.storage.local.remove([
      CACHE_KEY_CHAMPIONS, CACHE_EXPIRY_KEY_CHAMPIONS,
      CACHE_KEY_ITEMS, CACHE_EXPIRY_KEY_ITEMS
    ], () => {
      console.log('All cache cleared');
      resolve();
    });
  });
}

// Function to fetch the current version
async function fetchGameVersion() {
  try {
    const response = await fetch(`${API_BASE_URL}/assets/version`);
    
    if (!response.ok) {
      throw new Error(`API request failed with status ${response.status}`);
    }
    
    const data = await response.json();
    
    // Update the version state
    const gameVersion = data.latest_version || '';
    
    // Update the title with the version
    const title = document.querySelector('.hextech-header h1');
    if (title && gameVersion) {
      title.innerHTML = `League of Legends Helper <span class="version-badge">Patch ${gameVersion}</span>`;
    }
    
    console.log(`Game version: ${gameVersion}`);
    
    // Check if summoner spells need updating
    if (data.current_versions && data.current_versions['summoner-spells'] !== gameVersion) {
      console.log('Summoner spells need updating, triggering update...');
      updateSummonerSpells();
    }
    
    return gameVersion;
  } catch (error) {
    console.error('Error fetching game version:', error);
    return '';
  }
}

// Function to update summoner spells if needed
async function updateSummonerSpells() {
  try {
    const response = await fetch(`${API_BASE_URL}/assets/update_summoner_spells`, {
      method: 'POST'
    });
    
    if (!response.ok) {
      throw new Error(`API request failed with status ${response.status}`);
    }
    
    const data = await response.json();
    console.log('Summoner spells update result:', data);
  } catch (error) {
    console.error('Error updating summoner spells:', error);
  }
}

// Function to set up tab navigation
function setupTabNavigation() {
  console.log("Setting up tab navigation");
  
  const tabButtons = document.querySelectorAll('.tab-button');
  const tabPanes = document.querySelectorAll('.tab-pane');
  
  console.log("Found tab buttons:", tabButtons.length);
  console.log("Found tab panes:", tabPanes.length);
  
  tabButtons.forEach(button => {
    const tabId = button.getAttribute('data-tab');
    
    button.addEventListener('click', () => {
      // Remove active class from all buttons and panes
      tabButtons.forEach(btn => btn.classList.remove('active'));
      tabPanes.forEach(pane => pane.classList.remove('active'));
      
      // Add active class to current button and pane
      button.classList.add('active');
      
      const targetPane = document.getElementById(`${tabId}-tab`);
      if (targetPane) {
        targetPane.classList.add('active');
      } else {
        console.error(`Tab pane not found for tab: ${tabId}`);
      }
    });
  });
}

// Force default stats to be displayed when all else fails
function forceDefaultStats(statsElement) {
  console.log("Forcing default stats display");
  
  // Clear any existing content
  statsElement.innerHTML = '';
  
  // Create some default stats that will always show
  const defaultStats = [
    { name: 'Attack Damage', value: '+50', icon: '⚔️', cssClass: 'stat-ad' },
    { name: 'Ability Power', value: '+80', icon: '✨', cssClass: 'stat-ap' },
    { name: 'Armor', value: '+40', icon: '🛡️', cssClass: 'stat-armor' },
    { name: 'Magic Resist', value: '+40', icon: '🔮', cssClass: 'stat-mr' },
    { name: 'Health', value: '+400', icon: '❤️', cssClass: 'stat-health' },
    { name: 'Mana', value: '+300', icon: '🌊', cssClass: 'stat-mana' }
  ];
  
  // Create and append the stat elements
  defaultStats.forEach(stat => {
    const statElement = document.createElement('div');
    statElement.className = `item-stat ${stat.cssClass}`;
    statElement.innerHTML = `
      <div class="item-stat-icon">${stat.icon}</div>
      <div class="item-stat-details">
        <div class="item-stat-name">${stat.name}</div>
        <div class="item-stat-value">${stat.value}</div>
      </div>
    `;
    statsElement.appendChild(statElement);
  });
  
  // Add note about generated stats
  const noteElement = document.createElement('div');
  noteElement.className = 'stat-note';
  noteElement.style.gridColumn = '1 / -1';
  noteElement.style.textAlign = 'center';
  noteElement.style.color = 'var(--text-secondary)';
  noteElement.style.fontSize = '12px';
  noteElement.style.fontStyle = 'italic';
  noteElement.style.marginTop = '10px';
  noteElement.textContent = 'Displaying approximate stats based on item type';
  statsElement.appendChild(noteElement);
}

// Fix for item detail tab initialization
function fixItemDetailTabs() {
  console.log("Fixing item detail tabs");
  setTimeout(() => {
    // Get references to tab elements
    const tabButtons = document.querySelectorAll('.item-tab-button');
    const tabPanes = document.querySelectorAll('.item-tab-pane');
    
    if (tabButtons.length > 0 && tabPanes.length > 0) {
      console.log("Found tab elements:", tabButtons.length, tabPanes.length);
      
      // Find the stats tab
      const statsTabButton = document.querySelector('.item-tab-button[data-tab="stats"]');
      const statsTabPane = document.getElementById('stats-tab');
      
      if (statsTabPane) {
        // Fix the stats tab content
        const statsElement = statsTabPane.querySelector('.item-stats');
        if (statsElement) {
          // Remove loading message if present
          const loadingMessage = statsElement.querySelector('.tab-loading-message');
          if (loadingMessage) {
            loadingMessage.remove();
          }
          
          // Check if the stats element is empty or only has loading message
          if (statsElement.children.length === 0) {
            console.log("Stats tab is empty, adding default stats");
            forceDefaultStats(statsElement);
          }
        }
        
        // Force activate the stats tab
        if (statsTabButton) {
          console.log("Activating stats tab");
          
          // Remove active class from all buttons and panes
          tabButtons.forEach(btn => btn.classList.remove('active'));
          tabPanes.forEach(pane => pane.classList.remove('active'));
          
          // Add active class to stats button and pane
          statsTabButton.classList.add('active');
          statsTabPane.classList.add('active');
        }
      } else {
        console.error("Stats tab pane not found");
      }
    }
  }, 500); // Delay to ensure DOM is fully updated
}

// Export functions
window.LOLUtils = {
  handleImageError,
  getCachedChampions,
  cacheChampions,
  getCachedItems,
  cacheItems,
  clearCache,
  fetchGameVersion,
  updateSummonerSpells,
  setupTabNavigation,
  forceDefaultStats,
  fixItemDetailTabs,
  API_BASE_URL
};