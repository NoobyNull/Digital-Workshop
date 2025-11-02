# OpenRouter Provider Setup Guide

## Overview
OpenRouter is a unified API that provides access to 100+ vision models from multiple providers including OpenAI, Anthropic, Meta, and more. It's OpenAI-compatible, making it easy to integrate.

---

## Getting Started

### 1. Create an OpenRouter Account
1. Visit https://openrouter.io
2. Sign up for a free account
3. Go to https://openrouter.io/keys to get your API key

### 2. Configure in AutoGenDESC-AI

#### Option A: Using the GUI
1. Launch the application
2. Select "OpenRouter" from the provider dropdown
3. Click "Configure Provider"
4. Paste your OpenRouter API key
5. Select your desired model
6. Click "Test Connection"
7. Click "Save"

#### Option B: Edit config.json
```json
{
  "OpenRouter": {
    "api_key": "your-openrouter-api-key",
    "model": "gpt-4-vision-preview",
    "base_url": "https://openrouter.io/api/v1"
  }
}
```

---

## Available Vision Models

### OpenAI Models
- `gpt-4-vision-preview` - GPT-4 Vision
- `gpt-4o` - GPT-4o
- `gpt-4o-mini` - GPT-4o Mini

### Anthropic Models
- `claude-3-opus-20240229` - Claude 3 Opus
- `claude-3-sonnet-20240229` - Claude 3 Sonnet
- `claude-3-haiku-20240307` - Claude 3 Haiku

### Meta Models
- `llama-2-13b-chat` - Llama 2 13B
- `llama-3-70b-instruct` - Llama 3 70B

### Other Models
- `mistral-7b-instruct` - Mistral 7B
- `neural-chat-7b` - Neural Chat 7B
- And 100+ more...

**Note:** Model availability may change. Use the "Get Models" button in the configuration dialog to see the latest available models.

---

## Pricing

OpenRouter offers competitive pricing for all models. Visit https://openrouter.io/docs/models for current pricing.

**Key Benefits:**
- Pay-as-you-go pricing
- No subscription required
- Competitive rates compared to direct API access
- Free tier available for testing

---

## Features

### ✅ Supported Features
- Vision image analysis
- Model selection and switching
- Automatic model listing
- Custom prompts
- Base64 image encoding
- Multiple image formats (JPEG, PNG, GIF, WebP)

### ✅ Advantages
- Access to 100+ models with one API key
- Fallback to alternative models if one is unavailable
- Competitive pricing
- No vendor lock-in
- Easy to switch between models

---

## Usage Examples

### Basic Configuration
```json
{
  "OpenRouter": {
    "api_key": "sk-or-v1-...",
    "model": "gpt-4-vision-preview"
  }
}
```

### Using Claude 3 Opus
```json
{
  "OpenRouter": {
    "api_key": "sk-or-v1-...",
    "model": "claude-3-opus-20240229"
  }
}
```

### Using Llama Vision
```json
{
  "OpenRouter": {
    "api_key": "sk-or-v1-...",
    "model": "llama-2-13b-chat"
  }
}
```

---

## Troubleshooting

### "Invalid API Key" Error
- Verify your API key is correct
- Check that you copied the entire key from https://openrouter.io/keys
- Ensure the key hasn't expired

### "Model Not Found" Error
- The model may not be available on OpenRouter
- Use the "Get Models" button to see available models
- Try a different model from the list

### "Rate Limit Exceeded" Error
- You've exceeded OpenRouter's rate limits
- Wait a few minutes before retrying
- Consider upgrading your OpenRouter account for higher limits

### Connection Timeout
- Check your internet connection
- Verify OpenRouter is accessible (https://openrouter.io)
- Try a different model

---

## Best Practices

1. **Start with a Free Tier**
   - Test with the free tier before committing to paid usage
   - Use cheaper models for testing

2. **Monitor Usage**
   - Check your usage dashboard at https://openrouter.io/account/usage
   - Set up billing alerts if available

3. **Choose Appropriate Models**
   - Use cheaper models for simple tasks
   - Use more powerful models only when needed
   - Consider model speed vs. accuracy trade-offs

4. **Secure Your API Key**
   - Never commit your API key to version control
   - Use environment variables for sensitive data
   - Rotate your key periodically

5. **Test Before Production**
   - Test with sample images first
   - Verify model output quality
   - Check response times

---

## Comparison with Direct APIs

| Feature | OpenRouter | Direct API |
|---------|-----------|-----------|
| Models Available | 100+ | 1 |
| API Key Required | 1 | Multiple |
| Pricing | Competitive | Varies |
| Fallback Models | Yes | No |
| Setup Time | 5 minutes | 15+ minutes |
| Vendor Lock-in | Low | High |

---

## Support

- **OpenRouter Docs:** https://openrouter.io/docs
- **API Reference:** https://openrouter.io/docs/api/v1
- **Status Page:** https://status.openrouter.io
- **Community:** https://discord.gg/openrouter

---

## Next Steps

1. Get your API key from https://openrouter.io/keys
2. Configure OpenRouter in AutoGenDESC-AI
3. Test with a sample image
4. Start analyzing images with your preferred model!

