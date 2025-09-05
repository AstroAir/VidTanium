#!/usr/bin/env python3
"""
Enhanced PyInstaller build configuration for VidTanium
This script handles comprehensive build processes for creating optimized standalone executables
with support for multiple build profiles and cross-platform distribution.
"""

import os
import sys
import shutil
import subprocess
import platform
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

class BuildProfile(Enum):
    """Build profile types for different use cases"""
    DEVELOPMENT = "development"
    RELEASE = "release"
    MINIMAL = "minimal"
    PORTABLE = "portable"
    DEBUG = "debug"

@dataclass
class BuildConfig:
    """Enhanced build configuration with profile support"""
    app_name: str = "VidTanium"
    app_version: str = "0.1.0"
    description: str = "Video Download Tool with Built-in Player and Editor"
    author: str = "VidTanium Team"
    main_script: str = "main.py"
    icon_file: str = "assets/icon.ico"
    console: bool = False
    onefile: bool = True
    debug: bool = False
    upx: bool = True
    clean: bool = True
    profile: BuildProfile = BuildProfile.RELEASE

    # Advanced optimization settings
    optimize_imports: bool = True
    strip_debug: bool = True
    exclude_modules: List[str] = field(default_factory=list)
    include_modules: List[str] = field(default_factory=list)

    # Platform-specific settings
    windows_manifest: Optional[str] = None
    macos_bundle_id: str = "com.vidtanium.app"
    linux_desktop_file: bool = True

# Build profiles with optimized settings
BUILD_PROFILES = {
    BuildProfile.DEVELOPMENT: BuildConfig(
        console=True,
        debug=True,
        upx=False,
        onefile=False,
        optimize_imports=False,
        strip_debug=False,
        profile=BuildProfile.DEVELOPMENT
    ),
    BuildProfile.RELEASE: BuildConfig(
        console=False,
        debug=False,
        upx=True,
        onefile=True,
        optimize_imports=True,
        strip_debug=True,
        profile=BuildProfile.RELEASE
    ),
    BuildProfile.MINIMAL: BuildConfig(
        console=False,
        debug=False,
        upx=True,
        onefile=True,
        optimize_imports=True,
        strip_debug=True,
        exclude_modules=["test", "tests", "unittest", "pytest", "jupyter", "notebook", "IPython"],
        profile=BuildProfile.MINIMAL
    ),
    BuildProfile.PORTABLE: BuildConfig(
        console=False,
        debug=False,
        upx=False,  # Better compatibility
        onefile=False,
        optimize_imports=True,
        strip_debug=True,
        profile=BuildProfile.PORTABLE
    ),
    BuildProfile.DEBUG: BuildConfig(
        console=True,
        debug=True,
        upx=False,
        onefile=False,
        optimize_imports=False,
        strip_debug=False,
        profile=BuildProfile.DEBUG
    )
}

# Enhanced data files configuration
DATA_FILES_BASE = [
    ("src/locales", "locales"),
    ("config", "config"),
    ("docs/README.md", "README.md"),
    ("LICENSE", "LICENSE.txt"),
    ("CHANGELOG.md", "CHANGELOG.md"),
]

# Platform-specific data files
DATA_FILES_PLATFORM = {
    "Windows": [
        ("assets/windows", "assets"),
    ],
    "Darwin": [
        ("assets/macos", "assets"),
    ],
    "Linux": [
        ("assets/linux", "assets"),
        ("assets/vidtanium.desktop", "vidtanium.desktop"),
    ]
}

# Comprehensive hidden imports organized by category
HIDDEN_IMPORTS_CORE = [
    # Core application modules
    "src.core.downloader",
    "src.core.analyzer",
    "src.core.decryptor",
    "src.core.m3u8_parser",
    "src.core.media_processor",
    "src.core.merger",
    "src.core.scheduler",
    "src.core.thread_pool",
    "src.core.url_extractor",
    "src.core.singleton_manager",
    "src.core.ipc_server",
]

HIDDEN_IMPORTS_GUI = [
    # GUI modules
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
]

