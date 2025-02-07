#!/bin/bash

GREEN='\033[0;32m' # Green color
NC='\033[0m' # No Color

echo -e "${GREEN}This process might take 10-15 mins depending on VPS specs. Time to grab a coffee! ☕ ${NC}"

# Run apt-get update
echo -e "${GREEN}Updating VPS... Ensuring package lists are up to date.${NC}"
sudo apt-get update -qq -y

# Install Docker and Docker Compose
if ! command -v docker &> /dev/null; then
    echo -e "${GREEN}Installing Docker and Docker Compose...  No Docker? No party. 🐳${NC}"
    sudo apt-get install -y -qq ca-certificates curl && \
    sudo install -m 0755 -d /etc/apt/keyrings && \
    sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc && \
    sudo chmod a+r /etc/apt/keyrings/docker.asc && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
    $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
    sudo tee /etc/apt/sources.list.d/docker.list > /dev/null && \
    sudo apt-get update -qq && \
    sudo apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
else
    echo -e "${GREEN}Docker is already installed.${NC}"
fi

# Install Pip
if ! command -v pip3 &> /dev/null; then
    echo -e "${GREEN}Installing Pip (Python package manager)...${NC}"
    sudo apt install -y -qq python3-pip
else
    echo -e "${GREEN}Pip is already installed.${NC}"
fi

# Install dependencies for Pyenv
echo -e "${GREEN}Installing dependencies for Pyenv...${NC}"
sudo apt update -qq && sudo apt install -y -qq build-essential libssl-dev zlib1g-dev libbz2-dev \
    libreadline-dev libsqlite3-dev curl libncursesw5-dev xz-utils tk-dev libxml2-dev \
    libxmlsec1-dev libffi-dev liblzma-dev

# Install Pyenv
if ! command -v pyenv &> /dev/null; then
    echo -e "${GREEN}Installing Pyenv...${NC}"
    curl https://pyenv.run | bash
else
    echo -e "${GREEN}Pyenv is already installed.${NC}"
fi

# Add Pyenv to Shell Environment
echo -e "${GREEN}Configuring Pyenv...${NC}"
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init --path)"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc

source ~/.bashrc

# Apply Pyenv Configuration Immediately
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

# Check if Python 3.11.5 is already installed
if pyenv versions | grep -q "3.11.5"; then
    echo -e "${GREEN}Python 3.11.5 is already installed. Skipping installation.${NC}"
else
    echo -e "${GREEN}Installing Python 3.11.5 with Pyenv... This might take 10-15 minutes depending on VPS specs. Go touch grass 🌱${NC}"
    pyenv install -v 3.11.5
fi

# Create and activate a virtual environment
echo -e "${GREEN}Setting up a virtual environment for Python 3.11.5...${NC}"
pyenv virtualenv 3.11.5 ss_lite_multi_311
pyenv local ss_lite_multi_311

# Install Python Dependencies
echo -e "${GREEN}Installing required Python packages...${NC}"
pip install --break-system-packages -r requirements.txt

# Success message
echo -e "${GREEN}🎉 All dependencies installed successfully! You're all set🚀. Run these two commands to deploy your nodes! 👇\n\n1) ./bootstrap.sh\n2) python multi_clone.py ${NC}"

exec "$SHELL"