# ezplm-component-risk-agent

**面向 eZ-PLM 的电子元器件智能选型与供应链风险评估 Agent 系统**

第二十一届中国研究生电子设计竞赛 · AI 智能体赛道

---

## 快速运行（一键克隆部署）

```bash
# 0. 克隆仓库
git clone https://github.com/Lucas-cs11/ezplm-component-risk-agent.git
cd ezplm-component-risk-agent

# 1. 一键环境搭建
chmod +x setup.sh && ./setup.sh

# 2. 编辑 .env 填写 API 密钥（EZPLM_API_KEY、OPENAI_API_KEY）
vim .env

# 3. 启动后端（FastAPI）
PYTHONPATH=. python3 -m uvicorn app.main:app --reload --port 8000

# 4. 启动 Web 前端（Next.js，推荐）
cd frontend/web && npm install && npm run dev

# 5. （可选）启动旧版 Streamlit UI
PYTHONPATH=. streamlit run frontend/streamlit_app.py
```

> **环境要求**：Python 3.9+ | Node.js 18+ | macOS / Linux / WSL2

> **数据手册下载**（可选，已有 49 份预置）：`PYTHONPATH=. python3 scripts/download_datasheets.py`

---

## 项目现状（2026-06-18）

### 核心模块

| 模块 | 文件 | 说明 |
|------|------|------|
| 数据模型 | `app/schemas.py` | PartIR / RiskIR / TopologyIR / ScoreBreakdown 等 13 个 Pydantic v2 模型，含 Field(ge=0) 校验 |
| 需求解析 | `app/requirement_parser.py` | 四级容错链：LLM 语义 → 规则覆盖 → 电压兜底 → 温度匹配 |
| 约束校验 | `app/constraint_checker.py` | 需求约束完整性与合理性校验 |
| 意图分类 | `app/intent_classifier.py` | 三层意图分类：选型 / 对话 / 替换 |
| eZ-PLM 客户端 | `app/ezplm_client.py` | HMAC-SHA256 签名 + 多前缀分组查询 + 详情富化 + LRU 缓存淘汰 |
| LLM 客户端 | `app/llm_client.py` | DeepSeek/OpenAI 兼容，需求解析 + 器件评分双 Prompt |
| 混合评分 | `app/scoring.py` | **Scoring v2.0**：五层复合模型（Gate → Fit F → Risk R → Confidence C → Robustness B → RS），52 厂商统一白名单，车规/工业/消费三档成本基准 |
| 证据链 | `app/evidence.py` | 字段级证据 + 置信度 + 数据手册本地验证（S=1.00 最高可靠度） |
| 风险评估 | `app/report_generator.py` | **十维风险评估引擎**（ISO 31000 / IEC 60812）：D1–D10 加权评分 + 门禁项 + 0–100 风险指数 |
| 报告输出 | `app/output_generator.py` | BOM / 风险评估 / 拓扑分析 Markdown + TopologyIR JSON |
| BOM 输出 | `app/output_bom.py` | **专业 EBOM**：29 列主表 + AVL/AML + 供应链风险 + Excel 4-Sheet 导出 |
| Pipeline 编排 | `app/agent_orchestrator.py` | 7 阶段流水线 + RAG 检索 + 参考设计 + session 隔离 |
| LangGraph 编排 | `app/langgraph_orchestrator.py` | LangGraph 工作流编排（增强模式） |
| RAG 知识库 | `app/rag.py` | ChromaDB + sentence-transformers（all-MiniLM-L6-v2），离线容错 |
| ReAct Agent | `app/react_agent.py` | LangChain 1.3，4 工具，多轮会话，幻觉检测 |
| Agent 工具 | `app/agent_tools.py` | search / knowledge / alternatives / report |
| 工具 Schema | `app/tool_schema.py` | Agent 工具 JSON Schema 定义 |
| 数据手册解析 | `app/datasheet_parser.py` | PyMuPDF 解析 + 章节检测 + 滑动窗口分块（51 条正则模式覆盖 TI/ADI/ST/Microchip） |
| 数据手册 RAG | `app/datasheet_rag.py` | **50 器件注册表**（TI 22 / ADI 11 / Microchip 7 / ST 10）+ 双重注册验证 |
| 语义缓存 | `app/semantic_cache.py` | 选型结果语义缓存（减少重复 API 调用） |
| 会话记忆 | `app/memory.py` | Agent 会话记忆管理 |
| 深度思考 | `app/thinking.py` | LLM 思考深度控制 |
| FastAPI 服务 | `app/main.py` | **13 个 API 端点**（流式 SSE + session 隔离 + CORS 环境变量 + 文件上传增强） |
| 调试日志 | `app/log_util.py` | 结构化调试日志 |