HIDDEN_IMPORTS_THIRD_PARTY = [
    # Third-party libraries
    "qfluentwidgets",
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "PySide6.QtMultimedia",
    "PySide6.QtNetwork",
    "loguru",
    "requests",
    "aiofiles",
    "aiosqlite",
    "playwright",
    "bs4",
    "cryptography.fernet",
    "cryptography.hazmat.primitives.ciphers",
    "cryptography.hazmat.backends",
    "Crypto.Cipher.AES",
    "psutil",
]

# Comprehensive exclusion patterns
EXCLUDES_BASE = [
    "test", "tests", "unittest", "pytest",
    "jupyter", "notebook", "IPython",
    "matplotlib", "scipy", "numpy.tests", "pandas.tests",
]

EXCLUDES_DEVELOPMENT = [
    "mypy", "ruff", "coverage", "pytest-cov",
    "pytest-benchmark", "pytest-xvfb",
    "types-psutil", "types-requests",
]

EXCLUDES_OPTIONAL = [
    "tkinter", "turtle", "curses",
    "pydoc", "doctest", "xmlrpc",
    "http.server", "socketserver",
]

def get_project_root() -> Path:
    """Get the project root directory"""
    return Path(__file__).parent

def get_build_config(profile: BuildProfile = BuildProfile.RELEASE) -> BuildConfig:
    """Get build configuration for specified profile"""
    config = BUILD_PROFILES.get(profile, BUILD_PROFILES[BuildProfile.RELEASE])

    # Update version from pyproject.toml if available
    pyproject_path = get_project_root() / "pyproject.toml"
    if pyproject_path.exists():
        try:
            import tomllib
            with open(pyproject_path, "rb") as f:
                pyproject_data = tomllib.load(f)
                if "project" in pyproject_data and "version" in pyproject_data["project"]:
                    config.app_version = pyproject_data["project"]["version"]
        except ImportError:
            # Fallback for Python < 3.11
            try:
                import tomli
                with open(pyproject_path, "rb") as f:
                    pyproject_data = tomli.load(f)
                    if "project" in pyproject_data and "version" in pyproject_data["project"]:
                        config.app_version = pyproject_data["project"]["version"]
            except ImportError:
                print("⚠️  Could not read version from pyproject.toml (tomllib/tomli not available)")

    return config

def get_data_files(config: BuildConfig) -> List[Tuple[str, str]]:
    """Get data files list based on configuration and platform"""
    data_files = DATA_FILES_BASE.copy()

    # Add platform-specific files
    current_platform = platform.system()
    if current_platform in DATA_FILES_PLATFORM:
        platform_files = DATA_FILES_PLATFORM[current_platform]
        for src, dst in platform_files:
            src_path = get_project_root() / src
            if src_path.exists():
                data_files.append((src, dst))

    # Filter existing files only
    existing_files = []
    project_root = get_project_root()
    for src, dst in data_files:
        src_path = project_root / src
        if src_path.exists():
            existing_files.append((src, dst))
        else:
            print(f"⚠️  Data file not found, skipping: {src}")

    return existing_files

def get_hidden_imports(config: BuildConfig) -> List[str]:
    """Get hidden imports list based on configuration"""
    imports = HIDDEN_IMPORTS_CORE + HIDDEN_IMPORTS_GUI + HIDDEN_IMPORTS_THIRD_PARTY

    # Add profile-specific imports
    if config.include_modules:
        imports.extend(config.include_modules)

    return imports

def get_excludes(config: BuildConfig) -> List[str]:
    """Get exclusion list based on configuration"""
    excludes = EXCLUDES_BASE.copy()

    # Add development excludes for non-debug builds
    if config.profile != BuildProfile.DEBUG:
        excludes.extend(EXCLUDES_DEVELOPMENT)

    # Add optional excludes for minimal builds
    if config.profile == BuildProfile.MINIMAL:
        excludes.extend(EXCLUDES_OPTIONAL)

    # Add profile-specific excludes
    if config.exclude_modules:
        excludes.extend(config.exclude_modules)

    return excludes

