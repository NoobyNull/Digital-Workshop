# Vision AI Analysis Tool

A Python desktop application that allows you to analyze images using various AI providers and get structured results in JSON format.

## Features

- **Multiple AI Providers**: Support for OpenAI, Anthropic, Google Gemini, xAI, ZAI, Perplexity, Ollama, and AI Studio
- **GUI Interface**: User-friendly PySide6 interface for image selection and result preview
- **Structured Output**: Returns analysis in JSON format with title, description, and metadata keywords
- **Configuration Management**: Save and manage API keys for different providers
- **Custom Prompts**: Option to provide custom prompts for image analysis

## Installation

1. Clone or download this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

1. Copy `config.example.json` to `config.json`
2. Edit `config.json` and add your API keys for the providers you want to use

Example configuration:
```json
{
  "OpenAI": {
    "api_key": "your-openai-api-key-here",
    "model": "gpt-4-vision-preview"
  },
  "Anthropic": {
    "api_key": "your-anthropic-api-key-here",
    "model": "claude-3-opus-20240229"
  }
}
```

### Provider Setup

#### OpenAI
- Get API key from [OpenAI Platform](https://platform.openai.com/api-keys)
- Requires GPT-4 Vision API access

#### Anthropic
- Get API key from [Anthropic Console](https://console.anthropic.com/)
- Supports Claude 3 models with vision capabilities

#### Google Gemini
- Get API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
- Enable Gemini API in your Google Cloud project

#### xAI
- Get API key from [xAI](https://x.ai/)
- Currently in beta, may require waitlist access

#### ZAI
- Get API key from ZAI platform
- Contact ZAI for access

#### Perplexity
- Get API key from [Perplexity API](https://www.perplexity.ai/settings/api)
- Supports vision-capable models

#### Ollama
- Install [Ollama](https://ollama.ai/) locally
- Pull a vision model: `ollama pull llava`
- No API key required, uses local installation

#### AI Studio
- Get API key from AI Studio platform
- Contact AI Studio for access

## Usage

1. Run the application:
```bash
python main.py
```

2. Select an AI provider from the dropdown menu
3. Configure the provider by clicking "Configure Provider" (if not already configured)
4. Select an image using the "Select Image" button
5. Optionally, enter a custom prompt for analysis
6. Click "Analyze Image" to start the analysis
7. View the results in the right panel

## Output Format

The analysis returns a JSON object with the following structure:

```json
{
  "title": "Generated title for the image",
  "description": "Detailed description of the image content",
  "metadata_keywords": ["keyword1", "keyword2", "keyword3"]
}
```

## Supported Image Formats

- PNG (.png)
- JPEG (.jpg, .jpeg)
- GIF (.gif)
- WebP (.webp)

## Troubleshooting

### Common Issues

1. **Provider not configured**: Make sure you've entered valid API keys in the configuration
2. **Connection timeout**: Check your internet connection and API service status
3. **Ollama not accessible**: Ensure Ollama is running locally on port 11434
4. **Invalid image format**: Use supported image formats

### Debug Mode

To enable debug logging, modify the logging level in `main_window.py`:

```python
logging.basicConfig(level=logging.DEBUG)
```

## Development

### Project Structure

```
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── config.example.json     # Example configuration
├── providers/              # AI provider implementations
│   ├── __init__.py
│   ├── base_provider.py    # Base provider interface
│   ├── openai_provider.py
│   ├── anthropic_provider.py
│   ├── gemini_provider.py
│   ├── xai_provider.py
│   ├── zai_provider.py
│   ├── perplexity_provider.py
│   ├── ollama_provider.py
│   └── aistudio_provider.py
└── gui/                    # GUI components
    ├── __init__.py
    ├── main_window.py      # Main application window
    └── config_dialog.py    # Provider configuration dialog
```

### Adding New Providers

1. Create a new provider class inheriting from `BaseProvider`
2. Implement the required methods: `analyze_image()` and `is_configured()`
3. Add the provider to the providers list in `main_window.py`
4. Update the configuration loading/saving logic

## License

This project is provided as-is for educational and development purposes.

## Contributing

Feel free to submit issues and enhancement requests!