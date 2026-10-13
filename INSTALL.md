# Installation & Setup Guide

## Prerequisites

### 1. Ollama
```bash
# Already installed at /usr/local/bin/ollama
# Check if running:
curl http://localhost:11434/api/tags

# If not running, start it:
ollama serve

# Verify models:
ollama list

# You have:
# - deepseek-coder:6.7b (working but limited)
# - llama3.2:latest

# Recommended: Install larger model for better performance
ollama pull qwen2.5:14b
# OR
ollama pull llama3.1:70b  # If you have sufficient VRAM
```

### 2. Python
```bash
# You have Python 3.14.8 ✓
python3 --version
```

### 3. Chrome
```bash
# You have Chrome 154.0.8037.98 ✓
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version
```

## Installation

### Step 1: Activate Virtual Environment
```bash
cd /Users/troydaniel/dev/baton
source venv/bin/activate
```

**Already done:** Dependencies are installed, browser-agent CLI is ready.

### Step 2: Verify Installation
```bash
browser-agent check
```

You should see:
- ✓ Ollama is running
- ✓ Available models listed
- ✓ Chrome version displayed

### Step 3: Run Demo
```bash
# Test core functionality (no AI)
python demo.py
```

This will:
- Launch Chrome
- Navigate to example.com and python.org
- Extract page content
- Take screenshots
- Save Playwright trace

### Step 4: Test AI Automation
```bash
# Simple test (will hit model limitations)
browser-agent run "Go to example.com" --headed

# Expected: Loop detection will trigger
# This is normal with deepseek-coder:6.7b
```

## Configuration

### Default Config
Located in `configs/home.yaml`

```yaml
profile_name: home

ollama:
  base_url: http://localhost:11434
  model: deepseek-coder:6.7b  # Change this after installing better model
  timeout: 120

browser:
  headless: false
  max_concurrent_tasks: 3
  default_timeout: 30
  screenshot_on_error: true
```

### To Use Better Model
1. Install model:
   ```bash
   ollama pull qwen2.5:14b
   ```

2. Edit `configs/home.yaml`:
   ```yaml
   ollama:
     model: qwen2.5:14b
   ```

3. Test:
   ```bash
   browser-agent run "Go to example.com and tell me the main heading"
   ```

## Usage Examples

### Basic Commands
```bash
# Visible browser
browser-agent run "Your task here" --headed

# Headless
browser-agent run "Your task here" --headless

# Start from specific URL
browser-agent run "Test the form" --url http://localhost:3000 --headed

# Work profile
browser-agent --profile work run "Task" --url http://internal.company.com

# More steps before timeout
browser-agent run "Complex task" --max-steps 50
```

### Sample Tasks (Once Better Model Installed)
```bash
# Web research
browser-agent run "Go to Python.org and find the latest version"

# Testing
browser-agent run "Test the login form" --url http://localhost:3000 --headed

# Information gathering
browser-agent run "Visit example.com/products and list all items"
```

## Troubleshooting

### Ollama Not Running
```bash
# Start Ollama
ollama serve

# In another terminal, verify:
curl http://localhost:11434/api/tags
```

### Model Not Found
```bash
# List installed models
ollama list

# Install missing model
ollama pull deepseek-coder:6.7b
```

### Chrome Issues
```bash
# Playwright should find Chrome automatically
# If not, reinstall:
playwright install chrome --force
```

### AI Gets Stuck in Loops
This is expected with deepseek-coder:6.7b. Solutions:

1. **Install larger model** (recommended)
   ```bash
   ollama pull qwen2.5:14b
   # Update configs/home.yaml
   ```

2. **Use simpler tasks**
   - Single-step tasks work better
   - Clear, specific instructions
   - Avoid complex reasoning

3. **Run demo.py for manual control**
   - Shows browser automation works
   - Bypasses AI decision-making

### Permission Issues
```bash
# Make sure you're in the virtual environment
source venv/bin/activate

# Reinstall if needed
pip install -e .
```

## Development

### Project Structure
```
baton/
├── browser_agent/       # Main package
│   ├── browser/        # Browser management
│   ├── agent/          # AI agent logic
│   ├── tasks/          # Task models
│   ├── cli/            # CLI commands
│   └── config/         # Configuration
├── configs/            # YAML configs
├── venv/              # Virtual environment
├── demo.py            # Manual demo script
├── README.md          # Main documentation
├── STATUS.md          # Implementation status
└── INSTALL.md         # This file
```

### Running Tests
```bash
# Run manual demo (no AI)
python demo.py

# Run AI test (with model limitations)
browser-agent run "Simple task" --headed

# Check system
browser-agent check
```

### Viewing Results
```bash
# Screenshots
ls -l screenshots/

# Playwright traces (open in browser)
# Visit: https://trace.playwright.dev/
# Upload: traces/home/*.zip

# Or use Playwright CLI:
playwright show-trace traces/home/TASK_ID.zip
```

## Next Steps

1. **Install Better Model** (Highly Recommended)
   ```bash
   ollama pull qwen2.5:14b
   # Edit configs/home.yaml to use it
   ```

2. **Read STATUS.md**
   - Understand current limitations
   - See what's implemented vs planned
   - Review test results

3. **Read README.md**
   - Learn about features
   - See more examples
   - Understand architecture

4. **Experiment**
   - Try different tasks
   - Test with various models
   - Provide feedback via GitHub issues

## Getting Help

- Check README.md for features and examples
- Check STATUS.md for current limitations
- Run `browser-agent check` to verify setup
- Run `demo.py` to test core functionality
- Report issues: https://github.com/anthropics/claude-code/issues

## Uninstallation

```bash
# Deactivate virtual environment
deactivate

# Remove installation
cd /Users/troydaniel/dev
rm -rf baton

# Uninstall Ollama (if desired)
# Manual removal required - see Ollama docs
```

## Security Notes

- Work profile restricts domain access (configured in work.yaml)
- Never store passwords in config files
- Review actions before running on sensitive sites
- Use headless mode carefully (can't see what's happening)
- Audit logs available in work profile (not yet implemented)

## Performance

- Model size affects quality and speed
- Smaller models (6.7B): Fast but limited reasoning
- Medium models (14B): Good balance
- Large models (70B): Best quality, slower

Choose based on your use case:
- Simple tasks: 6.7B might work
- Complex automation: 14B+ recommended
- QA testing: 14B+ recommended
- Production use: 70B+ recommended
