#!/bin/bash

# Slack MCP Server Installation Script

set -e  # Exit on any error

echo "🚀 Installing Slack MCP Server..."

# Check if Python 3.10+ is available
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.10 or higher is required. Found Python $python_version"
    exit 1
fi

echo "✅ Python $python_version found"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install the package in development mode
echo "📥 Installing slack-mcp-server..."
pip install -e .

echo "✅ Installation complete!"
echo ""
echo "📝 Next steps:"
echo "1. 🔐 Set up credentials securely: slack-mcp-setup"
echo "2. 🧪 Test the installation: python -m slack_mcp"
echo "3. 📋 Add to your Claude Desktop config (see README.md)"
echo ""
echo "🔒 Secure Setup (Recommended):"
echo "   slack-mcp-setup"
echo ""
echo "🔗 Get your Slack API token: https://api.slack.com/apps"