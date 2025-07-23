# Powerloom Snapshotter CLI Documentation

## Table of Contents
- [Overview](#overview)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Interactive Shell Mode (Recommended)](#interactive-shell-mode-recommended)
- [Commands](#commands)
  - [configure](#configure)
  - [deploy](#deploy)
  - [list](#list)
  - [stop](#stop)
  - [restart](#restart)
  - [cleanup](#cleanup)
  - [logs](#logs)
  - [diagnose](#diagnose)
  - [identity](#identity)
  - [shell](#shell)
- [Configuration Files](#configuration-files)
- [Environment Variables](#environment-variables)
- [Troubleshooting](#troubleshooting)
- [Building from Source](#building-from-source)

## Overview

The Powerloom Snapshotter CLI (`powerloom-snapshotter-cli`) is a command-line tool for managing Powerloom snapshotter nodes. It simplifies the process of configuring, deploying, and managing multiple snapshotter instances across different chains and data markets.

### Command Aliases

The CLI provides multiple command aliases for convenience:
- `powerloom-snapshotter-cli` - Full command name
- `snapshotter` - Short alias

Both commands are equivalent and can be used interchangeably.

### Key Features

- 🚀 **Easy Configuration**: Set up credentials and settings for different chain/market combinations
- 📦 **Multi-Instance Management**: Deploy and manage multiple snapshotter instances
- 🔍 **Instance Monitoring**: View status, logs, and diagnostics for running instances
- 🐚 **Interactive Shell**: Fast command execution with history support
- 🔐 **Secure Credential Storage**: Namespaced environment files for different configurations
- 🏗️ **Identity Management**: Generate and manage signer identities

## Installation

### Using Pre-built Binaries (Recommended)

1. Download the latest binary for your platform from the [releases page](https://github.com/PowerLoom/snapshotter-lite-multi-setup/releases):
   - Linux x86_64: `powerloom-snapshotter-cli-linux-amd64`
   - Linux ARM64: `powerloom-snapshotter-cli-linux-arm64`
   - macOS ARM64 (Apple Silicon): `powerloom-snapshotter-cli-macos-arm64`

2. Make the binary executable:
   ```bash
   chmod +x powerloom-snapshotter-cli-*
   ```

3. Move to a directory in your PATH (optional):
   ```bash
   # Use the full name
   sudo mv powerloom-snapshotter-cli-* /usr/local/bin/powerloom-snapshotter-cli

   # Or use a shorter alias for convenience
   sudo mv powerloom-snapshotter-cli-* /usr/local/bin/snapshotter
   ```

### From PyPI Package

```bash
# Install using uv (recommended)
uv tool install powerloom-snapshotter-cli

# Or install using pipx
pipx install powerloom-snapshotter-cli
```

### Building from Source (Development)

```bash
# Clone the repository
git clone https://github.com/PowerLoom/snapshotter-lite-multi-setup.git
cd snapshotter-lite-multi-setup

# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Now you can run the CLI
uv run powerloom-snapshotter-cli --help

# Or use the shorter alias
uv run snapshotter --help

# For direct terminal access, install globally:
uv tool install --from . powerloom-snapshotter-cli
```

## Quick Start

### Recommended: Use Interactive Shell Mode

The CLI has a startup time when running individual commands. We strongly recommend using the **interactive shell mode** for a much faster and smoother experience:

```bash
# Start the interactive shell (one-time startup cost)
powerloom-snapshotter-cli shell
# Or use the alias: snapshotter shell

# Now run commands instantly without delays:
powerloom-snapshotter> configure
powerloom-snapshotter> deploy
powerloom-snapshotter> list
powerloom-snapshotter> logs --follow
```

**Note:** After installation with `uv sync`, commands are available through `uv run`. For direct terminal access without the `uv run` prefix, use `uv tool install`.

### Alternative: Individual Commands

If you prefer to run individual commands:

1. **Configure credentials for a chain/market combination:**
   ```bash
   powerloom-snapshotter-cli configure --env devnet --market uniswapv2
   ```

2. **Deploy snapshotter instances:**
   ```bash
   powerloom-snapshotter-cli deploy --env devnet --market uniswapv2
   ```

3. **Check status of running instances:**
   ```bash
   powerloom-snapshotter-cli list
   ```

4. **View logs:**
   ```bash
   powerloom-snapshotter-cli logs --env devnet --market uniswapv2
   ```

## Interactive Shell Mode (Recommended)

The shell mode provides a persistent session that eliminates the startup time for each command. This is the **preferred way** to use the CLI, especially when running multiple commands.

### Benefits of Shell Mode

- ⚡ **Instant command execution** - No startup delay between commands
- 📝 **Command history** - Use arrow keys to navigate previous commands
- 🔄 **Persistent session** - Maintains context between commands
- 🎯 **Better workflow** - Run multiple operations smoothly

### Starting the Shell

```bash
powerloom-snapshotter-cli shell
```

You'll see:
```
╭─── Powerloom Snapshotter CLI - Interactive Mode ────╮
│ Type 'help' for available commands, 'exit' or       │
│ 'quit' to leave.                                    │
│ Use Ctrl+C to cancel current command.               │
╰──────────────────────────────────────────────────────╯

powerloom-snapshotter>
```

### Example Shell Session

```bash
$ powerloom-snapshotter-cli shell

powerloom-snapshotter> configure
[Interactive configuration process...]

powerloom-snapshotter> deploy --env devnet --market uniswapv2
[Deployment process...]

powerloom-snapshotter> list
[Shows running instances...]

powerloom-snapshotter> logs --env devnet --market uniswapv2 --follow
[Real-time logs...]
^C  # Press Ctrl+C to stop following logs

powerloom-snapshotter> stop --env devnet --market uniswapv2
[Stops instances...]

powerloom-snapshotter> exit
Goodbye!
```

### Shell Commands

All regular CLI commands work in shell mode, plus:
- `help` - Show available commands
- `clear` or `cls` - Clear the screen
- `exit` or `quit` - Exit the shell
- ↑/↓ arrows - Navigate command history
- Ctrl+C - Cancel current command
- Ctrl+D - Exit shell

## Commands

### configure

Set up credentials and settings for a specific chain and data market combination.

```bash
powerloom-snapshotter-cli configure [OPTIONS]
```

**Options:**
- `--env, -e`: Powerloom chain name (e.g., DEVNET, MAINNET)
- `--market, -m`: Data market name (e.g., UNISWAPV2, AAVEV3)
- `--wallet, -w`: Wallet address holding the slots
- `--signer, -s`: Signer account address
- `--signer-key, -k`: Signer account private key
- `--source-rpc, -r`: Source chain RPC URL
- `--powerloom-rpc, -p`: Powerloom RPC URL
- `--telegram-chat, -t`: Telegram chat ID for notifications
- `--telegram-url, -u`: Telegram reporting URL

**Example:**
```bash
# Interactive mode (recommended)
powerloom-snapshotter-cli configure

# With options
powerloom-snapshotter-cli configure --env devnet --market uniswapv2 --wallet 0x123...
```

**Configuration files are stored in:** `~/.powerloom-snapshotter-cli/envs/`

### deploy

Deploy snapshotter nodes for specified environment and data markets.

```bash
powerloom-snapshotter-cli deploy [OPTIONS]
```

**Options:**
- `--env, -e`: Deployment environment (Powerloom chain name)
- `--market, -m`: Data markets to deploy (can be specified multiple times)
- `--slot, -s`: Specific slot IDs to deploy (can be specified multiple times)
- `--wallet, -w`: Wallet address holding the slots
- `--signer-address`: Signer account address
- `--signer-key`: Signer account private key

**Examples:**
```bash
# Interactive deployment
powerloom-snapshotter-cli deploy

# Deploy specific market
powerloom-snapshotter-cli deploy --env devnet --market uniswapv2

# Deploy specific slots
powerloom-snapshotter-cli deploy --env devnet --market uniswapv2 --slot 123 --slot 456

# Deploy multiple markets
powerloom-snapshotter-cli deploy --env devnet --market uniswapv2 --market aavev3
```

### list

List all active snapshotter instances.

```bash
powerloom-snapshotter-cli list
```

**Output includes:**
- Instance name
- Status (Active/Inactive)
- Docker container status
- Process details

### stop

Stop snapshotter instances.

```bash
powerloom-snapshotter-cli stop [OPTIONS]
```

**Options:**
- `--env, -e`: Filter by Powerloom chain
- `--market, -m`: Filter by data market
- `--slot, -s`: Stop specific slot

**Examples:**
```bash
# Stop all instances
powerloom-snapshotter-cli stop

# Stop all instances for a chain
powerloom-snapshotter-cli stop --env devnet

# Stop specific market instances
powerloom-snapshotter-cli stop --env devnet --market uniswapv2

# Stop specific slot
powerloom-snapshotter-cli stop --env devnet --market uniswapv2 --slot 123
```

### restart

Restart snapshotter instances (stop and start).

```bash
powerloom-snapshotter-cli restart [OPTIONS]
```

**Options:**
- `--env, -e`: Filter by Powerloom chain
- `--market, -m`: Filter by data market
- `--slot, -s`: Restart specific slot

### cleanup

Remove stopped instances and clean up resources.

```bash
powerloom-snapshotter-cli cleanup [OPTIONS]
```

**Options:**
- `--env, -e`: Filter by Powerloom chain
- `--market, -m`: Filter by data market
- `--slot, -s`: Cleanup specific slot
- `--force, -f`: Skip confirmation prompts

**Example:**
```bash
# Cleanup with confirmation
powerloom-snapshotter-cli cleanup --env devnet --market uniswapv2

# Force cleanup without confirmation
powerloom-snapshotter-cli cleanup --force
```

### logs

View logs for snapshotter instances.

```bash
powerloom-snapshotter-cli logs [OPTIONS]
```

**Options:**
- `--env, -e`: Powerloom chain name
- `--market, -m`: Data market name
- `--slot, -s`: Specific slot ID
- `--lines, -n`: Number of lines to show (default: 50)
- `--follow, -f`: Follow log output
- `--container, -c`: Container to show logs for (core-api or snapshotter)

**Examples:**
```bash
# View recent logs
powerloom-snapshotter-cli logs --env devnet --market uniswapv2

# Follow logs in real-time
powerloom-snapshotter-cli logs --env devnet --market uniswapv2 --follow

# View specific container logs
powerloom-snapshotter-cli logs --env devnet --market uniswapv2 --container core-api
```

### diagnose

Run diagnostics on the system and check requirements.

```bash
powerloom-snapshotter-cli diagnose [OPTIONS]
```

**Options:**
- `--clean, -c`: Clean up existing deployments
- `--force, -f`: Force cleanup without confirmation

**Diagnostics include:**
- Python version check
- System resources (CPU, memory, disk)
- Docker installation and status
- Network connectivity
- Required port availability
- Running instances status

### identity

Manage signer identities.

```bash
powerloom-snapshotter-cli identity COMMAND
```

**Subcommands:**

#### identity generate
Generate a new signer account:
```bash
powerloom-snapshotter-cli identity generate
```

#### identity show
Display signer address from a configuration:
```bash
powerloom-snapshotter-cli identity show --env devnet --market uniswapv2
```

**Options:**
- `--env, -e`: Powerloom chain name
- `--market, -m`: Data market name

### shell

Start an interactive shell session for faster command execution. **This is the recommended way to use the CLI.**

```bash
powerloom-snapshotter-cli shell
```

The shell mode eliminates the startup delay for each command, making it ideal for managing your snapshotter nodes efficiently. See the [Interactive Shell Mode](#interactive-shell-mode-recommended) section above for detailed usage and examples.

## Configuration Files

Configuration files are stored in `~/.powerloom-snapshotter-cli/envs/` with the naming convention:
```
.env.{chain}.{market}.{source_chain}
```

Example: `.env.devnet.uniswapv2.eth_mainnet`

### Configuration Contents

Each configuration file contains:
- `WALLET_HOLDER_ADDRESS`: Address holding slot NFTs
- `SIGNER_ACCOUNT_ADDRESS`: Address used for signing snapshots
- `SIGNER_ACCOUNT_PRIVATE_KEY`: Private key for signer account
- `SOURCE_RPC_URL`: RPC endpoint for source blockchain
- `POWERLOOM_RPC_URL`: Powerloom protocol RPC endpoint
- `TELEGRAM_CHAT_ID`: (Optional) Telegram chat for notifications
- `TELEGRAM_REPORTING_URL`: (Optional) Telegram webhook URL
- `MAX_STREAM_POOL_SIZE`: Connection pool size
- `CONNECTION_REFRESH_INTERVAL_SEC`: Connection refresh interval

## Environment Variables

The CLI respects the following environment variables as fallbacks:
- `WALLET_HOLDER_ADDRESS`
- `SIGNER_ACCOUNT_ADDRESS`
- `SIGNER_ACCOUNT_PRIVATE_KEY`
- `SOURCE_RPC_URL`
- `POWERLOOM_RPC_URL`

## Troubleshooting

### Common Issues

#### 1. "Docker daemon is not running"
**Solution:** Start Docker Desktop or the Docker service:
```bash
# macOS/Windows: Start Docker Desktop
# Linux:
sudo systemctl start docker
```

#### 2. "Command not found" after uv sync
**Solution:** Use the `uv run` prefix:
```bash
uv run powerloom-snapshotter-cli --help
```
Or install globally with `uv tool install` for direct access.

#### 3. "Wallet Holder Address could not be resolved"
**Solution:** Run `powerloom-snapshotter-cli configure` to set up credentials for the chain/market combination.

#### 4. "Screen session already exists"
**Solution:** Clean up existing sessions:
```bash
# List screen sessions
screen -ls

# Quit specific session
screen -X -S session_name quit

# Or use cleanup command
powerloom-snapshotter-cli cleanup --force
```

#### 5. "ABI files not found"
**Solution:** Ensure you're using the latest CLI version. The ABI files should be bundled with the binary.

#### 6. "No slots found for wallet"
**Solution:** Verify that:
- The wallet address owns slots on the specified chain
- You're using the correct chain (devnet vs mainnet)
- The RPC URL is accessible

### Debug Mode

For detailed debugging information:
```bash
# Set debug environment variable
export POWERLOOM_CLI_DEBUG=1

# Run commands with debug output
powerloom-snapshotter-cli deploy --env devnet --market uniswapv2
```

### Getting Help

- GitHub Issues: https://github.com/PowerLoom/snapshotter-lite-multi-setup/issues
- Documentation: https://docs.powerloom.io
- Discord: https://discord.gg/powerloom

## Building from Source

### Prerequisites
- Python 3.12+
- uv (Python package manager)
- Git

### Build Instructions

```bash
# Clone repository
git clone https://github.com/PowerLoom/snapshotter-lite-multi-setup.git
cd snapshotter-lite-multi-setup

# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Run from source
uv run powerloom-snapshotter-cli --help

# Build the package
uv build

# This will create:
# - dist/powerloom_snapshotter_cli-0.1.0-py3-none-any.whl
# - dist/powerloom_snapshotter_cli-0.1.0.tar.gz

# Build binary with PyInstaller
pyinstaller pyinstaller.spec

# Binary will be in dist/ directory
ls -la dist/
```

### Development Workflow

```bash
# Install development dependencies (included by default with uv sync)
uv sync

# Run tests
uv run pytest

# Format code
uv run black snapshotter_cli/
uv run isort snapshotter_cli/

# Type checking
uv run mypy snapshotter_cli/

# Note: Commands require the 'uv run' prefix.
# For direct access, use 'uv tool install'.
```

### Uninstalling

To uninstall the CLI:

```bash
# If installed with pip/uv in development
pip uninstall powerloom-snapshotter-cli -y

# If installed with pipx
pipx uninstall powerloom-snapshotter-cli

# If installed with uv tool
uv tool uninstall powerloom-snapshotter-cli

# If using pyenv, refresh shims after uninstall
pyenv rehash
```

---

For more information, visit the [Powerloom documentation](https://docs.powerloom.io).
