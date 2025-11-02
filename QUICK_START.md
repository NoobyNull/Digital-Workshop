# Quick Start: Gemini AI Integration

## 🚀 Get Started in 3 Steps

### Step 1: Set API Key
Choose your method:

**Windows Command Prompt:**
```bash
set GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY
```

**Windows PowerShell:**
```powershell
$env:GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY"
```

**Linux/Mac:**
```bash
export GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY
```

### Step 2: Run Application
```bash
python main.py
```

### Step 3: Use AI Analysis
1. Select a 3D model in Library
2. Generate preview image (if needed)
3. Go to **Metadata** tab
4. Click **"Run AI Analysis"** button
5. Review and save metadata

---

## ✅ Verify It Works

```bash
python tests/test_gemini_key.py YOUR_GOOGLE_API_KEY
```

Expected: `[SUCCESS] ✓ Gemini API key is working!`

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| `GEMINI_SETUP_GUIDE.md` | Complete setup & troubleshooting |
| `GEMINI_INTEGRATION_SUMMARY.md` | Technical details |
| `ENVIRONMENT_VARIABLE_SETUP.md` | Environment variable guide |
| `GEMINI_FIX_COMPLETE.md` | Full summary |

---

## 🔑 Your API Key

```
YOUR_GOOGLE_API_KEY
```

⚠️ **IMPORTANT:** Never commit this key to version control!

---

## 🎯 Available Models

- **Gemini 2.5 Flash** (recommended) - Fast & efficient
- **Gemini 2.5 Pro Preview** - More powerful
- **Gemini 2.5 Flash Lite** - Lightweight

---

## ❓ Common Issues

| Issue | Solution |
|-------|----------|
| "API key not configured" | Set environment variable, restart terminal |
| "Model not found" | Use models from list above |
| "No preview image" | Click "Generate Preview" first |
| "API key was reported as leaked" | Create new key at https://aistudio.google.com/app/apikey |

---

## 🔒 Security

✅ API keys loaded from environment variables only
✅ Never stored in configuration files
✅ Never committed to version control
✅ Masked in logs

---

## 📞 Support

1. Run test: `python tests/test_gemini_key.py your_key`
2. Check logs: Preferences → Advanced
3. Read docs: See documentation list above
4. Visit: https://ai.google.dev/docs

---

**Status:** ✅ READY TO USE

Enjoy AI-powered metadata generation! 🚀

