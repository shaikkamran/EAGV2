# ExplainWithAi - Chrome Extension

A powerful Chrome extension that explains selected text using Google's Gemini AI. Get instant, clear explanations of complex text with just a right-click or keyboard shortcut.

## ✨ Features

- **Multiple Ways to Explain**: Right-click context menu, keyboard shortcut (`Ctrl+Shift+E` / `Cmd+Shift+E`), or popup interface
- **Smart Text Selection**: Automatically detects selected text on any webpage
- **Flexible Explanation Styles**: Choose from ELI5, Key Points, or Plain explanations
- **Model Selection**: Support for multiple Gemini models (2.5 Flash, 2.0 Flash, 1.5 Pro)
- **Privacy-First**: Your API key stays in your browser, no data collection
- **Rate Limiting**: Built-in request throttling for optimal API usage
- **Safety Controls**: Configurable content filtering levels

## 🚀 Quick Start

### 1. Install the Extension

1. Download or clone this repository
2. **Optional: Install Cool Custom Icon**
   - Open `create-cool-icons.html` in your browser
   - Upload your `ExplainWithGemini.avif` file
   - Download the generated PNG icons and replace files in `assets/` folder
3. Open Chrome and navigate to `chrome://extensions/`
4. Enable "Developer mode" (toggle in top-right corner)
5. Click "Load unpacked" and select the `explain-with-ai` folder

### 2. Get Your Gemini API Key

1. Visit [Google AI Studio](https://ai.google.dev)
2. Sign in with your Google account
3. Click "Get API Key" → "Create API Key"
4. Copy your API key

### 3. Configure the Extension

1. Click the extension icon in Chrome's toolbar
2. Click "Settings" in the popup footer
3. Paste your API key in the "Gemini API Key" field
4. Click "Test API Connection" to verify
5. Click "Save Settings"

### 4. Start Explaining!

- **Select text** on any webpage and right-click → "Explain with AI"
- Use the keyboard shortcut: `Ctrl+Shift+E` (Windows/Linux) or `Cmd+Shift+E` (Mac)
- Click the extension icon to open the popup and paste text manually

## 📖 Usage Guide

### Context Menu
1. Select any text on a webpage
2. Right-click and choose "Explain with AI"
3. View the explanation in a notification or popup

### Keyboard Shortcut
1. Select text on any webpage
2. Press `Ctrl+Shift+E` (or `Cmd+Shift+E` on Mac)
3. Get instant explanations without interrupting your workflow

### Popup Interface
1. Click the extension icon in Chrome's toolbar
2. The popup will auto-fill with currently selected text (if any)
3. Or paste/type text manually
4. Choose explanation style and model
5. Click "Explain" and view results with copy/re-run options

### Settings Page
Access via popup footer or right-click extension icon → "Options":

- **API Key**: Your Gemini API key (required)
- **Default Model**: Choose your preferred Gemini model
- **Explanation Style**: Set default explanation approach
- **Safety Level**: Control content filtering strictness

## 🎯 Explanation Styles

| Style | Description | Best For |
|-------|-------------|----------|
| **ELI5** | Explain like I'm 5 - friendly, simple examples | Complex concepts, technical terms |
| **Key Points** | 3-5 bullet point summary | Quick overviews, main ideas |
| **Plain** | Simple, clear explanation | General use, balanced detail |

## ⚙️ Models & Performance

| Model | Speed | Capability | Best For |
|-------|-------|------------|----------|
| **Gemini 2.5 Flash** ⭐ | Very Fast | High | Recommended for most use |
| **Gemini 2.0 Flash** | Fast | High | Alternative fast option |
| **Gemini 1.5 Pro** | Slower | Highest | Complex analysis |

## 🛡️ Privacy & Security

- **Local Storage**: API keys stored securely in Chrome's sync storage
- **No Data Collection**: Extension doesn't collect or store your data
- **Direct API Calls**: Text sent only to Google's Gemini API
- **Rate Limiting**: 1 request per 2 seconds to prevent API abuse
- **Content Limits**: Text truncated at 8,000 characters for performance

## 🔧 Troubleshooting

### "API key not configured"
- Go to Settings and enter your Gemini API key
- Test the connection to verify it works
- Ensure the key is from ai.google.dev

### "Content blocked" errors
- Try adjusting Safety Level in Settings to "Relaxed" or "Off"
- Some content may be blocked by Gemini's safety filters
- Rephrase sensitive content or use different text

### "Network error" or timeouts
- Check your internet connection
- Verify the API key is correct and active
- Try again after a few moments

### Extension not responding
- Refresh the page and try again
- Check Chrome's extension manager for errors
- Reload the extension if needed

### Rate limiting messages
- Wait 2 seconds between requests
- The extension automatically enforces rate limits
- Consider using shorter text passages

## 🔗 Advanced Usage

### Keyboard Shortcuts
Customize in Chrome: `chrome://extensions/shortcuts`

### Multiple Models
Test different models for various use cases:
- Fast responses: Flash models
- Complex analysis: Pro models
- Experimentation: Try different versions

### Safety Settings
- **Default**: Blocks medium+ harmful content (recommended)
- **Relaxed**: Blocks only highly harmful content
- **Off**: No content filtering (development only)

## 📊 Token Usage

- **Typical Usage**: 50-200 tokens per explanation
- **Character Limit**: 8,000 characters max input
- **Optimization**: Shorter text = fewer tokens = faster responses

## 🆘 Support & Resources

- **Gemini API Docs**: [ai.google.dev](https://ai.google.dev)
- **Chrome Extension APIs**: [developer.chrome.com](https://developer.chrome.com/docs/extensions/)
- **Model Information**: [Gemini Models](https://ai.google.dev/models/gemini)

## 🧪 Development

### Project Structure
```
explain-with-gemini/
├── manifest.json           # Extension configuration
├── src/
│   ├── background.js       # Service worker
│   ├── content.js          # Content script
│   ├── popup.html/css/js   # Popup interface
│   └── options.html/css/js # Settings page
├── utils/
│   └── gemini.js          # API utility
├── assets/
│   └── icon*.png          # Extension icons
└── README.md              # This file
```

### Building from Source
1. Clone the repository
2. No build process required - pure JavaScript
3. Load unpacked in Chrome developer mode

### Contributing
1. Fork the repository
2. Create feature branch
3. Test thoroughly with your API key
4. Submit pull request

## 📄 License

This project is open source. See the license file for details.

## 🙏 Acknowledgments

- Built with Google's Gemini API
- Follows Chrome Extension Manifest V3 standards
- Designed for privacy and performance

---

**Happy explaining!** 🎉

Transform any text into clear, understandable explanations with the power of AI.
