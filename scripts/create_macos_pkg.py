#!/usr/bin/env python3
"""
macOS PKG installer creator for VidTanium
Creates professional macOS installer packages
"""

import os
import sys
import subprocess
import shutil
import plistlib
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from build_config import BuildConfig, get_build_config, BuildProfile

class MacOSPKGBuilder:
    """Creates macOS PKG installers"""
    
    def __init__(self, config: BuildConfig) -> None:
        self.config = config
        self.project_root = Path(__file__).parent.parent
        self.dist_dir = self.project_root / "dist"
        self.build_dir = self.project_root / "build_macos"
        
    def check_macos_tools(self) -> bool:
        """Check if required macOS tools are available"""
        required_tools = ["pkgbuild", "productbuild", "hdiutil"]
        missing_tools = []
        
        for tool in required_tools:
            try:
                subprocess.run([tool, "--help"], capture_output=True, check=True)
                print(f"✅ {tool} found")
            except (subprocess.CalledProcessError, FileNotFoundError):
                missing_tools.append(tool)
                print(f"❌ {tool} not found")
        
        if missing_tools:
            print(f"Missing tools: {', '.join(missing_tools)}")
            print("These tools are part of Xcode Command Line Tools")
            return False
        
        return True
    
    def create_app_bundle(self) -> Path:
        """Create or locate the app bundle"""
        app_bundle = self.dist_dir / f"{self.config.app_name}.app"
        
        if app_bundle.exists():
            print(f"✅ Found existing app bundle: {app_bundle}")
            return app_bundle
        
        # Create app bundle structure
        print("📦 Creating app bundle...")
        
        contents_dir = app_bundle / "Contents"
        macos_dir = contents_dir / "MacOS"
        resources_dir = contents_dir / "Resources"
        
        for directory in [macos_dir, resources_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Find executable
        exe_source = self.dist_dir / self.config.app_name
        if not exe_source.exists():
            exe_source = self.dist_dir / f"{self.config.app_name}.exe"
        
        if not exe_source.exists():
            raise FileNotFoundError(f"Executable not found in {self.dist_dir}")
        
        # Copy executable
        exe_dest = macos_dir / self.config.app_name
        if exe_source.is_dir():
            shutil.copytree(exe_source, exe_dest)
        else:
            shutil.copy2(exe_source, exe_dest)
        
        os.chmod(exe_dest, 0o755)
        
        # Copy icon if available
        icon_source = self.project_root / "assets" / "icon.icns"
        if icon_source.exists():
            shutil.copy2(icon_source, resources_dir / "icon.icns")
        
        # Create Info.plist
        info_plist = {
            "CFBundleExecutable": self.config.app_name,
            "CFBundleIdentifier": self.config.macos_bundle_id,
            "CFBundleName": self.config.app_name,
            "CFBundleDisplayName": self.config.app_name,
            "CFBundleVersion": self.config.app_version,
            "CFBundleShortVersionString": self.config.app_version,
            "CFBundlePackageType": "APPL",
            "CFBundleSignature": "????",
            "LSMinimumSystemVersion": "10.15",
            "NSHighResolutionCapable": True,
            "NSPrincipalClass": "NSApplication",
            "NSRequiresAquaSystemAppearance": False,
        }
        
        if icon_source.exists():
            info_plist["CFBundleIconFile"] = "icon.icns"
        
        with open(contents_dir / "Info.plist", "wb") as f:
            plistlib.dump(info_plist, f)
        
        print(f"✅ Created app bundle: {app_bundle}")
        return app_bundle
    
    def create_pkg_payload(self, app_bundle: Path) -> Path:
        """Create the payload directory for PKG"""
        payload_dir = self.build_dir / "payload"
        if payload_dir.exists():
            shutil.rmtree(payload_dir)
        
        # Create Applications directory structure
        apps_dir = payload_dir / "Applications"
        apps_dir.mkdir(parents=True)
        
        # Copy app bundle to payload
        dest_bundle = apps_dir / app_bundle.name
        shutil.copytree(app_bundle, dest_bundle)
        
        print(f"✅ Created PKG payload: {payload_dir}")
        return payload_dir
    
    def create_distribution_xml(self) -> Path:
        """Create distribution.xml for productbuild"""
        distribution_xml = f'''<?xml version="1.0" encoding="utf-8"?>
<installer-gui-script minSpecVersion="1">
    <title>{self.config.app_name}</title>
    <organization>{self.config.author}</organization>
    <domains enable_localSystem="true"/>
    <options customize="never" require-scripts="false"/>
    
    <pkg-ref id="{self.config.macos_bundle_id}.pkg"/>
    
    <choices-outline>
        <line choice="default">
            <line choice="{self.config.macos_bundle_id}.pkg"/>
        </line>
    </choices-outline>
    
    <choice id="default"/>
    <choice id="{self.config.macos_bundle_id}.pkg" visible="false">
        <pkg-ref id="{self.config.macos_bundle_id}.pkg"/>
    </choice>
    
    <pkg-ref id="{self.config.macos_bundle_id}.pkg" version="{self.config.app_version}" onConclusion="none">
        {self.config.app_name}.pkg
    </pkg-ref>
    
    <background file="background.png" mime-type="image/png" alignment="topleft" scaling="proportional"/>
    <welcome file="welcome.html" mime-type="text/html"/>
    <license file="license.html" mime-type="text/html"/>
    <readme file="readme.html" mime-type="text/html"/>
    
</installer-gui-script>'''
        
        dist_file = self.build_dir / "distribution.xml"
        with open(dist_file, 'w') as f:
            f.write(distribution_xml)
        
        return dist_file
    
    def create_installer_resources(self) -> None:
        """Create installer resources (welcome, license, etc.)"""
        resources_dir = self.build_dir / "resources"
        resources_dir.mkdir(exist_ok=True)
        
        # Create welcome.html
        welcome_html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Welcome</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .version {{ color: #666; font-size: 14px; }}
    </style>
</head>
<body>
    <h1>Welcome to {self.config.app_name}</h1>
    <p class="version">Version {self.config.app_version}</p>
    <p>{self.config.description}</p>
    <p>This installer will install {self.config.app_name} on your Mac.</p>
    <p>Click Continue to proceed with the installation.</p>
</body>
</html>'''
        
        with open(resources_dir / "welcome.html", 'w') as f:
            f.write(welcome_html)
        
        # Create license.html from LICENSE file
        license_file = self.project_root / "LICENSE"
        if license_file.exists():
            with open(license_file, 'r') as f:
                license_text = f.read()
            
            license_html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>License</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 20px; }}
        pre {{ background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; }}
    </style>
</head>
<body>
    <h1>License Agreement</h1>
    <pre>{license_text}</pre>
</body>
</html>'''
            
            with open(resources_dir / "license.html", 'w') as f:
                f.write(license_html)
        
        # Create readme.html
        readme_html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Read Me</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .info {{ background: #e8f4fd; padding: 15px; border-radius: 5px; margin: 15px 0; }}
    </style>
</head>
<body>
    <h1>{self.config.app_name} Installation</h1>
    
    <div class="info">
        <h3>System Requirements</h3>
        <ul>
            <li>macOS 10.15 (Catalina) or later</li>
            <li>64-bit Intel or Apple Silicon processor</li>
            <li>At least 100 MB of free disk space</li>
        </ul>
    </div>
    
    <div class="info">
        <h3>Installation Location</h3>
        <p>{self.config.app_name} will be installed in your Applications folder.</p>
    </div>
    
    <div class="info">
        <h3>Getting Started</h3>
        <p>After installation, you can find {self.config.app_name} in your Applications folder or launch it from Spotlight.</p>
    </div>
</body>
</html>'''
        
        with open(resources_dir / "readme.html", 'w') as f:
            f.write(readme_html)
        
        print(f"✅ Created installer resources: {resources_dir}")
    
    def build_pkg(self, payload_dir: Path) -> bool:
        """Build the PKG installer"""
        try:
            # Create component PKG
            component_pkg = self.build_dir / f"{self.config.app_name}.pkg"
            
            print("🔨 Building component package...")
            subprocess.run([
                "pkgbuild",
                "--root", str(payload_dir),
                "--identifier", self.config.macos_bundle_id,
                "--version", self.config.app_version,
                "--install-location", "/",
                str(component_pkg)
            ], check=True)
            
            # Create installer resources
            self.create_installer_resources()
            
            # Create distribution XML
            distribution_xml = self.create_distribution_xml()
            
            # Create final installer PKG
            installer_name = f"{self.config.app_name}_v{self.config.app_version}_macOS.pkg"
            installer_pkg = self.dist_dir / installer_name
            
            print("🔗 Building installer package...")
            subprocess.run([
                "productbuild",
                "--distribution", str(distribution_xml),
                "--resources", str(self.build_dir / "resources"),
                "--package-path", str(self.build_dir),
                str(installer_pkg)
            ], check=True)
            
            print(f"✅ Created PKG installer: {installer_pkg}")
            
            # Show file size
            if installer_pkg.exists():
                size_mb = installer_pkg.stat().st_size / 1024 / 1024
                print(f"📏 PKG size: {size_mb:.1f} MB")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ PKG build failed: {e}")
            return False

def main() -> None:
    """Main PKG builder function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="macOS PKG installer builder")
    parser.add_argument("--profile", type=str, choices=[p.value for p in BuildProfile],
                       default=BuildProfile.RELEASE.value, help="Build profile")
    
    args = parser.parse_args()
    
    # Get configuration
    profile = BuildProfile(args.profile)
    config = get_build_config(profile)
    
    print(f"🍎 Creating PKG installer for {config.app_name} v{config.app_version}")
    print(f"Profile: {config.profile.value}")
    print()
    
    # Create PKG builder
    builder = MacOSPKGBuilder(config)
    
    # Check macOS tools
    if not builder.check_macos_tools():
        sys.exit(1)
    
    try:
        # Create or locate app bundle
        app_bundle = builder.create_app_bundle()
        
        # Create PKG payload
        payload_dir = builder.create_pkg_payload(app_bundle)
        
        # Build PKG
        if builder.build_pkg(payload_dir):
            print("\n🎉 PKG installer created successfully!")
            print("\n💡 Next steps:")
            print("   • Test the PKG on different macOS versions")
            print("   • Sign the PKG with a Developer ID certificate")
            print("   • Notarize the PKG with Apple")
            print("   • Upload to distribution channels")
        else:
            print("\n❌ PKG creation failed!")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
