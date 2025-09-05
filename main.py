#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import logging
import argparse
from pathlib import Path
from typing import Optional

from src.app.application import Application
from src.core.singleton_manager import get_singleton_manager
from src.core.ipc_server import IPCClient


def setup_logging(debug: bool = False, log_level: Optional[str] = None) -> None:
    """设置日志系统"""
    if log_level:
        level = getattr(logging, log_level.upper(), logging.INFO)
    else:
        level = logging.DEBUG if debug else logging.INFO

    # 创建日志目录
    log_dir = Path.home() / ".encrypted_video_downloader" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"

    # 配置日志
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    # 减少第三方库的日志级别
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("PySide6").setLevel(logging.WARNING)


def parse_args() -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="VidTanium - 视频下载工具")

    # Basic arguments
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    parser.add_argument("--config-dir", "--config", type=str, help="指定配置目录")
    parser.add_argument("--url", type=str, help="要下载的视频URL")
    parser.add_argument("--allow-multiple", action="store_true", help="允许运行多个应用实例")

    # Enhanced configuration arguments
    parser.add_argument("--preset", type=str, help="使用指定的配置预设")
    parser.add_argument("--log-level", type=str, choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                       help="设置日志级别")
    parser.add_argument("--output-dir", type=str, help="设置下载输出目录")
    parser.add_argument("--max-concurrent", type=int, help="设置最大并发下载数")
    parser.add_argument("--proxy", type=str, help="设置代理服务器")
    parser.add_argument("--theme", type=str, choices=["system", "light", "dark"], help="设置应用主题")
    parser.add_argument("--no-gui", action="store_true", help="以无界面模式运行")

    # Configuration management arguments
    parser.add_argument("--export-config", type=str, help="导出配置到指定文件")
    parser.add_argument("--import-config", type=str, help="从指定文件导入配置")
    parser.add_argument("--validate-config", action="store_true", help="验证配置文件")
    parser.add_argument("--list-presets", action="store_true", help="列出可用的配置预设")
    parser.add_argument("--reset-config", action="store_true", help="重置配置为默认值")
    parser.add_argument("--backup-config", action="store_true", help="创建配置备份")

    # Feature flag arguments
    parser.add_argument("--enable-features", type=str, nargs="+", help="启用指定功能")
    parser.add_argument("--disable-features", type=str, nargs="+", help="禁用指定功能")
    parser.add_argument("--list-features", action="store_true", help="列出所有功能标志")

    # Debug and development arguments
    parser.add_argument("--debug-modules", type=str, nargs="+", help="为指定模块启用调试")
    parser.add_argument("--performance-profile", action="store_true", help="启用性能分析")
    parser.add_argument("--config-report", action="store_true", help="生成配置报告")

    return parser.parse_args()


def handle_list_presets(args) -> int:
    """处理列出预设命令"""
    try:
        from src.app.settings import Settings
        settings = Settings(config_dir=getattr(args, 'config_dir', None))
        presets = settings.list_presets()

        if presets:
            print("Available configuration presets:")
            for preset in presets:
                print(f"  - {preset}")
        else:
            print("No configuration presets available.")

        return 0
    except Exception as e:
        print(f"Error listing presets: {e}")
        return 1


def handle_list_features(args) -> int:
    """处理列出功能标志命令"""
    try:
        from src.app.settings import Settings
        settings = Settings(config_dir=getattr(args, 'config_dir', None))

        if settings.use_new_system and settings.feature_manager:
            features = settings.feature_manager.list_features()
            print("Available features:")
            for feature in features:
                status = "✓" if settings.feature_manager.is_enabled(feature.name) else "✗"
                print(f"  {status} {feature.name}: {feature.description}")
        else:
            print("Feature flags are only available with the enhanced configuration system.")

        return 0
    except Exception as e:
        print(f"Error listing features: {e}")
        return 1


def handle_validate_config(args) -> int:
    """处理验证配置命令"""
    try:
        from src.app.settings import Settings
        settings = Settings(config_dir=getattr(args, 'config_dir', None))

        is_valid, errors, warnings = settings.validate_configuration()

        if is_valid:
            print("✓ Configuration is valid")
        else:
            print("✗ Configuration validation failed")
            for error in errors:
                print(f"  Error: {error}")

        if warnings:
            print("Warnings:")
            for warning in warnings:
                print(f"  Warning: {warning}")

        return 0 if is_valid else 1
    except Exception as e:
        print(f"Error validating configuration: {e}")
        return 1


def handle_config_report(args) -> int:
    """处理生成配置报告命令"""
    try:
        from src.app.settings import Settings
        settings = Settings(config_dir=getattr(args, 'config_dir', None))

        if settings.use_new_system and settings.tools:
            report = settings.tools.generate_configuration_report(settings.settings)
            print(report)
        else:
            print("Configuration reports are only available with the enhanced configuration system.")

        return 0
    except Exception as e:
        print(f"Error generating configuration report: {e}")
        return 1


