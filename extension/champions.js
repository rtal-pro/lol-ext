// Champions-related functionality for League of Legends Helper extension

// Requires utils.js to be loaded first

class ChampionsManager {
  constructor() {
    // Get references to DOM elements - Champions
    this.championsList = document.getElementById('champions-list');
    this.loadingElement = document.getElementById('loading-champions');
    this.errorElement = document.getElementById('error-champions');
    this.noResultsElement = document.getElementById('no-results-champions');
    this.championDetailElement = document.getElementById('champion-detail');
    this.backButton = document.getElementById('back-button');
    this.resetSearchChampions = document.getElementById('reset-search-champions');
    
    // Initialize state
    this.allChampions = []; // Store all champions from API
    this.currentChampion = null; // Current champion being viewed
    this.API_BASE_URL = window.LOLUtils.API_BASE_URL;
    
    // Initialize filter state
    this.currentFilter = {
      searchText: '',
      activeTags: new Set() // Using a Set to track multiple active tags
    };
    
    // Set up event handlers
    this._setupEventHandlers();
  }
  
  _setupEventHandlers() {
    // Set up back button events
    this.backButton.addEventListener('click', () => this.showChampionsList());
    
    // Set up tag filter buttons
    const tagFilters = document.querySelectorAll('.tag-filter');
    tagFilters.forEach(button => {
      button.addEventListener('click', (e) => {
        e.preventDefault(); // Prevent any default behavior
        
        const tag = button.getAttribute('data-tag');
        console.log(`Tag filter clicked: ${tag}`);
        
        // Toggle tag in the active tags set
        if (this.currentFilter.activeTags.has(tag)) {
          this.currentFilter.activeTags.delete(tag);
          console.log(`Removed tag: ${tag}`);
        } else {
          this.currentFilter.activeTags.add(tag);
          console.log(`Added tag: ${tag}`);
        }
        
        console.log(`Active tags after click: [${Array.from(this.currentFilter.activeTags).join(', ')}]`);
        
        // Update UI
        this.updateTagFilterUI();
        
        // Reapply filters and display
        this.filterAndDisplayChampions();
      });
    });
    
    // Reset search button
    if (this.resetSearchChampions) {
      this.resetSearchChampions.addEventListener('click', () => this.resetAllFilters());
    }
  }

  // Function to fetch champions data with caching
  async fetchChampions() {
    try {
      // Show loading state
      this.loadingElement.style.display = 'block';
      this.errorElement.style.display = 'none';
      this.noResultsElement.style.display = 'none';
      
      // Check if we have cached champions data
      const champions = await window.LOLUtils.getCachedChampions();
      
      if (champions) {
        // Use cached data
        console.log('Using cached champions data');
        this.allChampions = champions;
        this.loadingElement.style.display = 'none';
        this.filterAndDisplayChampions();
        return;
      }
      
      // No cache or expired cache, fetch from API
      console.log('Fetching champions from API');
      const response = await fetch(`${this.API_BASE_URL}/champions`);
      
      if (!response.ok) {
        throw new Error(`API request failed with status ${response.status}`);
      }
      
      // Now the response is directly an array of champions
      const data = await response.json();
      
      // Hide loading state
      this.loadingElement.style.display = 'none';
      
      // Store champions for filtering
      this.allChampions = data || [];
      
      // Sort champions alphabetically by name
      this.allChampions.sort((a, b) => a.name.localeCompare(b.name));
      
      // Debug: Log champion data to understand structure
      if (this.allChampions.length > 0) {
        console.log('First few champions:', this.allChampions.slice(0, 3));
        
        // Specifically look for Jax
        const jax = this.allChampions.find(champ => 
          champ.name && champ.name.toLowerCase().includes('jax')
        );
        if (jax) {
          console.log('Found Jax:', jax);
        } else {
          console.log('Jax not found in champions list');
        }
      }
      
      // Save to cache
      await window.LOLUtils.cacheChampions(this.allChampions);
      
      // Process and display champions
      this.filterAndDisplayChampions();
    } catch (error) {
      console.error('Error fetching champions:', error);
      
      // Hide loading state and show error
      this.loadingElement.style.display = 'none';
      this.errorElement.style.display = 'block';
      this.errorElement.textContent = `Error loading champions: ${error.message}`;
    }
  }
  
  // Function to filter champions
  filterChampions() {
    console.log('All champions length:', this.allChampions.length);
    console.log('Current filter:', {
      searchText: this.currentFilter.searchText,
      activeTags: Array.from(this.currentFilter.activeTags)
    });
    
    // If no filters are active, return all champions
    if (this.currentFilter.searchText === '' && this.currentFilter.activeTags.size === 0) {
      return this.allChampions;
    }
    
    // Apply filters
    const filtered = this.allChampions.filter(champion => {
      if (!champion) {
        console.log('Warning: Undefined champion in filter');
        return false;
      }
      
      // Search text filter - making this more robust
      let matchesSearch = true;
      
      if (this.currentFilter.searchText !== '') {
        const searchText = this.currentFilter.searchText.toLowerCase();
        const championName = (champion.name || '').toLowerCase();
        const championId = (champion.id || '').toLowerCase();
        const championTitle = (champion.title || '').toLowerCase();
        
        matchesSearch = 
          championName.includes(searchText) || 
          championId.includes(searchText) || 
          championTitle.includes(searchText);
          
        if (championName.includes('jax') || championId.includes('jax')) {
          console.log(`Special debug - Jax found: ${champion.name}, matches search: ${matchesSearch}, search text: "${searchText}"`);
        }
      }
      
      // Tag filter - if no tags are selected, all champions match
      let matchesTags = true;
      
      if (this.currentFilter.activeTags.size > 0) {
        // Make sure champion.tags exists and is an array
        const championTags = Array.isArray(champion.tags) ? champion.tags : [];
        
        // If tags are selected, a champion must have ALL of the selected tags (AND logic)
        matchesTags = Array.from(this.currentFilter.activeTags).every(tag => {
          const matches = championTags.includes(tag);
          
          // Special debug for Jax
          if (champion.name && champion.name.includes('Jax') && this.currentFilter.activeTags.size > 0) {
            console.log(`Jax tag check: ${tag} in [${championTags.join(', ')}] = ${matches}`);
          }
          
          return matches;
        });
      }
      
      // Both filters must match
      return matchesSearch && matchesTags;
    });
    
    console.log(`Filtered champions: ${filtered.length} out of ${this.allChampions.length}`);
    return filtered;
  }
  
