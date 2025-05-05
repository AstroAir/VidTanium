import logging
import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QMenu, QToolBar, QStatusBar,
    QLabel, QSplitter, QMessageBox, QFileDialog, QApplication
)
from PySide6.QtCore import Qt, QSize, QTimer, Signal, Slot
from PySide6.QtGui import QIcon, QKeySequence, QAction

from .widgets.task_manager import TaskManager
from .widgets.log_viewer import LogViewer
from .dialogs.settings_dialog import SettingsDialog
from .dialogs.task_dialog import TaskDialog
from .dialogs.about_dialog import AboutDialog

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """应用程序主窗口"""

    def __init__(self, app, download_manager, settings):
        super().__init__()

        self.app = app
        self.download_manager = download_manager
        self.settings = settings

        self._force_close = False

        # 设置下载管理器回调
        self.download_manager.on_task_progress = self.on_task_progress
        self.download_manager.on_task_status_changed = self.on_task_status_changed
        self.download_manager.on_task_completed = self.on_task_completed
        self.download_manager.on_task_failed = self.on_task_failed

        # 设置窗口属性
        self.setWindowTitle("加密视频下载器")
        self.setMinimumSize(1000, 700)

        # 创建界面
        self._create_ui()
        self._create_menu()
        self._create_toolbar()
        self._create_statusbar()

        # 连接信号
        self._connect_signals()

        # 初始化自动保存定时器
        self._setup_auto_save()

        # 更新 UI
        self._update_ui()

        logger.info("主窗口已初始化")

    def _create_ui(self):
        """创建主窗口界面"""
        # 创建中央窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(6, 6, 6, 6)  # 减小边距
        main_layout.setSpacing(4)  # 减小间距，使布局更紧凑

        # 创建分割器
        self.main_splitter = QSplitter(Qt.Vertical)
        self.main_splitter.setHandleWidth(8)  # 增加分割条宽度，使其易于拖动
        self.main_splitter.setChildrenCollapsible(False)  # 防止子部件被完全折叠

        # 下载面板
        self.task_manager = TaskManager(self.settings)
        self.main_splitter.addWidget(self.task_manager)

        # 日志查看器
        self.log_viewer = LogViewer()
        self.main_splitter.addWidget(self.log_viewer)

        # 设置分割比例 (70% 任务, 30% 日志)
        self.main_splitter.setSizes(
            [int(self.height() * 0.7), int(self.height() * 0.3)])

        # 添加到主布局
        main_layout.addWidget(self.main_splitter)

        # 连接任务管理器信号
        self.task_manager.task_action_requested.connect(
            self.handle_task_action)

        # 窗口状态恢复
        geometry = self.settings.get("ui", "window_geometry", None)
        state = self.settings.get("ui", "window_state", None)

        if geometry:
            try:
                from PySide6.QtCore import QByteArray
                self.restoreGeometry(QByteArray.fromBase64(geometry.encode()))
            except Exception:
                pass

        if state:
            try:
                from PySide6.QtCore import QByteArray
                self.restoreState(QByteArray.fromBase64(state.encode()))
            except Exception:
                pass

    def _create_menu(self):
        """创建菜单栏"""
        # 文件菜单
        file_menu = self.menuBar().addMenu("文件(&F)")

        new_task_action = QAction("新建任务(&N)", self)
        new_task_action.setShortcut(QKeySequence.New)
        new_task_action.triggered.connect(self.show_new_task_dialog)
        file_menu.addAction(new_task_action)

        import_url_action = QAction("从URL导入(&I)", self)
        import_url_action.setShortcut("Ctrl+I")
        import_url_action.triggered.connect(self.import_from_url)
        file_menu.addAction(import_url_action)

        file_menu.addSeparator()

        settings_action = QAction("设置(&S)", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self.show_settings)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        import_menu = QMenu("导入", self)

        import_url_action = QAction("从URL导入", self)
        import_url_action.setShortcut("Ctrl+I")
        import_url_action.triggered.connect(self.import_from_url)
        import_menu.addAction(import_url_action)

        import_batch_action = QAction("批量导入URL", self)
        import_batch_action.setShortcut("Ctrl+B")
        import_batch_action.triggered.connect(self.import_batch_urls)
        import_menu.addAction(import_batch_action)

        file_menu.addMenu(import_menu)

        file_menu.addSeparator()

        exit_action = QAction("退出(&Q)", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 添加媒体菜单
        media_menu = self.menuBar().addMenu("媒体(&M)")

        process_media_action = QAction("处理媒体文件(&P)", self)
        process_media_action.setShortcut("Ctrl+P")
        process_media_action.triggered.connect(self.show_media_processing)
        media_menu.addAction(process_media_action)

        media_menu.addSeparator()

        batch_convert_action = QAction("批量转换(&B)", self)
        batch_convert_action.triggered.connect(self.show_batch_conversion)
        media_menu.addAction(batch_convert_action)

        # 任务菜单
        task_menu = self.menuBar().addMenu("任务(&T)")

        start_all_action = QAction("全部开始(&S)", self)
        start_all_action.triggered.connect(self.start_all_tasks)
        task_menu.addAction(start_all_action)

        pause_all_action = QAction("全部暂停(&P)", self)
        pause_all_action.triggered.connect(self.pause_all_tasks)
        task_menu.addAction(pause_all_action)

        task_menu.addSeparator()

        clear_completed_action = QAction("清除已完成任务(&C)", self)
        clear_completed_action.triggered.connect(self.clear_completed_tasks)
        task_menu.addAction(clear_completed_action)

        # 帮助菜单
        help_menu = self.menuBar().addMenu("帮助(&H)")

        about_action = QAction("关于(&A)", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def _create_toolbar(self):
        """创建工具栏"""
        # 主工具栏
        self.toolbar = QToolBar("主工具栏")
        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(QSize(24, 24))
        self.toolbar.setStyleSheet("""
            QToolBar {
                background-color: #f8f8f8;
                border-bottom: 1px solid #d0d0d0;
                padding: 2px;
                spacing: 2px;
            }
            
            QToolButton {
                border: none;
                padding: 4px;
                border-radius: 4px;
            }
            
            QToolButton:hover {
                background-color: #e8e8e8;
            }
            
            QToolButton:pressed {
                background-color: #d0d0d0;
            }
        """)
        self.addToolBar(self.toolbar)

        # 工具栏图标路径
        # 在实际应用中，应该从资源文件或图标文件夹中加载
        # 这里使用PySide6内置的标准图标作为示例
        from PySide6.QtGui import QIcon
        from PySide6.QtWidgets import QStyle

        # 获取标准图标
        style = self.style()

        # 新建任务
        new_task_action = QAction("新建任务", self)
        new_task_action.setIcon(style.standardIcon(QStyle.SP_FileIcon))
        new_task_action.setToolTip("创建新的下载任务")
        new_task_action.triggered.connect(self.show_new_task_dialog)
        self.toolbar.addAction(new_task_action)

        # 开始所有
        start_all_action = QAction("全部开始", self)
        start_all_action.setIcon(style.standardIcon(QStyle.SP_MediaPlay))
        start_all_action.setToolTip("开始所有等待中的任务")
        start_all_action.triggered.connect(self.start_all_tasks)
        self.toolbar.addAction(start_all_action)

        # 暂停所有
        pause_all_action = QAction("全部暂停", self)
        pause_all_action.setIcon(style.standardIcon(QStyle.SP_MediaPause))
        pause_all_action.setToolTip("暂停所有运行中的任务")
        pause_all_action.triggered.connect(self.pause_all_tasks)
        self.toolbar.addAction(pause_all_action)

        # 清理已完成
        clear_completed_action = QAction("清理已完成", self)
        clear_completed_action.setIcon(style.standardIcon(QStyle.SP_TrashIcon))
        clear_completed_action.setToolTip("清除所有已完成的任务")
        clear_completed_action.triggered.connect(self.clear_completed_tasks)
        self.toolbar.addAction(clear_completed_action)

        self.toolbar.addSeparator()

        # 媒体处理
        process_media_action = QAction("处理媒体", self)
        process_media_action.setIcon(
            style.standardIcon(QStyle.SP_DriveDVDIcon))
        process_media_action.setToolTip("处理媒体文件")
        process_media_action.triggered.connect(self.show_media_processing)
        self.toolbar.addAction(process_media_action)

        self.toolbar.addSeparator()

        # 设置
        settings_action = QAction("设置", self)
        settings_action.setIcon(style.standardIcon(
            QStyle.SP_FileDialogDetailedView))
        settings_action.setToolTip("打开设置对话框")
        settings_action.triggered.connect(self.show_settings)
        self.toolbar.addAction(settings_action)

        # 关于
        about_action = QAction("关于", self)
        about_action.setIcon(style.standardIcon(
            QStyle.SP_MessageBoxInformation))
        about_action.setToolTip("关于软件")
        about_action.triggered.connect(self.show_about)
        self.toolbar.addAction(about_action)

    def _create_statusbar(self):
        """创建状态栏"""
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #f8f8f8;
                border-top: 1px solid #d0d0d0;
            }
            
            QStatusBar::item {
                border: none;
            }
            
            QLabel {
                padding: 3px 6px;
            }
        """)
        self.setStatusBar(self.status_bar)

        # 创建状态布局
        from PySide6.QtWidgets import QFrame

        # 创建任务状态面板
        task_frame = QFrame()
        task_layout = QHBoxLayout(task_frame)
        task_layout.setContentsMargins(2, 0, 2, 0)
        task_layout.setSpacing(10)

        # 状态颜色指示器
        self.status_indicator = QLabel()
        self.status_indicator.setFixedSize(12, 12)
        self.status_indicator.setStyleSheet("""
            background-color: #00b050;
            border-radius: 6px;
        """)
        task_layout.addWidget(self.status_indicator)

        # 任务状态标签
        self.task_status_label = QLabel("就绪")
        task_layout.addWidget(self.task_status_label)

        # 添加到状态栏
        self.status_bar.addWidget(task_frame)

        # 添加分隔线
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.VLine)
        separator1.setFrameShadow(QFrame.Sunken)
        separator1.setStyleSheet("background-color: #d0d0d0;")
        separator1.setFixedWidth(1)
        separator1.setFixedHeight(16)
        self.status_bar.addWidget(separator1)

        # 活动任务信息
        self.active_tasks_label = QLabel("活动任务: 0/0")
        self.status_bar.addWidget(self.active_tasks_label)

        # 添加分隔线
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.VLine)
        separator2.setFrameShadow(QFrame.Sunken)
        separator2.setStyleSheet("background-color: #d0d0d0;")
        separator2.setFixedWidth(1)
        separator2.setFixedHeight(16)
        self.status_bar.addWidget(separator2)

        # CPU 使用率
        self.cpu_usage_label = QLabel("CPU: 0%")
        self.status_bar.addWidget(self.cpu_usage_label)

        # 内存使用率
        self.memory_usage_label = QLabel("内存: 0MB")
        self.status_bar.addWidget(self.memory_usage_label)

        # 添加弹簧
        self.status_bar.addPermanentWidget(QFrame(), 1)  # 弹簧

        # 总下载速度面板
        speed_frame = QFrame()
        speed_layout = QHBoxLayout(speed_frame)
        speed_layout.setContentsMargins(6, 0, 6, 0)
        speed_layout.setSpacing(6)

        # 速度图标
        from PySide6.QtGui import QIcon
        from PySide6.QtWidgets import QStyle, QLabel

        speed_icon = QLabel()
        speed_icon.setPixmap(self.style().standardIcon(
            QStyle.SP_ArrowDown).pixmap(16, 16))
        speed_layout.addWidget(speed_icon)

        # 速度标签
        self.speed_label = QLabel("0 B/s")
        self.speed_label.setStyleSheet("font-weight: bold;")
        speed_layout.addWidget(self.speed_label)

        # 添加到状态栏
        self.status_bar.addPermanentWidget(speed_frame)

        # 设置定时器更新CPU和内存使用情况
        self.system_info_timer = QTimer(self)
        self.system_info_timer.timeout.connect(self._update_system_info)
        self.system_info_timer.start(5000)  # 每5秒更新一次

    def _update_system_info(self):
        """更新系统信息显示"""
        try:
            import psutil

            # 更新CPU使用率
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.cpu_usage_label.setText(f"CPU: {cpu_percent:.1f}%")

            # 更新内存使用率
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            self.memory_usage_label.setText(f"内存: {memory_mb:.1f}MB")

        except ImportError:
            # 如果没有psutil，就隐藏这些标签
            self.cpu_usage_label.hide()
            self.memory_usage_label.hide()
        except Exception:
            # 发生错误，隐藏这些标签
            self.cpu_usage_label.hide()
            self.memory_usage_label.hide()

    def _connect_signals(self):
        """连接信号和槽"""
        # 任务管理器信号
        pass

    def _setup_auto_save(self):
        """设置自动保存定时器"""
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.timeout.connect(self.auto_save)
        self.auto_save_timer.start(60000)  # 每分钟保存一次

    def _update_ui(self):
        """更新UI状态"""
        # 更新任务列表
        self.task_manager.update_tasks(self.download_manager.tasks)

        # 更新状态栏
        active_count = len(self.download_manager.active_tasks)
        total_count = len(self.download_manager.tasks)

        # 更新活动任务标签
        self.active_tasks_label.setText(f"活动任务: {active_count}/{total_count}")

        # 更新状态指示器
        if active_count > 0:
            # 有活动任务时为蓝色
            self.status_indicator.setStyleSheet(
                "background-color: #0078d4; border-radius: 6px;")
            self.task_status_label.setText("正在下载")
        elif total_count > 0:
            # 有任务但没有活动任务为黄色
            self.status_indicator.setStyleSheet(
                "background-color: #ffb900; border-radius: 6px;")
            self.task_status_label.setText("已暂停")
        else:
            # 无任务为绿色
            self.status_indicator.setStyleSheet(
                "background-color: #00b050; border-radius: 6px;")
            self.task_status_label.setText("就绪")

    def auto_save(self):
        """自动保存状态"""
        # 保存所有任务进度
        for task in self.download_manager.tasks.values():
            task.save_progress()

    def closeEvent(self, event):
        """窗口关闭事件处理"""
        if self.app.tray_icon and self.settings.get("ui", "minimize_to_tray", False) and not self._force_close:
            event.ignore()
            self.hide()

            # 显示通知
            if self.settings.get("ui", "show_notifications", True):
                self.app.tray_icon.show_notification(
                    "加密视频下载器",
                    "程序已最小化到系统托盘，点击图标可恢复窗口。"
                )
            return

        # 检查是否有活动任务
        active_tasks = []
        for task in self.download_manager.tasks.values():
            if task.status in [task.status.RUNNING, task.status.PAUSED]:
                active_tasks.append(task)

        if active_tasks and self.settings.get("ui", "confirm_on_exit", True):
            result = QMessageBox.question(
                self,
                "确认退出",
                f"还有 {len(active_tasks)} 个任务正在进行中，确定要退出吗？\n(任务将被暂停，进度会被保存)",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if result == QMessageBox.No:
                event.ignore()
                return

        # 停止下载管理器
        self.download_manager.stop()

        # 保存窗口状态
        self.settings.set("ui", "window_geometry",
                          self.saveGeometry().toBase64().data().decode())
        self.settings.set("ui", "window_state",
                          self.saveState().toBase64().data().decode())
        self.settings.save_settings()

        # 继续关闭窗口
        event.accept()

    @Slot()
    def show_new_task_dialog(self):
        """显示新建任务对话框"""
        dialog = TaskDialog(self.settings, parent=self)

        if dialog.exec():
            # 获取任务参数
            task_data = dialog.get_task_data()

            # 创建下载任务
            from src.core.downloader import DownloadTask, TaskPriority

            priority_map = {
                "high": TaskPriority.HIGH,
                "normal": TaskPriority.NORMAL,
                "low": TaskPriority.LOW
            }

            task = DownloadTask(
                name=task_data["name"],
                base_url=task_data["base_url"],
                key_url=task_data["key_url"],
                segments=task_data["segments"],
                output_file=task_data["output_file"],
                settings=self.settings,
                priority=priority_map.get(
                    task_data["priority"], TaskPriority.NORMAL)
            )

            # 添加到下载管理器
            self.download_manager.add_task(task)

            # 如果设置了自动开始，立即启动任务
            if task_data["auto_start"]:
                self.download_manager.start_task(task.task_id)

            # 更新UI
            self._update_ui()

    @Slot()
    def import_from_url(self):
        """从URL导入任务"""
        # 这里简化处理，实际应用中需要解析URL提取M3U8和密钥信息
        # 可以选择URL后识别或手动输入
        QMessageBox.information(self, "信息", "此功能尚未实现")

    @Slot()
    def show_settings(self):
        """显示设置对话框"""
        dialog = SettingsDialog(self.settings, parent=self)

        if dialog.exec():
            # 设置已更新，刷新UI
            self._update_ui()

    @Slot()
    def show_about(self):
        """显示关于对话框"""
        dialog = AboutDialog(parent=self)
        dialog.exec()

    @Slot(str, str)
    def handle_task_action(self, task_id, action):
        """处理任务操作"""
        if action == "start":
            self.download_manager.start_task(task_id)
        elif action == "pause":
            self.download_manager.pause_task(task_id)
        elif action == "resume":
            self.download_manager.resume_task(task_id)
        elif action == "cancel":
            self.download_manager.cancel_task(task_id)
        elif action == "remove":
            self.download_manager.remove_task(task_id)
        elif action == "remove_with_file":
            self.download_manager.remove_task(task_id, delete_files=True)

        # 更新UI
        self._update_ui()

    @Slot()
    def start_all_tasks(self):
        """开始所有待处理任务"""
        for task_id, task in self.download_manager.tasks.items():
            if task.status in [task.status.PENDING, task.status.PAUSED]:
                self.download_manager.start_task(task_id)

        # 更新UI
        self._update_ui()

    @Slot()
    def pause_all_tasks(self):
        """暂停所有运行中的任务"""
        for task_id, task in self.download_manager.tasks.items():
            if task.status == task.status.RUNNING:
                self.download_manager.pause_task(task_id)

        # 更新UI
        self._update_ui()

    @Slot()
    def clear_completed_tasks(self):
        """清除所有已完成的任务"""
        task_ids = list(self.download_manager.tasks.keys())

        for task_id in task_ids:
            task = self.download_manager.tasks.get(task_id)
            if task and task.status in [task.status.COMPLETED, task.status.FAILED, task.status.CANCELED]:
                self.download_manager.remove_task(task_id)

        # 更新UI
        self._update_ui()

    @Slot(str, dict)
    def on_task_progress(self, task_id, progress):
        """处理任务进度更新"""
        # 更新任务管理器UI
        self.task_manager.update_task_progress(task_id, progress)

        # 更新状态栏
        total_speed = sum(task.progress.get("speed", 0) for task in self.download_manager.tasks.values(
        ) if task.status == task.status.RUNNING)
        self.speed_label.setText(self._format_speed(total_speed))

    @Slot(str, object, object)
    def on_task_status_changed(self, task_id, old_status, new_status):
        """处理任务状态变化"""
        # 更新任务管理器UI
        self.task_manager.update_task_status(task_id, new_status)

        # 更新状态栏
        active_count = len(self.download_manager.active_tasks)
        total_count = len(self.download_manager.tasks)
        self.task_status_label.setText(f"活动任务: {active_count}/{total_count}")

        # 发送系统通知
        if self.settings.get("ui", "show_notifications", True):
            task = self.download_manager.get_task(task_id)
            if task:
                if new_status == task.status.RUNNING and old_status != task.status.PAUSED:
                    self.app.send_notification(
                        "任务开始", f"任务 \"{task.name}\" 已开始下载")
                elif new_status == task.status.PAUSED:
                    self.app.send_notification(
                        "任务暂停", f"任务 \"{task.name}\" 已暂停")
                elif new_status == task.status.COMPLETED:
                    self.app.send_notification(
                        "任务完成", f"任务 \"{task.name}\" 已成功完成")
                elif new_status == task.status.FAILED:
                    self.app.send_notification(
                        "任务失败", f"任务 \"{task.name}\" 下载失败")
                elif new_status == task.status.CANCELED:
                    self.app.send_notification(
                        "任务取消", f"任务 \"{task.name}\" 已取消")

    @Slot(str, str)
    def on_task_completed(self, task_id, message):
        """处理任务完成"""
        # 记录日志
        logger.info(f"任务完成: {message}")
        self.log_viewer.add_log_entry(f"任务完成: {message}")

        # 更新UI
        self._update_ui()

    @Slot(str, str)
    def on_task_failed(self, task_id, message):
        """处理任务失败"""
        # 记录日志
        logger.error(f"任务失败: {message}")
        self.log_viewer.add_log_entry(f"任务失败: {message}", error=True)

        # 更新UI
        self._update_ui()

    def _format_speed(self, bytes_per_second):
        """格式化速度显示"""
        if bytes_per_second < 1024:
            return f"{bytes_per_second:.1f} B/s"
        elif bytes_per_second < 1024 * 1024:
            return f"{bytes_per_second / 1024:.1f} KB/s"
        else:
            return f"{bytes_per_second / (1024 * 1024):.2f} MB/s"

    @Slot()
    def import_batch_urls(self):
        """批量导入URL"""
        from src.gui.dialogs.batch_url_dialog import BatchURLDialog

        dialog = BatchURLDialog(self.settings, parent=self)
        dialog.urls_imported.connect(self._handle_batch_urls)

        dialog.exec()

    @Slot(list)
    def _handle_batch_urls(self, urls):
        """处理批量导入的URL"""
        if not urls:
            return

        # 询问是否自动解析
        result = QMessageBox.question(
            self,
            "URL处理",
            f"已导入 {len(urls)} 个URL，是否尝试自动解析为下载任务？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if result == QMessageBox.Yes:
            # 显示进度对话框
            from PySide6.QtWidgets import QProgressDialog
            progress = QProgressDialog("正在解析URL...", "取消", 0, len(urls), self)
            progress.setWindowTitle("解析中")
            progress.setMinimumDuration(0)
            progress.setModal(True)
            progress.show()

            # 解析URL并创建任务
            successful = 0
            for i, url in enumerate(urls):
                progress.setValue(i)
                progress.setLabelText(f"正在解析 URL {i+1}/{len(urls)}")

                if progress.wasCanceled():
                    break

                try:
                    # 尝试解析URL
                    from src.core.m3u8_parser import extract_m3u8_info

                    # 获取用户代理设置
                    user_agent = self.settings.get(
                        "advanced", "user_agent", "")
                    headers = {
                        "User-Agent": user_agent} if user_agent else None

                    # 提取信息
                    result = extract_m3u8_info(url, headers)

                    if result["success"]:
                        # 创建下载任务
                        from src.core.downloader import DownloadTask, TaskPriority

                        # 生成任务名称
                        from urllib.parse import urlparse
                        from os.path import basename, join

                        parsed_url = urlparse(url)
                        path = parsed_url.path
                        name = basename(path)
                        if name:
                            name = name.split(".")[0]  # 移除扩展名
                        else:
                            name = f"Task-{i+1}"

                        # 生成输出文件名
                        output_dir = self.settings.get(
                            "general", "output_directory", "")
                        output_file = join(output_dir, f"{name}.mp4")

                        # 创建任务
                        task = DownloadTask(
                            name=name,
                            base_url=result["base_url"],
                            key_url=result["key_url"],
                            segments=result["segments"],
                            output_file=output_file,
                            settings=self.settings,
                            priority=TaskPriority.NORMAL
                        )

                        # 添加到下载管理器
                        self.download_manager.add_task(task)

                        # 自动开始任务
                        self.download_manager.start_task(task.task_id)

                        successful += 1

                except Exception as e:
                    logger.error(f"解析URL出错: {url}, 错误: {e}")
                    continue

            progress.setValue(len(urls))

            # 更新UI
            self._update_ui()

            # 显示结果
            QMessageBox.information(
                self,
                "导入结果",
                f"成功导入 {successful} 个任务，失败 {len(urls) - successful} 个。"
            )

        else:
            # 将URL复制到剪贴板
            clipboard = QApplication.clipboard()
            clipboard.setText("\n".join(urls))

            QMessageBox.information(
                self,
                "URL已复制",
                f"{len(urls)} 个URL已复制到剪贴板。"
            )

    @Slot()
    def show_media_processing(self):
        """显示媒体处理对话框"""
        from src.gui.dialogs.media_processing_dialog import MediaProcessingDialog

        # 获取选中的任务
        selected_file = None
        selected_rows = self.task_manager.get_selected_rows()
        if selected_rows:
            task_id = selected_rows[0]
            task = self.download_manager.get_task(task_id)
            if task and task.status == task.status.COMPLETED and task.output_file:
                selected_file = task.output_file

        # 创建并显示对话框
        dialog = MediaProcessingDialog(
            self.settings, selected_file, parent=self)
        dialog.processing_completed.connect(
            self._on_media_processing_completed)

        dialog.exec()

    @Slot()
    def show_batch_conversion(self):
        """显示批量转换对话框"""
        QMessageBox.information(self, "功能提示", "批量转换功能正在开发中，敬请期待！")

    @Slot(bool, str)
    def _on_media_processing_completed(self, success, message):
        """媒体处理完成回调"""
        if success:
            self.log_viewer.add_log_entry(message)

            # 发送通知
            if self.settings.get("ui", "show_notifications", True):
                self.app.send_notification("媒体处理", "媒体处理已完成")
        else:
            self.log_viewer.add_log_entry(message, error=True)
