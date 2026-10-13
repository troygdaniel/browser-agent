# Browser Agent

> **For AI Agents:** This is a **self-learning, self-healing** browser automation tool. AI figures out tasks on first run (slow), saves them as fast recipes (2-3 seconds), and auto-heals when websites change. Think Playwright Test Recorder + AI that fixes broken tests.

**Self-learning browser automation:** AI learns tasks once, replays them fast forever.

## How It Works

**First Time (AI Learning):**
```bash
browser-agent run "Create ServiceNow CR from CHG0012345"
```
- 🤖 AI figures it out (slow, ~30s)
- 💾 Saves recipe automatically
- ✅ Done!

**Every Time After (Fast Recipe):**
```bash
browser-agent run servicenow-create-cr --chg_number CHG0067890
```
- ⚡ Replays recipe (2-3 seconds)
- 🎯 No AI needed
- 🔧 Auto-heals if website changes

## Features

- **Self-Learning** - AI learns tasks once, replays forever
- **Self-Healing** - Automatically fixes broken recipes when websites change
- **Fast Execution** - 2-3 seconds vs 30+ seconds for AI
- **Recipe Library** - Build reusable automation recipes
- **Variable Substitution** - Use same recipe with different inputs
- **Local AI** - Uses Ollama (optional: use Claude/GPT via API)
- **Chrome Automation** - Playwright-based browser control
- **Home/Work Profiles** - Separate configurations

## Quick Start

### One-Command Setup (Recommended)

```bash
git clone https://github.com/troygdaniel/browser-agent.git
cd browser-agent
./setup.sh
```

This will:
- ✓ Check Python 3.12+
- ✓ Check Ollama installation
- ✓ Download recommended AI model (qwen2.5:14b, 9GB)
- ✓ Install Python dependencies
- ✓ Install Chrome browser
- ✓ Verify everything works

### Manual Setup

### 1. Install Prerequisites

**Ollama (local AI):**
```bash
# macOS
brew install ollama

# Start Ollama server
ollama serve

# Pull model (in another terminal)
ollama pull deepseek-coder:6.7b
```

**Python 3.12+:**
```bash
python3 --version  # Should be 3.12 or higher
```

### 2. Install Browser Agent

```bash
# Clone or navigate to the project directory
cd /path/to/baton

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e .

# Install Playwright browsers
playwright install chrome
```

### 3. Check System

```bash
browser-agent check
```

You should see:
- ✓ Ollama is running
- ✓ Chrome available
- List of installed models

### 4. Run Your First Task

**Simple web search:**
```bash
browser-agent run "Go to Google and search for Python tutorials"
```

**Test a local app:**
```bash
browser-agent run "Test the login workflow" --url http://localhost:3000 --headed
```

**Information gathering:**
```bash
browser-agent run "Visit example.com and tell me what products they offer" --headed
```

## Usage

### Basic Commands

**Run a task (visible browser):**
```bash
browser-agent run "Your task description" --headed
```

**Run a task (headless):**
```bash
browser-agent run "Your task description" --headless
```

**Start from specific URL:**
```bash
browser-agent run "Test the checkout flow" --url https://example.com --headed
```

**Use work profile:**
```bash
browser-agent --profile work run "Test internal app" --url http://localhost:8080
```

**Limit steps:**
```bash
browser-agent run "Complex task" --max-steps 50
```

### Configuration Profiles

**Home Profile** (`configs/home.yaml`):
- Visible browser by default
- No domain restrictions
- Full automation capabilities
- For personal use

**Work Profile** (`configs/work.yaml`):
- Headless by default
- Domain allowlist
- Audit logging
- Restricted filesystem access
- For corporate use

Edit these files to customize behavior.

## Examples

### Web Research
```bash
browser-agent run "Find the latest Python release notes and summarize them"
```

### QA Testing
```bash
browser-agent run "Test the login form" --url http://localhost:3000 --headed
```

