# -*- coding: utf-8 -*-
"""
步骤四（统一）：大语言模型整理 txt 文档。

子步骤顺序：
  4     - 整理大纲 + 每个章节大纲的概要（output/outline/）
  4.1   - 将 txt 分隔成自然段落，每个段落一个 TXT（output/result/paragraphs/）
  4.2   - 对每个段落：先 LLM 加标点、句号换行，再以思维导图方式完整整理（output/result/mindmap/）
  4.4   - 将所有段落思维导图合并为每个 txt 源对应的一个完整思维导图（output/result/final_mindmap/）

可独立运行：python src/step4.py。需在项目根目录 .env 中配置 OPENAI_API_KEY。
"""

import logging
import re
import sys
import time
from pathlib import Path

if __name__ == "__main__":
    _src = Path(__file__).resolve().parent
    if str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

from config import (
    OUTPUT_TXT_DIR,
    OUTPUT_OUTLINE_DIR,
    OUTPUT_PARAGRAPHS_DIR,
    OUTPUT_MINDMAP_DIR,
    OUTPUT_FINAL_MINDMAP_DIR,
    LOG_DIR,
    LOG_FILE,
    PARAGRAPH_TARGET_CHARS,
    LLM_API_KEY,
    LLM_MODEL,
    LLM_BASE_URL,
    LLM_TIMEOUT,
    LLM_MAX_RETRIES,
)
from log_utils import format_file_size, format_duration, rel_path

# ---------------------------------------------------------------------------
# 日志
# ---------------------------------------------------------------------------
def _setup_logging() -> None:
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


# ---------------------------------------------------------------------------
# 错误日志封装：仅输出简短信息，不打印堆栈
# ---------------------------------------------------------------------------
def _short_error(exc: BaseException, max_len: int = 120) -> str:
    """将异常格式化为单行简短字符串，便于日志阅读。"""
    msg = f"{type(exc).__name__}: {exc}"
    return (msg[: max_len - 3] + "...") if len(msg) > max_len else msg


# ---------------------------------------------------------------------------
# LLM 调用：超时与重试
# ---------------------------------------------------------------------------
def _call_llm_with_retry(callable_fn, label: str) -> str:
    """
    执行 LLM 调用，连接失败或 429 限流时按 LLM_MAX_RETRIES 重试（退避递增）。
    :param callable_fn: 无参可调用对象，返回模型返回文本
    :param label: 日志标签（如文件名）
    :return: 模型返回的文本
    :raises: 最后一次尝试时的异常
    """
    from openai import APIConnectionError, RateLimitError

    last_exc: BaseException | None = None
    for attempt in range(LLM_MAX_RETRIES + 1):
        try:
            return callable_fn()
        except (APIConnectionError, RateLimitError) as e:
            last_exc = e
            if attempt < LLM_MAX_RETRIES:
                # 429 用较长退避（可能需等配额/分钟限制），连接错误用较短退避
                delay = (30 * (attempt + 1)) if isinstance(e, RateLimitError) else (2**attempt) + (time.time() % 1)
                kind = "限流/配额" if isinstance(e, RateLimitError) else "连接"
                logging.getLogger(__name__).warning(
                    "调用大模型%s失败 %s，%d 秒后重试（%d/%d）: %s",
                    kind,
                    label,
                    int(delay),
                    attempt + 1,
                    LLM_MAX_RETRIES,
                    str(e)[:80],
                )
                time.sleep(delay)
            else:
                if isinstance(e, RateLimitError):
                    logging.getLogger(__name__).error(
                        "提示：若为配额/余额不足，请至 OpenAI 账单页充值或更换 .env 中的 OPENAI_API_KEY / LLM_BASE_URL"
                    )
                raise
        except Exception as e:
            last_exc = e
            raise
    assert last_exc is not None
    raise last_exc


# ---------------------------------------------------------------------------
# 4 - 整理大纲 + 各章节概要
# ---------------------------------------------------------------------------
_PROMPT_OUTLINE = """你是一份课程/讲座转写文本的整理助手。请对用户提供的转写文本完成两件事：
1）整理大纲：根据内容给出层级化的大纲结构（可含一级、二级标题等）；
2）每个章节的概要：针对大纲中的每个章节，写一段话概括该章节的核心要点。

请用 Markdown 格式输出，结构建议为：
## 一、大纲
（层级化大纲）

## 二、各章节概要
### 第 x 章 / 第 x 节：标题
（该章节的概要段落）
"""


