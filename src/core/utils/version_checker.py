# version_checker.py
import os
import re
import subprocess
import shutil
import platform
from typing import Optional, List, TypedDict  # Updated imports
from dataclasses import dataclass
from enum import Enum
from loguru import logger


class Platform(Enum):
    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"
    UNKNOWN = "unknown"


@dataclass
class SoftwareInfo:
    name: str
    version: str
    path: Optional[str] = None
    installed: bool = False


# Define TypedDict for package manager configuration
class PackageManagerConfig(TypedDict):
    cmd: str
    args: List[str]


class VersionChecker:
    """Checks for installed software and their versions across operating systems."""

    @staticmethod
    def get_platform() -> Platform:
        """Detect the current operating system."""
        system = platform.system().lower()
        if system == "windows":
            return Platform.WINDOWS
        elif system == "darwin":
            return Platform.MACOS
        elif system == "linux":
            return Platform.LINUX
        else:
            return Platform.UNKNOWN

    def check_software(self, software_name: str) -> SoftwareInfo:
        """Check if a software is installed and get its version."""
        platform = self.get_platform()

        if platform == Platform.WINDOWS:
            return self._check_software_windows(software_name)
        elif platform == Platform.MACOS:
            return self._check_software_macos(software_name)
        elif platform == Platform.LINUX:
            return self._check_software_linux(software_name)
        else:
            logger.warning(
                f"Unsupported platform for checking {software_name}")
            return SoftwareInfo(name=software_name, version="", installed=False)

    def _check_software_windows(self, software_name: str) -> SoftwareInfo:
        """Check software on Windows using registry and PATH."""
        # First check if it's available in the PATH
        executable = f"{software_name}.exe"
        path = shutil.which(executable)

        if path:
            try:
                # Most programs respond to --version or -v
                result = subprocess.run([path, "--version"],
                                        capture_output=True, text=True, check=False)
                if result.returncode != 0:
                    # Try alternative version flag
                    result = subprocess.run([path, "-version"],
                                            capture_output=True, text=True, check=False)

                version = self._parse_version_output(result.stdout)
                return SoftwareInfo(name=software_name, version=version, path=path, installed=True)
            except (subprocess.SubprocessError, OSError) as e:
                logger.warning(
                    f"Error checking version for {software_name}: {e}")

        # If not found in PATH, check Windows registry
        try:
            import winreg
            reg_paths = [
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
            ]

            for reg_path in reg_paths:
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
                        subkey_count = winreg.QueryInfoKey(key)[0]

                        for i in range(subkey_count):
                            subkey_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, subkey_name) as subkey:
                                try:
                                    display_name = winreg.QueryValueEx(
                                        subkey, "DisplayName")[0]

                                    # Check if the software name is part of the display name
                                    if software_name.lower() in display_name.lower():
                                        version = winreg.QueryValueEx(
                                            subkey, "DisplayVersion")[0]
                                        install_location = winreg.QueryValueEx(
                                            subkey, "InstallLocation")[0]
                                        return SoftwareInfo(name=software_name,
                                                            version=version,
                                                            path=install_location,
                                                            installed=True)
                                except (OSError, FileNotFoundError):
                                    continue
                except (OSError, FileNotFoundError):
                    continue
        except ImportError:
            logger.warning(
                "Could not import winreg module for registry checks")

        return SoftwareInfo(name=software_name, version="", installed=False)

    def _check_software_macos(self, software_name: str) -> SoftwareInfo:
        """Check software on macOS using brew and PATH."""
        # First check if it's available in the PATH
        path = shutil.which(software_name)

        if path:
            try:
                # Try common version flags
                result = subprocess.run([path, "--version"],
                                        capture_output=True, text=True, check=False)
                if result.returncode != 0:
                    # Try alternative version flags
                    result = subprocess.run([path, "-v"],
                                            capture_output=True, text=True, check=False)
                    if result.returncode != 0:
                        result = subprocess.run([path, "-version"],
                                                capture_output=True, text=True, check=False)

                version = self._parse_version_output(result.stdout)
                return SoftwareInfo(name=software_name, version=version, path=path, installed=True)
            except (subprocess.SubprocessError, OSError) as e:
                logger.warning(
                    f"Error checking version for {software_name}: {e}")

        # Check via Homebrew if available
        try:
            if shutil.which("brew"):
                result = subprocess.run(["brew", "list", "--versions", software_name],
                                        capture_output=True, text=True, check=False)
                if result.returncode == 0 and result.stdout.strip():
                    # Parse Homebrew output format: name version1 version2 ...
                    parts = result.stdout.strip().split()
                    if len(parts) > 1:
                        version = parts[1]  # Get the first version listed
                        return SoftwareInfo(name=software_name, version=version, installed=True)
        except (subprocess.SubprocessError, OSError) as e:
            logger.warning(f"Error checking Homebrew for {software_name}: {e}")

        # Check via Applications directory
        common_paths = [
            f"/Applications/{software_name}.app",
            f"/Applications/{software_name}.app/Contents/Info.plist"
        ]

        for app_path in common_paths:
            if os.path.exists(app_path):
                # Try to extract version from Info.plist
                try:
                    result = subprocess.run(["defaults", "read", app_path.replace("/Info.plist", ""), "CFBundleShortVersionString"],
                                            capture_output=True, text=True, check=False)
                    if result.returncode == 0:
                        return SoftwareInfo(name=software_name, version=result.stdout.strip(),
                                            path=app_path, installed=True)
                except (subprocess.SubprocessError, OSError):
                    return SoftwareInfo(name=software_name, version="",
                                        path=app_path, installed=True)

        return SoftwareInfo(name=software_name, version="", installed=False)

    def _check_software_linux(self, software_name: str) -> SoftwareInfo:
        """Check software on Linux using package managers and PATH."""
        # First check if it's available in the PATH
        path = shutil.which(software_name)

        if path:
            try:
                # Try common version flags
                result = subprocess.run([path, "--version"],
                                        capture_output=True, text=True, check=False)
                if result.returncode != 0:
                    # Try alternative version flags
                    result = subprocess.run([path, "-v"],
                                            capture_output=True, text=True, check=False)
                    if result.returncode != 0:
                        result = subprocess.run([path, "-version"],
                                                capture_output=True, text=True, check=False)

                version = self._parse_version_output(result.stdout)
                return SoftwareInfo(name=software_name, version=version, path=path, installed=True)
            except (subprocess.SubprocessError, OSError) as e:
                logger.warning(
                    f"Error checking version for {software_name}: {e}")

        # Check with package managers
        package_managers: List[PackageManagerConfig] = [  # Apply TypedDict for precise typing
            {"cmd": "dpkg", "args": ["-l", software_name]},  # Debian/Ubuntu
            {"cmd": "rpm", "args": ["-q", software_name]},   # Red Hat/Fedora
            {"cmd": "pacman", "args": ["-Q", software_name]}  # Arch Linux
        ]

        for pm in package_managers:  # pm is now PackageManagerConfig
            # pm["cmd"] is str, pm["args"] is List[str]
            if shutil.which(pm["cmd"]):  # pm["cmd"] is correctly typed as str
                try:
                    command_list = [pm["cmd"]] + \
                        pm["args"]  # This will be List[str]
                    result = subprocess.run(command_list,  # command_list is List[str]
                                            capture_output=True, text=True, check=False)
                    if result.returncode == 0:
                        version = self._parse_version_output(result.stdout)
                        return SoftwareInfo(name=software_name, version=version, installed=True)
                except (subprocess.SubprocessError, OSError):
                    continue

        # Check flatpak
        if shutil.which("flatpak"):
            try:
                result = subprocess.run(["flatpak", "list", "--app", "--columns=application,version"],
                                        capture_output=True, text=True, check=False)
                if result.returncode == 0:
                    lines = result.stdout.strip().split("\n")
                    for line in lines:
                        parts = line.split()
                        if parts and software_name.lower() in parts[0].lower():
                            if len(parts) > 1:
                                return SoftwareInfo(name=software_name, version=parts[1], installed=True)
            except (subprocess.SubprocessError, OSError):
                pass

        # Check snap
        if shutil.which("snap"):
            try:
                result = subprocess.run(["snap", "list", software_name],
                                        capture_output=True, text=True, check=False)
                if result.returncode == 0:
                    lines = result.stdout.strip().split("\n")
                    if len(lines) > 1:  # Skip header line
                        parts = lines[1].split()
                        if len(parts) > 1:
                            return SoftwareInfo(name=software_name, version=parts[1], installed=True)
            except (subprocess.SubprocessError, OSError):
                pass

        return SoftwareInfo(name=software_name, version="", installed=False)

    def _parse_version_output(self, output: str) -> str:
        """Parse version information from command output."""
        # Common version patterns
        version_patterns = [
            r"version\s+([\d.]+)",  # version 1.2.3
            r"v([\d.]+)",           # v1.2.3
            r"(\d+\.\d+\.\d+)"      # 1.2.3
        ]

        for pattern in version_patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                return match.group(1)

        return output.strip() if output else ""
