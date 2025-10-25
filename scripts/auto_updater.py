#!/usr/bin/env python3
"""
Auto-updater system for VidTanium
Handles checking for updates, downloading, and installing new versions
"""

import os
import sys
import json
import hashlib
import tempfile
import subprocess
import platform
from pathlib import Path
from typing import Dict, Optional, Tuple, Any
from urllib.request import urlopen, urlretrieve
from urllib.error import URLError

class VidTaniumUpdater:
    """Auto-updater for VidTanium application"""
    
    def __init__(self, current_version: str = "0.1.0") -> None:
        self.current_version = current_version
        self.github_api_base = "https://api.github.com/repos/AstroAir/VidTanium"
        self.github_releases_url = f"{self.github_api_base}/releases"
        self.platform = platform.system().lower()
        self.architecture = platform.machine().lower()
        
        # Platform-specific file patterns
        self.platform_patterns = {
            "windows": [".exe", ".msi", "_windows.zip"],
            "darwin": [".pkg", ".dmg", "_macos.tar.gz"],
            "linux": [".AppImage", ".deb", ".rpm", "_linux.tar.gz"]
        }
    
    def check_for_updates(self) -> Optional[Dict[str, Any]]:
        """Check if a newer version is available"""
        try:
            print("🔍 Checking for updates...")
            
            # Get latest release info
            with urlopen(f"{self.github_releases_url}/latest") as response:
                release_data = json.loads(response.read().decode())
            
            latest_version = release_data["tag_name"].lstrip("v")
            
            if self._is_newer_version(latest_version, self.current_version):
                print(f"✅ New version available: {latest_version}")
                return {
                    "version": latest_version,
                    "tag_name": release_data["tag_name"],
                    "name": release_data["name"],
                    "body": release_data["body"],
                    "published_at": release_data["published_at"],
                    "assets": release_data["assets"]
                }
            else:
                print(f"✅ You have the latest version: {self.current_version}")
                return None
                
        except URLError as e:
            print(f"❌ Failed to check for updates: {e}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error checking updates: {e}")
            return None
    
    def _is_newer_version(self, latest: str, current: str) -> bool:
        """Compare version strings"""
        def version_tuple(v: str) -> tuple[int, ...]:
            return tuple(map(int, v.split('.')))
        
        try:
            return version_tuple(latest) > version_tuple(current)
        except ValueError:
            # Fallback to string comparison
            return latest > current
    
    def find_suitable_asset(self, assets: list[dict[str, Any]]) -> dict[str, Any] | None:
        """Find the most suitable asset for current platform"""
        if self.platform not in self.platform_patterns:
            print(f"❌ Unsupported platform: {self.platform}")
            return None
        
        patterns = self.platform_patterns[self.platform]
        
        # Look for platform-specific assets
        for asset in assets:
            name = asset["name"].lower()
            
            # Check if asset matches platform patterns
            for pattern in patterns:
                if pattern in name:
                    # Prefer specific architecture if available
                    if self.architecture in name or "x86_64" in name or "amd64" in name:
                        return asset
        
        # Fallback: return first matching pattern
        for asset in assets:
            name = asset["name"].lower()
            for pattern in patterns:
                if pattern in name:
                    return asset
        
        print(f"❌ No suitable asset found for {self.platform}")
        return None
    
    def download_update(self, asset: Dict[str, Any], download_dir: Path) -> Optional[Path]:
        """Download update file"""
        try:
            download_url = asset["browser_download_url"]
            filename = asset["name"]
            file_path = download_dir / filename
            
            print(f"📥 Downloading {filename}...")
            print(f"   Size: {asset['size'] / 1024 / 1024:.1f} MB")
            
            # Download with progress (simple version)
            def progress_hook(block_num, block_size, total_size) -> None:
                if total_size > 0:
                    percent = min(100, (block_num * block_size * 100) // total_size)
                    print(f"\r   Progress: {percent}%", end="", flush=True)
            
            urlretrieve(download_url, file_path, progress_hook)
            print()  # New line after progress
            
            print(f"✅ Downloaded: {file_path}")
            return file_path
            
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return None
    
    def verify_download(self, file_path: Path, expected_size: int) -> bool:
        """Verify downloaded file"""
        try:
            # Check file size
            actual_size = file_path.stat().st_size
            if actual_size != expected_size:
                print(f"❌ Size mismatch: expected {expected_size}, got {actual_size}")
                return False
            
            # TODO: Verify signature if available
            print("✅ Download verification passed")
            return True
            
        except Exception as e:
            print(f"❌ Verification failed: {e}")
            return False
    
    def install_update(self, file_path: Path) -> bool:
        """Install the downloaded update"""
        try:
            print(f"🔧 Installing update from {file_path}")
            
            if self.platform == "windows":
                return self._install_windows(file_path)
            elif self.platform == "darwin":
                return self._install_macos(file_path)
            elif self.platform == "linux":
                return self._install_linux(file_path)
            else:
                print(f"❌ Installation not supported for {self.platform}")
                return False
                
        except Exception as e:
            print(f"❌ Installation failed: {e}")
            return False
    
    def _install_windows(self, file_path: Path) -> bool:
        """Install update on Windows"""
        if file_path.suffix.lower() == ".msi":
            # Run MSI installer
            cmd = ["msiexec", "/i", str(file_path), "/quiet"]
            result = subprocess.run(cmd, capture_output=True)
            return result.returncode == 0
        elif file_path.suffix.lower() == ".exe":
            # Run EXE installer
            result = subprocess.run([str(file_path), "/S"], capture_output=True)
            return result.returncode == 0
        else:
            print("❌ Unsupported Windows installer format")
            return False
    
    def _install_macos(self, file_path: Path) -> bool:
        """Install update on macOS"""
        if file_path.suffix.lower() == ".pkg":
            # Install PKG
            cmd = ["sudo", "installer", "-pkg", str(file_path), "-target", "/"]
            result = subprocess.run(cmd)
            return result.returncode == 0
        elif file_path.suffix.lower() == ".dmg":
            print("💡 Please manually install from the downloaded DMG file")
            subprocess.run(["open", str(file_path)])
            return True
        else:
            print("❌ Unsupported macOS installer format")
            return False
    
    def _install_linux(self, file_path: Path) -> bool:
        """Install update on Linux"""
        if file_path.suffix.lower() == ".appimage":
            # Make AppImage executable and replace current
            os.chmod(file_path, 0o755)
            print("💡 AppImage is ready to use")
            return True
        elif file_path.suffix.lower() == ".deb":
            # Install DEB package
            cmd = ["sudo", "dpkg", "-i", str(file_path)]
            result = subprocess.run(cmd)
            return result.returncode == 0
        elif file_path.suffix.lower() == ".rpm":
            # Install RPM package
            cmd = ["sudo", "rpm", "-U", str(file_path)]
            result = subprocess.run(cmd)
            return result.returncode == 0
        else:
            print("❌ Unsupported Linux package format")
            return False
    
    def update(self, auto_install: bool = False) -> bool:
        """Complete update process"""
        print(f"🚀 VidTanium Auto-Updater")
        print(f"Current version: {self.current_version}")
        print(f"Platform: {self.platform} ({self.architecture})")
        print()
        
        # Check for updates
        release_info = self.check_for_updates()
        if not release_info:
            return True  # No update needed
        
        # Find suitable asset
        asset = self.find_suitable_asset(release_info["assets"])
        if not asset:
            return False
        
        # Ask user for confirmation
        if not auto_install:
            print(f"\n📋 Update Details:")
            print(f"   Version: {release_info['version']}")
            print(f"   File: {asset['name']}")
            print(f"   Size: {asset['size'] / 1024 / 1024:.1f} MB")
            print(f"\n{release_info['body'][:200]}...")
            
            response = input("\nDo you want to download and install this update? (y/N): ")
            if response.lower() != 'y':
                print("Update cancelled by user")
                return False
        
        # Download update
        with tempfile.TemporaryDirectory() as temp_dir:
            download_path = self.download_update(asset, Path(temp_dir))
            if not download_path:
                return False
            
            # Verify download
            if not self.verify_download(download_path, asset["size"]):
                return False
            
            # Install update
            if self.install_update(download_path):
                print("🎉 Update installed successfully!")
                print("💡 Please restart the application to use the new version")
                return True
            else:
                print("❌ Update installation failed")
                return False

def main() -> None:
    """Main updater function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="VidTanium Auto-Updater")
    parser.add_argument("--current-version", type=str, default="0.1.0",
                       help="Current version of VidTanium")
    parser.add_argument("--auto-install", action="store_true",
                       help="Automatically install updates without prompting")
    parser.add_argument("--check-only", action="store_true",
                       help="Only check for updates, don't download")
    
    args = parser.parse_args()
    
    updater = VidTaniumUpdater(args.current_version)
    
    if args.check_only:
        release_info = updater.check_for_updates()
        if release_info:
            print(f"New version available: {release_info['version']}")
            sys.exit(1)  # Exit code 1 indicates update available
        else:
            print("No updates available")
            sys.exit(0)
    else:
        success = updater.update(args.auto_install)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