def _call_llm_outline(text: str, api_key: str, model: str, base_url: str, label: str = "") -> str:
    from openai import OpenAI

    client_kw: dict = {"api_key": api_key, "timeout": float(LLM_TIMEOUT)}
    if base_url and base_url.strip():
        client_kw["base_url"] = base_url.strip()
    client = OpenAI(**client_kw)

    def _do() -> str:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": _PROMPT_OUTLINE},
                {"role": "user", "content": f"请对以下转写文本按要求整理大纲与各章节概要。\n\n---\n\n{text}"},
            ],
        )
        return (response.choices[0].message.content or "").strip()

    return _call_llm_with_retry(_do, label or "outline")


def _run_outline(api_key: str, model: str, base_url: str) -> None:
    """4：遍历 output/txt/ 下所有 .txt，生成大纲与各章节概要到 output/outline/"""
    logger = logging.getLogger(__name__)
    if not OUTPUT_TXT_DIR.is_dir():
        logger.error("txt 目录不存在: %s，请先完成步骤二。", OUTPUT_TXT_DIR)
        sys.exit(1)
    txt_files = sorted(OUTPUT_TXT_DIR.glob("*.txt"))
    if not txt_files:
        logger.info("步骤 4（大纲与概要）：无 txt 文件，跳过")
        return
    OUTPUT_OUTLINE_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("步骤 4（大纲与概要）开始 | 待处理: %d 个 txt | 模型: %s", len(txt_files), model)
    processed = 0
    for txt_path in txt_files:
        stem = txt_path.stem
        outline_path = OUTPUT_OUTLINE_DIR / f"{stem}_outline.md"
        if outline_path.exists():
            logger.info("跳过（已存在）: %s", rel_path(outline_path))
            processed += 1
            continue
        try:
            raw = txt_path.read_text(encoding="utf-8").strip()
        except Exception as e:
            logger.error("读取失败 %s: %s", txt_path.name, _short_error(e))
            continue
        if not raw:
            logger.warning("跳过（内容为空）: %s", txt_path.name)
            continue
        try:
            content = _call_llm_outline(raw, api_key, model, base_url, label=txt_path.name)
        except Exception as e:
            logger.error("调用大模型失败 %s: %s", txt_path.name, _short_error(e))
            continue
        if not content:
            logger.warning("大模型返回为空: %s", txt_path.name)
            continue
        try:
            outline_path.write_text(content, encoding="utf-8")
            logger.info("已保存: %s | 大小: %s", rel_path(outline_path), format_file_size(outline_path))
        except Exception as e:
            logger.error("写入失败 %s: %s", outline_path.name, _short_error(e))
            continue
        processed += 1
    logger.info("步骤 4（大纲与概要）结束 | 成功: %d", processed)


# ---------------------------------------------------------------------------
# 4.1 - 拆分自然段落
# ---------------------------------------------------------------------------
def _split_into_paragraphs(text: str, target_chars: int) -> list[str]:
    text = text.strip()
    if not text:
        return []
    pattern = r"(?<=[。！？；.!?])\s*"
    sentences = [s.strip() for s in re.split(pattern, text) if s.strip()]
    if not sentences:
        sentences = [text]
    if len(sentences) == 1 and len(sentences[0]) > target_chars:
        return [sentences[0][i : i + target_chars] for i in range(0, len(sentences[0]), target_chars)]
    paragraphs: list[str] = []
    current: list[str] = []
    current_len = 0
    for s in sentences:
        s_len = len(s)
        if current_len + s_len > target_chars and current:
            paragraphs.append("".join(current))
            current = [s]
            current_len = s_len
        else:
            current.append(s)
            current_len += s_len
    if current:
        paragraphs.append("".join(current))
    return paragraphs