### 数据与知识库

| 资源 | 说明 |
|------|------|
| eZ-PLM API | TI / ADI / Microchip / ST 四厂商物料；HMAC-SHA256 签名，24h 关键词缓存，详情富化 |
| 工程知识 RAG | `data/knowledge/` — 29 条（Buck/Boost/LDO 设计 + 热管理/车规/Layout/供应链/EMI/可靠性） |
| 数据手册 RAG | **50 器件 × 8,021 chunks** — 10 种 field type（overview / pinout / electrical / thermal / layout / package / application / absolute_max / typical_perf / general），384 维向量 |
| ChromaDB | `data/chroma_db/` — 持久化存储，cosine 距离 |

### 评测结果

| 评测 | 用例数 | 通过率 |
|------|:------:|:------:|
| 端到端 Pipeline | 28 条（Buck 14 + Boost 4 + LDO 10） | 100% |
| 核心字段解析准确率 | 7 个字段 | 100% |
| 证据链 | 846 条（平均置信度 0.90） | — |
| 端到端延迟 | 28 条用例 | 中位数 4.55s |

### 竞赛提交材料进度

| 材料 | 状态 |
|------|:----:|
| 技术论文（LaTeX，~8,400 字正文，30 页，38 篇参考文献） | ✅ 定稿 |
| 完整源代码（89 commits） | ✅ |
| 演示视频（MP4，1080p，3–5 分钟） | ⬜ |
| 答辩 PPT（15–20 页） | ⬜ |
| 复现文档 | ⬜ |
| eZ-PLM 对接文档 | 🟡 |
| 作品展示照片（5 张） | ⬜ |

---

## 代码文件说明

### 应用层（`app/`，共 23 个模块）

| 文件 | 功能 |
|------|------|
| `schemas.py` | 13 个 Pydantic v2 数据模型（含 Field(ge=0) 校验） |
| `requirement_parser.py` | 四级容错需求解析 |
| `constraint_checker.py` | 需求约束完整性与合理性校验 |
| `intent_classifier.py` | 三层意图分类（选型/对话/替换） |
| `ezplm_client.py` | eZ-PLM HMAC-SHA256 客户端 + LRU 缓存 |
| `llm_client.py` | DeepSeek/OpenAI 兼容 LLM 客户端 |
| `scoring.py` | **Scoring v2.0** 五层复合评分 |
| `evidence.py` | 字段级证据链 + 数据手册本地验证 |
| `report_generator.py` | 十维风险评估引擎 |
| `output_generator.py` | Markdown + JSON 报告输出 |
| `output_bom.py` | EBOM 29 列 + Excel 4-Sheet |
| `agent_orchestrator.py` | 7 阶段 Pipeline + session 隔离 |
| `langgraph_orchestrator.py` | LangGraph 工作流编排 |
| `rag.py` | ChromaDB + sentence-transformers |
| `react_agent.py` | ReAct Agent 多轮会话 |
| `agent_tools.py` | 4 个 LangChain Tool |
| `tool_schema.py` | Agent 工具 JSON Schema |
| `datasheet_parser.py` | PyMuPDF 解析 + 章节检测 + 滑窗分块 |
| `datasheet_rag.py` | 50 器件注册表 + 双重验证 |
| `semantic_cache.py` | 选型语义缓存 |
| `memory.py` | Agent 会话记忆 |
| `thinking.py` | LLM 思考深度控制 |
| `main.py` | FastAPI **13 端点** + SSE 流式 + CORS 环境变量 |
| `log_util.py` | 结构化日志 |

### 前端 / 脚本 / 数据

| 路径 | 说明 |
|------|------|
| `frontend/web/` | **Next.js 14 Web UI**（12 组件 + Zustand + SSE 流式 + DOMPurify + Tailwind CSS） |
| `frontend/streamlit_app.py` | Streamlit 旧版 UI（竞赛三场景快捷入口） |
| `scripts/build_knowledge_base.py` | RAG 工程知识库构建 |
| `scripts/download_datasheets.py` | 批量下载 50 份数据手册 PDF（断点续传） |
| `scripts/ingest_datasheets.py` | 全管线：下载 → 解析 → 分块 → 灌入 ChromaDB |
| `scripts/eval_for_paper.py` | 论文评测数据采集 |
| `scripts/llm_demo.py` | LLM 需求解析快速验证 |
| `docs/datasheets/` | 49 份数据手册 PDF（~110MB） |
| `data/knowledge/` | 29 条 RAG 工程知识 |

