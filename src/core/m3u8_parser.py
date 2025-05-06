import re
import requests
import urllib.parse
from enum import Enum
from typing import List, Dict, Optional, Tuple, Any
from loguru import logger

# ========================================================================
# Enums - 枚举类型定义
# ========================================================================


class StreamType(Enum):
    """Stream type enumeration"""
    AUDIO = "audio"
    VIDEO = "video"
    SUBTITLES = "subtitles"
    CLOSED_CAPTIONS = "closed-captions"
    UNKNOWN = "unknown"


class EncryptionMethod(Enum):
    """Encryption method enumeration"""
    NONE = "NONE"
    AES_128 = "AES-128"
    SAMPLE_AES = "SAMPLE-AES"
    UNKNOWN = "UNKNOWN"


# ========================================================================
# Models - 数据模型定义
# ========================================================================


class M3U8Segment:
    """M3U8 video segment"""

    def __init__(self):
        self.url = ""
        self.duration = 0
        self.index = 0
        self.encryption = EncryptionMethod.NONE
        self.key_url = ""
        self.key_iv = ""
        self.discontinuity = False


class M3U8Stream:
    """M3U8 video stream"""

    def __init__(self):
        self.url = ""
        self.type = StreamType.UNKNOWN
        self.bandwidth = 0
        self.resolution = ""
        self.codecs = ""
        self.name = ""
        self.segments = []
        self.encryption = EncryptionMethod.NONE
        self.key_url = ""
        self.key_iv = ""
        self.duration = 0
        self.segment_count = 0
        self.base_url = ""


# ========================================================================
# Parser - M3U8 解析器
# ========================================================================


