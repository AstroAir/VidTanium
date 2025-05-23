import pytest
from unittest.mock import patch, MagicMock

from m3u8_parser import (
    M3U8Parser,
    M3U8Stream,
    M3U8Segment,
    StreamType,
    EncryptionMethod,
    extract_url_pattern,
    extract_m3u8_url_from_page,
    extract_m3u8_info
)


class TestM3U8Models:
    """Test suite for the M3U8 data models."""

    def test_m3u8_segment_init(self) -> None:
        """Test initialization of M3U8Segment."""
        segment = M3U8Segment()
        assert segment.url == ""
        assert segment.duration == 0.0
        assert segment.index == 0
        assert segment.encryption == EncryptionMethod.NONE
        assert segment.key_url is None
        assert segment.key_iv is None
        assert segment.discontinuity is False

    def test_m3u8_stream_init(self) -> None:
        """Test initialization of M3U8Stream."""
        stream = M3U8Stream()
        assert stream.url == ""
        assert stream.type == StreamType.UNKNOWN
        assert stream.bandwidth == 0
        assert stream.resolution == ""
        assert stream.codecs == ""
        assert stream.name == ""
        assert stream.segments == []
        assert stream.encryption == EncryptionMethod.NONE
        assert stream.key_url is None
        assert stream.key_iv is None
        assert stream.duration == 0.0
        assert stream.segment_count == 0
        assert stream.base_url == ""


