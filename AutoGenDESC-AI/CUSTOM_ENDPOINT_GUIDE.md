# Custom Endpoint Configuration Guide

## Overview
The Vision AI Analysis Tool now supports custom endpoints for OpenAI-compatible and Anthropic-compatible providers. This allows you to use alternative providers, local deployments, or proxy services.

---

## OpenRouter Provider

OpenRouter provides access to 100+ vision models through a single API. It's OpenAI-compatible and supports models from OpenAI, Anthropic, Meta, and more.

```json
{
  "OpenRouter": {
    "api_key": "your-openrouter-api-key",
    "model": "gpt-4-vision-preview",
    "base_url": "https://openrouter.io/api/v1"
  }
}
```

**Get your API key:** https://openrouter.io/keys

**Available Models Include:**
- GPT-4 Vision (OpenAI)
- Claude 3 Opus/Sonnet/Haiku (Anthropic)
- Llama Vision (Meta)
- And 100+ more models

---

## OpenAI-Compatible Providers

### Azure OpenAI
```json
{
  "OpenAI": {
    "api_key": "your-azure-api-key",
    "model": "gpt-4-vision",
    "base_url": "https://<your-resource>.openai.azure.com/v1"
  }
}
```

### Local OpenAI-Compatible Server (e.g., LM Studio, Ollama with OpenAI API)
```json
{
  "OpenAI": {
    "api_key": "not-needed-for-local",
    "model": "your-local-model",
    "base_url": "http://localhost:8000/v1"
  }
}
```

### Third-Party OpenAI-Compatible Provider
```json
{
  "OpenAI": {
    "api_key": "your-provider-api-key",
    "model": "vision-model-name",
    "base_url": "https://api.provider.com/v1"
  }
}
```

---

## Anthropic-Compatible Providers

### Custom Anthropic-Compatible Server
```json
{
  "Anthropic": {
    "api_key": "your-api-key",
    "model": "claude-3-opus-20240229",
    "base_url": "https://custom-provider.com"
  }
}
```

### Local Anthropic-Compatible Deployment
```json
{
  "Anthropic": {
    "api_key": "local-key",
    "model": "claude-3-sonnet-20240229",
    "base_url": "http://localhost:9000"
  }
}
```

---

## Configuration Steps

### 1. Edit config.json
Open `config.json` in your project root and update the provider configuration:

```json
{
  "OpenAI": {
    "api_key": "your-custom-api-key",
    "model": "gpt-4-vision",
    "base_url": "https://your-custom-endpoint.com/v1"
  },
  "Anthropic": {
    "api_key": "your-custom-api-key",
    "model": "claude-3-opus-20240229",
    "base_url": "https://your-custom-endpoint.com"
  }
}
```

### 2. Using the GUI Configuration Dialog
1. Launch the application
2. Select the provider (OpenAI or Anthropic)
3. Click "Configure Provider"
4. Enter your API key
5. Enter your custom base URL in the "Base URL" field
6. Click "Test Connection" to verify
7. Click "Save"

### 3. Verify Configuration
- The configuration is saved to `config.json`
- On next launch, the custom endpoint will be used automatically

---

## Supported Providers with Custom Endpoints

| Provider | Custom Endpoint Support | Use Case |
|----------|------------------------|----------|
| OpenAI | ✅ Yes | Azure OpenAI, Local servers, Proxies |
| Anthropic | ✅ Yes | Custom deployments, Proxies |
| xAI | ✅ Yes | Custom endpoints |
| ZAI | ✅ Yes | Custom endpoints |
| Perplexity | ✅ Yes | Custom endpoints |
| AI Studio | ✅ Yes | Custom endpoints |
| Google Gemini | ❌ No | Uses official Google API only |
| Ollama | ✅ Yes | Local instance URL |

---

## Troubleshooting

### Connection Failed
- Verify the base_url is correct and accessible
- Check that your API key is valid for the custom endpoint
- Ensure the endpoint supports the same API format as the original provider

### Model Not Found
- Verify the model name is available on your custom endpoint
- Check the endpoint's documentation for available models
- Use the "Get Models" button in the configuration dialog to list available models

### Authentication Error
- Verify your API key is correct
- Check if the custom endpoint requires different authentication headers
- Consult the endpoint provider's documentation

---

## Best Practices

1. **Test Before Production**
   - Use "Test Connection" button to verify connectivity
   - Test with a sample image before processing important data

2. **Keep API Keys Secure**
   - Don't commit config.json with real API keys to version control
   - Use environment variables for sensitive data if possible

3. **Monitor Usage**
   - Custom endpoints may have different rate limits
   - Monitor your usage to avoid unexpected costs

4. **Fallback Configuration**
   - Keep a backup of working configurations
   - Document your custom endpoint setup for team members