  // Function to display champions in the UI
  displayChampions(champions) {
    console.log(`Displaying ${champions ? champions.length : 0} champions`);
    
    // Clear previous content
    this.championsList.innerHTML = '';
    
    // Check if we have champions to display
    if (!champions || champions.length === 0) {
      console.log('No champions to display, showing no results message');
      this.noResultsElement.style.display = 'block';
      
      // Debug current filter state
      console.log('Current filter state:', {
        searchText: this.currentFilter.searchText,
        activeTags: Array.from(this.currentFilter.activeTags)
      });
      
      return;
    }
    
    // Hide no results message if we have champions
    this.noResultsElement.style.display = 'none';
    
    // Create champion cards
    champions.forEach(champion => {
      const championCard = document.createElement('div');
      championCard.className = 'champion-card';
      championCard.setAttribute('data-id', champion.id);
      
      // Create an image element
      const imageUrl = champion.image && champion.image.full 
        ? `${this.API_BASE_URL}/assets/champion/image/${champion.id}`
        : 'images/champion-placeholder.png';
      
      // Format tags as badges with role-specific colors
      const tagsBadges = champion.tags.map(tag => 
        `<span class="champion-tag tag-${tag.toLowerCase()}">${tag}</span>`
      ).join('');
      
      // Set the card HTML
      championCard.innerHTML = `
        <div class="champion-image">
          <img src="${imageUrl}" alt="${champion.name}" class="champion-img">
        </div>
        <div class="champion-info">
          <h3 class="champion-name">${champion.name}</h3>
          <p class="champion-title">${champion.title || ''}</p>
          <div class="champion-tags">${tagsBadges}</div>
        </div>
      `;
      
      // Add error handler to the image
      const imgElement = championCard.querySelector('.champion-img');
      imgElement.addEventListener('error', function() {
        window.LOLUtils.handleImageError(this);
      });
      
      // Add click event to open champion detail view
      championCard.addEventListener('click', () => {
        console.log(`Champion clicked: ${champion.name}`);
        this.showChampionDetail(champion.id);
      });
      
      // Add card to list
      this.championsList.appendChild(championCard);
    });
    
    // Add simple count info
    const countInfo = document.createElement('div');
    countInfo.className = 'pagination-info';
    countInfo.textContent = `Showing ${champions.length} of ${this.allChampions.length} champions`;
    
    // If filters are active, add explanation of filter logic
    if (this.currentFilter.activeTags.size > 1) {
      const selectedTags = Array.from(this.currentFilter.activeTags).join(' AND ');
      countInfo.textContent += ` (filtered by: ${selectedTags})`;
    } else if (this.currentFilter.activeTags.size === 1) {
      const selectedTag = Array.from(this.currentFilter.activeTags)[0];
      countInfo.textContent += ` (filtered by: ${selectedTag})`;
    }
    
    this.championsList.appendChild(countInfo);
  }
  
  // Function to filter and display champions
  filterAndDisplayChampions() {
    console.log('Filtering champions with:', {
      searchText: this.currentFilter.searchText,
      activeTags: Array.from(this.currentFilter.activeTags)
    });
    
    const filteredChampions = this.filterChampions();
    console.log(`Filtered ${filteredChampions.length} champions out of ${this.allChampions.length}`);
    
    this.displayChampions(filteredChampions);
  }
  
  // Update tag filter UI to show active state
  updateTagFilterUI() {
    console.log('Updating tag filter UI, active tags:', Array.from(this.currentFilter.activeTags));
    
    const tagFilters = document.querySelectorAll('.tag-filter');
    tagFilters.forEach(button => {
      const tag = button.getAttribute('data-tag');
      const isActive = this.currentFilter.activeTags.has(tag);
      
      console.log(`Tag button: ${tag}, active: ${isActive}`);
      
      if (isActive) {
        button.classList.add('active');
      } else {
        button.classList.remove('active');
      }
    });
  }
  
  // Function to reset all filters
  resetAllFilters() {
    console.log('Resetting all filters');
    
    // Reset search input
    const searchInput = document.getElementById('search-input');
    const searchClear = document.getElementById('search-clear');
    if (searchInput) searchInput.value = '';
    this.currentFilter.searchText = '';
    if (searchClear) searchClear.style.display = 'none';
    
    // Reset tag filters
    this.currentFilter.activeTags.clear();
    this.updateTagFilterUI();
    
    // Reapply filters and display
    console.log('After reset - searchText:', this.currentFilter.searchText, 'activeTags:', Array.from(this.currentFilter.activeTags));
    this.filterAndDisplayChampions();
  }
  
