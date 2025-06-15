// Test script for the Items API
async function testItemsAPI() {
  const API_BASE_URL = 'http://localhost:8001/api/v1';
  const itemsUrl = `${API_BASE_URL}/items`;
  
  console.log('Testing Items API...');
  console.log('Items URL:', itemsUrl);
  
  try {
    // Fetch from API
    console.log('Fetching items from API');
    const response = await fetch(itemsUrl);
    
    // Log response status
    console.log('API response status:', response.status);
    
    if (!response.ok) {
      throw new Error(`API request failed with status ${response.status}`);
    }
    
    // Log the raw response for debugging
    const responseText = await response.text();
    console.log('Raw API response (first 500 chars):', responseText.substring(0, 500) + '...');
    
    // Parse the response as JSON
    const data = JSON.parse(responseText);
    
    // Log the structure of the response
    console.log('API response structure:', Object.keys(data));
    
    // Check if data has the expected structure
    if (data && data.tiers) {
      console.log('Found tiers in response:', data.tiers.length);
      
      // Log tier details
      data.tiers.forEach(tier => {
        console.log(`Tier ${tier.tier}: ${tier.items ? tier.items.length : 0} items`);
        
        // Log a sample item from each tier
        if (tier.items && tier.items.length > 0) {
          console.log('Sample item from tier:', tier.items[0]);
        }
      });
      
      // Total items count
      const totalItems = data.tiers.reduce((count, tier) => {
        return count + (tier.items ? tier.items.length : 0);
      }, 0);
      
      console.log(`Total items count: ${totalItems}`);
      
      return {
        success: true,
        tiersCount: data.tiers.length,
        totalItems: totalItems
      };
    } else {
      console.error('Invalid data format from API - missing tiers');
      return {
        success: false,
        error: 'Invalid data format - missing tiers'
      };
    }
  } catch (error) {
    console.error('Error fetching items:', error);
    return {
      success: false,
      error: error.message
    };
  }
}

// Run the test
testItemsAPI().then(result => {
  console.log('Test result:', result);
});