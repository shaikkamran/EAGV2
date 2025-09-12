/**
 * Setup script to configure the extension with the API key
 * Run this in the Chrome DevTools console on any page after loading the extension
 */

// Set the API key and default settings
const settings = {
  geminiApiKey: 'AIzaSyA6rrurtkWUemALCySiotDSwI61EAKyTK4',
  model: 'gemini-2.5-flash',
  preset: 'Plain',
  safetyLevel: 'BLOCK_MEDIUM_AND_ABOVE'
};

chrome.storage.sync.set(settings).then(() => {
  console.log('✅ Extension configured with API key and default settings');
  console.log('Settings:', settings);
}).catch(error => {
  console.error('❌ Error setting up extension:', error);
});
