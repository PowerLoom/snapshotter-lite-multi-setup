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

# Install uv
if ! command -v uv &> /dev/null; then
    echo -e "${GREEN}Installing uv (fast Python package manager)...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Add uv to PATH for current session
    export PATH="$HOME/.local/bin:$PATH"

    # Add to shell config for future sessions
    if [[ "$SHELL" == */zsh ]]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
    else
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    fi
else
    echo -e "${GREEN}uv is already installed.${NC}"
fi

# Make sure uv is in PATH
export PATH="$HOME/.local/bin:$PATH"

# Install Powerloom Snapshotter CLI and dependencies
echo -e "${GREEN}Installing Powerloom Snapshotter CLI and dependencies...${NC}"
./install-uv.sh

# Success message
echo -e "${GREEN}🎉 All dependencies installed successfully! You're all set🚀. Run these two commands to deploy your nodes! 👇\n\n1) ./bootstrap.sh\n2) uv run python multi_clone.py ${NC}"
