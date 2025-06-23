# Multi node setup for multiple Powerloom Snapshotter Lite: Protocol V2 slot holders on Linux VPS

## Table of Contents

- [Multi node setup for multiple Powerloom Snapshotter Lite: Protocol V2 slot holders on Linux VPS](#multi-node-setup-for-multiple-powerloom-snapshotter-lite-protocol-v2-slot-holders-on-linux-vps)
  - [Table of Contents](#table-of-contents)
  - [1. Preparation](#1-preparation)
    - [1.1 Run Diagnostics to cleanup old instances](#11-run-diagnostics-to-cleanup-old-instances)
    - [1.2 Choose Installation Method: Manual or Automated](#12-choose-installation-method-manual-or-automated)
      - [1.2.1 Automated Node dependency installation](#121-automated-node-dependency-installation)
      - [1.2.2 Manual Node dependency installation](#122-manual-node-dependency-installation)
  - [2. Setup](#2-setup)
    - [2.1 Initialize Environment](#21-initialize-environment)
    - [2.2 Run the deploy script](#22-run-the-deploy-script)
      - [2.2.0 Deploy script command line flags](#220-deploy-script-command-line-flags)
      - [2.2.1 Deploy a subset of slots](#221-deploy-a-subset-of-slots)
      - [2.2.2 Deploy all slots](#222-deploy-all-slots)
  - [3. Monitoring, diagnostics and cleanup](#3-monitoring-diagnostics-and-cleanup)
    - [3.1 Cleanup\[optional\]](#31-cleanupoptional)
      - [3.1.1 Stop and remove all powerloom containers](#311-stop-and-remove-all-powerloom-containers)
      - [3.1.2 Remove all Docker subnets assigned to the snapshotter-lite containers](#312-remove-all-docker-subnets-assigned-to-the-snapshotter-lite-containers)
      - [3.1.3 Cleanup stale images and networks and cache](#313-cleanup-stale-images-and-networks-and-cache)
  - [4. Case studies](#4-case-studies)
    - [4.1 Deploy subsets of slots with different configs](#41-deploy-subsets-of-slots-with-different-configs)
    - [4.2 Running Slots from Different Wallets on a Single VPS](#42-running-slots-from-different-wallets-on-a-single-vps)
  - [\[OPTIONAL\] Dev mode setup](#optional-dev-mode-setup)

> [!NOTE]
> This setup is for Lite nodes participating in the latest V2 of Powerloom Protocol with multiple data markets. [Protocol V1 setup](https://github.com/PowerLoom/snapshotter-lite-multi-setup/tree/main) is deprecated and its data markets are archived. Your submission data, rewards on it are finalized and recorded as [announced on Discord](https://discord.com/channels/777248105636560948/1146931631039463484/1242876184509812847).

## 1\. Preparation

Clone this repository and change into the repository's directory. All commands will be run within there henceforth.

``` bash
git clone https://github.com/PowerLoom/snapshotter-lite-multi-setup.git snapshotter-lite-multi-setup
cd snapshotter-lite-multi-setup
```

### 1.1 Run Diagnostics to cleanup old instances

First, run the diagnostic tool to check your system and clean up any existing deployments:

``` bash
./diagnose.sh -y
```

> [!NOTE]
> The `-y` flag is recommended to be used as it will skip all the prompts and cleanup existing Powerloom containers and legacy Docker networks without asking for confirmation. If you want to run the script with prompts, you can run it without the `-y` flag.

This will help you:

* Ensure Docker and Docker Compose Availability
* Check if default ports (e.g., `8002`, `50051`) are in use and suggests available alternatives.
* Scan Docker network configurations, listing used subnets and suggesting available ones.
* Check for PowerLoom deployment directories and removes them if necessary.
* Detect and terminate active screen sessions related to PowerLoom.
* Stop and remove all PowerLoom containers to prevent conflicts.
* Identify and remove unused or legacy Docker networks.

### 1.2 Choose Installation Method: Manual or Automated
To proceed, choose one of the following installation methods:

[1: Automated Node dependency installation](#121-automated-node-dependency-installation)

[2: Manual Node dependency installation](#122-manual-node-dependency-installation)

> [!NOTE]
> Important: You only need to complete one of the methods. After installation, skip to [2. Setup](#2-setup)

#### 1.2.1 Automated Node dependency installation
Run below command to install all node dependences in one go, It might take 10-15 mins depending on VPS specs.

``` bash
./prep.sh
```

This will:

* Update VPS
* Install Docker and Docker Compose
* Install Pip(Python package manager)
* Install Pyenv and their dependencies
* Add Pyenv to Shell Environment
* Create and activate a virtual environment
* Install Python 3.11.5 and their Dependencies

#### 1.2.2 Manual Node dependency installation
Run below commands to install all node dependences manually.

> **Setting Up the Environment**
 
Install docker and docker compose, Detailed instructions can be found at [Step 3: Setting Up the Environment](https://docs.powerloom.io/docs/build-with-powerloom/snapshotter-node/lite-node-v2/getting-started)


> **Install `pyenv`**
 
Detailed instructions and troubleshotting can be found on the [pyenv Github repo README](https://github.com/pyenv/pyenv?tab=readme-ov-file#installation). In general, the following should take care of the installation on an Ubuntu VPS.

```
sudo apt update && sudo apt install -y build-essential libssl-dev zlib1g-dev libbz2-dev \
libreadline-dev libsqlite3-dev curl libncursesw5-dev xz-utils tk-dev libxml2-dev \
libxmlsec1-dev libffi-dev liblzma-dev

curl https://pyenv.run | bash

echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init --path)"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc

source ~/.bashrc

pyenv install 3.11.5
```

> **Install `pyenv-virtualenv`**
  Detailed instructions can be [found here](https://github.com/pyenv/pyenv-virtualenv).

```
pyenv virtualenv 3.11.5 ss_lite_multi_311
pyenv local ss_lite_multi_311
```

> **Install all python requirements**

```bash
# install all python requirements
pip install -r requirements.txt
```

## 2. Setup

### 2.1 Initialize Environment

Run the bootstrap script to

* Initialize .env file
* re-initialize .env file

``` bash
./bootstrap.sh
```

If you are Initializing .env file for first time it will output like the following:

```
🟡 .env file not found, please follow the instructions below to create one!
creating .env file...
🫸 ▶︎ Please enter the WALLET_HOLDER_ADDRESS: 

🫸 ▶︎ Please enter the SOURCE_RPC_URL: 

🫸 ▶︎ Please enter the SIGNER_ACCOUNT_ADDRESS: 

🫸 ▶︎ Please enter the SIGNER_ACCOUNT_PRIVATE_KEY: 

🫸 ▶︎ Please enter the TELEGRAM_CHAT_ID (press enter to skip): 

🟢 .env file created successfully!
```

If you already have initilized .env file and trying to re-initilize, you will see output like following

```
🟢 .env file already found to be initialized! If you wish to change any of the values, please backup the .env file at the following prompt.
Do you wish to backup and modify the .env file? (y/n)
y
🟢 .env file backed up to .env.backup.20250210221149
creating .env file...
🫸 ▶︎ Please enter the WALLET_HOLDER_ADDRESS (press enter to keep current value: <wallet-holder-address>): 

🫸 ▶︎ Please enter the SOURCE_RPC_URL (press enter to keep current value: <source-rpc-url>): 

🫸 ▶︎ Please enter the SIGNER_ACCOUNT_ADDRESS (press enter to keep current value: <signer-account-address>): 

🫸 ▶︎ Please enter the SIGNER_ACCOUNT_PRIVATE_KEY (press enter to keep current value: [hidden]): 

🫸 ▶︎ Please enter the TELEGRAM_CHAT_ID (press enter to skip) (press enter to keep current value: <telegram-chat-id>): 

🟢 .env file created successfully!
```

This will:

* Back up any existing configuration
* Guide you through setting up required variables
* Create a new .env file with your settings
* This step will require you to inform the RPC URL, snapshotter owner wallet address, Signer(Burner) wallet address and signer(burner) wallet private key. When you paste or type the private key, it will look like nothing is typed or pasted, but that´s due to the sensitive information, simply paste and press enter!

### 2.2 Run the deploy script

The deploy script can be run interactively, as is, with

```bash
python multi_clone.py
```

#### 2.2.0 Deploy script command line flags

The deploy script supports several command line flags to customize its behavior:

```bash
python multi_clone.py [flags]
```

Available flags:
- `--data-market {1,2}`: Choose the data market (1: AAVEV3, 2: UNISWAPV2)
- `-y, --yes`: Deploy all nodes without prompting for confirmation
- `--latest-only`: Deploy only the latest (highest) slot
- `--use-env-connection-refresh-interval`: Use CONNECTION_REFRESH_INTERVAL_SEC from environment instead of calculating based on slots

Example usage:
```bash
# Deploy all slots non-interactively for UNISWAPV2
python multi_clone.py --data-market 2 -y

# Deploy only the latest slot
python multi_clone.py --latest-only

# Use environment variable for connection refresh interval
CONNECTION_REFRESH_INTERVAL_SEC=300 python multi_clone.py --use-env-connection-refresh-interval
```

When you run the deploy script without any flags, it will ask you if you want to deploy all nodes? If you want to [Deploy a subset of slots](#221-deploy-a-subset-of-slots) then press `n` else you want to [Deploy all slots](#222-deploy-all-slots) press `y`.

#### 2.2.1 Deploy a subset of slots

Enter `n` when asked if you want to deploy all slots. Proceed with the begin and end slot IDs for your deployment.

You will see an output like the following:

```
🟢 .env file found with following env variables...
SOURCE_RPC_URL=<your data source rpc url>
SIGNER_ACCOUNT_ADDRESS=<your signer account address>
WALLET_HOLDER_ADDRESS=<your slot holding wallet address>
PROST_RPC_URL=[[https://rpc.powerloom.network\](https://rpc.powerloom.network)](https://rpc.powerloom.network](https://rpc.powerloom.network)) PROST_CHAIN_ID=7865
TELEGRAM_CHAT_ID=<your telegram chat id>
Found n slots for wallet holder address
[xxx1, xxx2, xxx3,xxx4]
☑️ Do you want to deploy all slots? (y/n)n
🫸 ▶︎ Enter the start slot ID: xxx1 
🫸 ▶︎ Enter the end slot ID: xxx3 #This will deploy slot xxx1,xxx2,xxx3
```

Choose the data market namespace you want to deploy, UniswapV2 by default.

```
🔍 Select a data market contract (UNISWAPV2 is default):
1. AAVEV3
2. UNISWAPV2

🫸 ▶︎ Please enter your choice (1/2) [default: 2 - UNISWAPV2]: 2
```

And you will see the following output:

```
🟠 Deploying node for slot xxx1 in data market UNISWAPV2
----------------------------------------Spinning up docker containers for slot xxx1----------------------------------------
Sleeping for 30 seconds to allow docker containers to spin up...

...

🟠 Deploying node for slot xxx2 in data market UNISWAPV2
----------------------------------------Spinning up docker containers for slot xxx2----------------------------------------
Sleeping for 10 seconds to allow docker containers to spin up...

...

🟠 Deploying node for slot xxx3 in data market UNISWAPV2
----------------------------------------Spinning up docker containers for slot xxx3----------------------------------------
Sleeping for 10 seconds to allow docker containers to spin up...
```

#### 2.2.2 Deploy all slots

Enter `y` when asked if you want to deploy all slots.

You will see an output like the following:

```
🟢 .env file found with following env variables...
SOURCE_RPC_URL=<your data source rpc url>
SIGNER_ACCOUNT_ADDRESS=<your signer account address>
WALLET_HOLDER_ADDRESS=<your slot holding wallet address>
PROST_RPC_URL=[https://rpc.powerloom.network](https://rpc.powerloom.network)
PROST_CHAIN_ID=7865
TELEGRAM_CHAT_ID=<your telegram chat id>
Found n slots for wallet holder address
[list of slot ids]
☑️ Do you want to deploy all slots? (y/n)n
🫸 ▶︎ Enter the start slot ID: xxx1
🫸 ▶︎ Enter the end slot ID: xxx2
```

Choose the data market namespace you want to deploy, UniswapV2 by default.

```
🔍 Select a data market contract (UNISWAPV2 is default):
1. AAVEV3
2. UNISWAPV2

🫸 ▶︎ Please enter your choice (1/2) [default: 2 - UNISWAPV2]: 2
```

And you will see the following output:

```
🟠 Deploying node for slot xxx1 in data market UNISWAPV2
----------------------------------------Spinning up docker containers for slot xxx1----------------------------------------
Sleeping for 30 seconds to allow docker containers to spin up...

...

🟠 Deploying node for slot xxx2 in data market UNISWAPV2
----------------------------------------Spinning up docker containers for slot xxx2----------------------------------------
Sleeping for 10 seconds to allow docker containers to spin up...
```

## 3\. Monitoring\, diagnostics and cleanup

The multi setup comes bundled with a diagnostic and cleanup script.

``` bash
./diagnose.sh -y
```

> [!NOTE]
> The `-y` flag is recommended to be used as it will skip all the prompts and cleanup existing Powerloom containers and legacy Docker networks without asking for confirmation. If you want to run the script with prompts, you can run it without the `-y` flag.

The following output may vary depending on whether you have run snapshotter node(s) before this setup or not.

```
./diagnose.sh
🔍 Starting PowerLoom Node Diagnostics...

📦 Checking Docker installation...
✅ Docker is installed and running

🐳 Checking docker-compose...
✅ Docker Compose is available

🔌 Checking default ports...
⚠️ Port 8002 is in use
✅ Next available Core API port: 8003
⚠️ Port 50051 is in use
✅ Next available Collector port: 50052

🔍 Checking existing PowerLoom containers...
Found existing PowerLoom containers:
snapshotter-lite-v2-xxx1-mainnet-UNISWAPV2-ETH
snapshotter-lite-local-collector-xxx1-mainnet-UNISWAPV2-ETH
snapshotter-lite-v2-xxx2-mainnet-UNISWAPV2-ETH
```

If you want to cleanup the existing containers, follow along to the next section

### 3.1 Cleanup[optional]

> [!TIP]
> This is particularly useful if you find your nodes are not running as expected and want a fresh start.

#### 3.1.1 Stop and remove all powerloom containers

If the diagnostic script finds any running containers tagged with `snapshotter-lite`, it will ask you if you want to stop and remove them.

Select `y` at the following prompt and you see some logs like the following:

```
Would you like to stop and remove existing PowerLoom containers? (y/n): y 

Stopping running containers... (timeout: 30s per container)
Attempting to stop container snapshotter-lite-v2-xxx1-mainnet-UNISWAPV2-ETH...
snapshotter-lite-v2-xxx1-mainnet-UNISWAPV2-ETH
Attempting to stop container snapshotter-lite-local-collector-xxx1-mainnet-UNISWAPV2-ETH...
snapshotter-lite-local-collector-xxx1-mainnet-UNISWAPV2-ETH

Removing containers...
Removing container snapshotter-lite-v2-xxx1-mainnet-UNISWAPV2-ETH...
Removing container snapshotter-lite-local-collector-xxx1-mainnet-UNISWAPV2-ETH...

Removing container snapshotter-lite-v2-xxx2-mainnet-UNISWAPV2-ETH...
```

#### 3.1.2 Remove all Docker subnets assigned to the snapshotter-lite containers

Enter `y` at the following prompt and you see some logs like the following:

```
Would you like to remove existing PowerLoom networks? (y/n): y

Removing networks...
snapshotter-lite-v2-xxx1-mainnet-UNISWAPV2-ETH
snapshotter-lite-v2-xxx2-mainnet-UNISWAPV2-ETH
✅ Networks removed
```

#### 3.1.3 Cleanup stale images and networks and cache

> [!NOTE]
> This is a cleanup step that removes all stale images, networks and cache from Docker. Proceed only if all other attempts at running the node have failed after following our guides.

Enter `y` at the following prompt and you see some logs like the following. Press `y` again at the end to confirm with Docker.

```
Would you like to remove unused Docker resources (only unused images, networks, and cache)? (y/n): y 

Removing unused Docker resources...

Running docker network prune...

Running docker system prune...
WARNING! This will remove:
  - all stopped containers
  - all networks not used by at least one container
  - all images without at least one container associated to them
  - all build cache

Are you sure you want to continue? [y/N] y

Deleted Images:
untagged: [ghcr.io/powerloom/snapshotter-lite-v2:latest](http://ghcr.io/powerloom/snapshotter-lite-v2:latest)
untagged: [ghcr.io/powerloom/snapshotter-lite-v2@sha256:15e05050bbf1473a3b4345a188c44bb37fb343f89d24f9ce731e3c3df190ec98](http://ghcr.io/powerloom/snapshotter-lite-v2@sha256:15e05050bbf1473a3b4345a188c44bb37fb343f89d24f9ce731e3c3df190ec98)
deleted: sha256:33d723744d4cb306c9be663247464f497698682fb0d577290831114b825bc84a

Total reclaimed space: 1.614GB
✅ Cleanup complete

✅ Diagnostic check complete
```

If you encounter any issues, please contact us on [discord](https://discord.com/invite/powerloom).

## 4\. Case studies

### 4.1 Deploy subsets of slots with different configs

Meet Bob, The Architect of Chaos. Bob has five Powerloom slots, but he's got an itch to make things complicated—deploying three nodes each with a different RPC and two nodes sharing a single RPC. Here's how he pulls it off:

1. Bob logs into his VPS and follows [Preparation](#1-preparation).
2. When initializing the environment (by `./bootstrap.sh`), he inputs all the necessary slot info and sets **RPC1**.
3. Bob then runs the deploy script: (by `python multi_clone.py`). Since he's deploying a subset of slots, he follows [Deploy a subset of slots](#221-deploy-a-subset-of-slots) and sets the **start slot** and **end slot** to **slot1**. BOOM! **Slot1 is live.**
4. Bob repeats the process for **slot2** using **RPC2** and deploys **slot2** using the same method.
5. He does the same for **RPC3** to deploy **slot3**.
6. Now for the final trick, Bob wants **slot4 and slot5** to share **RPC4**. He reinitializes the env variables by (by `./bootstrap.sh`), and when deploying(by python multi\_clone.py), he sets **start slot to slot4 and end slot to slot5**.

BOOM! Bob did it. **Three slots running on three different RPCs and two slots sharing a single RPC.** Mission accomplished. 🎉

### 4.2 Running Slots from Different Wallets on a Single VPS

Meet Alice, the queen of efficiency. Unlike Bob, who enjoys juggling multiple RPCs, Alice faces a different challenge. Her four Powerloom slots are spread across three wallets, but she wants them all running smoothly on a single VPS. Here's how she pulls it off:
She clones `X(#of wallets)` multiscript directories, each with different destination directory name.

1. Alice logs into her VPS and follows [Preparation](#1-preparation), She then clones the repository three times, assigning a unique destination directory name to each clone.
2. Now, she [Setup](#2-setup) two nodes from **Wallet 1** on a single RPC. When initializing the environment (by `./bootstrap.sh`), she inputs all the necessary for wallet1 info and sets **RPC1**.
3. Alice then runs the deploy script: (by `python multi_clone.py`). Since she's deploying a subset of slots, she follows [Deploy a subset of slots](#221-deploy-a-subset-of-slots) and sets the **start slot** to **slot1** and **end slot** to **slot2**. BOOM! **Slot1 and slot2 is live.**
4. Alice then navigates to the second repository (by `cd <directory-name>`), initializes the environment (by `./bootstrap.sh`) and inputs all the necessary info for wallet2 and sets **RPC1**. She then deploys node from wallet 2 by running deploy script: (by `python multi_clone.py`) and follows [Deploy a subset of slots](#221-deploy-a-subset-of-slots)Finally, she repeats the same process for **Slot 3** from **Wallet 3**, just as she did for Slot 2.

BOOM! Alice did it. **Four slots from three different wallet running on single VPS.** Mission accomplished. 🎉

<br>
## [OPTIONAL] Dev mode setup

> [!WARNING]
> This section is not required if you are not planning on running a customized setup. For any related assistance, contact us on [discord](https://discord.com/invite/powerloom).

If you wish to customize the docker containers being launched by not using the published images from Powerloom, and instead clone the underlying snapshotter components locally and building their images, we support that as well now.

Ref: [Step 2](https://github.com/PowerLoom/snapshotter-lite-v2/blob/main/README.md), after running `./bootstrap.sh` , you can edit the generated `.env-mainnet-UNISWAPV2-ETH` file for the following fields

``` bash
DEV_MODE=False  # you can set this to True
# subseqeuently you can specify the branch of [https://github.com/PowerLoom/snapshotter-lite-v2](https://github.com/PowerLoom/snapshotter-lite-v2) that you wish to run
LITE_NODE_BRANCH=main
```