def _run_split_paragraphs() -> None:
    """4.1：将 output/txt/ 下所有 .txt 按自然段落拆分到 output/result/paragraphs/"""
    logger = logging.getLogger(__name__)
    if not OUTPUT_TXT_DIR.is_dir():
        logger.error("txt 目录不存在: %s，请先完成步骤二。", OUTPUT_TXT_DIR)
        sys.exit(1)
    txt_files = sorted(OUTPUT_TXT_DIR.glob("*.txt"))
    if not txt_files:
        logger.info("步骤 4.1（拆分段落）：无 txt 文件，跳过")
        return
    logger.info("步骤 4.1（拆分段落）开始 | 待处理: %d 个 txt | 目标长度: %d 字", len(txt_files), PARAGRAPH_TARGET_CHARS)
    total_paragraphs = 0
    for txt_path in txt_files:
        stem = txt_path.stem
        out_dir = OUTPUT_PARAGRAPHS_DIR / stem
        try:
            raw = txt_path.read_text(encoding="utf-8").strip()
        except Exception as e:
            logger.error("读取失败 %s: %s", txt_path.name, _short_error(e))
            continue
        if not raw:
            logger.warning("跳过（内容为空）: %s", txt_path.name)
            continue
        paragraphs = _split_into_paragraphs(raw, PARAGRAPH_TARGET_CHARS)
        if not paragraphs:
            continue
        out_dir.mkdir(parents=True, exist_ok=True)
        count = 0
        for i, para in enumerate(paragraphs, start=1):
            if not para.strip():
                continue
            out_path = out_dir / f"p_{i:03d}.txt"
            try:
                out_path.write_text(para.strip(), encoding="utf-8")
                count += 1
            except Exception as e:
                logger.error("写入失败 %s: %s", out_path.name, _short_error(e))
        if count > 0:
            logger.info("已保存 %d 个段落: %s", count, rel_path(out_dir))
        total_paragraphs += count
    logger.info("步骤 4.1（拆分段落）结束 | 共 %d 个段落", total_paragraphs)


# ---------------------------------------------------------------------------
# 4.2 - 每段落：加标点、句号换行 + 思维导图整理
# ---------------------------------------------------------------------------
_PROMPT_MINDMAP = """你是一份课程/讲座段落文本的整理助手。请对用户提供的段落文本完成两件事（按顺序）：

1. 先为原文增加标点符号（转写文本通常无标点），并在句号、问号、感叹号等处换行，便于阅读。
2. 再以思维导图方式对内容进行完整整理：一字不落、不丢弃任何知识点。

【思维导图要求】
- 使用 Markdown 标题层级（# ## ### ####）呈现思维导图结构。
- 主节点、子节点、细节逐级展开；术语、例句、概念、举例等需完整保留。
"""


def _call_llm_mindmap(text: str, api_key: str, model: str, base_url: str, label: str = "") -> str:
    from openai import OpenAI

    client_kw: dict = {"api_key": api_key, "timeout": float(LLM_TIMEOUT)}
    if base_url and base_url.strip():
        client_kw["base_url"] = base_url.strip()
    client = OpenAI(**client_kw)
    user_content = f"""请对以下段落文本：1）先加标点并在句号等处换行；2）再整理成思维导图，务必一字不落、不丢弃任何知识点。

---
{text}
"""

    def _do() -> str:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": _PROMPT_MINDMAP},
                {"role": "user", "content": user_content},
            ],
        )
        return (response.choices[0].message.content or "").strip()

    return _call_llm_with_retry(_do, label or "mindmap")


def _run_mindmap(api_key: str, model: str, base_url: str) -> None:
    """4.2：遍历 output/result/paragraphs/ 下所有段落 txt，生成思维导图到 output/result/mindmap/"""
    logger = logging.getLogger(__name__)
    if not OUTPUT_PARAGRAPHS_DIR.is_dir():
        logger.error("paragraphs 目录不存在: %s，请先完成步骤 4.1。", OUTPUT_PARAGRAPHS_DIR)
        sys.exit(1)
    para_files: list[tuple[Path, str]] = []
    for stem_dir in sorted(d for d in OUTPUT_PARAGRAPHS_DIR.iterdir() if d.is_dir()):
        stem = stem_dir.name
        for p in sorted(stem_dir.glob("p_*.txt")):
            para_files.append((p, stem))
    if not para_files:
        logger.info("步骤 4.2（思维导图）：无段落文件，跳过")
        return
    logger.info("步骤 4.2（思维导图）开始 | 待处理: %d 个段落 | 模型: %s", len(para_files), model)
    processed = 0
    skipped = 0
    for para_path, stem in para_files:
        para_name = para_path.stem
        mindmap_path = OUTPUT_MINDMAP_DIR / stem / f"{para_name}_mindmap.md"
        if mindmap_path.exists():
            logger.info("跳过（已存在）: %s", rel_path(mindmap_path))
            skipped += 1
            processed += 1
            continue
        try:
            raw = para_path.read_text(encoding="utf-8").strip()
        except Exception as e:
            logger.error("读取失败 %s: %s", para_path.name, _short_error(e))
            continue
        if not raw:
            logger.warning("跳过（段落为空）: %s", para_path.name)
            continue
        t0 = time.perf_counter()
        try:
            content = _call_llm_mindmap(raw, api_key, model, base_url, label=para_path.name)
        except Exception as e:
            logger.error("调用大模型失败 %s: %s", para_path.name, _short_error(e))
            continue
        if not content:
            logger.warning("大模型返回为空: %s", para_path.name)
            continue
        try:
            mindmap_path.parent.mkdir(parents=True, exist_ok=True)
            mindmap_path.write_text(content, encoding="utf-8")
            elapsed = time.perf_counter() - t0
            logger.info("已保存: %s | 大小: %s | 耗时: %s", rel_path(mindmap_path), format_file_size(mindmap_path), format_duration(elapsed))
        except Exception as e:
            logger.error("写入失败 %s: %s", mindmap_path.name, _short_error(e))
            continue
        processed += 1
    logger.info("步骤 4.2（思维导图）结束 | 成功: %d, 跳过: %d", processed, skipped)