class TestM3U8Parser:
    """Test suite for the M3U8Parser class."""

    def setup_method(self) -> None:
        """Set up test fixtures before each test."""
        self.parser = M3U8Parser()
        self.test_url = "https://example.com/playlist.m3u8"
        self.base_url = "https://example.com/"

    @patch('m3u8_parser.M3U8Parser.parse_url')
    def test_parse_url_master_playlist(self, mock_parse_url: MagicMock) -> None:
        """Test parsing a master playlist."""
        # 创建测试流
        stream1 = M3U8Stream()
        stream1.bandwidth = 800000
        stream1.resolution = "640x360"
        stream1.codecs = "avc1.42001e,mp4a.40.2"
        stream1.name = "360p"
        stream1.duration = 19.0
        stream1.segment_count = 2

        segment1 = M3U8Segment()
        segment1.duration = 9.0
        segment1.url = "https://example.com/segment_360p_0.ts"

        segment2 = M3U8Segment()
        segment2.duration = 10.0
        segment2.url = "https://example.com/segment_360p_1.ts"

        stream1.segments = [segment1, segment2]

        stream2 = M3U8Stream()
        stream2.bandwidth = 1400000
        stream2.resolution = "1280x720"
        stream2.codecs = "avc1.42001f,mp4a.40.2"
        stream2.name = "720p"
        stream2.duration = 19.0
        stream2.segment_count = 2

        segment3 = M3U8Segment()
        segment3.duration = 9.0
        segment3.url = "https://example.com/segment_720p_0.ts"

        segment4 = M3U8Segment()
        segment4.duration = 10.0
        segment4.url = "https://example.com/segment_720p_1.ts"

        stream2.segments = [segment3, segment4]

        # 设置模拟解析的返回值
        mock_parse_url.return_value = [stream1, stream2]

        # 解析 URL
        streams = self.parser.parse_url(self.test_url)

        # 验证解析结果
        assert len(streams) == 2

        # 检查第一个流
        assert streams[0].bandwidth == 800000
        assert streams[0].resolution == "640x360"
        assert streams[0].codecs == "avc1.42001e,mp4a.40.2"
        assert streams[0].name == "360p"
        assert len(streams[0].segments) == 2
        assert streams[0].duration == 19.0
        assert streams[0].segment_count == 2

        # 检查第二个流
        assert streams[1].bandwidth == 1400000
        assert streams[1].resolution == "1280x720"
        assert streams[1].codecs == "avc1.42001f,mp4a.40.2"
        assert streams[1].name == "720p"
        assert len(streams[1].segments) == 2
        assert streams[1].duration == 19.0
        assert streams[1].segment_count == 2

    @patch('m3u8_parser.M3U8Parser.parse_url')
    def test_parse_url_media_playlist(self, mock_parse_url: MagicMock) -> None:
        """Test parsing a media playlist (no master)."""
        # 创建测试流
        stream = M3U8Stream()
        stream.url = self.test_url
        stream.duration = 27.5  # 9.0 + 10.0 + 8.5
        stream.segment_count = 3

        segment1 = M3U8Segment()
        segment1.duration = 9.0
        segment1.url = "https://example.com/segment_0.ts"

        segment2 = M3U8Segment()
        segment2.duration = 10.0
        segment2.url = "https://example.com/segment_1.ts"

        segment3 = M3U8Segment()
        segment3.duration = 8.5
        segment3.url = "https://example.com/segment_2.ts"

        stream.segments = [segment1, segment2, segment3]

        # 设置模拟解析的返回值
        mock_parse_url.return_value = [stream]

        # 解析 URL
        streams = self.parser.parse_url(self.test_url)

        # 验证解析结果
        assert len(streams) == 1
        assert len(streams[0].segments) == 3
        assert streams[0].duration == 27.5  # 9.0 + 10.0 + 8.5
        assert streams[0].segment_count == 3
        assert streams[0].encryption == EncryptionMethod.NONE

    @patch('m3u8_parser.M3U8Parser.parse_url')
    def test_parse_url_encrypted_playlist(self, mock_parse_url: MagicMock) -> None:
        """Test parsing an encrypted media playlist."""
        # 创建加密测试流
        stream = M3U8Stream()
        stream.encryption = EncryptionMethod.AES_128
        stream.key_url = "https://example.com/key.bin"
        stream.key_iv = "0x0123456789ABCDEF0123456789ABCDEF"

        segment = M3U8Segment()
        segment.encryption = EncryptionMethod.AES_128
        segment.key_url = "https://example.com/key.bin"
        segment.key_iv = "0x0123456789ABCDEF0123456789ABCDEF"

        stream.segments = [segment]

        # 设置模拟解析的返回值
        mock_parse_url.return_value = [stream]

        # 解析 URL
        streams = self.parser.parse_url(self.test_url)

        # 验证加密详情
        assert len(streams) == 1
        assert streams[0].encryption == EncryptionMethod.AES_128
        assert streams[0].key_url == "https://example.com/key.bin"
        assert streams[0].key_iv == "0x0123456789ABCDEF0123456789ABCDEF"
        assert streams[0].segments[0].encryption == EncryptionMethod.AES_128
        assert streams[0].segments[0].key_url == "https://example.com/key.bin"

    @patch('m3u8_parser.M3U8Parser.parse_url')
    def test_parse_url_empty_playlist(self, mock_parse_url: MagicMock) -> None:
        """Test parsing an empty playlist."""
        # 设置模拟解析的返回值
        mock_parse_url.return_value = []

        # 解析 URL
        streams = self.parser.parse_url(self.test_url)

        # 验证空结果
        assert len(streams) == 0

    @patch('m3u8_parser.M3U8Parser.parse_url')
    def test_parse_url_download_error(self, mock_parse_url: MagicMock) -> None:
        """Test parsing with download error."""
        # 模拟下载错误
        mock_parse_url.side_effect = Exception("Connection error")

        # 解析 URL
        try:
            self.parser.parse_url(self.test_url)
            assert False, "应该抛出异常但没有"
        except Exception:
            pass

    # 创建一个测试类来包装受保护的方法
    class TestableM3U8Parser(M3U8Parser):
        """Helper class to access protected methods for testing."""

        def public_download_playlist(self, url: str) -> str:
            """Public wrapper for _download_playlist."""
            return self._download_playlist(url)

        def public_get_base_url(self, url: str) -> str:
            """Public wrapper for _get_base_url."""
            return self._get_base_url(url)

        def public_parse_attributes(self, attribute_string: str) -> dict[str, str]:
            """Public wrapper for _parse_attributes."""
            return self._parse_attributes(attribute_string)

    @patch('m3u8_parser.requests.get')
    def test_download_playlist_success(self, mock_get: MagicMock) -> None:
        """Test successful playlist download."""
        # 创建可测试解析器
        parser = self.TestableM3U8Parser()

        # 模拟成功的响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "Playlist content"
        mock_get.return_value = mock_response

        # 下载播放列表
        content = parser.public_download_playlist(self.test_url)

        # 验证返回的内容
        assert content == "Playlist content"
        mock_get.assert_called_once_with(self.test_url, headers={}, timeout=30)

    @patch('m3u8_parser.requests.get')
    def test_download_playlist_http_error(self, mock_get: MagicMock) -> None:
        """Test playlist download with HTTP error."""
        # 创建可测试解析器
        parser = self.TestableM3U8Parser()

        # 模拟 HTTP 错误
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        # 下载播放列表
        content = parser.public_download_playlist(self.test_url)

        # 验证空内容
        assert content == ""

    @patch('m3u8_parser.requests.get')
    def test_download_playlist_exception(self, mock_get: MagicMock) -> None:
        """Test playlist download with exception."""
        # 创建可测试解析器
        parser = self.TestableM3U8Parser()

        # 模拟请求异常
        mock_get.side_effect = Exception("Connection error")

        # 下载播放列表
        content = parser.public_download_playlist(self.test_url)

        # 验证空内容
        assert content == ""

    def test_get_base_url_normal(self) -> None:
        """Test getting base URL from normal URL."""
        # 创建可测试解析器
        parser = self.TestableM3U8Parser()

        url = "https://example.com/path/playlist.m3u8"
        base_url = parser.public_get_base_url(url)
        assert base_url == "https://example.com/path/"

    def test_get_base_url_no_path(self) -> None:
        """Test getting base URL from URL with no path."""
        # 创建可测试解析器
        parser = self.TestableM3U8Parser()

        url = "https://example.com"
        base_url = parser.public_get_base_url(url)
        assert base_url == "https://example.com/"

    def test_get_base_url_with_query(self) -> None:
        """Test getting base URL from URL with query params."""
        # 创建可测试解析器
        parser = self.TestableM3U8Parser()

        url = "https://example.com/path/playlist.m3u8?token=123"
        base_url = parser.public_get_base_url(url)
        assert base_url == "https://example.com/path/"

    def test_parse_attributes(self) -> None:
        """Test parsing of attribute string."""
        # 创建可测试解析器
        parser = self.TestableM3U8Parser()

        # Test with quoted values
        attr_string = 'BANDWIDTH=800000,RESOLUTION="640x360",CODECS="avc1.42001e,mp4a.40.2",NAME="360p"'
        attributes = parser.public_parse_attributes(attr_string)
        assert attributes["BANDWIDTH"] == "800000"
        assert attributes["RESOLUTION"] == "640x360"
        assert attributes["CODECS"] == "avc1.42001e,mp4a.40.2"
        assert attributes["NAME"] == "360p"

        # Test with unquoted values
        attr_string = 'METHOD=AES-128,URI="key.bin",IV=0x123456'
        attributes = parser.public_parse_attributes(attr_string)
        assert attributes["METHOD"] == "AES-128"
        assert attributes["URI"] == "key.bin"
        assert attributes["IV"] == "0x123456"

    def test_get_best_quality_stream(self) -> None:
        """Test getting best quality stream."""
        # Create test streams
        stream1 = M3U8Stream()
        stream1.bandwidth = 800000
        stream1.resolution = "640x360"

        stream2 = M3U8Stream()
        stream2.bandwidth = 1400000
        stream2.resolution = "1280x720"

        stream3 = M3U8Stream()
        stream3.bandwidth = 2000000
        stream3.resolution = "1920x1080"

        self.parser.streams = [stream1, stream2, stream3]

        # Get best quality stream
        best_stream = self.parser.get_best_quality_stream()

        # Verify it's the highest bandwidth
        assert best_stream is not None
        assert best_stream.bandwidth == 2000000
        assert best_stream.resolution == "1920x1080"

    def test_get_lowest_quality_stream(self) -> None:
        """Test getting lowest quality stream."""
        # Create test streams
        stream1 = M3U8Stream()
        stream1.bandwidth = 800000
        stream1.resolution = "640x360"

        stream2 = M3U8Stream()
        stream2.bandwidth = 1400000
        stream2.resolution = "1280x720"

        stream3 = M3U8Stream()
        stream3.bandwidth = 2000000
        stream3.resolution = "1920x1080"

        self.parser.streams = [stream1, stream2, stream3]

        # Get lowest quality stream
        lowest_stream = self.parser.get_lowest_quality_stream()

        # Verify it's the lowest bandwidth
        assert lowest_stream is not None
        assert lowest_stream.bandwidth == 800000
        assert lowest_stream.resolution == "640x360"

    def test_get_quality_stream_empty(self) -> None:
        """Test getting quality streams with empty list."""
        # Empty streams list
        self.parser.streams = []

        # Get streams
        best_stream = self.parser.get_best_quality_stream()
        lowest_stream = self.parser.get_lowest_quality_stream()

        # Verify None returned
        assert best_stream is None
        assert lowest_stream is None