class M3U8Parser:
    """M3U8 parser"""

    def __init__(self):
        self.streams = []
        self.master_url = ""
        self.base_url = ""
        self.master_playlist = ""
        self.headers = {}
        self.timeout = 30

    def parse_url(self, url: str, headers: Dict[str, str] = None, timeout: int = 30) -> List[M3U8Stream]:
        """
        Parse M3U8 URL

        Args:
            url: M3U8 playlist URL
            headers: HTTP request headers
            timeout: Request timeout in seconds

        Returns:
            List of parsed video streams
        """
        self.master_url = url
        self.base_url = self._get_base_url(url)
        self.headers = headers or {}
        self.timeout = timeout
        self.streams = []

        try:
            # Download master playlist
            logger.info(f"Downloading M3U8 playlist: {url}")
            content = self._download_playlist(url)
            if not content:
                logger.error(f"Unable to download M3U8 playlist: {url}")
                return []

            self.master_playlist = content
            logger.debug(
                f"Successfully downloaded playlist ({len(content)} bytes)")

            # Check if it's a master playlist or media playlist
            if "#EXT-X-STREAM-INF" in content:
                # Master playlist containing multiple streams
                logger.debug("Detected master playlist with multiple streams")
                self._parse_master_playlist(content)
            else:
                # Media playlist with only one stream
                logger.debug("Detected media playlist with segments")
                stream = M3U8Stream()
                stream.url = url
                stream.base_url = self.base_url
                self._parse_media_playlist(content, stream)
                self.streams.append(stream)

            logger.success(
                f"Successfully parsed {len(self.streams)} streams from M3U8")
            return self.streams

        except Exception as e:
            logger.error(f"Error parsing M3U8: {e}", exc_info=True)
            return []

    def _download_playlist(self, url: str) -> str:
        """Download playlist content"""
        try:
            logger.debug(f"Sending HTTP request to: {url}")
            response = requests.get(
                url, headers=self.headers, timeout=self.timeout)
            if response.status_code == 200:
                logger.debug(
                    f"Successfully received playlist ({len(response.text)} bytes)")
                return response.text
            else:
                logger.error(
                    f"Failed to download playlist, status code: {response.status_code}")
                return ""
        except Exception as e:
            logger.error(f"Error downloading playlist: {e}", exc_info=True)
            return ""

    def _get_base_url(self, url: str) -> str:
        """Get base URL for resolving relative paths"""
        parsed_url = urllib.parse.urlparse(url)
        path_parts = parsed_url.path.split('/')

        # Remove the last part (filename)
        if '.' in path_parts[-1]:
            path_parts.pop()

        # Rebuild the path
        new_path = '/'.join(path_parts)
        if not new_path.endswith('/'):
            new_path += '/'

        base_url = urllib.parse.urlunparse((
            parsed_url.scheme,
            parsed_url.netloc,
            new_path,
            parsed_url.params,
            parsed_url.query,
            parsed_url.fragment
        ))

        logger.debug(f"Base URL for {url}: {base_url}")
        return base_url

    def _parse_master_playlist(self, content: str) -> None:
        """Parse master playlist"""
        logger.info("Parsing master playlist")
        lines = content.splitlines()
        stream_info = None

        for i, line in enumerate(lines):
            line = line.strip()

            if line.startswith('#EXT-X-STREAM-INF:'):
                stream_info = self._parse_attributes(line[18:])

                # Make sure the next line is a URL
                if i + 1 < len(lines) and not lines[i + 1].startswith('#'):
                    stream = M3U8Stream()

                    # Set URL (absolute or relative)
                    stream_url = lines[i + 1]
                    if stream_url.startswith('http'):
                        stream.url = stream_url
                    else:
                        stream.url = urllib.parse.urljoin(
                            self.base_url, stream_url)

                    stream.base_url = self._get_base_url(stream.url)
                    stream.type = StreamType.VIDEO

                    # Set stream attributes
                    if 'BANDWIDTH' in stream_info:
                        stream.bandwidth = int(stream_info['BANDWIDTH'])
                    if 'RESOLUTION' in stream_info:
                        stream.resolution = stream_info['RESOLUTION']
                    if 'CODECS' in stream_info:
                        stream.codecs = stream_info['CODECS']
                    if 'NAME' in stream_info:
                        stream.name = stream_info['NAME']

                    logger.debug(
                        f"Found stream: {stream.resolution}, {stream.bandwidth} bps, URL: {stream.url}")

                    # Download and parse media playlist
                    logger.debug(f"Downloading media playlist: {stream.url}")
                    media_content = self._download_playlist(stream.url)
                    if media_content:
                        self._parse_media_playlist(media_content, stream)
                    else:
                        logger.warning(
                            f"Unable to download media playlist: {stream.url}")

                    self.streams.append(stream)

        logger.debug(f"Found {len(self.streams)} streams in master playlist")

    def _parse_media_playlist(self, content: str, stream: M3U8Stream) -> None:
        """Parse media playlist"""
        logger.info(
            f"Parsing media playlist for stream: {stream.name or stream.url}")
        lines = content.splitlines()
        current_key_url = None
        current_key_iv = None
        current_encryption = EncryptionMethod.NONE
        segment_index = 0
        total_duration = 0

        for i, line in enumerate(lines):
            line = line.strip()

            # Parse key lines
            if line.startswith('#EXT-X-KEY:'):
                key_info = self._parse_attributes(line[11:])
                if 'METHOD' in key_info:
                    method = key_info['METHOD']
                    if method == 'NONE':
                        current_encryption = EncryptionMethod.NONE
                        current_key_url = None
                        current_key_iv = None
                        logger.debug("No encryption detected")
                    elif method in ['AES-128', 'SAMPLE-AES']:
                        current_encryption = EncryptionMethod.AES_128 if method == 'AES-128' else EncryptionMethod.SAMPLE_AES
                        logger.debug(f"Detected encryption: {method}")

                        if 'URI' in key_info:
                            key_uri = key_info['URI'].strip('"')
                            if key_uri.startswith('http'):
                                current_key_url = key_uri
                            else:
                                current_key_url = urllib.parse.urljoin(
                                    stream.base_url, key_uri)
                            logger.debug(
                                f"Encryption key URL: {current_key_url}")

                        if 'IV' in key_info:
                            current_key_iv = key_info['IV']
                            logger.debug(f"Encryption IV: {current_key_iv}")

            # Parse segment lines
            elif line.startswith('#EXTINF:'):
                duration_str = line[8:].split(',')[0]
                duration = float(duration_str)
                total_duration += duration

                # Make sure the next line is a URL
                if i + 1 < len(lines) and not lines[i + 1].startswith('#'):
                    segment = M3U8Segment()
                    segment.duration = duration
                    segment.index = segment_index
                    segment.encryption = current_encryption
                    segment.key_url = current_key_url
                    segment.key_iv = current_key_iv

                    # Set URL (absolute or relative)
                    segment_url = lines[i + 1]
                    if segment_url.startswith('http'):
                        segment.url = segment_url
                    else:
                        segment.url = urllib.parse.urljoin(
                            stream.base_url, segment_url)

                    stream.segments.append(segment)
                    segment_index += 1

                    # Log every 50 segments to avoid flooding logs
                    if segment_index % 50 == 0:
                        logger.debug(f"Parsed {segment_index} segments so far")

        # Update stream information
        stream.duration = total_duration
        stream.segment_count = segment_index
        logger.debug(
            f"Found {segment_index} segments with total duration {total_duration:.2f} seconds")

        # Set stream encryption info (using first encrypted segment)
        for segment in stream.segments:
            if segment.encryption != EncryptionMethod.NONE:
                stream.encryption = segment.encryption
                stream.key_url = segment.key_url
                stream.key_iv = segment.key_iv
                logger.debug(
                    f"Stream encryption: {stream.encryption.value}, Key URL: {stream.key_url}")
                break

    def _parse_attributes(self, attribute_string: str) -> Dict[str, str]:
        """Parse attribute string"""
        attributes = {}
        pattern = r'([A-Z0-9-]+)=(?:"([^"]*)"|([^",]*))(?:,|$)'
        matches = re.findall(pattern, attribute_string)

        for match in matches:
            key = match[0]
            value = match[1] if match[1] else match[2]
            attributes[key] = value

        return attributes

    def get_best_quality_stream(self) -> Optional[M3U8Stream]:
        """Get highest quality stream"""
        if not self.streams:
            logger.warning("No streams available to select best quality")
            return None

        # Sort by bandwidth and select highest
        sorted_streams = sorted(
            self.streams, key=lambda s: s.bandwidth, reverse=True)
        best_stream = sorted_streams[0]
        logger.debug(
            f"Selected best quality stream: {best_stream.resolution}, {best_stream.bandwidth} bps")
        return best_stream

    def get_lowest_quality_stream(self) -> Optional[M3U8Stream]:
        """Get lowest quality stream"""
        if not self.streams:
            logger.warning("No streams available to select lowest quality")
            return None

        # Sort by bandwidth and select lowest
        sorted_streams = sorted(self.streams, key=lambda s: s.bandwidth)
        lowest_stream = sorted_streams[0]
        logger.debug(
            f"Selected lowest quality stream: {lowest_stream.resolution}, {lowest_stream.bandwidth} bps")
        return lowest_stream


