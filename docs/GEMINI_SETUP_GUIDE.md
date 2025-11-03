# Gemini API Setup Guide

## Overview
This guide explains how to set up and use Google Gemini with the Digital Workshop application for AI-powered image analysis and metadata generation.

## Prerequisites
- Google Cloud account
- Gemini API enabled in your Google Cloud project
- Valid Gemini API key

## Step 1: Get Your Gemini API Key

### Option A: Using Google AI Studio (Recommended for Development)
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click "Create API Key"
3. Select or create a Google Cloud project
4. Copy your API key

### Option B: Using Google Cloud Console
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Generative AI API
4. Go to APIs & Services → Credentials
5. Create an API key
6. Copy your API key

## Step 2: Configure Gemini in Digital Workshop

### Method 1: Environment Variable (Recommended)
Set the environment variable before running the application:

**Windows (Command Prompt):**
```bash
set GOOGLE_API_KEY=your_api_key_here
python main.py
```

**Windows (PowerShell):**
```powershell
$env:GOOGLE_API_KEY="your_api_key_here"
python main.py
```

**Linux/Mac:**
```bash
export GOOGLE_API_KEY=your_api_key_here
python main.py
```

### Method 2: Preferences Dialog (UI)
1. Open the application
2. Go to **Preferences** (Ctrl+,)
3. Click the **AI** tab
4. Select **Google Gemini Vision** from the provider dropdown
5. Enter your API key in the "API Key" field
6. Select your preferred model (default: Gemini 2.5 Flash)
7. Click **Apply** or **OK**

## Step 3: Verify Configuration

### Test Your API Key
Run the verification script:
```bash
cd "d:\Digital Workshop"
python tests/test_gemini_key.py your_api_key_here
```

Expected output:
```
[SUCCESS] ✓ Gemini API key is working!
Message: Gemini API key is working! Response: ...
```

## Step 4: Use AI Analysis

### Generate Metadata with AI
1. Select a 3D model in the Library
2. Generate a preview image (if not already done)
3. Go to the **Metadata** tab
4. Click **"Run AI Analysis"** button
5. Wait for analysis to complete
6. Review and edit the generated metadata
7. Save the metadata

### Available Models
- **Gemini 2.5 Flash** (Recommended) - Fast and efficient
- **Gemini 2.5 Pro Preview** - More powerful, slower
- **Gemini 2.5 Flash Lite** - Lightweight version

## Troubleshooting

### Error: "API key was reported as leaked"
**Solution:** Your API key has been compromised. Create a new one:
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Delete the old key
3. Create a new API key
4. Update your configuration

### Error: "Model not found"
**Solution:** The model name is outdated. Update to one of the available models:
- gemini-2.5-flash
- gemini-2.5-pro-preview-03-25
- gemini-2.5-flash-lite-preview-06-17

### Error: "API key not configured"
**Solution:** Make sure the environment variable is set:
```bash
# Check if variable is set
echo %GOOGLE_API_KEY%  # Windows
echo $GOOGLE_API_KEY   # Linux/Mac
```

### Error: "No preview image"
**Solution:** Generate a preview image first:
1. Select a model in the Library
2. Click "Generate Preview" button
3. Wait for preview to generate
4. Then click "Run AI Analysis"

### Error: "Quota exceeded"
**Solution:** You've exceeded your API quota. Check your usage at:
- [Google Cloud Console - Quotas](https://console.cloud.google.com/iam-admin/quotas)
- Wait for quota to reset or upgrade your plan

## Features

### AI Analysis Capabilities
The AI analysis generates:
- **Title**: Concise descriptive title for the model
- **Description**: Detailed description of the model content
- **Keywords**: Relevant tags for categorization and search

### Supported Image Formats
- PNG
- JPEG
- GIF
- WebP

### Batch Processing
Currently, AI analysis is performed one model at a time. Future versions will support batch processing.

## Security Notes

⚠️ **Important Security Considerations:**
1. **Never commit API keys** to version control
2. **Use environment variables** for production deployments
3. **Rotate keys regularly** for security
4. **Monitor API usage** to detect unauthorized access
5. **Use API key restrictions** in Google Cloud Console:
   - Restrict to specific APIs (Generative AI API)
   - Restrict to specific HTTP referrers (if applicable)

## API Costs

Google Gemini API is free for development with usage limits:
- Free tier includes monthly quotas
- Paid tier available for higher usage
- Check [Google AI Pricing](https://ai.google.dev/pricing) for current rates

## Files Modified

- `src/gui/services/ai_description_service.py` - Added Gemini support
- `src/gui/services/providers/gemini_provider.py` - Gemini provider implementation
- `src/gui/services/providers/anthropic_provider.py` - Anthropic provider (bonus)
- `AutoGenDESC-AI/providers/gemini_provider.py` - Updated model list

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the test output from `test_gemini_key.py`
3. Check application logs in the Advanced preferences tab
4. Visit [Google AI Documentation](https://ai.google.dev/docs)

