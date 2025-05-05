import re
import os
import requests
from typing import List, Dict, Optional, Set
from urllib.parse import urlparse, urljoin
from loguru import logger


class URLExtractor:
    """URL extractor for extracting URLs from various sources"""

    @staticmethod
    def extract_urls_from_text(text: str, pattern: str = None) -> List[str]:
        """
        Extract URLs from text

        Args:
            text: Source text
            pattern: Optional regex pattern, extracts all URLs by default

        Returns:
            List of URLs
        """
        if not text:
            logger.debug("No text provided for URL extraction")
            return []

        if pattern:
            # Use custom pattern
            try:
                logger.debug(
                    f"Extracting URLs using custom pattern: {pattern}")
                urls = re.findall(pattern, text)
                # If returning a list of tuples (regex has multiple capture groups), take the first element
                if urls and isinstance(urls[0], tuple):
                    urls = [url[0] for url in urls]
                logger.debug(
                    f"Extracted {len(urls)} URLs using custom pattern")
                return urls
            except re.error as e:
                logger.error(f"Regular expression error: {e}")
                return []
        else:
            # Default URL pattern
            url_pattern = r'https?://[^\s<>"\']+|www\.[^\s<>"\']+\.[^\s<>"\']+'
            logger.debug(f"Extracting URLs using default pattern")
            urls = re.findall(url_pattern, text)

            # Process URLs starting with www, add http://
            processed_urls = []
            for url in urls:
                if url.startswith("www."):
                    url = "http://" + url
                processed_urls.append(url)

            logger.debug(f"Extracted {len(processed_urls)} URLs from text")
            return processed_urls

    @staticmethod
    def extract_urls_from_file(file_path: str, pattern: str = None) -> List[str]:
        """
        Extract URLs from a file

        Args:
            file_path: Path to the file
            pattern: Optional regex pattern

        Returns:
            List of URLs
        """
        try:
            logger.info(f"Extracting URLs from file: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.debug(f"Read {len(content)} characters from file")
            urls = URLExtractor.extract_urls_from_text(content, pattern)
            logger.info(f"Successfully extracted {len(urls)} URLs from file")
            return urls
        except Exception as e:
            logger.error(
                f"Error extracting URLs from file: {e}", exc_info=True)
            return []

    @staticmethod
    def extract_media_urls_from_webpage(url: str, headers: Dict[str, str] = None,
                                        media_extensions: List[str] = None) -> List[str]:
        """
        Extract media URLs from a webpage

        Args:
            url: Webpage URL
            headers: HTTP request headers
            media_extensions: List of media file extensions

        Returns:
            List of media URLs
        """
        if not media_extensions:
            media_extensions = ['.mp4', '.m3u8', '.ts',
                                '.mp3', '.flv', '.avi', '.mov', '.wmv']

        logger.info(f"Extracting media URLs from webpage: {url}")
        logger.debug(
            f"Looking for media with extensions: {', '.join(media_extensions)}")

        try:
            headers = headers or {}
            if 'User-Agent' not in headers:
                headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                logger.debug("Added default User-Agent header")

            logger.debug(f"Sending HTTP request to: {url}")
            response = requests.get(url, headers=headers, timeout=30)
            content = response.text
            logger.debug(f"Received {len(content)} characters from webpage")

            # Extract all URLs
            all_urls = set()

            # Extract media file links
            for ext in media_extensions:
                pattern = rf'["\'](https?://[^"\']+{ext}[^"\']*)["\']'
                matches = re.findall(pattern, content)
                all_urls.update(matches)
                logger.debug(
                    f"Found {len(matches)} absolute URLs with extension {ext}")

                # Also look for relative paths
                pattern = rf'["\']([^"\']+{ext}[^"\']*)["\']'
                relative_matches = re.findall(pattern, content)
                relative_count = 0
                for match in relative_matches:
                    if not match.startswith(('http://', 'https://')):
                        # Convert to absolute URL
                        absolute_url = urljoin(url, match)
                        all_urls.add(absolute_url)
                        relative_count += 1
                logger.debug(
                    f"Found and converted {relative_count} relative URLs with extension {ext}")

            # Special handling for m3u8 links, which may be in JavaScript code
            pattern = r'["\'](https?://[^"\']+\.m3u8[^"\']*)["\']'
            matches = re.findall(pattern, content)
            all_urls.update(matches)
            logger.debug(f"Found {len(matches)} m3u8 URLs in JavaScript code")

            # Return sorted URL list
            result = sorted(list(all_urls))
            logger.success(
                f"Successfully extracted {len(result)} media URLs from webpage")
            return result

        except Exception as e:
            logger.error(
                f"Error extracting media URLs from webpage: {e}", exc_info=True)
            return []

    @staticmethod
    def filter_urls(urls: List[str], include_pattern: str = None,
                    exclude_pattern: str = None) -> List[str]:
        """
        Filter URLs based on patterns

        Args:
            urls: List of URLs
            include_pattern: Include pattern
            exclude_pattern: Exclude pattern

        Returns:
            Filtered list of URLs
        """
        logger.debug(f"Filtering {len(urls)} URLs")
        if include_pattern:
            logger.debug(f"Using include pattern: {include_pattern}")
        if exclude_pattern:
            logger.debug(f"Using exclude pattern: {exclude_pattern}")

        result = []

        for url in urls:
            # Check exclude pattern
            if exclude_pattern and re.search(exclude_pattern, url):
                continue

            # Check include pattern
            if include_pattern:
                if re.search(include_pattern, url):
                    result.append(url)
            else:
                result.append(url)

        logger.debug(f"Filtered results: {len(result)} URLs remaining")
        return result

    @staticmethod
    def normalize_url(url: str) -> str:
        """
        Normalize URL

        Args:
            url: URL to normalize

        Returns:
            Normalized URL
        """
        logger.debug(f"Normalizing URL: {url}")

        # Ensure URL has protocol
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
            logger.debug(f"Added http:// prefix to URL")

        # Parse URL
        parsed = urlparse(url)

        # Recombine
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if parsed.params:
            normalized += f";{parsed.params}"
        if parsed.query:
            normalized += f"?{parsed.query}"
        if parsed.fragment:
            normalized += f"#{parsed.fragment}"

        logger.debug(f"Normalized URL: {normalized}")
        return normalized

    @staticmethod
    def validate_url(url: str) -> bool:
        """
        Validate if URL is valid

        Args:
            url: URL to validate

        Returns:
            True if URL is valid, False otherwise
        """
        try:
            logger.debug(f"Validating URL: {url}")
            result = urlparse(url)
            valid = all([result.scheme, result.netloc])
            if valid:
                logger.debug(f"URL is valid: {url}")
            else:
                logger.debug(f"URL is invalid: {url}")
            return valid
        except Exception as e:
            logger.error(f"Error validating URL {url}: {e}")
            return False
