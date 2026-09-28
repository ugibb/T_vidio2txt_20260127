# -*- coding: utf-8 -*-
"""
运行日志辅助：文件大小、耗时等格式化，供各步骤统一使用。
"""

import time
from pathlib import Path

# 用于 rel_path 的项目根，延迟导入避免循环依赖
_PROJECT_ROOT: Path | None = None


def _get_project_root() -> Path:
    """获取项目根目录（延迟导入 config）。"""
    global _PROJECT_ROOT
    if _PROJECT_ROOT is None:
        from config import PROJECT_ROOT
        _PROJECT_ROOT = PROJECT_ROOT
    return _PROJECT_ROOT


def rel_path(path: Path) -> str:
    """将路径转为相对项目根的相对路径字符串，便于日志展示；若不在项目根下则退回文件名。"""
    try:
        return str(path.relative_to(_get_project_root()))
    except ValueError:
        return path.name


def format_file_size(path: Path) -> str:
    """将文件大小格式化为易读字符串（如 1.2 MB）。"""
    try:
        n = path.stat().st_size
    except OSError:
        return "?"
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.1f} KB"
    if n < 1024 * 1024 * 1024:
        return f"{n / (1024 * 1024):.1f} MB"
    return f"{n / (1024 * 1024 * 1024):.1f} GB"


def format_duration(seconds: float) -> str:
    """将秒数格式化为易读字符串（如 1分23秒）。"""
    if seconds < 60:
        return f"{seconds:.1f}秒"
    m = int(seconds // 60)
    s = seconds - m * 60
    if m < 60:
        return f"{m}分{s:.1f}秒"
    h = m // 60
    m = m % 60
    return f"{h}小时{m}分{s:.1f}秒"


class elapsed_timer:
    """上下文管理器：记录区间耗时，可通过 .seconds 获取秒数。"""

    def __init__(self) -> None:
        self.start: float = 0.0
        self.seconds: float = 0.0

    def __enter__(self) -> "elapsed_timer":
        self.start = time.perf_counter()
        return self

    def __exit__(self, *args: object) -> None:
        self.seconds = time.perf_counter() - self.start
