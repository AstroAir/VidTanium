import os
import subprocess
import shutil
import tempfile
from typing import List, Dict, Any, Optional
from loguru import logger
from src.core.utils.version_checker import VersionChecker  # Added import


def is_ffmpeg_available(ffmpeg_path: Optional[str] = None) -> bool:
    """Check if FFmpeg is installed and available in the system.
    Uses VersionChecker if no specific path is provided or if the path is empty.
    """
    if ffmpeg_path and ffmpeg_path.strip():  # If a specific, non-empty path is provided
        # Test this specific ffmpeg path
        cmd: List[str] = [ffmpeg_path, "-version"]
        try:
            result = subprocess.run(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False
            )
            if result.returncode == 0:
                logger.debug(
                    f"FFmpeg confirmed at specified path: {ffmpeg_path}")
                return True
            else:
                logger.debug(
                    f"Specified ffmpeg path {ffmpeg_path} did not respond to -version correctly. stderr: {result.stderr}")
                return False
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.debug(
                f"Failed to run ffmpeg -version with specified path: {ffmpeg_path}")
            return False
    else:  # If no specific path or path is empty/whitespace, use VersionChecker
        logger.debug(
            "No specific ffmpeg path provided or path is empty; using VersionChecker.")
        checker = VersionChecker()
        try:
            ffmpeg_info = checker.check_software("ffmpeg")
            if ffmpeg_info.installed:
                logger.debug(
                    f"VersionChecker found ffmpeg: Path='{ffmpeg_info.path}', Version='{ffmpeg_info.version}', Installed={ffmpeg_info.installed}")
                return True
            else:
                logger.debug("VersionChecker did not find ffmpeg.")
                return False
        except Exception as e:
            # Log the exception from VersionChecker if it fails unexpectedly
            logger.warning(
                f"VersionChecker encountered an error while checking for ffmpeg: {e}", exc_info=True)
            return False


def merge_files_ffmpeg(files: List[str], output_file: str, ffmpeg_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Merge video files using FFmpeg

    Args:
        files: List of files to merge
        output_file: Output file path
        ffmpeg_path: Path to FFmpeg executable

    Returns:
        dict: Result of the merge operation
    """
    try:
        # Create temporary file list
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            filelist = f.name
            for file in files:
                f.write(f"file '{os.path.abspath(file)}'\n")

        # Build FFmpeg command
        cmd: List[str] = [
            ffmpeg_path or "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", filelist,
            "-c", "copy",
            "-y",
            output_file
        ]

        # Execute command
        logger.info(f"Executing FFmpeg command: {' '.join(cmd)}")
        result = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Delete temporary file
        if os.path.exists(filelist):
            os.remove(filelist)

        # Check result
        if result.returncode != 0:
            logger.error(f"FFmpeg merge failed: {result.stderr}")
            return {"success": False, "error": result.stderr}

        logger.success(f"Successfully merged {len(files)} files using FFmpeg")
        return {"success": True}

    except Exception as e:
        logger.error(f"FFmpeg merge failed: {str(e)}", exc_info=True)
        return {"success": False, "error": str(e)}


def merge_files_binary(files: List[str], output_file: str) -> Dict[str, Any]:
    """
    Merge files using binary concatenation

    Args:
        files: List of files to merge
        output_file: Output file path

    Returns:
        dict: Result of the merge operation
    """
    try:
        with open(output_file, 'wb') as outfile:
            for file in files:
                if not os.path.exists(file):
                    logger.warning(f"File not found, skipping: {file}")
                    continue

                with open(file, 'rb') as infile:
                    shutil.copyfileobj(infile, outfile)
                    logger.debug(f"Appended file: {file}")

        logger.success(
            f"Successfully merged {len(files)} files using binary concatenation")
        return {"success": True}

    except Exception as e:
        logger.error(f"Binary merge failed: {str(e)}", exc_info=True)
        return {"success": False, "error": str(e)}


def convert_ts_to_mp4(ts_file: str, output_file: str, ffmpeg_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Convert TS file to MP4 format

    Args:
        ts_file: Input TS file path
        output_file: Output MP4 file path
        ffmpeg_path: Path to FFmpeg executable

    Returns:
        dict: Result of the conversion operation
    """
    try:
        cmd: List[str] = [
            ffmpeg_path or "ffmpeg",
            "-i", ts_file,
            "-c", "copy",
            "-y",
            output_file
        ]

        logger.info(f"Executing FFmpeg conversion command: {' '.join(cmd)}")
        result = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode != 0:
            logger.error(f"Conversion failed: {result.stderr}")
            return {"success": False, "error": result.stderr}

        logger.success(f"Successfully converted TS to MP4: {output_file}")
        return {"success": True}

    except Exception as e:
        logger.error(f"Conversion failed: {str(e)}", exc_info=True)
        return {"success": False, "error": str(e)}


def merge_files(files: List[str], output_file: str, settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Choose appropriate method to merge video files based on available tools

    Args:
        files: List of files to merge
        output_file: Output file path
        settings: Settings object containing configuration

    Returns:
        dict: Dictionary containing merge results
    """
    if not files:
        logger.error("No files to merge")
        return {"success": False, "error": "No files to merge"}

    # Sort files by name
    try:
        sorted_files: List[str] = sorted(files, key=lambda x: int(
            os.path.basename(x).split('_')[1].split('.')[0]))
    except (IndexError, ValueError):
        # Fallback to direct sorting if custom sort fails
        logger.warning(
            "Failed to sort files by segment number, using filename sort instead")
        sorted_files = sorted(files)

    logger.info(
        f"Preparing to merge {len(sorted_files)} files into {output_file}")

    # Get FFmpeg path from settings
    ffmpeg_path: Optional[str] = None
    if settings:
        ffmpeg_path = settings.get("advanced", {}).get("ffmpeg_path", "")

    # Check if FFmpeg is available
    if is_ffmpeg_available(ffmpeg_path):
        logger.info("FFmpeg is available, attempting direct MP4 merge")
        # Directly merge to MP4 using FFmpeg
        result = merge_files_ffmpeg(sorted_files, output_file, ffmpeg_path)
        if result["success"]:
            return result

        # If direct merge fails, try binary merge and then convert
        logger.warning(
            "Direct FFmpeg merge failed, attempting binary merge followed by conversion")

    # Use binary method to merge to TS
    ts_output = f"{output_file}.ts"
    logger.info(f"Performing binary merge to temporary file: {ts_output}")
    result = merge_files_binary(sorted_files, ts_output)

    if not result["success"]:
        return result

    # If FFmpeg is available and MP4 format is needed, convert to MP4
    if output_file.lower().endswith('.mp4') and is_ffmpeg_available(ffmpeg_path):
        logger.info(f"Converting merged TS file to MP4: {output_file}")
        result = convert_ts_to_mp4(ts_output, output_file, ffmpeg_path)

        # Delete temporary TS file
        if os.path.exists(ts_output):
            try:
                os.remove(ts_output)
                logger.debug(f"Deleted temporary TS file: {ts_output}")
            except Exception as e:
                logger.warning(f"Failed to delete temporary TS file: {e}")

        return result

    # If no conversion needed or FFmpeg not available, simply rename
    if ts_output != output_file:
        try:
            logger.info(f"Renaming {ts_output} to {output_file}")
            shutil.move(ts_output, output_file)
        except Exception as e:
            logger.error(f"Failed to rename file: {str(e)}", exc_info=True)
            return {"success": False, "error": f"Failed to rename file: {str(e)}"}

    logger.success(f"Successfully created output file: {output_file}")
    return {"success": True}
