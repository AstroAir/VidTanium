#!/usr/bin/env python3
"""
脚本用于批量重命名所有带有Enhanced前缀的组件引用
"""
import os
import re
from pathlib import Path

# 定义重命名映射
RENAME_MAP = {
    # 类名重命名
    "EnhancedEvent": "Event",
    "EnhancedEventSystem": "EventSystem",
    "EnhancedThemeSystem": "ThemeSystem",
    "EnhancedThemeManager": "ThemeManager",
    "EnhancedTaskItem": "TaskItem",
    "EnhancedSystemTrayIcon": "SystemTrayIcon",
    "EnhancedScheduleManager": "ScheduleManager",
    "EnhancedLogViewer": "LogViewer",
    "EnhancedLogEntry": "LogEntry",
    "EnhancedPaginatedLogContainer": "PaginatedLogContainer",
    "EnhancedInputDialog": "InputDialog",
    "EnhancedDashboardSystemStatus": "DashboardSystemStatus",
    "EnhancedDashboardStatsSection": "DashboardStatsSection",
    "EnhancedDashboardHeroSection": "DashboardHeroSection",
    "EnhancedDashboardInterface": "DashboardInterface",
    "EnhancedFluentProgressBar": "FluentProgressBar",
    "EnhancedProgressCard": "ProgressCard",
    "EnhancedTaskDialog": "TaskDialog",
    "EnhancedSettingsDialog": "SettingsDialog",
    "EnhancedErrorHandler": "ErrorHandler",
    "EnhancedHTTPAdapter": "HTTPAdapter",
    "EnhancedDesignSystem": "DesignSystem",
    "EnhancedTooltip": "Tooltip",
    
    # 函数名重命名
    "emit_enhanced_event": "emit_event",
    "get_enhanced_event_system": "get_event_system",
}

def process_file(filepath: Path) -> tuple[int, list[str]]:
    """处理单个文件，返回修改次数和修改详情"""
    if not filepath.suffix == ".py":
        return 0, []
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"无法读取 {filepath}: {e}")
        return 0, []
    
    original_content = content
    changes = []
    
    for old_name, new_name in RENAME_MAP.items():
        # 使用正则确保只替换完整的标识符
        pattern = r'\b' + re.escape(old_name) + r'\b'
        matches = re.findall(pattern, content)
        if matches:
            content = re.sub(pattern, new_name, content)
            changes.append(f"  {old_name} -> {new_name} ({len(matches)}次)")
    
    if content != original_content:
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            return len(changes), changes
        except Exception as e:
            print(f"无法写入 {filepath}: {e}")
            return 0, []
    
    return 0, []

def main():
    """主函数"""
    src_dir = Path(__file__).parent / "src"
    tests_dir = Path(__file__).parent / "tests"
    
    total_files = 0
    total_changes = 0
    
    print("开始批量重命名Enhanced组件...")
    print("=" * 80)
    
    for directory in [src_dir, tests_dir]:
        if not directory.exists():
            continue
            
        for filepath in directory.rglob("*.py"):
            change_count, changes = process_file(filepath)
            if change_count > 0:
                total_files += 1
                total_changes += change_count
                print(f"\n修改文件: {filepath.relative_to(Path(__file__).parent)}")
                for change in changes:
                    print(change)
    
    print("\n" + "=" * 80)
    print(f"完成! 共修改 {total_files} 个文件，{total_changes} 处更改")

if __name__ == "__main__":
    main()
