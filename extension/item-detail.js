/**
 * Item Detail Manager - Specialized component for handling item details
 * Uses a modular approach to decouple from the main item list functionality
 */

class ItemDetailManager {
  constructor() {
    // Get references to DOM elements
    this.itemDetail = document.getElementById('item-detail');
    this.backToItemsButton = document.getElementById('back-to-items-button');
    this.itemsListElement = document.getElementById('items-list');
    this.filtersContainer = document.getElementById('item-filters-container');
    
    // Initialize state
    this.currentItem = null;
    this.API_BASE_URL = window.LOLUtils ? window.LOLUtils.API_BASE_URL : '';
    this.isLoading = false;
    
    // Initialize event listeners
    this._setupEventListeners();
    
    console.log('ItemDetailManager initialized');
  }
  
  /**
   * Sets up event listeners for the component
   * Uses a pub/sub pattern to communicate with other components
   */
  _setupEventListeners() {
    // Listen for item selection events
    document.addEventListener('itemSelected', (event) => {
      const itemId = event.detail.itemId;
      console.log(`Item selected event received for ID: ${itemId}`);
      this.showItemDetail(itemId);
    });
    
    // Set up back button
    if (this.backToItemsButton) {
      this.backToItemsButton.addEventListener('click', () => {
        this.hideItemDetail();
        
        // Dispatch event to notify that we've returned to item list
        document.dispatchEvent(new CustomEvent('returnedToItemList'));
      });
    }
    
    // Listen for tab navigation
    const tabButtons = document.querySelectorAll('.item-tab-button');
    const tabPanes = document.querySelectorAll('.item-tab-pane');
    
    tabButtons.forEach(button => {
      button.addEventListener('click', () => {
        const tabId = button.getAttribute('data-tab');
        
        // Update active states
        tabButtons.forEach(btn => btn.classList.remove('active'));
        tabPanes.forEach(pane => pane.classList.remove('active'));
        
        // Activate selected tab
        button.classList.add('active');
        const targetPane = document.getElementById(`${tabId}-tab`);
        
        if (targetPane) {
          targetPane.classList.add('active');
          targetPane.style.display = 'block';
        }
      });
    });
  }
  
  /**
   * Shows the item detail view for a specific item
   * @param {string} itemId - The ID of the item to display
   */
  async showItemDetail(itemId) {
    // Prevent multiple simultaneous requests
    if (this.isLoading) return;
    
    this.isLoading = true;
    
    try {
      // Show the detail container first (for visual feedback)
      this.itemDetail.style.display = 'flex';
      
      // Hide item list and filters
      if (this.itemsListElement) {
        this.itemsListElement.style.display = 'none';
      }
      
      if (this.filtersContainer) {
        this.filtersContainer.style.display = 'none';
      }
      
      // Show loading states
      this._showLoadingState();
      
      // Fetch the item data
      const itemData = await this._fetchItemData(itemId);
      
      // Update current item reference
      this.currentItem = itemData;
      
      // Render the item detail
      this._renderItemDetail(itemData);
      
      // Hide loading states
      this._hideLoadingState();
      
      // Activate the default tab (stats)
      this._activateDefaultTab();
      
      // Scroll to top
      window.scrollTo(0, 0);
      
      // Animate entrance
      this._animateDetailEntrance();
      
    } catch (error) {
      console.error('Error showing item detail:', error);
      this._renderErrorState(error.message);
    } finally {
      this.isLoading = false;
    }
  }
  
  /**
   * Hides the item detail view and shows the item list
   */
  hideItemDetail() {
    // Hide detail view
    if (this.itemDetail) {
      // Animate exit first
      this.itemDetail.style.opacity = '0';
      this.itemDetail.style.transform = 'translateY(20px)';
      
      // Then hide after animation completes
      setTimeout(() => {
        this.itemDetail.style.display = 'none';
        this.itemDetail.style.opacity = '1';
        this.itemDetail.style.transform = 'translateY(0)';
      }, 300);
    }
    
    // Show items list
    if (this.itemsListElement) {
      this.itemsListElement.style.display = 'block';
    }
    
    // Show filters container
    if (this.filtersContainer) {
      this.filtersContainer.style.display = 'block';
    }
    
    // Clear current item
    this.currentItem = null;
  }
  
  /**
   * Shows loading states for all tabs
   */
  _showLoadingState() {
    // Show loading indicators
    document.querySelectorAll('.tab-loader').forEach(loader => {
      loader.style.display = 'flex';
    });
    
    // Show image loader
    const imageLoader = document.querySelector('.item-image-loader');
    if (imageLoader) {
      imageLoader.classList.remove('hidden');
    }
    
    // Clear previous content to avoid flashing
    const clearElements = [
      '.item-detail-name',
      '.item-detail-tier',
      '.gold-value',
      '.item-tier-indicator',
      '.item-stats',
      '.item-description',
      '.item-abilities-container',
      '.recipe-diagram',
      '.recipe-components',
      '.item-builds-into',
      '.related-items-scroll'
    ];
    
    clearElements.forEach(selector => {
      const element = document.querySelector(selector);
      if (element) {
        element.innerHTML = '';
      }
    });
    
    // Set image loader
    const imageElement = document.querySelector('.item-detail-image');
    if (imageElement) {
      imageElement.innerHTML = '<div class="item-image-loader"></div>';
    }
  }
  
  /**
   * Hides all loading states
   */
  _hideLoadingState() {
    // Hide all loading indicators
    document.querySelectorAll('.tab-loader').forEach(loader => {
      loader.style.display = 'none';
    });
    
    // Hide image loader
    const imageLoader = document.querySelector('.item-image-loader');
    if (imageLoader) {
      imageLoader.classList.add('hidden');
    }
  }
  
  /**
   * Activates the default tab (overview)
   */
  _activateDefaultTab() {
    const overviewButton = document.querySelector('.item-tab-button[data-tab="overview"]');
    if (overviewButton) {
      overviewButton.click();
    }
  }
  
  /**
   * Animates the entrance of the detail view
   */
  _animateDetailEntrance() {
    this.itemDetail.style.opacity = '0';
    this.itemDetail.style.transform = 'translateY(20px)';
    
    setTimeout(() => {
      this.itemDetail.style.transition = 'all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1)';
      this.itemDetail.style.opacity = '1';
      this.itemDetail.style.transform = 'translateY(0)';
    }, 50);
  }
  
