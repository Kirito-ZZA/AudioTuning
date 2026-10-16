# -*- mode: python ; coding: utf-8 -*-

import os
import sys

from PyInstaller.utils.hooks import collect_submodules

base = os.path.abspath(SPECPATH)
sys.path.insert(0, base)
sys.setrecursionlimit(5000)


a = Analysis(
    [os.path.join(base, "app.py")],
    pathex=[base],
    binaries=[],
    datas=[
        (os.path.join(base, "conf"), "conf"),
        (os.path.join(base, "resource"), "resource"),
    ],
    hiddenimports=collect_submodules("filters"),
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="AudioTuning",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=os.path.join(base, "resource", "pic", "app.ico"),
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="AudioTuning",
)
