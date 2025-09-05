#!/usr/bin/env python3
"""
Linux packaging script for VidTanium
Creates AppImage, deb, and rpm packages for comprehensive Linux distribution
"""

import os
import sys
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from build_config import BuildConfig, get_build_config, BuildProfile

class LinuxPackager:
    """Linux package builder for multiple formats"""
    
    def __init__(self, config: BuildConfig):
        self.config = config
        self.project_root = Path(__file__).parent.parent
        self.dist_dir = self.project_root / "dist"
        self.build_dir = self.project_root / "build_linux"
        
    def create_desktop_file(self) -> str:
        """Create .desktop file for Linux"""
        desktop_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name={self.config.app_name}
Comment={self.config.description}
Exec={self.config.app_name.lower()}
Icon={self.config.app_name.lower()}
Terminal=false
Categories=AudioVideo;Video;Network;
Keywords=video;download;player;editor;
StartupNotify=true
StartupWMClass={self.config.app_name}
"""
        
        desktop_file = self.build_dir / f"{self.config.app_name.lower()}.desktop"
        desktop_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(desktop_file, 'w') as f:
            f.write(desktop_content)
        
        return str(desktop_file)
    
    def create_appimage(self) -> bool:
        """Create AppImage package"""
        print("📦 Creating AppImage...")
        
        try:
            # Create AppDir structure
            appdir = self.build_dir / "AppDir"
            if appdir.exists():
                shutil.rmtree(appdir)
            
            # Create directory structure
            (appdir / "usr" / "bin").mkdir(parents=True)
            (appdir / "usr" / "share" / "applications").mkdir(parents=True)
            (appdir / "usr" / "share" / "icons" / "hicolor" / "256x256" / "apps").mkdir(parents=True)
            
            # Copy executable
            exe_source = self.dist_dir / self.config.app_name
            if not exe_source.exists():
                exe_source = self.dist_dir / f"{self.config.app_name}.exe"
            
            if not exe_source.exists():
                print(f"❌ Executable not found: {exe_source}")
                return False
            
            exe_dest = appdir / "usr" / "bin" / self.config.app_name.lower()
            if exe_source.is_dir():
                shutil.copytree(exe_source, exe_dest)
            else:
                shutil.copy2(exe_source, exe_dest)
                os.chmod(exe_dest, 0o755)
            
            # Create desktop file
            desktop_file = self.create_desktop_file()
            shutil.copy2(desktop_file, appdir / "usr" / "share" / "applications")
            shutil.copy2(desktop_file, appdir)  # Also in root for AppImage
            
            # Copy icon if available
            icon_source = self.project_root / "assets" / "icon.png"
            if icon_source.exists():
                icon_dest = appdir / "usr" / "share" / "icons" / "hicolor" / "256x256" / "apps" / f"{self.config.app_name.lower()}.png"
                shutil.copy2(icon_source, icon_dest)
                shutil.copy2(icon_source, appdir / f"{self.config.app_name.lower()}.png")
            
            # Create AppRun script
            apprun_content = f"""#!/bin/bash
# AppRun script for {self.config.app_name}
HERE="$(dirname "$(readlink -f "${{0}}")")"
export PATH="${{HERE}}/usr/bin:${{PATH}}"
export LD_LIBRARY_PATH="${{HERE}}/usr/lib:${{LD_LIBRARY_PATH}}"
exec "${{HERE}}/usr/bin/{self.config.app_name.lower}" "$@"
"""
            
            apprun_file = appdir / "AppRun"
            with open(apprun_file, 'w') as f:
                f.write(apprun_content)
            os.chmod(apprun_file, 0o755)
            
            # Download and use appimagetool
            appimage_name = f"{self.config.app_name}-{self.config.app_version}-x86_64.AppImage"
            appimage_path = self.dist_dir / appimage_name
            
            # Try to use appimagetool
            try:
                result = subprocess.run([
                    "appimagetool", str(appdir), str(appimage_path)
                ], capture_output=True, text=True, check=True)
                
                print(f"✅ Created AppImage: {appimage_path}")
                return True
                
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("⚠️  appimagetool not found, creating simple archive instead")
                
                # Create tar.gz as fallback
                archive_name = f"{self.config.app_name}-{self.config.app_version}-linux-x86_64.tar.gz"
                archive_path = self.dist_dir / archive_name
                
                subprocess.run([
                    "tar", "-czf", str(archive_path), "-C", str(appdir.parent), appdir.name
                ], check=True)
                
                print(f"✅ Created archive: {archive_path}")
                return True
                
        except Exception as e:
            print(f"❌ Failed to create AppImage: {e}")
            return False
    
    def create_deb_package(self) -> bool:
        """Create Debian package"""
        print("📦 Creating DEB package...")
        
        try:
            # Create package structure
            pkg_dir = self.build_dir / "deb"
            if pkg_dir.exists():
                shutil.rmtree(pkg_dir)
            
            # Create DEBIAN directory
            debian_dir = pkg_dir / "DEBIAN"
            debian_dir.mkdir(parents=True)
            
            # Create application directories
            app_dir = pkg_dir / "usr" / "bin"
            app_dir.mkdir(parents=True)
            
            desktop_dir = pkg_dir / "usr" / "share" / "applications"
            desktop_dir.mkdir(parents=True)
            
            icon_dir = pkg_dir / "usr" / "share" / "icons" / "hicolor" / "256x256" / "apps"
            icon_dir.mkdir(parents=True)
            
            # Copy executable
            exe_source = self.dist_dir / self.config.app_name
            if not exe_source.exists():
                exe_source = self.dist_dir / f"{self.config.app_name}.exe"
            
            if not exe_source.exists():
                print(f"❌ Executable not found: {exe_source}")
                return False
            
            exe_dest = app_dir / self.config.app_name.lower()
            if exe_source.is_dir():
                shutil.copytree(exe_source, exe_dest)
            else:
                shutil.copy2(exe_source, exe_dest)
                os.chmod(exe_dest, 0o755)
            
            # Copy desktop file
            desktop_file = self.create_desktop_file()
            shutil.copy2(desktop_file, desktop_dir)
            
            # Copy icon
            icon_source = self.project_root / "assets" / "icon.png"
            if icon_source.exists():
                shutil.copy2(icon_source, icon_dir / f"{self.config.app_name.lower()}.png")
            
            # Create control file
            control_content = f"""Package: {self.config.app_name.lower()}
