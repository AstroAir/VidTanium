#!/usr/bin/env python3
"""
Comprehensive build script for VidTanium
Orchestrates all packaging formats and platforms
"""

import os
import sys
import subprocess
import platform
import argparse
from pathlib import Path
from typing import List, Dict, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from build_config import BuildConfig, get_build_config, BuildProfile

class ComprehensiveBuilder:
    """Orchestrates all build processes"""
    
    def __init__(self, profile: BuildProfile = BuildProfile.RELEASE):
        self.config = get_build_config(profile)
        self.project_root = Path(__file__).parent.parent
        self.scripts_dir = self.project_root / "scripts"
        
    def build_python_package(self) -> bool:
        """Build Python wheel and source distribution"""
        print("🐍 Building Python package...")
        
        try:
            # Use uv to build the package
            result = subprocess.run([
                "uv", "build"
            ], cwd=self.project_root, check=True, capture_output=True, text=True)
            
            print("✅ Python package built successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Python package build failed: {e}")
            if e.stdout:
                print("STDOUT:", e.stdout)
            if e.stderr:
                print("STDERR:", e.stderr)
            return False
    
    def build_executable(self) -> bool:
        """Build standalone executable using PyInstaller"""
        print("🔨 Building standalone executable...")
        
        try:
            # Run the enhanced build config
            result = subprocess.run([
                sys.executable, "build_config.py", 
                "--profile", self.config.profile.value
            ], cwd=self.project_root, check=True)
            
            print("✅ Executable built successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Executable build failed: {e}")
            return False
    
    def build_linux_packages(self) -> bool:
        """Build Linux packages (AppImage, deb, rpm)"""
        if platform.system() != "Linux":
            print("⚠️  Skipping Linux packages (not on Linux)")
            return True
            
        print("🐧 Building Linux packages...")
        
        try:
            result = subprocess.run([
                sys.executable, str(self.scripts_dir / "build_linux_packages.py"),
                "--profile", self.config.profile.value,
                "--all"
            ], cwd=self.project_root, check=True)
            
            print("✅ Linux packages built successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Linux packages build failed: {e}")
            return False
    
    def build_docker_images(self) -> bool:
        """Build Docker images"""
        print("🐳 Building Docker images...")
        
        try:
            # Build all Docker targets
            targets = ["production-gui", "production-headless", "development"]
            
            for target in targets:
                print(f"   Building {target} image...")
                result = subprocess.run([
                    "docker", "build", 
                    "--target", target,
                    "--tag", f"vidtanium:{target}",
                    "--tag", f"vidtanium:{target}-{self.config.app_version}",
                    "."
                ], cwd=self.project_root, check=True, capture_output=True, text=True)
            
            print("✅ Docker images built successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Docker build failed: {e}")
            return False
        except FileNotFoundError:
            print("⚠️  Docker not found, skipping Docker builds")
            return True
    
    def run_tests(self) -> bool:
        """Run test suite"""
        print("🧪 Running tests...")
        
        try:
            result = subprocess.run([
                "uv", "run", "pytest", "tests/", "-v"
            ], cwd=self.project_root, check=True, capture_output=True, text=True)
            
            print("✅ All tests passed")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Tests failed: {e}")
            if e.stdout:
                print("Test output:", e.stdout[-1000:])  # Last 1000 chars
            return False
    
    def generate_checksums(self) -> bool:
        """Generate checksums for all build artifacts"""
        print("🔐 Generating checksums...")
        
        try:
            dist_dir = self.project_root / "dist"
            if not dist_dir.exists():
                print("⚠️  No dist directory found")
                return True
            
            import hashlib
            
            checksums = {}
            for file_path in dist_dir.rglob("*"):
                if file_path.is_file() and not file_path.name.endswith('.txt'):
                    sha256_hash = hashlib.sha256()
                    with open(file_path, "rb") as f:
                        for chunk in iter(lambda: f.read(4096), b""):
                            sha256_hash.update(chunk)
                    
                    rel_path = file_path.relative_to(dist_dir)
                    checksums[str(rel_path)] = sha256_hash.hexdigest()
            
            # Write checksums file
            checksum_file = dist_dir / "SHA256SUMS"
            with open(checksum_file, 'w') as f:
                f.write(f"# SHA256 checksums for {self.config.app_name} v{self.config.app_version}\n")
                f.write(f"# Generated: {__import__('datetime').datetime.now().isoformat()}\n\n")
                
                for file_path, file_hash in sorted(checksums.items()):
                    f.write(f"{file_hash}  {file_path}\n")
            
            print(f"✅ Generated checksums: {checksum_file}")
            print(f"   {len(checksums)} files processed")
            return True
            
        except Exception as e:
            print(f"❌ Checksum generation failed: {e}")
            return False
    
    def create_release_archive(self) -> bool:
        """Create release archive with all artifacts"""
        print("📦 Creating release archive...")
        
        try:
            import tarfile
            import zipfile
            
            dist_dir = self.project_root / "dist"
            if not dist_dir.exists():
                print("⚠️  No dist directory found")
                return False
            
            # Create archives
            archive_base = f"{self.config.app_name}-{self.config.app_version}-all-platforms"
            
            # Create tar.gz for Unix systems
            with tarfile.open(dist_dir / f"{archive_base}.tar.gz", "w:gz") as tar:
                tar.add(dist_dir, arcname=f"{self.config.app_name}-{self.config.app_version}")
            
            # Create zip for Windows systems
            with zipfile.ZipFile(dist_dir / f"{archive_base}.zip", "w", zipfile.ZIP_DEFLATED) as zip_file:
                for file_path in dist_dir.rglob("*"):
                    if file_path.is_file() and not file_path.name.endswith(('.tar.gz', '.zip')):
                        arc_path = f"{self.config.app_name}-{self.config.app_version}/{file_path.relative_to(dist_dir)}"
                        zip_file.write(file_path, arc_path)
            
            print(f"✅ Created release archives")
            return True
            
        except Exception as e:
            print(f"❌ Release archive creation failed: {e}")
            return False

