// This script updates the runes.js file to use local assets

const originalFetchFunction = `
  // Function to fetch runes data with caching
  async fetchRunes() {
    try {
      // Show loading state
      this.loadingElement.style.display = 'block';
      this.errorElement.style.display = 'none';
      this.noResultsElement.style.display = 'none';
      
      // Check if we have cached runes data
      const runes = await window.LOLUtils.getCachedRunes();
      
      if (runes) {
        // Use cached data
        console.log('Using cached runes data');
        this.runeData = runes; // Store the complete response
        this.allStyles = Array.isArray(runes.paths) ? runes.paths : runes; // Extract paths array if available
        this.processRunes();
        return;
      }
      
      // No cache or expired cache, fetch from API
      console.log('Fetching runes from API');
      try {
        const response = await fetch(\`\${this.API_BASE_URL}/runes\`);
        
        if (!response.ok) {
          throw new Error(\`API request failed with status \${response.status}\`);
        }
        
        const data = await response.json();
        this.runeData = data; // Store the complete response
        
        console.log('API response received:', typeof data);
        console.log('Has paths property:', data && data.paths ? 'yes' : 'no');
        
        // Log the API response structure for debugging
        console.log('API response structure:', {
          isArray: Array.isArray(data),
          hasPathsProperty: data && data.paths ? true : false,
          topLevelKeys: data ? Object.keys(data) : []
        });
        
        // Handle the RuneTreeResponse format from backend
        if (data && data.paths && Array.isArray(data.paths)) {
          console.log(\`API returned proper format with \${data.paths.length} paths\`);
          this.allStyles = data.paths;
        } 
        // Handle case where API returns an array directly
        else if (data && Array.isArray(data)) {
          console.log('API returned direct array of styles');
          this.allStyles = data;
        }
        // Handle object response with non-standard structure 
        else if (data && typeof data === 'object') {
          // Try all possible property names that might contain rune paths
          const possibleStylesProperties = ['paths', 'styles', 'runePaths', 'runes', 'data'];
          
          let foundStyles = false;
          
          // Check for known property names that might contain the paths
          for (const prop of possibleStylesProperties) {
            if (data[prop]) {
              if (Array.isArray(data[prop]) && data[prop].length > 0) {
                console.log(\`Found paths in '\${prop}' property\`);
                this.allStyles = data[prop];
                foundStyles = true;
                break;
              } 
              // Check if it's a nested object with paths
              else if (typeof data[prop] === 'object' && data[prop].paths && Array.isArray(data[prop].paths)) {
                console.log(\`Found nested paths in '\${prop}.paths' property\`);
                this.allStyles = data[prop].paths;
                foundStyles = true;
                break;
              }
            }
          }
          
          // If still not found, look for any array property that has rune-like objects
          if (!foundStyles) {
            const possibleArrayProps = Object.keys(data).filter(key => 
              Array.isArray(data[key]) && data[key].length > 0 &&
              data[key][0] && typeof data[key][0] === 'object' &&
              (data[key][0].slots || data[key][0].name || data[key][0].key || data[key][0].id)
            );
            
            if (possibleArrayProps.length > 0) {
              console.log(\`Using array from '\${possibleArrayProps[0]}' property\`);
              this.allStyles = data[possibleArrayProps[0]];
              foundStyles = true;
            }
          }
          
          // Last resort: if the data itself looks like a style object with slots
          if (!foundStyles && data.slots && Array.isArray(data.slots)) {
            console.log('Data itself appears to be a single path, wrapping in array');
            this.allStyles = [data];
            foundStyles = true;
          }
          
          // If we still can't find valid styles, use local data
          if (!foundStyles) {
            console.warn('Could not find valid styles in API response, using local data');
            this.allStyles = this._getLocalRuneData();
          }
        } 
        // If API data is not valid, use local data as fallback
        else {
          console.warn('API data format unexpected, using local data');
          this.allStyles = this._getLocalRuneData();
        }
      } catch (error) {
        // If API request fails, use local data
        console.warn('API request failed, using local rune data:', error);
        this.allStyles = this._getLocalRuneData();
      }
      
      // Hide loading state
      this.loadingElement.style.display = 'none';
      
      // Log final data structure for debugging
      console.log('Final allStyles structure:', 
        Array.isArray(this.allStyles) ? 
        \`Array with \${this.allStyles.length} items\` : 
        typeof this.allStyles);
      
      if (!Array.isArray(this.allStyles)) {
        console.error('allStyles is still not an array, using local data as fallback');
        this.allStyles = this._getLocalRuneData();
      }
      
      // Save to cache - save the complete response if available
      await window.LOLUtils.cacheRunes(this.runeData || this.allStyles);
      
      // Process and display runes
      this.processRunes();
    } catch (error) {
      console.error('Error fetching runes:', error);
      
      // Hide loading state and show error
      this.loadingElement.style.display = 'none';
      this.errorElement.style.display = 'block';
      this.errorElement.textContent = \`Error loading runes: \${error.message}\`;
    }
  }
`;

