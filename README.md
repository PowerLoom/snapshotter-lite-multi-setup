# Multi node setup for multiple Powerloom Snapshotter Lite slot holders on Linux VPS

## 0. Preparation.

Clone this repository. And change into the repository's directory. All commands will be run within there henceforth.

```
git clone https://github.com/PowerLoom/snapshotter-lite-multi-setup.git
cd snapshotter-lite-multi-setup
```

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
