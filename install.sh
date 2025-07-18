#!/bin/bash

set -e  # Exit on any error

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Function to run commands without loading shell config
run_clean() {
    env -i HOME="$HOME" PATH="/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin" bash -c "$*"
}

echo -e "${GREEN}🚀 Installing Powerloom Snapshotter CLI...${NC}\n"

# Install SSL dependencies based on OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    if ! command -v brew &> /dev/null; then
        echo -e "${YELLOW}Installing Homebrew...${NC}"
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    echo -e "${YELLOW}Installing SSL dependencies...${NC}"
    run_clean "HOMEBREW_NO_AUTO_UPDATE=1 brew install openssl@3 readline sqlite3 xz zlib"
    run_clean "brew link openssl@3 --force"
else
    # Linux
    echo -e "${YELLOW}Installing SSL dependencies...${NC}"
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y make build-essential libssl-dev zlib1g-dev \
        libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
        libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
    elif command -v yum &> /dev/null; then
        sudo yum install -y gcc zlib-devel bzip2 bzip2-devel readline-devel sqlite \
        sqlite-devel openssl-devel xz xz-devel libffi-devel
    fi
fi

# Check if pyenv is installed and install if needed
if ! command -v pyenv &> /dev/null; then
    echo -e "${YELLOW}Installing pyenv...${NC}"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        run_clean "brew install pyenv pyenv-virtualenv"
    else
        curl https://pyenv.run | bash
    fi

    # Add pyenv to path for current session
    export PYENV_ROOT="$HOME/.pyenv"
    export PATH="$PYENV_ROOT/bin:$PATH"

    # Initialize pyenv for current session
    eval "$(pyenv init --path)"
    eval "$(pyenv init -)"
    eval "$(pyenv virtualenv-init -)"

    # Add to shell config without sourcing
    if [[ "$SHELL" == */zsh ]]; then
        echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
        echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
        echo 'eval "$(pyenv init -)"' >> ~/.zshrc
        echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.zshrc
    else
        echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
        echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
        echo 'eval "$(pyenv init -)"' >> ~/.bashrc
        echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc
    fi
fi

# Remove existing Python installation if SSL is not working
if pyenv versions | grep -q "3.12"; then
    echo -e "${YELLOW}Removing existing Python 3.12 installation to ensure SSL support...${NC}"
    pyenv uninstall -f 3.12
fi

# Install Python 3.12 with SSL support
if ! pyenv versions | grep -q "3.12"; then
    echo -e "${YELLOW}Installing Python 3.12 with SSL support...${NC}"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # Get OpenSSL path
        OPENSSL_PATH=$(brew --prefix openssl@3)

        # Set build flags for SSL support
        export CFLAGS="-I${OPENSSL_PATH}/include -O2"
        export LDFLAGS="-L${OPENSSL_PATH}/lib"
        export PKG_CONFIG_PATH="${OPENSSL_PATH}/lib/pkgconfig"
        export PYTHON_CONFIGURE_OPTS="--enable-optimizations --with-openssl=${OPENSSL_PATH}"

        pyenv install 3.12
    else
        export PYTHON_CONFIGURE_OPTS="--enable-optimizations --with-openssl=$(which openssl)"
        pyenv install 3.12
    fi
fi

# Remove existing virtualenv if it exists
if pyenv virtualenvs | grep -q "powerloom-snapshotter-cli-global"; then
    echo -e "${YELLOW}Removing existing virtualenv...${NC}"
    pyenv uninstall -f powerloom-snapshotter-cli-global
fi

# Create global virtualenv for the CLI
echo -e "${YELLOW}Creating global virtualenv...${NC}"
pyenv virtualenv 3.12 powerloom-snapshotter-cli-global

# Activate the global virtualenv
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
pyenv activate --quiet powerloom-snapshotter-cli-global

# Verify we're using the correct Python version
echo -e "${YELLOW}Verifying Python version...${NC}"
python --version

# Verify SSL support
echo -e "${YELLOW}Verifying SSL support...${NC}"
python -c "import ssl; print(ssl.OPENSSL_VERSION)"

# Install/Update pip
python -m pip install --upgrade pip

# Install poetry if needed
if ! command -v poetry &> /dev/null; then
    echo -e "${YELLOW}Installing Poetry...${NC}"
    curl -sSL https://install.python-poetry.org | python3 -
fi

# Add poetry to PATH for current session
export PATH="$HOME/.local/bin:$PATH"

# Build and install the CLI
echo -e "${YELLOW}Building and installing Snapshotter CLI...${NC}"
poetry build
pip install dist/*.whl

# Create wrapper script
WRAPPER_PATH="/usr/local/bin/powerloom-snapshotter-cli"
echo -e "${YELLOW}Creating wrapper script at ${WRAPPER_PATH}...${NC}"

sudo tee "$WRAPPER_PATH" > /dev/null << 'EOF'
#!/bin/bash
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
pyenv activate --quiet powerloom-snapshotter-cli-global
python -m snapshotter_cli.cli "$@"
EOF

sudo chmod +x "$WRAPPER_PATH"

echo -e "\n${GREEN}✅ Installation complete!${NC}"
echo -e "\nYou may need to restart your terminal or run: ${YELLOW}source ~/.$(basename $SHELL)rc${NC}"
echo -e "Then you can use the CLI anywhere with: ${YELLOW}powerloom-snapshotter-cli${NC}"
echo -e "Try: ${YELLOW}powerloom-snapshotter-cli --help${NC}"
