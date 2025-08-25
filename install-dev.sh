#!/bin/bash

# Developer installation script with additional tools

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

print_info "Installing Jira CLI for development..."

# Check if Python is available
PYTHON_CMD=""
for cmd in python3 python3.11 python3.10 python3.9 python3.8 python; do
    if command -v "$cmd" &> /dev/null; then
        if "$cmd" -c "import sys; exit(0 if sys.version_info.major == 3 and sys.version_info >= (3, 8) else 1)" 2>/dev/null; then
            PYTHON_CMD="$cmd"
            break
        fi
    fi
done

if [[ -z "$PYTHON_CMD" ]]; then
    print_error "Python 3.8+ is required but not found."
    exit 1
fi

print_success "Using Python: $PYTHON_CMD"

# Create virtual environment
print_info "Creating virtual environment for development..."
$PYTHON_CMD -m venv venv
source venv/bin/activate

print_info "Installing dependencies..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

print_info "Installing development dependencies..."
python -m pip install black isort flake8 pytest pytest-cov mypy

print_info "Installing jira-cli in development mode..."
python -m pip install -e .

print_success "Development environment setup complete!"
echo
print_info "To activate the virtual environment:"
echo "  source venv/bin/activate"
echo
print_info "Development commands:"
echo "  black src/           # Format code"
echo "  isort src/           # Sort imports"
echo "  flake8 src/          # Lint code"
echo "  pytest               # Run tests"
echo "  mypy src/            # Type checking"