const updatedFetchWithLocalAssets = `
  // Function to fetch runes data with caching
  async fetchRunes() {
    try {
      // Show loading state
      this.loadingElement.style.display = 'block';
      this.errorElement.style.display = 'none';
      this.noResultsElement.style.display = 'none';
      
      // Check if we have cached runes data
      const runes = await window.LOLUtils.getCachedRunes();
      
      if (runes) {
        // Use cached data
        console.log('Using cached runes data');
        this.runeData = runes; // Store the complete response
        this.allStyles = Array.isArray(runes.paths) ? runes.paths : runes; // Extract paths array if available
        this.processRunes();
        return;
      }
      
      // No cache or expired cache, fetch from API
      console.log('Fetching runes from API');
      try {
        const response = await fetch(\`\${this.API_BASE_URL}/runes\`);
        
        if (!response.ok) {
          throw new Error(\`API request failed with status \${response.status}\`);
        }
        
        const data = await response.json();
        this.runeData = data; // Store the complete response
        
        console.log('API response received:', typeof data);
        console.log('Has paths property:', data && data.paths ? 'yes' : 'no');
        
        // Log the API response structure for debugging
        console.log('API response structure:', {
          isArray: Array.isArray(data),
          hasPathsProperty: data && data.paths ? true : false,
          topLevelKeys: data ? Object.keys(data) : []
        });
        
        // Handle the RuneTreeResponse format from backend
        if (data && data.paths && Array.isArray(data.paths)) {
          console.log(\`API returned proper format with \${data.paths.length} paths\`);
          this.allStyles = data.paths;
        } 
        // Handle case where API returns an array directly
        else if (data && Array.isArray(data)) {
          console.log('API returned direct array of styles');
          this.allStyles = data;
        }
        // Handle object response with non-standard structure 
        else if (data && typeof data === 'object') {
          // Try all possible property names that might contain rune paths
          const possibleStylesProperties = ['paths', 'styles', 'runePaths', 'runes', 'data'];
          
          let foundStyles = false;
          
          // Check for known property names that might contain the paths
          for (const prop of possibleStylesProperties) {
            if (data[prop]) {
              if (Array.isArray(data[prop]) && data[prop].length > 0) {
                console.log(\`Found paths in '\${prop}' property\`);
                this.allStyles = data[prop];
                foundStyles = true;
                break;
              } 
              // Check if it's a nested object with paths
              else if (typeof data[prop] === 'object' && data[prop].paths && Array.isArray(data[prop].paths)) {
                console.log(\`Found nested paths in '\${prop}.paths' property\`);
                this.allStyles = data[prop].paths;
                foundStyles = true;
                break;
              }
            }
          }
          
          // If still not found, look for any array property that has rune-like objects
          if (!foundStyles) {
            const possibleArrayProps = Object.keys(data).filter(key => 
              Array.isArray(data[key]) && data[key].length > 0 &&
              data[key][0] && typeof data[key][0] === 'object' &&
              (data[key][0].slots || data[key][0].name || data[key][0].key || data[key][0].id)
            );
            
            if (possibleArrayProps.length > 0) {
              console.log(\`Using array from '\${possibleArrayProps[0]}' property\`);
              this.allStyles = data[possibleArrayProps[0]];
              foundStyles = true;
            }
          }
          
          // Last resort: if the data itself looks like a style object with slots
          if (!foundStyles && data.slots && Array.isArray(data.slots)) {
            console.log('Data itself appears to be a single path, wrapping in array');
            this.allStyles = [data];
            foundStyles = true;
          }
          
          // If we still can't find valid styles, use local data
          if (!foundStyles) {
            console.warn('Could not find valid styles in API response, using local data');
            this.allStyles = this._getLocalRuneData();
          }
        } 
        // If API data is not valid, use local data as fallback
        else {
          console.warn('API data format unexpected, using local data');
          this.allStyles = this._getLocalRuneData();
        }
      } catch (error) {
        // If API request fails, use local data
        console.warn('API request failed, using local rune data:', error);
        this.allStyles = this._getLocalRuneData();
      }
      
      // Hide loading state
      this.loadingElement.style.display = 'none';
      
      // Log final data structure for debugging
      console.log('Final allStyles structure:', 
        Array.isArray(this.allStyles) ? 
        \`Array with \${this.allStyles.length} items\` : 
        typeof this.allStyles);
      
      if (!Array.isArray(this.allStyles)) {
        console.error('allStyles is still not an array, using local data as fallback');
        this.allStyles = this._getLocalRuneData();
      }
      
      // Save to cache - save the complete response if available
      await window.LOLUtils.cacheRunes(this.runeData || this.allStyles);
      
      // Process and display runes
      this.processRunes();
    } catch (error) {
      console.error('Error fetching runes:', error);
      
      // Hide loading state and show error
      this.loadingElement.style.display = 'none';
      this.errorElement.style.display = 'block';
      this.errorElement.textContent = \`Error loading runes: \${error.message}\`;
    }
  }
`;

