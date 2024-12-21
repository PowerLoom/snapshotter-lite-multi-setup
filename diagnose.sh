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
    docker network ls --format '{{.Name}}' | while read network; do
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
EXISTING_CONTAINERS=$(docker ps -a --filter "name=snapshotter-lite-v2" --format "{{.Names}}")
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
USED_SUBNETS=$(get_used_subnets | sort -n)
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

# Phase 2: Cleanup Options
echo -e "\n🧹 Cleanup Options:"

if [ -n "$EXISTING_CONTAINERS" ]; then
    read -p "Would you like to stop and remove existing PowerLoom containers? (y/n): " remove_containers
    if [ "$remove_containers" = "y" ]; then
        echo -e "\n${YELLOW}Stopping running containers...${NC}"
        docker ps --filter "name=snapshotter-lite-v2" -q | xargs -r docker stop
        
        echo -e "\n${YELLOW}Removing stopped containers...${NC}"
        docker ps -a --filter "name=snapshotter-lite-v2" -q | xargs -r docker rm
        
        echo -e "${GREEN}✅ Containers stopped and removed${NC}"
    fi
fi

# Check for existing screen sessions
echo -e "\n🖥️ Checking existing PowerLoom screen sessions..."
EXISTING_SCREENS=$(screen -ls | grep 'powerloom-premainnet-v2' || true)
if [ -n "$EXISTING_SCREENS" ]; then
    echo -e "${YELLOW}Found existing PowerLoom screen sessions:${NC}"
    echo "$EXISTING_SCREENS"
    read -p "Would you like to terminate these screen sessions? (y/n): " kill_screens
    if [ "$kill_screens" = "y" ]; then
        echo -e "\n${YELLOW}Killing screen sessions...${NC}"
        screen -ls | grep powerloom-premainnet-v2 | cut -d. -f1 | awk '{print $1}' | xargs -r kill
        echo -e "${GREEN}✅ Screen sessions terminated${NC}"
    fi
fi

if [ -n "$EXISTING_NETWORKS" ]; then
    read -p "Would you like to remove existing PowerLoom networks? (y/n): " remove_networks
    if [ "$remove_networks" = "y" ]; then
        echo -e "\n${YELLOW}Removing networks...${NC}"
        NETWORK_REMOVAL_FAILED=false
        
        while read -r network_id; do
            if ! docker network rm "$network_id" 2>/dev/null; then
                NETWORK_REMOVAL_FAILED=true
                network_name=$(docker network ls --format '{{.Name}}' --filter "id=$network_id")
                echo -e "${RED}❌ Failed to remove network ${network_name}${NC}"
            fi
        done < <(docker network ls --filter "name=snapshotter-lite-v2" -q)
        
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

read -p "Would you like to perform a system-wide Docker cleanup (this will remove all unused containers, networks, images, and cache)? (y/n): " deep_clean
if [ "$deep_clean" = "y" ]; then
    echo -e "\n${YELLOW}Performing system-wide Docker cleanup...${NC}"
    echo -e "${YELLOW}This might take a few minutes...${NC}"
    
    echo -e "\n${YELLOW}Stopping all containers...${NC}"
    docker ps -q | xargs -r docker stop
    
    echo -e "\n${YELLOW}Running docker system prune...${NC}"
    docker system prune -af --volumes
    
    echo -e "${GREEN}✅ System-wide cleanup complete${NC}"
fi

echo -e "\n${GREEN}✅ Diagnostic check complete${NC}"
