#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is in use
check_port() {
    if command_exists lsof; then
        lsof -i:"$1" >/dev/null 2>&1
    else
        netstat -tuln | grep -q ":$1 "
    fi
}

# Function to find next available port
find_next_available_port() {
    local port=$1
    while check_port $port; do
        port=$((port + 1))
    done
    echo $port
}

# Function to get all used Docker subnets in 172.18.0.0/16 range
get_used_subnets() {
    local networks="$1"
    echo "$networks" | while read -r network; do
        docker network inspect "$network" 2>/dev/null | grep -o '"Subnet": "172\.18\.[0-9]\+\.0/24"' | cut -d'.' -f3
    done
}

echo "🔍 Starting PowerLoom Node Diagnostics..."

# Phase 1: System Checks
echo -e "\n📦 Checking Docker installation..."
if ! command_exists docker; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}❌ Docker daemon is not running${NC}"
    echo "Please start Docker service"
    exit 1
fi
echo -e "${GREEN}✅ Docker is installed and running${NC}"

# Check docker-compose
echo -e "\n🐳 Checking docker-compose..."
if ! command_exists docker-compose && ! docker compose version >/dev/null 2>&1; then
    echo -e "${RED}❌ Neither docker-compose nor docker compose plugin found${NC}"
    echo "Please install docker-compose or Docker Compose plugin"
    exit 1
fi
echo -e "${GREEN}✅ Docker Compose is available${NC}"

# Check port availability
echo -e "\n🔌 Checking default ports..."
DEFAULT_CORE_API_PORT=8002
DEFAULT_LOCAL_COLLECTOR_PORT=50051

AVAILABLE_CORE_API_PORT=$(find_next_available_port $DEFAULT_CORE_API_PORT)
if [ "$AVAILABLE_CORE_API_PORT" != "$DEFAULT_CORE_API_PORT" ]; then
    echo -e "${YELLOW}⚠️ Port ${DEFAULT_CORE_API_PORT} is in use${NC}"
    echo -e "${GREEN}✅ Next available Core API port: ${AVAILABLE_CORE_API_PORT}${NC}"
fi

AVAILABLE_COLLECTOR_PORT=$(find_next_available_port $DEFAULT_LOCAL_COLLECTOR_PORT)
if [ "$AVAILABLE_COLLECTOR_PORT" != "$DEFAULT_LOCAL_COLLECTOR_PORT" ]; then
    echo -e "${YELLOW}⚠️ Port ${DEFAULT_LOCAL_COLLECTOR_PORT} is in use${NC}"
    echo -e "${GREEN}✅ Next available Collector port: ${AVAILABLE_COLLECTOR_PORT}${NC}"
fi

# Check existing containers and networks
echo -e "\n🔍 Checking existing PowerLoom containers..."
EXISTING_CONTAINERS=$(docker ps -a --filter "name=snapshotter-lite-v2" --filter "name=powerloom" --filter "name=local-collector" --format "{{.Names}}")
if [ -n "$EXISTING_CONTAINERS" ]; then
    echo -e "${YELLOW}Found existing PowerLoom containers:${NC}"
    echo "$EXISTING_CONTAINERS"
fi

echo -e "\n🌐 Checking existing PowerLoom networks..."
EXISTING_NETWORKS=$(docker network ls --filter "name=snapshotter-lite-v2" --format "{{.Name}}")
if [ -n "$EXISTING_NETWORKS" ]; then
    echo -e "${YELLOW}Found existing PowerLoom networks:${NC}"
    echo "$EXISTING_NETWORKS"
fi

# Check Docker subnet usage in 172.18.0.0/16 range
echo -e "\n🌐 Checking Docker subnet usage in 172.18.0.0/16 range..."
NETWORK_LIST=$(docker network ls --format '{{.Name}}')
USED_SUBNETS=$(get_used_subnets "$NETWORK_LIST" | sort -n)
if [ -n "$USED_SUBNETS" ]; then
    echo -e "${YELLOW}Found the following subnets in use:${NC}"
    while read -r octet; do
        echo "172.18.${octet}.0/24"
    done <<< "$USED_SUBNETS"
    
    # Find available subnets
    echo -e "\n${GREEN}First 5 available subnets:${NC}"
    current=0
    count=0
    while [ $count -lt 5 ] && [ $current -lt 256 ]; do
        if ! echo "$USED_SUBNETS" | grep -q "^$current$"; then
            echo "172.18.${current}.0/24"
            count=$((count + 1))
        fi
        current=$((current + 1))
    done
fi

# Check for cloned directories
echo -e "\n📁 Checking for PowerLoom deployment directories..."
# Matches patterns like:
# - powerloom-premainnet-v2-*
# - powerloom-testnet-v2-*
# - powerloom-mainnet-v2-*
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS version
    EXISTING_DIRS=$(find . -maxdepth 1 -type d \( -name "powerloom-premainnet-v2-*" -o -name "powerloom-testnet*" -o -name "powerloom-mainnet-v2-*" \) -exec basename {} \; || true)
