// Script to test Data Dragon CDN URLs for rune images

document.addEventListener('DOMContentLoaded', async function() {
  console.log('Testing rune image loading from Data Dragon CDN...');
  
  // Container for test results
  const resultsContainer = document.createElement('div');
  resultsContainer.id = 'test-results';
  resultsContainer.style.padding = '20px';
  resultsContainer.style.fontFamily = 'monospace';
  resultsContainer.innerHTML = '<h2>Rune Image Test Results</h2>';
  document.body.appendChild(resultsContainer);
  
  // Create status display
  const statusDisplay = document.createElement('div');
  statusDisplay.id = 'test-status';
  statusDisplay.style.marginBottom = '20px';
  statusDisplay.style.fontWeight = 'bold';
  statusDisplay.textContent = 'Loading rune data...';
  resultsContainer.appendChild(statusDisplay);
  
  // Create results table
  const resultsTable = document.createElement('table');
  resultsTable.style.width = '100%';
  resultsTable.style.borderCollapse = 'collapse';
  resultsTable.innerHTML = `
    <thead>
      <tr>
        <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Rune Name</th>
        <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Icon Path</th>
        <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Status</th>
        <th style="border: 1px solid #ddd; padding: 8px; text-align: left;">Preview</th>
      </tr>
    </thead>
    <tbody id="results-body"></tbody>
  `;
  resultsContainer.appendChild(resultsTable);
  
  // Function to test image loading
  async function testImageLoad(url) {
    return new Promise((resolve) => {
      const img = new Image();
      img.onload = () => resolve({ success: true, img });
      img.onerror = () => resolve({ success: false });
      img.src = url;
    });
  }
  
  try {
    // Fetch rune data from API
    statusDisplay.textContent = 'Fetching rune data from API...';
    const response = await fetch('http://localhost:8001/runes');
    
    if (!response.ok) {
      throw new Error(`API request failed with status ${response.status}`);
    }
    
    const data = await response.json();
    statusDisplay.textContent = 'Processing rune data...';
    
    // Process the data to extract paths and runes
    let allStyles = [];
    
    if (data && data.paths && Array.isArray(data.paths)) {
      allStyles = data.paths;
    } else if (data && Array.isArray(data)) {
      allStyles = data;
    } else {
      throw new Error('Invalid data format');
    }
    
    // Test styles first
    statusDisplay.textContent = 'Testing style path images...';
    const resultsBody = document.getElementById('results-body');
    
    for (const style of allStyles) {
      // Test style icon
      if (style && style.icon) {
        const row = document.createElement('tr');
        
        // Format CDN URL
        const cdnUrl = `https://ddragon.leagueoflegends.com/cdn/img/${style.icon}`;
        
        // Test image loading
        const loadResult = await testImageLoad(cdnUrl);
        
        // Create row with results
        row.innerHTML = `
          <td style="border: 1px solid #ddd; padding: 8px;">${style.name} (Style)</td>
          <td style="border: 1px solid #ddd; padding: 8px; font-size: 12px;">${style.icon}</td>
          <td style="border: 1px solid #ddd; padding: 8px; color: ${loadResult.success ? 'green' : 'red'}">
            ${loadResult.success ? '✓ Success' : '✗ Failed'}
          </td>
          <td style="border: 1px solid #ddd; padding: 8px;">
            ${loadResult.success ? 
              `<img src="${cdnUrl}" alt="${style.name}" style="width: 40px; height: 40px;">` : 
              `<div style="width: 40px; height: 40px; background-color: #ccc; display: flex; align-items: center; justify-content: center;">${style.name.charAt(0)}</div>`
            }
          </td>
        `;
        
        resultsBody.appendChild(row);
      }
      
      // Test individual runes in each style
      if (style.slots && Array.isArray(style.slots)) {
        for (const slot of style.slots) {
          if (slot.runes && Array.isArray(slot.runes)) {
            for (const rune of slot.runes) {
              if (rune && rune.icon) {
                const row = document.createElement('tr');
                
                // Format CDN URL
                const cdnUrl = `https://ddragon.leagueoflegends.com/cdn/img/${rune.icon}`;
                
                // Test image loading
                const loadResult = await testImageLoad(cdnUrl);
                
                // Create row with results
                row.innerHTML = `
                  <td style="border: 1px solid #ddd; padding: 8px;">${rune.name}</td>
                  <td style="border: 1px solid #ddd; padding: 8px; font-size: 12px;">${rune.icon}</td>
                  <td style="border: 1px solid #ddd; padding: 8px; color: ${loadResult.success ? 'green' : 'red'}">
                    ${loadResult.success ? '✓ Success' : '✗ Failed'}
                  </td>
                  <td style="border: 1px solid #ddd; padding: 8px;">
                    ${loadResult.success ? 
                      `<img src="${cdnUrl}" alt="${rune.name}" style="width: 40px; height: 40px;">` : 
                      `<div style="width: 40px; height: 40px; background-color: #ccc; display: flex; align-items: center; justify-content: center;">${rune.name.charAt(0)}</div>`
                    }
                  </td>
                `;
                
                resultsBody.appendChild(row);
              }
            }
          }
        }
      }
    }
    
    // Update status when complete
    statusDisplay.textContent = 'Testing complete!';
    
  } catch (error) {
    console.error('Test failed:', error);
    statusDisplay.textContent = `Error: ${error.message}`;
    statusDisplay.style.color = 'red';
  }
});