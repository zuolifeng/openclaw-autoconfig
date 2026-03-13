# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for OpenClaw AutoConfig

import os
import sys

block_cipher = None

ROOT = os.path.dirname(os.path.abspath(SPEC))

a = Analysis(
    [os.path.join(ROOT, 'main.py')],
    pathex=[ROOT],
    binaries=[],
    datas=[
        (os.path.join(ROOT, 'locales'), 'locales'),
        (os.path.join(ROOT, 'scripts'), 'scripts'),
        (os.path.join(ROOT, 'assets'), 'assets'),
    ],
    hiddenimports=['tkinter', 'tkinter.ttk', 'tkinter.messagebox', 'tkinter.scrolledtext'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name='OpenClawAutoConfig',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# macOS .app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='OpenClawAutoConfig.app',
        icon=None,
        bundle_identifier='com.openclaw.autoconfig',
        info_plist={
            'CFBundleName': 'OpenClaw AutoConfig',
            'CFBundleDisplayName': 'OpenClaw AutoConfig',
            'CFBundleShortVersionString': '1.0.0',
            'NSHighResolutionCapable': True,
        },
    )