else
    # Linux version
    EXISTING_DIRS=$(find . -maxdepth 1 -type d \( -name "powerloom-premainnet-v2-*" -o -name "powerloom-testnet*" -o -name "powerloom-mainnet-v2-*" \) -exec basename {} \; || true)
fi

if [ -n "$EXISTING_DIRS" ]; then
    echo -e "${YELLOW}Found existing PowerLoom deployment directories:${NC}"
    echo "$EXISTING_DIRS"
    read -p "Would you like to remove these directories? (y/n): " remove_dirs
    if [ "$remove_dirs" = "y" ]; then
        echo -e "\n${YELLOW}Removing deployment directories...${NC}"
        echo "$EXISTING_DIRS" | xargs -I {} rm -rf "{}"
        echo -e "${GREEN}✅ Deployment directories removed${NC}"
    fi
fi

# Phase 2: Cleanup Options
echo -e "\n🧹 Cleanup Options:"

if [ -n "$EXISTING_CONTAINERS" ]; then
    read -p "Would you like to stop and remove existing PowerLoom containers? (y/n): " remove_containers
    if [ "$remove_containers" = "y" ]; then
        echo -e "\n${YELLOW}Stopping running containers... (timeout: 30s per container)${NC}"
        # Stop containers with timeout and track failures
        STOP_FAILED=false
        echo "$EXISTING_CONTAINERS" | while read -r container; do
            # Only try to stop if container is running
            if docker ps -q --filter "name=$container" | grep -q .; then
                echo -e "Attempting to stop container ${container}..."
                if ! timeout 35 docker stop --time 30 "$container" 2>/dev/null; then
                    STOP_FAILED=true
                    echo -e "${YELLOW}⚠️ Container ${container} could not be stopped gracefully after 30 seconds${NC}"
                fi
            fi
        done

        echo -e "\n${YELLOW}Removing containers...${NC}"
        echo "$EXISTING_CONTAINERS" | while read -r container; do
            echo -e "Removing container ${container}..."
            if ! docker rm -f "$container" 2>/dev/null; then
                echo -e "${YELLOW}⚠️ Failed to remove container ${container}${NC}"
            fi
        done

        if [ "$STOP_FAILED" = true ]; then
            echo -e "${YELLOW}⚠️ Some containers could not be stopped gracefully and were forcefully removed${NC}"
        fi
    fi
fi

# Check for existing screen sessions
echo -e "\n🖥️ Checking existing PowerLoom screen sessions..."
EXISTING_SCREENS=$(screen -ls | grep -E 'powerloom-(premainnet|testnet|mainnet)-v2|snapshotter' || true)
if [ -n "$EXISTING_SCREENS" ]; then
    echo -e "${YELLOW}Found existing PowerLoom screen sessions:${NC}"
    echo "$EXISTING_SCREENS"
    read -p "Would you like to terminate these screen sessions? (y/n): " kill_screens
    if [ "$kill_screens" = "y" ]; then
        echo -e "\n${YELLOW}Killing screen sessions...${NC}"
        echo "$EXISTING_SCREENS" | cut -d. -f1 | awk '{print $1}' | xargs -r kill
        echo -e "${GREEN}✅ Screen sessions terminated${NC}"
    fi
fi

if [ -n "$EXISTING_NETWORKS" ]; then
    read -p "Would you like to remove existing PowerLoom networks? (y/n): " remove_networks
    if [ "$remove_networks" = "y" ]; then
        echo -e "\n${YELLOW}Removing networks...${NC}"
        NETWORK_REMOVAL_FAILED=false
        
        echo "$EXISTING_NETWORKS" | while read -r network; do
            if ! docker network rm "$network" 2>/dev/null; then
                NETWORK_REMOVAL_FAILED=true
                echo -e "${RED}❌ Failed to remove network ${network}${NC}"
            fi
        done
        
        if [ "$NETWORK_REMOVAL_FAILED" = true ]; then
            echo -e "\n${YELLOW}⚠️  Warning: Some networks could not be removed due to active endpoints.${NC}"
            echo -e "${YELLOW}This usually means there are still some containers using these networks.${NC}"
            echo -e "${YELLOW}A system-wide cleanup might be necessary to remove all resources.${NC}"
        else
            echo -e "${GREEN}✅ Networks removed${NC}"
        fi
    fi
fi

# Add system-wide cleanup option with context-aware message
if [ "$NETWORK_REMOVAL_FAILED" = true ]; then
    echo -e "\n${YELLOW}Due to network removal failures, a system-wide cleanup is recommended.${NC}"
fi

read -p "Would you like to remove unused Docker resources (only unused images, networks, and cache)? (y/n): " deep_clean
if [ "$deep_clean" = "y" ]; then
    echo -e "\n${YELLOW}Removing unused Docker resources...${NC}"
    
    echo -e "\n${YELLOW}Running docker network prune...${NC}"
    docker network prune -f
    
    echo -e "\n${YELLOW}Running docker system prune...${NC}"
    docker system prune -a
    
    echo -e "${GREEN}✅ Cleanup complete${NC}"
fi

echo -e "\n${GREEN}✅ Diagnostic check complete${NC}"
