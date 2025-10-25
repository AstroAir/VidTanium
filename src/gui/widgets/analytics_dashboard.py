"""
Analytics Dashboard Widget for VidTanium
Displays comprehensive analytics including ETA, bandwidth usage, and download statistics
"""

import time
from typing import Dict, List, Optional, Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QProgressBar, QFrame, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve, QByteArray
from PySide6.QtGui import QPainter, QPainterPath, QColor, QLinearGradient, QFont

from qfluentwidgets import (
    FluentIcon as FIF, ProgressRing, ProgressBar,
    TitleLabel, SubtitleLabel, BodyLabel, CaptionLabel, StrongBodyLabel,
    ElevatedCardWidget, ScrollArea,
    TransparentToolButton, PushButton
)

from ..utils.i18n import tr
from ..utils.formatters import format_size, format_speed, format_duration
from ...core.eta_calculator import ETAResult, ETAAlgorithm
from ...core.bandwidth_monitor import BandwidthStats, OptimizationRecommendation
from ...core.download_history_manager import HistoryStatistics


class MetricCard(ElevatedCardWidget):
    """Card displaying a single metric with trend indicator"""
    
    def __init__(self, title: str, icon: str, parent=None) -> None:
        super().__init__(parent)
        self.title = title
        self.icon_name = icon
        self.current_value = "0"
        self.trend = "stable"  # "up", "down", "stable"
        self.trend_percentage = 0.0
        
        self._setup_ui()
        self._setup_animations()
    
    def _setup_ui(self) -> None:
        """Setup the UI components"""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 12, 16, 12)

        # Header with icon and title
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        # Icon
        self.icon_label = QLabel()
        icon = getattr(FIF, self.icon_name.upper(), FIF.INFO)
        self.icon_label.setPixmap(icon.icon().pixmap(20, 20))
        header_layout.addWidget(self.icon_label)
        
        # Title
        title_label = CaptionLabel(self.title)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Trend indicator
        self.trend_label = CaptionLabel("")
        header_layout.addWidget(self.trend_label)
        
        layout.addLayout(header_layout)
        
        # Value
        self.value_label = SubtitleLabel(self.current_value)
        self.value_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 18px;
            }
        """)
        layout.addWidget(self.value_label)
    
    def _setup_animations(self) -> None:
        """Setup value change animations"""
        self.value_animation = QPropertyAnimation(self.value_label, QByteArray(b"geometry"))
        self.value_animation.setDuration(300)
        self.value_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    
    def update_value(self, value: str, trend: str = "stable", trend_percentage: float = 0.0) -> None:
        """Update metric value with trend"""
        self.current_value = value
        self.trend = trend
        self.trend_percentage = trend_percentage
        
        # Update value label
        self.value_label.setText(value)
        
        # Update trend indicator
        if trend == "up":
            self.trend_label.setText(f"↑ {trend_percentage:.1f}%")
            self.trend_label.setObjectName("trend-up")
        elif trend == "down":
            self.trend_label.setText(f"↓ {trend_percentage:.1f}%")
            self.trend_label.setObjectName("trend-down")
        else:
            self.trend_label.setText("—")
            self.trend_label.setObjectName("trend-stable")
        
        # Trigger animation
        self._animate_value_change()
    
    def _animate_value_change(self) -> None:
        """Animate value change"""
        # Simple scale animation
        original_geometry = self.value_label.geometry()
        self.value_animation.setStartValue(original_geometry)
        self.value_animation.setEndValue(original_geometry)
        self.value_animation.start()


class ETADisplayWidget(ElevatedCardWidget):
    """Widget displaying ETA information with confidence indicator"""
    
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.current_eta: Optional[ETAResult] = None
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup the UI components"""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 12, 16, 12)

        # Header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        icon_label = QLabel()
        icon_label.setPixmap(FIF.CLOCK.icon().pixmap(20, 20))
        header_layout.addWidget(icon_label)
        
        title_label = BodyLabel(tr("analytics.eta_title"))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # ETA display
        self.eta_label = TitleLabel("--")
        self.eta_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 24px;
            }
        """)
        layout.addWidget(self.eta_label)
        
        # Confidence and algorithm info
        info_layout = QHBoxLayout()
        info_layout.setSpacing(16)

        # Confidence indicator
        confidence_layout = QVBoxLayout()
        confidence_layout.setSpacing(4)
        
        confidence_title = CaptionLabel(tr("analytics.confidence"))
        confidence_layout.addWidget(confidence_title)
        
        self.confidence_bar = ProgressBar()
        self.confidence_bar.setFixedHeight(6)
        self.confidence_bar.setRange(0, 100)
        confidence_layout.addWidget(self.confidence_bar)
        
        info_layout.addLayout(confidence_layout)
        
        # Algorithm info
        algorithm_layout = QVBoxLayout()
        algorithm_layout.setSpacing(4)
        
        algorithm_title = CaptionLabel(tr("analytics.algorithm"))
        algorithm_layout.addWidget(algorithm_title)
        
        self.algorithm_label = CaptionLabel("--")
        algorithm_layout.addWidget(self.algorithm_label)
        
        info_layout.addLayout(algorithm_layout)
        
        # Speed trend
        trend_layout = QVBoxLayout()
        trend_layout.setSpacing(4)
        
        trend_title = CaptionLabel(tr("analytics.speed_trend"))
        trend_layout.addWidget(trend_title)
        
        self.trend_label = CaptionLabel("--")
        trend_layout.addWidget(self.trend_label)
        
        info_layout.addLayout(trend_layout)
        
        layout.addLayout(info_layout)
    
    def update_eta(self, eta_result: Optional[ETAResult]) -> None:
        """Update ETA display"""
        self.current_eta = eta_result
        
        if not eta_result:
            self.eta_label.setText("--")
            self.confidence_bar.setValue(0)
            self.algorithm_label.setText("--")
            self.trend_label.setText("--")
            return
        
        # Format ETA
        if eta_result.eta_seconds == float('inf'):
            eta_text = tr("analytics.eta_unknown")
        else:
            eta_text = format_duration(eta_result.eta_seconds)
        
        self.eta_label.setText(eta_text)
        
        # Update confidence
        confidence_percentage = int(eta_result.confidence * 100)
        self.confidence_bar.setValue(confidence_percentage)
        
        # Set confidence bar - let qfluentwidgets handle color
        # Higher confidence values will be shown with progress bar styling
        
        # Update algorithm
        algorithm_names = {
            ETAAlgorithm.SIMPLE_LINEAR: tr("analytics.algorithm_simple"),
            ETAAlgorithm.EXPONENTIAL_SMOOTHING: tr("analytics.algorithm_exponential"),
            ETAAlgorithm.WEIGHTED_AVERAGE: tr("analytics.algorithm_weighted"),
            ETAAlgorithm.ADAPTIVE_HYBRID: tr("analytics.algorithm_adaptive"),
            ETAAlgorithm.REGRESSION_BASED: tr("analytics.algorithm_regression")
        }
        self.algorithm_label.setText(algorithm_names.get(eta_result.algorithm_used, "Unknown"))
        
        # Update trend with semantic object name
        trend_text = tr(f"analytics.trend_{eta_result.speed_trend}")
        
        self.trend_label.setText(trend_text)
        self.trend_label.setObjectName(f"trend-{eta_result.speed_trend}")


class BandwidthAnalyticsWidget(ElevatedCardWidget):
    """Widget displaying bandwidth analytics and optimization suggestions"""
    
    optimization_requested = Signal(str, dict)  # suggestion_type, metadata
    
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.current_stats: Optional[BandwidthStats] = None
        self.recommendations: List[OptimizationRecommendation] = []
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup the UI components"""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 12, 16, 12)

        # Header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        icon_label = QLabel()
        icon_label.setPixmap(FIF.SPEED_HIGH.icon().pixmap(20, 20))
        header_layout.addWidget(icon_label)
        
        title_label = BodyLabel(tr("analytics.bandwidth_title"))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Metrics grid
        metrics_layout = QGridLayout()
        metrics_layout.setSpacing(8)
        
        # Current speed
        self.current_speed_card = MetricCard(tr("analytics.current_speed"), "SPEED_HIGH")
        metrics_layout.addWidget(self.current_speed_card, 0, 0)
        
        # Average speed
        self.avg_speed_card = MetricCard(tr("analytics.average_speed"), "SPEED_MEDIUM")
        metrics_layout.addWidget(self.avg_speed_card, 0, 1)
        
        # Utilization
        self.utilization_card = MetricCard(tr("analytics.utilization"), "CHART")
        metrics_layout.addWidget(self.utilization_card, 1, 0)
        
        # Efficiency
        self.efficiency_card = MetricCard(tr("analytics.efficiency"), "PERFORMANCE")
        metrics_layout.addWidget(self.efficiency_card, 1, 1)
        
        layout.addLayout(metrics_layout)
        
        # Optimization suggestions
        self.suggestions_widget = QWidget()
        suggestions_layout = QVBoxLayout(self.suggestions_widget)
        suggestions_layout.setSpacing(8)
        suggestions_layout.setContentsMargins(0, 8, 0, 0)
        
        suggestions_title = CaptionLabel(tr("analytics.optimization_suggestions"))
        suggestions_layout.addWidget(suggestions_title)
        
        self.suggestions_container = QWidget()
        self.suggestions_container_layout = QVBoxLayout(self.suggestions_container)
        self.suggestions_container_layout.setSpacing(4)
        self.suggestions_container_layout.setContentsMargins(0, 0, 0, 0)
        suggestions_layout.addWidget(self.suggestions_container)
        
        self.suggestions_widget.setVisible(False)
        layout.addWidget(self.suggestions_widget)
    
    def update_bandwidth_stats(self, stats: Optional[BandwidthStats]) -> None:
        """Update bandwidth statistics display"""
        self.current_stats = stats
        
        if not stats:
            self.current_speed_card.update_value("--")
            self.avg_speed_card.update_value("--")
            self.utilization_card.update_value("--")
            self.efficiency_card.update_value("--")
            return
        
        # Update metric cards
        self.current_speed_card.update_value(format_speed(stats.current_download_speed))
        self.avg_speed_card.update_value(format_speed(stats.average_download_speed))
        self.utilization_card.update_value(f"{stats.utilization_percentage:.1f}%")
        self.efficiency_card.update_value(f"{stats.efficiency_ratio * 100:.1f}%")
    
    def update_optimization_suggestions(self, recommendations: List[OptimizationRecommendation]) -> None:
        """Update optimization suggestions"""
        self.recommendations = recommendations
        
        # Clear existing suggestions
        for i in reversed(range(self.suggestions_container_layout.count())):
            child = self.suggestions_container_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        if not recommendations:
            self.suggestions_widget.setVisible(False)
            return
        
        # Add new suggestions
        for recommendation in recommendations[:3]:  # Show top 3 suggestions
            suggestion_widget = self._create_suggestion_widget(recommendation)
            self.suggestions_container_layout.addWidget(suggestion_widget)
        
        self.suggestions_widget.setVisible(True)
    
    def _create_suggestion_widget(self, recommendation: OptimizationRecommendation) -> QWidget:
        """Create widget for optimization suggestion"""
        widget = QFrame()
        widget.setObjectName("suggestion-frame")
        
        layout = QHBoxLayout(widget)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 6, 8, 6)
        
        # Priority indicator
        priority_label = QLabel("●")
        priority_label.setObjectName(f"priority-{recommendation.priority}")
        priority_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                font-weight: bold;
            }
        """)
        layout.addWidget(priority_label)
        
        # Description
        desc_label = CaptionLabel(recommendation.description)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Action button
        if recommendation.implementation_difficulty == "easy":
            action_button = PushButton(tr("analytics.apply"))
            action_button.setFixedSize(60, 24)
            action_button.clicked.connect(
                lambda: self.optimization_requested.emit(
                    recommendation.suggestion.value,
                    recommendation.metadata
                )
            )
            layout.addWidget(action_button)
        
        return widget


class AnalyticsDashboard(ScrollArea):
    """Main analytics dashboard widget"""
    
    optimization_requested = Signal(str, dict)
    
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Create main widget
        main_widget = QWidget()
        self.setWidget(main_widget)
        
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Title
        title_label = TitleLabel(tr("analytics.dashboard_title"))
        layout.addWidget(title_label)
        
        # ETA widget
        self.eta_widget = ETADisplayWidget()
        layout.addWidget(self.eta_widget)
        
        # Bandwidth analytics widget
        self.bandwidth_widget = BandwidthAnalyticsWidget()
        self.bandwidth_widget.optimization_requested.connect(self.optimization_requested.emit)
        layout.addWidget(self.bandwidth_widget)
        
        # History statistics (placeholder for now)
        self.history_stats_widget = ElevatedCardWidget()
        history_layout = QVBoxLayout(self.history_stats_widget)
        history_layout.setContentsMargins(16, 12, 16, 12)
        
        history_title = BodyLabel(tr("analytics.history_stats_title"))
        history_layout.addWidget(history_title)
        
        self.history_summary_label = BodyLabel(tr("analytics.history_loading"))
        history_layout.addWidget(self.history_summary_label)
        
        layout.addWidget(self.history_stats_widget)
        
        layout.addStretch()
    
    def update_eta(self, eta_result: Optional[ETAResult]) -> None:
        """Update ETA display"""
        self.eta_widget.update_eta(eta_result)
    
    def update_bandwidth_stats(self, stats: Optional[BandwidthStats]) -> None:
        """Update bandwidth statistics"""
        self.bandwidth_widget.update_bandwidth_stats(stats)
    
    def update_optimization_suggestions(self, recommendations: List[OptimizationRecommendation]) -> None:
        """Update optimization suggestions"""
        self.bandwidth_widget.update_optimization_suggestions(recommendations)
    
    def update_history_stats(self, stats: HistoryStatistics) -> None:
        """Update history statistics summary"""
        summary_text = tr("analytics.history_summary").format(
            total=stats.total_downloads,
            success_rate=stats.success_rate,
            total_data=format_size(stats.total_data_downloaded)
        )
        self.history_summary_label.setText(summary_text)
