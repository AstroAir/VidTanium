"""
Dashboard widgets package
"""

from .dashboard_interface import DashboardInterface
from .hero_section import DashboardHeroSection
from .stats_section import DashboardStatsSection
from .task_preview import DashboardTaskPreview
from .system_status import DashboardSystemStatus

__all__ = [
    'DashboardInterface',
    'DashboardHeroSection', 
    'DashboardStatsSection',
    'DashboardTaskPreview',
    'DashboardSystemStatus'
]
