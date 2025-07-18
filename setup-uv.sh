#!/bin/bash

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Setting up Powerloom Snapshotter CLI development environment with uv...${NC}\n"

# Install uv if not already installed
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}Installing uv...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Add uv to PATH for current session
    export PATH="$HOME/.local/bin:$PATH"

    # Add to shell config
    if [[ "$SHELL" == */zsh ]]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
    else
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    fi
else
    echo -e "${GREEN}✓ uv is already installed${NC}"
fi

# Check Python version requirement
echo -e "${YELLOW}Checking Python version...${NC}"
if [ -f ".python-version" ]; then
    PYTHON_VERSION=$(cat .python-version)
    echo -e "Project requires Python ${PYTHON_VERSION}"
else
    echo -e "${YELLOW}Setting Python version to 3.12...${NC}"
    uv python pin 3.12
fi

# Install Python if needed
echo -e "${YELLOW}Installing Python (if needed)...${NC}"
uv python install

# Sync dependencies
echo -e "${YELLOW}Installing project dependencies...${NC}"
uv sync

# Install pre-commit hooks
echo -e "${YELLOW}Installing pre-commit hooks...${NC}"
uv run pre-commit install

# Verify installation
echo -e "\n${YELLOW}Verifying installation...${NC}"
uv run powerloom-snapshotter-cli --version

echo -e "\n${GREEN}✅ Setup complete!${NC}"
echo -e "\nDevelopment commands:"
echo -e "  Run CLI:          ${YELLOW}uv run powerloom${NC}"
echo -e "  Run tests:        ${YELLOW}uv run pytest${NC}"
echo -e "  Format code:      ${YELLOW}./scripts/lint.sh fix${NC}"
echo -e "  Check code:       ${YELLOW}./scripts/lint.sh${NC}"
echo -e "  Build package:    ${YELLOW}uv build${NC}"
echo -e "\nThe virtual environment is in ${YELLOW}.venv/${NC}"
