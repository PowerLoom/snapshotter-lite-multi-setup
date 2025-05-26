import subprocess
from rich.console import Console
from typing import List, Dict

console = Console()

def get_docker_container_status_for_instance(instance_name_pattern: str) -> List[Dict[str, str]]:
    """Gets Docker container status for containers matching a name pattern."""
    containers = []
    try:
        # We need to be careful with the pattern. If instance_name_pattern is "pl_mainnet_uniswapv2_5481",
        # build.sh might name containers like "pl_mainnet_uniswapv2_5481_snapshotter_1" etc.
        # So, a wildcard search is appropriate.
        # The format string specifies tab-separated values for easier splitting.
        command = [
            "docker", "ps", "-a", 
            "--filter", f"name={instance_name_pattern}", # Match names containing the pattern
            "--format", "{{.Names}}\t{{.Status}}\t{{.ID}}"
        ]
        
        process = subprocess.run(
            command, 
            capture_output=True, 
            text=True, 
            check=True, 
            timeout=10
        )
        
        output_lines = process.stdout.strip().splitlines()
        for line in output_lines:
            if not line.strip():
                continue
            name, status, container_id = line.split('\t', 2)
            containers.append({
                "name": name.strip(),
                "status": status.strip(),
                "id": container_id.strip()
            })
        return containers
    except FileNotFoundError:
        console.print("❌ 'docker' command not found. Is Docker installed and running?", style="red")
        return containers # Return empty list
    except subprocess.CalledProcessError as e:
        # This can happen if docker ps fails for some reason, or if no containers match (though filter usually just returns empty)
        # For safety, log it but don't make the whole status command fail.
        console.print(f"[dim]Error running 'docker ps': {e.stderr.strip()}[/dim]", style="yellow")
        return containers
    except subprocess.TimeoutExpired:
        console.print("⏰ Timeout while running 'docker ps'.", style="yellow")
        return containers
    except Exception as e:
        console.print(f"⚠️ Unexpected error while getting Docker container status: {e}", style="yellow")
        return containers 