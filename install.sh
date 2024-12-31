#!/bin/bash

set -e  # Exit on any error

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🚀 Installing PowerLoom Snapshotter CLI...${NC}\n"

# Install SSL dependencies based on OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    if ! command -v brew &> /dev/null; then
        echo -e "${YELLOW}Installing Homebrew...${NC}"
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    echo -e "${YELLOW}Installing SSL dependencies...${NC}"
    brew install openssl readline sqlite3 xz zlib
else
    # Linux
    echo -e "${YELLOW}Installing SSL dependencies...${NC}"
    if command -v apt-get &> /dev/null; then
        # Debian/Ubuntu
        sudo apt-get update
        sudo apt-get install -y make build-essential libssl-dev zlib1g-dev \
        libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
        libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
    elif command -v yum &> /dev/null; then
        # CentOS/RHEL
        sudo yum install -y gcc zlib-devel bzip2 bzip2-devel readline-devel sqlite \
        sqlite-devel openssl-devel xz xz-devel libffi-devel
    fi
fi

# Check if pyenv is installed and install if needed
if ! command -v pyenv &> /dev/null; then
    echo -e "${YELLOW}Installing pyenv...${NC}"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install pyenv pyenv-virtualenv
    else
        curl https://pyenv.run | bash
        
        # Add to path for current session
        export PYENV_ROOT="$HOME/.pyenv"
        export PATH="$PYENV_ROOT/bin:$PATH"
        eval "$(pyenv init -)"
        eval "$(pyenv virtualenv-init -)"
        
        # Add to shell config
        echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
        echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
        echo 'eval "$(pyenv init -)"' >> ~/.bashrc
        echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc
    fi
fi

# Reload shell configuration
if [[ "$OSTYPE" == "darwin"* ]]; then
    source ~/.zshrc
else
    source ~/.bashrc
fi

# Install Python 3.8 with SSL support
if ! pyenv versions | grep -q "3.8"; then
    echo -e "${YELLOW}Installing Python 3.8...${NC}"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        CFLAGS="-I$(brew --prefix openssl)/include" \
        LDFLAGS="-L$(brew --prefix openssl)/lib" \
        pyenv install 3.8
    else
        pyenv install 3.8
    fi
fi

# Create global virtualenv for the CLI
if ! pyenv virtualenvs | grep -q "snapshotter-cli-global"; then
    echo -e "${YELLOW}Creating global virtualenv...${NC}"
    pyenv virtualenv 3.8 snapshotter-cli-global
fi

# Activate the global virtualenv
eval "$(pyenv init -)"
pyenv shell snapshotter-cli-global

# Install/Update pip with SSL support
python -m pip install --upgrade pip --trusted-host pypi.org --trusted-host files.pythonhosted.org

# Install poetry if needed
if ! command -v poetry &> /dev/null; then
    echo -e "${YELLOW}Installing Poetry...${NC}"
    curl -sSL https://install.python-poetry.org | python3 -
fi

# Build and install the CLI
echo -e "${YELLOW}Building and installing Snapshotter CLI...${NC}"
poetry build
pip install dist/*.whl --trusted-host pypi.org --trusted-host files.pythonhosted.org

# Create wrapper script
WRAPPER_PATH="/usr/local/bin/snapshotter-cli"
echo -e "${YELLOW}Creating wrapper script at ${WRAPPER_PATH}...${NC}"

sudo tee "$WRAPPER_PATH" > /dev/null << 'EOF'
#!/bin/bash
eval "$(pyenv init -)"
pyenv shell snapshotter-cli-global
python -m snapshotter_cli.cli "$@"
EOF

sudo chmod +x "$WRAPPER_PATH"

echo -e "\n${GREEN}✅ Installation complete!${NC}"
echo -e "\nYou can now use the CLI anywhere with: ${YELLOW}snapshotter-cli${NC}"
echo -e "Try: ${YELLOW}snapshotter-cli --help${NC}" 