  // Function to fetch and display champion details
  async showChampionDetail(championId) {
    try {
      // Find champion in our existing data
      const champion = this.allChampions.find(c => c.id === championId);
      
      if (!champion) {
        throw new Error(`Champion with ID ${championId} not found`);
      }
      
      // Update current champion
      this.currentChampion = champion;
      
      // Hide champions list, show detail view
      this.championsList.style.display = 'none';
      this.championDetailElement.style.display = 'block';
      
      // Hide the search container in champion detail view
      document.getElementById('champions-search-container').style.display = 'none';
      
      // Show loading state
      const loadingElement = document.createElement('div');
      loadingElement.className = 'loading';
      loadingElement.innerHTML = `
        <div class="loading-spinner"></div>
        <p>Loading ${champion.name} details...</p>
      `;
      this.championDetailElement.querySelector('.detail-content').appendChild(loadingElement);
      
      // Check if we have cached champion details
      const cacheKey = `${window.LOLUtils.CHAMPION_DETAIL_CACHE_PREFIX}${championId}`;
      let championDetails = null;
      
      try {
        // Try to get cached details
        await new Promise((resolve) => {
          chrome.storage.local.get([cacheKey], (result) => {
            championDetails = result[cacheKey];
            resolve();
          });
        });
      } catch (error) {
        console.error('Error reading cache:', error);
      }
      
      // If no cached details, fetch from API
      if (!championDetails) {
        // Fetch champion details from API
        const response = await fetch(`${this.API_BASE_URL}/champions/${championId}`);
        
        if (!response.ok) {
          throw new Error(`API request failed with status ${response.status}`);
        }
        
        championDetails = await response.json();
        
        // Check if tips are present, if not we might need to adjust our approach
        const hasTips = 
          (championDetails.allyTips && championDetails.allyTips.length > 0) ||
          (championDetails.allytips && championDetails.allytips.length > 0) ||
          (championDetails.ally_tips && championDetails.ally_tips.length > 0) ||
          (championDetails.enemyTips && championDetails.enemyTips.length > 0) ||
          (championDetails.enemytips && championDetails.enemytips.length > 0) ||
          (championDetails.enemy_tips && championDetails.enemy_tips.length > 0);
          
        if (!hasTips) {
          console.warn(`No tips found for champion ${championId} - this may indicate a data issue`);
        }
        
        // Cache the details
        chrome.storage.local.set({
          [cacheKey]: championDetails
        }, () => {
          console.log(`Champion details cached for ${championId}`);
        });
      } else {
        console.log(`Using cached details for ${championId}`);
      }
      
      // Remove loading state
      this.championDetailElement.querySelector('.loading')?.remove();
      
      // Display champion details
      this.displayChampionDetail(championDetails);
    } catch (error) {
      console.error('Error showing champion details:', error);
      
      // Show error in detail view
      this.championDetailElement.querySelector('.loading')?.remove();
      
      const errorElement = document.createElement('div');
      errorElement.className = 'error';
      errorElement.textContent = `Error loading champion details: ${error.message}`;
      this.championDetailElement.querySelector('.detail-content').appendChild(errorElement);
    }
  }
  
