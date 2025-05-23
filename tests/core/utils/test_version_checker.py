import platform
import pytest
from unittest.mock import patch, Mock
from typing import Any, List, Tuple, Optional
from src.core.utils.version_checker import VersionChecker, SoftwareInfo, Platform


# filepath: d:\Project\VidTanium\src\core\utils\test_version_checker.py

# 使用绝对导入，因为父目录是命名空间包


class TestVersionChecker:
    """Test suite for VersionChecker class."""

    checker: VersionChecker

    def setup_method(self):
        """Set up test fixtures."""
        self.checker = VersionChecker()

    def teardown_method(self):
        """Tear down test fixtures."""
        pass

    @patch('platform.system')
    def test_get_platform(self, mock_system: Mock):
        """Test platform detection."""
        # Test Windows detection
        mock_system.return_value = 'Windows'
        assert self.checker.get_platform() == Platform.WINDOWS

        # Test macOS detection
        mock_system.return_value = 'Darwin'
        assert self.checker.get_platform() == Platform.MACOS

        # Test Linux detection
        mock_system.return_value = 'Linux'
        assert self.checker.get_platform() == Platform.LINUX

        # Test unknown platform
        mock_system.return_value = 'Unknown'
        assert self.checker.get_platform() == Platform.UNKNOWN

    @patch('src.core.utils.version_checker.VersionChecker.get_platform')
    @patch('src.core.utils.version_checker.VersionChecker._check_software_windows')
    @patch('src.core.utils.version_checker.VersionChecker._check_software_macos')
    @patch('src.core.utils.version_checker.VersionChecker._check_software_linux')
    def test_check_software_routing(self, mock_linux: Mock, mock_macos: Mock, mock_windows: Mock, mock_platform: Mock):
        """Test proper routing by platform."""
        # Test Windows route
        mock_platform.return_value = Platform.WINDOWS
        mock_windows.return_value = SoftwareInfo(
            name="test", version="1.0", installed=True)
        result = self.checker.check_software("test")
        assert result.installed
        assert result.version == "1.0"
        mock_windows.assert_called_once_with("test")
        mock_macos.assert_not_called()
        mock_linux.assert_not_called()

        # Reset mocks
        mock_windows.reset_mock()
        mock_macos.reset_mock()
        mock_linux.reset_mock()

        # Test macOS route
        mock_platform.return_value = Platform.MACOS
        mock_macos.return_value = SoftwareInfo(
            name="test", version="2.0", installed=True)
        result = self.checker.check_software("test")
        assert result.installed
        assert result.version == "2.0"
        mock_macos.assert_called_once_with("test")
        mock_windows.assert_not_called()
        mock_linux.assert_not_called()

        # Reset mocks
        mock_windows.reset_mock()
        mock_macos.reset_mock()
        mock_linux.reset_mock()

        # Test Linux route
        mock_platform.return_value = Platform.LINUX
        mock_linux.return_value = SoftwareInfo(
            name="test", version="3.0", installed=True)
        result = self.checker.check_software("test")
        assert result.installed
        assert result.version == "3.0"
        mock_linux.assert_called_once_with("test")
        mock_windows.assert_not_called()
        mock_macos.assert_not_called()

        # Test unknown platform
        mock_platform.return_value = Platform.UNKNOWN
        result = self.checker.check_software("test")
        assert not result.installed
        assert result.version == ""
        mock_windows.assert_not_called()
        mock_macos.assert_not_called()
        mock_linux.assert_not_called()

    def test_parse_version_output(self):
        """Test version parsing from command output."""
        # Test version pattern 'version X.Y.Z'
        assert getattr(self.checker, "_parse_version_output")(
            "some text version 1.2.3 other text") == "1.2.3"

        # Test version pattern 'vX.Y.Z'
        assert getattr(self.checker, "_parse_version_output")(
            "some text v2.3.4 other text") == "2.3.4"

        # Test version pattern 'X.Y.Z'
        assert getattr(self.checker, "_parse_version_output")(
            "some text 3.4.5 other text") == "3.4.5"

        # Test with no version pattern
        assert getattr(self.checker, "_parse_version_output")(
            "some text without version") == "some text without version"

        # Test with empty string
        assert getattr(self.checker, "_parse_version_output")("") == ""

    @pytest.mark.skipif(platform.system() != 'Windows', reason="Windows-only test")
    @patch('shutil.which')
    @patch('subprocess.run')
    @patch('winreg.OpenKey')
    @patch('winreg.QueryValueEx')
    @patch('winreg.EnumKey')
    @patch('winreg.QueryInfoKey')
    def test_check_software_windows(self, mock_query_info: Mock, mock_enum_key: Mock, mock_query_value: Mock,
                                    _mock_open_key: Mock, mock_run: Mock, mock_which: Mock):
        """Test Windows software detection."""
        # Test successful detection in PATH
        mock_which.return_value = r"C:\Program Files\TestApp\testapp.exe"

        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "testapp version 1.2.3"
        mock_run.return_value = mock_process

        result = getattr(self.checker, "_check_software_windows")("testapp")
        assert result.installed
        assert result.version == "1.2.3"
        assert result.path == r"C:\Program Files\TestApp\testapp.exe"

        # Reset mocks for registry test
        mock_which.reset_mock()
        mock_run.reset_mock()

        # Test registry detection when not in PATH
        mock_which.return_value = None

        # Mock registry operations
        mock_query_info.return_value = (1, 0, 0)  # type: ignore
        mock_enum_key.return_value = "TestApp"

        # Setup QueryValueEx to return appropriate values for different keys
        def mock_query_value_side_effect(_key: Any, name: str) -> Tuple[Any, int]:
            if name == "DisplayName":
                return ("TestApp", 0)
            elif name == "DisplayVersion":
                return ("2.0.0", 0)
            elif name == "InstallLocation":
                return (r"C:\Program Files\TestApp", 0)
            raise FileNotFoundError  # Should not happen in this configured mock

        mock_query_value.side_effect = mock_query_value_side_effect

        result = getattr(self.checker, "_check_software_windows")("testapp")
        assert result.installed
        assert result.version == "2.0.0"
        assert result.path == r"C:\Program Files\TestApp"

        # Test when software is not found
        mock_which.return_value = None
        # Use built-in FileNotFoundError
        mock_query_value.side_effect = FileNotFoundError()

        result = getattr(self.checker, "_check_software_windows")(
            "nonexistent")
        assert not result.installed
        assert result.version == ""

    @pytest.mark.skipif(platform.system() != 'Darwin', reason="macOS-only test")
    @patch('shutil.which')
    @patch('subprocess.run')
    @patch('os.path.exists')
    def test_check_software_macos(self, mock_exists: Mock, mock_run: Mock, mock_which: Mock):
        """Test macOS software detection."""
        # Test successful detection in PATH
        mock_which.return_value = "/usr/local/bin/testapp"

        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "testapp version 1.2.3"
        mock_run.return_value = mock_process

        result = getattr(self.checker, "_check_software_macos")("testapp")
        assert result.installed
        assert result.version == "1.2.3"
        assert result.path == "/usr/local/bin/testapp"

        # Reset mocks for Homebrew test
        mock_which.reset_mock()
        mock_run.reset_mock()

        # Test Homebrew detection when not in PATH
        mock_which.side_effect = lambda cmd: "/usr/local/bin/brew" if cmd == "brew" else None

        mock_brew_process = Mock()
        mock_brew_process.returncode = 0
        mock_brew_process.stdout = "testapp 2.0.0"

        def mock_run_side_effect_brew(cmd_list: List[str], **_kwargs: Any) -> Mock:
            if cmd_list[0] == "/usr/local/bin/brew":
                return mock_brew_process
            return Mock(returncode=1)

        mock_run.side_effect = mock_run_side_effect_brew

        result = getattr(self.checker, "_check_software_macos")("testapp")
        assert result.installed
        assert result.version == "2.0.0"

        # Reset mocks for Applications test
        mock_which.reset_mock()
        mock_run.reset_mock()
        mock_which.return_value = None
        mock_which.side_effect = None  # type: ignore

        # Test Applications directory detection
        mock_exists.return_value = True

        mock_app_process = Mock()
        mock_app_process.returncode = 0
        mock_app_process.stdout = "3.0.0"
        mock_run.return_value = mock_app_process

        result = getattr(self.checker, "_check_software_macos")("testapp")
        assert result.installed
        assert result.version == "3.0.0"
        assert result.path is not None and "/Applications/testapp.app" in result.path

        # Test when software is not found
        mock_which.return_value = None
        mock_exists.return_value = False
        mock_run.return_value = Mock(returncode=1)

        result = getattr(self.checker, "_check_software_macos")("nonexistent")
        assert not result.installed
        assert result.version == ""

    @pytest.mark.skipif(platform.system() != 'Linux', reason="Linux-only test")
    @patch('shutil.which')
    @patch('subprocess.run')
    def test_check_software_linux(self, mock_run: Mock, mock_which: Mock):
        """Test Linux software detection."""
        # Test successful detection in PATH
        mock_which.return_value = "/usr/bin/testapp"

        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "testapp version 1.2.3"
        mock_run.return_value = mock_process

        result = getattr(self.checker, "_check_software_linux")("testapp")
        assert result.installed
        assert result.version == "1.2.3"
        assert result.path == "/usr/bin/testapp"

        # Reset mocks for package manager tests
        mock_which.reset_mock()
        mock_run.reset_mock()

        # Test package manager detection (dpkg)
        mock_which.side_effect = lambda cmd: "/usr/bin/dpkg" if cmd == "dpkg" else None

        mock_dpkg_process = Mock()
        mock_dpkg_process.returncode = 0
        mock_dpkg_process.stdout = "ii  testapp   2.0.0   amd64    Test application"

        def mock_run_side_effect_dpkg(cmd_list: List[str], **_kwargs: Any) -> Mock:
            if cmd_list[0] == "/usr/bin/dpkg":
                return mock_dpkg_process
            return Mock(returncode=1)

        mock_run.side_effect = mock_run_side_effect_dpkg

        result = getattr(self.checker, "_check_software_linux")("testapp")
        assert result.installed
        assert result.version == "2.0.0"

        # Reset mocks for flatpak test
        mock_which.reset_mock()
        mock_run.reset_mock()
        mock_which.side_effect = lambda cmd: "/usr/bin/flatpak" if cmd == "flatpak" else None

        mock_flatpak_process = Mock()
        mock_flatpak_process.returncode = 0
        mock_flatpak_process.stdout = "org.test.testapp    3.0.0"

        def mock_run_flatpak_side_effect(cmd_list: List[str], **_kwargs: Any) -> Mock:
            if cmd_list[0] == "/usr/bin/flatpak":
                return mock_flatpak_process
            return Mock(returncode=1)

        mock_run.side_effect = mock_run_flatpak_side_effect

        result = getattr(self.checker, "_check_software_linux")("testapp")
        assert result.installed
        assert result.version == "3.0.0"

        # Reset mocks for snap test
        mock_which.reset_mock()
        mock_run.reset_mock()
        mock_which.side_effect = lambda cmd: "/usr/bin/snap" if cmd == "snap" else None

        mock_snap_process = Mock()
        mock_snap_process.returncode = 0
        mock_snap_process.stdout = "Name    Version    Rev   Tracking  Publisher  Notes\ntestapp  4.0.0      1234  stable    canonical  -"

        def mock_run_snap_side_effect(cmd_list: List[str], **_kwargs: Any) -> Mock:
            if cmd_list[0] == "/usr/bin/snap":
                return mock_snap_process
            return Mock(returncode=1)

        mock_run.side_effect = mock_run_snap_side_effect

        result = getattr(self.checker, "_check_software_linux")("testapp")
        assert result.installed
        assert result.version == "4.0.0"

        # Test when software is not found
        mock_which.return_value = None
        mock_which.side_effect = None  # type: ignore
        mock_run.return_value = Mock(returncode=1)
        mock_run.side_effect = None  # type: ignore

        result = getattr(self.checker, "_check_software_linux")("nonexistent")
        assert not result.installed
        assert result.version == ""


# 配置测试框架
if __name__ == "__main__":
    pytest.main(["-v", __file__])
