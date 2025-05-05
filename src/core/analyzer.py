# src/core/analyzer.py
import re
import requests
from urllib.parse import urljoin
from loguru import logger
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional


class EncryptionType(Enum):
    NONE = "none"
    AES_128 = "aes-128"
    SAMPLE_AES = "sample-aes"
    CUSTOM = "custom"


@dataclass
class StreamInfo:
    resolution: str
    bandwidth: int
    url: str
    codec: Optional[str] = None


@dataclass
class M3U8Info:
    url: str
    variants: List[StreamInfo]
    segments: List[str]
    total_duration: float
    encryption: EncryptionType
    key_url: Optional[str] = None
    iv: Optional[str] = None
    encryption_details: Optional[Dict] = None


class MediaAnalyzer:
    """Media Analyzer for intelligent media processing"""

    def __init__(self, settings=None):
        self.settings = settings or {}
        self.user_agent = self.settings.get("user_agent",
                                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        self.timeout = self.settings.get("timeout", 30)
        self.verify_ssl = self.settings.get("verify_ssl", True)
        self.proxy = self.settings.get("proxy", None)
        logger.debug(
            f"MediaAnalyzer initialized with timeout={self.timeout}, verify_ssl={self.verify_ssl}")

    def analyze_url(self, url: str) -> Dict:
        """
        Analyze URL and return media information

        Args:
            url (str): URL to analyze

        Returns:
            Dict: Media information or error details
        """
        try:
            logger.info(f"Analyzing URL: {url}")
            # First try to determine URL type
            if self._is_direct_m3u8(url):
                logger.debug(f"URL appears to be a direct M3U8 link")
                return self.analyze_m3u8(url)
            else:
                # Try to extract media URLs from page
                logger.debug(f"Attempting to extract media URLs from web page")
                extracted_urls = self.extract_media_from_page(url)
                if not extracted_urls:
                    logger.warning(
                        f"No media URLs could be extracted from page: {url}")
                    return {"success": False, "error": "Unable to extract media URLs from page"}

                # Analyze first found M3U8
                logger.debug(
                    f"Found {len(extracted_urls)} potential media URLs")
                for media_url in extracted_urls:
                    if media_url.endswith(".m3u8"):
                        logger.info(f"Processing M3U8: {media_url}")
                        return self.analyze_m3u8(media_url)

                logger.error(f"No M3U8 streams found among extracted URLs")
                return {"success": False, "error": "No M3U8 streams found"}
        except Exception as e:
            logger.error(f"Error analyzing URL: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def analyze_m3u8(self, url: str) -> Dict:
        """
        Analyze M3U8 file content

        Args:
            url (str): M3U8 URL to analyze

        Returns:
            Dict: Analysis results or error details
        """
        try:
            logger.info(f"Analyzing M3U8 file: {url}")
            content = self._fetch_content(url)
            if not content:
                logger.error(f"Failed to download M3U8 content from {url}")
                return {"success": False, "error": "Unable to download M3U8 content"}

            # Parse M3U8 content
            if "#EXTM3U" not in content:
                logger.error(f"Invalid M3U8 format, missing #EXTM3U tag")
                return {"success": False, "error": "Invalid M3U8 format"}

            # Check if this is a master playlist (contains multiple stream variants)
            if "#EXT-X-STREAM-INF" in content:
                logger.debug(f"Detected master playlist with variants")
                return self._parse_master_playlist(content, url)
            else:
                logger.debug(f"Detected media playlist with segments")
                return self._parse_media_playlist(content, url)
        except Exception as e:
            logger.error(f"Error analyzing M3U8: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def extract_media_from_page(self, url: str) -> List[str]:
        """
        Extract media URLs from web page

        Args:
            url (str): Web page URL

        Returns:
            List[str]: List of extracted media URLs
        """
        logger.info(f"Extracting media URLs from page: {url}")
        content = self._fetch_content(url)
        if not content:
            logger.warning(f"Failed to fetch page content from {url}")
            return []

        # Extract all possible media URLs
        # 1. Look for .m3u8 links
        logger.debug("Searching for direct M3U8 links in page")
        m3u8_urls = re.findall(r'https?://[^"\']+\.m3u8', content)
        logger.debug(f"Found {len(m3u8_urls)} direct M3U8 links")

        # 2. Look for JSON data that might contain media information
        json_urls = []
        logger.debug("Searching for M3U8 links in JSON data")
        json_data_matches = re.findall(r'({[^}]+\.m3u8[^}]+})', content)
        for json_str in json_data_matches:
            try:
                # Extract URLs from JSON-style strings
                media_urls = re.findall(r'https?://[^"\']+\.m3u8', json_str)
                json_urls.extend(media_urls)
            except Exception as e:
                logger.debug(f"Error parsing JSON data: {e}")
                pass

        logger.debug(f"Found {len(json_urls)} M3U8 links in JSON data")

        # 3. Look for possible API calls
        logger.debug("Searching for potential API endpoints")
        api_urls = re.findall(r'https?://[^"\']+/api/[^"\']+', content)
        logger.debug(f"Found {len(api_urls)} potential API endpoints")

        # Combine all discovered URLs
        all_urls = list(set(m3u8_urls + json_urls))

        # If no media URLs were found directly, try accessing API endpoints
        if not all_urls and api_urls:
            logger.info("No direct media URLs found, trying API endpoints")
            for api_url in api_urls:
                try:
                    logger.debug(
                        f"Fetching content from API endpoint: {api_url}")
                    api_response = self._fetch_content(api_url)
                    if api_response:
                        media_urls = re.findall(
                            r'https?://[^"\']+\.m3u8', api_response)
                        logger.debug(
                            f"Found {len(media_urls)} M3U8 links from API endpoint")
                        all_urls.extend(media_urls)
                except Exception as e:
                    logger.debug(f"Error fetching API endpoint {api_url}: {e}")
                    pass

        unique_urls = list(set(all_urls))  # Remove duplicates
        logger.success(
            f"Extracted {len(unique_urls)} unique media URLs from page")
        return unique_urls

    def _is_direct_m3u8(self, url: str) -> bool:
        """
        Check if URL is a direct M3U8 link

        Args:
            url (str): URL to check

        Returns:
            bool: True if URL is likely a direct M3U8 link
        """
        # Simple check based on extension
        is_m3u8 = url.lower().endswith('.m3u8')
        logger.debug(f"URL {url} is direct M3U8: {is_m3u8}")
        return is_m3u8

    def _fetch_content(self, url: str) -> str:
        """
        Fetch content from URL

        Args:
            url (str): URL to fetch

        Returns:
            str: Content as string or empty string on failure
        """
        logger.debug(f"Fetching content from: {url}")
        headers = {"User-Agent": self.user_agent}
        proxies = {"http": self.proxy,
                   "https": self.proxy} if self.proxy else None

        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=self.timeout,
                verify=self.verify_ssl,
                proxies=proxies
            )

            if response.status_code == 200:
                logger.debug(
                    f"Successfully fetched content ({len(response.text)} bytes)")
                return response.text
            else:
                logger.warning(
                    f"Failed to fetch content: HTTP {response.status_code}")
                return ""

        except Exception as e:
            logger.error(f"Error fetching content: {e}", exc_info=True)
            return ""

    def _parse_master_playlist(self, content: str, base_url: str) -> Dict:
        """
        Parse master playlist (contains multiple stream variants)

        Args:
            content (str): M3U8 content
            base_url (str): Base URL for resolving relative paths

        Returns:
            Dict: Parsed master playlist information
        """
        logger.info("Parsing master playlist")
        variants = []
        lines = content.splitlines()

        for i, line in enumerate(lines):
            if line.startswith('#EXT-X-STREAM-INF:'):
                # Parse stream information
                resolution = re.search(r'RESOLUTION=(\d+x\d+)', line)
                bandwidth = re.search(r'BANDWIDTH=(\d+)', line)
                codec = re.search(r'CODECS="([^"]+)"', line)

                if i+1 < len(lines) and not lines[i+1].startswith('#'):
                    # Next line should contain the variant URL
                    variant_url = lines[i+1]
                    # Resolve relative URL
                    if not variant_url.startswith('http'):
                        variant_url = urljoin(base_url, variant_url)

                    variant = StreamInfo(
                        resolution=resolution.group(
                            1) if resolution else "unknown",
                        bandwidth=int(bandwidth.group(1)) if bandwidth else 0,
                        url=variant_url,
                        codec=codec.group(1) if codec else None
                    )
                    variants.append(variant)
                    logger.debug(
                        f"Found variant: resolution={variant.resolution}, bandwidth={variant.bandwidth}")

        # Return the list of variants
        if variants:
            logger.success(
                f"Successfully parsed master playlist with {len(variants)} variants")
            return {
                "success": True,
                "type": "master",
                "variants": [vars(v) for v in variants],
                "base_url": base_url
            }
        else:
            logger.error("No stream variants found in master playlist")
            return {"success": False, "error": "No stream variants found"}

    def _parse_media_playlist(self, content: str, base_url: str) -> Dict:
        """
        Parse media playlist (contains segments)

        Args:
            content (str): M3U8 content
            base_url (str): Base URL for resolving relative paths

        Returns:
            Dict: Parsed media playlist information
        """
        logger.info("Parsing media playlist")
        segments = []
        duration = 0.0
        encryption = EncryptionType.NONE
        key_url = None
        iv = None
        encryption_details = {}

        lines = content.splitlines()

        for i, line in enumerate(lines):
            if line.startswith('#EXTINF:'):
                # Parse segment duration
                segment_duration = float(
                    re.search(r'#EXTINF:([0-9.]+)', line).group(1))
                duration += segment_duration

                if i+1 < len(lines) and not lines[i+1].startswith('#'):
                    # Next line should contain the segment URL
                    segment_url = lines[i+1]
                    # Resolve relative URL
                    if not segment_url.startswith('http'):
                        segment_url = urljoin(base_url, segment_url)
                    segments.append(segment_url)

            elif line.startswith('#EXT-X-KEY:'):
                # Parse encryption information
                method_match = re.search(r'METHOD=(\w+)', line)
                if method_match:
                    method = method_match.group(1)
                    if method == "AES-128":
                        encryption = EncryptionType.AES_128
                    elif method == "SAMPLE-AES":
                        encryption = EncryptionType.SAMPLE_AES
                    else:
                        encryption = EncryptionType.CUSTOM

                    encryption_details["method"] = method

                uri_match = re.search(r'URI="([^"]+)"', line)
                if uri_match:
                    key_url = uri_match.group(1)
                    # Resolve relative URL
                    if not key_url.startswith('http'):
                        key_url = urljoin(base_url, key_url)
                    encryption_details["key_url"] = key_url

                iv_match = re.search(r'IV=0x([0-9a-fA-F]+)', line)
                if iv_match:
                    iv = iv_match.group(1)
                    encryption_details["iv"] = iv

        # Return the parsed information
        if segments:
            logger.success(
                f"Successfully parsed media playlist with {len(segments)} segments")
            result = {
                "success": True,
                "type": "media",
                "segments": segments,
                "segment_count": len(segments),
                "total_duration": round(duration, 2),
                "encryption": encryption.value,
                "base_url": base_url
            }

            if encryption != EncryptionType.NONE:
                logger.info(f"Media is encrypted using {encryption.value}")
                result["encryption_details"] = encryption_details
                if key_url:
                    result["key_url"] = key_url
                if iv:
                    result["iv"] = iv

            return result
        else:
            logger.error("No segments found in media playlist")
            return {"success": False, "error": "No segments found"}
