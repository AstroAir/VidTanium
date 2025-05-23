import pytest
import subprocess
from unittest.mock import patch, MagicMock, mock_open, ANY

from merger import is_ffmpeg_available, merge_files_ffmpeg, merge_files_binary, convert_ts_to_mp4, merge_files


class TestMerger:
    """Test suite for the merger module functions."""

    def setup_method(self) -> None:
        """Set up test fixtures before each test."""
        # Sample file list for tests
        self.test_files = [
            "file_1.ts",
            "file_2.ts",
            "file_3.ts"
        ]
        self.output_file = "output.mp4"
        self.ffmpeg_path = "/usr/bin/ffmpeg"
        self.settings = {
            "advanced": {
                "ffmpeg_path": self.ffmpeg_path
            }
        }

    def test_is_ffmpeg_available_success(self) -> None:
        """Test FFmpeg availability check when FFmpeg is available."""
        # Mock subprocess.run to simulate successful FFmpeg check
        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch('subprocess.run', return_value=mock_result) as mock_subprocess_run:
            result = is_ffmpeg_available(self.ffmpeg_path)
            assert result is True
            mock_subprocess_run.assert_called_once_with(
                [self.ffmpeg_path, "-version"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

    def test_is_ffmpeg_available_failure(self) -> None:
        """Test FFmpeg availability check when FFmpeg is not available."""
        # Mock subprocess.run to simulate failed FFmpeg check
        mock_result = MagicMock()
        mock_result.returncode = 1

        with patch('subprocess.run', return_value=mock_result) as mock_subprocess_run:
            result = is_ffmpeg_available(self.ffmpeg_path)
            assert result is False
            assert mock_subprocess_run.call_count == 1

    def test_is_ffmpeg_available_exception(self) -> None:
        """Test FFmpeg availability check when subprocess raises an exception."""
        # Mock subprocess.run to simulate an exception
        with patch('subprocess.run', side_effect=FileNotFoundError("Command not found")) as mock_subprocess_run:
            result = is_ffmpeg_available(self.ffmpeg_path)
            assert result is False
            assert mock_subprocess_run.call_count == 1

    def test_merge_files_ffmpeg_success(self) -> None:
        """Test merging files with FFmpeg successfully."""
        # Mock tempfile.NamedTemporaryFile to control the temporary file path
        mock_tempfile = MagicMock()
        mock_tempfile.__enter__.return_value.name = "temp_filelist.txt"

        # Mock file operations
        mock_file = mock_open()

        # Mock subprocess.run to simulate successful command execution
        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch('tempfile.NamedTemporaryFile', return_value=mock_tempfile), \
                patch('builtins.open', mock_file), \
                patch('os.path.abspath', return_value="/absolute/path/to/file"), \
                patch('subprocess.run', return_value=mock_result) as mock_subprocess_run, \
                patch('os.path.exists', return_value=True), \
                patch('os.remove') as mock_remove:

            result = merge_files_ffmpeg(
                self.test_files, self.output_file, self.ffmpeg_path)

            # Verify result is success
            assert result["success"] is True
            # Verify temporary file was removed
            mock_remove.assert_called_once_with("temp_filelist.txt")
            # Verify FFmpeg command was executed
            assert mock_subprocess_run.call_count == 1

    def test_merge_files_ffmpeg_failure(self) -> None:
        """Test merging files with FFmpeg when command fails."""
        # Mock tempfile.NamedTemporaryFile
        mock_tempfile = MagicMock()
        mock_tempfile.__enter__.return_value.name = "temp_filelist.txt"

        # Mock file operations
        mock_file = mock_open()

        # Mock subprocess.run to simulate failed command execution
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "FFmpeg error"

        with patch('tempfile.NamedTemporaryFile', return_value=mock_tempfile), \
                patch('builtins.open', mock_file), \
                patch('os.path.abspath', return_value="/absolute/path/to/file"), \
                patch('subprocess.run', return_value=mock_result), \
                patch('os.path.exists', return_value=True), \
                patch('os.remove') as mock_remove:

            result = merge_files_ffmpeg(
                self.test_files, self.output_file, self.ffmpeg_path)

            # Verify result is failure
            assert result["success"] is False
            assert result["error"] == "FFmpeg error"
            # Verify temporary file was removed
            mock_remove.assert_called_once_with("temp_filelist.txt")

    def test_merge_files_ffmpeg_exception(self) -> None:
        """Test merging files with FFmpeg when an exception occurs."""
        # Mock tempfile.NamedTemporaryFile to throw exception
        with patch('tempfile.NamedTemporaryFile', side_effect=Exception("Mock exception")):
            result = merge_files_ffmpeg(
                self.test_files, self.output_file, self.ffmpeg_path)

            # Verify result is failure
            assert result["success"] is False
            assert "Mock exception" in result["error"]

    def test_merge_files_binary_success(self) -> None:
        """Test binary merging of files successfully."""
        # Mock file operations
        mock_outfile = mock_open()
        mock_infile = mock_open()

        # Create a combined mock that handles both output and input file opens
        mock_combined = MagicMock()
        mock_combined.side_effect = [
            mock_outfile.return_value] + [mock_infile.return_value] * len(self.test_files)

        with patch('builtins.open', mock_combined), \
                patch('os.path.exists', return_value=True), \
                patch('shutil.copyfileobj') as mock_copyfileobj:

            result = merge_files_binary(self.test_files, self.output_file)

            # Verify result is success
            assert result["success"] is True
            # Verify files were copied
            assert mock_copyfileobj.call_count == len(self.test_files)

    def test_merge_files_binary_missing_file(self) -> None:
        """Test binary merging when some files are missing."""
        # Mock file operations
        mock_file = mock_open()

        # Simulate first file exists, second doesn't, third does
        def mock_exists(path: str) -> bool:
            return path != self.test_files[1]

        with patch('builtins.open', mock_file), \
                patch('os.path.exists', side_effect=mock_exists), \
                patch('shutil.copyfileobj') as mock_copyfileobj:

            result = merge_files_binary(self.test_files, self.output_file)

            # Verify result is success (should skip missing files)
            assert result["success"] is True
            # Verify copyfileobj was called twice (for files 1 and 3)
            assert mock_copyfileobj.call_count == 2

    def test_merge_files_binary_exception(self) -> None:
        """Test binary merging when an exception occurs."""
        # Mock file operations to throw exception
        with patch('builtins.open', side_effect=Exception("Mock exception")):
            result = merge_files_binary(self.test_files, self.output_file)

            # Verify result is failure
            assert result["success"] is False
            assert "Mock exception" in result["error"]

    def test_convert_ts_to_mp4_success(self) -> None:
        """Test converting TS to MP4 successfully."""
        # Mock subprocess.run to simulate successful command execution
        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch('subprocess.run', return_value=mock_result) as mock_subprocess_run:
            result = convert_ts_to_mp4(
                "input.ts", self.output_file, self.ffmpeg_path)

            # Verify result is success
            assert result["success"] is True
            # Verify FFmpeg command was executed with correct parameters
            mock_subprocess_run.assert_called_once_with(
                [self.ffmpeg_path, "-i", "input.ts",
                    "-c", "copy", "-y", self.output_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

    def test_convert_ts_to_mp4_failure(self) -> None:
        """Test converting TS to MP4 when command fails."""
        # Mock subprocess.run to simulate failed command execution
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Conversion error"

        with patch('subprocess.run', return_value=mock_result) as mock_subprocess_run:
            result = convert_ts_to_mp4(
                "input.ts", self.output_file, self.ffmpeg_path)

            # Verify result is failure
            assert result["success"] is False
            assert result["error"] == "Conversion error"
            assert mock_subprocess_run.call_count == 1

    def test_convert_ts_to_mp4_exception(self) -> None:
        """Test converting TS to MP4 when an exception occurs."""
        # Mock subprocess.run to throw exception
        with patch('subprocess.run', side_effect=Exception("Mock exception")):
            result = convert_ts_to_mp4(
                "input.ts", self.output_file, self.ffmpeg_path)

            # Verify result is failure
            assert result["success"] is False
            assert "Mock exception" in result["error"]

    def test_merge_files_no_files(self) -> None:
        """Test merge_files with empty file list."""
        result = merge_files([], self.output_file, self.settings)

        # Verify result is failure
        assert result["success"] is False
        assert result["error"] == "No files to merge"

    def test_merge_files_ffmpeg_direct_success(self) -> None:
        """Test merge_files when FFmpeg is available and direct merge succeeds."""
        with patch('merger.is_ffmpeg_available', return_value=True) as mock_is_ffmpeg_available, \
                patch('merger.merge_files_ffmpeg', return_value={"success": True}) as mock_merge_ffmpeg:

            result = merge_files(
                self.test_files, self.output_file, self.settings)

            # Verify is_ffmpeg_available was called with correct path
            assert mock_is_ffmpeg_available.call_count == 1
            mock_is_ffmpeg_available.assert_called_with(self.ffmpeg_path)

            # Verify merge_files_ffmpeg was called
            assert mock_merge_ffmpeg.call_count == 1
            mock_merge_ffmpeg.assert_called_with(
                ANY, self.output_file, self.ffmpeg_path)

            # Verify result is success
            assert result["success"] is True

    def test_merge_files_ffmpeg_direct_failure_binary_success(self) -> None:
        """Test merge_files when FFmpeg direct merge fails but binary merge succeeds."""
        with patch('merger.is_ffmpeg_available', return_value=True) as mock_is_ffmpeg_available, \
                patch('merger.merge_files_ffmpeg', return_value={"success": False}) as mock_merge_ffmpeg, \
                patch('merger.merge_files_binary', return_value={"success": True}) as mock_merge_binary, \
                patch('merger.convert_ts_to_mp4', return_value={"success": True}) as mock_convert, \
                patch('os.path.exists', return_value=True), \
                patch('os.remove') as mock_remove:

            result = merge_files(
                self.test_files, self.output_file, self.settings)

            # Verify functions were called
            assert mock_is_ffmpeg_available.call_count >= 1
            mock_is_ffmpeg_available.assert_called_with(self.ffmpeg_path)
            assert mock_merge_ffmpeg.call_count == 1
            assert mock_merge_binary.call_count == 1
            assert mock_convert.call_count == 1
            mock_convert.assert_called_with(
                f"{self.output_file}.ts", self.output_file, self.ffmpeg_path)
            mock_remove.assert_called_once_with(f"{self.output_file}.ts")

            # Verify result is success
            assert result["success"] is True

    def test_merge_files_no_ffmpeg(self) -> None:
        """Test merge_files when FFmpeg is not available."""
        with patch('merger.is_ffmpeg_available', return_value=False) as mock_is_ffmpeg_available, \
                patch('merger.merge_files_binary', return_value={"success": True}) as mock_merge_binary, \
                patch('shutil.move') as mock_move:

            # Use a non-mp4 output file to bypass conversion
            output_file = "output.wmv"

            result = merge_files(self.test_files, output_file, self.settings)

            # Verify functions were called
            assert mock_is_ffmpeg_available.call_count == 1
            mock_is_ffmpeg_available.assert_called_with(self.ffmpeg_path)
            assert mock_merge_binary.call_count == 1
            assert mock_move.call_count == 1
            mock_move.assert_called_with(f"{output_file}.ts", output_file)

            # Verify result is success
            assert result["success"] is True

    def test_merge_files_binary_failure(self) -> None:
        """Test merge_files when binary merge fails."""
        with patch('merger.is_ffmpeg_available', return_value=False) as mock_is_ffmpeg_available, \
                patch('merger.merge_files_binary', return_value={"success": False, "error": "Binary merge failed"}) as mock_merge_binary:

            result = merge_files(
                self.test_files, self.output_file, self.settings)

            # Verify functions were called
            assert mock_is_ffmpeg_available.call_count == 1
            mock_is_ffmpeg_available.assert_called_with(self.ffmpeg_path)
            assert mock_merge_binary.call_count == 1

            # Verify result is failure
            assert result["success"] is False
            assert result["error"] == "Binary merge failed"

    def test_merge_files_conversion_failure(self) -> None:
        """Test merge_files when TS to MP4 conversion fails."""
        with patch('merger.is_ffmpeg_available', return_value=True) as mock_is_ffmpeg_available, \
                patch('merger.merge_files_ffmpeg', return_value={"success": False}) as mock_merge_ffmpeg, \
                patch('merger.merge_files_binary', return_value={"success": True}) as mock_merge_binary, \
                patch('merger.convert_ts_to_mp4', return_value={"success": False, "error": "Conversion failed"}) as mock_convert, \
                patch('os.path.exists', return_value=True):

            result = merge_files(
                self.test_files, self.output_file, self.settings)

            # Verify functions were called
            assert mock_is_ffmpeg_available.call_count >= 1
            mock_is_ffmpeg_available.assert_called_with(self.ffmpeg_path)
            assert mock_merge_ffmpeg.call_count == 1
            assert mock_merge_binary.call_count == 1
            assert mock_convert.call_count == 1

            # Verify result is failure
            assert result["success"] is False
            assert result["error"] == "Conversion failed"

    def test_merge_files_rename_failure(self) -> None:
        """Test merge_files when file renaming fails."""
        with patch('merger.is_ffmpeg_available', return_value=False) as mock_is_ffmpeg_available, \
                patch('merger.merge_files_binary', return_value={"success": True}) as mock_merge_binary, \
                patch('shutil.move', side_effect=Exception("Rename failed")):

            # Use a non-mp4 output file to force renaming
            output_file = "output.wmv"

            result = merge_files(self.test_files, output_file, self.settings)

            # Verify functions were called
            assert mock_is_ffmpeg_available.call_count == 1
            mock_is_ffmpeg_available.assert_called_with(self.ffmpeg_path)
            assert mock_merge_binary.call_count == 1

            # Verify result is failure
            assert result["success"] is False
            assert "Rename failed" in result["error"]

    def test_merge_files_custom_sort(self) -> None:
        """Test merge_files with custom file sorting."""
        test_files = ["segment_2.ts", "segment_1.ts", "segment_10.ts"]
        expected_sort = ["segment_1.ts", "segment_2.ts", "segment_10.ts"]

        with patch('merger.is_ffmpeg_available', return_value=True), \
                patch('merger.merge_files_ffmpeg') as mock_merge_ffmpeg:

            # Set up the mock to capture the sorted_files argument
            mock_merge_ffmpeg.return_value = {"success": True}

            merge_files(test_files, self.output_file, self.settings)

            # Get the first positional argument passed to merge_files_ffmpeg
            sorted_files = mock_merge_ffmpeg.call_args[0][0]

            # Verify files were sorted correctly
            assert sorted_files == expected_sort

    def test_merge_files_sort_fallback(self) -> None:
        """Test merge_files with sort fallback for unusually named files."""
        test_files = ["file-a.ts", "file-b.ts", "file-c.ts"]

        with patch('merger.is_ffmpeg_available', return_value=True), \
                patch('merger.merge_files_ffmpeg') as mock_merge_ffmpeg:

            # Set up the mock to capture the sorted_files argument
            mock_merge_ffmpeg.return_value = {"success": True}

            merge_files(test_files, self.output_file, self.settings)

            # Get the first positional argument passed to merge_files_ffmpeg
            sorted_files = mock_merge_ffmpeg.call_args[0][0]

            # Verify files were sorted using direct sort
            assert sorted_files == sorted(test_files)

    def test_merge_files_no_settings(self) -> None:
        """Test merge_files with no settings provided."""
        with patch('merger.is_ffmpeg_available', return_value=True) as mock_is_ffmpeg_available, \
                patch('merger.merge_files_ffmpeg', return_value={"success": True}) as mock_merge_ffmpeg:

            result = merge_files(self.test_files, self.output_file, None)

            # Verify is_ffmpeg_available was called with None
            assert mock_is_ffmpeg_available.call_count == 1
            mock_is_ffmpeg_available.assert_called_with(None)

            # Verify merge_files_ffmpeg was called with None for ffmpeg_path
            assert mock_merge_ffmpeg.call_count == 1
            mock_merge_ffmpeg.assert_called_with(
                ANY, self.output_file, None)

            # Verify result is success
            assert result["success"] is True

    def test_merge_files_remove_temp_file_exception(self) -> None:
        """Test merge_files handles exception when removing temporary TS file."""
        with patch('merger.is_ffmpeg_available', return_value=True), \
                patch('merger.merge_files_ffmpeg', return_value={"success": False}), \
                patch('merger.merge_files_binary', return_value={"success": True}), \
                patch('merger.convert_ts_to_mp4', return_value={"success": True}), \
                patch('os.path.exists', return_value=True), \
                patch('os.remove', side_effect=Exception("Remove failed")), \
                patch('loguru.logger.warning') as mock_logger_warning:

            result = merge_files(
                self.test_files, self.output_file, self.settings)

            # Verify logger.warning was called for the remove exception
            assert mock_logger_warning.call_count == 1

            # But overall operation should still succeed
            assert result["success"] is True


if __name__ == "__main__":
    pytest.main(["-v", "test_merger.py"])
