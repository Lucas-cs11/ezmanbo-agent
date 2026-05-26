# ezplm-component-risk-agent

本仓库为“面向 eZ-PLM 的电子元器件选型与供应链风险评估智能体”项目的代码仓库（最小可运行版本）。

快速运行

- 启动后端（FastAPI）：

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

- 启动前端演示（Streamlit）：

```bash
streamlit run frontend/streamlit_app.py
```

代码文件与功能说明（简体中文）

- `app/`：后端主代码目录
  - `app/schemas.py`：项目的 IR（数据契约），包含 `RequirementConstraints`、`PartIR`、`ScoredPart`、`EvidenceIR`、`RiskIR`、`SelectionReport` 等数据模型。
  - `app/requirement_parser.py`：把用户的自然语言需求解析成结构化 `RequirementConstraints`（当前采用正则和规则的混合解析器）。
  - `app/ezplm_client.py`：Mock 的元器件检索客户端，从 `data/mock_parts.json` 读取并提供 `search_parts`、`find_replacements` 接口，后续可替换为真实 eZ-PLM API。
  - `app/scoring.py`：多维评分模块，基于参数匹配、供应链风险、成本、国产替代和证据覆盖等维度计算分数并输出 `ScoredPart`。
  - `app/evidence.py`：根据候选器件和评分结果生成证据链 `EvidenceIR`。
  - `app/agent_orchestrator.py`：主流程编排（deterministic）：解析需求 → 检索 → 评分 → 生成证据 → 生成报告。
  - `app/report_generator.py`：把结构化结果生成 `SelectionReport`，并生成文本摘要（用于前端或 Demo 展示）。
  - `app/main.py`：FastAPI 入口，提供 `/health`、`/analyze`、`/replacement` 等最小接口。

- `data/`
  - `data/mock_parts.json`：Mock 元器件库（当前包含若干 DC-DC Buck 示例，后续扩充到 >=30 条用于评测）。

- `frontend/`
  - `frontend/streamlit_app.py`：最小的 Streamlit 演示页面，用于输入需求并展示 `SelectionReport` 的 JSON 输出（演示用途）。

- `tests/`
  - `tests/cases/dc_dc_cases.jsonl`：JSONL 格式的测试用例（当前包含 5 条 DC-DC 用例）。
  - `tests/eval_runner.py`：自动评测脚本，读取用例并调用 `agent_orchestrator.analyze()`，输出评测结果到 `docs/eval_results.md`。

- `.github/`：包含 CI 工作流和 PR 模板
  - `.github/workflows/ci-python-3.11.yml`：GitHub Actions CI（Python 3.11），用于在推送/PR 时运行自动评测。
  - `.github/PULL_REQUEST_TEMPLATE.md`：PR 描述模板。

- 其它：`requirements.txt`（依赖）、`.gitignore` 等。

团队分工（建议与当前人员匹配）

- 队长（AI 工程师 / 技术负责人） — 负责总体设计与核心模块：
  - 主要修改/负责文件：`app/schemas.py`、`app/requirement_parser.py`、`app/scoring.py`、`app/evidence.py`、`app/agent_orchestrator.py`、`app/report_generator.py`。
  - 任务列表：设计 IR、定义评分规则、撰写和维护测试标准、实现需求解析逻辑、保证评分可解释性、撰写论文技术部分。

- 队员 B（后端 / 数据） — 负责 Mock 数据和后端接口：
  - 主要修改/负责文件：`data/mock_parts.json`、`app/ezplm_client.py`、`app/main.py`、CI 配置（`.github/workflows/ci-python-3.11.yml`）。
  - 任务列表：扩充并维护 Mock 元器件库（目标 >=30 条）、实现与维护 FastAPI 接口、保证检索逻辑贴合 IR 约束、对接后续真实 eZ-PLM API（接口可替换）。

- 队员 A（前端 / 测试 / 文档） — 负责前端和交付材料：
  - 主要修改/负责文件：`frontend/streamlit_app.py`、`tests/cases/*.jsonl`、`tests/eval_runner.py`、`README.md`、演示材料（docs/）。
  - 任务列表：实现 Streamlit 演示页面、整理与扩展测试用例（目标 20 条）、运行并记录评测结果、准备 Demo解说词与 README 操作说明、制作演示视频素材。

每个成员对应的初始待办（建议优先级）

1. 队长（高优先级）
   - 完成 `app/schemas.py` 的最终字段确认并在代码中注释字段含义。
   - 完善 `requirement_parser` 以覆盖主 Demo 句式并增加更多正则/提示测试用例。
   - 定义并实现评分权重与 `scoring.py` 的规则化计算（保证解释性）。

2. 队员 B（高优先级）
   - 把 `data/mock_parts.json` 扩充至 >=30 条 DC-DC / 其它类别（确保包含国产/进口标记）。
   - 检查并完善 `app/ezplm_client.py` 的筛选逻辑，确保满足硬过滤条件。
   - 配置 CI（已添加 GitHub Actions 基础工作流），调通后确保 CI 能通过评测脚本。

3. 队员 A（中优先级）
   - 将测试用例扩展到 20 条并保存到 `tests/cases/`。
   - 美化/完善 `frontend/streamlit_app.py` 的展示格式并确保其与后端联通。
   - 补充 README（本文件已初步完善），准备 Demo 文档与演示脚本。

如何协作（建议）

- 使用 GitHub Issues 跟踪每个待办，参考本仓库已有 Issue 模板；把任务拆成小 PR（例如 `feature/more-mock-parts`、`feature/ci-fix`、`feature/llm-client`）。
- CI 运行在 `main` 分支和 PR 上（已添加 3.11 工作流），确保每次合并前通过 `tests/eval_runner.py`。
- 在需要 LLM 支持的模块（未来）统一通过 `app/llm_client.py` 调用，保持业务逻辑与模型调用解耦。

如需我继续：
- 我可以现在为你在仓库中自动创建首批 Issues（包括：扩充 Mock 数据、添加 CI、扩展测试、实现 llm_client 骨架、完善 README），并为每个 Issue 生成査单（任务分解）。
- 或者我可以直接开始扩充 `data/mock_parts.json`（生成 30 条 Mock 条目）。

请回复你想让我继续做的下一件事：
- `创建 Issues` / `扩充 Mock 数据` / `实现 llm_client 骨架` / `其他：...`


