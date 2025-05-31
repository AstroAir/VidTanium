"""
日志条目模型类

定义日志条目的数据结构和工具方法
"""

from datetime import datetime


class LogEntry:
    """单个日志条目的数据模型"""

    def __init__(self, message, level="info", details=None, timestamp=None):
        """
        创建日志条目

        Args:
            message: 日志消息内容
            level: 日志级别 ('info', 'warning', 'error')
            details: 详细信息（可选）
            timestamp: 时间戳（默认为当前时间）
        """
        self.message = message
        self.level = level.lower()
        self.timestamp = timestamp or datetime.now()
        self.timestamp_str = self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        self.details = details or ""
        self.display_text = f"[{self.timestamp_str}] [{self.level.upper()}] {self.message}"

    def matches_search(self, search_text):
        """
        检查日志是否匹配搜索文本

        Args:
            search_text: 要搜索的文本

        Returns:
            bool: 是否匹配
        """
        if not search_text:
            return True

        search_text = search_text.lower()
        return (search_text in self.message.lower() or
                search_text in self.level.lower() or
                search_text in self.details.lower())

    def matches_level_filter(self, level_filter):
        """
        检查日志是否匹配级别过滤器

        Args:
            level_filter: 级别过滤索引 (0=全部, 1=仅错误, 2=仅警告, 3=仅信息, 4=无错误)

        Returns:
            bool: 是否匹配
        """
        if level_filter == 0:  # 全部
            return True
        elif level_filter == 1:  # 仅错误
            return self.level == "error"
        elif level_filter == 2:  # 仅警告
            return self.level == "warning"
        elif level_filter == 3:  # 仅信息
            return self.level == "info"
        elif level_filter == 4:  # 无错误
            return self.level != "error"
        return True

    def matches_date_filter(self, date_filter):
        """
        检查日志是否匹配日期过滤器

        Args:
            date_filter: 日期过滤索引 (0=全部, 1=今天, 2=一小时内, 3=十分钟内)

        Returns:
            bool: 是否匹配
        """
        if date_filter == 0:  # 全部
            return True

        now = datetime.now()

        if date_filter == 1:  # 今天
            return self.timestamp.date() == now.date()
        elif date_filter == 2:  # 一小时内
            return (now - self.timestamp).total_seconds() <= 3600
        elif date_filter == 3:  # 十分钟内
            return (now - self.timestamp).total_seconds() <= 600

        return True
