/**
 * Options Page Script for ExplainWithAi Extension
 * Handles settings management and API testing
 */

// DOM Elements
const apiKeyInput = document.getElementById('apiKey');
const toggleKeyBtn = document.getElementById('toggleKey');
const modelSelect = document.getElementById('model');
const presetSelect = document.getElementById('preset');
const safetyLevelSelect = document.getElementById('safetyLevel');
const testBtn = document.getElementById('testBtn');
const testSpinner = document.getElementById('testSpinner');
const testResult = document.getElementById('testResult');
const saveBtn = document.getElementById('saveBtn');
const resetBtn = document.getElementById('resetBtn');
const status = document.getElementById('status');

// Default settings
const DEFAULT_SETTINGS = {
  geminiApiKey: '',
  model: 'gemini-2.5-flash',
  preset: 'Plain',
  safetyLevel: 'BLOCK_MEDIUM_AND_ABOVE'
};

// State
let isApiKeyVisible = false;
let isTesting = false;
let settings = { ...DEFAULT_SETTINGS };

/**
 * Initialize options page
 */
async function initialize() {
  await loadSettings();
  setupEventListeners();
  updateUI();
}

/**
 * Load settings from storage
 */
async function loadSettings() {
  try {
    const result = await chrome.storage.sync.get(DEFAULT_SETTINGS);
    settings = { ...DEFAULT_SETTINGS, ...result };
  } catch (error) {
    console.error('Error loading settings:', error);
    showStatus('Error loading settings', 'error');
  }
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
  // API Key visibility toggle
  toggleKeyBtn.addEventListener('click', toggleApiKeyVisibility);
  
  // Form changes
  apiKeyInput.addEventListener('input', handleFormChange);
  modelSelect.addEventListener('change', handleFormChange);
  presetSelect.addEventListener('change', handleFormChange);
  safetyLevelSelect.addEventListener('change', handleFormChange);
  
  // Buttons
  testBtn.addEventListener('click', handleTestApi);
  saveBtn.addEventListener('click', handleSave);
  resetBtn.addEventListener('click', handleReset);
  
  // Keyboard shortcuts
  document.addEventListener('keydown', (e) => {
    if (e.ctrlKey || e.metaKey) {
      if (e.key === 's') {
        e.preventDefault();
        handleSave();
      }
    }
  });
}

/**
 * Update UI with current settings
 */
function updateUI() {
  apiKeyInput.value = settings.geminiApiKey;
  modelSelect.value = settings.model;
  presetSelect.value = settings.preset;
  safetyLevelSelect.value = settings.safetyLevel;
  
  updateSaveButtonState();
}

/**
 * Toggle API key visibility
 */
function toggleApiKeyVisibility() {
  isApiKeyVisible = !isApiKeyVisible;
  apiKeyInput.type = isApiKeyVisible ? 'text' : 'password';
  toggleKeyBtn.textContent = isApiKeyVisible ? '🙈' : '👁️';
  toggleKeyBtn.title = isApiKeyVisible ? 'Hide API Key' : 'Show API Key';
}

/**
 * Handle form field changes
 */
function handleFormChange() {
  updateSaveButtonState();
  hideStatus();
}

/**
 * Update save button state
 */
function updateSaveButtonState() {
  const hasChanges = (
    apiKeyInput.value !== settings.geminiApiKey ||
    modelSelect.value !== settings.model ||
    presetSelect.value !== settings.preset ||
    safetyLevelSelect.value !== settings.safetyLevel
  );
  
  saveBtn.disabled = !hasChanges;
}

/**
 * Handle API test
 */
