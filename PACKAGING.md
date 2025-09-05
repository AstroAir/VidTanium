# VidTanium Packaging System

This document describes the comprehensive packaging system for VidTanium, which supports multiple platforms and distribution formats.

## Overview

The VidTanium packaging system provides:

- **Enhanced PyInstaller Configuration** with build profiles
- **Cross-Platform Package Formats** (Windows, macOS, Linux)
- **Docker Containerization** with multi-stage builds
- **Automated CI/CD Workflows** with GitHub Actions
- **Package Verification** and digital signing
- **Auto-Updater System** for seamless updates

## Build Profiles

The system supports multiple build profiles optimized for different use cases:

- **`release`** - Production builds with full optimization
- **`development`** - Debug builds with console output
- **`minimal`** - Smallest possible builds with reduced features
- **`portable`** - Self-contained builds for maximum compatibility
- **`debug`** - Full debug builds with all debugging information

## Quick Start

### Basic Build

```bash
# Build with default release profile
python build_config.py

# Build with specific profile
python build_config.py --profile minimal

# Build directory distribution instead of single file
python build_config.py --directory
```

### Comprehensive Build

```bash
# Build all package formats for current platform
python scripts/build_all.py

# Build with specific profile
python scripts/build_all.py --profile release

# Skip tests during build
python scripts/build_all.py --skip-tests
```

## Platform-Specific Packaging

### Windows

```bash
# Build Windows executable
python build_config.py --profile release

# Create MSI installer
python scripts/create_msi.py --profile release

# Create NSIS installer (generated automatically)
makensis VidTanium_installer.nsi
```

**Output formats:**

- `VidTanium.exe` - Standalone executable
- `VidTanium_v0.1.0_Setup.msi` - MSI installer
- `VidTanium_Setup.exe` - NSIS installer

### macOS

```bash
# Build macOS executable
python build_config.py --profile release

# Create app bundle
./create_app_bundle.sh

# Create PKG installer
python scripts/create_macos_pkg.py --profile release
```

**Output formats:**

- `VidTanium.app` - Application bundle
- `VidTanium_v0.1.0_macOS.pkg` - PKG installer
- `VidTanium_v0.1.0_macOS.dmg` - Disk image

### Linux

```bash
# Build Linux executable
python build_config.py --profile release

# Create all Linux packages
python scripts/build_linux_packages.py --all

# Create specific package types
python scripts/build_linux_packages.py --appimage
python scripts/build_linux_packages.py --deb
python scripts/build_linux_packages.py --rpm
```

**Output formats:**

- `VidTanium-0.1.0-x86_64.AppImage` - Portable application
- `vidtanium_0.1.0_amd64.deb` - Debian package
- `vidtanium-0.1.0-1.x86_64.rpm` - RPM package

## Docker Containerization

### Building Docker Images

```bash
# Build all Docker images
python scripts/build_docker.py

# Build specific target
python scripts/build_docker.py --target headless

# Build and push to registry
python scripts/build_docker.py --push --registry ghcr.io/astroair
```

### Using Docker Images

```bash
# Run headless version
docker run -v ./downloads:/app/downloads ghcr.io/astroair/vidtanium:headless

# Run GUI version (with X11 forwarding)
docker run -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix ghcr.io/astroair/vidtanium:gui

# Development environment
docker-compose --profile dev up
```

### Docker Compose Profiles

- **`headless`** - Production headless deployment
- **`gui`** - GUI application with X11 forwarding
- **`dev`** - Development environment
- **`web`** - Web interface (future feature)

## Package Verification

### Generate Checksums

```bash
# Generate checksums for all packages
python scripts/package_verification.py --generate-checksums

# Verify packages against checksums
python scripts/package_verification.py --verify-checksums dist/SHA256SUMS
```

### Digital Signing

```bash
# Sign packages (platform-specific)
python scripts/package_verification.py --sign-packages

# Sign with specific key
python scripts/package_verification.py --sign-packages --signing-key "Developer ID"
```

**Signing Methods:**

- **Windows**: Authenticode with SignTool
- **macOS**: Code signing with codesign
- **Linux**: GPG signatures

## Auto-Updater

### Check for Updates

```bash
# Check for updates
python scripts/auto_updater.py --check-only

# Update with confirmation
python scripts/auto_updater.py

# Automatic update
python scripts/auto_updater.py --auto-install
```

### Integration

```python
from scripts.auto_updater import VidTaniumUpdater

updater = VidTaniumUpdater("0.1.0")
if updater.check_for_updates():
    updater.update(auto_install=False)
```

## CI/CD Integration

### GitHub Actions

The enhanced release workflow automatically:

1. **Builds** executables for all platforms
2. **Creates** platform-specific packages
3. **Builds** and pushes Docker images
4. **Tests** all generated packages
5. **Signs** packages (if configured)
6. **Generates** checksums and manifests
7. **Creates** GitHub releases
8. **Publishes** to PyPI

### Triggering Releases

```bash
# Manual release
gh workflow run "Enhanced Build and Release" -f version=1.0.0

# Tag-based release
git tag v1.0.0
git push origin v1.0.0
```

## Configuration

### Build Configuration

Edit `build_config.py` to customize:

- Application metadata
- Build profiles
- Platform-specific settings
- Dependency management
- Optimization options

### Environment Variables

```bash
# Docker registry
export DOCKER_REGISTRY=ghcr.io/astroair

# Build profile
export BUILD_PROFILE=release

# Signing configuration
export SIGNING_KEY_PATH=/path/to/key
export CODESIGN_IDENTITY="Developer ID Application"
```

## Troubleshooting

### Common Issues

1. **Missing Dependencies**

   ```bash
   # Install build tools
   uv sync --dev
   ```

2. **PyInstaller Errors**

   ```bash
   # Clean build directories
   python build_config.py --clean
   ```

3. **Docker Build Failures**

   ```bash
   # Clean Docker cache
   docker system prune -a
   ```

4. **Signing Failures**
   - Ensure signing certificates are properly installed
   - Check certificate validity and permissions
   - Verify signing tool availability

### Platform-Specific Requirements

**Windows:**

- Visual Studio Build Tools
- Windows SDK
- NSIS (for installers)
- WiX Toolset (for MSI)

**macOS:**

- Xcode Command Line Tools
- Developer certificates (for signing)

**Linux:**

- Build essentials
- AppImage tools
- Package building tools (dpkg, rpm)

## Advanced Usage

### Custom Build Profiles

Create custom build profiles by modifying `BUILD_PROFILES` in `build_config.py`:

```python
BUILD_PROFILES[BuildProfile.CUSTOM] = BuildConfig(
    profile=BuildProfile.CUSTOM,
    onefile=True,
    debug=False,
    upx=True,
    exclude_modules=["custom_excludes"]
)
```

### Integration with Other Tools

The packaging system can be integrated with:

- **Continuous Integration** platforms
- **Package repositories** (PyPI, Homebrew, etc.)
- **Distribution platforms** (Microsoft Store, Mac App Store)
- **Enterprise deployment** systems

## Support

For packaging-related issues:

1. Check the [troubleshooting section](#troubleshooting)
2. Review build logs for specific errors
3. Consult platform-specific documentation
4. Open an issue with detailed error information

## Contributing

When contributing to the packaging system:

1. Test changes on all supported platforms
2. Update documentation for new features
3. Ensure backward compatibility
4. Add appropriate tests for new functionality