### 测试 / 论文 / 文档

| 路径 | 说明 |
|------|------|
| `tests/eval_runner.py` | 自动评测框架 |
| `tests/cases/dc_dc_cases.jsonl` | DC-DC 评测用例 |
| `tests/cases/ldo_cases.jsonl` | LDO 评测用例 |
| `面向eZ_PLM的...系统v3/` | 技术论文 LaTeX 包（XeLaTeX → BibTeX → XeLaTeX ×2 编译） |
| `docs/merge-report-2026-05-28.md` | 分支合并详细报告 |
| `docs/eval_results/` | 评测结果 |

---

## API 端点（13 个）

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/health` | 健康检查（前端 30s 轮询 + 连接指示器） |
| `POST` | `/analyze` | （同步版，已弃用；请使用流式版） |
| `POST` | `/analyze/stream` | **SSE 流式选型**：7 阶段进度 + 实时评分 + session 隔离 |
| `POST` | `/replacement` | 替代器件查找，前端 `/replace` 命令入口 |
| `POST` | `/classify` | 三层意图分类 |
| `POST` | `/agent/chat` | ReAct Agent 单轮对话 |
| `POST` | `/agent/chat/stream` | **SSE 流式对话**：思考过程 + 正文分步推送 |
| `GET` | `/agent/sessions` | 活跃会话列表（前后端自动同步） |
| `POST` | `/agent/init_session` | 预注入选型上下文的会话创建 |
| `GET` | `/schematic/{topology}` | 参数化电路图 SVG（`?Vin=12&Vout=5&Iout=3`） |
| `GET` | `/report/{report_type}` | BOM / 风险 / 拓扑三类报告 |
| `POST` | `/upload/parse` | 文件上传解析（PDF 30 页 + Excel 全 Sheet） |
| `POST` | `/export/bom` | BOM Excel 导出 |

### 调用示例

```bash
# Pipeline 选型
curl -s -X POST http://localhost:8000/analyze \
  -H 'Content-Type: application/json' \
  -d '{"user_input":"12V转5V 3A 车规"}' | python3 -m json.tool

# Agent 单轮对话
curl -s -X POST http://localhost:8000/agent/chat \
  -H 'Content-Type: application/json' \
  -d '{"user_input":"12V转5V 3A buck降压芯片推荐"}'

# Agent 多轮追问
curl -s -X POST http://localhost:8000/agent/chat \
  -H 'Content-Type: application/json' \
  -d '{"user_input":"第一个推荐方案有国产替代吗？","session_id":"<上一步返回的 session_id>"}'
```

---

## 环境变量说明

| 变量 | 必填 | 说明 |
|------|:----:|------|
| `EZPLM_API_KEY` | **是** | eZ-PLM API 密钥；未填则无法查询器件数据 |
| `EZPLM_BASE_URL` | 否 | eZ-PLM API 地址，默认 `https://www.ezplm.cn` |
| `OPENAI_API_KEY` | 否 | LLM 密钥（DeepSeek/OpenAI）；未填则纯规则模式 |
| `OPENAI_BASE_URL` | 否 | LLM 地址；DeepSeek 设为 `https://api.deepseek.com` |
| `OPENAI_MODEL` | 否 | 模型名称；DeepSeek 设为 `deepseek-chat` |

复制 `.env.example` 为 `.env` 并填写密钥。**`.env` 已在 `.gitignore` 中，勿提交。**

---

## 论文编译

```bash
cd "面向eZ_PLM的电子元器件智能选型与风险评估Agent系统v3"
xelatex main.tex
bibtex main
xelatex main.tex
xelatex main.tex
```

需安装 TeX Live 2025（含 `gbt7714` 宏包）及 Fandol 中文字体。

---

## 分支规范

```
main（唯一活跃分支，直接迭代）
  ↓ 如需并行开发，从 main 创建 feature/<角色>/<任务>
  ↓ Push → GitHub 发起 PR → 至少 1 人 Review → Squash & Merge
```

| 类型 | 格式 |
|------|------|
| 队长功能 | `feature/lead/<任务>` |
| 队员 B 功能 | `feature/backend/<任务>` |
| 队员 A 功能 | `feature/frontend/<任务>` |
| Bug 修复 | `fix/<简述>` |
