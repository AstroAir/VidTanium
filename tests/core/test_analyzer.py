import pytest
from unittest.mock import patch, Mock
from typing import Dict, Any

# 导入要测试的模块
from analyzer import MediaAnalyzer


class TestMediaAnalyzer:
    """测试 MediaAnalyzer 类的测试套件。"""

    def setup_method(self):
        """设置测试装置。"""
        self.default_analyzer = MediaAnalyzer()
        self.custom_analyzer = MediaAnalyzer({
            "user_agent": "TestAgent/1.0",
            "timeout": 10,
            "verify_ssl": False,
            "proxy": "http://test-proxy:8080"
        })

    def test_initialization(self):
        """测试使用不同设置初始化。"""
        # 测试默认初始化
        assert self.default_analyzer.user_agent.startswith("Mozilla/5.0")
        assert self.default_analyzer.timeout == 30
        assert self.default_analyzer.verify_ssl is True
        assert self.default_analyzer.proxy is None

        # 测试自定义初始化
        assert self.custom_analyzer.user_agent == "TestAgent/1.0"
        assert self.custom_analyzer.timeout == 10
        assert self.custom_analyzer.verify_ssl is False
        assert self.custom_analyzer.proxy == "http://test-proxy:8080"

    # 移除对受保护方法的直接测试，改为测试公开方法
    def test_analyze_url_with_direct_m3u8(self):
        """测试使用直接 M3U8 URL 的 analyze_url 方法。"""
        with patch('analyzer.MediaAnalyzer._is_direct_m3u8') as mock_is_direct_m3u8:
            with patch('analyzer.MediaAnalyzer.analyze_m3u8') as mock_analyze_m3u8:
                # 模拟内部方法行为
                mock_is_direct_m3u8.return_value = True
                mock_analyze_m3u8.return_value = {
                    "success": True, "type": "test"}

                # 测试
                result = self.default_analyzer.analyze_url(
                    "http://example.com/video.m3u8")

                # 验证
                mock_is_direct_m3u8.assert_called_once_with(
                    "http://example.com/video.m3u8")
                mock_analyze_m3u8.assert_called_once_with(
                    "http://example.com/video.m3u8")
                assert result["success"] is True

    @patch('requests.get')
    def test_analyze_url_direct_m3u8(self, mock_get: Mock) -> None:
        """测试直接 M3U8 URL 的 analyze_url。"""
        # 设置
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        #EXTM3U
        #EXT-X-STREAM-INF:BANDWIDTH=1280000,RESOLUTION=640x360
        http://example.com/low.m3u8
        #EXT-X-STREAM-INF:BANDWIDTH=2560000,RESOLUTION=1280x720
        http://example.com/high.m3u8
        """
        mock_get.return_value = mock_response

        # 测试
        result = self.default_analyzer.analyze_url(
            "http://example.com/master.m3u8")

        # 验证
        assert result["success"] is True
        assert result["type"] == "master"
        assert len(result["variants"]) == 2
        assert result["variants"][0]["resolution"] == "640x360"
        assert result["variants"][1]["resolution"] == "1280x720"

    @patch('requests.get')
    def test_analyze_url_webpage_with_m3u8(self, mock_get: Mock) -> None:
        """测试包含 M3U8 链接的网页的 analyze_url。"""
        # 设置网页内容
        webpage_response = Mock()
        webpage_response.status_code = 200
        webpage_response.text = """
        <html>
        <body>
        <script>
        var videoUrl = "http://example.com/video.m3u8";
        </script>
        </body>
        </html>
        """

        # 设置 M3U8 内容
        m3u8_response = Mock()
        m3u8_response.status_code = 200
        m3u8_response.text = """
        #EXTM3U
        #EXTINF:10.0,
        segment1.ts
        #EXTINF:10.0,
        segment2.ts
        """

        # 配置模拟以根据 URL 返回不同响应
        def mock_get_side_effect(url: str, **kwargs: Dict[str, Any]) -> Mock:
            if url == "http://example.com":
                return webpage_response
            elif url == "http://example.com/video.m3u8":
                return m3u8_response
            return Mock(status_code=404)

        mock_get.side_effect = mock_get_side_effect

        # 测试
        result = self.default_analyzer.analyze_url("http://example.com")

        # 验证
        assert result["success"] is True
        assert result["type"] == "media"
        assert len(result["segments"]) == 2
        assert result["segment_count"] == 2
        assert result["total_duration"] == 20.0

    @patch('requests.get')
    def test_analyze_url_no_media(self, mock_get: Mock) -> None:
        """测试没有 M3U8 链接的网页的 analyze_url。"""
        # 设置
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>No media here</body></html>"
        mock_get.return_value = mock_response

        # 测试
        result = self.default_analyzer.analyze_url("http://example.com")

        # 验证
        assert result["success"] is False
        assert "error" in result
        assert "Unable to extract media URLs from page" in result["error"]

    @patch('requests.get')
    def test_analyze_m3u8_master_playlist(self, mock_get: Mock) -> None:
        """测试带有主播放列表的 analyze_m3u8。"""
        # 设置
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        #EXTM3U
        #EXT-X-STREAM-INF:BANDWIDTH=1280000,RESOLUTION=640x360,CODECS="avc1.4d401e,mp4a.40.2"
        low.m3u8
        #EXT-X-STREAM-INF:BANDWIDTH=2560000,RESOLUTION=1280x720,CODECS="avc1.4d401f,mp4a.40.2"
        high.m3u8
        """
        mock_get.return_value = mock_response

        # 测试
        result = self.default_analyzer.analyze_m3u8(
            "http://example.com/master.m3u8")

        # 验证
        assert result["success"] is True
        assert result["type"] == "master"
        assert len(result["variants"]) == 2
        assert result["variants"][0]["resolution"] == "640x360"
        assert result["variants"][0]["bandwidth"] == 1280000
        assert result["variants"][0]["codec"] == "avc1.4d401e,mp4a.40.2"
        assert result["variants"][0]["url"].endswith("low.m3u8")
        assert result["variants"][1]["resolution"] == "1280x720"

    @patch('requests.get')
    def test_analyze_m3u8_media_playlist(self, mock_get: Mock) -> None:
        """测试带有媒体播放列表的 analyze_m3u8。"""
        # 设置
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        #EXTM3U
        #EXT-X-VERSION:3
        #EXT-X-TARGETDURATION:10
        #EXTINF:9.5,
        segment1.ts
        #EXTINF:10.0,
        segment2.ts
        #EXTINF:8.5,
        segment3.ts
        #EXT-X-ENDLIST
        """
        mock_get.return_value = mock_response

        # 测试
        result = self.default_analyzer.analyze_m3u8(
            "http://example.com/playlist.m3u8")

        # 验证
        assert result["success"] is True
        assert result["type"] == "media"
        assert len(result["segments"]) == 3
        assert result["segment_count"] == 3
        assert result["total_duration"] == 28.0
        assert result["encryption"] == "none"
        assert result["segments"][0].endswith("segment1.ts")

    @patch('requests.get')
    def test_analyze_m3u8_encrypted_media_playlist(self, mock_get: Mock) -> None:
        """测试带加密媒体播放列表的 analyze_m3u8。"""
        # 设置
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        #EXTM3U
        #EXT-X-VERSION:3
        #EXT-X-KEY:METHOD=AES-128,URI="key.bin",IV=0x1234567890ABCDEF1234567890ABCDEF
        #EXTINF:10.0,
        segment1.ts
        #EXTINF:10.0,
        segment2.ts
        #EXT-X-ENDLIST
        """
        mock_get.return_value = mock_response

        # 测试
        result = self.default_analyzer.analyze_m3u8(
            "http://example.com/playlist.m3u8")

        # 验证
        assert result["success"] is True
        assert result["encryption"] == "aes-128"
        assert "key_url" in result
        assert result["key_url"].endswith("key.bin")
        assert result["iv"] == "1234567890ABCDEF1234567890ABCDEF"
        assert "encryption_details" in result
        assert result["encryption_details"]["method"] == "AES-128"

    @patch('requests.get')
    def test_analyze_m3u8_invalid_format(self, mock_get: Mock) -> None:
        """测试无效 M3U8 格式的 analyze_m3u8。"""
        # 设置
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "This is not an M3U8 file"
        mock_get.return_value = mock_response

        # 测试
        result = self.default_analyzer.analyze_m3u8(
            "http://example.com/invalid.m3u8")

        # 验证
        assert result["success"] is False
        assert "error" in result
        assert "Invalid M3U8 format" in result["error"]

    @patch('requests.get')
    def test_extract_media_from_page(self, mock_get: Mock) -> None:
        """测试 extract_media_from_page 方法。"""
        # 设置
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
        <body>
        <script>
        var videoUrl = "http://example.com/video1.m3u8";
        var player = {
            "sources": [
                {"src": "http://example.com/video2.m3u8", "type": "application/x-mpegURL"},
                {"src": "http://example.com/video.mp4", "type": "video/mp4"}
            ]
        };
        </script>
        <a href="http://example.com/api/getVideo">API Link</a>
        </body>
        </html>
        """
        mock_get.return_value = mock_response

        # 测试
        result = self.default_analyzer.extract_media_from_page(
            "http://example.com")

        # 验证
        assert len(result) == 2
        assert "http://example.com/video1.m3u8" in result
        assert "http://example.com/video2.m3u8" in result

    @patch('requests.get')
    def test_extract_media_from_page_with_api_endpoints(self, mock_get: Mock) -> None:
        """测试带有 API 端点的 extract_media_from_page。"""
        # 设置网页内容
        webpage_response = Mock()
        webpage_response.status_code = 200
        webpage_response.text = """
        <html>
        <body>
        <a href="http://example.com/api/getVideo">API Link</a>
        </body>
        </html>
        """

        # 设置 API 响应
        api_response = Mock()
        api_response.status_code = 200
        api_response.text = '{"url": "http://example.com/video.m3u8"}'

        # 配置模拟以根据 URL 返回不同响应
        def mock_get_side_effect(url: str, **kwargs: Dict[str, Any]) -> Mock:
            if url == "http://example.com":
                return webpage_response
            elif url == "http://example.com/api/getVideo":
                return api_response
            return Mock(status_code=404)

        mock_get.side_effect = mock_get_side_effect

        # 测试
        result = self.default_analyzer.extract_media_from_page(
            "http://example.com")

        # 验证
        assert len(result) == 1
        assert "http://example.com/video.m3u8" in result

    # 移除对内部方法的直接测试
    # 使用集成测试来验证内部方法的行为

    @patch('requests.get')
    def test_analyze_url_integration(self, mock_get: Mock) -> None:
        """整合测试 analyze_url 方法。"""
        # 1. 测试直接 M3U8 链接
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = """
        #EXTM3U
        #EXT-X-VERSION:3
        #EXTINF:10.0,
        segment1.ts
        """
        mock_get.return_value = mock_response

        result = self.default_analyzer.analyze_url(
            "http://example.com/playlist.m3u8")
        assert result["success"] is True
        assert result["type"] == "media"

        # 2. 测试从网页提取
        webpage_mock = Mock()
        webpage_mock.status_code = 200
        webpage_mock.text = '<html><script>var url = "http://example.com/video.m3u8";</script></html>'

        m3u8_mock = Mock()
        m3u8_mock.status_code = 200
        m3u8_mock.text = """
        #EXTM3U
        #EXT-X-STREAM-INF:BANDWIDTH=1280000,RESOLUTION=640x360
        low.m3u8
        """

        def get_side_effect(url: str, **kwargs: Dict[str, Any]) -> Mock:
            if url == "http://example.com/page":
                return webpage_mock
            else:
                return m3u8_mock

        mock_get.side_effect = get_side_effect

        result = self.default_analyzer.analyze_url("http://example.com/page")
        assert result["success"] is True


# 如果直接执行文件，则运行测试
if __name__ == "__main__":
    pytest.main(["-v", __file__])