  /**
   * Fetches item data from API or cache
   * @param {string} itemId - The ID of the item to fetch
   * @returns {Object} The item data
   */
  async _fetchItemData(itemId) {
    try {
      console.log(`Fetching item data for ID: ${itemId}`);
      
      // Try to get from cache first
      let cachedItems = [];
      if (window.LOLUtils && window.LOLUtils.getCachedItems) {
        cachedItems = await window.LOLUtils.getCachedItems() || [];
      }
      
      // Check cache
      let item = cachedItems.find(item => item.id === itemId);
      
      // If item exists in cache with full details, use it
      if (item && item.description) {
        console.log(`Using cached data for item: ${item.name}`);
        return item;
      }
      
      // Otherwise fetch from API
      console.log(`Fetching item details from API for ID: ${itemId}`);
      const response = await fetch(`${this.API_BASE_URL}/items/${itemId}`);
      
      if (!response.ok) {
        throw new Error(`API request failed with status ${response.status}`);
      }
      
      // Parse item data
      const itemData = await response.json();
      
      // Try to fetch additional recipe data
      try {
        const recipeResponse = await fetch(`${this.API_BASE_URL}/items/${itemId}/recipe?depth=2`);
        
        if (recipeResponse.ok) {
          const recipeData = await recipeResponse.json();
          
          // Merge recipe data with item data
          return { ...itemData, ...recipeData };
        }
      } catch (recipeError) {
        console.warn('Error fetching recipe data:', recipeError);
        // Continue with base item data
      }
      
      return itemData;
    } catch (error) {
      console.error('Error fetching item data:', error);
      throw error;
    }
  }
  
  /**
   * Renders the item detail view with the provided data
   * @param {Object} item - The item data to display
   */
  _renderItemDetail(item) {
    if (!item) {
      this._renderErrorState('Item data not available');
      return;
    }
    
    // Render item name and basic info
    this._renderItemHeader(item);
    
    // Render overview tab (stats + description)
    this._renderItemOverview(item);
    
    // Render build path
    this._renderBuildPath(item);
    
    // Render related items
    this._renderRelatedItems(item);
  }
  
  /**
   * Renders the item overview tab (combined stats and description)
   * @param {Object} item - The item data
   */
  _renderItemOverview(item) {
    // Render stats
    this._renderItemStats(item);
    
    // Render description
    this._renderItemDescription(item);
  }
  
  /**
   * Renders the item header section
   * @param {Object} item - The item data
   */
  _renderItemHeader(item) {
    // Set item name
    document.querySelector('.item-detail-name').textContent = item.name || 'Unknown Item';
    
    // Determine correct image URL with fallbacks
    let imageUrl;
    
    // First, always try our backend API for consistency with item list
    if (item.image) {
      // Use our backend API which should have all synced images
      imageUrl = `${this.API_BASE_URL}/assets/item/image/${item.id}`;
    } else {
      // Fallback to placeholder
      imageUrl = 'images/item-placeholder.png';
    }
      
    const itemDetailImage = document.querySelector('.item-detail-image');
    itemDetailImage.innerHTML = `
      <img src="${imageUrl}" alt="${item.name}" class="item-detail-img">
      <div class="item-image-loader hidden"></div>
    `;
    
    // Add image error handler
    const imgElement = itemDetailImage.querySelector('img');
    imgElement.addEventListener('error', function() {
      if (window.LOLUtils && window.LOLUtils.handleImageError) {
        window.LOLUtils.handleImageError(this);
      } else {
        // Try Dragon API as fallback if backend image fails
        if (this.src.includes('/assets/item/image/')) {
          this.src = `https://ddragon.leagueoflegends.com/cdn/13.21.1/img/item/${item.id}.png`;
        } else {
          // Final fallback to placeholder
          this.src = 'images/item-placeholder.png';
        }
      }
    });
    
    // Set tier indicator
    const tierIndicator = document.querySelector('.item-tier-indicator');
    const tier = this._getItemTier(item);
    let tierSymbol = '';
    let tierClass = '';
    
    switch(tier) {
      case 'mythic':
        tierSymbol = 'M';
        tierClass = 'tier-indicator-mythic';
        break;
      case 'legendary':
        tierSymbol = 'L';
        tierClass = 'tier-indicator-legendary';
        break;
      case 'epic':
        tierSymbol = 'E';
        tierClass = 'tier-indicator-epic';
        break;
      default:
        tierSymbol = 'B';
    }
    
    tierIndicator.innerHTML = tierSymbol;
    tierIndicator.className = `item-tier-indicator ${tierClass}`;
    
    // Set tier badge
    const tierElement = document.querySelector('.item-detail-tier');
    let tierName = tier.charAt(0).toUpperCase() + tier.slice(1);
    
    tierElement.innerHTML = `<span class="item-tier-badge ${tierClass}">${tierName}</span>`;
    
    // Set gold info
    const goldElement = document.querySelector('.gold-value');
    if (item.gold && item.gold.total) {
      goldElement.textContent = `${item.gold.total}`;
      
      if (item.gold.sell) {
        goldElement.textContent += ` (Sells for: ${item.gold.sell})`;
      }
    } else {
      goldElement.textContent = 'No cost';
    }
  }
  
  /**
   * Renders the item stats section
   * @param {Object} item - The item data
   */
  _renderItemStats(item) {
    const statsElement = document.querySelector('.item-stats');
    
    // Extract stats from item data
    const statsArray = this._extractItemStats(item);
    
    if (statsArray.length > 0) {
      // Clear existing content
      statsElement.innerHTML = '';
      
      // Render each stat
      statsArray.forEach(stat => {
        const statElement = document.createElement('div');
        statElement.className = `item-stat ${stat.cssClass || ''}`;
        
        statElement.innerHTML = `
          <div class="item-stat-icon">${stat.icon || '📊'}</div>
          <div class="item-stat-details">
            <div class="item-stat-name">${stat.name}</div>
            <div class="item-stat-value">${stat.value || ''}</div>
          </div>
        `;
        
        statsElement.appendChild(statElement);
      });
    } else {
      // Fallback for items with no stats
      statsElement.innerHTML = `
        <div class="no-stats-message">
          <p>This item has no stat bonuses.</p>
        </div>
      `;
    }
  }
  