Version: {self.config.app_version}
Section: video
Priority: optional
Architecture: amd64
Depends: libc6, libgcc-s1, libstdc++6
Maintainer: {self.config.author} <noreply@vidtanium.com>
Description: {self.config.description}
 VidTanium is a comprehensive video download tool with built-in player
 and editor capabilities. It supports multiple video formats and
 provides an intuitive user interface for managing video downloads.
"""
            
            with open(debian_dir / "control", 'w') as f:
                f.write(control_content)
            
            # Build package
            deb_name = f"{self.config.app_name.lower()}_{self.config.app_version}_amd64.deb"
            deb_path = self.dist_dir / deb_name
            
            subprocess.run([
                "dpkg-deb", "--build", str(pkg_dir), str(deb_path)
            ], check=True)
            
            print(f"✅ Created DEB package: {deb_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create DEB package: {e}")
            return False
    
    def create_rpm_package(self) -> bool:
        """Create RPM package"""
        print("📦 Creating RPM package...")
        
        try:
            # Create RPM build structure
            rpm_root = self.build_dir / "rpm"
            if rpm_root.exists():
                shutil.rmtree(rpm_root)
            
            for subdir in ["BUILD", "RPMS", "SOURCES", "SPECS", "SRPMS"]:
                (rpm_root / subdir).mkdir(parents=True)
            
            # Create spec file
            spec_content = f"""Name: {self.config.app_name.lower()}
Version: {self.config.app_version}
Release: 1%{{?dist}}
Summary: {self.config.description}

License: MIT
URL: https://github.com/AstroAir/VidTanium
Source0: %{{name}}-%{{version}}.tar.gz

BuildArch: x86_64
Requires: glibc, libgcc, libstdc++

%description
VidTanium is a comprehensive video download tool with built-in player
and editor capabilities. It supports multiple video formats and
provides an intuitive user interface for managing video downloads.

%prep
%setup -q

%build
# Nothing to build, pre-compiled

%install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/usr/bin
mkdir -p $RPM_BUILD_ROOT/usr/share/applications
mkdir -p $RPM_BUILD_ROOT/usr/share/icons/hicolor/256x256/apps

cp {self.config.app_name.lower()} $RPM_BUILD_ROOT/usr/bin/
cp {self.config.app_name.lower()}.desktop $RPM_BUILD_ROOT/usr/share/applications/
cp {self.config.app_name.lower()}.png $RPM_BUILD_ROOT/usr/share/icons/hicolor/256x256/apps/

%files
/usr/bin/{self.config.app_name.lower()}
/usr/share/applications/{self.config.app_name.lower()}.desktop
/usr/share/icons/hicolor/256x256/apps/{self.config.app_name.lower()}.png

%changelog
* {__import__('datetime').datetime.now().strftime('%a %b %d %Y')} {self.config.author} <noreply@vidtanium.com> - {self.config.app_version}-1
- Initial RPM package
"""
            
            spec_file = rpm_root / "SPECS" / f"{self.config.app_name.lower()}.spec"
            with open(spec_file, 'w') as f:
                f.write(spec_content)
            
            print(f"✅ Created RPM spec file: {spec_file}")
            print("💡 To build RPM, run: rpmbuild -ba " + str(spec_file))
            return True
            
        except Exception as e:
            print(f"❌ Failed to create RPM package: {e}")
            return False

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Linux package builder for VidTanium")
    parser.add_argument("--profile", type=str, choices=[p.value for p in BuildProfile],
                       default=BuildProfile.RELEASE.value, help="Build profile")
    parser.add_argument("--appimage", action="store_true", help="Create AppImage")
    parser.add_argument("--deb", action="store_true", help="Create DEB package")
    parser.add_argument("--rpm", action="store_true", help="Create RPM package")
    parser.add_argument("--all", action="store_true", help="Create all package types")
    
    args = parser.parse_args()
    
    # Get configuration
    profile = BuildProfile(args.profile)
    config = get_build_config(profile)
    
    # Create packager
    packager = LinuxPackager(config)
    
    print(f"🐧 Creating Linux packages for {config.app_name} v{config.app_version}")
    print(f"Profile: {config.profile.value}")
    print()
    
    success = True
    
    if args.all or args.appimage:
        success &= packager.create_appimage()
    
    if args.all or args.deb:
        success &= packager.create_deb_package()
    
    if args.all or args.rpm:
        success &= packager.create_rpm_package()
    
    if not any([args.appimage, args.deb, args.rpm, args.all]):
        print("No package type specified. Use --all or specify individual types.")
        success = False
    
    if success:
        print("\n🎉 Linux packaging completed successfully!")
    else:
        print("\n❌ Some packages failed to build")
        sys.exit(1)

if __name__ == "__main__":
    main()
