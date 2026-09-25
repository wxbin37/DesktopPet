# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files


block_cipher = None

datas = [("assets", "assets")]

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
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
    [],
    exclude_binaries=True,
    name="DesktopPetLulu",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
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
    name="DesktopPetLulu",
)

app = BUNDLE(
    coll,
    name="DesktopPetLulu.app",
    icon="assets/lulu.icns",
    bundle_identifier="com.desktop.pet.lulu",
    info_plist={
        "CFBundleName": "DesktopPetLulu",
        "CFBundleDisplayName": "DesktopPetLulu",
        "CFBundleShortVersionString": "1.1.0",
        "CFBundleVersion": "1.1.0",
        "LSUIElement": True,
        "NSInputMonitoringUsageDescription": "用于在你敲键盘时让桌宠播放打字动画。",
        "NSAccessibilityUsageDescription": "用于让桌宠保持在最前端并响应桌面互动。",
        "NSHumanReadableCopyright": "MIT License",
    },
)