  /**
   * Extracts stats from item data
   * @param {Object} item - The item data
   * @returns {Array} Array of stat objects
   */
  _extractItemStats(item) {
    const statsArray = [];
    
    // First try to extract from description HTML
    if (item.description) {
      // Check for stats in mainText format
      const statsMatch = item.description.match(/<mainText><stats>(.*?)<\/stats>/s);
      if (statsMatch && statsMatch[1]) {
        const statsHtml = statsMatch[1];
        
        // Look for Ornn bonus stats - these use <ornnBonus> tags
        const ornnBonusRegex = /<ornnBonus>([^<]+)<\/ornnBonus>([^<]+)/g;
        let ornnMatch;
        
        while ((ornnMatch = ornnBonusRegex.exec(statsHtml)) !== null) {
          const value = ornnMatch[1].trim();
          const name = ornnMatch[2].trim();
          
          // Determine icon and CSS class based on stat name
          const statInfo = this._getStatInfo(name);
          
          statsArray.push({
            value,
            name,
            icon: statInfo.icon,
            cssClass: statInfo.cssClass
          });
        }
        
        // Also look for regular stats with <attention> tags
        const statRegex = /<attention>([^<]+)<\/attention>([^<]+)/g;
        let match;
        
        while ((match = statRegex.exec(statsHtml)) !== null) {
          const value = match[1].trim();
          const name = match[2].trim();
          
          // Determine icon and CSS class based on stat name
          const statInfo = this._getStatInfo(name);
          
          statsArray.push({
            value,
            name,
            icon: statInfo.icon,
            cssClass: statInfo.cssClass
          });
        }
      }
    }
    
    // If no stats found in HTML, try regex patterns
    if (statsArray.length === 0 && item.description) {
      const statPatterns = [
        { pattern: /\+?(\d+)\s*(?:Attack Damage|AD)/i, name: 'Attack Damage', icon: '⚔️', cssClass: 'stat-ad' },
        { pattern: /\+?(\d+)\s*(?:Ability Power|AP)/i, name: 'Ability Power', icon: '✨', cssClass: 'stat-ap' },
        { pattern: /\+?(\d+)%\s*(?:Attack Speed|AS)/i, name: 'Attack Speed', icon: '⚡', cssClass: 'stat-as', percent: true },
        { pattern: /\+?(\d+)\s*(?:Armor)/i, name: 'Armor', icon: '🛡️', cssClass: 'stat-armor' },
        { pattern: /\+?(\d+)\s*(?:Magic Resist|MR)/i, name: 'Magic Resist', icon: '🔮', cssClass: 'stat-mr' },
        { pattern: /\+?(\d+)\s*(?:Health|HP)/i, name: 'Health', icon: '❤️', cssClass: 'stat-health' },
        { pattern: /\+?(\d+)\s*(?:Mana|MP)/i, name: 'Mana', icon: '🔹', cssClass: 'stat-mana' },
        { pattern: /\+?(\d+)%\s*(?:Life Steal)/i, name: 'Life Steal', icon: '🧛', cssClass: 'stat-lifesteal', percent: true },
        { pattern: /\+?(\d+)\s*(?:Movement Speed|MS)/i, name: 'Movement Speed', icon: '👟', cssClass: 'stat-ms' },
        { pattern: /\+?(\d+)%\s*(?:Critical Strike|Crit)/i, name: 'Critical Strike', icon: '🎯', cssClass: 'stat-crit', percent: true },
        { pattern: /\+?(\d+)\s*(?:Health Regen|HP5)/i, name: 'Health Regen', icon: '💓', cssClass: 'stat-hp-regen' },
        { pattern: /\+?(\d+)\s*(?:Mana Regen|MP5)/i, name: 'Mana Regen', icon: '💧', cssClass: 'stat-mp-regen' },
        { pattern: /\+?(\d+)\s*(?:Ability Haste|AH)/i, name: 'Ability Haste', icon: '⏱', cssClass: 'stat-haste' },
        { pattern: /\+?(\d+)%\s*(?:Omnivamp)/i, name: 'Omnivamp', icon: '🔄', cssClass: 'stat-omnivamp', percent: true }
      ];
      
      statPatterns.forEach(stat => {
        const match = item.description.match(stat.pattern);
        if (match && match[1]) {
          statsArray.push({
            value: match[1] + (stat.percent ? '%' : ''),
            name: stat.name,
            icon: stat.icon,
            cssClass: stat.cssClass
          });
        }
      });
    }
    
    // If still no stats, check if item has stats object
    if (statsArray.length === 0 && item.stats && Object.keys(item.stats).length > 0) {
      // Map stat keys to readable names
      const statMapping = {
        'FlatPhysicalDamageMod': { name: 'Attack Damage', icon: '⚔️', cssClass: 'stat-ad' },
        'FlatMagicDamageMod': { name: 'Ability Power', icon: '✨', cssClass: 'stat-ap' },
        'PercentAttackSpeedMod': { name: 'Attack Speed', icon: '⚡', cssClass: 'stat-as', percent: true },
        'FlatArmorMod': { name: 'Armor', icon: '🛡️', cssClass: 'stat-armor' },
        'FlatSpellBlockMod': { name: 'Magic Resist', icon: '🔮', cssClass: 'stat-mr' },
        'FlatHPPoolMod': { name: 'Health', icon: '❤️', cssClass: 'stat-health' },
        'FlatMPPoolMod': { name: 'Mana', icon: '🔹', cssClass: 'stat-mana' },
        'FlatMovementSpeedMod': { name: 'Movement Speed', icon: '👟', cssClass: 'stat-ms' },
        'FlatCritChanceMod': { name: 'Critical Chance', icon: '🎯', cssClass: 'stat-crit' },
        'FlatHPRegenMod': { name: 'Health Regen', icon: '💓', cssClass: 'stat-hp-regen' },
        'FlatMPRegenMod': { name: 'Mana Regen', icon: '💧', cssClass: 'stat-mp-regen' },
        'PercentLifeStealMod': { name: 'Life Steal', icon: '🧛', cssClass: 'stat-lifesteal', percent: true },
        'PercentSpellVampMod': { name: 'Spell Vamp', icon: '🧙', cssClass: 'stat-spellvamp', percent: true }
      };
      
      Object.entries(item.stats).forEach(([key, value]) => {
        if (value && value !== 0) {
          const statInfo = statMapping[key] || { name: key, icon: '📊', cssClass: '' };
          let formattedValue = value;
          
          if (statInfo.percent) {
            formattedValue = `${(value * 100).toFixed(0)}%`;
          }
          
          statsArray.push({
            value: formattedValue,
            name: statInfo.name,
            icon: statInfo.icon,
            cssClass: statInfo.cssClass
          });
        }
      });
    }
    
    return statsArray;
  }
  
  /**
   * Gets icon and CSS class for a stat based on its name
   * @param {string} statName - The stat name
   * @returns {Object} The stat info with icon and CSS class
   */
  _getStatInfo(statName) {
    const statName_lower = statName.toLowerCase();
    
    if (statName_lower.includes('attack damage') || statName_lower.includes('ad')) {
      return { icon: '⚔️', cssClass: 'stat-ad' };
    } else if (statName_lower.includes('ability power') || statName_lower.includes('ap')) {
      return { icon: '✨', cssClass: 'stat-ap' };
    } else if (statName_lower.includes('attack speed')) {
      return { icon: '⚡', cssClass: 'stat-as' };
    } else if (statName_lower.includes('armor')) {
      return { icon: '🛡️', cssClass: 'stat-armor' };
    } else if (statName_lower.includes('magic resist')) {
      return { icon: '🔮', cssClass: 'stat-mr' };
    } else if (statName_lower.includes('health') && !statName_lower.includes('regen')) {
      return { icon: '❤️', cssClass: 'stat-health' };
    } else if (statName_lower.includes('mana') && !statName_lower.includes('regen')) {
      return { icon: '🔹', cssClass: 'stat-mana' };
    } else if (statName_lower.includes('movement speed')) {
      return { icon: '👟', cssClass: 'stat-ms' };
    } else if (statName_lower.includes('crit')) {
      return { icon: '🎯', cssClass: 'stat-crit' };
    } else if (statName_lower.includes('health regen')) {
      return { icon: '💓', cssClass: 'stat-hp-regen' };
    } else if (statName_lower.includes('mana regen')) {
      return { icon: '💧', cssClass: 'stat-mp-regen' };
    } else if (statName_lower.includes('haste')) {
      return { icon: '⏱', cssClass: 'stat-haste' };
    } else if (statName_lower.includes('omnivamp')) {
      return { icon: '🔄', cssClass: 'stat-omnivamp' };
    } else if (statName_lower.includes('life steal')) {
      return { icon: '🧛', cssClass: 'stat-lifesteal' };
    }
    
    // Default
    return { icon: '📊', cssClass: '' };
  }
  
