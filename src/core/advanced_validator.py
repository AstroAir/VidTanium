"""
Advanced Validation System for VidTanium
Provides content-type detection, bandwidth estimation, and smart defaults
"""

import time
import requests
import threading
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from urllib.parse import urlparse, parse_qs
from loguru import logger
import re


class ContentType(Enum):
    """Content type classifications"""
    M3U8_PLAYLIST = "m3u8_playlist"
    MP4_VIDEO = "mp4_video"
    WEBM_VIDEO = "webm_video"
    AVI_VIDEO = "avi_video"
    MKV_VIDEO = "mkv_video"
    AUDIO_STREAM = "audio_stream"
    LIVE_STREAM = "live_stream"
    UNKNOWN = "unknown"


class QualityLevel(Enum):
    """Video quality levels"""
    LOW = "low"          # 240p-360p
    MEDIUM = "medium"    # 480p-720p
    HIGH = "high"        # 1080p
    ULTRA = "ultra"      # 1440p+


@dataclass
class ContentInfo:
    """Information about content to be downloaded"""
    url: str
    content_type: ContentType
    file_size_mb: Optional[float] = None
    duration_seconds: Optional[int] = None
    quality_level: Optional[QualityLevel] = None
    bitrate_kbps: Optional[int] = None
    resolution: Optional[Tuple[int, int]] = None
    codec: Optional[str] = None
    container_format: Optional[str] = None
    is_live: bool = False
    estimated_segments: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BandwidthEstimate:
    """Bandwidth estimation results"""
    download_speed_mbps: float
    upload_speed_mbps: float
    latency_ms: float
    estimated_download_time_seconds: float
    confidence_level: float  # 0.0 to 1.0
    test_duration_seconds: float
    timestamp: float = field(default_factory=time.time)


@dataclass
class SmartDefaults:
    """Smart default settings based on content analysis"""
    recommended_quality: QualityLevel
    concurrent_connections: int
    retry_attempts: int
    timeout_seconds: int
    buffer_size_mb: int
    use_resume: bool
    estimated_completion_time: str
    storage_requirements_mb: float
    network_requirements_mbps: float


class ContentTypeDetector:
    """Detects content type from URLs and headers"""
    
    def __init__(self) -> None:
        self.url_patterns = {
            ContentType.M3U8_PLAYLIST: [
                r'\.m3u8(\?.*)?$',
                r'/playlist\.m3u8',
                r'/index\.m3u8',
                r'master\.m3u8'
            ],
            ContentType.MP4_VIDEO: [
                r'\.mp4(\?.*)?$',
                r'\.m4v(\?.*)?$'
            ],
            ContentType.WEBM_VIDEO: [
                r'\.webm(\?.*)?$'
            ],
            ContentType.AVI_VIDEO: [
                r'\.avi(\?.*)?$'
            ],
            ContentType.MKV_VIDEO: [
                r'\.mkv(\?.*)?$'
            ],
            ContentType.AUDIO_STREAM: [
                r'\.mp3(\?.*)?$',
                r'\.aac(\?.*)?$',
                r'\.m4a(\?.*)?$',
                r'\.flac(\?.*)?$'
            ]
        }
        
        self.content_type_headers = {
            'application/vnd.apple.mpegurl': ContentType.M3U8_PLAYLIST,
            'application/x-mpegURL': ContentType.M3U8_PLAYLIST,
            'video/mp4': ContentType.MP4_VIDEO,
            'video/webm': ContentType.WEBM_VIDEO,
            'video/x-msvideo': ContentType.AVI_VIDEO,
            'video/x-matroska': ContentType.MKV_VIDEO,
            'audio/mpeg': ContentType.AUDIO_STREAM,
            'audio/mp4': ContentType.AUDIO_STREAM
        }
    
    def detect_content_type(self, url: str, headers: Optional[Dict[str, str]] = None) -> ContentType:
        """Detect content type from URL and headers"""
        # First try headers if available
        if headers:
            content_type_header = headers.get('content-type', '').lower()
            for header_type, content_type in self.content_type_headers.items():
                if header_type in content_type_header:
                    return content_type
        
        # Then try URL patterns
        url_lower = url.lower()
        for content_type, patterns in self.url_patterns.items():
            for pattern in patterns:
                if re.search(pattern, url_lower):
                    return content_type
        
        # Check for live stream indicators
        if self._is_live_stream_url(url):
            return ContentType.LIVE_STREAM
        
        return ContentType.UNKNOWN
    
    def _is_live_stream_url(self, url: str) -> bool:
        """Check if URL indicates a live stream"""
        live_indicators = [
            'live', 'stream', 'broadcast', 'tv', 'radio',
            'rtmp://', 'rtsp://', 'hls://'
        ]
        url_lower = url.lower()
        return any(indicator in url_lower for indicator in live_indicators)


