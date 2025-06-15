// Update to the ItemsManager's fetchItems method to fetch all items across multiple pages

// Original method only fetches one page:
// const response = await fetch(`${this.API_BASE_URL}/items?limit=100`);

// Modified version to fetch all items across pages:
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