  /**
   * Renders the item description section
   * @param {Object} item - The item data
   */
  _renderItemDescription(item) {
    const descriptionElement = document.querySelector('.item-description');
    const abilitiesContainer = document.querySelector('.item-abilities-container');
    
    // Clear existing content
    descriptionElement.innerHTML = '';
    abilitiesContainer.innerHTML = '';
    
    // Extract main description text
    let mainText = '';
    
    if (item.description) {
      if (item.description.includes('<mainText>')) {
        // Modern format
        mainText = item.description
          .replace(/<mainText><stats>.*?<\/stats>(<br><br>)?/s, '')
          .replace(/<active>ACTIVE<\/active>.*?(?=<\/mainText>)/s, '')
          .replace(/<passive>PASSIVE<\/passive>.*?(?=<\/mainText>)/s, '')
          .replace(/<\/?mainText>/g, '')
          .replace(/<br><br><br>/g, '<br><br>');
      } else {
        // Legacy format
        mainText = item.description
          .replace(/UNIQUE Passive(?: - [^:]+)?:.*?(?=(UNIQUE|$))/s, '')
          .replace(/UNIQUE Active(?: - [^:]+)?:.*?(?=(UNIQUE|$))/s, '');
      }
      
      // If description is empty after extraction, use plaintext
      if (mainText.trim() === '' || mainText.trim() === '<br><br>') {
        mainText = item.plaintext || 'No description available.';
      }
    } else {
      mainText = item.plaintext || 'No description available.';
    }
    
    // Format special tags
    mainText = this._formatSpecialTags(mainText);
    
    // Set description
    descriptionElement.innerHTML = `<div class="main-description">${mainText}</div>`;
    
    // Extract and render abilities
    this._renderItemAbilities(item, abilitiesContainer);
  }
  
  /**
   * Formats special tags in text
   * @param {string} text - The text to format
   * @returns {string} The formatted text
   */
  _formatSpecialTags(text) {
    if (!text) return '';
    
    return text
      .replace(/<physicalDamage>(.*?)<\/physicalDamage>/g, '<span class="physical-damage">$1</span>')
      .replace(/<magicDamage>(.*?)<\/magicDamage>/g, '<span class="magic-damage">$1</span>')
      .replace(/<trueDamage>(.*?)<\/trueDamage>/g, '<span class="true-damage">$1</span>')
      .replace(/<status>(.*?)<\/status>/g, '<span class="status-effect">$1</span>')
      .replace(/<attention>(.*?)<\/attention>/g, '<span class="spell-active">$1</span>')
      .replace(/<healing>(.*?)<\/healing>/g, '<span class="healing">$1</span>')
      .replace(/<champion>(.*?)<\/champion>/g, '<span class="demacian-gold">$1</span>')
      .replace(/<keywordMajor>(.*?)<\/keywordMajor>/g, '<span class="demacian-gold">$1</span>')
      .replace(/<keyword>(.*?)<\/keyword>/g, '<span class="status-effect">$1</span>');
  }
  
  /**
   * Renders item active and passive abilities
   * @param {Object} item - The item data
   * @param {HTMLElement} container - The container element
   */
  _renderItemAbilities(item, container) {
    if (!item.description) return;
    
    // Check for active and passive abilities
    let activeAbility = null;
    let passiveAbility = null;
    
    // Modern format
    if (item.description.includes('<mainText>')) {
      // Extract active ability
      const activeMatch = item.description.match(/<active>ACTIVE<\/active><br><active>([^<]+)<\/active><br>([^<]+)/);
      if (activeMatch) {
        activeAbility = {
          name: activeMatch[1].trim(),
          description: activeMatch[2].trim()
        };
      }
      
      // Extract passive ability
      const passiveMatch = item.description.match(/<passive>PASSIVE<\/passive><br>([^<]+)/);
      if (passiveMatch) {
        passiveAbility = {
          name: 'Passive',
          description: passiveMatch[1].trim()
        };
      }
    } else {
      // Legacy format
      const passiveMatch = item.description.match(/UNIQUE Passive(?: - ([^:]+))?:(.*?)(?=(UNIQUE|$))/s);
      if (passiveMatch) {
        passiveAbility = {
          name: passiveMatch[1] ? passiveMatch[1].trim() : 'Unique Passive',
          description: passiveMatch[2].trim()
        };
      }
      
      const activeMatch = item.description.match(/UNIQUE Active(?: - ([^:]+))?:(.*?)(?=(UNIQUE|$))/s);
      if (activeMatch) {
        activeAbility = {
          name: activeMatch[1] ? activeMatch[1].trim() : 'Unique Active',
          description: activeMatch[2].trim()
        };
      }
    }
    
    // Render passive ability
    if (passiveAbility) {
      const passiveDiv = document.createElement('div');
      passiveDiv.className = 'item-passive';
      passiveDiv.innerHTML = `
        <div class="ability-header passive-header">
          <span class="ability-icon passive-icon">P</span>
          <span class="ability-name passive-name">${passiveAbility.name}</span>
        </div>
        <div class="ability-description passive-description">
          ${this._formatSpecialTags(passiveAbility.description)}
        </div>
      `;
      
      container.appendChild(passiveDiv);
    }
    
    // Render active ability
    if (activeAbility) {
      const activeDiv = document.createElement('div');
      activeDiv.className = 'item-active';
      activeDiv.innerHTML = `
        <div class="ability-header active-header">
          <span class="ability-icon active-icon">A</span>
          <span class="ability-name active-name">${activeAbility.name}</span>
        </div>
        <div class="ability-description active-description">
          ${this._formatSpecialTags(activeAbility.description)}
        </div>
      `;
      
      container.appendChild(activeDiv);
    }
  }
  
  /**
   * Renders the build path tab
   * @param {Object} item - The item data
   */
  _renderBuildPath(item) {
    const treeElement = document.querySelector('.recipe-tree');
    const efficiencyElement = document.querySelector('.recipe-efficiency');
    const costFlowElement = document.querySelector('.recipe-cost-flow');
    const componentsElement = document.querySelector('.recipe-components');
    
    // Clear existing content
    treeElement.innerHTML = '';
    efficiencyElement.innerHTML = '';
    costFlowElement.innerHTML = '';
    componentsElement.innerHTML = '';
    
    // Show loading indicator while we check build paths
    treeElement.innerHTML = '<div class="loading-message">Checking build path information...</div>';
    
    // Process build path asynchronously
    this._processBuildPath(item, treeElement, efficiencyElement, costFlowElement, componentsElement);
  }
  
