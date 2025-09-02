#!/usr/bin/env python3
"""
PyInstaller build configuration for VidTanium
This script handles the complete build process for creating standalone executables
"""

import os
import sys
import shutil
import subprocess
import platform
from pathlib import Path
from typing import List, Dict, Any

# Build configuration
BUILD_CONFIG = {
    "app_name": "VidTanium",
    "app_version": "0.1.0",
    "description": "Video Download Tool",
    "author": "VidTanium Team",
    "main_script": "main.py",
    "icon_file": "assets/icon.ico",  # Will be created if doesn't exist
    "console": False,  # Set to True for debug builds
    "onefile": True,   # Set to False for directory distribution
    "debug": False,    # Set to True for debug builds
    "upx": True,       # Use UPX compression if available
    "clean": True,     # Clean build directories before building
}

# Additional data files and directories to include
DATA_FILES = [
    ("src/locales", "locales"),
    ("config", "config"),
    ("docs/README.md", "README.md"),
    ("LICENSE", "LICENSE.txt"),
]

# Hidden imports that PyInstaller might miss
HIDDEN_IMPORTS = [
    "src.core.downloader",
    "src.core.analyzer",
    "src.core.decryptor", 
    "src.core.m3u8_parser",
    "src.core.media_processor",
    "src.core.merger",
    "src.core.scheduler",
    "src.core.thread_pool",
    "src.core.url_extractor",
    "src.gui.dialogs.task_dialog",
    "src.gui.dialogs.about_dialog",
    "src.gui.dialogs.batch_url_dialog",
    "src.gui.widgets.task_manager",
    "src.gui.widgets.log.log_viewer",
    "src.gui.widgets.dashboard.dashboard_interface",
    "src.gui.widgets.settings",
    "src.gui.utils.formatters",
    "src.gui.utils.i18n",
    "src.gui.utils.theme",
    "qfluentwidgets",
    "PySide6.QtCore",
    "PySide6.QtGui", 
    "PySide6.QtWidgets",
    "loguru",
    "requests",
    "cryptography.fernet",
    "cryptography.hazmat.primitives.ciphers",
    "cryptography.hazmat.backends",
]

# Packages to exclude from the build
EXCLUDES = [
    "test",
    "tests", 
    "unittest",
    "pytest",
    "jupyter",
    "notebook",
    "IPython",
    "matplotlib",
    "scipy",
    "numpy.tests",
    "pandas.tests",
]

def get_project_root() -> Path:
    """Get the project root directory"""
    return Path(__file__).parent

def create_icon_if_missing():
    """Create a default icon if none exists"""
    icon_path = get_project_root() / BUILD_CONFIG["icon_file"]
    if not icon_path.exists():
        print(f"Creating default icon at {icon_path}")
        # Create assets directory if it doesn't exist
        icon_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create a simple placeholder icon
        # In a real scenario, you'd want to provide a proper .ico file
        try:
            from PIL import Image, ImageDraw
            # Create a simple 256x256 icon
            img = Image.new('RGBA', (256, 256), (102, 126, 234, 255))
            draw = ImageDraw.Draw(img)
            
            # Draw a simple "V" shape
            draw.polygon([(60, 60), (128, 180), (196, 60), (170, 60), (128, 140), (86, 60)], 
                        fill=(255, 255, 255, 255))
            
            # Save as ICO
            img.save(icon_path, format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
            print(f"✅ Created default icon: {icon_path}")
        except ImportError:
            print("⚠️  PIL not available, creating without icon")
            BUILD_CONFIG["icon_file"] = None
        except Exception as e:
            print(f"⚠️  Could not create icon: {e}")
            BUILD_CONFIG["icon_file"] = None

def clean_build_dirs():
    """Clean build and dist directories"""
    if not BUILD_CONFIG["clean"]:
        return
        
    project_root = get_project_root()
    dirs_to_clean = ["build", "dist", "__pycache__"]
    
    for dir_name in dirs_to_clean:
        dir_path = project_root / dir_name
        if dir_path.exists():
            print(f"🧹 Cleaning {dir_path}")
            shutil.rmtree(dir_path)

def check_dependencies():
    """Check if all required dependencies are available"""
    required_packages = ["PyInstaller", "PySide6", "qfluentwidgets", "loguru", "requests", "cryptography"]
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.lower().replace("-", "_"))
            print(f"✅ {package} is available")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} is missing")
    
    if missing_packages:
        print(f"\n❌ Missing required packages: {', '.join(missing_packages)}")
        print("Install them with: pip install " + " ".join(missing_packages))
        return False
    
    return True

