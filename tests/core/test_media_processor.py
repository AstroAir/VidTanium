import pytest
import subprocess
from unittest.mock import patch, MagicMock
from typing import Dict, Any
from media_processor import MediaProcessor


class TestMediaProcessor:
    """Test suite for the MediaProcessor class."""

    def setup_method(self) -> None:
        """Set up test fixtures before each test."""
        self.ffmpeg_path = "/usr/bin/ffmpeg"
        self.processor = MediaProcessor(ffmpeg_path=self.ffmpeg_path)
        self.input_file = "input.mp4"
        self.output_file = "output.mp4"

    def test_init(self) -> None:
        """Test initialization of MediaProcessor."""
        # Test with custom ffmpeg path
        processor = MediaProcessor(ffmpeg_path=self.ffmpeg_path)
        assert processor.ffmpeg_path == self.ffmpeg_path
        assert processor.last_command == ""
        assert processor.last_output == ""

        # Test with default ffmpeg path (None)
        processor = MediaProcessor()
        assert processor.ffmpeg_path is None
        assert processor.last_command == ""
        assert processor.last_output == ""

    @patch('os.path.exists')
    def test_convert_format_file_not_exists(self, mock_exists: MagicMock) -> None:
        """Test convert_format when input file doesn't exist."""
        mock_exists.return_value = False
        result = self.processor.convert_format(
            self.input_file, self.output_file)
        assert result["success"] is False
        assert f"Input file does not exist: {self.input_file}" in result["error"]

    @patch('os.path.exists')
    @patch.object(MediaProcessor, '_run_command')
    def test_convert_format_default_options(self, mock_run_command: MagicMock, mock_exists: MagicMock) -> None:
        """Test convert_format with default options."""
        mock_exists.return_value = True
        mock_run_command.return_value = {"success": True, "output": "Success"}

        result = self.processor.convert_format(
            self.input_file, self.output_file)

        assert result["success"] is True
        assert mock_run_command.call_count == 1
        # Verify command has correct structure
        cmd = mock_run_command.call_args[0][0]
        assert cmd[0] == self.ffmpeg_path
        assert cmd[1] == "-i"
        assert cmd[2] == self.input_file
        assert "-c:v" in cmd
        assert "copy" in cmd
        assert "-c:a" in cmd
        assert "copy" in cmd
        assert "-y" in cmd
        assert self.output_file in cmd

    @patch('os.path.exists')
    @patch.object(MediaProcessor, '_run_command')
    def test_convert_format_custom_options(self, mock_run_command: MagicMock, mock_exists: MagicMock) -> None:
        """Test convert_format with custom options."""
        mock_exists.return_value = True
        mock_run_command.return_value = {"success": True, "output": "Success"}

        # 添加类型标注解决 "format_options"的类型部分未知 问题
        format_options: dict[str, str | int] = {
            "codec": "h264",
            "audio_codec": "aac",
            "bitrate": "2000k",
            "audio_bitrate": "128k",
            "resolution": "1280x720",
            "fps": 30
        }

        result = self.processor.convert_format(
            self.input_file, self.output_file, format_options)

        assert result["success"] is True
        assert mock_run_command.call_count == 1
        # Verify command has correct structure with options
        cmd = mock_run_command.call_args[0][0]
        assert cmd[0] == self.ffmpeg_path
        assert "-c:v" in cmd
        assert "h264" in cmd
        assert "-b:v" in cmd
        assert "2000k" in cmd
        assert "-s" in cmd
        assert "1280x720" in cmd
        assert "-r" in cmd
        assert "30" in cmd
        assert "-c:a" in cmd
        assert "aac" in cmd
        assert "-b:a" in cmd
        assert "128k" in cmd

    @patch('os.path.exists')
    def test_clip_video_file_not_exists(self, mock_exists: MagicMock) -> None:
        """Test clip_video when input file doesn't exist."""
        mock_exists.return_value = False
        result = self.processor.clip_video(self.input_file, self.output_file)
        assert result["success"] is False
        assert f"Input file does not exist: {self.input_file}" in result["error"]

    @patch('os.path.exists')
    @patch.object(MediaProcessor, '_run_command')
    def test_clip_video_without_times(self, mock_run_command: MagicMock, mock_exists: MagicMock) -> None:
        """Test clip_video without specifying times."""
        mock_exists.return_value = True
        mock_run_command.return_value = {"success": True, "output": "Success"}

        result = self.processor.clip_video(self.input_file, self.output_file)

        assert result["success"] is True
        assert mock_run_command.call_count == 1
        # Verify command has correct structure
        cmd = mock_run_command.call_args[0][0]
        assert cmd[0] == self.ffmpeg_path
        assert "-i" in cmd
        assert self.input_file in cmd
        assert "-ss" not in cmd  # No start time
        assert "-t" not in cmd   # No duration
        assert "-c" in cmd
        assert "copy" in cmd
        assert "-y" in cmd
        assert self.output_file in cmd

    @patch('os.path.exists')
    @patch.object(MediaProcessor, '_run_command')
    def test_clip_video_with_times(self, mock_run_command: MagicMock, mock_exists: MagicMock) -> None:
        """Test clip_video with specified times."""
        mock_exists.return_value = True
        mock_run_command.return_value = {"success": True, "output": "Success"}

        result = self.processor.clip_video(
            self.input_file, self.output_file, start_time="00:01:00", duration="00:00:30")

        assert result["success"] is True
        assert mock_run_command.call_count == 1
        # Verify command has correct structure
        cmd = mock_run_command.call_args[0][0]
        assert cmd[0] == self.ffmpeg_path
        assert "-ss" in cmd
        assert "00:01:00" in cmd
        assert "-t" in cmd
        assert "00:00:30" in cmd

    @patch('os.path.exists')
    def test_extract_audio_file_not_exists(self, mock_exists: MagicMock) -> None:
        """Test extract_audio when input file doesn't exist."""
        mock_exists.return_value = False
        result = self.processor.extract_audio(self.input_file, "output.mp3")
        assert result["success"] is False
        assert f"Input file does not exist: {self.input_file}" in result["error"]

    @patch('os.path.exists')
    @patch.object(MediaProcessor, '_run_command')
    def test_extract_audio_default(self, mock_run_command: MagicMock, mock_exists: MagicMock) -> None:
        """Test extract_audio with default settings."""
        mock_exists.return_value = True
        mock_run_command.return_value = {"success": True, "output": "Success"}

        audio_output = "output.mp3"
        result = self.processor.extract_audio(self.input_file, audio_output)

        assert result["success"] is True
        assert mock_run_command.call_count == 1
        # Verify command has correct structure
        cmd = mock_run_command.call_args[0][0]
        assert cmd[0] == self.ffmpeg_path
        assert "-i" in cmd
        assert self.input_file in cmd
        assert "-vn" in cmd  # Remove video
        assert "-f" in cmd
        assert "mp3" in cmd
        assert "-y" in cmd
        assert audio_output in cmd

    @patch('os.path.exists')
    @patch.object(MediaProcessor, '_run_command')
    def test_extract_audio_custom(self, mock_run_command: MagicMock, mock_exists: MagicMock) -> None:
        """Test extract_audio with custom settings."""
        mock_exists.return_value = True
        mock_run_command.return_value = {"success": True, "output": "Success"}

        audio_output = "output.aac"
        result = self.processor.extract_audio(
            self.input_file, audio_output, audio_format="aac", audio_bitrate="192k")

        assert result["success"] is True
        assert mock_run_command.call_count == 1
        # Verify command has correct structure
        cmd = mock_run_command.call_args[0][0]
        assert "-f" in cmd
        assert "aac" in cmd
        assert "-b:a" in cmd
        assert "192k" in cmd

    @patch('os.path.exists')
    def test_edit_metadata_file_not_exists(self, mock_exists: MagicMock) -> None:
        """Test edit_metadata when input file doesn't exist."""
        mock_exists.return_value = False
        result = self.processor.edit_metadata(
            self.input_file, self.output_file, {"title": "Test"})
        assert result["success"] is False
        assert f"Input file does not exist: {self.input_file}" in result["error"]

    def test_edit_metadata_no_metadata(self) -> None:
        """Test edit_metadata with no metadata provided."""
        result = self.processor.edit_metadata(
            self.input_file, self.output_file, {})
        assert result["success"] is False
        assert "No metadata provided" in result["error"]

    @patch('os.path.exists')
    @patch.object(MediaProcessor, '_run_command')
    def test_edit_metadata(self, mock_run_command: MagicMock, mock_exists: MagicMock) -> None:
        """Test edit_metadata with metadata."""
        mock_exists.return_value = True
        mock_run_command.return_value = {"success": True, "output": "Success"}

        metadata = {
            "title": "Test Video",
            "artist": "Test Artist",
            "year": "2023"
        }

        result = self.processor.edit_metadata(
            self.input_file, self.output_file, metadata)

        assert result["success"] is True
        assert mock_run_command.call_count == 1
        # Verify command has metadata arguments
        cmd = mock_run_command.call_args[0][0]
        assert "-metadata" in cmd
        assert "title=Test Video" in cmd
        assert "artist=Test Artist" in cmd
        assert "year=2023" in cmd
        assert "-c" in cmd
        assert "copy" in cmd

    @patch('os.path.exists')
    def test_compress_video_file_not_exists(self, mock_exists: MagicMock) -> None:
        """Test compress_video when input file doesn't exist."""
        mock_exists.return_value = False
        result = self.processor.compress_video(
            self.input_file, self.output_file)
        assert result["success"] is False
        assert f"Input file does not exist: {self.input_file}" in result["error"]

    @patch('os.path.exists')
    @patch.object(MediaProcessor, '_run_command')
    @patch('media_processor.MediaProcessor.get_video_info')
    def test_compress_video_with_target_size(self, mock_get_video_info: MagicMock,
                                             mock_run_command: MagicMock,
                                             mock_exists: MagicMock) -> None:
        """Test compress_video with target size."""
        mock_exists.return_value = True
        mock_run_command.return_value = {"success": True, "output": "Success"}
        # 使用一个可公开访问的方法替代受保护的 _get_video_duration
        mock_get_video_info.return_value = {
            "success": True, "info": {"format": {"duration": "300"}}}

        result = self.processor.compress_video(
            self.input_file, self.output_file, target_size_mb=100)

        assert result["success"] is True
        assert mock_run_command.call_count == 1
        # Verify command has bitrate calculated from target size
        cmd = mock_run_command.call_args[0][0]
        assert "-b:v" in cmd
        # Bitrate should be calculated: 100MB * 8 * 1024 / 300s = 2730.67 kbps
        # The exact value might differ due to rounding
        assert any(arg.endswith("k") for arg in cmd)
        assert "-c:v" in cmd
        assert "libx264" in cmd
        assert "-c:a" in cmd
        assert "copy" in cmd

    @patch('os.path.exists')
    @patch.object(MediaProcessor, '_run_command')
    def test_compress_video_with_quality(self, mock_run_command: MagicMock, mock_exists: MagicMock) -> None:
        """Test compress_video with quality setting."""
        mock_exists.return_value = True
        mock_run_command.return_value = {"success": True, "output": "Success"}

        result = self.processor.compress_video(
            self.input_file, self.output_file, quality=23)

        assert result["success"] is True
        assert mock_run_command.call_count == 1
        # Verify command has CRF setting
        cmd = mock_run_command.call_args[0][0]
        assert "-crf" in cmd
        assert "23" in cmd
        assert "-c:v" in cmd
        assert "libx264" in cmd

    @patch('os.path.exists')
    def test_get_video_info_file_not_exists(self, mock_exists: MagicMock) -> None:
        """Test get_video_info when file doesn't exist."""
        mock_exists.return_value = False
        result = self.processor.get_video_info(self.input_file)
        assert result["success"] is False
        assert f"File does not exist: {self.input_file}" in result["error"]

    @patch('os.path.exists')
    @patch.object(MediaProcessor, '_run_command')
    def test_get_video_info_command_failed(self, mock_run_command: MagicMock, mock_exists: MagicMock) -> None:
        """Test get_video_info when command fails."""
        mock_exists.return_value = True
        mock_run_command.return_value = {
            "success": False, "error": "Command failed"}

        result = self.processor.get_video_info(self.input_file)

        assert result["success"] is False
        assert "Command failed" in result["error"]
        assert mock_run_command.call_count == 1
        # Verify ffprobe command structure
        cmd = mock_run_command.call_args[0][0]
        assert "ffprobe" in cmd[0]
        assert "-v" in cmd
        assert "quiet" in cmd
        assert "-print_format" in cmd
        assert "json" in cmd
        assert "-show_format" in cmd
        assert "-show_streams" in cmd
        assert self.input_file in cmd

    @patch('os.path.exists')
    @patch.object(MediaProcessor, '_run_command')
    def test_get_video_info_success(self, mock_run_command: MagicMock, mock_exists: MagicMock) -> None:
        """Test get_video_info with successful command."""
        mock_exists.return_value = True
        json_output = '{"streams": [{"codec_type": "video"}], "format": {"duration": "300.5"}}'
        mock_run_command.return_value = {
            "success": True, "output": json_output}

        result = self.processor.get_video_info(self.input_file)

        assert result["success"] is True
        assert "info" in result
        assert "streams" in result["info"]
        assert "format" in result["info"]
        assert result["info"]["format"]["duration"] == "300.5"

    @patch('os.path.exists')
    @patch.object(MediaProcessor, '_run_command')
    def test_get_video_info_invalid_json(self, mock_run_command: MagicMock, mock_exists: MagicMock) -> None:
        """Test get_video_info with invalid JSON output."""
        mock_exists.return_value = True
        mock_run_command.return_value = {"success": True, "output": "Not JSON"}

        result = self.processor.get_video_info(self.input_file)

        assert result["success"] is False
        assert "Failed to parse video information" in result["error"]

    @patch('media_processor.MediaProcessor.get_video_info')
    def test_video_processor_methods(self, mock_get_video_info: MagicMock) -> None:
        """测试 MediaProcessor 中可供公开访问的方法，避免直接访问受保护的方法"""
        # 测试有 duration 的情况
        mock_get_video_info.return_value = {
            "success": True, "info": {"format": {"duration": "123.45"}}}

        # 创建一个测试用的 MediaProcessor 子类来访问受保护的方法
        class TestableMediaProcessor(MediaProcessor):
            def get_video_duration(self, video_file: str) -> float:
                return self._get_video_duration(video_file)

            def run_command(self, command: list[str]) -> Dict[str, Any]:
                return self._run_command(command)

        # 创建可测试的处理器
        processor = TestableMediaProcessor(self.ffmpeg_path)

        # 测试 get_video_duration
        duration = processor.get_video_duration(self.input_file)
        assert duration == 123.45

        # 测试没有 duration 的情况
        mock_get_video_info.return_value = {
            "success": True, "info": {"format": {}}}
        duration = processor.get_video_duration(self.input_file)
        assert duration == 0

        # 测试 API 错误的情况
        mock_get_video_info.return_value = {"success": False, "error": "Error"}
        duration = processor.get_video_duration(self.input_file)
        assert duration == 0

        # 测试 run_command
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = "Processing completed"

        with patch('subprocess.run', return_value=mock_result):
            cmd = ["echo", "test"]
            result = processor.run_command(cmd)

            assert result["success"] is True
            assert result["output"] == "Processing completed"
            assert processor.last_command == "echo test"
            assert processor.last_output == "Processing completed"

    @patch('subprocess.run')
    def test_run_command_methods(self, mock_subprocess_run: MagicMock) -> None:
        """通过子类测试 _run_command 方法"""
        # 创建一个测试用的 MediaProcessor 子类来访问受保护的方法
        class TestableMediaProcessor(MediaProcessor):
            def run_command(self, command: list[str]) -> Dict[str, Any]:
                return self._run_command(command)

        processor = TestableMediaProcessor(self.ffmpeg_path)

        # 测试成功情况
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = "Processing completed"
        mock_subprocess_run.return_value = mock_result

        cmd = ["echo", "test"]
        result = processor.run_command(cmd)

        assert result["success"] is True
        assert result["output"] == "Processing completed"
        assert processor.last_command == "echo test"
        assert processor.last_output == "Processing completed"
        assert mock_subprocess_run.call_count == 1

        # 测试失败情况
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Error occurred"
        mock_subprocess_run.return_value = mock_result

        cmd = ["false"]
        result = processor.run_command(cmd)

        assert result["success"] is False
        assert result["error"] == "Error occurred"
        assert processor.last_command == "false"
        assert processor.last_output == "Error occurred"

        # 测试异常情况
        mock_subprocess_run.side_effect = Exception("Test exception")

        cmd = ["nonexistent"]
        result = processor.run_command(cmd)

        assert result["success"] is False
        assert "Test exception" in result["error"]
        assert processor.last_command == "nonexistent"

    @patch('os.path.exists')
    def test_batch_convert_file_input_not_exists(self, mock_exists: MagicMock) -> None:
        """Test batch_convert_file when input file doesn't exist."""
        mock_exists.return_value = False
        result = self.processor.batch_convert_file(self.input_file, {})
        assert result["success"] is False
        assert "输入文件不存在" in result["message"]

    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('subprocess.run')
    def test_batch_convert_file_success(self, mock_run: MagicMock,
                                        mock_makedirs: MagicMock,
                                        mock_exists: MagicMock) -> None:
        """Test batch_convert_file with successful conversion."""
        mock_exists.side_effect = [
            True, False]  # Input exists, output does not
        mock_run.return_value = MagicMock(returncode=0)

        # 添加类型标注解决 "options"的类型部分未知 问题
        options: dict[str, str | int | bool] = {
            "format": "mp4",
            "output_dir": "/output",
            "video_codec": "libx264",
            "audio_codec": "aac",
            "bitrate": 2000,
            "resolution": "720p",
            "keep_original": True
        }

        result = self.processor.batch_convert_file(self.input_file, options)

        assert result["success"] is True
        assert "文件转换成功" in result["message"]
        assert "output_file" in result
        assert mock_makedirs.call_count == 1
        assert mock_run.call_count == 1
        # Verify command structure
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == self.ffmpeg_path
        assert "-c:v" in cmd
        assert "libx264" in cmd
        assert "-b:v" in cmd
        assert "2000k" in cmd
        assert "-vf" in cmd
        assert "scale=1280:720" in cmd
        assert "-c:a" in cmd
        assert "aac" in cmd
        assert "-f" in cmd
        assert "mp4" in cmd

    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('subprocess.run')
    def test_batch_convert_file_with_copy_mode(self, mock_run: MagicMock,
                                               mock_makedirs: MagicMock,
                                               mock_exists: MagicMock) -> None:
        """Test batch_convert_file with copy mode."""
        mock_exists.side_effect = [
            True, False]  # Input exists, output does not
        mock_run.return_value = MagicMock(returncode=0)

        # 添加类型标注
        options: dict[str, str] = {
            "format": "mp4",
            "video_codec": "copy",
            "audio_codec": "copy"
        }

        result = self.processor.batch_convert_file(self.input_file, options)

        assert result["success"] is True
        assert mock_run.call_count == 1
        # Verify command structure for copy mode
        cmd = mock_run.call_args[0][0]
        assert "-c:v" in cmd
        assert "copy" in cmd
        assert "-c:a" in cmd
        assert "copy" in cmd

    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('subprocess.run')
    @patch('os.remove')
    def test_batch_convert_file_delete_original(self, mock_remove: MagicMock,
                                                mock_run: MagicMock,
                                                mock_makedirs: MagicMock,
                                                mock_exists: MagicMock) -> None:
        """Test batch_convert_file with delete original option."""
        mock_exists.side_effect = [
            True, False, True]  # Input exists, output doesn't initially, output exists after conversion
        mock_run.return_value = MagicMock(returncode=0)

        # 添加类型标注
        options: dict[str, str | bool] = {
            "format": "mp4",
            "keep_original": False
        }

        result = self.processor.batch_convert_file(self.input_file, options)

        assert result["success"] is True
        assert mock_remove.call_count == 1

    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('subprocess.run')
    def test_batch_convert_file_output_exists(self, mock_run: MagicMock,
                                              mock_makedirs: MagicMock,
                                              mock_exists: MagicMock) -> None:
        """Test batch_convert_file when output file already exists."""
        mock_exists.side_effect = [
            True, True, False]  # Input exists, output.mp4 exists, output_converted.mp4 doesn't
        mock_run.return_value = MagicMock(returncode=0)

        # 添加类型标注
        options: dict[str, str] = {"format": "mp4"}
        result = self.processor.batch_convert_file(self.input_file, options)

        assert result["success"] is True
        assert "input_converted.mp4" in result["output_file"]

    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('subprocess.run')
    def test_batch_convert_file_ffmpeg_error(self, mock_run: MagicMock,
                                             mock_makedirs: MagicMock,
                                             mock_exists: MagicMock) -> None:
        """Test batch_convert_file when FFmpeg returns an error."""
        mock_exists.side_effect = [True, False]  # Input exists, output doesn't
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "ffmpeg", stderr="FFmpeg error")

        # 添加类型标注
        options: dict[str, str] = {"format": "mp4"}
        result = self.processor.batch_convert_file(self.input_file, options)

        assert result["success"] is False
        assert "FFmpeg 执行错误" in result["message"]

    @patch('os.path.exists')
    def test_batch_convert_file_general_exception(self, mock_exists: MagicMock) -> None:
        """Test batch_convert_file with a general exception."""
        mock_exists.side_effect = Exception("Test exception")

        # 添加类型标注
        options: dict[str, str] = {"format": "mp4"}
        result = self.processor.batch_convert_file(self.input_file, options)

        assert result["success"] is False
        assert "转换过程中出错" in result["message"]
        assert "Test exception" in result["message"]


if __name__ == "__main__":
    pytest.main(["-v", "test_media_processor.py"])