# ========================================================================
# URL Pattern Utils - URL模式工具
# ========================================================================


def extract_url_pattern(url: str) -> Dict[str, str]:
    """
    Extract pattern from URL for batch download
    Example: https://example.com/video/segment1.ts 
    Returns: {"base_url": "https://example.com/video/segment", "pattern": "{}.ts"}
    """
    try:
        logger.debug(f"Extracting URL pattern from: {url}")
        # Find numeric part
        match = re.search(r'(\d+)(\.[^.]+)?$', url)
        if match:
            # Extract number and extension
            number_part = match.group(1)
            extension = match.group(2) or ""

            # Replace number part with format placeholder
            base_url = url[:match.start(1)]

            pattern_info = {
                "base_url": base_url,
                "pattern": "{}{}".format("", extension)
            }

            logger.debug(
                f"Pattern extracted: {pattern_info['base_url']} + index + {pattern_info['pattern']}")
            return pattern_info

        logger.warning(f"No numeric pattern found in URL: {url}")
        return None

    except Exception as e:
        logger.error(f"Error extracting URL pattern: {e}", exc_info=True)
        return None


# ========================================================================
# Extractors - 提取器函数
# ========================================================================


def extract_m3u8_url_from_page(url: str, headers: Dict[str, str] = None) -> str:
    """Extract M3U8 link from webpage"""
    try:
        logger.debug(f"Attempting to extract M3U8 URL from page: {url}")
        headers = headers or {}
        response = requests.get(url, headers=headers, timeout=30)
        content = response.text
        logger.debug(f"Retrieved page content ({len(content)} bytes)")

        # Search for M3U8 links
        patterns = [
            r'https?://[^"\']+\.m3u8',  # Basic HTTP/HTTPS links
            r'"([^"]+\.m3u8[^"]*)"',    # Links in double quotes
            r'\'([^\']+\.m3u8[^\']*)\''  # Links in single quotes
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content)
            if matches:
                # Return first matching link
                match = matches[0]
                # If tuple (regex capture group), return first element
                if isinstance(match, tuple):
                    match = match[0]
                logger.success(f"Found M3U8 URL in page: {match}")
                return match

        logger.warning("No M3U8 URL found in page content")
        return ""

    except Exception as e:
        logger.error(
            f"Error extracting M3U8 URL from page: {e}", exc_info=True)
        return ""


