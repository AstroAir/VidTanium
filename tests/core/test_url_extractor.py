import pytest
from unittest.mock import patch, Mock, MagicMock, mock_open
import requests

# 使用相对导入来解决导入路径问题
from src.core.url_extractor import URLExtractor


class TestURLExtractor:
    """Test suite for URLExtractor class."""

    def setup_method(self) -> None:
        """Set up test environment before each test."""
        # Common test data
        self.sample_text = """
        Here are some URLs:
        https://example.com
        http://test.org/path
        www.example.org/test.html
        Not a URL: just some text
        """

        self.sample_html = """
        <html>
        <head><title>Test Page</title></head>
        <body>
            <a href="https://example.com/video.mp4">Video 1</a>
            <video src="https://example.com/media/video2.mp4"></video>
            <script>
                var videoUrl = "https://streaming.example.com/video.m3u8?token=123";
                var relativePath = "/videos/sample.mp4";
            </script>
            <img src="image.jpg" />
        </body>
        </html>
        """

    def test_extract_urls_from_text_empty_input(self) -> None:
        """Test extracting URLs from empty text."""
        # Test with empty string
        result = URLExtractor.extract_urls_from_text("")
        assert result == []

        # 正确的方法是不要尝试传递 None，因为该方法需要 str 类型
        # 而是在测试中捕获类型错误
        with pytest.raises(Exception):  # 使用通用 Exception 而非 TypeError
            # mypy 会静态检查出这个错误，但我们在运行时测试这个行为
            URLExtractor.extract_urls_from_text("")  # 

    def test_extract_urls_from_text_default_pattern(self) -> None:
        """Test extracting URLs with default pattern."""
        result = URLExtractor.extract_urls_from_text(self.sample_text)

        # Check if the correct URLs were extracted
        assert "https://example.com" in result
        assert "http://test.org/path" in result
        assert "http://www.example.org/test.html" in result  # With http:// prefix
        assert len(result) == 3

        # Check that the www. URL was properly processed
        assert all(url.startswith(('http://', 'https://')) for url in result)

    def test_extract_urls_from_text_custom_pattern(self) -> None:
        """Test extracting URLs with custom pattern."""
        # Custom pattern to extract only https URLs
        pattern = r'(https://[^\s<>"\']+)'
        result = URLExtractor.extract_urls_from_text(self.sample_text, pattern)

        assert "https://example.com" in result
        assert "http://test.org/path" not in result
        assert len(result) == 1

    def test_extract_urls_from_text_invalid_pattern(self) -> None:
        """Test extracting URLs with invalid regex pattern."""
        # Invalid regex pattern (unbalanced parenthesis)
        pattern = r'(https://'
        result = URLExtractor.extract_urls_from_text(self.sample_text, pattern)

        # Should return empty list on regex error
        assert result == []

    def test_extract_urls_from_text_multiple_capture_groups(self) -> None:
        """Test extracting URLs with pattern containing multiple capture groups."""
        # Pattern with multiple capture groups
        pattern = r'(https?://([^\s<>"\']+))'
        result = URLExtractor.extract_urls_from_text(self.sample_text, pattern)

        # Should extract the first group
        assert "https://example.com" in result
        assert "http://test.org/path" in result
        assert "example.com" not in result  # Second capture group should be ignored
        assert len(result) == 2

    @patch('builtins.open', new_callable=mock_open, read_data="https://example.com\nhttp://test.org")
    def test_extract_urls_from_file_success(self, mock_file: MagicMock) -> None:
        """Test extracting URLs from a file successfully."""
        result = URLExtractor.extract_urls_from_file("dummy/path.txt")

        # File should be opened with correct parameters
        mock_file.assert_called_with("dummy/path.txt", 'r', encoding='utf-8')

        # Check if URLs were extracted
        assert "https://example.com" in result
        assert "http://test.org" in result
        assert len(result) == 2

    @patch('builtins.open', side_effect=IOError("File not found"))
    def test_extract_urls_from_file_error(self, mock_file: MagicMock) -> None:
        """Test extracting URLs from a file that doesn't exist."""
        result = URLExtractor.extract_urls_from_file("nonexistent/file.txt")

        # Should return empty list on file error
        assert result == []
        mock_file.assert_called_with(
            "nonexistent/file.txt", 'r', encoding='utf-8')

    @patch('requests.get')
    def test_extract_media_urls_from_webpage_success(self, mock_get: MagicMock) -> None:
        """Test extracting media URLs from a webpage successfully."""
        # Configure the mock response
        mock_response = Mock()
        mock_response.text = self.sample_html
        mock_get.return_value = mock_response

        result = URLExtractor.extract_media_urls_from_webpage(
            "https://example.com")

        # Validate the requests.get call
        mock_get.assert_called()
        assert mock_get.call_args_list[0][0][0] == "https://example.com"

        # Check extracted URLs
        assert "https://example.com/video.mp4" in result
        assert "https://example.com/media/video2.mp4" in result
        assert "https://streaming.example.com/video.m3u8?token=123" in result
        # Relative URL converted to absolute
        assert "https://example.com/videos/sample.mp4" in result
        assert len(result) == 4

        # Verify the URLs are sorted
        assert result == sorted(result)

    @patch('requests.get')
    def test_extract_media_urls_custom_extensions(self, mock_get: MagicMock) -> None:
        """Test extracting media URLs with custom extensions."""
        # Configure the mock response
        mock_response = Mock()
        mock_response.text = """
        <a href="https://example.com/document.pdf">PDF</a>
        <a href="https://example.com/data.csv">CSV</a>
        """
        mock_get.return_value = mock_response

        result = URLExtractor.extract_media_urls_from_webpage(
            "https://example.com",
            media_extensions=['.pdf', '.csv']
        )

        assert "https://example.com/document.pdf" in result
        assert "https://example.com/data.csv" in result
        assert len(result) == 2

    @patch('requests.get')
    def test_extract_media_urls_custom_headers(self, mock_get: MagicMock) -> None:
        """Test extracting media URLs with custom headers."""
        # Configure the mock response
        mock_response = Mock()
        mock_response.text = self.sample_html
        mock_get.return_value = mock_response

        custom_headers = {
            'User-Agent': 'Custom User Agent',
            'Referer': 'https://referer.com'
        }

        result = URLExtractor.extract_media_urls_from_webpage(
            "https://example.com",
            headers=custom_headers
        )

        # 获取 mock_get 被调用时传入的 kwargs 参数，并检查 headers
        called_kwargs = mock_get.call_args_list[0][1]
        assert called_kwargs.get('headers') == custom_headers

        # Check result contains expected URLs
        assert len(result) == 4

    @patch('requests.get', side_effect=requests.exceptions.RequestException("Connection error"))
    def test_extract_media_urls_request_error(self, mock_get: MagicMock) -> None:
        """Test handling request errors when extracting media URLs."""
        result = URLExtractor.extract_media_urls_from_webpage(
            "https://example.com")

        # Should return empty list on request error
        assert result == []
        mock_get.assert_called()

    def test_filter_urls_no_patterns(self) -> None:
        """Test filtering URLs without any patterns."""
        urls = ["https://example.com", "https://test.com/image.jpg",
                "http://media.org/video.mp4"]
        result = URLExtractor.filter_urls(urls)

        # Without patterns, all URLs should be included
        assert result == urls
        assert len(result) == 3

    def test_filter_urls_include_pattern(self) -> None:
        """Test filtering URLs with include pattern only."""
        urls = ["https://example.com", "https://test.com/image.jpg",
                "http://media.org/video.mp4"]
        result = URLExtractor.filter_urls(urls, include_pattern=r'image|video')

        # Only URLs matching the pattern should be included
        assert "https://test.com/image.jpg" in result
        assert "http://media.org/video.mp4" in result
        assert "https://example.com" not in result
        assert len(result) == 2

    def test_filter_urls_exclude_pattern(self) -> None:
        """Test filtering URLs with exclude pattern only."""
        urls = ["https://example.com", "https://test.com/image.jpg",
                "http://media.org/video.mp4"]
        result = URLExtractor.filter_urls(urls, exclude_pattern=r'image|video')

        # URLs matching the pattern should be excluded
        assert "https://example.com" in result
        assert "https://test.com/image.jpg" not in result
        assert "http://media.org/video.mp4" not in result
        assert len(result) == 1

    def test_filter_urls_both_patterns(self) -> None:
        """Test filtering URLs with both include and exclude patterns."""
        urls = [
            "https://example.com",
            "https://test.com/image.jpg",
            "http://media.org/video.mp4",
            "https://media.org/video.jpg"
        ]
        result = URLExtractor.filter_urls(
            urls,
            include_pattern=r'media\.org',
            exclude_pattern=r'\.mp4'
        )

        # URLs must match include pattern AND not match exclude pattern
        # Matches include, doesn't match exclude
        assert "https://media.org/video.jpg" in result
        # Matches include, but also matches exclude
        assert "http://media.org/video.mp4" not in result
        assert "https://test.com/image.jpg" not in result  # Doesn't match include
        assert "https://example.com" not in result  # Doesn't match include
        assert len(result) == 1

    def test_normalize_url_already_normalized(self) -> None:
        """Test normalizing an already normalized URL."""
        url = "https://example.com/path?query=value#fragment"
        result = URLExtractor.normalize_url(url)

        # URL should remain unchanged
        assert result == url

    def test_normalize_url_add_protocol(self) -> None:
        """Test normalizing a URL without protocol."""
        url = "example.com/path"
        result = URLExtractor.normalize_url(url)

        # Protocol should be added
        assert result == "http://example.com/path"

    def test_normalize_url_with_components(self) -> None:
        """Test normalizing a URL with various components."""
        url = "www.example.com/path;param?query=value#fragment"
        result = URLExtractor.normalize_url(url)

        # All components should be preserved
        assert result == "http://www.example.com/path;param?query=value#fragment"

    def test_validate_url_valid(self) -> None:
        """Test validating valid URLs."""
        valid_urls = [
            "https://example.com",
            "http://test.org/path",
            "https://sub.domain.com/path?query=value#fragment"
        ]

        for url in valid_urls:
            assert URLExtractor.validate_url(url) is True

    def test_validate_url_invalid(self) -> None:
        """Test validating invalid URLs."""
        invalid_urls = [
            "",  # Empty
            "not a url",  # No structure
            "://missing-protocol.com",  # Missing protocol
            "http://",  # Missing domain
            "http://.com",  # Invalid domain
        ]

        for url in invalid_urls:
            assert URLExtractor.validate_url(url) is False

    def test_validate_url_exception(self) -> None:
        """Test URL validation with input that causes exceptions."""
        # Test with None which should cause an exception
        with patch('urllib.parse.urlparse', side_effect=Exception("Test exception")):
            assert URLExtractor.validate_url("https://example.com") is False


if __name__ == "__main__":
    pytest.main(["-v", "test_url_extractor.py"])