  // Function to display champion details
  displayChampionDetail(champion) {
    // Debug log champion data
    console.log(`Champion ${champion.name} details:`, champion);
    
    // Debug spells with detailed information
    if (champion.spells) {
      console.log(`Spell data for ${champion.name}:`);
      champion.spells.forEach((spell, index) => {
        console.log(`Spell ${index} (${spell.key || 'unknown key'}): ID=${spell.id || 'missing'}`);
        console.log(`- cooldownBurn: ${spell.cooldownBurn || 'missing'}`);
        console.log(`- cooldown: ${JSON.stringify(spell.cooldown) || 'missing'}`);
        console.log(`- costBurn: ${spell.costBurn || 'missing'}`);
        console.log(`- cost: ${JSON.stringify(spell.cost) || 'missing'}`);
        console.log(`- rangeBurn: ${spell.rangeBurn || 'missing'}`);
        console.log(`- range: ${JSON.stringify(spell.range) || 'missing'}`);
      });
    }
    
    // Debug tips - inspect ALL champion properties to find tips
    console.log(`Tips for ${champion.name}:`);
    
    // Look at all champion properties to find tips
    console.log(`All champion properties:`);
    for (const prop in champion) {
      // Look for properties that might contain "tip" in their name
      if (prop.toLowerCase().includes('tip')) {
        console.log(`Property ${prop}:`, champion[prop]);
      }
    }
    
    // Check common property name formats
    console.log(`Common property formats:`);
    console.log(`allyTips:`, champion.allyTips || 'undefined');
    console.log(`enemyTips:`, champion.enemyTips || 'undefined');
    console.log(`allytips:`, champion.allytips || 'undefined');
    console.log(`enemytips:`, champion.enemytips || 'undefined');
    console.log(`ally_tips:`, champion.ally_tips || 'undefined');
    console.log(`enemy_tips:`, champion.enemy_tips || 'undefined');
    
    // Set champion name and title
    this.championDetailElement.querySelector('.champion-detail-name').textContent = champion.name;
    this.championDetailElement.querySelector('.champion-detail-title').textContent = champion.title || '';
    
    // Set champion splash art
    const splashElement = this.championDetailElement.querySelector('.champion-splash');
    const splashUrl = `${this.API_BASE_URL}/assets/champion/splash/${champion.id}/0`;
    splashElement.innerHTML = `<img src="${splashUrl}" alt="${champion.name}" class="champion-splash-img">`;
    
    // Add error handler to the splash image
    const splashImgElement = splashElement.querySelector('.champion-splash-img');
    splashImgElement.addEventListener('error', function() {
      window.LOLUtils.handleImageError(this);
    });
    
    // Set champion tags
    const tagsElement = this.championDetailElement.querySelector('.champion-detail-tags');
    tagsElement.innerHTML = '';
    
    if (champion.tags && champion.tags.length > 0) {
      champion.tags.forEach(tag => {
        const tagElement = document.createElement('span');
        tagElement.className = `champion-tag tag-${tag.toLowerCase()}`;
        tagElement.textContent = tag;
        tagsElement.appendChild(tagElement);
      });
    }
    
    // Set champion stats with enhanced layout and visuals
    const statsGrid = this.championDetailElement.querySelector('.stats-grid');
    statsGrid.innerHTML = '';
    
    if (champion.stats && champion.info) {
      // Create a container for the champion ratings/difficulty metrics
      const ratingsSection = document.createElement('div');
      ratingsSection.className = 'stats-section rating-section';
      ratingsSection.innerHTML = `
        <h4><span>Champion Metrics</span></h4>
        <div class="ratings-grid">
          <div class="stat-item rating-item">
            <div class="stat-value">${champion.info.attack || 0}<span class="rating-scale">/10</span></div>
            <div class="stat-name">Attack</div>
            <div class="stat-bar" style="--fill-percent: ${(champion.info.attack || 0) * 10}%"></div>
          </div>
          <div class="stat-item rating-item">
            <div class="stat-value">${champion.info.defense || 0}<span class="rating-scale">/10</span></div>
            <div class="stat-name">Defense</div>
            <div class="stat-bar" style="--fill-percent: ${(champion.info.defense || 0) * 10}%"></div>
          </div>
          <div class="stat-item rating-item">
            <div class="stat-value">${champion.info.magic || 0}<span class="rating-scale">/10</span></div>
            <div class="stat-name">Magic</div>
            <div class="stat-bar" style="--fill-percent: ${(champion.info.magic || 0) * 10}%"></div>
          </div>
          <div class="stat-item rating-item">
            <div class="stat-value">${champion.info.difficulty || 0}<span class="rating-scale">/10</span></div>
            <div class="stat-name">Difficulty</div>
            <div class="stat-bar" style="--fill-percent: ${(champion.info.difficulty || 0) * 10}%"></div>
          </div>
        </div>
      `;
      statsGrid.appendChild(ratingsSection);
      
      // Group primary stats in a more organized way
      const baseStatsSection = document.createElement('div');
      baseStatsSection.className = 'stats-section base-stats-section';
      baseStatsSection.innerHTML = '<h4><span>Combat Stats</span></h4><div class="base-stats-grid"></div>';
      
      const secondaryStatsSection = document.createElement('div');
      secondaryStatsSection.className = 'stats-section secondary-stats-section';
      secondaryStatsSection.innerHTML = '<h4><span>Scaling Stats</span></h4><div class="secondary-stats-grid"></div>';
      
      // Map stat keys to more readable names with improved icons and categories
      const primaryStats = {
        hp: { name: 'Health', icon: '❤️', category: 'primary', cssClass: 'stat-health' },
        mp: { name: 'Mana', icon: '🔹', category: 'primary', cssClass: 'stat-mana' },
        movespeed: { name: 'Move Speed', icon: '👟', category: 'primary', cssClass: 'stat-movespeed' },
        armor: { name: 'Armor', icon: '🛡️', category: 'primary', cssClass: 'stat-armor' },
        spellblock: { name: 'Magic Resist', icon: '🔮', category: 'primary', cssClass: 'stat-mr' },
        attackrange: { name: 'Attack Range', icon: '🏹', category: 'primary', cssClass: 'stat-range' },
        attackdamage: { name: 'Attack Damage', icon: '⚔️', category: 'primary', cssClass: 'stat-ad' },
        attackspeed: { name: 'Attack Speed', icon: '⚡', category: 'primary', cssClass: 'stat-as' },
        crit: { name: 'Critical', icon: '🎯', category: 'primary', cssClass: 'stat-crit' }
      };
      
      const secondaryStats = {
        hpperlevel: { name: 'HP/Level', icon: '📈', category: 'scaling', cssClass: 'stat-hp-per-lvl' },
        mpperlevel: { name: 'Mana/Level', icon: '📈', category: 'scaling', cssClass: 'stat-mana-per-lvl' },
        armorperlevel: { name: 'Armor/Lvl', icon: '📈', category: 'scaling', cssClass: 'stat-armor-per-lvl' },
        spellblockperlevel: { name: 'MR/Level', icon: '📈', category: 'scaling', cssClass: 'stat-mr-per-lvl' },
        attackdamageperlevel: { name: 'AD/Level', icon: '📈', category: 'scaling', cssClass: 'stat-ad-per-lvl' },
        attackspeedperlevel: { name: 'AS/Level', icon: '📈', category: 'scaling', cssClass: 'stat-as-per-lvl' },
        critperlevel: { name: 'Crit/Level', icon: '📈', category: 'scaling', cssClass: 'stat-crit-per-lvl' },
        hpregen: { name: 'HP Regen', icon: '💓', category: 'regen', cssClass: 'stat-hp-regen' },
        hpregenperlevel: { name: 'HP Regen/Lvl', icon: '📈', category: 'regen', cssClass: 'stat-hp-regen-per-lvl' },
        mpregen: { name: 'Mana Regen', icon: '💧', category: 'regen', cssClass: 'stat-mana-regen' },
        mpregenperlevel: { name: 'Mana Regen/Lvl', icon: '📈', category: 'regen', cssClass: 'stat-mana-regen-per-lvl' }
      };
      
      // Add stat format functions
      const formatStatValue = (key, value) => {
        if (value === undefined || value === null) return '-';
        
        // Special formatting for different stat types
        if (key === 'attackspeed') return value.toFixed(2);
        if (key.includes('regen')) return value.toFixed(1);
        if (key === 'movespeed') return Math.round(value);
        if (key === 'attackrange') return Math.round(value);
        if (key.includes('perlevel')) return `+${value.toFixed(1)}`;
        
        return typeof value === 'number' ? value.toFixed(1) : value;
      };
      
      // Create primary stat blocks
      const baseStatsGrid = baseStatsSection.querySelector('.base-stats-grid');
      Object.entries(primaryStats).forEach(([key, statInfo]) => {
        const value = champion.stats[key];
        if (value !== undefined && value !== null) {
          const statElement = document.createElement('div');
          statElement.className = `stat-item ${statInfo.cssClass || ''}`;
          statElement.innerHTML = `
            <div class="stat-value">${formatStatValue(key, value)}</div>
            <div class="stat-name">${statInfo.name}</div>
            <div class="stat-icon">${statInfo.icon}</div>
            <div class="stat-hextech-glow"></div>
          `;
          baseStatsGrid.appendChild(statElement);
        }
      });
      
      // Create secondary stat blocks
      const secondaryStatsGrid = secondaryStatsSection.querySelector('.secondary-stats-grid');
      Object.entries(secondaryStats).forEach(([key, statInfo], index) => {
        const value = champion.stats[key];
        if (value !== undefined && value !== null) {
          const statElement = document.createElement('div');
          statElement.className = `stat-item ${statInfo.cssClass || ''}`;
          statElement.innerHTML = `
            <div class="stat-value">${formatStatValue(key, value)}</div>
            <div class="stat-name">${statInfo.name}</div>
            <div class="stat-icon">${statInfo.icon}</div>
            <div class="stat-hextech-glow"></div>
          `;
          // Set a custom CSS variable to ensure staggered animations work properly
          statElement.style.setProperty('--item-index', index);
          secondaryStatsGrid.appendChild(statElement);
        }
      });
      
      // Only add sections that have content
      if (baseStatsGrid.children.length > 0) {
        statsGrid.appendChild(baseStatsSection);
      }
      
      if (secondaryStatsGrid.children.length > 0) {
        statsGrid.appendChild(secondaryStatsSection);
      }
      
      // Removed Champion Highlights section
      
      // Create radar chart as a completely separate section
      const attack = champion.info.attack || 0;
      const defense = champion.info.defense || 0;
      const magic = champion.info.magic || 0;
      const difficulty = champion.info.difficulty || 0;
      
      // Calculate radar chart points (hexagon shape)
      const calculateRadarPoint = (value, angle) => {
        const center = 50;
        const maxRadius = 40;
        const radius = (value / 10) * maxRadius;
        const x = center + radius * Math.cos(angle);
        const y = center + radius * Math.sin(angle);
        return `${x},${y}`;
      };
      
      const angles = [
        0,               // Attack (right)
        Math.PI / 3,     // Defense (bottom right)
        2 * Math.PI / 3, // Magic (bottom left)
        Math.PI,         // Difficulty (left)
        4 * Math.PI / 3, // Utility (top left) - calculated from others
        5 * Math.PI / 3  // Mobility (top right) - calculated from others
      ];
      
      // Calculate supplementary stats based on primary ones (for visualization balance)
      const utility = Math.max(2, Math.round((magic + defense) / 2));
      const mobility = Math.max(2, Math.round((attack + difficulty) / 3));
      
      const radarValues = [attack, defense, magic, difficulty, utility, mobility];
      const radarPoints = radarValues.map((value, i) => calculateRadarPoint(value, angles[i])).join(' ');
      
      // Base points for the maximum outline (value 10)
      const maxPoints = angles.map(angle => calculateRadarPoint(10, angle)).join(' ');
      
      // Create champion profile section with resource and role info plus radar chart
      const profileSection = document.createElement('div');
      profileSection.className = 'stats-section profile-section';
      
      profileSection.innerHTML = `
        <h4><span>Champion Profile</span></h4>
        
        <div class="profile-content">
          <div class="profile-highlights">
            <div class="highlight-item">
              <div class="highlight-label">Resource</div>
              <div class="highlight-value">${champion.partype || 'Mana'}</div>
            </div>
            <div class="highlight-item">
              <div class="highlight-label">Role</div>
              <div class="highlight-value">${champion.tags ? champion.tags.join(', ') : 'Unknown'}</div>
            </div>
          </div>
          
          <div class="radar-chart-container">
            <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
              <!-- Background hexagon grid -->
              <polygon class="radar-grid-10" points="${maxPoints}" />
              <polygon class="radar-grid-8" points="${angles.map(angle => calculateRadarPoint(8, angle)).join(' ')}" />
              <polygon class="radar-grid-6" points="${angles.map(angle => calculateRadarPoint(6, angle)).join(' ')}" />
              <polygon class="radar-grid-4" points="${angles.map(angle => calculateRadarPoint(4, angle)).join(' ')}" />
              <polygon class="radar-grid-2" points="${angles.map(angle => calculateRadarPoint(2, angle)).join(' ')}" />
              
              <!-- Champion stat profile -->
              <polygon class="radar-data" points="${radarPoints}" />
              
              <!-- Stat labels -->
              <text x="${calculateRadarPoint(11, angles[0]).split(',')[0]}" y="${calculateRadarPoint(11, angles[0]).split(',')[1]}" class="radar-label">Attack</text>
              <text x="${calculateRadarPoint(11, angles[1]).split(',')[0]}" y="${calculateRadarPoint(11, angles[1]).split(',')[1]}" class="radar-label">Defense</text>
              <text x="${calculateRadarPoint(11, angles[2]).split(',')[0]}" y="${calculateRadarPoint(11, angles[2]).split(',')[1]}" class="radar-label">Magic</text>
              <text x="${calculateRadarPoint(11, angles[3]).split(',')[0]}" y="${calculateRadarPoint(11, angles[3]).split(',')[1]}" class="radar-label">Difficulty</text>
              <text x="${calculateRadarPoint(11, angles[4]).split(',')[0]}" y="${calculateRadarPoint(11, angles[4]).split(',')[1]}" class="radar-label">Utility</text>
              <text x="${calculateRadarPoint(11, angles[5]).split(',')[0]}" y="${calculateRadarPoint(11, angles[5]).split(',')[1]}" class="radar-label">Mobility</text>
              
              <!-- Stat data points -->
              <circle cx="${calculateRadarPoint(attack, angles[0]).split(',')[0]}" cy="${calculateRadarPoint(attack, angles[0]).split(',')[1]}" r="2" class="radar-point" data-stat="attack" />
              <circle cx="${calculateRadarPoint(defense, angles[1]).split(',')[0]}" cy="${calculateRadarPoint(defense, angles[1]).split(',')[1]}" r="2" class="radar-point" data-stat="defense" />
              <circle cx="${calculateRadarPoint(magic, angles[2]).split(',')[0]}" cy="${calculateRadarPoint(magic, angles[2]).split(',')[1]}" r="2" class="radar-point" data-stat="magic" />
              <circle cx="${calculateRadarPoint(difficulty, angles[3]).split(',')[0]}" cy="${calculateRadarPoint(difficulty, angles[3]).split(',')[1]}" r="2" class="radar-point" data-stat="difficulty" />
              <circle cx="${calculateRadarPoint(utility, angles[4]).split(',')[0]}" cy="${calculateRadarPoint(utility, angles[4]).split(',')[1]}" r="2" class="radar-point" data-stat="utility" />
              <circle cx="${calculateRadarPoint(mobility, angles[5]).split(',')[0]}" cy="${calculateRadarPoint(mobility, angles[5]).split(',')[1]}" r="2" class="radar-point" data-stat="mobility" />
            </svg>
            
            <div class="radar-legend">
              <div class="radar-legend-title">Strength Profile</div>
              <div class="radar-legend-description">Visualization of ${champion.name}'s strengths</div>
            </div>
          </div>
        </div>
      `;
      
      // Add the profile section inside the stats grid
      statsGrid.appendChild(profileSection);
    }
    
    // Set champion lore
    const loreElement = this.championDetailElement.querySelector('.lore-text');
    loreElement.textContent = champion.lore || 'No lore available.';
    
    // Set champion abilities with enhanced layout and interactive elements
    const abilitiesContainer = this.championDetailElement.querySelector('.abilities-container');
    abilitiesContainer.innerHTML = '';
    
    if (champion.spells && champion.spells.length > 0) {
      // Add passive ability with enhanced styling
      if (champion.passive) {
        const passiveElement = document.createElement('div');
        passiveElement.className = 'ability passive';
        
        // For passive ability image
        let passiveImageUrl = 'images/champion-placeholder.png';
        // According to the API_ENDPOINTS.md, the correct URL is:
        // GET /assets/champion/passive/{champion_id}
        passiveImageUrl = `${this.API_BASE_URL}/assets/champion/passive/${champion.id}`;
        console.log(`Loading passive image for ${champion.id}: ${passiveImageUrl}`);
        
        // Make sure we have a passive description, default to empty string if missing
        if (!champion.passive.description) {
          console.warn(`Missing description for ${champion.name}'s passive`);
          champion.passive.description = `No description available for ${champion.name}'s passive ability.`;
        }
        
        // Format the passive description with highlighted keywords
        const formattedPassiveDescription = this._formatAbilityText(champion.passive.description);
        
        passiveElement.innerHTML = `
          <div class="ability-header">
            <div class="ability-image">
              <img src="${passiveImageUrl}" alt="${champion.passive.name}" class="ability-img">
            </div>
            <div class="ability-info">
              <div class="ability-name">${champion.passive.name}</div>
              <div class="ability-type">Passive</div>
            </div>
          </div>
          <div class="ability-description-container">
            <div class="ability-description">${formattedPassiveDescription}</div>
          </div>
        `;
        
        abilitiesContainer.appendChild(passiveElement);
      }
      
      // Add regular abilities (Q, W, E, R) with enhanced styling and interactive elements
      const abilityKeys = ['Q', 'W', 'E', 'R'];
      
      champion.spells.forEach((spell, index) => {
        if (index < 4) {
          const abilityElement = document.createElement('div');
          abilityElement.className = 'ability';
          
          // Make sure we have a spell description, default to empty string if missing
          if (!spell.description) {
            console.warn(`Missing description for ${champion.name}'s spell ${index}`);
            spell.description = `No description available for ${champion.name}'s ${abilityKeys[index]} ability.`;
          }
          
          // For spell ability image, we need to handle different API response formats
          let spellImageUrl = 'images/champion-placeholder.png';
          
          // Try multiple approaches to get a valid spell image URL
          if (spell.id) {
            // First try the direct spell ID approach (most reliable)
            spellImageUrl = `${this.API_BASE_URL}/assets/champion/spell/${spell.id}`;
            console.log(`Loading spell image for ${spell.id}: ${spellImageUrl}`);
          } else if (spell.image && spell.image.full) {
            // If we have an image.full property, try using that
            const imageName = spell.image.full.replace('.png', '');
            spellImageUrl = `${this.API_BASE_URL}/assets/champion/spell/${imageName}`;
            console.log(`Loading spell image using image.full: ${spellImageUrl}`);
          } else {
            // Last resort - try constructing a spell ID from champion ID and slot
            // This is a best-effort approach based on naming conventions
            const slotLetters = ['Q', 'W', 'E', 'R'];
            const constructedId = champion.id + slotLetters[index];
            spellImageUrl = `${this.API_BASE_URL}/assets/champion/spell/${constructedId}`;
            console.log(`Loading spell image using constructed ID: ${spellImageUrl}`);
          }
          
          const key = abilityKeys[index];
          
          // Format ability text to highlight important information
          const formattedDescription = this._formatAbilityText(spell.description);
          
          // Extract ability details for enhanced display
          // Handle different possible property names for cooldown
          let cooldown = "N/A";
          if (spell.cooldownBurn) {
            cooldown = spell.cooldownBurn;
          } else if (spell.cooldown) {
            // If we have an array of cooldowns, join them with slashes
            if (Array.isArray(spell.cooldown)) {
              cooldown = spell.cooldown.join('/');
            } else {
              cooldown = String(spell.cooldown);
            }
          }
          
          // Handle different possible property names for cost
          let cost = "0";
          if (spell.costBurn) {
            cost = spell.costBurn;
          } else if (spell.cost) {
            // If we have an array of costs, join them with slashes
            if (Array.isArray(spell.cost)) {
              cost = spell.cost.join('/');
            } else {
              cost = String(spell.cost);
            }
          }
          
          const costType = champion.partype || "Resource";
          
          // Handle different possible property names for range
          let range = "N/A";
          if (spell.rangeBurn) {
            range = spell.rangeBurn;
          } else if (spell.range) {
            // If we have an array of ranges, join them with slashes
            if (Array.isArray(spell.range)) {
              range = spell.range.join('/');
            } else {
              range = String(spell.range);
            }
          }
          
          // Create visual stats for the ability with interactive visualizations
          
          // Process cooldown data for visualization
          let cooldownValue = cooldown;
          if (cooldown.includes('/')) {
            // If cooldown has multiple values (like "12/11/10/9/8"), use the lowest one
            cooldownValue = cooldown.split('/').pop();
          }
          // Convert to number for visualization
          let cooldownNum = parseFloat(cooldownValue);
          if (isNaN(cooldownNum)) cooldownNum = 0;
          
          // Calculate cooldown visualization level (1-5)
          const cooldownLevel = Math.min(5, Math.max(1, Math.ceil(cooldownNum / 4)));
          
          // Create a cooldown meter
          const cooldownMeter = `<div class="cooldown-meter level-${cooldownLevel}">
            ${Array(cooldownLevel).fill('<span class="meter-segment"></span>').join('')}
          </div>`;
          
          const cooldownStat = `<div class="ability-stat cooldown-stat" title="Lower cooldown allows more frequent use">
            <span class="ability-stat-icon">⏱</span>
            <span>Cooldown: ${cooldown}s</span>
            ${cooldownMeter}
          </div>`;
          
          // Process cost data for visualization
          let costValue = "0";
          if (cost.includes('/')) {
            // If cost has multiple values, use the highest one
            costValue = cost.split('/').pop();
          } else {
            costValue = cost;
          }
          
          // Convert to number for visualization
          let costNum = parseFloat(costValue);
          if (isNaN(costNum)) costNum = 0;
          
          // Calculate cost visualization level (1-5)
          const costType_LC = costType.toLowerCase();
          const costColor = costType_LC.includes('mana') ? 'mana' : 
                         costType_LC.includes('energy') ? 'energy' : 
                         costType_LC.includes('health') ? 'health' : 
                         costType_LC.includes('fury') ? 'fury' : 'resource';
          
          const costLevel = Math.min(5, Math.max(0, Math.ceil(costNum / 20)));
          
          // Create a cost meter
          const costMeter = costNum > 0 ? `<div class="cost-meter ${costColor}-cost level-${costLevel}">
            ${Array(costLevel).fill('<span class="meter-segment"></span>').join('')}
          </div>` : '';
          
          const costStat = cost !== "0" ? `<div class="ability-stat cost-stat" title="Resource required to use this ability">
            <span class="ability-stat-icon">✧</span>
            <span>Cost: ${cost} ${costType}</span>
            ${costMeter}
          </div>` : '';
          
          // Process range data for visualization
          let rangeValue = range;
          if (range.includes('/')) {
            // If range has multiple values, use the highest one
            rangeValue = range.split('/').pop();
          }
          
          // Convert to number for visualization  
          let rangeNum = parseFloat(rangeValue);
          if (isNaN(rangeNum)) rangeNum = 0;
          
          // Calculate range visualization type
          const rangeType = rangeValue.toLowerCase().includes('global') ? 'global' :
                         rangeNum > 1000 ? 'long' :
                         rangeNum > 500 ? 'medium' :
                         rangeNum > 0 ? 'short' : 'self';
          
          const rangeIndicator = `<div class="range-indicator range-${rangeType}">
            <span class="center-point"></span>
            <span class="range-circle"></span>
          </div>`;
          
          const rangeStat = range !== "N/A" && range !== "self" ? `<div class="ability-stat range-stat" title="The distance this ability can reach">
            <span class="ability-stat-icon">↔</span>
            <span>Range: ${range}</span>
            ${rangeIndicator}
          </div>` : '';
          
          // Add special tags for ability based on description
          const tags = [];
          const description = spell.description || '';
          
          if (description.toLowerCase().includes('stun') || 
              description.toLowerCase().includes('immobilize') ||
              description.toLowerCase().includes('root')) {
            tags.push('<span class="ability-tag cc-tag">CC</span>');
          }
          
          if (description.toLowerCase().includes('heal') || 
              description.toLowerCase().includes('restore health')) {
            tags.push('<span class="ability-tag heal-tag">HEAL</span>');
          }
          
          if (description.toLowerCase().includes('shield')) {
            tags.push('<span class="ability-tag shield-tag">SHIELD</span>');
          }
          
          if (description.toLowerCase().includes('dash') || 
              description.toLowerCase().includes('blink') ||
              description.toLowerCase().includes('teleport')) {
            tags.push('<span class="ability-tag mobility-tag">MOBILITY</span>');
          }
          
          const abilityTags = tags.length > 0 ? 
            `<div class="ability-tags">${tags.join('')}</div>` : '';
          
          abilityElement.innerHTML = `
            <div class="ability-header">
              <div class="ability-image">
                <img src="${spellImageUrl}" alt="${spell.name}" class="ability-img">
              </div>
              <div class="ability-info">
                <div class="ability-name">${spell.name}</div>
                <div class="ability-type">${key}</div>
                ${abilityTags}
              </div>
            </div>
            <div class="ability-description-container">
              <div class="ability-description">${formattedDescription}</div>
            </div>
            <div class="ability-cooldown">
              ${cooldownStat}
              ${costStat}
              ${rangeStat}
            </div>
          `;
          
          abilitiesContainer.appendChild(abilityElement);
        }
      });
    } else {
      abilitiesContainer.innerHTML = '<p>No ability information available.</p>';
    }
    
    // Set champion tips by calling the separate method
    this.displayChampionTips(champion);
  }
  
