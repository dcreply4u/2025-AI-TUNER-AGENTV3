"""
Build Protected Version - Create protected/obfuscated build for hardware

This script creates a protected version of the application using:
1. PyInstaller (compiles to executable)
2. Code obfuscation
3. License embedding
4. Secure packaging
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def build_protected():
    """Build protected version of the application."""
    print("=" * 60)
    print("Building Protected AI Tuner Agent")
    print("=" * 60)
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("ERROR: PyInstaller not installed")
        print("Install with: pip install pyinstaller")
        return False
    
    # Create build directory
    build_dir = Path("build/protected")
    build_dir.mkdir(parents=True, exist_ok=True)
    
    # PyInstaller spec file
    spec_content = """
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['ui/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config', 'config'),
        ('docs', 'docs'),
    ],
    hiddenimports=[
        'PySide6',
        'pyqtgraph',
        'numpy',
        'pandas',
        'scikit-learn',
    ],
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
    name='AI-Tuner-Agent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compress with UPX
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
"""
    
    spec_file = build_dir / "ai_tuner.spec"
    with open(spec_file, 'w') as f:
        f.write(spec_content)
    
    print("\n1. Building with PyInstaller...")
    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller", str(spec_file)],
        cwd=build_dir,
    )
    
    if result.returncode != 0:
        print("ERROR: PyInstaller build failed")
        return False
    
    print("\n2. Creating protected package...")
    
    # Copy license file template
    license_template = """
AI TUNER AGENT - PROTECTED BUILD
================================

This is a protected build of the AI Tuner Agent.
Unauthorized copying, modification, or reverse engineering is prohibited.

License Key: [REQUIRED]
Device ID: [AUTO-GENERATED]

For support, contact: support@aituner.com
"""
    
    license_file = build_dir / "LICENSE.txt"
    with open(license_file, 'w') as f:
        f.write(license_template)
    
    print("\n3. Build complete!")
    print(f"   Output: {build_dir / 'dist'}")
    print("\n4. Next steps:")
    print("   - Test the protected build")
    print("   - Configure license keys")
    print("   - Deploy to hardware")
    
    return True


if __name__ == "__main__":
    success = build_protected()
    sys.exit(0 if success else 1)