  /**
   * Processes the build path data asynchronously with fallbacks to Dragon API
   * @param {Object} item - The item data
   * @param {HTMLElement} treeElement - The tree container element
   * @param {HTMLElement} efficiencyElement - The efficiency container element
   * @param {HTMLElement} costFlowElement - The cost flow container element
   * @param {HTMLElement} componentsElement - The components container element
   */
  async _processBuildPath(item, treeElement, efficiencyElement, costFlowElement, componentsElement) {
    try {
      // First try to use the item's "from" property
      let components = [];
      
      if (item.from && item.from.length > 0) {
        components = await this._getComponentItems(item.from);
      }
      
      // If no components found via "from", try to get data from Dragon API
      if (components.length === 0) {
        console.log("No build path found in local data, trying Dragon API...");
        
        try {
          const dragonResponse = await fetch(`https://ddragon.leagueoflegends.com/cdn/13.21.1/data/en_US/item.json`);
          
          if (dragonResponse.ok) {
            const dragonData = await dragonResponse.json();
            const dragonItem = dragonData.data[item.id];
            
            if (dragonItem && dragonItem.from && dragonItem.from.length > 0) {
              console.log(`Found build path in Dragon API for ${item.name}: ${dragonItem.from.join(', ')}`);
              
              // Get components using the "from" array from Dragon API
              components = await this._getComponentItems(dragonItem.from);
              
              // Update the item with the Dragon API data
              item.from = dragonItem.from;
              item.from.found_in_backend = false; // Mark as not from our backend
            }
          }
        } catch (dragonError) {
          console.warn('Error fetching from Dragon API:', dragonError);
        }
      }
      
      // If we have components, render the build path
      if (components.length > 0) {
        // Get recursive component data
        const recipeData = await this._getRecursiveRecipeData(item);
        
        // Create enhanced recipe tree visualization
        this._renderRecipeTree(item, components, recipeData, treeElement);
        
        // Create gold efficiency visualization
        this._renderGoldEfficiency(item, components, efficiencyElement);
        
        // Create cost flow visualization
        this._renderCostFlow(item, components, costFlowElement);
        
        // Create detailed cost calculation
        this._renderCostCalculation(item, components, componentsElement);
        
        // Set up zoom controls
        this._setupRecipeControls(treeElement);
        
        // Add gold particle animations
        this._addGoldParticleEffects(costFlowElement);
      } else {
        // Still no components found, show message
        treeElement.innerHTML = '<p class="no-data-message">This is a basic item with no recipe.</p>';
      }
    } catch (error) {
      console.error('Error processing build path:', error);
      treeElement.innerHTML = `<p class="error-message">Error loading build path: ${error.message}</p>`;
    }
  }
  
  /**
   * Gets recursive recipe data for an item
   * @param {Object} item - The item data
   * @returns {Promise<Object>} Promise resolving to recipe data
   */
  async _getRecursiveRecipeData(item) {
    try {
      // First check if we already have recipe data in the item object
      if (item.buildsFrom && Array.isArray(item.buildsFrom) && item.buildsFrom.length > 0) {
        return item;
      }
      
      // If not, try to fetch from API
      console.log(`Fetching recipe data for ${item.name} (${item.id})`);
      const recipeResponse = await fetch(`${this.API_BASE_URL}/items/${item.id}/recipe?depth=3`);
      
      if (recipeResponse.ok) {
        const recipeData = await recipeResponse.json();
        
        // Check if recipeData has valid buildsFrom data
        if (recipeData.buildsFrom && recipeData.buildsFrom.length > 0) {
          return recipeData;
        }
      }
      
      // If backend API doesn't have the data, fallback to Dragon API
      // This is important for mythic items which may not have build path in our DB
      try {
        console.log("Backend API missing build path data, trying Dragon API...");
        const dragonResponse = await fetch(`https://ddragon.leagueoflegends.com/cdn/13.21.1/data/en_US/item.json`);
        
        if (dragonResponse.ok) {
          const dragonData = await dragonResponse.json();
          const dragonItem = dragonData.data[item.id];
          
          if (dragonItem && dragonItem.from && dragonItem.from.length > 0) {
            console.log(`Found build path in Dragon API for ${item.name}: ${dragonItem.from.join(', ')}`);
            
            // Get components from Dragon API "from" array
            const componentItems = await this._getComponentItems(dragonItem.from);
            
            return {
              ...item,
              from: dragonItem.from,
              buildsFrom: componentItems
            };
          }
        }
      } catch (dragonError) {
        console.warn('Error fetching from Dragon API:', dragonError);
      }
      
      // If all attempts fail, create a simpler recipe from the 'from' property
      return {
        ...item,
        buildsFrom: await this._getComponentItems(item.from || [])
      };
    } catch (error) {
      console.warn('Error fetching recursive recipe data:', error);
      // Fall back to simple component list
      return {
        ...item,
        buildsFrom: await this._getComponentItems(item.from || [])
      };
    }
  }
  
  /**
   * Renders the enhanced recipe tree visualization
   * @param {Object} item - The item data
   * @param {Array} components - Array of component items
   * @param {Object} recipeData - Full recipe data with nested components
   * @param {HTMLElement} container - The container element
   */
  _renderRecipeTree(item, components, recipeData, container) {
    // Create SVG element for connections
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.classList.add('tree-connector');
    svg.style.width = '100%';
    svg.style.height = '100%';
    svg.style.position = 'absolute';
    svg.style.top = '0';
    svg.style.left = '0';
    svg.style.zIndex = '1';
    svg.style.pointerEvents = 'none';
    container.appendChild(svg);
    
    // Create root node (final item)
    const rootNode = this._createTreeNode(item, true);
    container.appendChild(rootNode);
    
    // Create children container
    const childrenContainer = document.createElement('div');
    childrenContainer.className = 'tree-children';
    rootNode.appendChild(childrenContainer);
    
    // Render component nodes
    components.forEach(comp => {
      const childNode = this._createTreeNode(comp);
      childrenContainer.appendChild(childNode);
      
      // Add sub-components recursively if available in recipeData
      if (recipeData.buildsFrom) {
        const compData = recipeData.buildsFrom.find(c => c.id === comp.id);
        if (compData && compData.buildsFrom && compData.buildsFrom.length > 0) {
          const subChildrenContainer = document.createElement('div');
          subChildrenContainer.className = 'tree-children';
          childNode.appendChild(subChildrenContainer);
          
          compData.buildsFrom.forEach(subComp => {
            const subChildNode = this._createTreeNode(subComp);
            subChildrenContainer.appendChild(subChildNode);
            
            // Draw connector
            setTimeout(() => {
              this._drawConnector(svg, subChildNode, childNode);
            }, 100);
          });
        }
      }
      
      // Draw connector after nodes are rendered
      setTimeout(() => {
        this._drawConnector(svg, childNode, rootNode);
      }, 100);
    });
    
    // Add entrance animation
    setTimeout(() => {
      rootNode.style.opacity = '1';
      rootNode.style.transform = 'translateY(0)';
      
      const childNodes = container.querySelectorAll('.tree-node:not(.final-item)');
      childNodes.forEach((node, index) => {
        setTimeout(() => {
          node.style.opacity = '1';
          node.style.transform = 'translateY(0)';
        }, 100 + index * 50);
      });
    }, 100);
  }
  
