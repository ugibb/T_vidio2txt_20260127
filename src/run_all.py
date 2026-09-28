# -*- coding: utf-8 -*-
"""
全局运行入口：按顺序执行所有步骤（步骤一 → 步骤二 → 步骤四统一）。

步骤四（统一）包含：4 大纲与概要 → 4.1 拆分段落 → 4.2 思维导图 → 4.4 合并思维导图。
各步骤仍可独立运行（如 python src/step4.py）。步骤四需在项目根目录 .env 中配置 OPENAI_API_KEY。
"""

import logging
import sys
import time
from pathlib import Path

# 将 src 加入路径，便于从项目根以 python src/run_all.py 方式运行
if __name__ == "__main__":
    _src = Path(__file__).resolve().parent
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

from config import LOG_DIR, LOG_FILE
from log_utils import format_duration


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


def main() -> None:
    """按顺序执行：步骤一 → 步骤二 → 步骤 4.1 → 步骤四 → 步骤 4.2"""
    setup_logging()
    logger = logging.getLogger(__name__)

    total_start = time.perf_counter()
    logger.info("======== 全局流水线开始 ========")

    steps = [
        ("步骤一（抽离音频）", "step1_extract_audio", "main"),
        ("步骤二（转写文本）", "step2_transcribe", "main"),  
    ]
    # ("步骤四（统一：大纲 / 段落 / 思维导图 / 合并）", "step4", "main"),

    for label, module_name, func_name in steps:
        logger.info("======== %s ========", label)
        try:
            module = __import__(module_name, fromlist=[func_name])
            run = getattr(module, func_name)
            run()
        except SystemExit as e:
            logger.error("%s 退出，码: %s", label, e.code)
            sys.exit(e.code if e.code is not None else 1)
        except Exception as e:
            logger.exception("%s 执行异常: %s", label, e)
            sys.exit(1)

    total_elapsed = time.perf_counter() - total_start
    logger.info("======== 全局流水线结束 | 总耗时: %s ========", format_duration(total_elapsed))


if __name__ == "__main__":
    main()
