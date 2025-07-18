# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

block_cipher = None

# Get the current directory
current_dir = Path(os.getcwd())

# Determine platform-specific binary name
platform = os.environ.get('PLATFORM', 'unknown')
arch = os.environ.get('ARCH', 'unknown')
binary_name = f'powerloom-snapshotter-cli-{platform}-{arch}'

a = Analysis(
    ['snapshotter_cli/__main__.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        (str(current_dir / 'snapshotter_cli/utils/abi/PowerloomNodes.json'), 'snapshotter_cli/utils/abi'),
        (str(current_dir / 'snapshotter_cli/utils/abi/ProtocolState.json'), 'snapshotter_cli/utils/abi'),
    ],
    hiddenimports=[
        'snapshotter_cli',
        'snapshotter_cli.cli',
        'snapshotter_cli.commands',
        'snapshotter_cli.commands.configure',
        'snapshotter_cli.commands.deploy',
        'snapshotter_cli.commands.diagnose',
        'snapshotter_cli.commands.manage',
        'snapshotter_cli.commands.shell',
        'snapshotter_cli.utils',
        'typer',
        'rich',
        'web3',
        'psutil',
        'pydantic',
        'dotenv',
        'eth_account',
        'eth_utils',
        'hexbytes',
        'cytoolz',
        'eth_typing',
        'eth_abi',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['test', 'tests', 'pytest', 'flaky', '_pytest'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=binary_name,
    debug=False,
    bootloader_ignore_signals=True,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
