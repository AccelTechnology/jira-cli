#!/bin/bash

set -e

echo "Installing Jira CLI..."

# Check if Python 3.8+ is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Check Python version
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
required_version="3.8"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    echo "Error: Python 3.8 or higher is required. Found: Python $python_version"
    exit 1
fi

echo "Python version check passed: $python_version"

# Install the package in development mode
echo "Installing jira-cli..."
pip3 install -e .

echo "Installation completed successfully!"
echo ""
echo "Usage:"
echo "  jira-cli --help                 # Show help"
echo "  jira-cli auth test              # Test connection"
echo "  jira-cli epics                  # List epics"
echo "  jira-cli my-issues              # List your issues"
echo "  jira-cli search 'project=ACCELERP' # Search issues"
echo ""
echo "Make sure to set your environment variables:"
echo "  export JIRA_EMAIL=your.email@example.com"
echo "  export JIRA_API_TOKEN=your_api_token"
echo "  export JIRA_URL=https://your-domain.atlassian.net  # Optional"