async function handleTestApi() {
  if (isTesting) return;
  
  const apiKey = apiKeyInput.value.trim();
  const model = modelSelect.value;
  
  if (!apiKey) {
    showTestResult('Please enter an API key first', 'error');
    return;
  }
  
  try {
    setTestingState(true);
    hideTestResult();
    
    const response = await chrome.runtime.sendMessage({
      type: 'TEST_API',
      apiKey: apiKey,
      model: model
    });
    
    if (response.success) {
      const usageText = response.usage ? 
        ` (${response.usage.totalTokens || 'N/A'} tokens used)` : '';
      showTestResult(`✅ API connection successful${usageText}`, 'success');
    } else {
      const errorMsg = response.error || 'Unknown error';
      const hint = response.hint ? `\n💡 ${response.hint}` : '';
      showTestResult(`❌ ${errorMsg}${hint}`, 'error');
    }
    
  } catch (error) {
    console.error('Error testing API:', error);
    showTestResult('❌ Failed to test API connection', 'error');
  } finally {
    setTestingState(false);
  }
}

/**
 * Handle save settings
 */
async function handleSave() {
  try {
    const newSettings = {
      geminiApiKey: apiKeyInput.value.trim(),
      model: modelSelect.value,
      preset: presetSelect.value,
      safetyLevel: safetyLevelSelect.value
    };
    
    // Validate settings
    if (!newSettings.geminiApiKey) {
      showStatus('API key is required', 'error');
      apiKeyInput.focus();
      return;
    }
    
    if (!newSettings.model) {
      showStatus('Model selection is required', 'error');
      modelSelect.focus();
      return;
    }
    
    // Save to storage
    await chrome.storage.sync.set(newSettings);
    settings = { ...newSettings };
    
    updateSaveButtonState();
    showStatus('Settings saved successfully', 'success');
    
    // Auto-hide success message
    setTimeout(hideStatus, 3000);
    
  } catch (error) {
    console.error('Error saving settings:', error);
    showStatus('Failed to save settings', 'error');
  }
}

/**
 * Handle reset to defaults
 */
async function handleReset() {
  if (!confirm('Reset all settings to default values?')) {
    return;
  }
  
  try {
    await chrome.storage.sync.clear();
    settings = { ...DEFAULT_SETTINGS };
    updateUI();
    showStatus('Settings reset to defaults', 'success');
    
    setTimeout(hideStatus, 3000);
    
  } catch (error) {
    console.error('Error resetting settings:', error);
    showStatus('Failed to reset settings', 'error');
  }
}

/**
 * Set testing state
 */
function setTestingState(testing) {
  isTesting = testing;
  testBtn.disabled = testing;
  
  if (testing) {
    testBtn.classList.add('loading');
  } else {
    testBtn.classList.remove('loading');
  }
}

/**
 * Show test result
 */
function showTestResult(message, type) {
  testResult.textContent = message;
  testResult.className = `test-result ${type}`;
}

/**
 * Hide test result
 */
function hideTestResult() {
  testResult.className = 'test-result';
}

/**
 * Show status message
 */
function showStatus(message, type) {
  status.textContent = message;
  status.className = `status ${type}`;
}

/**
 * Hide status message
 */
function hideStatus() {
  status.className = 'status';
}

/**
 * Validate API key format (basic check)
 */
function isValidApiKeyFormat(key) {
  // Basic validation - Gemini API keys typically start with certain patterns
  return key.length > 20 && /^[A-Za-z0-9_-]+$/.test(key);
}

/**
 * Auto-validate API key on input
 */
function setupApiKeyValidation() {
  let validationTimeout;
  
  apiKeyInput.addEventListener('input', () => {
    clearTimeout(validationTimeout);
    
    validationTimeout = setTimeout(() => {
      const key = apiKeyInput.value.trim();
      
      if (key && !isValidApiKeyFormat(key)) {
        apiKeyInput.style.borderColor = '#ea4335';
      } else {
        apiKeyInput.style.borderColor = '';
      }
    }, 500);
  });
}

/**
 * Enhanced initialization
 */
async function enhancedInitialize() {
  await initialize();
  setupApiKeyValidation();
  
  // Focus API key field if empty
  if (!settings.geminiApiKey) {
    apiKeyInput.focus();
  }
  
  // Show helpful tip if no API key is set
  if (!settings.geminiApiKey) {
    setTimeout(() => {
      showStatus('👋 Welcome! Please enter your Gemini API key to get started', 'success');
    }, 1000);
  }
}

// Initialize when DOM is loaded
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', enhancedInitialize);
} else {
  enhancedInitialize();
}
