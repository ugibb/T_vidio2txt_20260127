# -*- coding: utf-8 -*-
"""
统一配置项

所有路径、模型名等可调参数在此定义。
秘钥类配置（如 API Key）从项目根目录 .env 文件加载，请复制 .env.example 为 .env 后填写。
"""

import os
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# 项目根目录（以 src 的上级目录为项目根）
# ---------------------------------------------------------------------------
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# 从 .env 加载秘钥等配置（在读取 LLM 等配置前执行）
# ---------------------------------------------------------------------------
def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
        env_path = PROJECT_ROOT / ".env"
        if env_path.is_file():
            load_dotenv(env_path)
    except ImportError:
        pass


_load_dotenv()

# ---------------------------------------------------------------------------
# 输入输出路径
# ---------------------------------------------------------------------------
# MP4 视频所在目录
INPUT_DIR: Path = PROJECT_ROOT / "input"

# 抽离出的 MP3 保存目录（与步骤一/二文档中的 output/MP3 一致）
OUTPUT_MP3_DIR: Path = PROJECT_ROOT / "output" / "mp3"

# 转写文本保存目录
OUTPUT_TXT_DIR: Path = PROJECT_ROOT / "output" / "txt"

# 步骤四：LLM 整理后的大纲与章节概要输出目录
OUTPUT_OUTLINE_DIR: Path = PROJECT_ROOT / "output" / "outline"

# 步骤 4.1：按自然段落拆分后的 txt 输出目录（每个段落一个 txt）
OUTPUT_PARAGRAPHS_DIR: Path = PROJECT_ROOT / "output" / "result" / "paragraphs"

# 步骤 4.2：每个段落的思维导图整理输出目录
OUTPUT_MINDMAP_DIR: Path = PROJECT_ROOT / "output" / "result" / "mindmap"

# 步骤 4.4：每个 txt 源对应的完整思维导图（合并该源下所有段落思维导图）
OUTPUT_FINAL_MINDMAP_DIR: Path = PROJECT_ROOT / "output" / "result" / "final_mindmap"

# 步骤 4.1：自然段落目标字符数（约多少字为一段，用于合并短句）
PARAGRAPH_TARGET_CHARS: int = 500

# ---------------------------------------------------------------------------
# 日志
# ---------------------------------------------------------------------------
# 日志文件所在目录
LOG_DIR: Path = PROJECT_ROOT / "log"

# 日志文件名（按日期区分，格式：app_2026-01-29.log）
LOG_FILENAME: str = f"void2Txt_{datetime.now().strftime('%Y-%m-%d')}.log"

# 日志文件完整路径
LOG_FILE: Path = LOG_DIR / LOG_FILENAME

# ---------------------------------------------------------------------------
# 转写相关（Whisper）
# ---------------------------------------------------------------------------
# Whisper 模型名：tiny / base / small / medium / large
WHISPER_MODEL: str = "base"

# 转写输出语言：zh=中文简体，None=自动识别
WHISPER_LANGUAGE: str | None = "zh"

# ---------------------------------------------------------------------------
# 步骤四：大语言模型（从 .env 读取秘钥，未设置则为空）
# ---------------------------------------------------------------------------
# 可选 LLM 配置（在 .env 中设置 OPENAI_API_KEY + 以下 BASE_URL / MODEL 即可切换）：
#   智谱 GLM-4（当前默认）:   BASE_URL=https://open.bigmodel.cn/api/paas/v4            MODEL=glm-4
#   Kimi 国内 K2.5:                                BASE_URL=https://api.moonshot.cn/v1   MODEL=kimi-k2.5
#   Kimi 国内（moonshot-v1）:                     BASE_URL=https://api.moonshot.cn/v1   MODEL=moonshot-v1-32k
#   Kimi 全球（platform.moonshot.ai）:             BASE_URL=https://api.moonshot.ai/v1   MODEL=moonshot-v1-32k
#   通义千问-Max:             BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1  MODEL=qwen-max
#   OpenAI:                   BASE_URL= 留空                                            MODEL=gpt-4o-mini
#   DeepSeek:                 BASE_URL=https://api.deepseek.com/v1                     MODEL=deepseek-chat
#
# OpenAI 兼容 API Key（在 .env 中配置 OPENAI_API_KEY；通义也可用 DASHSCOPE_API_KEY）
# 通义千问必须使用「百炼 API Key」（sk- 开头），在 百炼控制台 API-Key 页面创建；
# 不可使用 RAM 的 accessKeyId/accessKeySecret。获取：https://bailian.console.aliyun.com/?tab=model#/api-key
# 清洗 Key：去除首尾及行内 \r\n/空格，避免 .env 换行或 CRLF 导致 401
def _clean_api_key(raw: str) -> str:
    if not raw:
        return ""
    return raw.replace("\r", "").replace("\n", "").strip()


LLM_API_KEY: str = _clean_api_key(os.environ.get("OPENAI_API_KEY", ""))

# 调用的模型名（可在 .env 中配置 LLM_MODEL；默认智谱 glm-4）
LLM_MODEL: str = os.environ.get("LLM_MODEL", "glm-4").strip() or "glm-4"

# API 基础 URL（可在 .env 中配置 LLM_BASE_URL；默认智谱 GLM-4）
LLM_BASE_URL: str = os.environ.get(
    "LLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4"
).strip()

# 单次请求超时秒数（大文本时适当增大，可在 .env 中配置 LLM_TIMEOUT）
LLM_TIMEOUT: int = int(os.environ.get("LLM_TIMEOUT", "180").strip() or "180")

# 连接失败时的重试次数（可在 .env 中配置 LLM_MAX_RETRIES）
LLM_MAX_RETRIES: int = int(os.environ.get("LLM_MAX_RETRIES", "3").strip() or "3")
