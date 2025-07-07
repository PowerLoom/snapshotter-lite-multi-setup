#!/usr/bin/env python3
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

def install_uv():
    """Install uv if not already installed."""
    try:
        subprocess.run(["uv", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Install uv using pip
        subprocess.run([
            "pip", "install", "--user", "uv"
        ], check=True)

def main():
    # Get the absolute path of the project root
    project_root = Path(__file__).parent.absolute()
    
    # Create build directory
    build_dir = project_root / "build"
    build_dir.mkdir(exist_ok=True)
    os.chdir(build_dir)

    # Install uv
    install_uv()

    # Create a new venv with uv and install dependencies
    subprocess.run([
        "uv", "venv",
        "--python", sys.executable,  # Use the current Python interpreter
        ".venv"
    ], check=True)

    # Get venv Python path
    if platform.system() == "Windows":
        python_exe = ".venv/Scripts/python.exe"
    else:
        python_exe = ".venv/bin/python"

    # Install dependencies using uv
    subprocess.run([
        "uv", "pip", "install",
        "--python", python_exe,
        "pyinstaller",
        str(project_root)  # Install our package using absolute path
    ], check=True)

    # Create PyInstaller spec with proper imports
    subprocess.run([
        python_exe, "-m", "PyInstaller",
        "--onefile",  # Create a single executable
        "--name", "snapshotter-cli",
        "--add-data", f"{project_root}/snapshotter_cli/utils/abi/*:snapshotter_cli/utils/abi/",  # Include ABI files
        "--hidden-import", "snapshotter_cli.commands.configure",
        "--hidden-import", "snapshotter_cli.commands.deploy",
        "--hidden-import", "snapshotter_cli.commands.diagnose",
        "--hidden-import", "snapshotter_cli.commands.identity",
        "--hidden-import", "snapshotter_cli.commands.status",
        str(project_root / "snapshotter_cli" / "cli.py")  # Use absolute path
    ], check=True)

    # Copy binary to dist directory
    dist_dir = project_root / "dist"
    dist_dir.mkdir(exist_ok=True)
    
    binary = "snapshotter-cli.exe" if platform.system() == "Windows" else "snapshotter-cli"
    shutil.copy2(f"dist/{binary}", dist_dir)

    print(f"\nBuild complete! Binary available at: {dist_dir}/{binary}")

if __name__ == "__main__":
    main() 