def extract_m3u8_info(url: str, headers: Dict[str, str] = None) -> Dict[str, Any]:
    """
    Extract M3U8 information from URL

    Args:
        url: M3U8 link or webpage containing M3U8 link
        headers: HTTP request headers

    Returns:
        Dictionary containing parsed information
    """
    result = {
        "success": False,
        "message": "",
        "streams": [],
        "selected_stream": None,
        "key_url": "",
        "segments": 0,
        "duration": 0,
        "encryption": "NONE"
    }

    try:
        logger.info(f"Extracting M3U8 information from URL: {url}")

        # Ensure URL is an M3U8 link
        if not url.endswith('.m3u8') and '.m3u8' not in url:
            # Try to extract M3U8 link from page
            logger.debug(
                f"URL is not a direct M3U8 link, attempting to extract M3U8 URL from page")
            m3u8_url = extract_m3u8_url_from_page(url, headers)
            if not m3u8_url:
                logger.error("Unable to extract M3U8 link from page")
                result["message"] = "Unable to extract M3U8 link from page"
                return result
            logger.success(f"Extracted M3U8 URL: {m3u8_url}")
            url = m3u8_url

        # Parse M3U8
        logger.debug(f"Initializing M3U8 parser for URL: {url}")
        parser = M3U8Parser()
        streams = parser.parse_url(url, headers)

        if not streams:
            logger.error("Unable to parse M3U8 playlist")
            result["message"] = "Unable to parse M3U8 playlist"
            return result

        # Get best quality stream
        selected_stream = parser.get_best_quality_stream()
        logger.debug(
            f"Selected best quality stream from {len(streams)} available streams")

        # Build result
        result["success"] = True
        result["streams"] = [
            {
                "resolution": s.resolution,
                "bandwidth": s.bandwidth,
                "url": s.url,
                "segments": len(s.segments)
            }
            for s in streams
        ]

        if selected_stream:
            result["selected_stream"] = {
                "url": selected_stream.url,
                "resolution": selected_stream.resolution,
                "bandwidth": selected_stream.bandwidth,
                "segments": len(selected_stream.segments),
                "duration": selected_stream.duration
            }

            result["key_url"] = selected_stream.key_url
            result["segments"] = selected_stream.segment_count
            result["duration"] = selected_stream.duration
            result["encryption"] = selected_stream.encryption.value

            logger.success(
                f"Stream analysis complete: {result['segments']} segments, {result['duration']:.2f} seconds, encryption: {result['encryption']}")

            # Process URLs for batch download
            if selected_stream.segments:
                # Try to extract pattern from segment URLs
                first_url = selected_stream.segments[0].url
                logger.debug(
                    f"Analyzing segment URL pattern from: {first_url}")

                # Determine base URL and index pattern
                base_url_pattern = extract_url_pattern(first_url)
                if base_url_pattern:
                    result["base_url"] = base_url_pattern["base_url"]
                    result["pattern"] = base_url_pattern["pattern"]
                    logger.debug(
                        f"URL pattern detected: {result['base_url']} + index + {result['pattern']}")
                else:
                    result["base_url"] = selected_stream.base_url
                    logger.debug(
                        f"No specific URL pattern detected, using base URL: {result['base_url']}")

        return result

    except Exception as e:
        logger.error(f"Error extracting M3U8 information: {e}", exc_info=True)
        result["message"] = f"Error extracting M3U8 information: {str(e)}"
        return result
