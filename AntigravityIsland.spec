# -*- mode: python ; coding: utf-8 -*-

import sys
import os

block_cipher = None

CURRENT_DIR = os.path.abspath(SPECPATH)

datas = [
    (os.path.join(CURRENT_DIR, 'assets', 'app.ico'), 'assets')
]

hiddenimports = [
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'PyQt6.QtNetwork',
    'PyQt6.QtWebSockets',
]

excludes = [
    'PyQt6.QtQml',
    'PyQt6.QtQuick',
    'PyQt6.QtQuickWidgets',
    'PyQt6.QtPdf',
    'PyQt6.QtPdfWidgets',
    'PyQt6.QtMultimedia',
    'PyQt6.QtMultimediaWidgets',
    'PyQt6.QtOpenGL',
    'PyQt6.QtOpenGLWidgets',
    'PyQt6.QtDesigner',
    'PyQt6.QtHelp',
    'PyQt6.QtPrintSupport',
    'PyQt6.QtSpatialAudio',
    'PyQt6.QtTest',
    'PyQt6.QtXml',
    'tkinter',
    'unittest',
    'pydoc',
    'doctest',
    'xmlrpc'
]

a = Analysis(
    ['capsule_gui.py'],
    pathex=[CURRENT_DIR],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
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
    name='AntigravityIsland',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(CURRENT_DIR, 'assets', 'app.ico'),
    version=os.path.join(CURRENT_DIR, 'version_info.txt')
)
