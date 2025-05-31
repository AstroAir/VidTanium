from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import Signal, Slot, QObject
import logging

logger = logging.getLogger(__name__)


class SystemTrayIcon(QObject):
    """系统托盘图标管理器"""

    # 信号定义
    action_triggered = Signal(str)  # 动作名称

    def __init__(self, app, settings, parent=None):
        super().__init__(parent)

        self.app = app
        self.settings = settings
        self.parent_widget = parent

        # 创建托盘图标
        self.tray_icon = QSystemTrayIcon(parent)

        # 设置图标（实际应用中应加载实际图标）
        # self.tray_icon.setIcon(QIcon(":/images/icon.png"))
        self.tray_icon.setIcon(self.app.style().standardIcon(
            self.app.style().SP_MediaPlay))

        # 设置提示文本
        self.tray_icon.setToolTip("加密视频下载器")

        # 创建托盘菜单
        self.tray_menu = QMenu(parent)
        self._create_tray_menu()

        # 设置托盘菜单
        self.tray_icon.setContextMenu(self.tray_menu)

        # 连接信号
        self.tray_icon.activated.connect(self._on_tray_activated)

    def _create_tray_menu(self):
        """创建托盘菜单"""
        # 显示/隐藏主窗口
        self.show_action = QAction("显示", self.parent_widget)
        self.show_action.triggered.connect(
            lambda: self.action_triggered.emit("show"))
        self.tray_menu.addAction(self.show_action)

        self.hide_action = QAction("隐藏", self.parent_widget)
        self.hide_action.triggered.connect(
            lambda: self.action_triggered.emit("hide"))
        self.tray_menu.addAction(self.hide_action)

        self.tray_menu.addSeparator()

        # 任务控制
        self.start_all_action = QAction("开始所有任务", self.parent_widget)
        self.start_all_action.triggered.connect(
            lambda: self.action_triggered.emit("start_all"))
        self.tray_menu.addAction(self.start_all_action)

        self.pause_all_action = QAction("暂停所有任务", self.parent_widget)
        self.pause_all_action.triggered.connect(
            lambda: self.action_triggered.emit("pause_all"))
        self.tray_menu.addAction(self.pause_all_action)

        self.tray_menu.addSeparator()

        # 退出
        self.exit_action = QAction("退出", self.parent_widget)
        self.exit_action.triggered.connect(
            lambda: self.action_triggered.emit("exit"))
        self.tray_menu.addAction(self.exit_action)

    def _on_tray_activated(self, reason):
        """托盘图标被激活"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # 单击托盘图标
            if self.parent_widget is not None:
                if self.parent_widget.isVisible():
                    self.action_triggered.emit("hide")
                else:
                    self.action_triggered.emit("show")
            else:
                # Handle case when parent widget doesn't exist
                # Could log a warning or show a notification
                self.action_triggered.emit("show")

    def show_notification(self, title, message, icon=None, duration=5000):
        """显示托盘通知

        Args:
            title (str): 通知标题
            message (str): 通知内容
            icon: 通知图标 (可选)
            duration: 通知显示时长(毫秒，默认5000)
        """
        if not self.settings.get("ui", "show_notifications", True):
            return

        # Use default icon if none provided
        tray_icon = QSystemTrayIcon.MessageIcon.Information
        if icon:
            tray_icon = icon

        self.tray_icon.showMessage(title, message, tray_icon, duration)

    def show(self):
        """显示托盘图标"""
        self.tray_icon.show()

    def hide(self):
        """隐藏托盘图标"""
        self.tray_icon.hide()

    def is_supported(self):
        """检查系统是否支持托盘图标"""
        return QSystemTrayIcon.isSystemTrayAvailable()

    def update_menu_state(self, running_tasks):
        """更新菜单状态"""
        has_running = running_tasks > 0

        # 更新动作状态
        self.start_all_action.setEnabled(True)
        self.pause_all_action.setEnabled(has_running)

        # 更新图标提示
        if has_running:
            self.tray_icon.setToolTip(f"加密视频下载器 - {running_tasks} 个任务运行中")
        else:
            self.tray_icon.setToolTip("加密视频下载器")
