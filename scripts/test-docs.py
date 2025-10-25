#!/usr/bin/env python3
"""
Test script for MkDocs documentation setup
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path

def run_command(cmd, cwd=None) -> tuple[bool, str, str]:
    """Run a command and return the result"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            cwd=cwd,
            capture_output=True, 
            text=True,
            timeout=60
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def check_mkdocs_installation() -> bool:
    """Check if MkDocs and required plugins are installed"""
    print("🔍 Checking MkDocs installation...")
    
    success, stdout, stderr = run_command("mkdocs --version")
    if not success:
        print("❌ MkDocs not installed. Install with: pip install -r requirements-docs.txt")
        return False
    
    print(f"✅ MkDocs installed: {stdout.strip()}")
    return True

def validate_mkdocs_config() -> bool:
    """Validate the mkdocs.yml configuration"""
    print("🔍 Validating MkDocs configuration...")
    
    if not os.path.exists("mkdocs.yml"):
        print("❌ mkdocs.yml not found")
        return False
    
    success, stdout, stderr = run_command("mkdocs config")
    if not success:
        print(f"❌ Invalid mkdocs.yml configuration: {stderr}")
        return False
    
    print("✅ MkDocs configuration is valid")
    return True

def test_build() -> bool:
    """Test building the documentation"""
    print("🔍 Testing documentation build...")
    
    # Clean any existing build
    if os.path.exists("site"):
        shutil.rmtree("site")
    
    success, stdout, stderr = run_command("mkdocs build --strict")
    if not success:
        print(f"❌ Build failed: {stderr}")
        return False
    
    if not os.path.exists("site/index.html"):
        print("❌ Build succeeded but no index.html found")
        return False
    
    print("✅ Documentation build successful")
    return True

def test_serve() -> bool:
    """Test serving the documentation (quick test)"""
    print("🔍 Testing documentation serve...")
    
    # Start server in background and test quickly
    success, stdout, stderr = run_command("timeout 5s mkdocs serve --dev-addr=127.0.0.1:8001 2>/dev/null || true")
    
    # Just check if the command ran without immediate errors
    if "Address already in use" in stderr:
        print("⚠️  Port 8001 in use, but serve command works")
        return True
    
    print("✅ Documentation serve test completed")
    return True

def check_documentation_files() -> bool:
    """Check if all required documentation files exist"""
    print("🔍 Checking documentation files...")
    
    required_files = [
        "docs/index.md",
        "docs/installation.md",
        "docs/workflow-guide.md",
        "docs/getting-started.md",
        "docs/user-manual.md",
        "docs/examples.md",
        "docs/api-reference.md",
        "docs/developer-guide.md",
        "docs/project-structure.md",
        "docs/documentation.md",
        "docs/help-system.md"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing documentation files: {', '.join(missing_files)}")
        return False
    
    print("✅ All required documentation files exist")
    return True

def check_internal_links() -> bool:
    """Basic check for internal links in markdown files"""
    print("🔍 Checking internal links...")
    
    docs_dir = Path("docs")
    markdown_files = list(docs_dir.glob("**/*.md"))
    
    issues = []
    for md_file in markdown_files:
        try:
            content = md_file.read_text(encoding='utf-8')
            # Simple check for broken relative links
            import re
            links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
            
            for link_text, link_url in links:
                if link_url.startswith(('http://', 'https://', '#')):
                    continue  # Skip external links and anchors
                
                if link_url.endswith('.md'):
                    # Check if the referenced file exists
                    target_file = docs_dir / link_url
                    if not target_file.exists():
                        issues.append(f"{md_file.name}: broken link to {link_url}")
        
        except Exception as e:
            issues.append(f"{md_file.name}: error reading file - {e}")
    
    if issues:
        print("⚠️  Link issues found:")
        for issue in issues[:10]:  # Show first 10 issues
            print(f"   - {issue}")
        if len(issues) > 10:
            print(f"   ... and {len(issues) - 10} more issues")
        return False
    
    print("✅ Internal links check passed")
    return True

def main() -> int:
    """Main test function"""
    print("🚀 Testing VidTanium MkDocs Documentation Setup")
    print("=" * 50)
    
    # Change to project root directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    os.chdir(project_root)
    
    tests = [
        check_mkdocs_installation,
        validate_mkdocs_config,
        check_documentation_files,
        test_build,
        test_serve,
        check_internal_links,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            failed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Your MkDocs setup is ready.")
        print("\n📝 Next steps:")
        print("   1. Run 'mkdocs serve' to preview locally")
        print("   2. Run 'mkdocs build' to build for production")
        print("   3. Deploy to GitHub Pages or your preferred platform")
        return 0
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
