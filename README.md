# Multi node setup for multiple Powerloom Snapshotter Lite: Protocol V2 slot holders on Linux VPS

> [!NOTE]
> This setup is for Lite nodes participating in the latest V2 of Powerloom Protocol with multiple data markets. [Protocol V1 setup](https://github.com/PowerLoom/snapshotter-lite-multi-setup/tree/main) is deprecated and its data markets are archived. Your submission data, rewards on it are finalized and recorded as [announced on Discord](https://discord.com/channels/777248105636560948/1146931631039463484/1242876184509812847).

## 0. Preparation

Clone this repository and change into the repository's directory. All commands will be run within there henceforth.

```bash
git clone https://github.com/PowerLoom/snapshotter-lite-multi-setup.git
cd snapshotter-lite-multi-setup
```

## 1. System Check and Environment Setup

### 1.1 Run Diagnostics
First, run the diagnostic tool to check your system and clean up any existing deployments:
```bash
./diagnose.sh
```
This will help you:
- Verify system requirements
- Detect and manage running instances
- Clean up stale deployments and Docker resources
- Ensure a clean setup environment

### 1.2 Initialize Environment
```bash
./bootstrap.sh
```
This will:
- Back up any existing configuration
- Guide you through setting up required variables
- Create a new .env file with your settings

## 1. Setup Python environment

This is of utmost importance. We want to setup an isolated virtual environment with the right Python version and modules without affecting any global Python installations on the VPS or your local machine.

### 1.1 Install `pyenv`

Detailed instructions and troubleshotting can be found on the [pyenv Github repo README](https://github.com/pyenv/pyenv?tab=readme-ov-file#installation). In general, the following should take care of the installation on an Ubuntu VPS.

```
sudo apt install build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev curl libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
curl https://pyenv.run | bash
pyenv install 3.11.5
source ~/.bashrc
```
### 1.2 Install `pyenv-virtualenv`

Detailed instructions can be [found here](https://github.com/pyenv/pyenv-virtualenv).

```
git clone https://github.com/pyenv/pyenv-virtualenv.git $(pyenv root)/plugins/pyenv-virtualenv
echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc
pyenv virtualenv 3.11.5 ss_lite_multi_311
pyenv local ss_lite_multi_311
```

## 2. Run the setup

```bash
# prepare the .env file
./init.sh
# install all python requirements
pip install -r requirements.txt
# run the setup
python multi_clone.py
```


[<img src="https://img.youtube.com/vi/SPToeDh9MUo/hqdefault.jpg" width="600" height="300"
/>](https://youtu.be/SPToeDh9MUo)



If you encounter any issues, please contact us on [discord](https://discord.com/invite/powerloom).


## [OPTIONAL] Dev mode setup

> [!WARNING]
>This section is not required if you are not planning on running a customized setup. For any related assistance, contact us on [discord](https://discord.com/invite/powerloom).


If you wish to customize the docker containers being launched by not using the published images from Powerloom, and instead clone the underlying snapshotter components locally and building their images, we support that as well now.

Ref: [Step 2](#2-run-the-setup), after running `./init.sh` , you can edit the generated `.env` file for the following fields

```bash
DEV_MODE=False  # you can set this to True
# subseqeuently you can specify the branch of https://github.com/PowerLoom/snapshotter-lite-v2 that you wish to run
LITE_NODE_BRANCH=main
```