  /**
   * Creates a tree node element
   * @param {Object} item - The item data
   * @param {boolean} isFinalItem - Whether this is the final item
   * @returns {HTMLElement} The tree node element
   */
  _createTreeNode(item, isFinalItem = false) {
    const nodeElement = document.createElement('div');
    nodeElement.className = 'tree-node';
    if (isFinalItem) {
      nodeElement.classList.add('final-item');
    }
    
    // Set initial state for animation
    nodeElement.style.opacity = '0';
    nodeElement.style.transform = 'translateY(20px)';
    
    // Create node content
    let imageUrl;
    
    // Use our backend API for all items for consistency
    if (item.image) {
      // Use our backend API which should have all synced images
      imageUrl = `${this.API_BASE_URL}/assets/item/image/${item.id}`;
    } else {
      // Fallback to placeholder
      imageUrl = 'images/item-placeholder.png';
    }
    
    const nodeContent = document.createElement('div');
    nodeContent.className = 'tree-node-content';
    nodeContent.innerHTML = `
      <div class="tree-node-icon">
        <img src="${imageUrl}" alt="${item.name}" class="tree-node-img">
      </div>
      <div class="tree-node-name">${item.name}</div>
      ${item.gold && item.gold.total ? `<div class="tree-node-cost">${item.gold.total}</div>` : ''}
    `;
    
    nodeElement.appendChild(nodeContent);
    
    // Add data-id attribute for item identification
    nodeElement.setAttribute('data-id', item.id);
    
    // Add image error handler
    const imgElement = nodeContent.querySelector('img');
    imgElement.addEventListener('error', function() {
      if (window.LOLUtils && window.LOLUtils.handleImageError) {
        window.LOLUtils.handleImageError(this);
      } else {
        // Try Dragon API as fallback if backend image fails
        if (this.src.includes('/assets/item/image/')) {
          this.src = `https://ddragon.leagueoflegends.com/cdn/13.21.1/img/item/${item.id}.png`;
        } else {
          // Final fallback to placeholder
          this.src = 'images/item-placeholder.png';
        }
      }
    });
    
    // Add click handler for item navigation
    nodeContent.addEventListener('click', () => {
      document.dispatchEvent(new CustomEvent('itemSelected', {
        detail: { itemId: item.id }
      }));
    });
    
    return nodeElement;
  }
  
  /**
   * Draws an SVG connector between two nodes
   * @param {SVGElement} svg - The SVG element to draw on
   * @param {HTMLElement} fromNode - The source node
   * @param {HTMLElement} toNode - The target node
   */
  _drawConnector(svg, fromNode, toNode) {
    // Get positions
    const fromRect = fromNode.querySelector('.tree-node-content').getBoundingClientRect();
    const toRect = toNode.querySelector('.tree-node-content').getBoundingClientRect();
    const svgRect = svg.getBoundingClientRect();
    
    // Calculate connector points
    const fromX = (fromRect.left + fromRect.right) / 2 - svgRect.left;
    const fromY = fromRect.top - svgRect.top;
    const toX = (toRect.left + toRect.right) / 2 - svgRect.left;
    const toY = toRect.bottom - svgRect.top;
    
    // Create path element
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.classList.add('tree-connector-line');
    
    // Set path data for curved line
    const midY = (fromY + toY) / 2;
    path.setAttribute('d', `M ${fromX},${fromY} C ${fromX},${midY} ${toX},${midY} ${toX},${toY}`);
    
    // Add arrow marker
    const arrow = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
    arrow.classList.add('tree-connector-arrow');
    
    // Position arrow at the middle of the path
    const arrowX = (fromX + toX) / 2;
    const arrowY = midY;
    arrow.setAttribute('points', `${arrowX-5},${arrowY-3} ${arrowX+5},${arrowY} ${arrowX-5},${arrowY+3}`);
    
    // Add elements to SVG
    svg.appendChild(path);
    svg.appendChild(arrow);
  }
  
  /**
   * Sets up the recipe controls for zooming and expanding
   * @param {HTMLElement} treeElement - The tree container element
   */
  _setupRecipeControls(treeElement) {
    const zoomInBtn = document.querySelector('.zoom-in-btn');
    const zoomOutBtn = document.querySelector('.zoom-out-btn');
    const expandAllBtn = document.querySelector('.expand-all-btn');
    
    let currentScale = 1;
    
    // Zoom in button
    if (zoomInBtn) {
      zoomInBtn.addEventListener('click', () => {
        currentScale = Math.min(currentScale + 0.1, 1.5);
        treeElement.style.transform = `scale(${currentScale})`;
      });
    }
    
    // Zoom out button
    if (zoomOutBtn) {
      zoomOutBtn.addEventListener('click', () => {
        currentScale = Math.max(currentScale - 0.1, 0.5);
        treeElement.style.transform = `scale(${currentScale})`;
      });
    }
    
    // Expand all button
    if (expandAllBtn) {
      expandAllBtn.addEventListener('click', () => {
        const childContainers = treeElement.querySelectorAll('.tree-children');
        childContainers.forEach(container => {
          container.style.display = container.style.display === 'none' ? 'flex' : 'none';
        });
      });
    }
  }
  
  /**
   * Renders the gold efficiency visualization
   * @param {Object} item - The item data
   * @param {Array} components - Array of component items
   * @param {HTMLElement} container - The container element
   */
  _renderGoldEfficiency(item, components, container) {
    // Calculate basic efficiency (ratio of total stats value to item cost)
    // This is a simplified approximation
    const efficiency = this._calculateEfficiency(item, components);
    
    container.innerHTML = `
      <h3>Gold Efficiency</h3>
      <div class="efficiency-meter">
        <div class="efficiency-fill" style="width: ${Math.min(efficiency * 100, 100)}%"></div>
        <div class="efficiency-marker" style="left: 50%">100%</div>
      </div>
      <div class="efficiency-value">${Math.round(efficiency * 100)}% Efficient</div>
      <div class="efficiency-explanation">
        Gold efficiency compares the value of the item's stats to its total cost.
        ${efficiency >= 1 ? 'This item is cost-effective!' : 'This item\'s value comes from its unique effects.'}
      </div>
    `;
  }
  
  /**
   * Calculates the gold efficiency of an item
   * @param {Object} item - The item data
   * @param {Array} components - Array of component items
   * @returns {number} The efficiency ratio
   */
  _calculateEfficiency(item, components) {
    // This is a simplified calculation that estimates efficiency
    // A more accurate version would need detailed stat gold values
    
    // Base value approximation: using component cost as base value
    const componentsCost = components.reduce((total, comp) => {
      return total + (comp.gold && comp.gold.total ? comp.gold.total : 0);
    }, 0);
    
    const totalCost = item.gold && item.gold.total ? item.gold.total : 0;
    
    if (totalCost === 0) return 1; // Avoid division by zero
    
    // Calculate efficiency as ratio of component cost to total cost
    // This assumes components are 100% efficient and any additional cost
    // goes toward unique effects or additional stats
    const baseEfficiency = componentsCost / totalCost;
    
    // Add bonus for mythic and legendary items (they have unique effects)
    const tier = this._getItemTier(item);
    let tierBonus = 0;
    
    if (tier === 'mythic') {
      tierBonus = 0.3; // 30% bonus for mythic effects
    } else if (tier === 'legendary') {
      tierBonus = 0.15; // 15% bonus for legendary effects
    } else if (tier === 'epic') {
      tierBonus = 0.05; // 5% bonus for epic items
    }
    
    return Math.min(baseEfficiency + tierBonus, 1.5); // Cap at 150% efficiency
  }
  
