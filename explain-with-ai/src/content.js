/**
 * Content Script for ExplainWithAi Extension
 * Provides text selection functionality when injected
 */

/**
 * Get current text selection from the page
 * @returns {string} Selected text or empty string
 */
function getSelectedText() {
  const selection = window.getSelection();
  return selection ? selection.toString().trim() : '';
}

// Export for use when injected via chrome.scripting.executeScript
if (typeof window !== 'undefined') {
  window.getSelectedText = getSelectedText;
}

// For module usage
export { getSelectedText };
