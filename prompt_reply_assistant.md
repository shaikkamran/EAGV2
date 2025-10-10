You are an expert Chrome Extensions engineer + product designer. Build a production-ready **Manifest V3** Chrome extension named **Contextual Reply Assistant** that:

- Adds a ✨ AI Reply button next to message composers on **WhatsApp Web**, **LinkedIn (messages)**, and **Gmail**.
- Extracts the **recent conversation context** (last N messages, bounded) directly from the DOM.
- Uses **Gemini 2.0 Flash** as the **default LLM** (via Google AI “Generative Language” REST API). The user provides a **Gemini API key** in Settings.
- Supports a **basic Persona RAG**: the user uploads a **persona file** (Markdown/JSON/TXT). We store it **locally** and retrieve the top-K persona snippets relevant to the current thread, then prepend them to the LLM prompt (no vectors server—just lightweight in-extension retrieval).
- Prioritizes **privacy** and **minimal permissions**; never expose API keys to content scripts; no analytics.
- Generates **three reply variants** that mirror the target platform’s tone/format and the user’s persona/preferences.

================================
## 0) Goals & Non-Goals
- GOAL: One-click, context-aware reply drafts with persona-aligned tone.
- GOAL: Run LLM calls **only** from the background service worker (MV3).
- GOAL: Persona-RAG in the extension (no external DB).
- NON-GOAL: Auto-send messages. We only draft and insert.

================================
## 1) Security, Privacy, and Safety
Implement and document in README:

**Key Handling**
- Store the **Gemini API key** only in `chrome.storage.local`.
- All LLM calls go through the **background service worker** (never content scripts). Content scripts have **no** access to the API key.

**Data Minimization**
- Extract only the last **6–10** message bubbles (platform-specific), truncate combined context (WhatsApp/LinkedIn ~4k chars, Gmail ~6k chars).
- Never persist conversation content. It is only passed transiently to the background for the single LLM call.

**Persona Storage & RAG**
- Persona file uploaded via Options page (Markdown/JSON/TXT).
- Parse → chunk into ~700–900 char blocks with slight overlap.
- Compute lightweight **keyword/term-frequency vectors in-extension** and pick **top-K (e.g., 3–5)** snippets relevant to the current thread via cosine similarity on bag-of-words TF (no external embedding requests needed).
- Store persona chunks and their term frequencies in `chrome.storage.local` (not sync) to avoid size limits.

**PII Redaction (Optional Toggle)**
- Before sending to LLM, run a regex redactor for emails/phone numbers/credit card patterns. Replace with tokens like `[EMAIL]`, `[PHONE]`. Toggle in Options.

**Permissions**
- Only request: `activeTab`, `scripting`, `storage`.
- `host_permissions`: `https://web.whatsapp.com/*`, `https://www.linkedin.com/*`, `https://mail.google.com/*`.

**No Analytics**
- Zero telemetry by default.

**CSP / Remote Code**
- MV3 defaults; no remote code execution; only fetch to Gemini API domain or a user-specified **custom endpoint**.

================================
## 2) How Context Is Read (Answering the user’s question)
Explain in code comments + README: **content scripts run in the page**, so they can read the visible DOM (chat bubbles/email bodies + composer). They gather the most recent messages, trim them, and send to background via `chrome.runtime.sendMessage`. The browser can read that text because it’s on the current page and we have host permissions for that origin.

================================
## 3) Functional Requirements
- **Toolbar next to composer** with:
  - ✨ **AI Reply**
  - Tone chips: *Auto*, *Formal*, *Casual*, *Persuasive*
  - Show **3 suggestions**; each has **Insert** and **Copy**.
- **Persona RAG flow**:
  1) On generation, background retrieves user persona top-K chunks relevant to the thread (keyword TF cosine).
  2) Prepend a **persona system block** to the LLM messages so replies reflect the user’s voice/preferences.
- **LinkedIn recruiter logic**:
  - If thread hints “role/opening/opportunity/recruiter”, add gratitude, ask for missing details (comp, stack, location, seniority), propose next steps aligned with persona constraints (e.g., remote-first, salary expectations—if present in persona).
- **Scheduling logic**:
  - If a meeting is requested, propose 2–3 time windows, use concise format, avoid weekends unless persona prefers otherwise.
- **Language auto-detect** (lightweight):
  - If latest incoming message is non-English (heuristic: Unicode script check or LLM hint), generate in that language.
- **Keyboard shortcut**:
  - `Alt+R` (Win/Linux) / `Option+R` (macOS) triggers generation on the active supported site.

================================
## 4) Project Structure (create these files, fully implemented)
- `manifest.json`
- `background.js` — service worker: Gemini client, provider abstraction, persona RAG select-K, PII redaction, rate limit, error handling.
- `lib/llmClient.js` — message helper for content scripts → background.
- `lib/rag.js` — persona parse/chunk/store + TF vectorizer + cosine similarity select-K.
- `content/common/ui.js` — toolbar, tone chips, suggestions pane.
- `content/whatsapp.js` — site integration.
- `content/linkedin.js` — site integration.
- `content/gmail.js` — site integration.
- `options.html` `options.js` `options.css` — settings + persona uploader (file input).
- `popup.html` `popup.js` `popup.css` — small status screen (key set? persona loaded?).
- `assets/icon16.png` `icon48.png` `icon128.png` — placeholder icons.
- `README.md` — install, privacy, persona RAG explanation, troubleshooting, extension points.
- `LICENSE` — MIT.

================================
## 5) Manifest (MV3)
- Name: “Contextual Reply Assistant”
- Version: 0.2.0
- Permissions: `activeTab`, `scripting`, `storage`
- Host permissions: WhatsApp, LinkedIn, Gmail
- Background: `service_worker: background.js`, type `module` preferred
- Content scripts: one per site (`run_at: document_idle`)
- Action: popup
- Commands: `generate-reply` for the keyboard shortcut

================================
## 6) Gemini 2.0 Flash — Provider Details (default)
Implement a provider abstraction with **Gemini default** and an optional **custom endpoint**:

```ts
// Types (JS ok)
type ChatMessage = { role: 'system'|'user'|'assistant'; content: string };
type LLMRequest = {
  provider: 'gemini'|'custom';
  apiKey?: string;
  model: string;             // default: "gemini-2.0-flash" (allow override)
  messages: ChatMessage[];
  temperature?: number;      // default ~0.7
  endpoint?: string;         // custom endpoint only
};
type LLMResponse = { ok: true; content: string } | { ok: false; error: string };