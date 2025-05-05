import os
import subprocess
import shutil
import tempfile
from typing import Dict, List, Tuple, Any, Optional
from loguru import logger


class MediaProcessor:
    """Media processor for video transcoding, editing and other operations"""

    def __init__(self, ffmpeg_path=None):
        """
        Initialize media processor

        Args:
            ffmpeg_path: Path to FFmpeg executable
        """
        self.ffmpeg_path = ffmpeg_path
        self.last_command = ""
        self.last_output = ""
        logger.debug(
            f"MediaProcessor initialized with FFmpeg path: {ffmpeg_path or 'system default'}")

    def convert_format(self, input_file: str, output_file: str,
                       format_options: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Convert video format

        Args:
            input_file: Input file path
            output_file: Output file path
            format_options: Format options dictionary
                - codec: Video codec
                - audio_codec: Audio codec
                - bitrate: Video bitrate
                - audio_bitrate: Audio bitrate
                - resolution: Resolution
                - fps: Frame rate

        Returns:
            Dict: Dictionary containing processing results
        """
        logger.info(f"Converting format from {input_file} to {output_file}")

        if not os.path.exists(input_file):
            logger.error(f"Input file does not exist: {input_file}")
            return {"success": False, "error": f"Input file does not exist: {input_file}"}

        # Default options
        options = {
            "codec": "copy",
            "audio_codec": "copy",
            "bitrate": None,
            "audio_bitrate": None,
            "resolution": None,
            "fps": None
        }

        # Update options with provided values
        if format_options:
            options.update(format_options)
            logger.debug(f"Format options applied: {format_options}")

        # Build command
        cmd = [self.ffmpeg_path or "ffmpeg", "-i", input_file]

        # Add video encoding options
        if options["codec"] != "copy":
            cmd.extend(["-c:v", options["codec"]])
            logger.debug(f"Using video codec: {options['codec']}")

            # Video bitrate
            if options["bitrate"]:
                cmd.extend(["-b:v", options["bitrate"]])
                logger.debug(f"Setting video bitrate: {options['bitrate']}")

            # Resolution
            if options["resolution"]:
                cmd.extend(["-s", options["resolution"]])
                logger.debug(f"Setting resolution: {options['resolution']}")

            # Frame rate
            if options["fps"]:
                cmd.extend(["-r", str(options["fps"])])
                logger.debug(f"Setting frame rate: {options['fps']}")
        else:
            cmd.extend(["-c:v", "copy"])
            logger.debug("Using copy mode for video stream (no re-encoding)")

        # Add audio encoding options
        if options["audio_codec"] != "copy":
            cmd.extend(["-c:a", options["audio_codec"]])
            logger.debug(f"Using audio codec: {options['audio_codec']}")

            # Audio bitrate
            if options["audio_bitrate"]:
                cmd.extend(["-b:a", options["audio_bitrate"]])
                logger.debug(
                    f"Setting audio bitrate: {options['audio_bitrate']}")
        else:
            cmd.extend(["-c:a", "copy"])
            logger.debug("Using copy mode for audio stream (no re-encoding)")

        # Output file
        cmd.extend(["-y", output_file])

        return self._run_command(cmd)

    def clip_video(self, input_file: str, output_file: str,
                   start_time: str = None, duration: str = None) -> Dict[str, Any]:
        """
        Clip video

        Args:
            input_file: Input file path
            output_file: Output file path
            start_time: Start time (HH:MM:SS.xxx)
            duration: Duration (HH:MM:SS.xxx)

        Returns:
            Dict: Dictionary containing processing results
        """
        logger.info(f"Clipping video: {input_file} → {output_file}")
        logger.debug(
            f"Clip settings - Start time: {start_time or 'beginning'}, Duration: {duration or 'until end'}")

        if not os.path.exists(input_file):
            logger.error(f"Input file does not exist: {input_file}")
            return {"success": False, "error": f"Input file does not exist: {input_file}"}

        # Build command
        cmd = [self.ffmpeg_path or "ffmpeg", "-i", input_file]

        # Add start time
        if start_time:
            cmd.extend(["-ss", start_time])

        # Add duration
        if duration:
            cmd.extend(["-t", duration])

        # Don't re-encode (stream copy)
        cmd.extend(["-c", "copy"])
        logger.debug("Using stream copy mode (no re-encoding)")

        # Output file
        cmd.extend(["-y", output_file])

        return self._run_command(cmd)

    def extract_audio(self, input_file: str, output_file: str,
                      audio_format: str = "mp3", audio_bitrate: str = None) -> Dict[str, Any]:
        """
        Extract audio track from video

        Args:
            input_file: Input file path
            output_file: Output file path
            audio_format: Audio format
            audio_bitrate: Audio bitrate

        Returns:
            Dict: Dictionary containing processing results
        """
        logger.info(f"Extracting audio from {input_file} to {output_file}")
        logger.debug(
            f"Audio extraction settings - Format: {audio_format}, Bitrate: {audio_bitrate or 'default'}")

        if not os.path.exists(input_file):
            logger.error(f"Input file does not exist: {input_file}")
            return {"success": False, "error": f"Input file does not exist: {input_file}"}

        # Build command
        cmd = [self.ffmpeg_path or "ffmpeg", "-i", input_file, "-vn"]

        # Add audio format
        if audio_format:
            cmd.extend(["-f", audio_format])

        # Add audio bitrate
        if audio_bitrate:
            cmd.extend(["-b:a", audio_bitrate])

        # Output file
        cmd.extend(["-y", output_file])

        return self._run_command(cmd)

    def edit_metadata(self, input_file: str, output_file: str,
                      metadata: Dict[str, str]) -> Dict[str, Any]:
        """
        Edit media metadata

        Args:
            input_file: Input file path
            output_file: Output file path
            metadata: Metadata dictionary

        Returns:
            Dict: Dictionary containing processing results
        """
        logger.info(f"Editing metadata for {input_file}")
        logger.debug(f"Metadata to set: {metadata}")

        if not os.path.exists(input_file):
            logger.error(f"Input file does not exist: {input_file}")
            return {"success": False, "error": f"Input file does not exist: {input_file}"}

        if not metadata:
            logger.error("No metadata provided")
            return {"success": False, "error": "No metadata provided"}

        # Build command
        cmd = [self.ffmpeg_path or "ffmpeg", "-i", input_file]

        # Add metadata
        for key, value in metadata.items():
            cmd.extend(["-metadata", f"{key}={value}"])

        # Don't re-encode
        cmd.extend(["-c", "copy"])
        logger.debug("Using stream copy mode (no re-encoding)")

        # Output file
        cmd.extend(["-y", output_file])

        return self._run_command(cmd)

    def compress_video(self, input_file: str, output_file: str,
                       target_size_mb: int = None, quality: int = None) -> Dict[str, Any]:
        """
        Compress video

        Args:
            input_file: Input file path
            output_file: Output file path
            target_size_mb: Target size in MB
            quality: Quality (0-51, 0 is lossless, 23 is default, 51 is worst)

        Returns:
            Dict: Dictionary containing processing results
        """
        logger.info(f"Compressing video: {input_file} → {output_file}")
        logger.debug(
            f"Compression settings - Target size: {target_size_mb or 'not specified'} MB, Quality: {quality or 'not specified'}")

        if not os.path.exists(input_file):
            logger.error(f"Input file does not exist: {input_file}")
            return {"success": False, "error": f"Input file does not exist: {input_file}"}

        # Build command
        cmd = [self.ffmpeg_path or "ffmpeg", "-i", input_file]

        if target_size_mb:
            # Get video duration
            duration = self._get_video_duration(input_file)
            if duration:
                # Calculate bitrate (in kbps)
                # Formula: bitrate = target_size_bytes * 8 / duration_seconds / 1000
                bitrate = int(target_size_mb * 8 * 1024 / duration)
                cmd.extend(["-b:v", f"{bitrate}k"])
                logger.debug(
                    f"Calculated bitrate for {target_size_mb}MB target: {bitrate}k")

        if quality is not None:
            # Use CRF (Constant Rate Factor) mode for quality-based encoding
            cmd.extend(["-crf", str(quality)])
            logger.debug(f"Using CRF quality setting: {quality}")

        # Use libx264 encoder
        cmd.extend(["-c:v", "libx264"])
        logger.debug("Using libx264 video codec for compression")

        # Keep audio unchanged
        cmd.extend(["-c:a", "copy"])
        logger.debug("Keeping audio stream unchanged")

        # Output file
        cmd.extend(["-y", output_file])

        return self._run_command(cmd)

    def get_video_info(self, video_file: str) -> Dict[str, Any]:
        """
        Get video information

        Args:
            video_file: Video file path

        Returns:
            Dict: Dictionary containing video information
        """
        logger.info(f"Getting video information for: {video_file}")

        if not os.path.exists(video_file):
            logger.error(f"File does not exist: {video_file}")
            return {"success": False, "error": f"File does not exist: {video_file}"}

        # Use ffprobe to get video information
        cmd = [
            self.ffmpeg_path[:-5] + "probe" if self.ffmpeg_path else "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            video_file
        ]

        result = self._run_command(cmd)

        if not result["success"]:
            return result

        # Parse output
        import json
        try:
            info = json.loads(result["output"])
            logger.debug(
                f"Successfully parsed video metadata ({len(info.get('streams', []))} streams found)")
            return {"success": True, "info": info}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse video information: {e}")
            return {"success": False, "error": f"Failed to parse video information: {e}"}

    def _get_video_duration(self, video_file: str) -> float:
        """
        Get video duration in seconds

        Args:
            video_file: Video file path

        Returns:
            float: Video duration in seconds
        """
        result = self.get_video_info(video_file)

        if result["success"] and "info" in result:
            info = result["info"]
            if "format" in info and "duration" in info["format"]:
                duration = float(info["format"]["duration"])
                logger.debug(f"Video duration: {duration} seconds")
                return duration

        logger.warning("Could not determine video duration")
        return 0

    def _run_command(self, command: List[str]) -> Dict[str, Any]:
        """
        Run command

        Args:
            command: Command list

        Returns:
            Dict: Dictionary containing processing results
        """
        self.last_command = " ".join(command)
        logger.info(f"Executing command: {self.last_command}")

        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )

            self.last_output = result.stderr

            if result.returncode != 0:
                logger.error(
                    f"Command execution failed with return code {result.returncode}")
                logger.error(f"Error output: {result.stderr}")
                return {"success": False, "error": result.stderr}

            logger.success(
                f"Command executed successfully (return code: {result.returncode})")
            if len(result.stderr) > 0:
                logger.debug(
                    f"Command output: {result.stderr[:500]}{'...' if len(result.stderr) > 500 else ''}")

            return {"success": True, "output": result.stderr}

        except Exception as e:
            logger.error(f"Error executing command: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
