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
PYTHONPATH=. uvicorn app.main:app --reload --port 8000

# 5. 启动前端演示（Streamlit）
PYTHONPATH=. streamlit run frontend/streamlit_app.py

# 6. 运行评测
PYTHONPATH=. python3 tests/eval_runner.py
```

> **注意**：所有脚本需在项目根目录下加 `PYTHONPATH=.` 运行。

---

## 当前进展（2026-05-28 晚）

### 已完成模块

| 模块 | 文件 | 状态 | 说明 |
|------|------|:----:|------|
| 数据模型 | `app/schemas.py` | ✅ | PartIR / RiskIR / TopologyIR / ScoreBreakdown，Pydantic v2 + dataclass 双实现 |
| 需求解析 | `app/requirement_parser.py` | ✅ | 四级容错链：LLM 语义 → 规则覆盖 → 电压兜底 → 温度匹配 |
| eZ-PLM 客户端 | `app/ezplm_client.py` | ✅ | HMAC-SHA256 签名 + 多前缀分组查询 + MPN 电压推断 + Mock 兜底 |
| LLM 客户端 | `app/llm_client.py` | ✅ | DeepSeek/OpenAI 兼容，需求解析 + 器件评分双 Prompt |
| 混合评分 | `app/scoring.py` | ✅ | 双模自适应（rule_only / llm_enhanced）+ 去重 + Top-N 分级 |
| 证据链 | `app/evidence.py` | ✅ | 8 类字段级证据，含置信度与人工复核标记 |
| 风险报告 | `app/report_generator.py` | ✅ | 13 条规则引擎 + LLM 叙述分离 + FMEA RPN + 5×5 热力矩阵 |
| 报告输出 | `app/output_generator.py` | ✅ | BOM / 风险评估 / 拓扑分析 Markdown + TopologyIR JSON |
| Pipeline 调度 | `app/agent_orchestrator.py` | ✅ | 五阶段流水线 + RAG 自动检索 + 参考设计拉取 |
| RAG 知识库 | `app/rag.py` | ✅ | ChromaDB + sentence-transformers，12 条工程知识 |
| ReAct Agent | `app/react_agent.py` | ✅ | LangChain 1.3，4 工具，多轮会话 |
| Agent 工具 | `app/agent_tools.py` | ✅ | search / knowledge / alternatives / report |
| 数据手册 RAG | `app/datasheet_rag.py` | ✅ | 数据手册 QA 模块（队员 B） |
| FastAPI 服务 | `app/main.py` | ✅ | `/health` `/analyze` `/replacement` `/agent/chat` `/agent/sessions` |
| Mock 数据 | `data/mock_parts.json` | ✅ | 209 条（Buck/Boost/LDO，国产/进口，车规/非车规） |
| RAG 知识条目 | `data/knowledge/` | ✅ | 12 条（Buck 设计/热管理/车规/Layout/供应链） |
| Streamlit 前端 | `frontend/streamlit_app.py` | ✅ | 增强版 UI（队员 A） |
| 评测框架 | `tests/eval_runner.py` | ✅ | 20 条用例，90% 通过率（队员 A 扩展） |
| PDF 报告生成 | `generate_detailed_pdf.py` | ✅ | 中文 PDF 工作报告（队员 B） |
| 技术论文 | `latex-paper/` | ✅ | LaTeX 6 章 + 40 篇参考文献，Overleaf-ready |
| CI/CD | `.github/workflows/` | ✅ | Python 3.11 自动评测 |

### 评测结果

```
队员 A 20 条用例版：18/20（90%）
队长 10 条用例版：  10/10（100%）
```

---

## 分支合并状态（2026-05-28 晚）

| 分支 | 负责人 | 提交数 | 状态 |
|------|--------|:------:|:----:|
| `feature/backend/more-mock-data` | 队员 B | — | ✅ 已合并至 main（5/28 上午） |
| `feature/backend/api-integration` | 队员 B | 10 | ✅ 已合并至 main（5/28 晚） |
| `feature/frontend/eval-report` | 队员 A | 3 | ✅ 已合并至 main（5/28 晚） |
| `feature/frontend/ui-v2` | 队员 A | 0 | ✅ 已包含于 eval-report |

> 当前 GitHub 仅保留 `main` 分支（43 次提交）。详细合并报告见 [`docs/merge-report-2026-05-28.md`](docs/merge-report-2026-05-28.md)。

---

## 项目规划进度

| 规划项 | 原计划周 | 状态 |
|--------|:-------:|:----:|
| IR 数据模型 (PartIR/RiskIR/TopologyIR) | W1 | ✅ |
| eZ-PLM API HMAC 签名客户端 | W1 | ✅ |
| ChromaDB 向量知识库 + RAG 集成 | W2 | ✅ |
| LangChain ReAct Agent + 多轮对话 | W3 | ✅ |
| 场景 1 USB-C PD 方案 | W3 | 🟡 基础 Pipeline 可演示 |
| 场景 2 车规降压方案 | W3 | 🟡 mock 缺车规 5V 器件 |
| 场景 3 国产替代追问 | W3 | ✅ Agent 多轮对话可演示 |
| FastAPI + Streamlit 联调 | W4 | ✅ 四端点就绪，前端增强版 |
| 技术论文 | W4-5 | ✅ LaTeX 初稿完成 |
| 演示视频 / PPT / 展架 | W5 | ⬜ |
| 专家评审表 | — | ⬜ |

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
| `agent_orchestrator.py` | Pipeline 主调度 + RAG 检索 + LLM 参考设计拉取 |
| `main.py` | FastAPI 服务（5 端点） |
| `rag.py` | ChromaDB 向量存储 + sentence-transformers 语义检索 |
| `agent_tools.py` | 4 个 LangChain Tool（搜索/知识/替代/报告） |
| `react_agent.py` | ReAct Agent + 多轮会话管理 |
| `datasheet_rag.py` | 数据手册 RAG 模块（队员 B） |

### 前端 / 脚本 / 数据

| 路径 | 说明 |
|------|------|
| `frontend/streamlit_app.py` | Streamlit 增强版 UI（队员 A） |
| `scripts/build_knowledge_base.py` | RAG 知识库构建（`--rebuild` / `--query`） |
| `scripts/import_parts_from_api.py` | eZ-PLM API 批量导入 |
| `scripts/llm_demo.py` | LLM 需求解析快速验证 |
| `data/mock_parts.json` | 209 条 Mock 器件 |
| `data/knowledge/engineering_knowledge.json` | 12 条 RAG 工程知识 |
| `generate_detailed_pdf.py` | PDF 工作报告生成（队员 B） |

### 测试 / 文档

| 路径 | 说明 |
|------|------|
| `tests/eval_runner.py` | 20 条用例自动评测框架（队员 A 扩展） |
| `tests/cases/dc_dc_cases.jsonl` | DC-DC 评测用例 |
| `latex-paper/` | 技术论文 LaTeX 包（XeLaTeX 编译） |
| `docs/daily/` | 工作日报 |
| `docs/merge-report-2026-05-28.md` | 分支合并详细报告 |
| `docs/eval_results/` | 评测结果（队员 A） |

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

# Agent 对话（单轮）
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
