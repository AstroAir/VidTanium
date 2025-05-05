#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import logging
import argparse
from pathlib import Path

from src.app.application import Application


def setup_logging(debug=False):
    """设置日志系统"""
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


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="加密视频下载工具")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    parser.add_argument("--config", type=str, help="指定配置目录")
    parser.add_argument("--url", type=str, help="要下载的视频URL")
    return parser.parse_args()


def main():
    """主函数"""
    # 解析命令行参数
    args = parse_args()

    # 设置日志
    setup_logging(args.debug)

    # 创建并运行应用
    app = Application(config_dir=args.config)

    # 如果提供了URL，自动创建下载任务
    if args.url:
        app.add_task_from_url(args.url)

    # 运行应用
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
