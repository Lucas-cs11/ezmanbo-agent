# ezplm-component-risk-agent

**面向 eZ-PLM 的电子元器件选型与供应链风险评估智能体**

---

## 快速运行

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置环境变量（复制 .env.example 为 .env 并填写真实密钥）
cp .env.example .env

# 3. 启动后端（FastAPI）
PYTHONPATH=. uvicorn app.main:app --reload --port 8000

# 4. 启动前端演示（Streamlit）
PYTHONPATH=. streamlit run frontend/streamlit_app.py

# 5. 运行评测
PYTHONPATH=. python tests/eval_runner.py
```

> **注意**：所有脚本需在项目根目录下加 `PYTHONPATH=.` 运行，或通过 FastAPI/Streamlit 入口启动。

---

## 当前进展（2026-05-26）

### 已完成

| 模块 | 状态 | 说明 |
|------|------|------|
| 数据契约 `schemas.py` | ✅ | 全部 IR 模型，双模式（Pydantic v2 / dataclass） |
| 需求解析 `requirement_parser.py` | ✅ | LLM 优先 + 规则兜底；支持中英文句式、输入/输出电压模式、LLM 输出归一化 |
| 多维评分 `scoring.py` | ✅ | 5 维加权（参数 35% + 供应 25% + 成本 15% + 国产 15% + 证据 10%） |
| 证据链 `evidence.py` | ✅ | 对每个候选器件生成字段级证据 |
| 报告生成 `report_generator.py` | ✅ | 输出 `SelectionReport`，含推荐分级与摘要 |
| 流程编排 `agent_orchestrator.py` | ✅ | 五步 pipeline：解析 → 检索 → 评分 → 证据 → 报告 |
| EZ-PLM 客户端 `ezplm_client.py` | ✅ | 支持真实 API（HMAC 签名）+ mock 数据兜底；适配真实返回格式 |
| LLM 客户端 `llm_client.py` | ✅ | OpenAI-compatible，已对接 DeepSeek |
| FastAPI 接口 `main.py` | ✅ | `/health` `/analyze` `/replacement` |
| Mock 数据 `mock_parts.json` | ✅ | 32 条 DC-DC Buck（国产/进口、车规/非车规、宽压/大电流/停产多场景） |
| Streamlit 演示 `streamlit_app.py` | 🔧 基础版 | 可输入需求、展示 JSON 报告，待完善 UI |
| 评测用例 `dc_dc_cases.jsonl` | ✅ | 10 条用例 |
| 评测脚本 `eval_runner.py` | ✅ | 自动化评测，输出 `docs/eval_results.md` |
| CI `.github/workflows/` | ✅ | Python 3.11 自动评测 |

### 评测结果（纯规则模式，无需 LLM）

```
dc_dc_001 ✅  dc_dc_002 ✅  dc_dc_003 ✅  dc_dc_004 ✅  dc_dc_005 ✅
dc_dc_006 ✅  dc_dc_007 ✅  dc_dc_008 ✅  dc_dc_009 ✅  dc_dc_010 ✅
通过率：10/10（100%）
```

---

## 后续四天工作安排

> 基准日期：2026-05-26，截止：2026-05-29

### Day 1（5/26，今日）— 基础设施 ✅

- [x] 修复 `requirement_parser.py` 语法错误 & LLM 输出归一化
- [x] 扩充 mock 数据至 32 条（含大电流/高压/停产场景）
- [x] 对接真实 EZ-PLM API，适配返回格式
- [x] 对接 DeepSeek LLM API
- [x] 评测 10/10 通过
- [x] 建立仓库管理规范（CODEOWNERS、分支策略、工作流）

### Day 2（5/27）— 核心功能完善

| 负责人 | 任务 | 分支 |
|--------|------|------|
| 队长 | 优化 `scoring.py` 权重与解释性字段；扩展 `requirement_parser` 句式覆盖 | `feature/lead/scoring-v2` |
| 队员 B | 扩充 mock 数据至 50+ 条（加入 LDO、Boost 类别）；完善 `/replacement` 接口 | `feature/backend/more-mock-data` |
| 队员 A | 将测试用例扩展至 20 条；美化 Streamlit UI（展示评分明细、证据链） | `feature/frontend/ui-v2` |

### Day 3（5/28）— 集成测试 & 文档

| 负责人 | 任务 | 分支 |
|--------|------|------|
| 队长 | 开启 LLM 的端到端评测；撰写论文技术部分 | `feature/lead/e2e-eval` |
| 队员 B | EZ-PLM 真实 API 联调（若白名单覆盖）；FastAPI 接口稳定性测试 | `feature/backend/api-integration` |
| 队员 A | 运行 20 条用例完整评测并输出报告；补充演示说明文档 | `feature/frontend/eval-report` |

### Day 4（5/29）— Demo 准备 & 收尾

| 负责人 | 任务 |
|--------|------|
| 队长 | 代码审查；评测报告确认；论文技术节定稿 |
| 队员 B | CI 全绿；部署验证（可选） |
| 队员 A | 演示脚本与视频素材；最终 README 更新；提交物料整理 |

---

## 每个人的工作流

### 通用流程（所有成员必须遵守）

```
main（受保护，禁止直接 push）
  ↓ git pull origin main
  ↓ git checkout -b feature/<角色>/<任务简述>
     开发 → 本地测试通过 → git commit
  ↓ git push origin feature/<角色>/<任务简述>
  ↓ GitHub 发起 Pull Request → main
  ↓ 等待 CI 通过 + 至少 1 人 Review
  ↓ Squash & Merge → main