const originalImageFunction = `
  // Use the backend's assets endpoint for rune images
  // There's no specific style endpoint, so we use the rune image endpoint
  const styleIconUrl = \`\${this.API_BASE_URL}/assets/rune/image/\${style.id}\`;
  imgElement.src = styleIconUrl;
`;

const updatedImageFunction = `
  // Use local assets for rune images
  const styleIconUrl = \`assets/runes/\${style.id}.png\`;
  imgElement.src = styleIconUrl;
`;

const originalRuneImageUrl = `
  // Use the backend's assets endpoint with correct path
  const runeIconUrl = \`\${this.API_BASE_URL}/assets/rune/image/\${rune.id}\`;
  imgElement.src = runeIconUrl;
`;

const updatedRuneImageUrl = `
  // Use local assets for rune images
  const runeIconUrl = \`assets/runes/\${rune.id}.png\`;
  imgElement.src = runeIconUrl;
`;

const originalStyleIconUrl = `
  // Use the backend's assets endpoint with correct path
  const styleIconUrl = \`\${this.API_BASE_URL}/assets/rune/image/\${rune.styleId}\`;
  styleImgElement.src = styleIconUrl;
`;

const updatedStyleIconUrl = `
  // Use local assets for rune images
  const styleIconUrl = \`assets/runes/\${rune.styleId}.png\`;
  styleImgElement.src = styleIconUrl;
`;

const originalSimilarRuneIconUrl = `
  // Use the backend's assets endpoint with correct path
  const runeIconUrl = \`\${this.API_BASE_URL}/assets/rune/image/\${similarRune.id}\`;
  imgElement.src = runeIconUrl;
`;

const updatedSimilarRuneIconUrl = `
  // Use local assets for rune images
  const runeIconUrl = \`assets/runes/\${similarRune.id}.png\`;
  imgElement.src = runeIconUrl;
`;

// Read the original file, make the replacements, and write the updated file
const fs = require('fs');
const path = '/home/rod/Projects/lol-ext/extension/runes.js';

fs.readFile(path, 'utf8', (err, data) => {
  if (err) {
    console.error('Error reading the file:', err);
    return;
  }

  // Replace all occurrences
  let updatedData = data.replace(originalStyleIconUrl, updatedImageFunction);
  updatedData = updatedData.replace(originalRuneImageUrl, updatedRuneImageUrl);
  updatedData = updatedData.replace(originalStyleIconUrl, updatedStyleIconUrl);
  updatedData = updatedData.replace(originalSimilarRuneIconUrl, updatedSimilarRuneIconUrl);

  // Write the updated content back to the file
  fs.writeFile(path, updatedData, 'utf8', (err) => {
    if (err) {
      console.error('Error writing to the file:', err);
      return;
    }
    console.log('Successfully updated runes.js to use local assets!');
  });
});