def main():
    """Main build orchestration function"""
    parser = argparse.ArgumentParser(description="Comprehensive VidTanium build system")
    parser.add_argument("--profile", type=str, choices=[p.value for p in BuildProfile],
                       default=BuildProfile.RELEASE.value, help="Build profile")
    parser.add_argument("--skip-tests", action="store_true", help="Skip running tests")
    parser.add_argument("--skip-docker", action="store_true", help="Skip Docker builds")
    parser.add_argument("--python-only", action="store_true", help="Build Python package only")
    parser.add_argument("--executable-only", action="store_true", help="Build executable only")
    
    args = parser.parse_args()
    
    # Create builder
    profile = BuildProfile(args.profile)
    builder = ComprehensiveBuilder(profile)
    
    print(f"🚀 Starting comprehensive build for {builder.config.app_name} v{builder.config.app_version}")
    print(f"Profile: {profile.value}")
    print(f"Platform: {platform.system()} {platform.machine()}")
    print()
    
    success = True
    
    # Run tests first (unless skipped)
    if not args.skip_tests:
        success &= builder.run_tests()
        print()
    
    # Build Python package
    if not args.executable_only:
        success &= builder.build_python_package()
        print()
    
    # Build executable
    if not args.python_only:
        success &= builder.build_executable()
        print()
        
        # Build platform-specific packages
        success &= builder.build_linux_packages()
        print()
        
        # Build Docker images (unless skipped)
        if not args.skip_docker:
            success &= builder.build_docker_images()
            print()
    
    # Generate checksums and archives
    if success:
        success &= builder.generate_checksums()
        print()
        
        success &= builder.create_release_archive()
        print()
    
    # Final status
    if success:
        print("🎉 Comprehensive build completed successfully!")
        print("\n📋 Build artifacts:")
        
        dist_dir = Path(__file__).parent.parent / "dist"
        if dist_dir.exists():
            for item in sorted(dist_dir.iterdir()):
                if item.is_file():
                    size_mb = item.stat().st_size / 1024 / 1024
                    print(f"   📄 {item.name} ({size_mb:.1f} MB)")
                elif item.is_dir():
                    file_count = len(list(item.rglob('*')))
                    print(f"   📁 {item.name}/ ({file_count} files)")
        
        print("\n🚀 Ready for distribution!")
    else:
        print("❌ Build failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
