# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for UCSI Decoder Web Application
Build command: pyinstaller UCSIDecoder.spec
"""
import os
# Project root is the parent of the scripts/ folder
ROOT = os.path.abspath(os.path.join(SPECPATH, '..'))

block_cipher = None

a = Analysis(
    [os.path.join(ROOT, 'app.py')],
    pathex=[ROOT],
    binaries=[(os.path.join(ROOT, 'scripts', 'UcsiControl.exe'), '.')] if os.path.exists(os.path.join(ROOT, 'scripts', 'UcsiControl.exe')) else [],
    datas=[
        (os.path.join(ROOT, 'app/templates'), 'app/templates'),
        (os.path.join(ROOT, 'app/static'), 'app/static'),
        (os.path.join(ROOT, 'decoders'), 'decoders'),
        (os.path.join(ROOT, 'aardvark'), 'aardvark'),
    ],
    hiddenimports=[
        'flask',
        'werkzeug',
        'serial',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
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
    name='UCSIDecoder',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