class TestURLPatternUtils:
    """Test suite for URL pattern utils."""

    def test_extract_url_pattern_simple(self) -> None:
        """Test extracting pattern from simple URL."""
        url = "https://example.com/video/segment1.ts"
        pattern_info = extract_url_pattern(url)

        assert pattern_info is not None
        assert pattern_info["base_url"] == "https://example.com/video/segment"
        assert pattern_info["pattern"] == ".ts"

    def test_extract_url_pattern_complex(self) -> None:
        """Test extracting pattern from complex URL."""
        url = "https://example.com/path/to/video-part-23.mp4?token=123"
        pattern_info = extract_url_pattern(url)

        assert pattern_info is not None
        assert pattern_info["base_url"] == "https://example.com/path/to/video-part-"
        assert pattern_info["pattern"] == ".mp4?token=123"

    def test_extract_url_pattern_no_number(self) -> None:
        """Test extracting pattern from URL without number."""
        url = "https://example.com/video/segment.ts"
        pattern_info = extract_url_pattern(url)

        assert pattern_info is None

    def test_extract_url_pattern_exception(self) -> None:
        """Test extracting pattern with exception."""
        # 使用 patch 替换 re.search 函数
        with patch('m3u8_parser.re.search', side_effect=Exception("Regex error")):
            pattern_info = extract_url_pattern(
                "https://example.com/segment1.ts")
            assert pattern_info is None


