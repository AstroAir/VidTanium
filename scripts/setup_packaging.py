#!/usr/bin/env python3
"""
Setup script for VidTanium packaging system
Initializes the packaging environment and makes scripts executable
"""

import os
import sys
import stat
import platform
from pathlib import Path

def make_executable(file_path: Path):
    """Make a file executable on Unix systems"""
    if platform.system() != "Windows":
        current_permissions = file_path.stat().st_mode
        file_path.chmod(current_permissions | stat.S_IEXEC)

def setup_packaging_system():
    """Initialize the packaging system"""
    project_root = Path(__file__).parent.parent
    scripts_dir = project_root / "scripts"
    
    print("🚀 Setting up VidTanium packaging system...")
    print(f"Project root: {project_root}")
    print()
    
    # Scripts to make executable
    scripts_to_setup = [
        "build_config.py",
        "scripts/build_all.py",
        "scripts/build_linux_packages.py",
        "scripts/build_docker.py",
        "scripts/create_msi.py",
        "scripts/create_macos_pkg.py",
        "scripts/auto_updater.py",
        "scripts/package_verification.py",
        "scripts/setup_packaging.py"
    ]
    
    # Shell scripts
    shell_scripts = [
        "create_app_bundle.sh"
    ]
    
    print("📝 Making scripts executable...")
    
    # Make Python scripts executable
    for script_path in scripts_to_setup:
        full_path = project_root / script_path
        if full_path.exists():
            make_executable(full_path)
            print(f"   ✅ {script_path}")
        else:
            print(f"   ⚠️  {script_path} not found")
    
    # Make shell scripts executable
    for script_name in shell_scripts:
        script_path = project_root / script_name
        if script_path.exists():
            make_executable(script_path)
            print(f"   ✅ {script_name}")
        else:
            print(f"   ⚠️  {script_name} not found")
    
    print()
    
    # Create necessary directories
    directories_to_create = [
        "dist",
        "build",
        "assets",
        "downloads",
        "config"
    ]
    
    print("📁 Creating directories...")
    
    for dir_name in directories_to_create:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"   ✅ Created {dir_name}/")
        else:
            print(f"   ✅ {dir_name}/ exists")
    
    print()
    
    # Check dependencies
    print("🔍 Checking dependencies...")
    
    required_python_packages = [
        "uv",
        "build", 
        "pyinstaller",
        "pillow"
    ]
    
    missing_packages = []
    
    for package in required_python_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"   ✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"   ❌ {package}")
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Install with: uv add " + " ".join(missing_packages))
    
    print()
    
    # Check platform-specific tools
    print("🔧 Checking platform-specific tools...")
    
    if platform.system() == "Windows":
        tools_to_check = [
            ("nsis", "NSIS installer creator"),
            ("candle", "WiX Toolset compiler"),
            ("signtool", "Code signing tool")
        ]
    elif platform.system() == "Darwin":
        tools_to_check = [
            ("codesign", "Code signing tool"),
            ("pkgbuild", "Package builder"),
            ("hdiutil", "Disk image utility")
        ]
    else:  # Linux
        tools_to_check = [
            ("dpkg-deb", "Debian package builder"),
            ("rpmbuild", "RPM package builder"),
            ("appimagetool", "AppImage creator"),
            ("gpg", "GPG signing tool")
        ]
    
    for tool, description in tools_to_check:
        try:
            import subprocess
            subprocess.run([tool, "--help"], capture_output=True, check=True)
            print(f"   ✅ {tool} - {description}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"   ⚠️  {tool} - {description} (optional)")
    
    print()
    
    # Check Docker
    print("🐳 Checking Docker...")
    try:
        import subprocess
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True, check=True)
        print(f"   ✅ {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("   ⚠️  Docker not found (optional)")
    
    print()
    
    # Display usage information
    print("📋 Packaging System Ready!")
    print()
    print("Quick Start Commands:")
    print("   python build_config.py                    # Basic build")
    print("   python scripts/build_all.py               # Comprehensive build")
    print("   python scripts/build_docker.py            # Docker images")
    print("   python scripts/package_verification.py    # Verify packages")
    print()
    print("Platform-Specific:")
    
    if platform.system() == "Windows":
        print("   python scripts/create_msi.py             # Windows MSI installer")
    elif platform.system() == "Darwin":
        print("   ./create_app_bundle.sh                   # macOS app bundle")
        print("   python scripts/create_macos_pkg.py       # macOS PKG installer")
    else:
        print("   python scripts/build_linux_packages.py  # Linux packages")
    
    print()
    print("For detailed documentation, see PACKAGING.md")
    print()
    print("🎉 Setup complete!")

def main():
    """Main setup function"""
    try:
        setup_packaging_system()
    except KeyboardInterrupt:
        print("\n❌ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
