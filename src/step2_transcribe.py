# -*- coding: utf-8 -*-
"""
步骤二：将 output/MP3/ 下的 MP3 转写为文本，保存至 output/txt/{原文件名}.txt

若 output/txt/{原文件名}.txt 已存在则跳过该文件。
可独立运行，仅执行「转写」步骤。
依赖：openai-whisper。优先使用 imageio_ffmpeg 自带的 ffmpeg（随 moviepy 安装），
若未安装则需系统已安装 ffmpeg。
"""

import os
import logging
import sys
import time
from pathlib import Path

# 将 src 加入路径，便于从项目根以 python src/step2_transcribe.py 方式运行
if __name__ == "__main__":
    _src = Path(__file__).resolve().parent
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

from config import PROJECT_ROOT, OUTPUT_MP3_DIR, OUTPUT_TXT_DIR, LOG_DIR, LOG_FILE, WHISPER_MODEL, WHISPER_LANGUAGE
from log_utils import format_file_size, format_duration, rel_path

# 项目内用于放置 ffmpeg 链接的目录（imageio_ffmpeg 的二进制名为 ffmpeg-macos-xxx，需提供名为 ffmpeg 的入口）
BIN_DIR: Path = PROJECT_ROOT / "bin"


def ensure_ffmpeg_in_path() -> None:
    """
    若已安装 imageio_ffmpeg（随 moviepy），将其自带的 ffmpeg 通过项目 bin/ffmpeg 暴露，
    并加入 PATH，供 Whisper 使用（Whisper 只查找名为 ffmpeg 的可执行文件）。
    """
    try:
        import imageio_ffmpeg
        ffmpeg_exe = Path(imageio_ffmpeg.get_ffmpeg_exe()).resolve()
        BIN_DIR.mkdir(parents=True, exist_ok=True)
        link_path = BIN_DIR / "ffmpeg"
        if not link_path.exists() or link_path.resolve() != ffmpeg_exe:
            if link_path.exists():
                link_path.unlink()
            link_path.symlink_to(ffmpeg_exe)
        bin_str = str(BIN_DIR)
        path_sep = os.pathsep
        old_path = os.environ.get("PATH", "")
        if bin_str not in old_path.split(path_sep):
            os.environ["PATH"] = bin_str + path_sep + old_path
    except Exception:
        pass


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


def transcribe_mp3_to_txt(mp3_path: Path, txt_path: Path, model_name: str, language: str | None) -> bool:
    """
    将 MP3 转写为文本并保存。

    :param mp3_path: MP3 文件路径
    :param txt_path: 输出 txt 路径
    :param model_name: whisper 模型名（tiny/base/small/medium/large）
    :param language: 输出语言，zh=中文简体，None=自动识别
    :return: 是否成功
    """
    try:
        import whisper
    except ImportError:
        logging.error("请先安装 openai-whisper: pip install openai-whisper")
        return False

    try:
        model = whisper.load_model(model_name)
        result = model.transcribe(str(mp3_path), language=language, verbose=False)
        text = result.get("text", "").strip()
        txt_path.parent.mkdir(parents=True, exist_ok=True)
        txt_path.write_text(text, encoding="utf-8")
        return True
    except Exception as e:
        logging.exception("转写失败 %s: %s", mp3_path.name, e)
        return False


def main() -> None:
    """遍历 output/MP3/ 下所有 .mp3，转写为 txt 并保存到 output/txt/"""
    ensure_ffmpeg_in_path()
    setup_logging()
    logger = logging.getLogger(__name__)

    if not OUTPUT_MP3_DIR.is_dir():
        logger.error("MP3 目录不存在: %s，请先运行步骤一生成 MP3。", OUTPUT_MP3_DIR)
        sys.exit(1)

    # 确保转写文本输出目录存在，否则 txt_path.exists() 会全为 False，导致已存在的文本不会被跳过
    OUTPUT_TXT_DIR.mkdir(parents=True, exist_ok=True)

    mp3_files = sorted(OUTPUT_MP3_DIR.glob("*.mp3"))

    if not mp3_files:
        logger.info("output/MP3 目录下没有 .mp3 文件")
        return

    start_time = time.perf_counter()
    logger.info(
        "步骤二开始 | 共 %d 个 MP3 | 文本输出目录: %s（对应 txt 已存在则跳过）| 模型: %s | 语言: %s",
        len(mp3_files), rel_path(OUTPUT_TXT_DIR), WHISPER_MODEL, WHISPER_LANGUAGE or "自动",
    )

    processed = 0
    skipped = 0
    failed = 0

    for mp3_path in mp3_files:
        stem = mp3_path.stem
        txt_path = OUTPUT_TXT_DIR / f"{stem}.txt"
        if txt_path.exists():
            logger.info("跳过（文件已存在）: %s | 已有: %s", rel_path(txt_path), format_file_size(txt_path))
            skipped += 1
            continue
        mp3_size = format_file_size(mp3_path)
        logger.info("转写: %s | 输入大小: %s", mp3_path.name, mp3_size)
        t0 = time.perf_counter()
        if transcribe_mp3_to_txt(mp3_path, txt_path, WHISPER_MODEL, WHISPER_LANGUAGE):
            elapsed = time.perf_counter() - t0
            txt_size = format_file_size(txt_path)
            logger.info("已保存文本: %s | 输出大小: %s | 耗时: %s", rel_path(txt_path), txt_size, format_duration(elapsed))
            processed += 1
        else:
            logger.warning("转写未完成: %s", mp3_path.name)
            failed += 1

    total_elapsed = time.perf_counter() - start_time
    logger.info(
        "步骤二（转写文本）结束 | 成功: %d, 跳过: %d, 失败: %d | 总耗时: %s",
        processed, skipped, failed, format_duration(total_elapsed),
    )


if __name__ == "__main__":
    main()