# ---------------------------------------------------------------------------
# 4.4 - 合并每个 txt 源下所有段落思维导图为完整思维导图
# ---------------------------------------------------------------------------
def _run_merge_mindmap() -> None:
    """4.4：将每个 stem 下所有 p_*_mindmap.md 合并为一个 {stem}_full_mindmap.md，保存到 output/result/final_mindmap/"""
    logger = logging.getLogger(__name__)
    if not OUTPUT_MINDMAP_DIR.is_dir():
        logger.info("步骤 4.4（合并思维导图）：mindmap 目录不存在，跳过")
        return
    OUTPUT_FINAL_MINDMAP_DIR.mkdir(parents=True, exist_ok=True)
    stem_dirs = sorted(d for d in OUTPUT_MINDMAP_DIR.iterdir() if d.is_dir())
    if not stem_dirs:
        logger.info("步骤 4.4（合并思维导图）：无 mindmap 子目录，跳过")
        return
    logger.info("步骤 4.4（合并思维导图）开始 | 待合并: %d 个源", len(stem_dirs))
    merged = 0
    for stem_dir in stem_dirs:
        stem = stem_dir.name
        mindmap_files = sorted(stem_dir.glob("p_*_mindmap.md"))
        if not mindmap_files:
            continue
        out_path = OUTPUT_FINAL_MINDMAP_DIR / f"{stem}_full_mindmap.md"
        parts: list[str] = []
        for f in mindmap_files:
            try:
                parts.append(f.read_text(encoding="utf-8").strip())
            except Exception as e:
                logger.error("读取失败 %s: %s", f.name, _short_error(e))
        if not parts:
            continue
        sep = "\n\n---\n\n"
        full_content = f"# {stem}\n\n" + sep.join(parts)
        try:
            out_path.write_text(full_content, encoding="utf-8")
            logger.info("已合并: %s | %d 个段落 | 大小: %s", rel_path(out_path), len(parts), format_file_size(out_path))
            merged += 1
        except Exception as e:
            logger.error("写入失败 %s: %s", out_path.name, _short_error(e))
    logger.info("步骤 4.4（合并思维导图）结束 | 成功: %d", merged)


# ---------------------------------------------------------------------------
# 统一入口
# ---------------------------------------------------------------------------
def main() -> None:
    """按顺序执行：4（大纲与概要）→ 4.1（拆分段落）→ 4.2（思维导图）→ 4.4（合并思维导图）"""
    _setup_logging()
    logger = logging.getLogger(__name__)

    if not LLM_API_KEY:
        logger.error("未配置 API Key，请在项目根目录 .env 中配置 OPENAI_API_KEY（可复制 .env.example 为 .env 后填写）")
        sys.exit(1)

    model = LLM_MODEL
    base_url = LLM_BASE_URL or ""

    total_start = time.perf_counter()
    logger.info("======== 步骤四（统一）开始 ========")
    logger.info("LLM 请求地址: %s | 模型: %s", base_url or "(默认)", model)

    _run_outline(LLM_API_KEY, model, base_url)
    _run_split_paragraphs()
    _run_mindmap(LLM_API_KEY, model, base_url)
    _run_merge_mindmap()

    total_elapsed = time.perf_counter() - total_start
    logger.info("======== 步骤四（统一）结束 | 总耗时: %s ========", format_duration(total_elapsed))


if __name__ == "__main__":
    main()
