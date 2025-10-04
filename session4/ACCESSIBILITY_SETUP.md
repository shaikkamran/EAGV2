## macOS Accessibility Permissions Setup

The "Access not allowed" error occurs because macOS requires explicit permission for applications to control other applications via AppleScript/System Events.

### Fix the Issue:

1. **Open System Preferences/Settings**:
   - macOS Ventura/Sonnet: Apple Menu → System Settings
   - Earlier versions: Apple Menu → System Preferences

2. **Navigate to Privacy & Security**:
   - Click on "Privacy & Security" in the sidebar

3. **Go to Accessibility**:
   - Scroll down and click on "Accessibility"

4. **Add Terminal/Python**:
   - Click the "+" button
   - Navigate to `/Applications/Utilities/Terminal.app` and add it
   - If using Python directly, also add your Python executable (usually `/usr/bin/python3` or from your conda/virtual environment)

5. **Alternative: Add Script Editor**:
   - You can also add `/Applications/Utilities/Script Editor.app`

### Quick Test:

After adding permissions, test with this simple AppleScript:

```applescript
tell application "Preview"
    activate
end tell
```

### Alternative Approach (No Permissions Needed):

Instead of UI automation, we can use simpler methods that don't require accessibility permissions.
