# ezplm-component-risk-agent

**面向 eZ-PLM 的电子元器件智能选型与供应链风险评估 Agent 系统**

第二十一届中国研究生电子设计竞赛 · AI 智能体赛道

---

## 快速运行

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量（复制 .env.example 为 .env 并填写真实密钥）
cp .env.example .env

# 3. 构建 RAG 知识库（首次运行必需）
PYTHONPATH=. python3 scripts/build_knowledge_base.py

# 4. 启动后端（FastAPI）
PYTHONPATH=. python3 -m uvicorn app.main:app --reload --port 8000

# 5. 启动前端演示（Streamlit）
PYTHONPATH=. python3 -m streamlit run frontend/streamlit_app.py

# 6. 运行评测
PYTHONPATH=. python3 tests/eval_runner.py
```

> **注意**：所有脚本需在项目根目录下加 `PYTHONPATH=.` 运行。

---

## 项目现状（2026-06-01）

### 核心模块

| 模块 | 文件 | 说明 |
|------|------|------|
| 数据模型 | `app/schemas.py` | PartIR / RiskIR / TopologyIR / ScoreBreakdown，Pydantic v2 |
| 需求解析 | `app/requirement_parser.py` | 四级容错链：LLM 语义 → 规则覆盖 → 电压兜底 → 温度匹配 |
| eZ-PLM 客户端 | `app/ezplm_client.py` | HMAC-SHA256 签名 + 多前缀分组查询 + MPN 电压推断 + Mock 兜底 |
| LLM 客户端 | `app/llm_client.py` | DeepSeek/OpenAI 兼容，需求解析 + 器件评分双 Prompt |
| 混合评分 | `app/scoring.py` | 双模自适应（rule_only / llm_enhanced）+ 去重 + Top-N 分级 |
| 证据链 | `app/evidence.py` | 8 类字段级证据，含置信度与人工复核标记 |
| 风险报告 | `app/report_generator.py` | 13 条规则引擎 + LLM 叙述分离 + FMEA RPN + 5×5 热力矩阵 |
| 报告输出 | `app/output_generator.py` | BOM / 风险评估 / 拓扑分析 Markdown + TopologyIR JSON |
| BOM 输出 | `app/output_bom.py` | BOM 选型清单 Markdown 渲染（独立模块） |
| Pipeline 调度 | `app/agent_orchestrator.py` | 五阶段流水线 + RAG 自动检索 + 参考设计拉取 |
| RAG 知识库 | `app/rag.py` | ChromaDB + sentence-transformers，29 条工程知识（11 个类别） |
| ReAct Agent | `app/react_agent.py` | LangChain 1.3，4 工具，多轮会话，幻觉检测 |
| Agent 工具 | `app/agent_tools.py` | search / knowledge / alternatives / report |
| 数据手册 RAG | `app/datasheet_rag.py` | 数据手册 QA 模块 |
| FastAPI 服务 | `app/main.py` | `/health` `/analyze` `/replacement` `/agent/chat` `/agent/sessions` |
| 调试日志 | `app/log_util.py` | 调试日志工具 |

### 数据与知识库

| 资源 | 说明 |
|------|------|
| Mock 器件库 | `data/mock_parts.json` — 1,237 条（Buck/Boost/LDO，国产/进口，车规/非车规） |
| RAG 知识条目 | `data/knowledge/engineering_knowledge.json` — 29 条（Buck/Boost/LDO 设计 + 热管理/车规/Layout/供应链/EMI/可靠性） |
| ChromaDB 向量库 | `data/chroma_db/` — 持久化存储，384 维向量 |

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
| 门型展架（80×180cm） | ⬜ |
| 作品展示照片（5 张） | ⬜ |

---

## 代码文件说明

### 应用层（`app/`）

| 文件 | 功能 |
|------|------|
| `schemas.py` | PartIR / RiskIR / TopologyIR / ScoreBreakdown 等全部 IR 数据模型 |
| `requirement_parser.py` | 四级容错需求解析链（LLM + 规则 + 电压兜底 + 温度匹配） |
| `ezplm_client.py` | eZ-PLM API HMAC 签名客户端 + Mock 兜底 + MPN 电压推断 |
| `llm_client.py` | DeepSeek/OpenAI 兼容 LLM（需求解析 + 器件评分双 Prompt） |
| `scoring.py` | 双模混合评分（rule_only / llm_enhanced）+ 去重 + Top-N |
| `evidence.py` | 8 类字段级证据链（含置信度 + 人工复核标记） |
| `report_generator.py` | 双层风险评估（13 条规则引擎 + LLM 叙述分离） |
| `output_generator.py` | BOM / 风险评估 / 拓扑分析 Markdown + TopologyIR JSON |
| `output_bom.py` | BOM 选型清单生成（独立模块） |
| `agent_orchestrator.py` | Pipeline 主调度 + RAG 检索 + LLM 参考设计拉取 |
| `main.py` | FastAPI 服务（5 端点） |
| `rag.py` | ChromaDB 向量存储 + sentence-transformers 语义检索 |
| `agent_tools.py` | 4 个 LangChain Tool（搜索/知识/替代/报告） |
| `react_agent.py` | ReAct Agent + 多轮会话管理 + 幻觉检测 |
| `datasheet_rag.py` | 数据手册 RAG 模块 |
| `log_util.py` | 调试日志工具 |

### 前端 / 脚本 / 数据

| 路径 | 说明 |
|------|------|
| `frontend/streamlit_app.py` | Streamlit 增强版 UI，竞赛三场景快捷入口 |
| `scripts/build_knowledge_base.py` | RAG 知识库构建（`--rebuild` / `--query`） |
| `scripts/import_parts_from_api.py` | eZ-PLM API 批量导入 |
| `scripts/llm_demo.py` | LLM 需求解析快速验证 |
| `scripts/eval_for_paper.py` | 论文评测数据采集脚本 |
| `data/mock_parts.json` | 1,237 条 Mock 器件 |
| `data/knowledge/engineering_knowledge.json` | 29 条 RAG 工程知识 |

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

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/health` | 健康检查 |
| `POST` | `/analyze` | Pipeline 选型分析，返回 SelectionReport JSON |
| `POST` | `/replacement` | 替代器件查找，返回 ReplacementReport JSON |
| `POST` | `/agent/chat` | ReAct Agent 对话，支持 `session_id` 多轮 |
| `GET` | `/agent/sessions` | 查看活跃 Agent 会话 |

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
| `EZPLM_API_KEY` | 否 | eZ-PLM API 密钥；未填则使用 mock 数据 |
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