class BandwidthEstimator:
    """Estimates network bandwidth and performance"""
    
    def __init__(self) -> None:
        self.test_urls = [
            "https://httpbin.org/bytes/1048576",  # 1MB test file
            "https://httpbin.org/bytes/5242880",  # 5MB test file
        ]
        self.cache: Dict[str, BandwidthEstimate] = {}
        self.cache_duration = 300  # 5 minutes
    
    def estimate_bandwidth(self, test_duration_seconds: float = 10.0) -> BandwidthEstimate:
        """Estimate current bandwidth"""
        # Check cache first
        cache_key = f"bandwidth_{int(time.time() // self.cache_duration)}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            # Perform bandwidth test
            start_time = time.time()
            total_bytes = 0
            successful_tests = 0
            latencies = []
            
            for test_url in self.test_urls:
                if time.time() - start_time > test_duration_seconds:
                    break
                
                try:
                    # Measure latency
                    ping_start = time.time()
                    response = requests.head(test_url, timeout=5)
                    latency = (time.time() - ping_start) * 1000  # Convert to ms
                    latencies.append(latency)
                    
                    # Measure download speed
                    download_start = time.time()
                    response = requests.get(test_url, timeout=10, stream=True)
                    
                    chunk_size = 8192
                    bytes_downloaded = 0
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        bytes_downloaded += len(chunk)
                        if time.time() - download_start > 5:  # Max 5 seconds per test
                            break
                    
                    download_time = time.time() - download_start
                    if download_time > 0:
                        total_bytes += bytes_downloaded
                        successful_tests += 1
                
                except Exception as e:
                    logger.warning(f"Bandwidth test failed for {test_url}: {e}")
                    continue
            
            # Calculate results
            total_time = time.time() - start_time
            if total_bytes > 0 and total_time > 0:
                download_speed_mbps = (total_bytes * 8) / (total_time * 1_000_000)  # Convert to Mbps
                avg_latency = sum(latencies) / len(latencies) if latencies else 100
                confidence = min(successful_tests / len(self.test_urls), 1.0)
                
                estimate = BandwidthEstimate(
                    download_speed_mbps=download_speed_mbps,
                    upload_speed_mbps=download_speed_mbps * 0.1,  # Estimate upload as 10% of download
                    latency_ms=avg_latency,
                    estimated_download_time_seconds=0,  # Will be calculated per content
                    confidence_level=confidence,
                    test_duration_seconds=total_time
                )
                
                # Cache the result
                self.cache[cache_key] = estimate
                return estimate
        
        except Exception as e:
            logger.error(f"Bandwidth estimation failed: {e}")
        
        # Return conservative estimate if test fails
        return BandwidthEstimate(
            download_speed_mbps=5.0,  # Conservative 5 Mbps
            upload_speed_mbps=1.0,
            latency_ms=100,
            estimated_download_time_seconds=0,
            confidence_level=0.3,
            test_duration_seconds=0
        )


