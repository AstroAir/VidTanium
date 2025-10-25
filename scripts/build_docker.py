#!/usr/bin/env python3
"""
Docker build and management script for VidTanium
Handles building, tagging, and pushing Docker images
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import List, Dict, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from build_config import BuildConfig, get_build_config, BuildProfile

class DockerBuilder:
    """Docker image builder and manager"""
    
    def __init__(self, config: BuildConfig) -> None:
        self.config = config
        self.project_root = Path(__file__).parent.parent
        self.dockerfile = self.project_root / "Dockerfile"
        
        # Docker image configuration
        self.image_name = "vidtanium"
        self.registry = os.getenv("DOCKER_REGISTRY", "ghcr.io/astroair")
        
        self.targets = {
            "gui": "production-gui",
            "headless": "production-headless", 
            "dev": "development"
        }
    
    def check_docker(self) -> bool:
        """Check if Docker is available"""
        try:
            result = subprocess.run(["docker", "--version"], capture_output=True, text=True, check=True)
            print(f"✅ Docker found: {result.stdout.strip()}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Docker not found or not running")
            print("💡 Install Docker from https://docker.com/")
            return False
    
    def build_image(self, target: str, tags: Optional[List[str]] = None, push: bool = False) -> bool:
        """Build Docker image for specific target"""
        if target not in self.targets:
            print(f"❌ Unknown target: {target}")
            print(f"Available targets: {', '.join(self.targets.keys())}")
            return False
        
        dockerfile_target = self.targets[target]
        
        # Default tags
        if tags is None:
            tags = [
                f"{self.image_name}:{target}",
                f"{self.image_name}:{target}-{self.config.app_version}",
                f"{self.image_name}:{target}-latest"
            ]
        
        print(f"🐳 Building {target} image...")
        print(f"   Target: {dockerfile_target}")
        print(f"   Tags: {', '.join(tags)}")
        
        try:
            # Build command
            cmd = [
                "docker", "build",
                "--target", dockerfile_target,
                "--file", str(self.dockerfile)
            ]
            
            # Add tags
            for tag in tags:
                cmd.extend(["--tag", tag])
                if self.registry:
                    cmd.extend(["--tag", f"{self.registry}/{tag}"])
            
            # Add build args
            cmd.extend([
                "--build-arg", f"VERSION={self.config.app_version}",
                "--build-arg", f"BUILD_DATE={__import__('datetime').datetime.now().isoformat()}",
                "--build-arg", f"VCS_REF={self._get_git_commit()}"
            ])
            
            # Add context
            cmd.append(str(self.project_root))
            
            # Execute build
            result = subprocess.run(cmd, check=True)
            
            print(f"✅ Successfully built {target} image")
            
            # Push if requested
            if push:
                return self.push_image(tags)
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to build {target} image: {e}")
            return False
    
    def push_image(self, tags: List[str]) -> bool:
        """Push Docker images to registry"""
        if not self.registry:
            print("⚠️  No registry configured, skipping push")
            return True
        
        print(f"📤 Pushing images to {self.registry}...")
        
        try:
            for tag in tags:
                registry_tag = f"{self.registry}/{tag}"
                print(f"   Pushing {registry_tag}...")
                
                subprocess.run([
                    "docker", "push", registry_tag
                ], check=True)
            
            print("✅ Successfully pushed all images")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to push images: {e}")
            return False
    
    def build_all_images(self, push: bool = False) -> bool:
        """Build all Docker images"""
        print(f"🐳 Building all Docker images for {self.config.app_name} v{self.config.app_version}")
        print()
        
        success = True
        
        for target in self.targets.keys():
            if not self.build_image(target, push=push):
                success = False
            print()
        
        return success
    
    def test_images(self) -> bool:
        """Test built Docker images"""
        print("🧪 Testing Docker images...")
        
        tests = [
            {
                "name": "GUI image basic test",
                "image": f"{self.image_name}:gui",
                "command": ["python", "-c", "import sys; print('GUI image OK'); sys.exit(0)"],
                "expected_exit": 0
            },
            {
                "name": "Headless image basic test", 
                "image": f"{self.image_name}:headless",
                "command": ["python", "-c", "import sys; print('Headless image OK'); sys.exit(0)"],
                "expected_exit": 0
            },
            {
                "name": "Development image basic test",
                "image": f"{self.image_name}:dev", 
                "command": ["python", "-c", "import sys; print('Dev image OK'); sys.exit(0)"],
                "expected_exit": 0
            }
        ]
        
        success = True
        
        for test in tests:
            print(f"   Running: {test['name']}")
            
            try:
                result = subprocess.run([
                    "docker", "run", "--rm",
                    test["image"]
                ] + test["command"], 
                capture_output=True, text=True, timeout=30)
                
                if result.returncode == test["expected_exit"]:
                    print(f"   ✅ {test['name']} passed")
                else:
                    print(f"   ❌ {test['name']} failed (exit code: {result.returncode})")
                    success = False
                    
            except subprocess.TimeoutExpired:
                print(f"   ❌ {test['name']} timed out")
                success = False
            except Exception as e:
                print(f"   ❌ {test['name']} error: {e}")
                success = False
        
        return success
    
    def clean_images(self) -> bool:
        """Clean up Docker images"""
        print("🧹 Cleaning up Docker images...")
        
        try:
            # Remove dangling images
            subprocess.run([
                "docker", "image", "prune", "-f"
            ], check=True)
            
            # Remove old VidTanium images (keep latest)
            result = subprocess.run([
                "docker", "images", "--format", "{{.Repository}}:{{.Tag}}",
                "--filter", f"reference={self.image_name}"
            ], capture_output=True, text=True)
            
            images = result.stdout.strip().split('\n')
            latest_images = [img for img in images if 'latest' in img]
            old_images = [img for img in images if img not in latest_images and img.strip()]
            
            if old_images:
                print(f"   Removing {len(old_images)} old images...")
                subprocess.run([
                    "docker", "rmi"
                ] + old_images, check=True)
            
            print("✅ Docker cleanup completed")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Docker cleanup failed: {e}")
            return False
    
    def _get_git_commit(self) -> str:
        """Get current git commit hash"""
        try:
            result = subprocess.run([
                "git", "rev-parse", "--short", "HEAD"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        
        return "unknown"
    
    def show_images(self) -> None:
        """Show built VidTanium Docker images"""
        print("📋 VidTanium Docker images:")
        
        try:
            result = subprocess.run([
                "docker", "images", "--format", 
                "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}",
                "--filter", f"reference={self.image_name}"
            ], capture_output=True, text=True)
            
            if result.stdout.strip():
                print(result.stdout)
            else:
                print("   No VidTanium images found")
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to list images: {e}")

def main() -> None:
    """Main Docker build function"""
    parser = argparse.ArgumentParser(description="VidTanium Docker builder")
    parser.add_argument("--profile", type=str, choices=[p.value for p in BuildProfile],
                       default=BuildProfile.RELEASE.value, help="Build profile")
    parser.add_argument("--target", type=str, choices=["gui", "headless", "dev", "all"],
                       default="all", help="Docker target to build")
    parser.add_argument("--push", action="store_true", help="Push images to registry")
    parser.add_argument("--test", action="store_true", help="Test built images")
    parser.add_argument("--clean", action="store_true", help="Clean up old images")
    parser.add_argument("--list", action="store_true", help="List VidTanium images")
    parser.add_argument("--registry", type=str, help="Docker registry URL")
    
    args = parser.parse_args()
    
    # Get configuration
    profile = BuildProfile(args.profile)
    config = get_build_config(profile)
    
    # Create Docker builder
    builder = DockerBuilder(config)
    
    # Override registry if provided
    if args.registry:
        builder.registry = args.registry
    
    # Check Docker
    if not builder.check_docker():
        sys.exit(1)
    
    print(f"🐳 VidTanium Docker Builder")
    print(f"Version: {config.app_version}")
    print(f"Profile: {config.profile.value}")
    if builder.registry:
        print(f"Registry: {builder.registry}")
    print()
    
    success = True
    
    # Handle list command
    if args.list:
        builder.show_images()
        return
    
    # Handle clean command
    if args.clean:
        success &= builder.clean_images()
        print()
    
    # Build images
    if args.target == "all":
        success &= builder.build_all_images(push=args.push)
    else:
        success &= builder.build_image(args.target, push=args.push)
    
    # Test images
    if args.test and success:
        print()
        success &= builder.test_images()
    
    # Show final status
    print()
    if success:
        print("🎉 Docker build completed successfully!")
        builder.show_images()
        
        print("\n💡 Next steps:")
        print("   • Test containers with docker-compose")
        print("   • Deploy to container registry")
        print("   • Set up container orchestration")
    else:
        print("❌ Docker build failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
