// Background service worker
// This script runs in the background and can handle events even when the popup is closed

// Listen for installation
chrome.runtime.onInstalled.addListener(function() {
  console.log('League of Legends Helper extension installed');
  
  // Initialize storage with default settings if needed
  chrome.storage.local.get(['apiEndpoint'], function(result) {
    if (!result.apiEndpoint) {
      chrome.storage.local.set({
        apiEndpoint: 'http://localhost:8001/api/v1'
      });
    }
  });
});

// Listen for messages from popup or content scripts
chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
  if (request.action === 'ping') {
    sendResponse({status: 'pong', message: 'Background service worker is running'});
  }
  
  // Keep the message channel open for async responses
  return true;
});