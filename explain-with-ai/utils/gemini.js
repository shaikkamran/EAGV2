/**
 * Gemini API utility for ExplainWithAi Chrome Extension
 * 
 * API Documentation:
 * - Gemini REST API: https://ai.google.dev/api/rest
 * - Model reference: https://ai.google.dev/models/gemini
 */

/**
 * Call Gemini generateContent API
 * @param {Object} options
 * @param {string} options.apiKey - Gemini API key
 * @param {string} options.model - Model name (e.g., 'gemini-2.5-flash')
 * @param {string} options.prompt - Text prompt to send
 * @param {number} [options.maxOutputTokens=300] - Maximum tokens to generate
 * @param {string} [options.safetyLevel='BLOCK_MEDIUM_AND_ABOVE'] - Safety setting level
 * @returns {Promise<{text: string, usage: {promptTokens: number, candidateTokens: number}}>}
 */
export async function callGemini({ apiKey, model, prompt, maxOutputTokens = 300, safetyLevel = 'BLOCK_MEDIUM_AND_ABOVE' }) {
  if (!apiKey) {
    throw new Error('API key is required');
  }
  
  if (!model) {
    throw new Error('Model is required');
  }
  
  if (!prompt) {
    throw new Error('Prompt is required');
  }

  const url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}`;
  
  // Safety settings mapping
  const safetySettings = getSafetySettings(safetyLevel);
  
  const requestBody = {
    contents: [
      {
        parts: [
          { text: prompt }
        ]
      }
    ],
    generationConfig: {
      maxOutputTokens: maxOutputTokens,
      temperature: 0.3
    },
    safetySettings: safetySettings
  };

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestBody)
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new GeminiError(response.status, errorData.error?.message || response.statusText, errorData);
    }

    const data = await response.json();
    
    // Handle safety blocks
    if (data.promptFeedback?.blockReason) {
      throw new GeminiError(400, `Content blocked: ${data.promptFeedback.blockReason}`, {
        blockReason: data.promptFeedback.blockReason,
        safetyRatings: data.promptFeedback.safetyRatings
      });
    }

    // Extract response text
    const candidates = data.candidates;
    if (!candidates || candidates.length === 0) {
      throw new GeminiError(400, 'No candidates returned from API', data);
    }

    const candidate = candidates[0];
    
    // Check for finish reason blocks
    if (candidate.finishReason === 'SAFETY') {
      throw new GeminiError(400, 'Response blocked for safety reasons', {
        finishReason: candidate.finishReason,
        safetyRatings: candidate.safetyRatings
      });
    }

    const parts = candidate.content?.parts;
    if (!parts || parts.length === 0) {
      throw new GeminiError(400, 'No content parts returned', candidate);
    }

    const text = parts.map(part => part.text || '').join('').trim();
    
    if (!text) {
      throw new GeminiError(400, 'Empty response text', candidate);
    }

    // Extract usage information
    const usage = extractUsage(data, prompt, text);

    return { text, usage };
    
  } catch (error) {
    if (error instanceof GeminiError) {
      throw error;
    }
    
    // Network or other errors
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new GeminiError(0, 'Network error - check your internet connection', { originalError: error.message });
    }
    
    throw new GeminiError(500, error.message || 'Unknown error occurred', { originalError: error.message });
  }
}

/**
 * Get safety settings based on level
 * @param {string} level - 'BLOCK_MEDIUM_AND_ABOVE', 'BLOCK_ONLY_HIGH', 'BLOCK_NONE'
 * @returns {Array} Safety settings array
 */
function getSafetySettings(level) {
  const categories = [
    'HARM_CATEGORY_HARASSMENT',
    'HARM_CATEGORY_HATE_SPEECH', 
    'HARM_CATEGORY_SEXUALLY_EXPLICIT',
    'HARM_CATEGORY_DANGEROUS_CONTENT'
  ];

  let threshold;
  switch (level) {
    case 'BLOCK_NONE':
    case 'OFF':
      threshold = 'BLOCK_NONE';
      break;
    case 'BLOCK_ONLY_HIGH':
    case 'RELAXED':
      threshold = 'BLOCK_ONLY_HIGH';
      break;
    case 'BLOCK_MEDIUM_AND_ABOVE':
    case 'DEFAULT':
    default:
      threshold = 'BLOCK_MEDIUM_AND_ABOVE';
      break;
  }

  return categories.map(category => ({
    category,
    threshold
  }));
}

/**
 * Extract usage information from API response
 * @param {Object} data - API response data
 * @param {string} prompt - Original prompt
 * @param {string} text - Generated text
 * @returns {Object} Usage statistics
 */
function extractUsage(data, prompt, text) {
  // Try to get actual usage metadata if available
  const usageMetadata = data.usageMetadata;
  if (usageMetadata) {
    return {
      promptTokens: usageMetadata.promptTokenCount || 0,
      candidateTokens: usageMetadata.candidatesTokenCount || 0,
      totalTokens: usageMetadata.totalTokenCount || 0
    };
  }

  // Fallback to character-based estimation
  // Rough approximation: 1 token ≈ 4 characters for English text
  const estimatedPromptTokens = Math.ceil(prompt.length / 4);
  const estimatedCandidateTokens = Math.ceil(text.length / 4);

  return {
    promptTokens: estimatedPromptTokens,
    candidateTokens: estimatedCandidateTokens,
    totalTokens: estimatedPromptTokens + estimatedCandidateTokens
  };
}

/**
 * Custom error class for Gemini API errors
 */
export class GeminiError extends Error {
  constructor(status, message, details = {}) {
    super(message);
    this.name = 'GeminiError';
    this.status = status;
    this.details = details;
    
    // Provide user-friendly error codes and hints
    this.code = this.getErrorCode(status, message, details);
    this.hint = this.getErrorHint(this.code, status);
  }

  getErrorCode(status, message, details) {
    if (status === 401 || message.includes('API key')) {
      return 'INVALID_API_KEY';
    }
    if (status === 400 && message.includes('blocked')) {
      return 'CONTENT_BLOCKED';
    }
    if (status === 429 || message.includes('quota') || message.includes('rate limit')) {
      return 'RATE_LIMITED';
    }
    if (status === 404 || message.includes('model')) {
      return 'INVALID_MODEL';
    }
    if (status === 0 || message.includes('network') || message.includes('fetch')) {
      return 'NETWORK_ERROR';
    }
    if (status >= 500) {
      return 'SERVER_ERROR';
    }
    return 'UNKNOWN_ERROR';
  }

  getErrorHint(code, status) {
    switch (code) {
      case 'INVALID_API_KEY':
        return 'Check your API key in the extension options. Get a key at ai.google.dev';
      case 'CONTENT_BLOCKED':
        return 'Try different text or change safety settings in options';
      case 'RATE_LIMITED':
        return 'Too many requests. Wait a moment and try again';
      case 'INVALID_MODEL':
        return 'Check model name in options. Use "gemini-2.5-flash" or similar';
      case 'NETWORK_ERROR':
        return 'Check your internet connection and try again';
      case 'SERVER_ERROR':
        return 'Gemini service is temporarily unavailable. Try again later';
      default:
        return 'Check extension options and try again';
    }
  }
}
