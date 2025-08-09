# Changelog

All notable changes to the Powerloom Snapshotter CLI and setup tools will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2025-08-09

### Fixed
- **Critical: ENV file case mismatch (#72)** - CLI now generates `.env-mainnet-UNISWAPV2-ETH` instead of `.env-MAINNET-UNISWAPV2-ETH` to match `build.sh` expectations
- **Devnet deployments** - Added missing `--devnet` flag when deploying to devnet
- **Data market contract numbers** - Added `--data-market-contract-number` flag with proper mapping (1=AAVEV3, 2=UNISWAPV2)

### Changed
- **Chain selection order** - Mainnet now appears first in all selection prompts
- **Chain name display** - Chains now display as "Mainnet" and "Devnet" (title case) instead of all caps
- **Default market number** - Changed default from 2 to 1 for unknown markets (more conservative approach)
- **UI consistency** - Configure command now uses the same Panel-based UI as deploy command for chain selection

### Enhanced
- **Shell mode** - Applied chain ordering and title case improvements to interactive shell

## [0.1.2] - 2025-08-08

### Fixed
- Character removal in wallet address input on Linux - lowercase 'b' characters were being incorrectly removed

### Added
- Git commit info to version display for better tracking

## [0.1.1] - 2025-08-05

### Fixed
- Terminal display issues in Linux CLI builds - prompts now display correctly with proper newlines
- Deployment market selection flow - market selection now happens before env file loading
- Linux binary glibc compatibility - builds now use Ubuntu 22.04 for better compatibility

### Changed
- GitHub Actions workflow updated to use Ubuntu 22.04
- Standardized architecture naming to `amd64` for consistency

### Enhanced
- Streamlined configuration UX - auto-uses defaults from sources.json, no RPC URL prompt needed
- Auto-selection for single-market chains

## [0.1.0] - 2025-07-23

### Added
- Initial release of `powerloom-snapshotter-cli`
- Interactive shell mode to eliminate ~6-7 second startup delays
- Configure command for credential management
- Deploy command for node deployment
- Status command for monitoring containers
- List command for viewing deployments
- Logs command for viewing container logs
- Identity management commands
- Support for multiple chains (MAINNET, DEVNET)
- Support for multiple markets (UNISWAPV2, AAVEV3)

### Legacy Support
- Maintained backward compatibility with traditional scripts:
  - `bootstrap.sh` for configuration
  - `multi_clone.py` for deployment
  - `diagnose.sh` for system diagnostics
  - `prep.sh` for automated system preparation