  /**
   * Renders the cost flow visualization
   * @param {Object} item - The item data
   * @param {Array} components - Array of component items
   * @param {HTMLElement} container - The container element
   */
  _renderCostFlow(item, components, container) {
    const componentsCost = components.reduce((total, comp) => {
      return total + (comp.gold && comp.gold.total ? comp.gold.total : 0);
    }, 0);
    
    const totalCost = item.gold && item.gold.total ? item.gold.total : 0;
    const combineCost = totalCost - componentsCost;
    
    // Skip if no costs available
    if (totalCost <= 0) {
      container.innerHTML = '<p class="no-data-message">Cost information not available.</p>';
      return;
    }
    
    // Calculate percentages for visualization
    const componentsPercent = (componentsCost / totalCost) * 100;
    const combinePercent = (combineCost / totalCost) * 100;
    
    container.innerHTML = `
      <h3>Cost Breakdown</h3>
      <div class="cost-flow-visualization">
        <div class="cost-flow-segment" style="left: 0; width: ${componentsPercent}%;">
          <div class="cost-flow-bar cost-flow-components" style="height: 100%"></div>
          <div class="cost-flow-label">Components</div>
          <div class="cost-flow-value">${componentsCost} G</div>
        </div>
        <div class="cost-flow-segment" style="left: ${componentsPercent}%; width: ${combinePercent}%;">
          <div class="cost-flow-bar cost-flow-combine" style="height: 100%"></div>
          <div class="cost-flow-label">Combine Cost</div>
          <div class="cost-flow-value">${combineCost} G</div>
        </div>
      </div>
    `;
  }
  
  /**
   * Adds gold particle effects to the cost flow visualization
   * @param {HTMLElement} container - The container element
   */
  _addGoldParticleEffects(container) {
    // Skip if container not found
    if (!container) return;
    
    // Create gold particles
    const particleCount = 20;
    const particles = [];
    
    // Create particle elements
    for (let i = 0; i < particleCount; i++) {
      const particle = document.createElement('div');
      particle.className = 'gold-particle';
      container.appendChild(particle);
      
      // Set random initial position
      const x = Math.random() * container.offsetWidth;
      const y = Math.random() * container.offsetHeight;
      particle.style.left = `${x}px`;
      particle.style.top = `${y}px`;
      
      // Add to array for animation
      particles.push({
        element: particle,
        x,
        y,
        speedX: Math.random() * 2 - 1,
        speedY: Math.random() * 2 - 1,
        size: 3 + Math.random() * 3
      });
    }
    
    // Animate particles
    let animationId;
    
    const animateParticles = () => {
      particles.forEach(particle => {
        // Update position
        particle.x += particle.speedX;
        particle.y += particle.speedY;
        
        // Bounce off edges
        if (particle.x <= 0 || particle.x >= container.offsetWidth) {
          particle.speedX *= -1;
        }
        
        if (particle.y <= 0 || particle.y >= container.offsetHeight) {
          particle.speedY *= -1;
        }
        
        // Update element position
        particle.element.style.left = `${particle.x}px`;
        particle.element.style.top = `${particle.y}px`;
        particle.element.style.width = `${particle.size}px`;
        particle.element.style.height = `${particle.size}px`;
      });
      
      animationId = requestAnimationFrame(animateParticles);
    };
    
    // Start animation
    animateParticles();
    
    // Clean up when tab changes or component unmounts
    const tabButtons = document.querySelectorAll('.item-tab-button');
    tabButtons.forEach(button => {
      button.addEventListener('click', () => {
        if (button.getAttribute('data-tab') !== 'build-path') {
          cancelAnimationFrame(animationId);
          particles.forEach(particle => {
            if (particle.element.parentNode) {
              particle.element.parentNode.removeChild(particle.element);
            }
          });
        }
      });
    });
  }
  
  /**
   * Renders the detailed cost calculation
   * @param {Object} item - The item data
   * @param {Array} components - Array of component items
   * @param {HTMLElement} container - The container element
   */
  _renderCostCalculation(item, components, container) {
    const componentsCost = components.reduce((total, comp) => {
      return total + (comp.gold && comp.gold.total ? comp.gold.total : 0);
    }, 0);
    
    const totalCost = item.gold && item.gold.total ? item.gold.total : 0;
    const combineCost = totalCost - componentsCost;
    
    if (combineCost > 0) {
      container.innerHTML = `
        <div class="recipe-cost-calculation">
          <div class="cost-row"><span>Components Cost:</span> <span>${componentsCost} G</span></div>
          <div class="cost-row"><span>Combine Cost:</span> <span>${combineCost} G</span></div>
          <div class="cost-row total-cost"><span>Total Cost:</span> <span>${totalCost} G</span></div>
        </div>
      `;
    }
  }
  
  /**
   * Renders the related items tab
   * @param {Object} item - The item data
   */
  _renderRelatedItems(item) {
    const buildsIntoElement = document.querySelector('.item-builds-into');
    const relatedItemsElement = document.querySelector('.related-items-scroll');
    
    // Clear existing content
    buildsIntoElement.innerHTML = '';
    relatedItemsElement.innerHTML = '';
    
    // Get all items that this item builds into
    this._getBuildsIntoItems(item.id).then(buildsIntoItems => {
      if (buildsIntoItems.length > 0) {
        buildsIntoElement.innerHTML = '<div class="builds-into-header">This item builds into:</div>';
        
        const itemsContainer = document.createElement('div');
        itemsContainer.className = 'related-items-grid';
        
        buildsIntoItems.forEach(buildItem => {
          itemsContainer.appendChild(this._createRelatedItemCard(buildItem));
        });
        
        buildsIntoElement.appendChild(itemsContainer);
      } else {
        buildsIntoElement.innerHTML = '<p class="no-data-message">This item doesn\'t build into anything else.</p>';
      }
    });
    
    // Get related items (similar tags/stats)
    this._getRelatedItems(item).then(relatedItems => {
      if (relatedItems.length > 0) {
        const itemsContainer = document.createElement('div');
        itemsContainer.className = 'related-items-grid';
        
        relatedItems.forEach(relatedItem => {
          itemsContainer.appendChild(this._createRelatedItemCard(relatedItem));
        });
        
        relatedItemsElement.appendChild(itemsContainer);
      } else {
        relatedItemsElement.innerHTML = '<p class="no-data-message">No related items found.</p>';
      }
    });
  }
  
