# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for the voice assistant.

Build commands:
  Windows:  pyinstaller assistant.spec
  Linux:    pyinstaller assistant.spec
  macOS:    pyinstaller assistant.spec

Output lands in dist/assistant/  (--onedir, not --onefile, because torch is huge).
Models (Whisper, Silero) are NOT bundled — downloaded at first run into ~/.cache.
"""

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

# ── Whisper assets (mel filters, vocabulary, etc.) ────────────────────────────
whisper_datas = collect_data_files("whisper")

# ── soundfile needs libsndfile ─────────────────────────────────────────────────
soundfile_datas = collect_data_files("soundfile")
soundfile_bins  = collect_dynamic_libs("soundfile")

block_cipher = None

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=soundfile_bins,
    datas=whisper_datas + soundfile_datas,
    hiddenimports=[
        # torch
        "torch",
        "torch.nn",
        "torch.nn.functional",
        "torchaudio",
        # whisper
        "whisper",
        "whisper.audio",
        "whisper.decoding",
        "whisper.model",
        "whisper.tokenizer",
        "whisper.transcribe",
        "whisper.utils",
        # silero (loaded via torch.hub — dynamic import)
        "omegaconf",
        "tqdm",
        # audio
        "sounddevice",
        "soundfile",
        "_soundfile",
        # Qt
        "PyQt5",
        "PyQt5.QtCore",
        "PyQt5.QtGui",
        "PyQt5.QtWidgets",
        # input
        "pynput",
        "pynput.keyboard",
        "pynput.mouse",
        # PIL
        "PIL",
        "PIL.ImageGrab",
        # misc
        "dotenv",
        "requests",
        "numpy",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=["hook_torch_dll.py"],
    excludes=[
        "torchvision",
        "pytest",
        "IPython",
        "matplotlib",
        "scipy",
        "sklearn",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="assistant",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,          # compress binaries (needs upx installed)
    console=True,      # keep console for print() debug output
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="assistant",
)
