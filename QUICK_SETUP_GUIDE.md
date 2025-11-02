# Quick Setup Guide - Gemini AI Integration

## TL;DR - 3 Steps to Get Started

### Step 1: Set Environment Variable
Open Command Prompt and run:
```bash
set GOOGLE_API_KEY=AIzaSyBPSlisUcMHwaiLTcCWLlSQlmjUFhTFR2c
```

### Step 2: Start Application
```bash
python main.py
```

### Step 3: Use AI Analysis
1. Select a 3D model
2. Click "Generate Preview" (if needed)
3. Click "Run AI Analysis" button
4. Done! Metadata is auto-generated

---

## Detailed Setup

### For Windows Command Prompt

```bash
# Set the environment variable
set GOOGLE_API_KEY=AIzaSyBPSlisUcMHwaiLTcCWLlSQlmjUFhTFR2c

# Navigate to project
cd "d:\Digital Workshop"

# Run the application
python main.py
```

### For Windows PowerShell

```powershell
# Set the environment variable
$env:GOOGLE_API_KEY="AIzaSyBPSlisUcMHwaiLTcCWLlSQlmjUFhTFR2c"

# Navigate to project
cd "d:\Digital Workshop"

# Run the application
python main.py
```

### For Linux/Mac

```bash
# Set the environment variable
export GOOGLE_API_KEY=AIzaSyBPSlisUcMHwaiLTcCWLlSQlmjUFhTFR2c

# Navigate to project
cd ~/path/to/Digital\ Workshop

# Run the application
python main.py
```

---

## Verify Setup

### Test 1: Check Environment Variable
```bash
# Windows
echo %GOOGLE_API_KEY%

# Linux/Mac
echo $GOOGLE_API_KEY
```

Should show: `AIzaSyBPSlisUcMHwaiLTcCWLlSQlmjUFhTFR2c`

### Test 2: Run Integration Tests
```bash
cd "d:\Digital Workshop"
python tests/test_gemini_integration.py AIzaSyBPSlisUcMHwaiLTcCWLlSQlmjUFhTFR2c
```

Should show: `✓ ALL TESTS PASSED - Gemini integration is working!`

### Test 3: Test in Preferences
1. Open application
2. Go to Preferences (Ctrl+,)
3. Click AI tab
4. Select "Google Gemini Vision"
5. Click "Test Connection"
6. Should show: `✓ Using API key from environment variable: GOOGLE_API_KEY`

---

## Using AI Analysis

### In Metadata Editor

1. **Select a Model**
   - Click on a 3D model in the Library panel

2. **Generate Preview** (if needed)
   - Click "Generate Preview" button
   - Wait for thumbnail to generate

3. **Run AI Analysis**
   - Click "Run AI Analysis" button
   - Wait for AI to analyze the image
   - Metadata fields auto-populate:
     - Title
     - Description
     - Keywords

4. **Review & Save**
   - Review the generated metadata
   - Edit if needed
   - Click "Save" to save changes

---

## Troubleshooting

### Problem: "API key not configured"
**Solution:**
1. Verify environment variable is set: `echo %GOOGLE_API_KEY%`
2. Restart terminal/IDE
3. Restart application

### Problem: "Test Connection" shows error
**Solution:**
1. Make sure environment variable is set
2. Verify API key is correct
3. Check internet connection
4. Try again

### Problem: "Run AI Analysis" button doesn't work
**Solution:**
1. Ensure environment variable is set
2. Restart application
3. Generate preview image first
4. Check that Gemini is selected in Preferences

### Problem: "No module named 'src'"
**Solution:**
1. Make sure you're in the project directory: `cd "d:\Digital Workshop"`
2. Run from project root, not from subdirectory

---

## What's New

✅ **Fixed Issues:**
- AI service now initialized in main window
- Preferences dialog checks environment variables
- Test connection works without manual entry
- "Run AI Analysis" button fully functional

✅ **New Features:**
- Environment variable documentation in Preferences
- Helpful error messages
- Comprehensive test suite

✅ **Security:**
- API keys loaded from environment only
- Never stored in config files
- Masked in logs

---

## Files Changed

- `src/gui/main_window.py` - Added AI service initialization
- `src/gui/preferences.py` - Enhanced test connection
- `tests/test_gemini_integration.py` - New test suite

---

## Support

For detailed information, see:
- `GEMINI_PREFERENCES_FIX.md` - Complete technical details
- `GEMINI_SETUP_GUIDE.md` - Comprehensive setup guide
- `ENVIRONMENT_VARIABLE_SETUP.md` - Environment variable help

---

## Summary

✅ **Status: READY TO USE**

Your Gemini AI integration is now fully functional!

1. Set environment variable
2. Start application
3. Use "Run AI Analysis" button
4. Enjoy AI-powered metadata! 🚀