def handle_export_config(args) -> int:
    """处理导出配置命令"""
    try:
        from pathlib import Path
        from src.app.settings import Settings

        settings = Settings(config_dir=getattr(args, 'config_dir', None))
        output_path = Path(args.export_config)

        if settings.export_configuration(output_path):
            print(f"Configuration exported to: {output_path}")
            return 0
        else:
            print("Failed to export configuration")
            return 1
    except Exception as e:
        print(f"Error exporting configuration: {e}")
        return 1


def handle_import_config(args) -> int:
    """处理导入配置命令"""
    try:
        from pathlib import Path
        from src.app.settings import Settings

        input_path = Path(args.import_config)
        if not input_path.exists():
            print(f"Configuration file not found: {input_path}")
            return 1

        settings = Settings(config_dir=getattr(args, 'config_dir', None))

        if settings.use_new_system and settings.tools:
            success, config, errors = settings.tools.import_configuration(input_path)
            if success:
                settings.settings = config
                settings.save_settings(config)
                print(f"Configuration imported from: {input_path}")
                return 0
            else:
                print("Failed to import configuration:")
                for error in errors:
                    print(f"  Error: {error}")
                return 1
        else:
            print("Configuration import is only available with the enhanced configuration system.")
            return 1
    except Exception as e:
        print(f"Error importing configuration: {e}")
        return 1


def handle_reset_config(args) -> int:
    """处理重置配置命令"""
    try:
        from src.app.settings import Settings

        # Confirm reset
        response = input("Are you sure you want to reset configuration to defaults? (y/N): ")
        if response.lower() != 'y':
            print("Configuration reset cancelled.")
            return 0

        settings = Settings(config_dir=getattr(args, 'config_dir', None))

        # Create backup before reset
        settings.create_backup("Before configuration reset")

        # Reset to defaults
        if settings.use_new_system and settings.loader:
            default_config = settings.loader._get_default_config()
        else:
            default_config = settings.default_settings.copy()

        settings.settings = default_config
        settings.save_settings(default_config)

        print("Configuration reset to defaults.")
        return 0
    except Exception as e:
        print(f"Error resetting configuration: {e}")
        return 1


def handle_backup_config(args) -> int:
    """处理备份配置命令"""
    try:
        from src.app.settings import Settings

        settings = Settings(config_dir=getattr(args, 'config_dir', None))

        if settings.create_backup("Manual backup"):
            print("Configuration backup created successfully.")
            return 0
        else:
            print("Failed to create configuration backup.")
            return 1
    except Exception as e:
        print(f"Error creating configuration backup: {e}")
        return 1


def check_singleton_and_activate() -> bool:
    """Check for existing instance and try to activate it"""
    try:
        singleton_manager = get_singleton_manager()
        is_running, instance_info = singleton_manager.is_another_instance_running()

        if is_running and instance_info:
            print("Another instance of VidTanium is already running.")
            print("Attempting to bring the existing window to the foreground...")

            # Try to activate the existing instance
            if singleton_manager.try_activate_existing(instance_info):
                print("Successfully activated the existing instance.")
                return True
            else:
                print("Failed to activate the existing instance, but it's still running.")
                print("Please check the system tray or taskbar for the VidTanium window.")
                return True

        return False

    except Exception as e:
        print(f"Error checking for existing instances: {e}")
        print("Continuing with application startup...")
        return False


def main() -> int:
    """主函数"""
    # 解析命令行参数
    args = parse_args()

    # 设置日志
    log_level = args.log_level if hasattr(args, 'log_level') and args.log_level else None
    setup_logging(args.debug, log_level)

    # Check for singleton behavior (can be disabled with --allow-multiple flag)
    allow_multiple = getattr(args, 'allow_multiple', False)
    if not allow_multiple:
        if check_singleton_and_activate():
            return 0  # Exit gracefully, existing instance was activated

    # Handle configuration management commands first
    if hasattr(args, 'list_presets') and args.list_presets:
        return handle_list_presets(args)

    if hasattr(args, 'list_features') and args.list_features:
        return handle_list_features(args)

    if hasattr(args, 'validate_config') and args.validate_config:
        return handle_validate_config(args)

    if hasattr(args, 'config_report') and args.config_report:
        return handle_config_report(args)

    if hasattr(args, 'export_config') and args.export_config:
        return handle_export_config(args)

    if hasattr(args, 'import_config') and args.import_config:
        return handle_import_config(args)

    if hasattr(args, 'reset_config') and args.reset_config:
        return handle_reset_config(args)

    if hasattr(args, 'backup_config') and args.backup_config:
        return handle_backup_config(args)

    # 创建并运行应用
    config_dir = getattr(args, 'config_dir', None) or getattr(args, 'config', None)
    app = Application(config_dir=config_dir, cli_args=args)

    # 如果提供了URL，自动创建下载任务
    if args.url:
        app.add_task_from_url(args.url)

    # 运行应用
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
