from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFileDialog, QFormLayout,
    QDialogButtonBox, QMessageBox, QProgressDialog, QWidget
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QIcon
import os

from qfluentwidgets import (
    PushButton, LineEdit, CheckBox, SpinBox, ComboBox,
    CardWidget, StrongBodyLabel, InfoBar, InfoBarPosition,
    SimpleCardWidget, SubtitleLabel, FluentIcon
)


class TaskDialog(QDialog):
    """新建任务对话框"""

    def __init__(self, settings, parent=None):
        super().__init__(parent)

        self.settings = settings

        self.setWindowTitle("新建下载任务")
        self.setMinimumSize(550, 480)
        self.resize(550, 480)
        self.setWindowIcon(FluentIcon.DOWNLOAD.icon())

        self._create_ui()

    def _create_ui(self):
        """创建界面"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 15, 20, 15)
        main_layout.setSpacing(15)

        # 标题
        self.title_label = SubtitleLabel("新建下载任务")
        main_layout.addWidget(self.title_label)

        # 基本信息卡片
        basic_card = CardWidget()
        basic_layout = QFormLayout()
        basic_layout.setContentsMargins(15, 15, 15, 15)
        basic_layout.setSpacing(12)
        basic_layout.setLabelAlignment(Qt.AlignRight)
        basic_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        # 添加卡片标题
        basic_title = StrongBodyLabel("基本信息")
        basic_layout.addRow(basic_title)

        # 任务名称
        self.name_input = LineEdit()
        self.name_input.setPlaceholderText("输入任务名称")
        basic_layout.addRow("任务名称:", self.name_input)

        # 视频基础URL
        url_layout = QHBoxLayout()
        self.base_url_input = LineEdit()
        self.base_url_input.setPlaceholderText("输入视频M3U8地址")
        url_layout.addWidget(self.base_url_input)

        self.extract_button = PushButton("提取")
        self.extract_button.setIcon(FluentIcon.DOWNLOAD)
        self.extract_button.clicked.connect(self._extract_m3u8_info)
        url_layout.addWidget(self.extract_button)

        basic_layout.addRow("视频URL:", url_layout)

        # 密钥URL
        self.key_url_input = LineEdit()
        self.key_url_input.setPlaceholderText("输入视频密钥URL")
        basic_layout.addRow("密钥URL:", self.key_url_input)

        # 视频片段数量
        self.segments_input = SpinBox()
        self.segments_input.setRange(1, 10000)
        self.segments_input.setValue(200)
        basic_layout.addRow("视频片段数量:", self.segments_input)

        # 输出文件
        output_layout = QHBoxLayout()
        self.output_input = LineEdit()
        self.output_input.setPlaceholderText("选择保存位置...")
        output_layout.addWidget(self.output_input)

        self.browse_button = PushButton("浏览...")
        self.browse_button.setIcon(FluentIcon.SAVE)
        self.browse_button.clicked.connect(self._browse_output)
        output_layout.addWidget(self.browse_button)

        basic_layout.addRow("输出文件:", output_layout)

        basic_card.setLayout(basic_layout)
        main_layout.addWidget(basic_card)

        # 高级选项卡片
        advanced_card = CardWidget()
        advanced_layout = QFormLayout()
        advanced_layout.setContentsMargins(15, 15, 15, 15)
        advanced_layout.setSpacing(12)
        advanced_layout.setLabelAlignment(Qt.AlignRight)
        advanced_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        # 添加卡片标题
        advanced_title = StrongBodyLabel("高级选项")
        advanced_layout.addRow(advanced_title)

        # 优先级
        self.priority_combo = ComboBox()
        self.priority_combo.addItem("高", "high")
        self.priority_combo.addItem("中", "normal")
        self.priority_combo.addItem("低", "low")
        self.priority_combo.setCurrentIndex(1)  # 默认选中"中"
        advanced_layout.addRow("任务优先级:", self.priority_combo)

        # 自动开始
        self.auto_start_check = CheckBox("添加后自动开始下载")
        self.auto_start_check.setChecked(True)
        advanced_layout.addRow("", self.auto_start_check)

        advanced_card.setLayout(advanced_layout)
        main_layout.addWidget(advanced_card)

        # 使用标准按钮盒
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.button(QDialogButtonBox.Ok).setText("确定")
        self.button_box.button(QDialogButtonBox.Ok).setIcon(FluentIcon.ACCEPT)
        self.button_box.button(QDialogButtonBox.Cancel).setText("取消")
        self.button_box.button(
            QDialogButtonBox.Cancel).setIcon(FluentIcon.CANCEL)

        # 连接信号
        self.button_box.accepted.connect(self._on_ok)
        self.button_box.rejected.connect(self.reject)

        main_layout.addWidget(self.button_box)

        # 填充默认值
        self._fill_defaults()

    def _fill_defaults(self):
        """填充默认值"""
        # 设置默认的输出目录
        output_dir = self.settings.get("general", "output_directory", "")
        if output_dir and os.path.exists(output_dir):
            self.output_input.setText(os.path.join(output_dir, "output.mp4"))

    def _browse_output(self):
        """浏览输出文件"""
        output_dir = self.settings.get("general", "output_directory", "")
        filename, _ = QFileDialog.getSaveFileName(
            self, "选择输出文件", output_dir, "视频文件 (*.mp4);;所有文件 (*)"
        )

        if filename:
            self.output_input.setText(filename)

            # 更新默认输出目录
            self.settings.set("general", "output_directory",
                              os.path.dirname(filename))

    def _on_ok(self):
        """确定按钮点击"""
        # 验证输入
        if not self.base_url_input.text():
            self._show_error("请输入视频基础URL")
            return

        if not self.key_url_input.text():
            self._show_error("请输入密钥URL")
            return

        if not self.output_input.text():
            self._show_error("请选择输出文件")
            return

        # 创建任务名称（如果未提供）
        if not self.name_input.text():
            filename = os.path.basename(self.output_input.text())
            name = os.path.splitext(filename)[0]
            self.name_input.setText(name)

        # 接受对话框
        self.accept()

    def _show_error(self, message):
        """显示错误消息"""
        QMessageBox.warning(self, "输入错误", message)

    def _extract_m3u8_info(self):
        """从M3U8 URL自动提取信息"""
        url = self.base_url_input.text().strip()
        if not url:
            self._show_error("请输入M3U8 URL")
            return

        # 显示加载对话框
        progress = QProgressDialog("正在分析M3U8...", "取消", 0, 0, self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setWindowTitle("提取中")
        progress.setMinimumDuration(0)
        progress.setValue(0)
        progress.show()

        try:
            # 导入M3U8解析器
            from src.core.m3u8_parser import extract_m3u8_info

            # 获取用户代理设置
            user_agent = self.settings.get("advanced", "user_agent", "")
            headers = {"User-Agent": user_agent} if user_agent else None

            # 提取信息
            result = extract_m3u8_info(url, headers)

            # 关闭进度对话框
            progress.close()

            if not result["success"]:
                self._show_error(f"提取失败: {result['message']}")
                return

            # 填充表单
            if result["base_url"]:
                self.base_url_input.setText(result["base_url"])

            if result["key_url"]:
                self.key_url_input.setText(result["key_url"])

            if result["segments"]:
                self.segments_input.setValue(result["segments"])

            # 如果没有提供任务名称，从URL创建一个
            if not self.name_input.text():
                from urllib.parse import urlparse
                from os.path import basename

                parsed_url = urlparse(url)
                path = parsed_url.path
                name = basename(path)
                if name:
                    name = name.split(".")[0]  # 移除扩展名
                    self.name_input.setText(name)

            # 显示提取结果
            QMessageBox.information(
                self,
                "提取成功",
                f"成功提取M3U8信息:\n"
                f"- 分辨率: {result['selected_stream']['resolution'] if 'resolution' in result['selected_stream'] else '未知'}\n"
                f"- 片段数: {result['segments']}\n"
                f"- 时长: {int(result['duration'])}秒\n"
                f"- 加密方式: {result['encryption']}"
            )

        except Exception as e:
            progress.close()
            import traceback
            self._show_error(f"提取过程出错: {str(e)}\n{traceback.format_exc()}")

    def get_task_data(self):
        """获取任务数据"""
        return {
            "name": self.name_input.text(),
            "base_url": self.base_url_input.text(),
            "key_url": self.key_url_input.text(),
            "segments": self.segments_input.value(),
            "output_file": self.output_input.text(),
            "priority": self.priority_combo.currentData(),
            "auto_start": self.auto_start_check.isChecked()
        }
