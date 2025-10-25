#!/usr/bin/env python3
"""
Package verification and signing system for VidTanium
Handles digital signatures, checksums, and package integrity verification
"""

import os
import sys
import hashlib
import subprocess
import platform
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import json

class PackageVerifier:
    """Package verification and signing utilities"""
    
    def __init__(self) -> None:
        self.project_root = Path(__file__).parent.parent
        self.dist_dir = self.project_root / "dist"
        self.platform = platform.system().lower()
        
    def generate_checksums(self, files: Optional[List[Path]] = None) -> Dict[str, str]:
        """Generate SHA256 checksums for files"""
        if files is None:
            # Find all distributable files
            files = []
            for pattern in ["*.whl", "*.tar.gz", "*.exe", "*.msi", "*.pkg", "*.dmg", 
                           "*.AppImage", "*.deb", "*.rpm"]:
                files.extend(self.dist_dir.glob(pattern))
        
        checksums = {}
        
        for file_path in files:
            if file_path.is_file():
                sha256_hash = hashlib.sha256()
                
                print(f"📊 Generating checksum for {file_path.name}...")
                
                with open(file_path, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        sha256_hash.update(chunk)
                
                checksums[file_path.name] = sha256_hash.hexdigest()
                print(f"   SHA256: {checksums[file_path.name]}")
        
        return checksums
    
    def save_checksums(self, checksums: Dict[str, str], output_file: Optional[Path] = None) -> Path:
        """Save checksums to file"""
        if output_file is None:
            output_file = self.dist_dir / "SHA256SUMS"
        
        with open(output_file, 'w') as f:
            f.write("# SHA256 checksums for VidTanium distribution packages\n")
            f.write(f"# Generated: {__import__('datetime').datetime.now().isoformat()}\n")
            f.write(f"# Platform: {platform.system()} {platform.machine()}\n\n")
            
            for filename, checksum in sorted(checksums.items()):
                f.write(f"{checksum}  {filename}\n")
        
        print(f"✅ Checksums saved to: {output_file}")
        return output_file
    
    def verify_checksums(self, checksum_file: Path) -> bool:
        """Verify files against checksums"""
        if not checksum_file.exists():
            print(f"❌ Checksum file not found: {checksum_file}")
            return False
        
        print(f"🔍 Verifying checksums from {checksum_file}")
        
        base_dir = checksum_file.parent
        failed_files = []
        verified_files = []
        
        with open(checksum_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('#') or not line:
                    continue
                
                try:
                    checksum, filename = line.split('  ', 1)
                    file_path = base_dir / filename
                    
                    if not file_path.exists():
                        print(f"❌ File not found: {filename}")
                        failed_files.append(filename)
                        continue
                    
                    # Calculate actual checksum
                    sha256_hash = hashlib.sha256()
                    with open(file_path, "rb") as file_obj:
                        for chunk in iter(lambda: file_obj.read(4096), b""):
                            sha256_hash.update(chunk)
                    
                    actual_checksum = sha256_hash.hexdigest()
                    
                    if actual_checksum == checksum:
                        print(f"✅ {filename}")
                        verified_files.append(filename)
                    else:
                        print(f"❌ {filename} - checksum mismatch")
                        failed_files.append(filename)
                        
                except ValueError:
                    print(f"⚠️  Invalid checksum line: {line}")
        
        print(f"\n📊 Verification Results:")
        print(f"   ✅ Verified: {len(verified_files)} files")
        print(f"   ❌ Failed: {len(failed_files)} files")
        
        return len(failed_files) == 0
    
    def sign_packages(self, signing_key: Optional[str] = None) -> bool:
        """Sign packages with digital signatures"""
        print("🔐 Signing packages...")
        
        if self.platform == "windows":
            return self._sign_windows_packages(signing_key)
        elif self.platform == "darwin":
            return self._sign_macos_packages(signing_key)
        elif self.platform == "linux":
            return self._sign_linux_packages(signing_key)
        else:
            print(f"⚠️  Signing not implemented for {self.platform}")
            return True
    
    def _sign_windows_packages(self, signing_key: Optional[str]) -> bool:
        """Sign Windows packages with Authenticode"""
        try:
            # Find signtool
            signtool_paths = [
                "signtool.exe",
                r"C:\Program Files (x86)\Windows Kits\10\bin\x64\signtool.exe",
                r"C:\Program Files (x86)\Microsoft SDKs\Windows\v10.0A\bin\NETFX 4.8 Tools\signtool.exe"
            ]
            
            signtool = None
            for path in signtool_paths:
                try:
                    subprocess.run([path, "/?"], capture_output=True, check=True)
                    signtool = path
                    break
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue
            
            if not signtool:
                print("⚠️  SignTool not found, skipping Windows signing")
                return True
            
            # Sign executables and installers
            files_to_sign = list(self.dist_dir.glob("*.exe")) + list(self.dist_dir.glob("*.msi"))
            
            for file_path in files_to_sign:
                print(f"   Signing {file_path.name}...")
                
                cmd = [signtool, "sign"]
                
                if signing_key:
                    cmd.extend(["/f", signing_key])
                else:
                    # Use certificate store
                    cmd.extend(["/a"])
                
                cmd.extend(["/t", "http://timestamp.digicert.com", str(file_path)])
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"   ✅ Signed {file_path.name}")
                else:
                    print(f"   ❌ Failed to sign {file_path.name}: {result.stderr}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ Windows signing failed: {e}")
            return False
    
    def _sign_macos_packages(self, signing_key: Optional[str]) -> bool:
        """Sign macOS packages with codesign"""
        try:
            # Check if codesign is available
            subprocess.run(["codesign", "--version"], capture_output=True, check=True)
            
            # Sign app bundles and packages
            files_to_sign = list(self.dist_dir.glob("*.app")) + list(self.dist_dir.glob("*.pkg"))
            
            for file_path in files_to_sign:
                print(f"   Signing {file_path.name}...")
                
                cmd = ["codesign", "--sign"]
                
                if signing_key:
                    cmd.append(signing_key)
                else:
                    cmd.append("-")  # Ad-hoc signing
                
                cmd.extend(["--force", "--deep", str(file_path)])
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"   ✅ Signed {file_path.name}")
                else:
                    print(f"   ❌ Failed to sign {file_path.name}: {result.stderr}")
                    return False
            
            return True
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️  codesign not found, skipping macOS signing")
            return True
        except Exception as e:
            print(f"❌ macOS signing failed: {e}")
            return False
    
    def _sign_linux_packages(self, signing_key: Optional[str]) -> bool:
        """Sign Linux packages with GPG"""
        try:
            # Check if gpg is available
            subprocess.run(["gpg", "--version"], capture_output=True, check=True)
            
            # Sign packages
            files_to_sign = (list(self.dist_dir.glob("*.deb")) + 
                           list(self.dist_dir.glob("*.rpm")) + 
                           list(self.dist_dir.glob("*.AppImage")))
            
            for file_path in files_to_sign:
                print(f"   Signing {file_path.name}...")
                
                signature_file = file_path.with_suffix(file_path.suffix + ".sig")
                
                cmd = ["gpg", "--detach-sign", "--armor"]
                
                if signing_key:
                    cmd.extend(["--local-user", signing_key])
                
                cmd.extend(["--output", str(signature_file), str(file_path)])
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f"   ✅ Signed {file_path.name} -> {signature_file.name}")
                else:
                    print(f"   ❌ Failed to sign {file_path.name}: {result.stderr}")
                    return False
            
            return True
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️  GPG not found, skipping Linux signing")
            return True
        except Exception as e:
            print(f"❌ Linux signing failed: {e}")
            return False
    
    def create_release_manifest(self) -> Dict[str, Any]:
        """Create a comprehensive release manifest"""
        manifest = {
            "version": "0.1.0",  # Should be read from config
            "build_date": __import__('datetime').datetime.now().isoformat(),
            "platform": platform.system(),
            "architecture": platform.machine(),
            "python_version": platform.python_version(),
            "packages": {}
        }
        
        # Add package information
        for file_path in self.dist_dir.glob("*"):
            if file_path.is_file() and not file_path.name.startswith('.'):
                file_info = {
                    "size": file_path.stat().st_size,
                    "sha256": self._calculate_sha256(file_path),
                    "type": self._get_package_type(file_path)
                }
                
                # Add signature info if available
                sig_file = file_path.with_suffix(file_path.suffix + ".sig")
                if sig_file.exists():
                    file_info["signature"] = sig_file.name
                
                manifest["packages"][file_path.name] = file_info
        
        return manifest
    
    def _calculate_sha256(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def _get_package_type(self, file_path: Path) -> str:
        """Determine package type from file extension"""
        suffix = file_path.suffix.lower()
        
        type_map = {
            ".whl": "python_wheel",
            ".tar.gz": "source_distribution",
            ".exe": "windows_executable",
            ".msi": "windows_installer",
            ".pkg": "macos_installer",
            ".dmg": "macos_disk_image",
            ".appimage": "linux_appimage",
            ".deb": "debian_package",
            ".rpm": "rpm_package"
        }
        
        return type_map.get(suffix, "unknown")

def main() -> None:
    """Main verification function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="VidTanium Package Verifier")
    parser.add_argument("--generate-checksums", action="store_true",
                       help="Generate checksums for all packages")
    parser.add_argument("--verify-checksums", type=str,
                       help="Verify packages against checksum file")
    parser.add_argument("--sign-packages", action="store_true",
                       help="Sign packages with digital signatures")
    parser.add_argument("--signing-key", type=str,
                       help="Path to signing key or key identifier")
    parser.add_argument("--create-manifest", action="store_true",
                       help="Create release manifest")
    
    args = parser.parse_args()
    
    verifier = PackageVerifier()
    
    success = True
    
    if args.generate_checksums:
        checksums = verifier.generate_checksums()
        verifier.save_checksums(checksums)
    
    if args.verify_checksums:
        success &= verifier.verify_checksums(Path(args.verify_checksums))
    
    if args.sign_packages:
        success &= verifier.sign_packages(args.signing_key)
    
    if args.create_manifest:
        manifest = verifier.create_release_manifest()
        manifest_file = verifier.dist_dir / "release_manifest.json"
        
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        print(f"✅ Release manifest created: {manifest_file}")
    
    if not any([args.generate_checksums, args.verify_checksums, 
                args.sign_packages, args.create_manifest]):
        parser.print_help()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
