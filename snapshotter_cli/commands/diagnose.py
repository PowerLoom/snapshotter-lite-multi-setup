import os
import subprocess
from typing import Dict, List, Tuple

import typer
from rich.panel import Panel

from snapshotter_cli.utils.console import console


def check_sudo_access() -> bool:
    """Check if we have sudo access."""
    try:
        subprocess.run(["sudo", "-n", "true"], capture_output=True, check=True)
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
        return subprocess.run(["sudo"] + command, **kwargs, check=True)


def check_command_exists(command: str) -> bool:
    """Check if a command exists in the system."""
    try:
        subprocess.run(["which", command], capture_output=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def check_docker_status() -> Tuple[bool, str]:
    """Check if Docker is installed and running."""
    if not check_command_exists("docker"):
        return False, "Docker is not installed"

    try:
        run_with_sudo(["docker", "info"], capture_output=True)
        return True, "Docker is installed and running"
    except subprocess.CalledProcessError:
        return False, "Docker daemon is not running"


def check_docker_compose() -> Tuple[bool, str]:
    """Check if docker-compose is available."""
    if check_command_exists("docker-compose"):
        return True, "docker-compose is available"

    try:
        run_with_sudo(["docker", "compose", "version"], capture_output=True)
        return True, "Docker Compose plugin is available"
    except subprocess.CalledProcessError:
        return False, "Neither docker-compose nor Docker Compose plugin found"


def get_powerloom_containers() -> List[Dict[str, str]]:
    """Get list of Powerloom containers with their IDs and names."""
    try:
        # Create a list of filters for different container name patterns
        filters = [
            "name=snapshotter-lite-v2",
            "name=powerloom-premainnet-",
            "name=powerloom-testnet-",
            "name=powerloom-mainnet-",
            "name=local-collector",
        ]
        # Run docker ps with multiple filters and format to get just ID and name
        result = run_with_sudo(
            ["docker", "ps", "-a", "--format", "{{.ID}}\t{{.Names}}"]
            + sum([["--filter", f] for f in filters], []),
            capture_output=True,
            text=True,
        )
        containers = []
        for line in result.stdout.strip().split("\n"):
            if line:
                container_id, container_name = line.strip().split("\t")
                containers.append(
                    {"id": container_id.strip(), "name": container_name.strip()}
                )
        return containers
    except subprocess.CalledProcessError:
        return []


def get_powerloom_networks() -> List[str]:
    """Get list of Powerloom networks."""
    try:
        result = run_with_sudo(
            [
                "docker",
                "network",
                "ls",
                "--filter",
                "name=snapshotter-lite-v2",
                "--format",
                "{{.Name}}",
            ],
            capture_output=True,
            text=True,
        )
        return [line for line in result.stdout.split("\n") if line]
    except subprocess.CalledProcessError:
        return []


def get_powerloom_screen_sessions() -> List[Dict[str, str]]:
    """Get list of Powerloom screen sessions."""
    try:
        # Use screen -ls to list sessions and grep for powerloom patterns
        result = subprocess.run(["screen", "-ls"], capture_output=True, text=True)
        if result.returncode > 1:  # screen -ls returns 1 if no sessions exist
            return []

        # Parse screen output and look for powerloom sessions
        sessions = []
        for line in result.stdout.split("\n"):
            if any(
                pattern in line
                for pattern in [
                    "powerloom-premainnet",
                    "powerloom-testnet",
                    "powerloom-mainnet",
                    "snapshotter",
                    "pl_",
                ]
            ):
                # Extract session ID from the line (first number in the line)
                session_id = line.split(".")[0].strip()
                if session_id.isdigit():
                    sessions.append({"id": session_id, "name": line.strip()})
        return sessions
    except subprocess.CalledProcessError:
        return []


def cleanup_resources(force: bool = False) -> None:
    """Clean up Docker resources."""
    containers = get_powerloom_containers()
    networks = get_powerloom_networks()
    screen_sessions = get_powerloom_screen_sessions()

    if screen_sessions and (
        force
        or typer.confirm(
            "Would you like to terminate existing Powerloom screen sessions?"
        )
    ):
        console.print("Terminating screen sessions...", style="yellow")
        for session in screen_sessions:
            try:
                subprocess.run(["kill", session["id"]], check=True)
                console.print(
                    f"✅ Terminated screen session: {session['name']}", style="green"
                )
            except subprocess.CalledProcessError as e:
                console.print(
                    f"⚠️  Failed to terminate screen session {session['name']}: {e}",
                    style="red",
                )
                continue
        console.print("Screen session cleanup completed", style="green")

    if containers and (
        force
        or typer.confirm(
            "Would you like to stop and remove existing Powerloom containers?"
        )
    ):
        console.print("Stopping and removing containers...", style="yellow")
        for container in containers:
            try:
                container_id = container["id"]
                container_name = container["name"]
                run_with_sudo(["docker", "stop", container_id], capture_output=True)
                run_with_sudo(["docker", "rm", container_id], capture_output=True)
                console.print(
                    f"✅ Removed container: {container_name} ({container_id})",
                    style="green",
                )
            except subprocess.CalledProcessError as e:
                console.print(
                    f"⚠️  Failed to remove container {container_name} ({container_id}): {e}",
                    style="red",
                )
                continue
        console.print("Container cleanup completed", style="green")

    if networks and (
        force or typer.confirm("Would you like to remove Powerloom networks?")
    ):
        console.print("Removing networks...", style="yellow")
        for network in networks:
            try:
                run_with_sudo(["docker", "network", "rm", network], capture_output=True)
                console.print(f"✅ Removed network: {network}", style="green")
            except subprocess.CalledProcessError as e:
                console.print(
                    f"⚠️  Failed to remove network {network}: {e}", style="red"
                )
                continue
        console.print("Network cleanup completed", style="green")


def run_diagnostics(clean: bool = False, force: bool = False) -> None:
    """Run system diagnostics and optionally clean up resources."""
    # Check Docker installation and status
    docker_ok, docker_msg = check_docker_status()
    console.print(
        Panel(f"Docker Status: {docker_msg}", style="green" if docker_ok else "red")
    )
    if not docker_ok:
        return

    # Check Docker Compose
    compose_ok, compose_msg = check_docker_compose()
    console.print(
        Panel(
            f"Docker Compose Status: {compose_msg}",
            style="green" if compose_ok else "red",
        )
    )
    if not compose_ok:
        return

    # Show existing resources
    if containers := get_powerloom_containers():
        console.print("\nExisting Powerloom containers:", style="yellow")
        # Get full container details for display
        try:
            result = run_with_sudo(
                [
                    "docker",
                    "ps",
                    "-a",
                    "--format",
                    "table {{.ID}}\t{{.Image}}\t{{.Command}}\t{{.CreatedAt}}\t{{.Status}}\t{{.Ports}}\t{{.Names}}",
                ]
                + sum(
                    [
                        ["--filter", f]
                        for f in [
                            "name=snapshotter-lite-v2",
                            "name=powerloom-premainnet-",
                            "name=powerloom-testnet-",
                            "name=powerloom-mainnet-",
                            "name=local-collector",
                        ]
                    ],
                    [],
                ),
                capture_output=True,
                text=True,
            )
            for line in result.stdout.split("\n"):
                if line.strip():
                    console.print(f"  • {line}")
        except subprocess.CalledProcessError:
            # Fallback to simple display if detailed view fails
            for container in containers:
                console.print(f"  • {container['name']} ({container['id']})")

    if networks := get_powerloom_networks():
        console.print("\nExisting Powerloom networks:", style="yellow")
        for network in networks:
            console.print(f"  • {network}")

    if screen_sessions := get_powerloom_screen_sessions():
        console.print("\nExisting Powerloom screen sessions:", style="yellow")
        for session in screen_sessions:
            console.print(f"  • {session['name']}")

    # Clean up if requested
    if clean or (containers or networks or screen_sessions):
        cleanup_resources(force)


def diagnose_command(clean: bool = False, force: bool = False):
    """CLI command handler for diagnose."""
    console.print(
        "🔍 Running Powerloom Snapshotter Node Diagnostics...", style="bold blue"
    )
    run_diagnostics(clean, force)
