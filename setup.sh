#!/bin/bash

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Setting up Powerloom Snapshotter CLI development environment...${NC}\n"

# Check if pyenv is installed
if ! command -v pyenv &> /dev/null; then
    echo -e "${YELLOW}pyenv not found. Installing...${NC}"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        brew install pyenv pyenv-virtualenv
    else
        # Linux
        curl https://pyenv.run | bash
    fi

    # Add pyenv to shell
    echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
    echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
    echo 'eval "$(pyenv init -)"' >> ~/.zshrc
    echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.zshrc

    # Source the updated profile
    source ~/.zshrc
fi

# Install Python 3.12 if not already installed
if ! pyenv versions | grep -q "3.12"; then
    echo -e "${YELLOW}Installing Python 3.12...${NC}"
    pyenv install 3.12
fi

# Create virtualenv if it doesn't exist
if ! pyenv virtualenvs | grep -q "snapshotter-env"; then
    echo -e "${YELLOW}Creating virtualenv...${NC}"
    pyenv virtualenv 3.12 "snapshotter-env-${RANDOM}"
fi

# Set local Python version
pyenv local "snapshotter-env-${RANDOM}"

# Install/Update pip
python -m pip install --upgrade pip

# Uninstall poetry if exists (to ensure clean install)
if command -v poetry &> /dev/null; then
    echo -e "${YELLOW}Removing existing Poetry installation...${NC}"
    curl -sSL https://install.python-poetry.org | POETRY_UNINSTALL=1 python3 -
fi

# Install latest poetry
echo -e "${YELLOW}Installing latest Poetry...${NC}"
curl -sSL https://install.python-poetry.org | python3 -

# Configure poetry to use virtualenvs in project
poetry config virtualenvs.in-project true

# Install dependencies
echo -e "${YELLOW}Installing project dependencies...${NC}"
poetry install

echo -e "\n${GREEN}✅ Setup complete!${NC}"
echo -e "\nYou can now use the CLI with: ${YELLOW}poetry run powerloom-snapshotter-cli${NC}"
