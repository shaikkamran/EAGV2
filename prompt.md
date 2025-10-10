SYSTEM / DEV INSTRUCTIONS FOR CURSOR – build a Gemini-powered Chrome extension

You are an expert Chrome Extension engineer. Create a production-grade Manifest V3 extension named “Explain with Gemini” that explains selected text using the Gemini API.

0) High-level behavior
	•	When the user selects text on any webpage, they can:
	•	Right-click → “Explain with Gemini” to generate a concise, plain-English explanation.
	•	Use a keyboard shortcut (suggest: Ctrl+Shift+E / Command+Shift+E).
	•	Open the popup:
	•	Auto-prefills with the page’s current selection (if any),
	•	Or lets the user paste custom text.
	•	Extension calls Gemini generateContent and renders the result with: Copy, Re-run, and a tiny usage indicator.

1) Security & privacy
	•	Never hard-code API keys. Store key in chrome.storage.sync as geminiApiKey.
	•	Add "host_permissions": ["https://generativelanguage.googleapis.com/*"] and "permissions": ["storage", "contextMenus", "activeTab", "scripting", "commands", "notifications"].
	•	Truncate selections > 8,000 chars (warn user).
	•	Simple rate limiter: ≥1 request / 2s across the extension.
	•	Sanitize any HTML output (render plain text in popup).

2) Project structure
explain-with-gemini/
  ├─ manifest.json
  ├─ README.md
  ├─ src/
  │   ├─ background.js          // service worker: context menu, commands, messaging, rate limit
  │   ├─ content.js             // read selection when requested
  │   ├─ popup.html
  │   ├─ popup.js
  │   ├─ popup.css
  │   ├─ options.html
  │   ├─ options.js
  │   └─ options.css
  ├─ utils/
  │   └─ gemini.js              // REST helper for generateContent
  └─ assets/
      ├─ icon16.png
      ├─ icon48.png
      └─ icon128.png

3) manifest.json (MV3)
	•	name: Explain with Gemini
	•	action.default_popup: src/popup.html
	•	background.service_worker: src/background.js
	•	permissions: ["contextMenus","storage","activeTab","scripting","commands","notifications"]
	•	host_permissions: ["https://generativelanguage.googleapis.com/*"]
	•	commands: one command id explain-selection with a suggested default shortcut
	•	include icons from /assets

4) utils/gemini.js

Implement callGemini({ apiKey, model, prompt, maxOutputTokens, safetyLevel }):
	•	Endpoint: POST https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${apiKey}
	•	Request body (text-only):
{
  "contents": [
    { "parts": [ { "text": "<PROMPT TEXT>" } ] }
  ],
  "generationConfig": {
    "maxOutputTokens": 300,
    "temperature": 0.3
  },
  "safetySettings": [
    // Make this optional; default "BLOCK_MEDIUM_AND_ABOVE" for common categories.
    // Allow 'OFF' via Options to reduce blocking during prototyping.
  ]
}

	•	Parse response text from candidates[0].content.parts[].text (or from promptFeedback / safety blocks). Return { text, usage } where usage can be approximated from promptTokenCount/candidates[0].usageMetadata if present; otherwise estimate by characters.

5) src/background.js (service worker)

Responsibilities:
	•	Context menu: create “Explain with Gemini” (contexts: ["selection"]).
	•	Commands: on explain-selection, read selection from active tab via chrome.scripting.executeScript.
	•	Rate limiting: basic token bucket or timestamp check.
	•	Settings: read from chrome.storage.sync → { geminiApiKey, model, preset, safetyLevel }.
	•	Build prompt using presets (below) + selection.
	•	Call callGemini(...), then:
	•	If popup is open, chrome.runtime.sendMessage with the result.
	•	Else, show a notification (title “Explanation ready”, message is first 200 chars) with a “Copy” action that copies full text via a temporary offscreen document or scripting API.
	•	Errors: normalize into { code, message, hint } (e.g., missing key, 400 schema error, 401 auth, 429 rate limit, network).

6) src/content.js
	•	Export a function that returns window.getSelection()?.toString() || "".
	•	Do not run persistently; inject only when needed via chrome.scripting.executeScript.

7) Popup UI (src/popup.*)
	•	Minimal, accessible UI:
	•	Textarea prefilled with current selection (if any).
	•	Preset selector: ELI5, Key points, Plain.
	•	Model dropdown (default gemini-2.5-flash).
	•	Safety level dropdown: Default (block medium+), Relaxed, Off.
	•	“Explain” button (disabled while loading), spinner, error area.
	•	Output area with monospace font, Copy, Re-run, and usage line.
	•	On submit, send { type: "EXPLAIN_TEXT", text, preset, model, safetyLevel } to background and render the response.

8) Options page (src/options.*)
	•	Inputs:
	•	Gemini API key (password field with show/hide).
	•	Default model (text or select; default gemini-2.5-flash).
	•	Default preset.
	•	Safety level (Default/Relaxed/Off).
	•	Buttons:
	•	Save → chrome.storage.sync.
	•	Test call → run a 1-token ping to verify credentials; show success/error inline.
	•	Add a doc hint linking to ai.google.dev “Get API key” page.

9) Presets (UX copy)
	•	ELI5 → prefix:
Explain like I’m 5, with a friendly tone and simple examples:\n\n
	•	Key points → prefix:
Summarize into 3–5 bullet points anyone can understand:\n\n
	•	Plain → prefix:
Explain simply and clearly:\n\n

10) Token/length constraints
	•	Limit selection to 8,000 chars; show “Truncated for speed (8,000/… chars).”
	•	Default maxOutputTokens: 300 (configurable in code, not surfaced in UI yet).

11) Code quality & misc
	•	Plain JavaScript modules (no bundler).
	•	ES2022 features supported by Chrome.
	•	Small helpers: getSelectionFromActiveTab(), readSettings(), withRateLimit(fn), buildPrompt(preset, text).
	•	Comments + error messages that guide the user to Options when needed.

12) Deliverables

Generate working code for every file in the structure above, plus simple placeholder icons and a clear README.md covering:
	•	Loading unpacked extension
	•	Setting the Gemini API key
	•	Using context menu / shortcut / popup
	•	Troubleshooting (missing key, CORS/host permissions, model errors, safety blocks)

13) Defaults & references to bake into comments
	•	Default model: gemini-2.5-flash (fast + value). Mention that model names follow <model>-<generation>-<variation> (e.g., gemini-2.0-flash). Link in comments to the Gemini models doc.
	•	Endpoint + request shape are from Gemini REST docs; include links in comments near the fetch call.


