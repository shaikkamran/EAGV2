/**
 * Popup Script for ExplainWithAi Extension
 * Handles UI interactions and communication with background script
 */

// DOM Elements
const textInput = document.getElementById('textInput');
const charCount = document.getElementById('charCount');
const presetSelect = document.getElementById('presetSelect');
const modelSelect = document.getElementById('modelSelect');
const safetySelect = document.getElementById('safetySelect');
const explainBtn = document.getElementById('explainBtn');
const spinner = document.getElementById('spinner');
const errorSection = document.getElementById('errorSection');
const errorMessage = document.getElementById('errorMessage');
const errorHint = document.getElementById('errorHint');
const outputSection = document.getElementById('outputSection');
const outputText = document.getElementById('outputText');
const usageInfo = document.getElementById('usageInfo');
const copyBtn = document.getElementById('copyBtn');
const rerunBtn = document.getElementById('rerunBtn');

// State
let currentExplanation = '';
let isLoading = false;

// Constants
const MAX_CHARS = 8000;

/**
 * Initialize popup
 */
async function initialize() {
  await loadSettings();
  await loadCurrentSelection();
  setupEventListeners();
  updateCharCount();
}

/**
 * Load user settings
 */
async function loadSettings() {
  try {
    const settings = await chrome.storage.sync.get({
      model: 'gemini-2.5-flash',
      preset: 'Plain',
      safetyLevel: 'BLOCK_MEDIUM_AND_ABOVE'
    });
    
    presetSelect.value = settings.preset;
    modelSelect.value = settings.model;
    safetySelect.value = settings.safetyLevel;
  } catch (error) {
    console.error('Error loading settings:', error);
  }
}

/**
 * Load current page selection or pending explanation
 */
async function loadCurrentSelection() {
  try {
    // First check for pending explanation from context menu/keyboard shortcut
    const local = await chrome.storage.local.get(['pendingExplanation', 'autoExplain']);
    
    if (local.pendingExplanation) {
      textInput.value = local.pendingExplanation;
      updateCharCount();
      
      // Clear the pending explanation
      await chrome.storage.local.remove(['pendingExplanation']);
      
      // Auto-explain if requested
      if (local.autoExplain) {
        await chrome.storage.local.remove(['autoExplain']);
        setTimeout(() => {
          if (textInput.value.trim()) {
            handleExplain();
          }
        }, 500); // Small delay to let UI render
      }
      
      return;
    }
    
    // Fallback to getting current selection
    const response = await chrome.runtime.sendMessage({ type: 'GET_SELECTION' });
    if (response?.selection) {
      textInput.value = response.selection;
      updateCharCount();
    }
  } catch (error) {
    console.error('Error loading selection:', error);
    // Ignore errors - user can still manually input text
  }
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
  // Text input events
  textInput.addEventListener('input', updateCharCount);
  textInput.addEventListener('paste', () => {
    setTimeout(updateCharCount, 10); // Allow paste to complete
  });

  // Form submission
  explainBtn.addEventListener('click', handleExplain);
  textInput.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'Enter') {
      handleExplain();
    }
  });

  // Action buttons
  copyBtn.addEventListener('click', handleCopy);
  rerunBtn.addEventListener('click', handleRerun);

  // Listen for messages from background script
  chrome.runtime.onMessage.addListener(handleMessage);
}

/**
 * Update character count display
 */
function updateCharCount() {
  const length = textInput.value.length;
  charCount.textContent = `${length.toLocaleString()} / ${MAX_CHARS.toLocaleString()} characters`;
  
  if (length > MAX_CHARS) {
    charCount.classList.add('warning');
  } else {
    charCount.classList.remove('warning');
  }
}

/**
 * Handle explain button click
 */