  // Helper method to format ability text with highlighted keywords
  _formatAbilityText(text) {
    if (!text) return '';
    
    // Replace common LoL keywords and metrics with colored and styled versions
    // Physical damage
    text = text.replace(/(\d+(?:\.\d+)?(?:%)?(?:\s+to\s+\d+(?:\.\d+)?(?:%)?)?)\s+(physical damage|Physical Damage|Attack Damage)/gi, 
      '<span class="physical-damage">$1 physical damage</span>');
    
    // Magic damage
    text = text.replace(/(\d+(?:\.\d+)?(?:%)?(?:\s+to\s+\d+(?:\.\d+)?(?:%)?)?)\s+(magic damage|Magic Damage|Ability Power)/gi, 
      '<span class="magic-damage">$1 magic damage</span>');
    
    // Status effects
    const statusEffects = ['stun', 'slow', 'knock up', 'silence', 'root', 'snare', 'charm', 'taunt', 'blind', 'disarm', 'ground', 'nearsight', 'polymorph', 'sleep', 'suppress'];
    statusEffects.forEach(effect => {
      const regex = new RegExp(`(${effect}(?:s|ed|ing)?)`, 'gi');
      text = text.replace(regex, '<span class="status-effect">$1</span>');
    });
    
    // Healing effects
    text = text.replace(/(heals?|healing|restore|restored|restores)\s+(\d+(?:\.\d+)?(?:%)?(?:\s+to\s+\d+(?:\.\d+)?(?:%)?)?)/gi, 
      '<span class="healing">$1 $2</span>');
    
    // Movement speed
    text = text.replace(/(movement speed|Movement Speed)\s+(\d+(?:\.\d+)?(?:%)?)/gi, 
      '<span class="movement-speed">movement speed $2</span>');
    
    // Recast/active component keywords
    text = text.replace(/\b(recast|Recast|RECAST)\b/gi, '<span class="recast-ability">RECAST</span>');
    text = text.replace(/\b(active|Active|ACTIVE):/gi, '<span class="spell-active">ACTIVE:</span>');
    text = text.replace(/\b(passive|Passive|PASSIVE):/gi, '<span class="spell-passive">PASSIVE:</span>');
    
    return text;
  }
  
