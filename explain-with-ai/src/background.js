/**
 * Background Service Worker for ExplainWithAi Extension
 * Handles context menus, keyboard commands, rate limiting, and API calls
 */

import { callGemini, GeminiError } from '../utils/gemini.js';

// Rate limiting: minimum 2 seconds between requests
let lastRequestTime = 0;
const RATE_LIMIT_MS = 2000;

// Default settings
const DEFAULT_SETTINGS = {
  geminiApiKey: '',
  model: 'gemini-2.5-flash',
  preset: 'Plain',
  safetyLevel: 'BLOCK_MEDIUM_AND_ABOVE'
};

// Presets for prompts
const PRESETS = {
  'ELI5': 'Explain like I\'m 5, with a friendly tone and simple examples:\n\n',
  'Key points': 'Summarize into 3–5 bullet points anyone can understand:\n\n', 
  'Plain': 'Explain simply and clearly:\n\n'
};

/**
 * Initialize extension on installation/startup
 */
chrome.runtime.onInstalled.addListener(async () => {
  console.log('ExplainWithAi extension installed');
  
  // Create context menu
  chrome.contextMenus.create({
    id: 'explain-with-ai',
    title: 'Explain with AI',
    contexts: ['selection']
  });

  // Initialize default settings if not present
  const settings = await readSettings();
  if (!settings.model) {
    await chrome.storage.sync.set(DEFAULT_SETTINGS);
  }
});

/**
 * Handle context menu clicks
 */
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId === 'explain-with-ai') {
    const selectedText = info.selectionText;
    if (selectedText) {
      // Store the selected text for the popup to use
      await chrome.storage.local.set({ 
        pendingExplanation: selectedText,
        autoExplain: true 
      });
      
      // Open the popup by triggering the action
      try {
        await chrome.action.openPopup();
      } catch (error) {
        // Fallback: open popup in a new window if openPopup is not available
        const popup = await chrome.windows.create({
          url: chrome.runtime.getURL('src/popup.html'),
          type: 'popup',
          width: 520,
          height: 680,
          focused: true
        });
        
        // Store popup window ID to communicate with it
        await chrome.storage.local.set({ popupWindowId: popup.id });
      }
    }
  }
});

/**
 * Handle keyboard commands
 */
chrome.commands.onCommand.addListener(async (command, tab) => {
  if (command === 'explain-selection') {
    try {
      const selectedText = await getSelectionFromActiveTab(tab);
      if (selectedText) {
        // Store the selected text for the popup to use
        await chrome.storage.local.set({ 
          pendingExplanation: selectedText,
          autoExplain: true 
        });
        
        // Open the popup
        try {
          await chrome.action.openPopup();
        } catch (error) {
          // Fallback: open popup in a new window
          const popup = await chrome.windows.create({
            url: chrome.runtime.getURL('src/popup.html'),
            type: 'popup',
            width: 520,
            height: 680,
            focused: true
          });
          
          await chrome.storage.local.set({ popupWindowId: popup.id });
        }
      } else {
        // Open popup anyway for manual text entry
        try {
          await chrome.action.openPopup();
        } catch (error) {
          const popup = await chrome.windows.create({
            url: chrome.runtime.getURL('src/popup.html'),
            type: 'popup',
            width: 520,
            height: 680,
            focused: true
          });
          
          await chrome.storage.local.set({ popupWindowId: popup.id });
        }
      }
    } catch (error) {
      console.error('Error getting selection:', error);
      showErrorNotification('Failed to get selected text');
    }
  }
});

/**
 * Handle messages from popup and content scripts
 */
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  switch (message.type) {
    case 'EXPLAIN_TEXT':
      handleExplainMessage(message, sendResponse);
      return true; // Keep message channel open for async response
      
    case 'GET_SELECTION':
      handleGetSelection(sender.tab, sendResponse);
      return true;
      
    case 'TEST_API':
      handleTestApi(message, sendResponse);
      return true;
      
    default:
      sendResponse({ error: 'Unknown message type' });
  }
});

/**
 * Handle explain request from context menu or keyboard shortcut
 */
async function handleExplainRequest(text, tab) {
  try {
    // Check rate limit
    if (!checkRateLimit()) {
      showErrorNotification('Please wait before making another request');
      return;
    }

    const settings = await readSettings();
    
    if (!settings.geminiApiKey) {
      showErrorNotification('API key not set. Please configure in extension options.');
      return;
    }

    const prompt = buildPrompt(settings.preset, text);
    const result = await callGemini({
      apiKey: settings.geminiApiKey,
      model: settings.model,
      prompt: prompt,
      safetyLevel: settings.safetyLevel
    });

    // Check if popup is open - if so, send result there
    try {
      await chrome.runtime.sendMessage({
        type: 'EXPLANATION_RESULT',
        result: result,
        originalText: text
      });
    } catch (error) {
      // Popup not open, show notification instead
      showResultNotification(result.text);
    }

  } catch (error) {
    console.error('Error explaining text:', error);
    
    let errorMessage = 'Failed to explain text';
    let hint = 'Check extension options';
    
    if (error instanceof GeminiError) {
      errorMessage = error.message;
      hint = error.hint;
    }
    
    // Try to send to popup first
    try {
      await chrome.runtime.sendMessage({
        type: 'EXPLANATION_ERROR',
        error: { message: errorMessage, hint: hint, code: error.code }
      });
    } catch (popupError) {
      // Popup not open, show notification
      showErrorNotification(`${errorMessage}. ${hint}`);
    }
  }
}

