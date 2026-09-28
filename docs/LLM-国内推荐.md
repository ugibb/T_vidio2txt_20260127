# 国内 LLM 推荐（替代 OpenAI，用于步骤四）

**当前项目默认**：**Kimi 月之暗面**（moonshot-v1-32k）。通义、智谱、DeepSeek 等仍可通过 `.env` 中 `LLM_BASE_URL`、`LLM_MODEL` 切换，**无需改代码**。

本项目步骤四（大纲、思维导图等）使用 **OpenAI 兼容接口**，只需在 `.env` 中配置 `OPENAI_API_KEY`（各平台 Key 均用此变量名），如需更换 LLM 再设置 `LLM_BASE_URL`、`LLM_MODEL` 即可。

以下为国内最匹配「长文本整理、大纲、思维导图」的推荐。

---

## 当前默认：Kimi（月之暗面）

- **能力**：超长上下文（8k/32k/128k 可选），适合长转写、大纲、思维导图。
- **价格**：按量计费。国内在 **Kimi Code（platform.moonshot.cn）** 或全球 **platform.moonshot.ai** 注册并创建 API Key。

**重要**：Key 与 API 端点必须对应，否则会 401 Invalid Authentication。
- **国内 Key**（在 platform.moonshot.cn / Kimi Code 创建，通常以 `sk-kimi-` 开头）→ 必须设置 **`LLM_BASE_URL=https://api.moonshot.cn/v1`**
- **全球 Key**（在 platform.moonshot.ai 创建）→ 使用默认 `https://api.moonshot.ai/v1` 即可，可不写 `LLM_BASE_URL`

**`.env` 配置示例（国内 Kimi Code，K2.5 旗舰）：**

```bash
OPENAI_API_KEY=你的Kimi密钥
LLM_BASE_URL=https://api.moonshot.cn/v1
# 可选：LLM_MODEL=kimi-k2.5（默认）或 kimi-k2.5-preview / kimi-k2-0905-preview / moonshot-v1-32k
```

**`.env` 配置示例（全球 Kimi）：**

```bash
OPENAI_API_KEY=你的Kimi密钥
# 可选：LLM_MODEL=moonshot-v1-8k 或 moonshot-v1-32k（默认）或 moonshot-v1-128k
```

- 国内开放平台：<https://platform.moonshot.cn>（Kimi Code）  
- 全球开放平台：<https://platform.moonshot.ai>

---

## 备选：DeepSeek

- **能力**：长文本理解与生成强，适合大纲提取、章节概要、加标点、思维导图；中文表现好；128K 上下文。
- **价格**：约为 GPT-4 的 1/3，性价比高。
- **网络**：国内可直接访问官方 API。

**`.env` 配置示例：**

```bash
# 在 platform.deepseek.com 注册并创建 API Key
OPENAI_API_KEY=sk-你的DeepSeek密钥
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
```

- 开放平台：<https://platform.deepseek.com>
- 文档：<https://platform.deepseek.com/docs>

---

## 备选一：智谱 GLM-4

- **能力**：GLM-4 文档理解与结构化输出好，适合大纲、概要、思维导图；接口与 OpenAI 兼容。
- **价格**：按量计费，有免费额度。

**`.env` 配置示例：**

```bash
# 在 open.bigmodel.cn 注册并创建 API Key
OPENAI_API_KEY=你的智谱API密钥
LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4
LLM_MODEL=glm-4
```

- 开放平台：<https://open.bigmodel.cn>
- 文档：<https://docs.bigmodel.cn>

---

## 备选二：通义千问（阿里云 DashScope）

- **能力**：通义千问-Max 长文本与多轮理解好，适合课程/讲座类整理。
- **价格**：按量计费，新用户有额度。

**认证说明（必读）**：本项目使用 DashScope 的 **OpenAI 兼容接口**，认证方式为 **百炼 API Key**（格式 `sk-` 开头），**不能**使用阿里云 RAM 的 accessKeyId + accessKeySecret。  
请在 **百炼控制台 → API-Key** 创建密钥：<https://bailian.console.aliyun.com/?tab=model#/api-key>  
（用阿里云账号登录后，在「模型服务灵积 / 百炼」里创建 API Key，不是 RAM 访问密钥。）

**`.env` 配置示例：**

```bash
# 使用上面获取的百炼 API Key（sk- 开头）
OPENAI_API_KEY=sk-你的百炼API密钥
# 或单独为通义配置：DASHSCOPE_API_KEY=sk-你的百炼API密钥

LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-max
```

- 开放平台：<https://dashscope.console.aliyun.com>
- API Key 获取：<https://bailian.console.aliyun.com/?tab=model#/api-key>
- 兼容说明：<https://help.aliyun.com/zh/model-studio/compatibility-of-openai-with-dashscope>

---

## 小结

| 厂商       | 推荐场景           | 上下文   | 备注                 |
|------------|--------------------|----------|----------------------|
| **Kimi**   | **当前默认**       | 8k/32k/128k | 超长上下文、moonshot.ai |
| DeepSeek   | 综合强、性价比高   | 128K     | 国内直连、便宜       |
| 智谱 GLM-4 | 大纲/思维导图稳定  | 128K     | 兼容性好             |
| 通义千问   | 阿里生态、长文本  | 较长     | 需百炼 API Key       |

**操作步骤：** 在对应平台注册 → 创建 API Key → 在项目根目录 `.env` 中填入上述三行（`OPENAI_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL`）→ 运行 `python3 src/step4.py` 或 `python3 src/run_all.py`。