class ContentAnalyzer:
    """Analyzes content to extract metadata and information"""
    
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'VidTanium/1.0'})
    
    def analyze_content(self, url: str) -> ContentInfo:
        """Analyze content and extract information"""
        try:
            # Get basic info with HEAD request
            response = self.session.head(url, timeout=10, allow_redirects=True)
            headers = dict(response.headers)
            
            # Detect content type
            detector = ContentTypeDetector()
            content_type = detector.detect_content_type(url, headers)
            
            # Create base content info
            content_info = ContentInfo(
                url=url,
                content_type=content_type
            )
            
            # Extract file size
            content_length = headers.get('content-length')
            if content_length:
                content_info.file_size_mb = int(content_length) / (1024 * 1024)
            
            # Analyze based on content type
            if content_type == ContentType.M3U8_PLAYLIST:
                self._analyze_m3u8_playlist(content_info)
            elif content_type in [ContentType.MP4_VIDEO, ContentType.WEBM_VIDEO, ContentType.AVI_VIDEO, ContentType.MKV_VIDEO]:
                self._analyze_video_file(content_info, headers)
            
            return content_info
            
        except Exception as e:
            logger.error(f"Content analysis failed for {url}: {e}")
            return ContentInfo(url=url, content_type=ContentType.UNKNOWN)
    
    def _analyze_m3u8_playlist(self, content_info: ContentInfo) -> None:
        """Analyze M3U8 playlist content"""
        try:
            response = self.session.get(content_info.url, timeout=10)
            playlist_content = response.text
            
            # Parse M3U8 content
            lines = playlist_content.strip().split('\n')
            
            # Check if it's a live stream
            content_info.is_live = '#EXT-X-PLAYLIST-TYPE:VOD' not in playlist_content
            
            # Count segments
            segment_count = playlist_content.count('#EXTINF:')
            content_info.estimated_segments = segment_count
            
            # Extract duration for VOD
            if not content_info.is_live:
                duration_matches = re.findall(r'#EXTINF:([\d.]+)', playlist_content)
                if duration_matches:
                    total_duration = sum(float(d) for d in duration_matches)
                    content_info.duration_seconds = int(total_duration)
            
            # Extract quality information from variant playlists
            bandwidth_matches = re.findall(r'BANDWIDTH=(\d+)', playlist_content)
            if bandwidth_matches:
                max_bandwidth = max(int(b) for b in bandwidth_matches)
                content_info.bitrate_kbps = max_bandwidth // 1000
                
                # Estimate quality level based on bandwidth
                if max_bandwidth < 1_000_000:  # < 1 Mbps
                    content_info.quality_level = QualityLevel.LOW
                elif max_bandwidth < 5_000_000:  # < 5 Mbps
                    content_info.quality_level = QualityLevel.MEDIUM
                elif max_bandwidth < 10_000_000:  # < 10 Mbps
                    content_info.quality_level = QualityLevel.HIGH
                else:
                    content_info.quality_level = QualityLevel.ULTRA
            
            # Extract resolution
            resolution_matches = re.findall(r'RESOLUTION=(\d+)x(\d+)', playlist_content)
            if resolution_matches:
                max_resolution = max(resolution_matches, key=lambda x: int(x[0]) * int(x[1]))
                content_info.resolution = (int(max_resolution[0]), int(max_resolution[1]))
            
        except Exception as e:
            logger.error(f"M3U8 analysis failed: {e}")
    
    def _analyze_video_file(self, content_info: ContentInfo, headers: Dict[str, str]) -> None:
        """Analyze video file content"""
        # Extract container format from content type or URL
        content_type_header = headers.get('content-type', '').lower()
        if 'mp4' in content_type_header:
            content_info.container_format = 'mp4'
        elif 'webm' in content_type_header:
            content_info.container_format = 'webm'
        elif 'avi' in content_type_header:
            content_info.container_format = 'avi'
        elif 'matroska' in content_type_header:
            content_info.container_format = 'mkv'
        
        # Estimate quality based on file size (rough estimation)
        if content_info.file_size_mb:
            if content_info.file_size_mb < 100:
                content_info.quality_level = QualityLevel.LOW
            elif content_info.file_size_mb < 500:
                content_info.quality_level = QualityLevel.MEDIUM
            elif content_info.file_size_mb < 2000:
                content_info.quality_level = QualityLevel.HIGH
            else:
                content_info.quality_level = QualityLevel.ULTRA