def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of a file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def create_icon_if_missing(config: BuildConfig) -> bool:
    """Create a default icon if none exists"""
    icon_path = get_project_root() / config.icon_file

    if icon_path.exists():
        return True

    print(f"Creating default icon at {icon_path}")
    # Create assets directory if it doesn't exist
    icon_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        from PIL import Image, ImageDraw, ImageFont

        # Create icons for different platforms
        if platform.system() == "Windows":
            # Create ICO file with multiple sizes
            sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
            images = []

            for size in sizes:
                img = Image.new('RGBA', size, (102, 126, 234, 255))
                draw = ImageDraw.Draw(img)

                # Scale the "V" shape based on size
                w, h = size
                scale = w / 256
                points = [
                    (int(60 * scale), int(60 * scale)),
                    (int(w/2), int(180 * scale)),
                    (int(196 * scale), int(60 * scale)),
                    (int(170 * scale), int(60 * scale)),
                    (int(w/2), int(140 * scale)),
                    (int(86 * scale), int(60 * scale))
                ]
                draw.polygon(points, fill=(255, 255, 255, 255))
                images.append(img)

            # Save as ICO with multiple sizes
            images[0].save(icon_path, format='ICO', sizes=[img.size for img in images], append_images=images[1:])

        elif platform.system() == "Darwin":
            # Create ICNS file for macOS
            icns_path = icon_path.with_suffix('.icns')
            img = Image.new('RGBA', (512, 512), (102, 126, 234, 255))
            draw = ImageDraw.Draw(img)

            # Draw "V" shape
            draw.polygon([(120, 120), (256, 360), (392, 120), (340, 120), (256, 280), (172, 120)],
                        fill=(255, 255, 255, 255))

            # Save as PNG first, then convert to ICNS if possible
            png_path = icon_path.with_suffix('.png')
            img.save(png_path, format='PNG')

            # Try to create ICNS using iconutil (macOS only)
            try:
                iconset_dir = icon_path.parent / "VidTanium.iconset"
                iconset_dir.mkdir(exist_ok=True)

                # Create different sizes for iconset
                sizes = [16, 32, 64, 128, 256, 512]
                for size in sizes:
                    resized = img.resize((size, size), Image.Resampling.LANCZOS)
                    resized.save(iconset_dir / f"icon_{size}x{size}.png")
                    if size <= 256:  # Create @2x versions
                        resized.save(iconset_dir / f"icon_{size//2}x{size//2}@2x.png")

                # Convert to ICNS
                result = subprocess.run(['iconutil', '-c', 'icns', str(iconset_dir)],
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    config.icon_file = str(icns_path.relative_to(get_project_root()))
                    shutil.rmtree(iconset_dir)  # Clean up
                else:
                    config.icon_file = str(png_path.relative_to(get_project_root()))

            except Exception:
                config.icon_file = str(png_path.relative_to(get_project_root()))

        else:
            # Linux - create PNG
            png_path = icon_path.with_suffix('.png')
            img = Image.new('RGBA', (256, 256), (102, 126, 234, 255))
            draw = ImageDraw.Draw(img)

            # Draw "V" shape
            draw.polygon([(60, 60), (128, 180), (196, 60), (170, 60), (128, 140), (86, 60)],
                        fill=(255, 255, 255, 255))

            img.save(png_path, format='PNG')
            config.icon_file = str(png_path.relative_to(get_project_root()))

        print(f"✅ Created default icon: {config.icon_file}")
        return True

    except ImportError:
        print("⚠️  PIL not available, building without icon")
        config.icon_file = ""
        return False
    except Exception as e:
        print(f"⚠️  Could not create icon: {e}")
        config.icon_file = ""
        return False

def clean_build_dirs(config: BuildConfig):
    """Clean build and dist directories"""
    if not config.clean:
        return

    project_root = get_project_root()
    dirs_to_clean = ["build", "dist", "__pycache__"]

    # Add profile-specific directories
    dirs_to_clean.extend([
        f"build_{config.profile.value}",
        f"dist_{config.profile.value}",
    ])

    # Clean Python cache directories recursively
    cache_patterns = ["__pycache__", "*.pyc", "*.pyo", ".pytest_cache", ".mypy_cache"]

    for dir_name in dirs_to_clean:
        dir_path = project_root / dir_name
        if dir_path.exists():
            print(f"🧹 Cleaning {dir_path}")
            shutil.rmtree(dir_path)

    # Clean cache files recursively
    for pattern in cache_patterns:
        if pattern.startswith("."):
            # Directory patterns
            for cache_dir in project_root.rglob(pattern):
                if cache_dir.is_dir():
                    print(f"🧹 Cleaning cache: {cache_dir}")
                    shutil.rmtree(cache_dir, ignore_errors=True)
        else:
            # File patterns
            for cache_file in project_root.rglob(pattern):
                if cache_file.is_file():
                    cache_file.unlink(missing_ok=True)

def check_dependencies(config: BuildConfig) -> bool:
    """Check if all required dependencies are available"""
    required_packages = {
        "PyInstaller": "pyinstaller",
        "PySide6": "PySide6",
        "qfluentwidgets": "qfluentwidgets",
        "loguru": "loguru",
        "requests": "requests",
        "cryptography": "cryptography",
        "aiofiles": "aiofiles",
        "aiosqlite": "aiosqlite",
        "psutil": "psutil",
    }

    optional_packages = {
        "PIL": "Pillow",  # For icon creation
        "playwright": "playwright",  # For web scraping
        "bs4": "beautifulsoup4",  # For HTML parsing
    }

    missing_required = []
    missing_optional = []

    # Check required packages
    for display_name, import_name in required_packages.items():
        try:
            __import__(import_name.replace("-", "_"))
            print(f"✅ {display_name} is available")
        except ImportError:
            missing_required.append(display_name)
            print(f"❌ {display_name} is missing")

    # Check optional packages
    for display_name, import_name in optional_packages.items():
        try:
            __import__(import_name.replace("-", "_"))
            print(f"✅ {display_name} is available (optional)")
        except ImportError:
            missing_optional.append(display_name)
            print(f"⚠️  {display_name} is missing (optional)")

    # Report results
    if missing_required:
        print(f"\n❌ Missing required packages: {', '.join(missing_required)}")
        print("Install them with: uv add " + " ".join(required_packages[pkg] for pkg in missing_required))
        return False

    if missing_optional:
        print(f"\n⚠️  Missing optional packages: {', '.join(missing_optional)}")
        print("Install them with: uv add " + " ".join(optional_packages[pkg] for pkg in missing_optional))

    # Check PyInstaller version
    try:
        import PyInstaller
        version = getattr(PyInstaller, '__version__', 'unknown')
        print(f"✅ PyInstaller version: {version}")

        # Warn about old versions
        if version != 'unknown':
            major, minor = map(int, version.split('.')[:2])
            if major < 5 or (major == 5 and minor < 0):
                print("⚠️  Consider upgrading PyInstaller to version 5.0+ for better performance")
    except Exception:
        pass

    return True

def check_upx(config: BuildConfig) -> bool:
    """Check if UPX is available for compression"""
    if not config.upx:
        return False

    try:
        result = subprocess.run(["upx", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✅ UPX is available: {version_line}")
            return True
    except FileNotFoundError:
        pass

    print("⚠️  UPX not found, building without compression")
    print("💡 Install UPX from https://upx.github.io/ for smaller executables")
    return False

def generate_spec_file(config: BuildConfig) -> str:
    """Generate PyInstaller spec file with enhanced configuration"""
    project_root = get_project_root()
    data_files = get_data_files(config)
    hidden_imports = get_hidden_imports(config)
    excludes = get_excludes(config)

    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
# Generated PyInstaller spec file for {config.app_name} v{config.app_version}
# Build profile: {config.profile.value}
# Generated on: {__import__('datetime').datetime.now().isoformat()}

import sys
from pathlib import Path

# Project root
project_root = Path(r"{project_root}")

# Data files to include
datas = [
'''

    # Add data files
    for src, dst in data_files:
        src_path = project_root / src
        spec_content += f'    (r"{src_path}", "{dst}"),\n'

    spec_content += ''']

# Hidden imports
hiddenimports = [
'''

    for import_name in hidden_imports:
        spec_content += f'    "{import_name}",\n'

    spec_content += ''']

# Excludes
excludes = [
'''

    for exclude in excludes:
        spec_content += f'    "{exclude}",\n'

    spec_content += f''']

block_cipher = None

# Analysis configuration
a = Analysis(
    [r"{project_root / config.main_script}"],
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
    optimize={2 if config.optimize_imports else 0},
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
'''

    upx_available = check_upx(config)

    if config.onefile:
        spec_content += f'''
# Single file executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="{config.app_name}",
    debug={config.debug},
    bootloader_ignore_signals=False,
    strip={config.strip_debug},
    upx={config.upx and upx_available},
    upx_exclude=[],
    runtime_tmpdir=None,
    console={config.console},
'''

        # Add icon if available
        icon_path = project_root / config.icon_file
        if config.icon_file and icon_path.exists():
            spec_content += f'    icon=r"{icon_path}",\n'

        # Add version file for Windows
        if platform.system() == "Windows":
            version_file = project_root / 'version_info.txt'
            if version_file.exists():
                spec_content += f'    version_file=r"{version_file}",\n'

        # Add platform-specific options
        if platform.system() == "Darwin":
            spec_content += f'    bundle_identifier="{config.macos_bundle_id}",\n'

        spec_content += ')\n'
    else:
        spec_content += f'''
# Directory distribution
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="{config.app_name}",
    debug={config.debug},
    bootloader_ignore_signals=False,
    strip={config.strip_debug},
    upx=False,
    console={config.console},
'''

        # Add icon if available
        icon_path = project_root / config.icon_file
        if config.icon_file and icon_path.exists():
            spec_content += f'    icon=r"{icon_path}",\n'

        spec_content += ''')

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip={config.strip_debug},
    upx={config.upx and upx_available},
    upx_exclude=[],
    name="{config.app_name}",
)
'''

    # Generate spec file with profile suffix
    spec_filename = f"{config.app_name}_{config.profile.value}.spec"
    spec_file_path = project_root / spec_filename

    with open(spec_file_path, 'w', encoding='utf-8') as f:
        f.write(spec_content)

    print(f"✅ Generated spec file: {spec_file_path}")
    print(f"   Profile: {config.profile.value}")
    print(f"   One file: {config.onefile}")
    print(f"   Debug: {config.debug}")
    print(f"   UPX: {config.upx and upx_available}")

    return str(spec_file_path)

def create_version_info(config: BuildConfig):
    """Create version info file for Windows builds"""
    if platform.system() != "Windows":
        return

    project_root = get_project_root()

    # Parse version string to components
    version_parts = config.app_version.split('.')
    while len(version_parts) < 4:
        version_parts.append('0')

    file_version = tuple(int(part) for part in version_parts[:4])
    version_str = '.'.join(version_parts[:4])

    version_info_content = f'''# UTF-8
# Version information for {config.app_name}
# Generated automatically - do not edit manually

VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={file_version},
    prodvers={file_version},
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
        [StringStruct(u'CompanyName', u'{config.author}'),
        StringStruct(u'FileDescription', u'{config.description}'),
        StringStruct(u'FileVersion', u'{version_str}'),
        StringStruct(u'InternalName', u'{config.app_name}'),
        StringStruct(u'LegalCopyright', u'Copyright © 2025 {config.author}'),
        StringStruct(u'OriginalFilename', u'{config.app_name}.exe'),
        StringStruct(u'ProductName', u'{config.app_name}'),
        StringStruct(u'ProductVersion', u'{config.app_version}'),
        StringStruct(u'Comments', u'Built with profile: {config.profile.value}')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
'''

    version_file_path = project_root / "version_info.txt"
    with open(version_file_path, 'w', encoding='utf-8') as f:
        f.write(version_info_content)

    print(f"✅ Created version info: {version_file_path}")
    print(f"   Version: {version_str}")
    print(f"   Profile: {config.profile.value}")

def build_executable(config: BuildConfig, spec_file: str) -> bool:
    """Build the executable using PyInstaller with enhanced error handling"""
    try:
        cmd = ["pyinstaller", "--clean", spec_file]

        # Add debug options
        if config.debug:
            cmd.extend(["--debug=all", "--log-level=DEBUG"])
        else:
            cmd.append("--log-level=INFO")

        # Add additional PyInstaller options
        if config.profile == BuildProfile.MINIMAL:
            cmd.append("--exclude-module=tkinter")

        print(f"🔨 Building executable with {config.profile.value} profile...")
        print(f"Command: {' '.join(cmd)}")
        print(f"Working directory: {get_project_root()}")

        # Set environment variables for better builds
        env = os.environ.copy()
        env['PYTHONOPTIMIZE'] = '2' if config.optimize_imports else '0'

        # Run PyInstaller
        start_time = __import__('time').time()
        result = subprocess.run(
            cmd,
            cwd=get_project_root(),
            env=env,
            capture_output=True,
            text=True,
            check=False
        )
        build_time = __import__('time').time() - start_time

        # Handle results
        if result.returncode == 0:
            print(f"✅ Build completed successfully in {build_time:.1f} seconds!")
            if result.stdout:
                print("Build output:")
                print(result.stdout[-1000:])  # Show last 1000 chars
            return True
        else:
            print(f"❌ Build failed with return code: {result.returncode}")
            if result.stderr:
                print("Error output:")
                print(result.stderr[-2000:])  # Show last 2000 chars of errors
            if result.stdout:
                print("Build output:")
                print(result.stdout[-1000:])
            return False

    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        return False
    except FileNotFoundError:
        print("❌ PyInstaller not found.")
        print("Install with: uv add pyinstaller")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during build: {e}")
        return False

def post_build_tasks(config: BuildConfig) -> bool:
    """Perform post-build tasks like copying additional files and generating checksums"""
    project_root = get_project_root()
    dist_dir = project_root / "dist"

    if not dist_dir.exists():
        print("❌ Dist directory not found")
        return False

    print("📦 Performing post-build tasks...")

    # Copy additional documentation
    additional_files = [
        ("CHANGELOG.md", "CHANGELOG.md"),
        ("CONTRIBUTING.md", "CONTRIBUTING.md"),
        ("README.md", "README.md"),
        ("LICENSE", "LICENSE.txt"),
    ]

    # Determine target directory
    if config.onefile:
        target_dir = dist_dir
    else:
        target_dir = dist_dir / config.app_name
        if not target_dir.exists():
            print(f"❌ Expected directory not found: {target_dir}")
            return False

    # Copy files
    copied_files = []
    for src, dst in additional_files:
        src_path = project_root / src
        if src_path.exists():
            dst_path = target_dir / dst

            try:
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_path, dst_path)
                copied_files.append(dst)
                print(f"✅ Copied {src} -> {dst}")
            except Exception as e:
                print(f"⚠️  Could not copy {src}: {e}")

    # Generate checksums for all files in dist
    print("🔐 Generating checksums...")
    checksums = {}

    for file_path in target_dir.rglob("*"):
        if file_path.is_file() and not file_path.name.endswith('.txt'):
            try:
                file_hash = calculate_file_hash(file_path)
                rel_path = file_path.relative_to(target_dir)
                checksums[str(rel_path)] = file_hash
                print(f"   {rel_path}: {file_hash[:16]}...")
            except Exception as e:
                print(f"⚠️  Could not hash {file_path}: {e}")

    # Save checksums
    if checksums:
        checksum_file = target_dir / "checksums.txt"
        with open(checksum_file, 'w', encoding='utf-8') as f:
            f.write(f"# SHA256 checksums for {config.app_name} v{config.app_version}\n")
            f.write(f"# Build profile: {config.profile.value}\n")
            f.write(f"# Generated: {__import__('datetime').datetime.now().isoformat()}\n\n")

            for file_path, file_hash in sorted(checksums.items()):
                f.write(f"{file_hash}  {file_path}\n")

        print(f"✅ Generated checksums: {checksum_file}")

    return True

def create_installer_script(config: BuildConfig):
    """Create installer script for easier distribution"""
    project_root = get_project_root()

    if platform.system() == "Windows":
        # Create NSIS installer script
        exe_name = f"{config.app_name}.exe"
        if not config.onefile:
            exe_name = f"{config.app_name}\\{config.app_name}.exe"

        nsis_content = f'''!include "MUI2.nsh"

Name "{config.app_name}"
OutFile "{config.app_name}_v{config.app_version}_Setup.exe"
InstallDir "$PROGRAMFILES\\{config.app_name}"
InstallDirRegKey HKCU "Software\\{config.app_name}" ""
RequestExecutionLevel admin

; Version information
VIProductVersion "{config.app_version}.0"
VIAddVersionKey "ProductName" "{config.app_name}"
VIAddVersionKey "ProductVersion" "{config.app_version}"
VIAddVersionKey "CompanyName" "{config.author}"
VIAddVersionKey "FileDescription" "{config.description}"
VIAddVersionKey "FileVersion" "{config.app_version}"
VIAddVersionKey "LegalCopyright" "© 2025 {config.author}"

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

  ; Copy main executable and files
  File /r "dist\\*"

  ; Create shortcuts
  CreateDirectory "$SMPROGRAMS\\{config.app_name}"
  CreateShortCut "$SMPROGRAMS\\{config.app_name}\\{config.app_name}.lnk" "$INSTDIR\\{exe_name}"
  CreateShortCut "$DESKTOP\\{config.app_name}.lnk" "$INSTDIR\\{exe_name}"

  ; Registry entries
  WriteRegStr HKCU "Software\\{config.app_name}" "" $INSTDIR
  WriteRegStr HKCU "Software\\{config.app_name}" "Version" "{config.app_version}"

  ; Uninstaller
  WriteUninstaller "$INSTDIR\\uninstall.exe"

  ; Add to Add/Remove Programs
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{config.app_name}" "DisplayName" "{config.app_name}"
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{config.app_name}" "UninstallString" "$INSTDIR\\uninstall.exe"
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{config.app_name}" "DisplayVersion" "{config.app_version}"
  WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{config.app_name}" "Publisher" "{config.author}"
SectionEnd

Section "Uninstall"
  ; Remove files
  RMDir /r "$INSTDIR"

  ; Remove shortcuts
  Delete "$SMPROGRAMS\\{config.app_name}\\{config.app_name}.lnk"
  Delete "$DESKTOP\\{config.app_name}.lnk"
  RMDir "$SMPROGRAMS\\{config.app_name}"

  ; Remove registry entries
  DeleteRegKey HKCU "Software\\{config.app_name}"
  DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{config.app_name}"
SectionEnd
'''

        nsis_file = project_root / f"{config.app_name}_installer.nsi"
        with open(nsis_file, 'w', encoding='utf-8') as f:
            f.write(nsis_content)

        print(f"✅ Created NSIS installer script: {nsis_file}")
        print(f"💡 To create installer, install NSIS and run: makensis {nsis_file.name}")
    
    elif platform.system() == "Darwin":
        # Create macOS app bundle script
        app_bundle_script = f'''#!/bin/bash
# Create macOS app bundle for {config.app_name}
APP_NAME="{config.app_name}"
BUNDLE_DIR="dist/$APP_NAME.app"

echo "Creating macOS app bundle..."

# Create bundle structure
mkdir -p "$BUNDLE_DIR/Contents/MacOS"
mkdir -p "$BUNDLE_DIR/Contents/Resources"

# Copy executable
if [ -f "dist/$APP_NAME" ]; then
    cp "dist/$APP_NAME" "$BUNDLE_DIR/Contents/MacOS/"
    chmod +x "$BUNDLE_DIR/Contents/MacOS/$APP_NAME"
elif [ -d "dist/$APP_NAME" ]; then
    cp -r "dist/$APP_NAME/"* "$BUNDLE_DIR/Contents/MacOS/"
    chmod +x "$BUNDLE_DIR/Contents/MacOS/$APP_NAME"
else
    echo "Error: Could not find executable in dist/"
    exit 1
fi

# Copy icon if available
if [ -f "assets/icon.icns" ]; then
    cp "assets/icon.icns" "$BUNDLE_DIR/Contents/Resources/"
fi

# Create Info.plist
cat > "$BUNDLE_DIR/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>$APP_NAME</string>
    <key>CFBundleIdentifier</key>
    <string>{config.macos_bundle_id}</string>
    <key>CFBundleName</key>
    <string>$APP_NAME</string>
    <key>CFBundleDisplayName</key>
    <string>{config.app_name}</string>
    <key>CFBundleVersion</key>
    <string>{config.app_version}</string>
    <key>CFBundleShortVersionString</key>
    <string>{config.app_version}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF

echo "✅ Created macOS app bundle: $BUNDLE_DIR"

# Create DMG if hdiutil is available
if command -v hdiutil >/dev/null 2>&1; then
    echo "Creating DMG..."
    DMG_NAME="{config.app_name}_v{config.app_version}_macOS.dmg"
    hdiutil create -volname "$APP_NAME" -srcfolder "$BUNDLE_DIR" -ov -format UDZO "dist/$DMG_NAME"
    echo "✅ Created DMG: dist/$DMG_NAME"
fi
'''

        script_file = project_root / "create_app_bundle.sh"
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(app_bundle_script)

        # Make script executable
        os.chmod(script_file, 0o755)
        print(f"✅ Created app bundle script: {script_file}")
        print("💡 Run ./create_app_bundle.sh after building to create macOS app bundle")

def main():
    """Enhanced main build function with profile support"""
    import argparse

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Enhanced VidTanium build system")
    parser.add_argument("--profile", type=str, choices=[p.value for p in BuildProfile],
                       default=BuildProfile.RELEASE.value, help="Build profile to use")
    parser.add_argument("--onefile", action="store_true", help="Create single file executable")
    parser.add_argument("--directory", action="store_true", help="Create directory distribution")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--no-upx", action="store_true", help="Disable UPX compression")
    parser.add_argument("--no-clean", action="store_true", help="Skip cleaning build directories")

    args = parser.parse_args()

    # Get build configuration
    profile = BuildProfile(args.profile)
    config = get_build_config(profile)

    # Apply command line overrides
    if args.onefile:
        config.onefile = True
    elif args.directory:
        config.onefile = False

    if args.debug:
        config.debug = True
        config.console = True

    if args.no_upx:
        config.upx = False

    if args.no_clean:
        config.clean = False

    # Display build information
    print(f"🚀 Building {config.app_name} v{config.app_version}")
    print(f"Platform: {platform.system()} {platform.machine()}")
    print(f"Python: {sys.version}")
    print(f"Profile: {config.profile.value}")
    print(f"Distribution: {'Single file' if config.onefile else 'Directory'}")
    print(f"Debug: {config.debug}")
    print(f"UPX: {config.upx}")
    print()

    # Check dependencies
    if not check_dependencies(config):
        sys.exit(1)

    # Clean build directories
    clean_build_dirs(config)

    # Create icon if missing
    create_icon_if_missing(config)

    # Create version info for Windows
    create_version_info(config)

    # Generate spec file
    spec_file = generate_spec_file(config)

    # Build executable
    if build_executable(config, spec_file):
        # Post-build tasks
        if post_build_tasks(config):
            # Create installer script
            create_installer_script(config)

            print()
            print("🎉 Build completed successfully!")

            # Show output location and statistics
            project_root = get_project_root()
            if config.onefile:
                if platform.system() == "Windows":
                    output_path = project_root / "dist" / f"{config.app_name}.exe"
                else:
                    output_path = project_root / "dist" / config.app_name
            else:
                output_path = project_root / "dist" / config.app_name

            print(f"📦 Output: {output_path}")

            if output_path.exists():
                if output_path.is_file():
                    size_mb = output_path.stat().st_size / 1024 / 1024
                    print(f"📏 Size: {size_mb:.1f} MB")
                elif output_path.is_dir():
                    total_size = sum(f.stat().st_size for f in output_path.rglob('*') if f.is_file())
                    size_mb = total_size / 1024 / 1024
                    file_count = len(list(output_path.rglob('*')))
                    print(f"📏 Total size: {size_mb:.1f} MB ({file_count} files)")

                print(f"✅ Executable is ready!")

                # Show next steps
                print("\n📋 Next steps:")
                if platform.system() == "Windows":
                    print("   • Test the executable on a clean Windows system")
                    print("   • Run the NSIS installer script to create setup.exe")
                elif platform.system() == "Darwin":
                    print("   • Run ./create_app_bundle.sh to create macOS app bundle")
                    print("   • Test the app bundle on different macOS versions")
                else:
                    print("   • Test the executable on different Linux distributions")
                    print("   • Consider creating AppImage, deb, or rpm packages")

            else:
                print("❌ Output file not found!")
                sys.exit(1)
        else:
            print("⚠️  Build completed but post-build tasks failed")
            sys.exit(1)
    else:
        print("❌ Build failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