def check_upx():
    """Check if UPX is available for compression"""
    if not BUILD_CONFIG["upx"]:
        return False
        
    try:
        result = subprocess.run(["upx", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ UPX is available for compression")
            return True
    except FileNotFoundError:
        pass
    
    print("⚠️  UPX not found, building without compression")
    return False

def generate_spec_file() -> str:
    """Generate PyInstaller spec file"""
    project_root = get_project_root()
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# Project root
project_root = Path(r"{project_root}")

# Data files to include
datas = [
'''
    
    # Add data files
    for src, dst in DATA_FILES:
        src_path = project_root / src
        if src_path.exists():
            spec_content += f'    (r"{src_path}", "{dst}"),\n'
    
    spec_content += ''']

# Hidden imports
hiddenimports = [
'''
    
    for import_name in HIDDEN_IMPORTS:
        spec_content += f'    "{import_name}",\n'
    
    spec_content += ''']

# Excludes
excludes = [
'''
    
    for exclude in EXCLUDES:
        spec_content += f'    "{exclude}",\n'
    
    spec_content += f''']

block_cipher = None

a = Analysis(
    [r"{project_root / BUILD_CONFIG['main_script']}"],
    pathex=[r"{project_root}"],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
'''

    if BUILD_CONFIG["onefile"]:
        spec_content += f'''
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="{BUILD_CONFIG['app_name']}",
    debug={BUILD_CONFIG['debug']},
    bootloader_ignore_signals=False,
    strip=False,
    upx={BUILD_CONFIG['upx'] and check_upx()},
    upx_exclude=[],
    runtime_tmpdir=None,
    console={BUILD_CONFIG['console']},
'''
        
        if BUILD_CONFIG["icon_file"] and (project_root / BUILD_CONFIG["icon_file"]).exists():
            spec_content += f'    icon=r"{project_root / BUILD_CONFIG["icon_file"]}",\n'
            
        if platform.system() == "Windows":
            spec_content += f'''    version_file=r"{project_root / 'version_info.txt'}",
'''
        
        spec_content += ')\n'
    else:
        spec_content += f'''
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="{BUILD_CONFIG['app_name']}",
    debug={BUILD_CONFIG['debug']},
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console={BUILD_CONFIG['console']},
'''
        
        if BUILD_CONFIG["icon_file"] and (project_root / BUILD_CONFIG["icon_file"]).exists():
            spec_content += f'    icon=r"{project_root / BUILD_CONFIG["icon_file"]}",\n'
            
        spec_content += ''')

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True and upx_available,
    upx_exclude=[],
    name="VidTanium",
)
'''
    
    spec_file_path = project_root / f"{BUILD_CONFIG['app_name']}.spec"
    with open(spec_file_path, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print(f"✅ Generated spec file: {spec_file_path}")
    return str(spec_file_path)

def create_version_info():
    """Create version info file for Windows builds"""
    if platform.system() != "Windows":
        return
        
    project_root = get_project_root()
    version_info_content = f'''# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'{BUILD_CONFIG["author"]}'),
        StringStruct(u'FileDescription', u'{BUILD_CONFIG["description"]}'),
        StringStruct(u'FileVersion', u'{BUILD_CONFIG["app_version"]}'),
        StringStruct(u'InternalName', u'{BUILD_CONFIG["app_name"]}'),
        StringStruct(u'LegalCopyright', u'Copyright © 2025 {BUILD_CONFIG["author"]}'),
        StringStruct(u'OriginalFilename', u'{BUILD_CONFIG["app_name"]}.exe'),
        StringStruct(u'ProductName', u'{BUILD_CONFIG["app_name"]}'),
        StringStruct(u'ProductVersion', u'{BUILD_CONFIG["app_version"]}')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
'''
    
    version_file_path = project_root / "version_info.txt"
    with open(version_file_path, 'w', encoding='utf-8') as f:
        f.write(version_info_content)
    
    print(f"✅ Created version info: {version_file_path}")

def build_executable(spec_file: str) -> bool:
    """Build the executable using PyInstaller"""
    try:
        cmd = ["pyinstaller", "--clean", spec_file]
        
        if BUILD_CONFIG["debug"]:
            cmd.append("--debug=all")
        
        print(f"🔨 Building executable...")
        print(f"Command: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, cwd=get_project_root(), check=True)
        
        if result.returncode == 0:
            print("✅ Build completed successfully!")
            return True
        else:
            print(f"❌ Build failed with return code: {result.returncode}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        return False
    except FileNotFoundError:
        print("❌ PyInstaller not found. Install with: pip install pyinstaller")
        return False

def post_build_tasks():
    """Perform post-build tasks like copying additional files"""
    project_root = get_project_root()
    dist_dir = project_root / "dist"
    
    if not dist_dir.exists():
        print("❌ Dist directory not found")
        return
    
    print("📦 Performing post-build tasks...")
    
    # Copy additional documentation
    additional_files = [
        ("CHANGELOG.md", "CHANGELOG.md"),
        ("CONTRIBUTING.md", "CONTRIBUTING.md"),
        ("docs/USER_MANUAL.md", "USER_MANUAL.md"),
    ]
    
    for src, dst in additional_files:
        src_path = project_root / src
        if src_path.exists():
            if BUILD_CONFIG["onefile"]:
                dst_path = dist_dir / dst
            else:
                dst_path = dist_dir / BUILD_CONFIG["app_name"] / dst
            
            try:
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_path, dst_path)
                print(f"✅ Copied {src} -> {dst}")
            except Exception as e:
                print(f"⚠️  Could not copy {src}: {e}")

def create_installer_script():
    """Create installer script for easier distribution"""
    project_root = get_project_root()
    
    if platform.system() == "Windows":
        # Create NSIS installer script
        nsis_content = f'''!include "MUI2.nsh"

Name "{BUILD_CONFIG['app_name']}"
OutFile "{BUILD_CONFIG['app_name']}_Setup.exe"
InstallDir "$PROGRAMFILES\\{BUILD_CONFIG['app_name']}"
InstallDirRegKey HKCU "Software\\{BUILD_CONFIG['app_name']}" ""
RequestExecutionLevel admin

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

Section "MainSection" SEC01
  SetOutPath "$INSTDIR"
  File "dist\\{BUILD_CONFIG['app_name']}.exe"
  File "LICENSE.txt"
  File "README.md"
  
  CreateDirectory "$SMPROGRAMS\\{BUILD_CONFIG['app_name']}"
  CreateShortCut "$SMPROGRAMS\\{BUILD_CONFIG['app_name']}\\{BUILD_CONFIG['app_name']}.lnk" "$INSTDIR\\{BUILD_CONFIG['app_name']}.exe"
  CreateShortCut "$DESKTOP\\{BUILD_CONFIG['app_name']}.lnk" "$INSTDIR\\{BUILD_CONFIG['app_name']}.exe"
  
  WriteRegStr HKCU "Software\\{BUILD_CONFIG['app_name']}" "" $INSTDIR
  WriteUninstaller "$INSTDIR\\uninstall.exe"
SectionEnd

Section "Uninstall"
  Delete "$INSTDIR\\{BUILD_CONFIG['app_name']}.exe"
  Delete "$INSTDIR\\LICENSE.txt"
  Delete "$INSTDIR\\README.md"
  Delete "$INSTDIR\\uninstall.exe"
  
  Delete "$SMPROGRAMS\\{BUILD_CONFIG['app_name']}\\{BUILD_CONFIG['app_name']}.lnk"
  Delete "$DESKTOP\\{BUILD_CONFIG['app_name']}.lnk"
  RMDir "$SMPROGRAMS\\{BUILD_CONFIG['app_name']}"
  RMDir "$INSTDIR"
  
  DeleteRegKey /ifempty HKCU "Software\\{BUILD_CONFIG['app_name']}"
SectionEnd
'''
        
        nsis_file = project_root / f"{BUILD_CONFIG['app_name']}_installer.nsi"
        with open(nsis_file, 'w', encoding='utf-8') as f:
            f.write(nsis_content)
        
        print(f"✅ Created NSIS installer script: {nsis_file}")
        print("💡 To create installer, install NSIS and run: makensis VidTanium_installer.nsi")
    
    elif platform.system() == "Darwin":
        # Create macOS app bundle script
        app_bundle_script = f'''#!/bin/bash
# Create macOS app bundle
APP_NAME="{BUILD_CONFIG['app_name']}"
BUNDLE_DIR="dist/$APP_NAME.app"

mkdir -p "$BUNDLE_DIR/Contents/MacOS"
mkdir -p "$BUNDLE_DIR/Contents/Resources"

# Copy executable
cp "dist/$APP_NAME" "$BUNDLE_DIR/Contents/MacOS/"

# Create Info.plist
cat > "$BUNDLE_DIR/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>$APP_NAME</string>
    <key>CFBundleIdentifier</key>
    <string>com.vidtanium.app</string>
    <key>CFBundleName</key>
    <string>$APP_NAME</string>
    <key>CFBundleVersion</key>
    <string>{BUILD_CONFIG['app_version']}</string>
    <key>CFBundleShortVersionString</key>
    <string>{BUILD_CONFIG['app_version']}</string>
</dict>
</plist>
EOF

echo "✅ Created macOS app bundle: $BUNDLE_DIR"
'''
        
        script_file = project_root / "create_app_bundle.sh"
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(app_bundle_script)
        
        # Make script executable
        os.chmod(script_file, 0o755)
        print(f"✅ Created app bundle script: {script_file}")

def main():
    """Main build function"""
    print(f"🚀 Building {BUILD_CONFIG['app_name']} v{BUILD_CONFIG['app_version']}")
    print(f"Platform: {platform.system()} {platform.machine()}")
    print(f"Python: {sys.version}")
    print()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Clean build directories
    clean_build_dirs()
    
    # Create icon if missing
    create_icon_if_missing()
    
    # Create version info for Windows
    create_version_info()
    
    # Generate spec file
    spec_file = generate_spec_file()
    
    # Build executable
    if build_executable(spec_file):
        # Post-build tasks
        post_build_tasks()
        
        # Create installer script
        create_installer_script()
        
        print()
        print("🎉 Build completed successfully!")
        
        # Show output location
        project_root = get_project_root()
        if BUILD_CONFIG["onefile"]:
            output_path = project_root / "dist" / f"{BUILD_CONFIG['app_name']}.exe"
        else:
            output_path = project_root / "dist" / BUILD_CONFIG["app_name"]
        
        print(f"📦 Output: {output_path}")
        
        if output_path.exists():
            if output_path.is_file():
                size_mb = output_path.stat().st_size / 1024 / 1024
                print(f"📏 Size: {size_mb:.1f} MB")
            print(f"✅ Executable is ready!")
        else:
            print("❌ Output file not found!")
            sys.exit(1)
    else:
        print("❌ Build failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
