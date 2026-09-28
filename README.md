# MP4 抽音与转写工具

## 功能说明

1. 从 `input` 文件夹读取 MP4 视频，抽离音频并保存为 `output/MP3/{原文件名}.mp3`
2. 将上述 MP3 转写为文本，保存至 `output/txt/{原文件名}.txt`（可配置输出语言为中文简体）
3. 利用大语言模型整理 txt 文档：① 整理大纲；② 每个章节大纲的概要，保存至 `output/outline/{原文件名}_outline.md`
4. **步骤 4.1**：将 txt 分隔成自然段落，每个段落一个 txt，保存至 `output/paragraphs/{原文件名}/p_001.txt` 等
5. **步骤 4.2**：将每个段落 txt 以思维导图方式完整整理（一字不落），保存至 `output/mindmap/{原文件名}/p_001_mindmap.md` 等

## 目录结构

```
20260101-English/
├── input/              # 待处理的 MP4 文件
├── output/
│   ├── MP3/            # 抽离出的音频
│   ├── txt/            # 转写文本
│   ├── outline/        # 步骤四：LLM 整理的大纲与章节概要（Markdown）
│   ├── paragraphs/     # 步骤 4.1：按自然段落拆分的 txt（每段一个文件）
│   └── mindmap/        # 步骤 4.2：每个段落的思维导图整理（Markdown）
├── log/                # 运行日志（app_YYYY-MM-DD.log，按日期区分）
├── src/
│   ├── config.py       # 统一配置项
│   ├── step1_extract_audio.py   # 步骤一：抽离 MP4 音频为 MP3
│   ├── step2_transcribe.py     # 步骤二：将 MP3 转写为 txt
│   ├── step4_organize_txt.py   # 步骤四：LLM 整理大纲与章节概要
│   ├── step4_1_split_paragraphs.py   # 步骤 4.1：拆分自然段落
│   ├── step4_2_mindmap.py      # 步骤 4.2：思维导图方式整理每个段落
│   └── run_all.py             # 全局入口：按顺序执行所有步骤
├── requirements.txt
└── README.md
```

## 环境要求

- Python 3.8+
- 系统已安装 [FFmpeg](https://ffmpeg.org/)（moviepy、whisper 依赖）

macOS 安装 FFmpeg：`brew install ffmpeg`

## 使用方法

```bash
# 进入项目目录
cd 20260101-English

# 安装依赖
pip install -r requirements.txt

# 方式一：一键执行所有步骤（步骤一 → 二 → 4.1 → 四 → 4.2；步骤四与 4.2 需 OPENAI_API_KEY）
python src/run_all.py

# 方式二：按需独立执行某一步
# 步骤一：仅抽离音频（可独立运行）
python src/step1_extract_audio.py

# 步骤二：仅转写 MP3 为文本（可独立运行，依赖 output/MP3/ 下已有 MP3）
python src/step2_transcribe.py

# 步骤 4.1：将 txt 分隔成自然段落（可独立运行，依赖 output/txt/ 下已有 txt）
python src/step4_1_split_paragraphs.py

# 步骤 4.2：以思维导图方式整理每个段落（可独立运行，依赖 output/paragraphs/；需设置 OPENAI_API_KEY）
python src/step4_2_mindmap.py

# 步骤四：LLM 整理 txt 大纲与章节概要（可独立运行，依赖 output/txt/；需设置 OPENAI_API_KEY）
python src/step4_organize_txt.py
```

- 步骤一：遍历 `input/` 下所有 `.mp4`，抽离音频到 `output/MP3/`。
- 步骤二：遍历 `output/MP3/` 下所有 `.mp3`，转写为文本到 `output/txt/`（可配置 WHISPER_LANGUAGE 为 zh 输出中文简体）。
- 步骤 4.1：遍历 `output/txt/` 下所有 `.txt`，按自然段落拆分到 `output/paragraphs/{原名}/p_001.txt` 等。
- 步骤 4.2：遍历 `output/paragraphs/` 下所有段落 txt，调用大模型以思维导图方式完整整理，输出到 `output/mindmap/{原名}/p_001_mindmap.md` 等。
- 步骤四：遍历 `output/txt/` 下所有 `.txt`，调用大模型整理大纲与各章节概要，输出到 `output/outline/{原名}_outline.md`。
- 运行日志统一写入 `log/app_YYYY-MM-DD.log`（按日期区分），同时会在控制台输出。

## 配置说明

所有可调项在 `src/config.py` 中定义：

| 配置项 | 说明 |
|--------|------|
| INPUT_DIR | MP4 视频所在目录 |
| OUTPUT_MP3_DIR | MP3 输出目录 |
| OUTPUT_TXT_DIR | 转写文本输出目录 |
| OUTPUT_OUTLINE_DIR | 步骤四：大纲与概要输出目录 |
| OUTPUT_PARAGRAPHS_DIR | 步骤 4.1：段落 txt 输出目录 |
| OUTPUT_MINDMAP_DIR | 步骤 4.2：思维导图输出目录 |
| LOG_DIR / LOG_FILE | 日志目录与日志文件 |
| WHISPER_MODEL | Whisper 模型：tiny / base / small / medium / large |
| WHISPER_LANGUAGE | 转写输出语言：zh=中文简体，None=自动识别 |
| PARAGRAPH_TARGET_CHARS | 步骤 4.1：自然段落目标字符数（约多少字为一段） |

### 秘钥配置（.env）

API Key 等秘钥类配置统一在项目根目录 **.env** 文件中配置，勿提交到版本库。

1. 复制 `.env.example` 为 `.env`：`cp .env.example .env`
2. 在 `.env` 中填写 `OPENAI_API_KEY=你的密钥`
3. 可选：`LLM_MODEL`、`LLM_BASE_URL` 可在 `.env` 中覆盖（见 .env.example 注释）

步骤四（LLM 整理大纲、思维导图等）运行前需在 `.env` 中配置 `OPENAI_API_KEY`。  
若 OpenAI 不可用或流量受限，可改用**国内 LLM**（DeepSeek / 智谱 GLM-4 / 通义千问 / Kimi），只需改 `.env` 中的 `LLM_BASE_URL` 与 `LLM_MODEL`，详见 **[docs/LLM-国内推荐.md](docs/LLM-国内推荐.md)**。

## 依赖说明

| 包 | 用途 |
|----|------|
| moviepy | 从 MP4 抽离音频并导出为 MP3 |
| openai-whisper | 本地语音转写（模型在 config.py 中配置） |
| openai | 步骤四：调用大模型（OpenAI 或兼容接口） |