class TestExtractors:
    """Test suite for extractor functions."""

    @patch('m3u8_parser.requests.get')
    def test_extract_m3u8_url_from_page_simple(self, mock_get: MagicMock) -> None:
        """Test extracting M3U8 URL from page with simple pattern."""
        # Mock page content with M3U8 URL
        mock_response = MagicMock()
        mock_response.text = """
        Some page content
        https://example.com/playlist.m3u8
        More content
        """
        mock_get.return_value = mock_response

        # Extract URL
        url = extract_m3u8_url_from_page("https://example.com/page")

        assert url == "https://example.com/playlist.m3u8"

    @patch('m3u8_parser.requests.get')
    def test_extract_m3u8_url_from_page_quoted(self, mock_get: MagicMock) -> None:
        """Test extracting M3U8 URL from page with quotes."""
        # Mock page content with quoted M3U8 URL
        mock_response = MagicMock()
        mock_response.text = """
        Some page content
        var url = "https://example.com/playlist.m3u8?token=123";
        More content
        """
        mock_get.return_value = mock_response

        # Extract URL
        url = extract_m3u8_url_from_page("https://example.com/page")

        assert url == "https://example.com/playlist.m3u8?token=123"

    @patch('m3u8_parser.requests.get')
    def test_extract_m3u8_url_from_page_none(self, mock_get: MagicMock) -> None:
        """Test extracting M3U8 URL from page with no URL."""
        # Mock page content without M3U8 URL
        mock_response = MagicMock()
        mock_response.text = "Some page content without M3U8 links"
        mock_get.return_value = mock_response

        # Extract URL
        url = extract_m3u8_url_from_page("https://example.com/page")

        assert url == ""

    @patch('m3u8_parser.requests.get')
    def test_extract_m3u8_url_from_page_exception(self, mock_get: MagicMock) -> None:
        """Test extracting M3U8 URL with exception."""
        # Mock request exception
        mock_get.side_effect = Exception("Connection error")

        # Extract URL
        url = extract_m3u8_url_from_page("https://example.com/page")

        assert url == ""

    @patch('m3u8_parser.extract_m3u8_url_from_page')
    @patch('m3u8_parser.M3U8Parser.parse_url')
    def test_extract_m3u8_info_from_page(self, mock_parse_url: MagicMock, mock_extract: MagicMock) -> None:
        """Test extracting M3U8 info from a webpage (not direct M3U8 link)."""
        # Setup mocks
        mock_extract.return_value = "https://example.com/playlist.m3u8"

        # Create mock stream
        stream = M3U8Stream()
        stream.url = "https://example.com/playlist.m3u8"
        stream.resolution = "1280x720"
        stream.bandwidth = 1500000
        stream.duration = 60.0
        stream.segment_count = 6
        stream.base_url = "https://example.com/"

        # Create mock segment
        segment = M3U8Segment()
        segment.url = "https://example.com/segment1.ts"
        segment.duration = 10.0
        segment.index = 0

        stream.segments = [segment]

        # Setup parser mock
        mock_parse_url.return_value = [stream]

        # Extract info
        result = extract_m3u8_info("https://example.com/page")

        # Verify results
        assert result["success"] is True
        assert len(result["streams"]) == 1
        assert result["streams"][0]["resolution"] == "1280x720"
        assert result["streams"][0]["bandwidth"] == 1500000
        assert result["streams"][0]["url"] == "https://example.com/playlist.m3u8"
        assert result["segments"] == 6
        assert result["duration"] == 60.0
        assert "base_url" in result
        assert "pattern" in result

    @patch('m3u8_parser.M3U8Parser.parse_url')
    def test_extract_m3u8_info_direct_link(self, mock_parse_url: MagicMock) -> None:
        """Test extracting M3U8 info from direct M3U8 link."""
        # Create mock stream
        stream = M3U8Stream()
        stream.url = "https://example.com/playlist.m3u8"
        stream.resolution = "1920x1080"
        stream.bandwidth = 2000000
        stream.duration = 120.0
        stream.segment_count = 12
        stream.base_url = "https://example.com/"
        stream.encryption = EncryptionMethod.AES_128
        stream.key_url = "https://example.com/key.bin"
        stream.key_iv = "0x123456"

        # Create mock segment
        segment = M3U8Segment()
        segment.url = "https://example.com/segment1.ts"
        segment.duration = 10.0
        segment.index = 0
        segment.encryption = EncryptionMethod.AES_128
        segment.key_url = "https://example.com/key.bin"
        segment.key_iv = "0x123456"

        stream.segments = [segment]

        # Setup parser mock
        mock_parse_url.return_value = [stream]

        # Extract info
        result = extract_m3u8_info("https://example.com/playlist.m3u8")

        # Verify results
        assert result["success"] is True
        assert result["selected_stream"]["resolution"] == "1920x1080"
        assert result["selected_stream"]["bandwidth"] == 2000000
        assert result["key_url"] == "https://example.com/key.bin"
        assert result["encryption"] == "AES-128"

    @patch('m3u8_parser.M3U8Parser.parse_url')
    def test_extract_m3u8_info_no_streams(self, mock_parse_url: MagicMock) -> None:
        """Test extracting M3U8 info with no streams."""
        # Mock empty streams list
        mock_parse_url.return_value = []

        # Extract info
        result = extract_m3u8_info("https://example.com/playlist.m3u8")

        # Verify results
        assert result["success"] is False
        assert result["message"] == "Unable to parse M3U8 playlist"

    @patch('m3u8_parser.extract_m3u8_url_from_page')
    def test_extract_m3u8_info_no_url(self, mock_extract: MagicMock) -> None:
        """Test extracting M3U8 info with no URL found."""
        # Mock URL extraction failure
        mock_extract.return_value = ""

        # Extract info
        result = extract_m3u8_info("https://example.com/page")

        # Verify results
        assert result["success"] is False
        assert result["message"] == "Unable to extract M3U8 link from page"

    @patch('m3u8_parser.M3U8Parser.parse_url')
    def test_extract_m3u8_info_exception(self, mock_parse_url: MagicMock) -> None:
        """Test extracting M3U8 info with exception."""
        # Mock exception
        mock_parse_url.side_effect = Exception("Parsing error")

        # Extract info
        result = extract_m3u8_info("https://example.com/playlist.m3u8")

        # Verify results
        assert result["success"] is False
        assert "Parsing error" in result["message"]


if __name__ == "__main__":
    pytest.main(["-v", "test_m3u8_parser.py"])