/**
 * Handle explain message from popup
 */
async function handleExplainMessage(message, sendResponse) {
  try {
    // Check rate limit
    if (!checkRateLimit()) {
      sendResponse({ 
        error: { 
          message: 'Rate limited', 
          hint: 'Please wait 2 seconds between requests',
          code: 'RATE_LIMITED'
        } 
      });
      return;
    }

    const settings = await readSettings();
    
    if (!settings.geminiApiKey) {
      sendResponse({ 
        error: { 
          message: 'API key not configured', 
          hint: 'Please set your Gemini API key in the extension options',
          code: 'INVALID_API_KEY'
        } 
      });
      return;
    }

    const { text, preset, model, safetyLevel } = message;
    const prompt = buildPrompt(preset || settings.preset, text);
    
    const result = await callGemini({
      apiKey: settings.geminiApiKey,
      model: model || settings.model,
      prompt: prompt,
      safetyLevel: safetyLevel || settings.safetyLevel
    });

    sendResponse({ result });

  } catch (error) {
    console.error('Error in handleExplainMessage:', error);
    
    let errorResponse = { 
      message: 'Unknown error occurred',
      hint: 'Check extension options and try again',
      code: 'UNKNOWN_ERROR'
    };
    
    if (error instanceof GeminiError) {
      errorResponse = {
        message: error.message,
        hint: error.hint,
        code: error.code
      };
    }
    
    sendResponse({ error: errorResponse });
  }
}

/**
 * Handle get selection message
 */
async function handleGetSelection(tab, sendResponse) {
  try {
    const selection = await getSelectionFromActiveTab(tab);
    sendResponse({ selection });
  } catch (error) {
    console.error('Error getting selection:', error);
    sendResponse({ selection: '' });
  }
}

/**
 * Handle API test message
 */
async function handleTestApi(message, sendResponse) {
  try {
    const { apiKey, model } = message;
    
    // Simple test prompt
    const testPrompt = 'Test';
    
    const result = await callGemini({
      apiKey: apiKey,
      model: model || 'gemini-2.5-flash',
      prompt: testPrompt,
      maxOutputTokens: 10,
      safetyLevel: 'BLOCK_MEDIUM_AND_ABOVE'
    });

    sendResponse({ success: true, usage: result.usage });

  } catch (error) {
    console.error('API test failed:', error);
    
    let errorResponse = {
      success: false,
      error: 'API test failed',
      hint: 'Check your API key and model settings'
    };
    
    if (error instanceof GeminiError) {
      errorResponse.error = error.message;
      errorResponse.hint = error.hint;
      errorResponse.code = error.code;
    }
    
    sendResponse(errorResponse);
  }
}

/**
 * Get selected text from active tab
 */
async function getSelectionFromActiveTab(tab) {
  try {
    const results = await chrome.scripting.executeScript({
      target: { tabId: tab?.id || (await getCurrentTab()).id },
      func: () => window.getSelection()?.toString() || ''
    });
    
    return results[0]?.result || '';
  } catch (error) {
    console.error('Error executing script:', error);
    return '';
  }
}

/**
 * Get current active tab
 */
async function getCurrentTab() {
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  return tabs[0];
}

/**
 * Read settings from storage
 */
async function readSettings() {
  try {
    const result = await chrome.storage.sync.get(DEFAULT_SETTINGS);
    return { ...DEFAULT_SETTINGS, ...result };
  } catch (error) {
    console.error('Error reading settings:', error);
    return DEFAULT_SETTINGS;
  }
}

/**
 * Build prompt with preset prefix
 */
function buildPrompt(preset, text) {
  // Truncate text if too long
  const maxLength = 8000;
  let processedText = text;
  let truncatedNote = '';
  
  if (text.length > maxLength) {
    processedText = text.substring(0, maxLength);
    truncatedNote = `\n\n[Note: Text truncated from ${text.length} to ${maxLength} characters for processing]`;
  }
  
  const prefix = PRESETS[preset] || PRESETS['Plain'];
  return prefix + processedText + truncatedNote;
}

/**
 * Check rate limit
 */
function checkRateLimit() {
  const now = Date.now();
  if (now - lastRequestTime < RATE_LIMIT_MS) {
    return false;
  }
  lastRequestTime = now;
  return true;
}

/**
 * Show result notification
 */
function showResultNotification(text) {
  const previewText = text.length > 200 ? text.substring(0, 200) + '...' : text;
  
  chrome.notifications.create({
    type: 'basic',
    iconUrl: 'assets/icon48.png',
    title: 'Explanation ready',
    message: previewText,
    buttons: [{ title: 'Copy' }]
  });
}

/**
 * Show error notification
 */
function showErrorNotification(message) {
        chrome.notifications.create({
          type: 'basic',
          iconUrl: 'assets/icon48.png',
          title: 'ExplainWithAi Error',
          message: message
        });
}

/**
 * Handle notification button clicks
 */
chrome.notifications.onButtonClicked.addListener(async (notificationId, buttonIndex) => {
  if (buttonIndex === 0) { // Copy button
    // Copy the full explanation text to clipboard
    // This would need the full text stored somewhere, for now just clear the notification
    chrome.notifications.clear(notificationId);
  }
});

/**
 * Clear notification when clicked
 */
chrome.notifications.onClicked.addListener((notificationId) => {
  chrome.notifications.clear(notificationId);
});
