# -*- coding: utf-8 -*-
"""
步骤一：从 input 目录的 MP4 中抽离音频，保存为 output/MP3/{原文件名}.mp3

若 output/MP3/{原文件名}.mp3 已存在则跳过该文件。
可独立运行，仅执行「抽音」步骤。
依赖：moviepy，系统需安装 ffmpeg。
"""

import logging
import sys
import time
from pathlib import Path

# 将 src 加入路径，便于从项目根以 python src/step1_extract_audio.py 方式运行
if __name__ == "__main__":
    _src = Path(__file__).resolve().parent
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

from config import INPUT_DIR, OUTPUT_MP3_DIR, LOG_DIR, LOG_FILE
from log_utils import format_file_size, format_duration, rel_path


def setup_logging() -> None:
    """将运行日志输出到 log 目录下的日志文件"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
        force=True,
    )


def extract_audio_from_mp4(mp4_path: Path, mp3_path: Path) -> bool:
    """
    从 MP4 抽离音频并保存为 MP3。

    :param mp4_path: MP4 文件路径
    :param mp3_path: 输出 MP3 路径
    :return: 是否成功
    """
    # moviepy 2.x 使用 from moviepy import VideoFileClip
    try:
        from moviepy import VideoFileClip
    except ImportError:
        logging.error("请先安装 moviepy: pip install moviepy")
        return False

    try:
        clip = VideoFileClip(str(mp4_path))
        if clip.audio is None:
            logging.warning("跳过（无音轨）: %s", mp4_path.name)
            clip.close()
            return False
        mp3_path.parent.mkdir(parents=True, exist_ok=True)
        clip.audio.write_audiofile(str(mp3_path))
        clip.close()
        return True
    except Exception as e:
        logging.exception("抽离音频失败 %s: %s", mp4_path.name, e)
        return False


def main() -> None:
    """遍历 input 下所有 .mp4，抽离为 MP3 并保存到 output/MP3/"""
    setup_logging()
    logger = logging.getLogger(__name__)

    if not INPUT_DIR.is_dir():
        logger.error("input 目录不存在: %s", INPUT_DIR)
        sys.exit(1)

    OUTPUT_MP3_DIR.mkdir(parents=True, exist_ok=True)
    mp4_files = sorted(INPUT_DIR.glob("*.mp4"))

    if not mp4_files:
        logger.info("input 目录下没有 .mp4 文件")
        return

    start_time = time.perf_counter()
    logger.info("步骤一开始 | 待处理: %d 个 MP4", len(mp4_files))

    processed = 0
    skipped = 0
    failed = 0

    for mp4_path in mp4_files:
        stem = mp4_path.stem
        mp3_path = OUTPUT_MP3_DIR / f"{stem}.mp3"
        if mp3_path.exists():
            logger.info("跳过（文件已存在）: %s | 已有: %s", rel_path(mp3_path), format_file_size(mp3_path))
            skipped += 1
            continue
        mp4_size = format_file_size(mp4_path)
        logger.info("处理: %s | 输入大小: %s", mp4_path.name, mp4_size)
        t0 = time.perf_counter()
        if extract_audio_from_mp4(mp4_path, mp3_path):
            elapsed = time.perf_counter() - t0
            mp3_size = format_file_size(mp3_path)
            logger.info("已保存音频: %s | 输出大小: %s | 耗时: %s", rel_path(mp3_path), mp3_size, format_duration(elapsed))
            processed += 1
        else:
            logger.warning("抽离音频未完成: %s", mp4_path.name)
            failed += 1

    total_elapsed = time.perf_counter() - start_time
    logger.info(
        "步骤一（抽离音频）结束 | 成功: %d, 跳过: %d, 失败: %d | 总耗时: %s",
        processed, skipped, failed, format_duration(total_elapsed),
    )


if __name__ == "__main__":
    main()