  /**
   * Creates a related item card
   * @param {Object} item - The item data
   * @returns {HTMLElement} The item card element
   */
  _createRelatedItemCard(item) {
    const itemCard = document.createElement('div');
    itemCard.className = 'recipe-item';
    itemCard.setAttribute('data-id', item.id);
    
    // Determine correct image URL with fallbacks
    let imageUrl;
    if (item.image) {
      // Use our backend API for all items for consistency
      imageUrl = `${this.API_BASE_URL}/assets/item/image/${item.id}`;
    } else {
      // Fallback to placeholder
      imageUrl = 'images/item-placeholder.png';
    }
      
    itemCard.innerHTML = `
      <div class="recipe-item-image">
        <img src="${imageUrl}" alt="${item.name}" class="related-item-img">
      </div>
      <div class="recipe-item-name">${item.name}</div>
      ${item.gold && item.gold.total ? `<div class="recipe-item-cost">${item.gold.total}</div>` : ''}
    `;
    
    // Add image error handler
    const imgElement = itemCard.querySelector('img');
    imgElement.addEventListener('error', function() {
      if (window.LOLUtils && window.LOLUtils.handleImageError) {
        window.LOLUtils.handleImageError(this);
      } else {
        // Try Dragon API as fallback if backend image fails
        if (this.src.includes('/assets/item/image/')) {
          this.src = `https://ddragon.leagueoflegends.com/cdn/13.21.1/img/item/${item.id}.png`;
        } else {
          // Final fallback to placeholder
          this.src = 'images/item-placeholder.png';
        }
      }
    });
    
    // Add click handler
    itemCard.addEventListener('click', () => {
      document.dispatchEvent(new CustomEvent('itemSelected', {
        detail: { itemId: item.id }
      }));
    });
    
    return itemCard;
  }
  
  /**
   * Gets component items from an array of item IDs
   * @param {Array} itemIds - Array of item IDs
   * @returns {Promise<Array>} Promise resolving to array of item objects
   */
  async _getComponentItems(itemIds) {
    if (!itemIds || !Array.isArray(itemIds) || itemIds.length === 0) {
      return [];
    }
    
    // Get all items from cache
    let allItems = [];
    
    if (window.LOLUtils && window.LOLUtils.getCachedItems) {
      allItems = await window.LOLUtils.getCachedItems() || [];
    }
    
    // Filter for component items
    const cachedComponents = allItems.filter(item => itemIds.includes(item.id));
    
    // If we found all components in cache, return them
    if (cachedComponents.length === itemIds.length) {
      return cachedComponents;
    }
    
    // Otherwise, we need to fetch missing components
    const missingIds = itemIds.filter(id => !cachedComponents.some(item => item.id === id));
    console.log(`Missing component items: ${missingIds.join(', ')}`);
    
    // Try to fetch missing components from API
    const missingComponents = await Promise.all(
      missingIds.map(async id => {
        try {
          // Try our backend API first
          const response = await fetch(`${this.API_BASE_URL}/items/${id}`);
          
          if (response.ok) {
            return await response.json();
          }
          
          // If backend fails, try triggering a component sync and retry
          console.log(`Component ${id} not found in backend, triggering component sync...`);
          
          try {
            // Call the sync endpoint to trigger component sync
            const syncResponse = await fetch(`${this.API_BASE_URL}/sync/missing-components`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json'
              },
              body: JSON.stringify({ background: true })
            });
            
            if (syncResponse.ok) {
              console.log(`Component sync triggered, waiting before retry...`);
              
              // Wait a short time for the sync to process
              await new Promise(resolve => setTimeout(resolve, 2000));
              
              // Retry fetching the component
              const retryResponse = await fetch(`${this.API_BASE_URL}/items/${id}`);
              
              if (retryResponse.ok) {
                return await retryResponse.json();
              }
            }
          } catch (syncError) {
            console.error(`Error during component sync: ${syncError}`);
          }
          
          // If all else fails, return a minimal placeholder item
          console.log(`Component ${id} still not found after sync attempt, using placeholder`);
          return {
            id: id,
            name: `Component ${id}`,
            description: `Description not available`,
            plaintext: `Basic component`,
            tier: 1,
            image: {
              full: `${id}.png`
            },
            gold: {
              base: 400,
              total: 400,
              sell: 160,
              purchasable: true
            },
            tags: ["Placeholder"],
            buildsFrom: [],
            buildsInto: []
          };
        } catch (error) {
          console.error(`Error fetching component ${id}:`, error);
          return {
            id: id,
            name: `Component ${id}`,
            description: "Unable to load component",
            image: { full: null },
            gold: { total: 0 },
            error: true
          };
        }
      })
    );
    
    return [...cachedComponents, ...missingComponents];
  }
  
  /**
   * Gets items that the specified item builds into
   * @param {string} itemId - The item ID
   * @returns {Promise<Array>} Promise resolving to array of item objects
   */
  async _getBuildsIntoItems(itemId) {
    // Get all items from cache
    let allItems = [];
    
    if (window.LOLUtils && window.LOLUtils.getCachedItems) {
      allItems = await window.LOLUtils.getCachedItems() || [];
    }
    
    // Filter for items that build from this item
    return allItems.filter(item => 
      item.from && item.from.includes(itemId)
    );
  }
  
  /**
   * Gets related items based on tags and stats
   * @param {Object} item - The item data
   * @returns {Promise<Array>} Promise resolving to array of related items
   */
  async _getRelatedItems(item) {
    // Get all items from cache
    let allItems = [];
    
    if (window.LOLUtils && window.LOLUtils.getCachedItems) {
      allItems = await window.LOLUtils.getCachedItems() || [];
    }
    
    // If item has tags, use them for finding related items
    if (item.tags && item.tags.length > 0) {
      const relatedItems = allItems.filter(otherItem => 
        otherItem.id !== item.id && // Not the same item
        otherItem.tags &&
        otherItem.tags.some(tag => item.tags.includes(tag))
      );
      
      // Sort by relevance (number of matching tags)
      return relatedItems
        .sort((a, b) => {
          const aMatches = a.tags.filter(tag => item.tags.includes(tag)).length;
          const bMatches = b.tags.filter(tag => item.tags.includes(tag)).length;
          return bMatches - aMatches;
        })
        .slice(0, 6); // Limit to 6 items
    }
    
    // If no tags, fall back to items of same tier
    const tier = this._getItemTier(item);
    return allItems
      .filter(otherItem => 
        otherItem.id !== item.id &&
        this._getItemTier(otherItem) === tier
      )
      .slice(0, 6); // Limit to 6 items
  }
  
  /**
   * Renders an error state
   * @param {string} message - The error message
   */
  _renderErrorState(message) {
    // Hide all loading states
    this._hideLoadingState();
    
    // Show error message in content area
    document.querySelector('.item-detail-content').innerHTML = `
      <div class="item-error">
        <div class="error-icon">⚠️</div>
        <div class="error-message">Failed to load item details.</div>
        <div class="error-description">${message}</div>
        <button class="back-to-items-button">Back to Items</button>
      </div>
    `;
    
    // Add click handler to back button
    document.querySelector('.back-to-items-button').addEventListener('click', () => {
      this.hideItemDetail();
    });
  }
  
  /**
   * Determines the tier of an item
   * @param {Object} item - The item data
   * @returns {string} The item tier
   */
  _getItemTier(item) {
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
}

// Create and initialize the ItemDetailManager
document.addEventListener('DOMContentLoaded', function() {
  // Initialize ItemDetailManager and make it globally available
  window.itemDetailManager = new ItemDetailManager();
  console.log('ItemDetailManager initialized and attached to window');
});