#!/bin/bash
# Browser Agent - Quick Setup Script

set -e

echo "=========================================="
echo "Browser Agent - Setup"
echo "=========================================="

# Check Python
echo ""
echo "1. Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.12+"
    exit 1
fi
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✓ Python $PYTHON_VERSION"

# Check Ollama
echo ""
echo "2. Checking Ollama..."
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama not found."
    echo ""
    echo "Install with:"
    echo "  macOS: brew install ollama"
    echo "  Linux: curl https://ollama.ai/install.sh | sh"
    echo ""
    echo "Then run: ollama serve"
    exit 1
fi
echo "✓ Ollama installed"

# Check if Ollama is running
echo ""
echo "3. Checking Ollama server..."
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "❌ Ollama server not running"
    echo ""
    echo "Start with: ollama serve"
    echo "(Run in a separate terminal)"
    exit 1
fi
echo "✓ Ollama server running"

# Check/Install recommended model
echo ""
echo "4. Checking AI model..."
if ollama list | grep -q "qwen2.5:14b"; then
    echo "✓ qwen2.5:14b already installed"
else
    echo "Installing recommended model: qwen2.5:14b (9GB download)..."
    echo "This will take several minutes depending on your internet speed."
    echo ""
    ollama pull qwen2.5:14b
    echo "✓ Model installed"
fi

# Create virtual environment
echo ""
echo "5. Setting up Python environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment exists"
fi

# Install dependencies
echo ""
echo "6. Installing dependencies..."
source venv/bin/activate
pip install -q --upgrade pip
pip install -q -e .
echo "✓ Dependencies installed"

# Install Playwright browsers
echo ""
echo "7. Installing browser..."
if ! command -v playwright &> /dev/null; then
    echo "Installing Playwright..."
fi
playwright install chrome 2>&1 | grep -v "is already installed" || true
echo "✓ Chrome browser ready"

# Verify installation
echo ""
echo "8. Verifying installation..."
if browser-agent check > /dev/null 2>&1; then
    echo "✓ Installation verified"
else
    echo "⚠️  Installation complete but verification failed"
    echo "   Run 'browser-agent check' manually to diagnose"
fi

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Quick test:"
echo "  source venv/bin/activate"
echo "  python demo.py"
echo ""
echo "Or run automation:"
echo "  browser-agent run \"Your task here\" --headed"
echo ""
echo "Documentation:"
echo "  README.md    - Quick start"
echo "  INSTALL.md   - Detailed setup"
echo "  STATUS.md    - Current status"
echo ""