### Data Collection
```bash
browser-agent run "Go to example.com/products and list all product names"
```

### Navigation
```bash
browser-agent run "Navigate to GitHub, search for 'playwright', and open the first result"
```

## How It Works

1. **Browser Manager** - Launches Chrome via Playwright with isolated sessions
2. **AI Agent** - Uses local Ollama to decide next actions
3. **Executor** - Executes actions (click, type, navigate, etc.)
4. **Task Loop** - Continues until task completes or needs attention

### Agent Actions

The AI can perform these actions:
- `navigate` - Go to URL
- `click` - Click element
- `type` - Enter text
- `wait` - Pause briefly
- `scroll` - Scroll page
- `complete` - Task finished
- `needs_attention` - Requires human help

### Human Intervention

If the agent encounters:
- Login/authentication
- CAPTCHA
- MFA
- Unexpected errors

It will pause and mark the task as "needs attention."

## Project Structure

```
baton/
├── browser_agent/
│   ├── browser/         # Browser management
│   ├── agent/           # AI agent logic
│   ├── tasks/           # Task models
│   ├── cli/             # Command-line interface
│   └── config/          # Configuration
├── configs/
│   ├── home.yaml        # Home profile
│   └── work.yaml        # Work profile
├── screenshots/         # Error screenshots
├── traces/              # Playwright traces
└── requirements.txt
```

## Development Status

### ✅ Phase 1 - Working Browser Agent
- Chrome automation
- Ollama integration
- Basic agent loop
- CLI with `run` command
- Visible/headless modes
- Configuration profiles

### 🚧 Phase 2 - Background Execution (Planned)
- Persistent task runner
- SQLite task storage
- Concurrent task execution
- Status/logs commands
- Task cancellation

### 🚧 Phase 3 - Human Intervention (Planned)
- Pause/resume capability
- Browser takeover
- Authentication handling

### 🚧 Phase 4 - QA Testing (Planned)
- Exploratory testing mode
- Defect detection
- HTML reports

### 🚧 Phase 5 - Multi-Agent Integration (Planned)
- HTTP API for task monitoring
- Integration with external workboards

## Troubleshooting

### Ollama not available
```bash
# Make sure Ollama is running
ollama serve

# Check if model is installed
ollama list

# Install if needed
ollama pull deepseek-coder:6.7b
```

### Playwright/Chrome issues
```bash
# Reinstall browsers
playwright install chrome

# Check Chrome
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version
```

### Task not completing
- Try increasing `--max-steps`
- Check screenshots in `screenshots/` directory
- Check Playwright trace in `traces/` directory
- Use `--headed` to watch what's happening

### AI making wrong decisions
- Smaller models (6.7B) may struggle with complex tasks
- Consider installing larger model:
  ```bash
  ollama pull qwen2.5:14b
  ```
- Update `configs/home.yaml` to use the new model

## Future Enhancements

- [ ] Background task execution
- [ ] Concurrent multi-task support
- [ ] Persistent sessions (saved logins)
- [ ] QA testing mode with defect reports
- [ ] HTML result reports
- [ ] HTTP API for integration
- [ ] MCP server for AI agent integration
- [ ] Vision model support for screenshot analysis
- [ ] Better error recovery
- [ ] Domain-specific prompt templates

## License

MIT

## Contributing

This is a personal project. Feel free to fork and adapt for your needs.

## Safety & Security

⚠️ **Important:**
- Never use work profile without organizational approval
- Don't automate CAPTCHA solving or authentication bypasses
- Respect website terms of service
- Don't store plaintext passwords in configs
- Review automation actions before deploying

## Credits

Built with:
- [Playwright](https://playwright.dev/) - Browser automation
- [Ollama](https://ollama.ai/) - Local AI inference
- [Typer](https://typer.tiangolo.com/) - CLI framework
- [Rich](https://rich.readthedocs.io/) - Terminal formatting
