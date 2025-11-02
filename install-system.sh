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

print_info "Installing Jira CLI system-wide..."

# Check for root privileges
if [[ $EUID -eq 0 ]]; then
    SUDO_CMD=""
    print_warning "Running as root. Installing system-wide."
elif command -v sudo &> /dev/null; then
    SUDO_CMD="sudo"
    print_info "Using sudo for system-wide installation."
else
    print_error "This script requires root privileges or sudo access for system-wide installation."
    print_info "Please run with sudo or as root user."
    exit 1
fi

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

# Upgrade pip system-wide
print_info "Upgrading pip..."
eval "$SUDO_CMD $PIP_CMD install --upgrade pip" || print_warning "Failed to upgrade pip, continuing..."

# Install the package system-wide (not in development mode)
print_info "Installing jira-cli system-wide..."
if eval "$SUDO_CMD $PIP_CMD install ."; then
    print_success "jira-cli installed successfully system-wide!"
else
    print_error "Installation failed!"
    exit 1
fi

# Verify installation
print_info "Verifying installation..."
if command -v jira-cli &> /dev/null; then
    INSTALL_LOCATION=$(which jira-cli)
    print_success "jira-cli is available at: $INSTALL_LOCATION"
    
    # Test the command
    if jira-cli --help &> /dev/null; then
        print_success "jira-cli command is working correctly"
    else
        print_warning "jira-cli command installed but may have issues"
    fi
else
    print_error "jira-cli command not found in PATH after installation"
    print_info "You may need to restart your shell or update your PATH"
fi

# Check if user's local bin directory is in PATH (for user installations)
USER_BIN="$HOME/.local/bin"
if [[ ":$PATH:" != *":$USER_BIN:"* ]] && [[ -d "$USER_BIN" ]]; then
    print_warning "Your local bin directory ($USER_BIN) is not in PATH"
    print_info "Add this to your shell profile (~/.bashrc, ~/.zshrc, etc.):"
    echo "  export PATH=\"\$PATH:$USER_BIN\""
fi

# Final instructions
echo
echo "============================================"
print_success "System-wide installation completed!"
echo "============================================"
echo
print_info "Usage:"
echo "  jira-cli --help                           # Show help"
echo "  jira-cli auth test                        # Test connection"
echo "  jira-cli config --setup-help              # Configuration help"
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
print_info "Get your API token from: https://id.atlassian.com/manage-profile/security/api-tokens"
echo
print_info "To uninstall: $SUDO_CMD $PIP_CMD uninstall jira-cli"