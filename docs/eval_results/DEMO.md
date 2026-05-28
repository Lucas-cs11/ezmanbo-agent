# eZ-PLM Component Risk Agent — 演示说明文档

> **分支**：`feature/frontend/eval-report`  
> **生成日期**：2026-05-28  
> **版本**：IR v0.1 (纯规则模式)

---

## 目录

1. [项目概述](#项目概述)
2. [环境准备](#环境准备)
3. [启动服务](#启动服务)
4. [Streamlit 前端操作指南](#streamlit-前端操作指南)
5. [评测执行](#评测执行)
6. [评测报告解读](#评测报告解读)
7. [UI 美化详解](#ui-美化详解)

---

## 项目概述

**eZ-PLM Component Risk Agent** 是一个智能 DC-DC 转换器选型与风险评估工具，支持：

- 🧠 自然语言需求解析（电压/电流/温度/拓扑/偏好）
- 📊 五维评分模型（参数匹配、供应风险、成本、国产化、证据可信度）
- 🔗 规则化证据链（8 类语义证据 + 置信度评分）
- ⚠️ 9 条风险评估规则（供应链 + 工程技术）
- 🌐 Streamlit Web 交互界面

---

## 环境准备

```bash
# 1. 克隆项目
git clone https://github.com/Lucas-cs11/ezplm-component-risk-agent.git
cd ezplm-component-risk-agent

# 2. 切换到评测分支
git checkout feature/frontend/eval-report

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量（可选，纯规则模式无需 API Key）
cp .env.example .env
# 编辑 .env，填入 OPENAI_API_KEY / EZPLM_API_KEY（LLM 增强模式需要）
```

**依赖清单** (`requirements.txt`)：
```
fastapi
uvicorn[standard]
streamlit
pydantic
requests
pandas
```

---

## 启动服务

### 启动后端 API（终端 1）

```bash
cd ezplm-component-risk-agent
python -m uvicorn app.main:app --port 8001 --host 0.0.0.0
```

预期输出：
```
INFO:     Started server process [xxxxx]
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
```

### 启动 Streamlit 前端（终端 2）

```bash
cd ezplm-component-risk-agent
python -m streamlit run frontend/streamlit_app.py --server.port 8501
```

预期输出：
```
  You can now view your Streamlit app in your browser.
  Local URL: http://localhost:8501
```

浏览器访问 `http://localhost:8501` 即可看到主界面。

---

## Streamlit 前端操作指南

### 1. 主界面布局

```
┌──────────────────────────────────────────────────────────┐
│ 🔬 eZ-PLM Component Risk Agent                           │
│ Intelligent DC-DC converter selection...                 │
├────────────────────────────────┬─────────────────────────┤
│ 📝 Requirement Description     │ 🎯 Tips                 │
│ [文本输入框]                    │ • 指定电压/电流/温度    │
│                                │ • 标注车规/工业等级     │
│                                │ • 偏好国产或低供应风险  │
│                                │                         │
│                                │ [🚀 Analyze]            │
│                                │ [🔄 Clear]              │
├────────────────────────────────┴─────────────────────────┤
│ ⚙️ Sidebar: Settings + 6 个预设模板 (Quick Load)         │
└──────────────────────────────────────────────────────────┘
```

### 2. 预设示例

在侧边栏 **📋 Preset Examples** 下拉菜单中选择：

| 预设 | 输入 |
|------|------|
| 车规级 12V→5V 3A 国产 | 我需要一个 12V 转 5V、3A 的车规级降压芯片，工作温度 -40°C 到 125°C，优先考虑国产替代。 |
| 工业 24V→12V 2A | 需要 24V 转 12V、2A 的降压方案，工作温度 -40°C 到 85°C。 |
| 大功率 24V→5V 10A | 输入 24V，输出 5V，电流 10A，高功率场景。 |
| 低压 5V→3.3V 1A | 请给我一个 5V 到 3.3V 的降压芯片，输出 1A。 |
| 车规 36V→5V 8A 国产 | 36V 输入，输出 5V、8A，车规级，工作温度 -40°C 到 125°C，必须国产，低供应风险。 |
| 性价比 12V→5V 1.2A | 12V 转 5V、1.2A 降压，室温使用，要求成本最低。 |

### 3. 分析结果展示

点击 **🚀 Analyze** 后，页面依次展示：

#### a. 📋 Parsed Requirement Constraints（可折叠）
- 三列布局：分类/拓扑/等级 | 电压/电流 | 温度/偏好

#### b. 📊 Score Summary Dashboard
- 4 个指标卡片：总数 / ⭐推荐 / 🟡备份 / 🔴不推荐

#### c. 🏆 Ranking & Score Breakdown
- 每个候选器件一张评分卡片：
  - 渐变色背景 + 左侧色带（绿/黄/红 = 推荐/备份/不推荐）
  - 型号 + 厂商 + 徽章（国产/进口/车规/生命周期）
  - 总分进度条（动态颜色 ≥75 绿 / ≥50 黄 / 红）
  - 五维子评分：📐参数匹配 / 📦供应风险 / 💰成本 / 🇨🇳国产 / 📄证据
  - 关键规格行
  - 评分原因标签

#### d. 🔗 Evidence Chain
- 按器件 Tab 分组展示
- 每项证据：紫色类型标签 + 声明 + 来源路径 + 置信度色标
- 无数据手册自动标记 ⚠️ need_human_review

#### e. ⚠️ Risk Assessment
- Overall Risk 级别 + 各风险项描述与缓解措施

---

## 评测执行

### 运行 20 条用例完整评测

```bash
cd ezplm-component-risk-agent
python -m tests.eval_runner
```

### 输出文件

| 文件 | 路径 | 说明 |
|------|------|------|
| Markdown 报告 | `docs/eval_results/eval_report.md` | 结构化评测报告，含逐用例详情 |
| JSON 摘要 | `docs/eval_results/eval_summary.json` | 机器可读的评测结果 |

### 评测逻辑

每条用例检查以下维度：

```python
checks = {
    "category":           # 分类（dc_dc_converter / ldo）
    "topology":           # 拓扑（buck / boost）
    "output_voltage_v":   # 输出电压
    "output_current_a":   # 输出电流
    "temperature_min_c":  # 最低温度
    "temperature_max_c":  # 最高温度
    "grade":              # 等级（automotive / industrial / consumer）
    "preferences":        # 偏好（domestic_alternative / low_supply_risk）
}
```

---

## 评测报告解读

### 报告结构

```
# eZ-PLM Component Risk Agent — 评测报告
│
├── 生成时间 / 用例总数 / 通过率 / 评测模式
│
├── 📊 总览
│   └── 20 行汇总表：用例 ID | 输入摘要 | 通过 | 推荐数 | 风险等级 | 耗时
│
├── 📋 逐用例详情（×20）
│   ├── 输入 + 耗时
│   ├── 解析约束表
│   ├── 候选评分明细表（# 型号 厂商 国产 车规 总分 参数 供应 成本 国产 证据 推荐等级）
│   ├── TOP1 评分原因列表
│   ├── 证据链表（器件 证据类型 声明 置信度 需人工）
│   └── 风险评估
│
└── Footer
```

### 当前评测结果（2026-05-28）

| 指标 | 数值 |
|------|------|
| 用例总数 | 20 |
| 通过 | 18 ✅ |
| 失败 | 2 ❌ |
| 通过率 | **90.0%** |
| 平均耗时 | < 3ms/条 |
| 评测模式 | 纯规则模式，无 LLM 依赖 |

### 失败用例分析

| 用例 | 失败原因 | 根因 |
|------|----------|------|
| dc_dc_013 | `preference 'low_supply_risk' missing` | 输入"希望库存充足"未触发 `low_supply_risk` 关键词 |
| dc_dc_017 | `preference 'low_supply_risk' missing` | 输入"库存优先"未触发 `low_supply_risk` 关键词 |

**改进方向**：在 `requirement_parser.py` 中扩展 `low_supply_risk` 触发词，增加"库存充足"、"库存优先"、"库存充裕"等中文变体。

### 用例覆盖矩阵

| 维度 | 覆盖用例 |
|------|----------|
| 车规级 (automotive) | 001, 008, 011, 016, 020 |
| 工业温度 | 002, 004, 006, 012, 017 |
| 消费电子/室温 | 003, 005, 007, 009, 015, 019 |
| 国产偏好 | 001, 006, 011, 012, 014, 016, 018, 020 |
| 低供应风险偏好 | 004, 009, 011, 013, 017, 020 |
| 高功率 (>5A) | 010, 011, 013, 020 |
| 封装偏好 | 018 |
| 成本优先 | 015 |
| 低压 (<2V 输出) | 014, 019 |

---

## UI 美化详解

### 评分卡片设计

```
┌─────────────────────────────────────────────────────┐
│ ┃  #1  ┃  LMR14030SDDAR  by TI         ⭐ Recommended │
│ ┃      ┃  🌍 进口  🚗 车规  active                   │
│ ┃      ┃                                              │
│ ┃      ┃  95 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ / 100    │
│ ┃      ┃                                              │
│ ┃      ┃  📐参数 95  📦供应 92  💰成本 85  🇨🇳国产 100  📄证据 90 │
│ ┃      ┃                                              │
│ ┃      ┃  📐 4–36V in | ⚡ 3A out | 🌡 -40–125°C | 📦 50000 | 💰 ¥3.20 │
│ ┃      ┃  [输入电压覆盖 ✓] [输出电流满足 ✓] [温度范围覆盖 ✓] │
└─────────────────────────────────────────────────────┘
```

### CSS 自定义类

| CSS 类 | 用途 |
|--------|------|
| `.score-card` | 默认评分卡片（紫色色带） |
| `.score-card.recommended` | 推荐卡片（绿色色带 + 绿色渐变背景） |
| `.score-card.backup` | 备份卡片（黄色色带） |
| `.score-card.not-recommended` | 不推荐卡片（红色色带） |
| `.badge-domestic` | 🇨🇳 国产徽章（绿色） |
| `.badge-import` | 🌍 进口徽章（红色） |
| `.badge-auto` | 🚗 车规徽章（蓝色） |
| `.badge-active` / `.badge-obsolete` / `.badge-discontinued` | 生命周期徽章 |
| `.evidence-type` | 紫色证据类型标签 |
| `.risk-high` / `.risk-medium` / `.risk-low` | 风险级别颜色 |
| `.score-bar-fill` | 动态总分进度条（CSS transition 动画） |

### 证据链展示

```
┌─ 🔗 Evidence Chain ──────────────────────────────────┐
│ [SYWT-5083B] [SYWT-65W-12V] [SYWT-60W-12V]            │  ← Tab 切换
├───────────────────────────────────────────────────────┤
│ ┃ ezplm_api  输入电压覆盖 ✓ (4.5-36V)                  │
│ ┃ source: ezplm::input_voltage_min_v  conf: 95%        │
│ ┃                                                      │
│ ┃ ezplm_api  输出电流充足 ✓ (3A)                        │
│ ┃ source: ezplm::output_current_max_a  conf: 95%       │
│ ┃                                                      │
│ ┃ datasheet  数据手册可查                               │
│ ┃ source: ezplm::datasheet_url  conf: 85%              │
│ ┃                                                      │
│ ┃ missing_datasheet ⚠️ 无数据手册，建议人工复核          │
│ ┃ source: ezplm::datasheet_url  conf: 60%  ⚠️          │
└───────────────────────────────────────────────────────┘
```

---

## 项目文件结构

```
ezplm-component-risk-agent/
├── app/
│   ├── agent_orchestrator.py   # 分析管线编排
│   ├── evidence.py             # 8 类规则化证据链
│   ├── ezplm_client.py         # eZ-PLM API / Mock 数据
│   ├── llm_client.py           # LLM 客户端
│   ├── main.py                 # FastAPI 入口
│   ├── report_generator.py     # 9 条规则风险评估
│   ├── requirement_parser.py   # NLP 需求解析
│   ├── schemas.py              # Pydantic 数据模型
│   └── scoring.py              # 五维评分 + 动态权重
├── tests/
│   ├── cases/
│   │   └── dc_dc_cases.jsonl   # 20 条测试用例
│   └── eval_runner.py          # 评测执行 + 报告生成
├── frontend/
│   └── streamlit_app.py        # Streamlit Web UI
├── docs/
│   ├── daily/2026-05-27.md     # 工作日历
│   └── eval_results/
│       ├── DEMO.md             # 本演示说明文档
│       ├── eval_report.md      # 评测报告 (Markdown)
│       └── eval_summary.json   # 评测摘要 (JSON)
├── data/mock_parts.json        # Mock 器件库
├── requirements.txt
└── .env.example
```

---

*文档由 `feature/frontend/eval-report` 分支维护*