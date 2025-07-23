import subprocess

from rich.console import Console

console = Console()


def is_docker_running() -> bool:
    """Checks if the Docker daemon is running and responsive."""
    try:
        # Use check=False because `docker info` can sometimes exit with non-zero
        # even if operational (e.g., warnings). We primarily care about connectivity.
        process = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,  # Add a timeout to prevent indefinite hanging
        )

        # A common error message if Docker daemon is not running
        if (
            "Cannot connect to the Docker daemon" in process.stderr
            or "Is the docker daemon running?" in process.stderr
            or process.returncode != 0
        ):  # Consider any non-zero return code as a potential issue for simplicity here
            # console.print("[dim]Docker info stderr: " + process.stderr + "[/dim]", style="yellow") # Optional: for debugging
            # console.print("[dim]Docker info return code: " + str(process.returncode) + "[/dim]", style="yellow") # Optional: for debugging
            return False
        return True
    except FileNotFoundError:
        # Docker command itself is not found
        return False
    except subprocess.TimeoutExpired:
        console.print(
            "⏰ Timeout while trying to connect to Docker daemon.", style="yellow"
        )
        return False
    except Exception as e:
        # Catch any other unexpected errors during the check
        console.print(
            f"⚠️ Unexpected error while checking Docker status: {e}", style="yellow"
        )
        return False


def does_screen_session_exist(session_name: str) -> bool:
    """Checks if a screen session with the exact given name exists."""
    try:
        process = subprocess.run(
            ["screen", "-ls"],
            capture_output=True,
            text=True,
            check=False,  # screen -ls exits 0 even if no sessions, 1 if sessions
            timeout=5,
        )

        # screen -ls can exit with 1 if there are sessions, 0 if no sessions exist (or some other states)
        # We need to parse the output regardless of exit code, unless it's a fundamental error running screen itself.
        if (
            process.returncode > 1
            and "No Sockets found" not in process.stdout
            and "No Sockets found" not in process.stderr
        ):
            console.print(
                f"[dim]Error running 'screen -ls'. RC: {process.returncode}, Stderr: {process.stderr.strip()}[/dim]",
                style="yellow",
            )
            return False

        for line in process.stdout.splitlines():
            line = line.strip()
            parts = line.split("\t")
            if not parts:
                continue

            pid_session_part = parts[0]
            if "." in pid_session_part:
                actual_session_name = pid_session_part.split(".", 1)[1]
                if actual_session_name == session_name:
                    return True
        return False
    except FileNotFoundError:
        console.print(
            "❌ 'screen' command not found. Is screen installed?", style="red"
        )
        return False  # Cannot check if screen is not installed, treat as session not existing for safety of creation.
    except subprocess.TimeoutExpired:
        console.print("⏰ Timeout while running 'screen -ls'.", style="yellow")
        return False
    except Exception as e:
        console.print(
            f"⚠️ Unexpected error while checking screen session status: {e}",
            style="yellow",
        )
        return False


def list_snapshotter_screen_sessions() -> list[dict[str, str]]:
    """Lists running screen sessions matching the snapshotter naming convention."""
    sessions = []
    try:
        process = subprocess.run(
            ["screen", "-ls"], capture_output=True, text=True, check=False, timeout=5
        )
        if (
            process.returncode > 1
            and "No Sockets found" not in process.stdout
            and "No Sockets found" not in process.stderr
        ):
            console.print(
                f"[dim]Error running 'screen -ls'. RC: {process.returncode}, Stderr: {process.stderr.strip()}[/dim]",
                style="yellow",
            )
            return sessions

        for line in process.stdout.splitlines():
            line = line.strip()
            parts = line.split("\t")
            if not parts or len(parts) < 2:  # Need at least name and status part
                continue

            pid_session_part = parts[0]
            status_part = parts[1]  # e.g., (01/23/2024 11:29:09 AM)   (Detached)

            if "." in pid_session_part:
                pid_str, session_name = pid_session_part.split(".", 1)
                # Check if it matches our snapshotter naming convention: pl_{chain}_{market}_{slot}
                if session_name.startswith("pl_") and session_name.count("_") >= 3:
                    sessions.append(
                        {
                            "pid": pid_str,
                            "name": session_name,
                            "status_str": status_part.strip(),
                        }
                    )
        return sessions
    except FileNotFoundError:
        console.print(
            "❌ 'screen' command not found. Is screen installed?", style="red"
        )
        return sessions
    except subprocess.TimeoutExpired:
        console.print("⏰ Timeout while running 'screen -ls'.", style="yellow")
        return sessions
    except Exception as e:
        console.print(
            f"⚠️ Unexpected error while listing screen sessions: {e}", style="yellow"
        )
        return sessions