  // Set champion tips
  displayChampionTips(champion) {
    const allyTipsList = this.championDetailElement.querySelector('.ally-tips-list');
    const enemyTipsList = this.championDetailElement.querySelector('.enemy-tips-list');
    
    allyTipsList.innerHTML = '';
    enemyTipsList.innerHTML = '';
    
    // Get ally tips, checking multiple possible property names
    let allyTips = [];
    
    // Check API endpoint documentation to see what property names are used
    // The backend converts database snake_case to camelCase in the response
    if (champion.allyTips && Array.isArray(champion.allyTips)) {
      console.log('Found allyTips property (camelCase with capital T)');
      allyTips = champion.allyTips;
    } else if (champion.allytips && Array.isArray(champion.allytips)) {
      console.log('Found allytips property (camelCase)');
      allyTips = champion.allytips;
    } else if (champion.ally_tips && Array.isArray(champion.ally_tips)) {
      console.log('Found ally_tips property (snake_case)');
      allyTips = champion.ally_tips;
    } else {
      console.warn('No ally tips property found in champion data');
    }
    
    // Display ally tips
    if (allyTips.length > 0) {
      allyTips.forEach(tip => {
        if (tip && typeof tip === 'string') {
          const tipItem = document.createElement('li');
          tipItem.textContent = tip;
          allyTipsList.appendChild(tipItem);
        }
      });
    } else {
      allyTipsList.innerHTML = '<li>No ally tips available.</li>';
    }
    
    // Get enemy tips, checking multiple possible property names
    let enemyTips = [];
    
    // Check API endpoint documentation to see what property names are used
    // The backend converts database snake_case to camelCase in the response
    if (champion.enemyTips && Array.isArray(champion.enemyTips)) {
      console.log('Found enemyTips property (camelCase with capital T)');
      enemyTips = champion.enemyTips;
    } else if (champion.enemytips && Array.isArray(champion.enemytips)) {
      console.log('Found enemytips property (camelCase)');
      enemyTips = champion.enemytips;
    } else if (champion.enemy_tips && Array.isArray(champion.enemy_tips)) {
      console.log('Found enemy_tips property (snake_case)');
      enemyTips = champion.enemy_tips;
    } else {
      console.warn('No enemy tips property found in champion data');
    }
    
    // Display enemy tips
    if (enemyTips.length > 0) {
      enemyTips.forEach(tip => {
        if (tip && typeof tip === 'string') {
          const tipItem = document.createElement('li');
          tipItem.textContent = tip;
          enemyTipsList.appendChild(tipItem);
        }
      });
    } else {
      enemyTipsList.innerHTML = '<li>No enemy tips available.</li>';
    }
    
    // Set champion skins
    const skinsCarousel = this.championDetailElement.querySelector('.skins-carousel');
    skinsCarousel.innerHTML = '';
    
    if (champion.skins && champion.skins.length > 0) {
      champion.skins.forEach(skin => {
        const skinElement = document.createElement('div');
        skinElement.className = 'skin-item';
        
        const skinImageUrl = `${this.API_BASE_URL}/assets/champion/loading/${champion.id}/${skin.num}`;
        
        skinElement.innerHTML = `
          <div class="skin-image">
            <img src="${skinImageUrl}" alt="${skin.name}" class="skin-img">
          </div>
          <div class="skin-name">${skin.name === 'default' ? champion.name : skin.name}</div>
        `;
        
        skinsCarousel.appendChild(skinElement);
      });
    } else {
      skinsCarousel.innerHTML = '<p>No skin information available.</p>';
    }
    
    // Set up tab navigation
    window.LOLUtils.setupTabNavigation();
    
    // Dispatch event to notify that champion detail view is shown
    // This allows other components to react to this event
    document.dispatchEvent(new CustomEvent('championDetailShown', {
      detail: { championId: champion.id }
    }));
  }
  
  // Function to navigate back to champions list
  showChampionsList() {
    // Hide champion detail
    this.championDetailElement.style.display = 'none';
    
    // Show champions list
    this.championsList.style.display = 'grid';
    
    // Show the search container again
    document.getElementById('champions-search-container').style.display = 'block';
    
    // Clear current champion
    this.currentChampion = null;
    
    // Scroll back to top
    window.scrollTo(0, 0);
  }
}

// Export the class
window.ChampionsManager = ChampionsManager;