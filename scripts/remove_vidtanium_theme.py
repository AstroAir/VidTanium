#!/usr/bin/env python3
"""
批量移除 VidTaniumTheme 引用的脚本
用于快速优化剩余组件
"""

import re
from pathlib import Path
from typing import List, Tuple

# 需要处理的文件列表
FILES_TO_PROCESS = [
    "src/gui/widgets/analytics_dashboard.py",
    "src/gui/widgets/log/log_viewer.py",
    "src/gui/widgets/status_widget.py",
    "src/gui/widgets/schedule_manager.py",
    "src/gui/widgets/dashboard/task_preview.py",
    "src/gui/widgets/tooltip.py",
    "src/gui/widgets/dashboard/system_status.py",
    "src/gui/widgets/bulk_operations_manager.py",
    "src/gui/dialogs/task_dialog.py",
    "src/gui/widgets/dashboard/stats_section.py",
    "src/gui/widgets/dashboard/dashboard_interface.py",
    "src/gui/widgets/dashboard/hero_section.py",
]

def remove_vidtanium_theme_import(content: str) -> str:
    """移除 VidTaniumTheme 导入"""
    patterns = [
        r'from \.\.utils\.theme import VidTaniumTheme\n',
        r'from \.\.\.utils\.theme import VidTaniumTheme\n',
        r'from ..utils.theme import VidTaniumTheme, .*\n',
    ]
    
    for pattern in patterns:
        content = re.sub(pattern, '', content)
    
    return content

def add_qconfig_import(content: str) -> str:
    """添加 qconfig 导入（如果需要）"""
    # 检查是否已有 qfluentwidgets 导入
    if 'from qfluentwidgets import' in content:
        # 在 qfluentwidgets 导入行添加 qconfig
        if 'qconfig' not in content:
            content = content.replace(
                'from qfluentwidgets import (',
                'from qfluentwidgets import (\n    qconfig,'
            )
    return content

def replace_color_references(content: str) -> str:
    """替换颜色引用"""
    # 移除简单的颜色设置
    content = re.sub(
        r'\.setStyleSheet\(f?["\']color:\s*\{VidTaniumTheme\.\w+\};?["\']\)',
        '',
        content
    )
    
    # 移除带有 VidTaniumTheme 的复杂 setStyleSheet
    # 这需要手动处理复杂情况
    
    return content

def remove_theme_colors(content: str) -> str:
    """移除主题颜色常量的使用"""
    # 替换常见的主题颜色
    replacements = [
        # 简单替换模式
        (r'\{VidTaniumTheme\.TEXT_PRIMARY\}', ''),
        (r'\{VidTaniumTheme\.TEXT_SECONDARY\}', ''),
        (r'\{VidTaniumTheme\.TEXT_TERTIARY\}', ''),
        (r'VidTaniumTheme\.TEXT_PRIMARY', ''),
        (r'VidTaniumTheme\.TEXT_SECONDARY', ''),
        (r'VidTaniumTheme\.BG_PRIMARY', ''),
        (r'VidTaniumTheme\.BG_SURFACE', ''),
        (r'VidTaniumTheme\.BORDER_COLOR', ''),
    ]
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    return content

def process_file(file_path: Path) -> Tuple[bool, str]:
    """处理单个文件"""
    try:
        if not file_path.exists():
            return False, f"File not found: {file_path}"
        
        content = file_path.read_text(encoding='utf-8')
        
        # 检查是否需要处理
        if 'VidTaniumTheme' not in content:
            return False, f"No VidTaniumTheme found in: {file_path}"
        
        original_count = content.count('VidTaniumTheme')
        
        # 应用转换
        content = remove_vidtanium_theme_import(content)
        content = remove_theme_colors(content)
        content = replace_color_references(content)
        
        # 保存
        file_path.write_text(content, encoding='utf-8')
        
        new_count = content.count('VidTaniumTheme')
        removed = original_count - new_count
        
        return True, f"Processed: {file_path.name} (Removed {removed}/{original_count} references)"
        
    except Exception as e:
        return False, f"Error processing {file_path}: {e}"

def main():
    """主函数"""
    print("VidTaniumTheme 批量移除工具")
    print("=" * 50)
    
    project_root = Path(__file__).parent.parent
    processed = 0
    failed = 0
    
    for file_path_str in FILES_TO_PROCESS:
        file_path = project_root / file_path_str
        success, message = process_file(file_path)
        
        print(message)
        
        if success:
            processed += 1
        else:
            failed += 1
    
    print("=" * 50)
    print(f"完成！处理: {processed}, 失败: {failed}")
    print("\n注意：此脚本只处理简单情况，复杂的样式表需要手动优化")

if __name__ == "__main__":
    main()
