# Environment Variable Setup Guide

## Why Environment Variables?

Environment variables are the **recommended way** to provide API keys because:
- ✅ Keys are NOT stored in configuration files
- ✅ Keys are NOT committed to version control
- ✅ Keys are NOT visible in preferences UI
- ✅ Keys are NOT logged to files
- ✅ Different keys for different environments (dev, staging, prod)

## Setting Up Environment Variables

### Windows Command Prompt

**Temporary (current session only):**
```bash
set GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY
python main.py
```

**Permanent (system-wide):**
1. Press `Win + X` → Select "System"
2. Click "Advanced system settings"
3. Click "Environment Variables"
4. Under "User variables", click "New"
5. Variable name: `GOOGLE_API_KEY`
6. Variable value: `YOUR_GOOGLE_API_KEY`
7. Click OK and restart your terminal/IDE

**Verify it's set:**
```bash
echo %GOOGLE_API_KEY%
```

### Windows PowerShell

**Temporary (current session only):**
```powershell
$env:GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY"
python main.py
```

**Permanent (user profile):**
1. Open PowerShell as Administrator
2. Run:
```powershell
[Environment]::SetEnvironmentVariable("GOOGLE_API_KEY", "YOUR_GOOGLE_API_KEY", "User")
```
3. Restart PowerShell

**Verify it's set:**
```powershell
$env:GOOGLE_API_KEY
```

### Linux/Mac

**Temporary (current session only):**
```bash
export GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY
python main.py
```

**Permanent (add to shell profile):**

For Bash (~/.bashrc or ~/.bash_profile):
```bash
echo 'export GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY' >> ~/.bashrc
source ~/.bashrc
```

For Zsh (~/.zshrc):
```bash
echo 'export GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY' >> ~/.zshrc
source ~/.zshrc
```

**Verify it's set:**
```bash
echo $GOOGLE_API_KEY
```

## Using with IDEs

### Visual Studio Code

**Method 1: Launch Configuration (.vscode/launch.json)**
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Digital Workshop",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/main.py",
            "console": "integratedTerminal",
            "env": {
                "GOOGLE_API_KEY": "YOUR_GOOGLE_API_KEY"
            }
        }
    ]
}
```

**Method 2: .env File**
1. Create `.env` file in project root:
```
GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY
```

2. Install python-dotenv:
```bash
pip install python-dotenv
```

3. Add to main.py (before imports):
```python
from dotenv import load_dotenv
load_dotenv()
```

### PyCharm

1. Go to Run → Edit Configurations
2. Select your Python configuration
3. Click "Environment variables" field
4. Add: `GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY`
5. Click OK

### Jupyter Notebook

```python
import os
os.environ['GOOGLE_API_KEY'] = 'YOUR_GOOGLE_API_KEY'

# Now run your code
```

## Multiple API Keys

You can set multiple provider keys:

**Windows Command Prompt:**
```bash
set GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY
set OPENAI_API_KEY=sk-...
set ANTHROPIC_API_KEY=sk-ant-...
python main.py
```

**Linux/Mac:**
```bash
export GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
python main.py
```

## Supported Environment Variables

| Provider | Environment Variable | Example |
|----------|----------------------|---------|
| Google Gemini | `GOOGLE_API_KEY` | `AIzaSyB...` |
| OpenAI | `OPENAI_API_KEY` | `sk-...` |
| Anthropic | `ANTHROPIC_API_KEY` | `sk-ant-...` |
| OpenRouter | `OPENROUTER_API_KEY` | `sk-or-...` |

## Batch File (Windows)

Create `run_app.bat`:
```batch
@echo off
set GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY
python main.py
pause
```

Then double-click `run_app.bat` to run the app.

## Shell Script (Linux/Mac)

Create `run_app.sh`:
```bash
#!/bin/bash
export GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY
python main.py
```

Make executable and run:
```bash
chmod +x run_app.sh
./run_app.sh
```

## Docker

In your Dockerfile:
```dockerfile
ENV GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY
```

Or pass at runtime:
```bash
docker run -e GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY my-app
```

## Verification

### Check if Variable is Set

**Windows:**
```bash
echo %GOOGLE_API_KEY%
```

**Linux/Mac:**
```bash
echo $GOOGLE_API_KEY
```

### Test with Application

```bash
python tests/test_gemini_key.py
```

If environment variable is set, it will use it automatically.

## Troubleshooting

### "API key not configured" Error

**Check 1:** Verify environment variable is set
```bash
# Windows
echo %GOOGLE_API_KEY%

# Linux/Mac
echo $GOOGLE_API_KEY
```

**Check 2:** Restart terminal/IDE after setting variable

**Check 3:** Verify variable name is exactly `GOOGLE_API_KEY` (case-sensitive on Linux/Mac)

**Check 4:** Check for extra spaces:
```bash
# ❌ Wrong (has space)
set GOOGLE_API_KEY = AIzaSyB...

# ✅ Correct (no space)
set GOOGLE_API_KEY=AIzaSyB...
```

### Variable Not Persisting

**Windows:** Use System Properties (not just Command Prompt)
- Win + X → System → Advanced system settings → Environment Variables

**Linux/Mac:** Add to shell profile (~/.bashrc, ~/.zshrc, etc.)

### Multiple Terminals

Each terminal session needs the variable set. Use permanent setup (system-wide or shell profile) to avoid this.

## Security Best Practices

⚠️ **IMPORTANT:**
1. **Never commit .env files** to version control
2. **Add .env to .gitignore**:
   ```
   .env
   .env.local
   *.env
   ```
3. **Use different keys** for different environments
4. **Rotate keys regularly** for security
5. **Monitor API usage** to detect unauthorized access
6. **Use API key restrictions** in Google Cloud Console

## Next Steps

1. Set your `GOOGLE_API_KEY` environment variable
2. Restart your terminal/IDE
3. Run the application
4. Test with "Run AI Analysis" button
5. Verify it works!