async function handleExplain() {
  const text = textInput.value.trim();
  
  if (!text) {
    showError('Please enter some text to explain', 'Select text on the page or paste text in the input field');
    return;
  }

  if (isLoading) {
    return;
  }

  try {
    setLoading(true);
    hideError();
    hideOutput();

    // Truncate text if necessary
    let processedText = text;
    if (text.length > MAX_CHARS) {
      processedText = text.substring(0, MAX_CHARS);
    }

    const response = await chrome.runtime.sendMessage({
      type: 'EXPLAIN_TEXT',
      text: processedText,
      preset: presetSelect.value,
      model: modelSelect.value,
      safetyLevel: safetySelect.value
    });

    if (response.error) {
      showError(response.error.message, response.error.hint);
    } else if (response.result) {
      showOutput(response.result);
    } else {
      showError('Unexpected response format', 'Please try again');
    }

  } catch (error) {
    console.error('Error explaining text:', error);
    showError('Failed to communicate with extension', 'Please try refreshing the page and extension');
  } finally {
    setLoading(false);
  }
}

/**
 * Handle copy button click
 */
async function handleCopy() {
  try {
    await navigator.clipboard.writeText(currentExplanation);
    
    // Visual feedback
    const originalText = copyBtn.textContent;
    copyBtn.textContent = '✓ Copied!';
    setTimeout(() => {
      copyBtn.textContent = originalText;
    }, 2000);
    
  } catch (error) {
    console.error('Error copying text:', error);
    
    // Fallback for older browsers
    const textArea = document.createElement('textarea');
    textArea.value = currentExplanation;
    document.body.appendChild(textArea);
    textArea.select();
    document.execCommand('copy');
    document.body.removeChild(textArea);
    
    copyBtn.textContent = '✓ Copied!';
    setTimeout(() => {
      copyBtn.textContent = '📋 Copy';
    }, 2000);
  }
}

/**
 * Handle re-run button click
 */
function handleRerun() {
  handleExplain();
}

/**
 * Handle messages from background script
 */
function handleMessage(message, sender, sendResponse) {
  switch (message.type) {
    case 'EXPLANATION_RESULT':
      if (message.result) {
        showOutput(message.result);
        if (message.originalText && !textInput.value) {
          textInput.value = message.originalText;
          updateCharCount();
        }
      }
      setLoading(false);
      break;
      
    case 'EXPLANATION_ERROR':
      if (message.error) {
        showError(message.error.message, message.error.hint);
      }
      setLoading(false);
      break;
  }
}

/**
 * Set loading state
 */
function setLoading(loading) {
  isLoading = loading;
  explainBtn.disabled = loading;
  
  if (loading) {
    explainBtn.classList.add('loading');
  } else {
    explainBtn.classList.remove('loading');
  }
}

/**
 * Show error message
 */
function showError(message, hint = '') {
  errorMessage.textContent = message;
  errorHint.textContent = hint;
  errorSection.style.display = 'block';
  hideOutput();
}

/**
 * Hide error message
 */
function hideError() {
  errorSection.style.display = 'none';
}

/**
 * Show output
 */
function showOutput(result) {
  currentExplanation = result.text;
  outputText.textContent = result.text;
  
  // Show usage information
  if (result.usage) {
    const { promptTokens, candidateTokens, totalTokens } = result.usage;
    usageInfo.textContent = `${totalTokens || (promptTokens + candidateTokens)} tokens used`;
  } else {
    usageInfo.textContent = '';
  }
  
  outputSection.style.display = 'block';
  hideError();
  
  // Scroll to output
  setTimeout(() => {
    outputSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }, 100);
}

/**
 * Hide output
 */
function hideOutput() {
  outputSection.style.display = 'none';
  currentExplanation = '';
}

/**
 * Focus text input when popup opens
 */
function focusInput() {
  // Small delay to ensure popup is fully rendered
  setTimeout(() => {
    if (!textInput.value) {
      textInput.focus();
    }
  }, 100);
}

// Initialize when DOM is loaded
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    initialize();
    focusInput();
  });
} else {
  initialize();
  focusInput();
}