class SmartDefaultsGenerator:
    """Generates smart default settings based on content analysis"""
    
    def __init__(self) -> None:
        self.bandwidth_estimator = BandwidthEstimator()
    
    def generate_defaults(self, content_info: ContentInfo) -> SmartDefaults:
        """Generate smart defaults based on content analysis"""
        # Get bandwidth estimate
        bandwidth = self.bandwidth_estimator.estimate_bandwidth()
        
        # Base defaults
        defaults = SmartDefaults(
            recommended_quality=content_info.quality_level or QualityLevel.MEDIUM,
            concurrent_connections=4,
            retry_attempts=3,
            timeout_seconds=30,
            buffer_size_mb=10,
            use_resume=True,
            estimated_completion_time="Unknown",
            storage_requirements_mb=content_info.file_size_mb or 100,
            network_requirements_mbps=1.0
        )
        
        # Adjust based on content type
        if content_info.content_type == ContentType.M3U8_PLAYLIST:
            defaults.concurrent_connections = min(8, max(2, int(bandwidth.download_speed_mbps)))
            defaults.retry_attempts = 5  # More retries for segmented content
            
            if content_info.is_live:
                defaults.buffer_size_mb = 5  # Smaller buffer for live streams
                defaults.use_resume = False  # Can't resume live streams
                defaults.estimated_completion_time = "Continuous (Live Stream)"
            else:
                # Estimate completion time for VOD
                if content_info.duration_seconds and bandwidth.download_speed_mbps > 0:
                    # Rough estimation: assume 1 Mbps per hour of content
                    estimated_size_mb = (content_info.duration_seconds / 3600) * 125  # 1 Mbps = 125 MB/hour
                    download_time_seconds = (estimated_size_mb * 8) / bandwidth.download_speed_mbps
                    defaults.estimated_completion_time = self._format_duration(download_time_seconds)
                    defaults.storage_requirements_mb = estimated_size_mb
        
        elif content_info.content_type in [ContentType.MP4_VIDEO, ContentType.WEBM_VIDEO, ContentType.AVI_VIDEO, ContentType.MKV_VIDEO]:
            defaults.concurrent_connections = 2  # Fewer connections for single files
            defaults.buffer_size_mb = 20  # Larger buffer for single files
            
            if content_info.file_size_mb and bandwidth.download_speed_mbps > 0:
                download_time_seconds = (content_info.file_size_mb * 8) / bandwidth.download_speed_mbps
                defaults.estimated_completion_time = self._format_duration(download_time_seconds)
        
        # Adjust based on bandwidth
        if bandwidth.download_speed_mbps < 2:
            defaults.concurrent_connections = max(1, defaults.concurrent_connections // 2)
            defaults.timeout_seconds = 60  # Longer timeout for slow connections
        elif bandwidth.download_speed_mbps > 10:
            defaults.concurrent_connections = min(16, defaults.concurrent_connections * 2)
        
        # Set network requirements
        if content_info.bitrate_kbps:
            defaults.network_requirements_mbps = content_info.bitrate_kbps / 1000 * 1.2  # 20% overhead
        
        return defaults
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format"""
        if seconds < 60:
            return f"{seconds:.0f} seconds"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f} minutes"
        else:
            hours = seconds / 3600
            return f"{hours:.1f} hours"


class AdvancedValidator:
    """Main advanced validation system"""
    
    def __init__(self) -> None:
        self.content_analyzer = ContentAnalyzer()
        self.defaults_generator = SmartDefaultsGenerator()
        logger.info("Advanced validator initialized")
    
    def validate_and_analyze(self, url: str) -> Tuple[ContentInfo, SmartDefaults]:
        """Perform comprehensive validation and analysis"""
        # Analyze content
        content_info = self.content_analyzer.analyze_content(url)
        
        # Generate smart defaults
        smart_defaults = self.defaults_generator.generate_defaults(content_info)
        
        logger.info(f"Advanced validation completed for {url}: {content_info.content_type.value}")
        return content_info, smart_defaults


# Global advanced validator instance
advanced_validator = AdvancedValidator()
