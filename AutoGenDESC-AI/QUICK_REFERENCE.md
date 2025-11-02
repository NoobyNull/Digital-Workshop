# Quick Reference - Provider Configuration

## Provider Status Overview

```
✅ OpenAI          - Custom endpoints supported
✅ OpenRouter      - 100+ models via OpenAI-compatible API
✅ Anthropic       - Custom endpoints supported
✅ Google Gemini   - Official API only
✅ xAI (Grok)      - Custom endpoints supported
✅ ZAI             - Custom endpoints supported
✅ Perplexity      - Custom endpoints supported
✅ Ollama          - Local instance supported
✅ AI Studio       - Custom endpoints supported
```

---

## Configuration Template

### Default Configuration (No Custom Endpoint)
```json
{
  "OpenAI": {
    "api_key": "sk-...",
    "model": "gpt-4-vision-preview"
  }
}
```

### Custom Endpoint Configuration
```json
{
  "OpenAI": {
    "api_key": "your-api-key",
    "model": "gpt-4-vision",
    "base_url": "https://your-endpoint.com/v1"
  }
}
```

---

## Common Custom Endpoints

### Azure OpenAI
```
base_url: https://<resource>.openai.azure.com/v1
```

### Local OpenAI-Compatible (LM Studio, etc.)
```
base_url: http://localhost:8000/v1
```

### Ollama Local
```
base_url: http://localhost:11434
```

---

## Configuration Methods

### Method 1: Edit config.json
```bash
# Edit config.json directly
{
  "OpenAI": {
    "api_key": "...",
    "base_url": "https://custom-endpoint.com/v1"
  }
}
```

### Method 2: GUI Configuration Dialog
1. Launch application
2. Select provider
3. Click "Configure Provider"
4. Enter API key and base URL
5. Click "Test Connection"
6. Click "Save"

---

## Troubleshooting Quick Tips

| Issue | Solution |
|-------|----------|
| Connection Failed | Verify base_url is correct and accessible |
| Model Not Found | Check model name is available on endpoint |
| Auth Error | Verify API key is valid for endpoint |
| No Models Listed | Use "Get Models" button to refresh |

---

## Files to Know

| File | Purpose |
|------|---------|
| `config.json` | Your configuration (don't commit with real keys) |
| `config.example.json` | Example configuration template |
| `gui/config_dialog.py` | Configuration UI |
| `providers/*.py` | Provider implementations |

---

## Key Changes Made

✅ Added custom endpoint support to 7 providers
✅ Fixed Gemini provider API usage
✅ Fixed configuration dialog handling
✅ Updated main_window.py to load custom endpoints
✅ Updated config files with base_url fields

---

## Testing Checklist

- [ ] Test default OpenAI endpoint
- [ ] Test custom OpenAI endpoint
- [ ] Test default Anthropic endpoint
- [ ] Test custom Anthropic endpoint
- [ ] Test Gemini with API key
- [ ] Test model selection for each provider
- [ ] Test "Test Connection" button
- [ ] Test configuration save/load

---

## Important Notes

⚠️ **Security:** Don't commit real API keys to version control
⚠️ **Gemini:** Only supports official Google API (no custom endpoints)
⚠️ **Ollama:** Requires local instance to be running
⚠️ **Rate Limits:** Custom endpoints may have different limits

---

## Support Resources

- `PROVIDER_VERIFICATION_REPORT.md` - Detailed provider info
- `CUSTOM_ENDPOINT_GUIDE.md` - Comprehensive endpoint guide
- `CHANGES_SUMMARY.md` - Technical change details
- `VERIFICATION_COMPLETE.md` - Full verification report

