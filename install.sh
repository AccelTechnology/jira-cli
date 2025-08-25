#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info "Installing Jira CLI for Unix/Linux/macOS..."

# Detect OS
OS="unknown"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]]; then
    OS="windows"
fi

print_info "Detected OS: $OS"

# Check if Python is available (try multiple commands)
PYTHON_CMD=""
for cmd in python3 python3.11 python3.10 python3.9 python3.8 python; do
    if command -v "$cmd" &> /dev/null; then
        # Check if it's actually Python 3
        if "$cmd" -c "import sys; exit(0 if sys.version_info.major == 3 else 1)" 2>/dev/null; then
            PYTHON_CMD="$cmd"
            break
        fi
    fi
done

if [[ -z "$PYTHON_CMD" ]]; then
    print_error "Python 3 is required but not found."
    if [[ "$OS" == "macos" ]]; then
        print_info "Install Python using Homebrew: brew install python3"
        print_info "Or download from: https://www.python.org/downloads/"
    elif [[ "$OS" == "linux" ]]; then
        print_info "Install Python using your package manager:"
        print_info "  Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
        print_info "  CentOS/RHEL: sudo yum install python3 python3-pip"
        print_info "  Arch Linux: sudo pacman -S python python-pip"
    fi
    exit 1
fi

# Check Python version
python_version=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")

if ! $PYTHON_CMD -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    print_error "Python 3.8 or higher is required. Found: Python $python_version"
    print_info "Please upgrade your Python installation."
    exit 1
fi

print_success "Python version check passed: $python_version (using $PYTHON_CMD)"

# Check if pip is available
PIP_CMD=""
for pip_cmd in "$PYTHON_CMD -m pip" pip3 pip; do
    if eval "$pip_cmd --version" &> /dev/null; then
        PIP_CMD="$pip_cmd"
        break
    fi
done

if [[ -z "$PIP_CMD" ]]; then
    print_error "pip is required but not available."
    print_info "Install pip using your package manager or get-pip.py"
    exit 1
fi

print_success "pip found: $PIP_CMD"

# Ask about virtual environment
if [[ -t 0 ]]; then  # Check if we're in an interactive terminal
    echo
    read -p "Do you want to create a virtual environment? (recommended) [Y/n]: " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        CREATE_VENV=false
    else
        CREATE_VENV=true
    fi
else
    # Non-interactive mode, default to creating venv
    CREATE_VENV=true
    print_info "Non-interactive mode: creating virtual environment by default"
fi

# Create virtual environment if requested
if [[ "$CREATE_VENV" == true ]]; then
    print_info "Creating virtual environment..."
    if $PYTHON_CMD -m venv jira-cli-venv; then
        print_success "Virtual environment created successfully"
        
        # Activate virtual environment
        print_info "Activating virtual environment..."
        source jira-cli-venv/bin/activate
        print_success "Virtual environment activated"
        
        # Update PIP_CMD to use the venv pip
        PIP_CMD="python -m pip"
    else
        print_warning "Failed to create virtual environment. Proceeding with global installation."
        CREATE_VENV=false
    fi
fi

# Upgrade pip
print_info "Upgrading pip..."
eval "$PIP_CMD install --upgrade pip" || print_warning "Failed to upgrade pip, continuing..."

# Install the package in development mode
print_info "Installing jira-cli..."
if eval "$PIP_CMD install -e ."; then
    print_success "jira-cli installed successfully!"
else
    print_error "Installation failed!"
    exit 1
fi

# Final instructions
echo
echo "============================================"
print_success "Installation completed successfully!"
echo "============================================"
echo
print_info "Usage:"
echo "  jira-cli --help                           # Show help"
echo "  jira-cli auth test                        # Test connection"
echo "  jira-cli epics                            # List epics"
echo "  jira-cli my-issues                        # List your issues"
echo "  jira-cli search 'project=YOUR_PROJECT'    # Search issues"
echo
print_info "Configuration:"
echo "Set these environment variables in your shell profile (~/.bashrc, ~/.zshrc, etc.):"
echo "  export JIRA_EMAIL=\"your.email@example.com\""
echo "  export JIRA_API_TOKEN=\"your_api_token\""
echo "  export JIRA_URL=\"https://your-domain.atlassian.net\"  # Optional"
echo

if [[ "$CREATE_VENV" == true ]]; then
    print_warning "Virtual environment created in 'jira-cli-venv' directory."
    print_info "To activate it in the future, run:"
    echo "  source jira-cli-venv/bin/activate"
    echo
    print_info "To deactivate the virtual environment, run:"
    echo "  deactivate"
fi

print_info "Get your API token from: https://id.atlassian.com/manage-profile/security/api-tokens"