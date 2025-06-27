"""
日志查看器组件

提供日志查看、过滤和管理功能
"""

# 重定向导入，使用增强版本
from .log.log_viewer import LogViewer

# 保持所有的公共API
__all__ = ['LogViewer']
