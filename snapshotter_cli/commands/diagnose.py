import os
import subprocess
from typing import List, Tuple
import psutil
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def check_sudo_access() -> bool:
    """Check if we have sudo access."""
    try:
        subprocess.run(['sudo', '-n', 'true'], capture_output=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def run_with_sudo(command: List[str], **kwargs) -> subprocess.CompletedProcess:
    """Run a command with sudo if necessary."""
    try:
        # Try without sudo first
        return subprocess.run(command, **kwargs, check=True)
    except (subprocess.CalledProcessError, PermissionError):
        # If failed, try with sudo
        if not check_sudo_access():
            console.print("⚠️  Docker commands require sudo access", style="yellow")
            if not typer.confirm("Would you like to proceed with sudo?"):
                raise typer.Abort()
        return subprocess.run(['sudo'] + command, **kwargs, check=True)

def check_command_exists(command: str) -> bool:
    """Check if a command exists in the system."""
    try:
        subprocess.run(['which', command], capture_output=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def check_docker_status() -> Tuple[bool, str]:
    """Check if Docker is installed and running."""
    if not check_command_exists('docker'):
        return False, "Docker is not installed"
    
    try:
        run_with_sudo(['docker', 'info'], capture_output=True)
        return True, "Docker is installed and running"
    except subprocess.CalledProcessError:
        return False, "Docker daemon is not running"

def check_docker_compose() -> Tuple[bool, str]:
    """Check if docker-compose is available."""
    if check_command_exists('docker-compose'):
        return True, "docker-compose is available"
    
    try:
        run_with_sudo(['docker', 'compose', 'version'], capture_output=True)
        return True, "Docker Compose plugin is available"
    except subprocess.CalledProcessError:
        return False, "Neither docker-compose nor Docker Compose plugin found"

def check_port_in_use(port: int) -> bool:
    """Check if a port is in use."""
    try:
        for conn in psutil.net_connections(kind='inet'):
            if conn.laddr.port == port:
                return True
        return False
    except psutil.AccessDenied:
        # Fall back to using sudo netstat if psutil needs elevated privileges
        try:
            result = run_with_sudo(['netstat', '-tuln'], capture_output=True, text=True)
            return f":{port}" in result.stdout
        except subprocess.CalledProcessError:
            console.print(f"⚠️  Unable to check port {port}", style="yellow")
            return False

def find_next_available_port(start_port: int) -> int:
    """Find the next available port starting from start_port."""
    port = start_port
    while check_port_in_use(port):
        port += 1
    return port

def get_powerloom_containers() -> List[str]:
    """Get list of PowerLoom containers."""
    try:
        # Create a list of filters for different container name patterns
        filters = [
            'name=snapshotter-lite-v2',
            'name=powerloom-premainnet-',
            'name=powerloom-testnet-',
            'name=powerloom-mainnet-',
            'name=local-collector'
        ]
        # Run docker ps with multiple filters
        result = run_with_sudo(
            ['docker', 'ps', '-a'] + sum([['--filter', f] for f in filters], []),
            capture_output=True, text=True
        )
        return [line for line in result.stdout.split('\n') if line]
    except subprocess.CalledProcessError:
        return []

def get_powerloom_networks() -> List[str]:
    """Get list of PowerLoom networks."""
    try:
        result = run_with_sudo(
            ['docker', 'network', 'ls', '--filter', 'name=snapshotter-lite-v2', '--format', '{{.Name}}'],
            capture_output=True, text=True
        )
        return [line for line in result.stdout.split('\n') if line]
    except subprocess.CalledProcessError:
        return []

def cleanup_resources(force: bool = False) -> None:
    """Clean up Docker resources."""
    containers = get_powerloom_containers()
    networks = get_powerloom_networks()
    
    if containers and (force or typer.confirm("Would you like to stop and remove existing PowerLoom containers?")):
        console.print("Stopping and removing containers...", style="yellow")
        for container in containers:
            try:
                run_with_sudo(['docker', 'stop', container], capture_output=True)
                run_with_sudo(['docker', 'rm', container], capture_output=True)
                console.print(f"✅ Removed container: {container}", style="green")
            except subprocess.CalledProcessError as e:
                console.print(f"⚠️  Failed to remove container {container}: {e}", style="red")
                continue
        console.print("Container cleanup completed", style="green")

    if networks and (force or typer.confirm("Would you like to remove PowerLoom networks?")):
        console.print("Removing networks...", style="yellow")
        for network in networks:
            try:
                run_with_sudo(['docker', 'network', 'rm', network], capture_output=True)
                console.print(f"✅ Removed network: {network}", style="green")
            except subprocess.CalledProcessError as e:
                console.print(f"⚠️  Failed to remove network {network}: {e}", style="red")
                continue
        console.print("Network cleanup completed", style="green")

def run_diagnostics(clean: bool = False, force: bool = False) -> None:
    """Run system diagnostics and optionally clean up resources."""
    # Check Docker installation and status
    docker_ok, docker_msg = check_docker_status()
    console.print(Panel(f"Docker Status: {docker_msg}", style="green" if docker_ok else "red"))
    if not docker_ok:
        return

    # Check Docker Compose
    compose_ok, compose_msg = check_docker_compose()
    console.print(Panel(f"Docker Compose Status: {compose_msg}", style="green" if compose_ok else "red"))
    if not compose_ok:
        return

    # Check ports
    ports_table = Table(title="Port Status")
    ports_table.add_column("Service")
    ports_table.add_column("Default Port")
    ports_table.add_column("Status")
    ports_table.add_column("Next Available")

    for service, port in [("Core API", 8002), ("Local Collector", 50051)]:
        in_use = check_port_in_use(port)
        next_port = find_next_available_port(port) if in_use else port
        ports_table.add_row(
            service,
            str(port),
            "In Use" if in_use else "Available",
            str(next_port) if in_use else "-"
        )
    
    console.print(ports_table)

    # Show existing resources
    if containers := get_powerloom_containers():
        console.print("\nExisting PowerLoom containers:", style="yellow")
        for container in containers:
            console.print(f"  • {container}")

    if networks := get_powerloom_networks():
        console.print("\nExisting PowerLoom networks:", style="yellow")
        for network in networks:
            console.print(f"  • {network}")

    # Clean up if requested
    if clean or (containers or networks):
        cleanup_resources(force)

def diagnose_command(clean: bool = False, force: bool = False):
    """CLI command handler for diagnose."""
    console.print("🔍 Running PowerLoom Snapshotter Node Diagnostics...", style="bold blue")
    run_diagnostics(clean, force)
