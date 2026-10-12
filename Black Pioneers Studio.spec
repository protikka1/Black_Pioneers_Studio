# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
import os
import shutil
import sys
from PyInstaller.utils.hooks import collect_all, collect_submodules, copy_metadata

root = Path(SPECPATH)
ffmpeg = os.environ.get("BLACK_PIONEERS_FFMPEG") or shutil.which("ffmpeg")
if not ffmpeg or not Path(ffmpeg).is_file():
    raise SystemExit("FFmpeg is missing. Set BLACK_PIONEERS_FFMPEG to its full path.")

datas = [(str(root / "app.py"), "studio"), (str(root / "LICENSE"), "studio")]
binaries = [(str(Path(ffmpeg).resolve()), "bin")]
hiddenimports = []
for package in ("streamlit", "moviepy", "edge_tts", "imageio", "PIL"):
    package_datas, package_binaries, package_imports = collect_all(package)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_imports
for package in ("black_pioneers_studio", "database"):
    hiddenimports += collect_submodules(package)
# The bundled script is interpreted at runtime, so analysis cannot infer its imports.
hiddenimports += ["pandas", "openpyxl", "imageio_ffmpeg", "requests", "streamlit.web.bootstrap"]
for package in ("streamlit", "moviepy", "edge-tts", "imageio-ffmpeg", "pillow"):
    datas += copy_metadata(package, recursive=True)

signing_identity = os.environ.get("BLACK_PIONEERS_CODESIGN_IDENTITY") or None
entitlements = str(root / "scripts" / "mac_entitlements.plist") if signing_identity else None

a = Analysis(
    [str(root / "desktop_launcher.py")], pathex=[str(root)],
    binaries=binaries, datas=datas, hiddenimports=hiddenimports,
    hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[], noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [], exclude_binaries=True, name="Black Pioneers Studio",
    debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
    console=False if sys.platform == "darwin" else True,
    argv_emulation=False, target_arch=None,
    codesign_identity=signing_identity, entitlements_file=entitlements,
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="Black Pioneers Studio")
if sys.platform == "darwin":
    app = BUNDLE(
        coll, name="Black Pioneers Studio.app", icon=None,
        bundle_identifier="com.blackpioneers.studio",
        info_plist={"CFBundleShortVersionString": "1.0.0", "CFBundleVersion": "1",
                    "NSHighResolutionCapable": True},
    )