```

### 分支命名规范

| 类型 | 格式 | 示例 |
|------|------|------|
| 队长功能 | `feature/lead/<任务>` | `feature/lead/scoring-v2` |
| 队员 B 功能 | `feature/backend/<任务>` | `feature/backend/more-mock-data` |
| 队员 A 功能 | `feature/frontend/<任务>` | `feature/frontend/ui-v2` |
| Bug 修复 | `fix/<简述>` | `fix/eval-runner-import` |

### 队长工作流

```bash
git checkout main && git pull origin main
git checkout -b feature/lead/scoring-v2

# 负责文件
# app/schemas.py  app/requirement_parser.py  app/scoring.py
# app/evidence.py  app/agent_orchestrator.py  app/report_generator.py  app/llm_client.py

# 本地验证
PYTHONPATH=. python3 scripts/llm_demo.py       # 验证解析
PYTHONPATH=. python3 tests/eval_runner.py       # 验证评测全通过

git add app/
git commit -m "feat(scoring): <描述>"
git push origin feature/lead/scoring-v2
# → GitHub 发起 PR，请求队员 A 或 B 审阅
```

### 队员 B 工作流

```bash
git checkout main && git pull origin main
git checkout -b feature/backend/more-mock-data

# 负责文件
# data/mock_parts.json  app/ezplm_client.py  app/main.py  .github/workflows/

# 新增 mock 数据后验证
PYTHONPATH=. python3 -c "
from app.ezplm_client import _load_parts
parts = _load_parts()
print(f'共 {len(parts)} 条器件')
"

# 接口验证（启动服务后）
curl -s -X POST http://localhost:8000/analyze \
  -H 'Content-Type: application/json' \
  -d '{"user_input":"12V转5V 3A 车规"}' | python3 -m json.tool

git add data/ app/ezplm_client.py app/main.py
git commit -m "feat(data): <描述>"
git push origin feature/backend/more-mock-data
# → GitHub 发起 PR，请求队长审阅
```

### 队员 A 工作流

```bash
git checkout main && git pull origin main
git checkout -b feature/frontend/ui-v2

# 负责文件
# frontend/streamlit_app.py  tests/cases/dc_dc_cases.jsonl
# tests/eval_runner.py  docs/  README.md

# 本地验证
PYTHONPATH=. python3 tests/eval_runner.py           # 评测全通过
PYTHONPATH=. streamlit run frontend/streamlit_app.py # 前端预览

git add frontend/ tests/ docs/ README.md
git commit -m "feat(frontend): <描述>"
git push origin feature/frontend/ui-v2
# → GitHub 发起 PR，请求队长审阅
```

---

## 仓库管理设置（GitHub 管理员操作一次）

以下设置在 **GitHub → Settings → Branches** 中手动完成：

1. **保护 `main` 分支**
   - ✅ Require a pull request before merging
   - ✅ Require at least 1 approving review
   - ✅ Require status checks to pass（选择 CI workflow）
   - ✅ Do not allow bypassing the above settings（包括管理员）

2. **启用 CODEOWNERS 自动指定审阅人**
   - 文件已在 `.github/CODEOWNERS`
   - 将其中 `@LEAD_GITHUB_USERNAME` 等占位符替换为真实 GitHub 用户名

---

## 代码文件说明

| 文件 | 负责人 | 功能 |
|------|--------|------|
| `app/schemas.py` | 队长 | 全部数据模型 IR |
| `app/requirement_parser.py` | 队长 | 自然语言 → 结构化约束（LLM + 规则） |
| `app/scoring.py` | 队长 | 5 维加权评分 |
| `app/evidence.py` | 队长 | 字段级证据链生成 |
| `app/agent_orchestrator.py` | 队长 | 五步流水线编排 |
| `app/report_generator.py` | 队长 | SelectionReport 组装 |
| `app/llm_client.py` | 队长 | OpenAI-compatible LLM 封装 |
| `app/ezplm_client.py` | 队员 B | EZ-PLM API 客户端（含 mock fallback） |
| `app/main.py` | 队员 B | FastAPI 入口 |
| `data/mock_parts.json` | 队员 B | 器件库（32 条） |
| `.github/workflows/` | 队员 B | CI 配置 |
| `frontend/streamlit_app.py` | 队员 A | Streamlit 演示页面 |
| `tests/cases/dc_dc_cases.jsonl` | 队员 A | 评测用例（10 条） |
| `tests/eval_runner.py` | 队员 A | 自动评测脚本 |
| `docs/` | 队员 A | 文档与评测报告 |
| `README.md` | 队员 A | 本文件 |
| `scripts/llm_demo.py` | 队长 | 需求解析快速验证 |

---

## 环境变量说明

| 变量 | 必填 | 说明 |
|------|------|------|
| `EZPLM_API_KEY` | 否 | EZ-PLM API 密钥；未填则使用 mock 数据 |
| `EZPLM_BASE_URL` | 否 | EZ-PLM API 地址，默认 `https://www.ezplm.cn` |
| `OPENAI_API_KEY` | 否 | LLM 密钥（DeepSeek/OpenAI）；未填则纯规则解析 |
| `OPENAI_BASE_URL` | 否 | LLM 地址；使用 DeepSeek 时设为 `https://api.deepseek.com` |
| `OPENAI_MODEL` | 否 | 模型名称；使用 DeepSeek 时设为 `deepseek-chat` |

复制 `.env.example` 为 `.env` 并填写密钥。**`.env` 已在 `.gitignore` 中，勿提交。**
