# eZmanbo 系统架构图生成指令

> 本文档提供 6 张核心架构图的 Mermaid 代码（可直接粘贴到 https://mermaid.live 渲染）及配套的 AI 图像生成提示词（适用于 Midjourney / DALL-E 等工具生成信息图风格示意图）。每张图均附有用于手绘/draw.io 制图的文字说明。

---

## 图1：系统总体四层架构

### Mermaid 代码

```mermaid
flowchart TD
    UI["🖥️ Web 前端\n(Next.js + Zustand)\n多轮对话界面 / 参数表单 / 进度推送"]

    subgraph L1["第一层：需求解析层"]
        P1["自然语言输入"]
        P2["LLM 语义理解\n(意图分类 / 实体提取)"]
        P3["正则规则校验\n(数值提取 / 单位换算 / 等级映射)"]
        P4["RequirementConstraints\n结构化约束对象"]
        P1 --> P2 --> P3 --> P4
    end

    subgraph L2["第二层：候选召回与映射层"]
        S1["MPN 前缀关键词生成\n(按类别+拓扑+厂商偏好)"]
        S2["eZ-PLM API 并发查询\n(asyncio.Semaphore / 令牌桶限速)"]
        S3["PartIR 字段规范化映射\n(异构字段 → 统一内部格式)"]
        S4["约束条件预过滤\n(电压容差±8% / 电流匹配 / 生命周期标记)"]
        S1 --> S2 --> S3 --> S4
    end

    subgraph L3["第三层：评分与安全决策层"]
        E1["器件详情富化\n(补充搜索阶段缺失字段)"]
        E2["D1–D7 七维适配度评分\n(几何加权聚合 → F)"]
        E3["R1–R9 九维风险评分\n(加权求和 → R)"]
        E4["可信度 C × 稳健性 B"]
        E5["RS = 100 × F^α × (1-R/100)^β × C^γ × B^δ"]
        E6["安全约束逐项核查\nG1电气 G2温度 G3认证 G4生命周期 G5完整性 G6边界"]
        E7{{"通过？"}}
        PASS["PASS / CONDITIONAL\n进入推荐列表"]
        FAIL["NOT_RECOMMENDED\n排除 + 标注原因"]
        E1 --> E2 & E3 & E4 --> E5 --> E6 --> E7
        E7 -- 是 --> PASS
        E7 -- 否 --> FAIL
    end

    subgraph L4["第四层：输出与 Agent 层"]
        O1["证据链组装\n(E1 平台数据 / E2 技术手册 / E3 规则推断)"]
        O2["选型报告生成\n(推荐列表 / 风险等级 / 参数匹配依据)"]
        O3["ReAct Agent\n(多轮对话 / 4工具调用 / 诚实降级)"]
        O4["结构化导出\n(Excel BOM / 决策包 / SSE 流式推送)"]
        O1 --> O2 --> O4
        O3 --> O4
    end

    UI -->|"自然语言需求"| L1
    L1 -->|"RequirementConstraints"| L2
    L2 -->|"候选 PartIR 列表 (≤150)"| L3
    L3 -->|"已通过核查的 ScoredPart 列表"| L4
    L4 -->|"SSE 事件流"| UI

    EZPLM[("eZ-PLM 平台 API\nHMAC-SHA256 认证")]
    S2 <-->|"关键词查询 / 器件详情"| EZPLM
    LLM[("LLM API\n(需求解析 / 文本汇总)")]
    P2 <--> LLM
    O3 <--> LLM
```

### 用于 draw.io / 手绘的文字说明

整体为纵向四层矩形区块，从上到下依次为：
- **第一层（蓝色）**：需求解析层，含 LLM 语义模块和正则规则模块两个并联子模块，输出 RequirementConstraints 方框
- **第二层（绿色）**：候选召回层，含关键词生成→并发 API 查询→字段规范化→预过滤四个顺序步骤，右侧标注 eZ-PLM API 圆柱
- **第三层（橙色）**：评分与决策层，评分子模块（D1-D7 / R1-R9 / C / B → RS 公式）后接六条规则的菱形判断框，分叉为 PASS（进入）和 FAIL（排除）两个出口
- **第四层（紫色）**：输出层，含证据链组装、报告生成、ReAct Agent 三个模块，下方连接导出模块
- 左右两侧分别标注 LLM API（虚线连接第一层和Agent）和前端 Web（顶部箭头进入）

---

## 图2：自然语言约束解析模块

```mermaid
flowchart LR
    IN["用户自然语言输入\n例：'12V锂电池转3.3V，STM32，工业级'"]

    subgraph LLM_LAYER["LLM 语义理解层"]
        L1["意图分类\n(选型 / 追问 / 对话)"]
        L2["隐含语义推断\n(STM32 → Vout=3.3V)"]
        L3["器件类别识别\n(降压转换器 / LDO / Boost)"]
        L4["LLM 输出\n(JSON 格式约束字段草稿)"]
        L1 & L2 & L3 --> L4
    end

    subgraph RULE_LAYER["规则提取与校验层"]
        R1["电压正则提取\n(_VIN_REGEX / _VOUT_REGEX)"]
        R2["电流正则提取\n(A / mA 单位换算)"]
        R3["拓扑关键词匹配\n(buck/降压/boost/升压/ldo)"]
        R4["等级→温度映射\n(工业级→-40~85°C\n车规级→-40~125°C+认证标记)"]
        R5["封装正则匹配\n(SOT-23/QFN/TO-220等)"]
    end

    subgraph OUTPUT["输出：RequirementConstraints"]
        F1["input_voltage_nominal_v"]
        F2["output_voltage_v"]
        F3["output_current_a"]
        F4["topology"]
        F5["grade / temperature_min/max_c"]
        F6["category / package_preference"]
    end

    FALLBACK["正则兜底路径\n(LLM 失败时独立提取)"]

    IN --> LLM_LAYER
    IN --> RULE_LAYER
    L4 -->|"JSON 草稿"| RULE_LAYER
    R1 & R2 & R3 & R4 & R5 --> OUTPUT
    IN -->|"LLM 不可用时"| FALLBACK --> OUTPUT
```

---

## 图3：候选召回与 PartIR 规范化流程

```mermaid
flowchart TD
    RC["RequirementConstraints\n{ category: buck, Vin: 12V, Vout: 5V, Iout: 2A }"]

    KW["MPN 前缀关键词生成\n_generate_keywords(constraints)\n\n降压(Buck)前缀列表示例：\nTPS54, TPS56, LMR14, LMR16,\nADP230, MCP163, ST1S10..."]

    subgraph PARALLEL["并发批量搜索 (asyncio.Semaphore=4)"]
        B1["批次1: TPS54/TPS56\n→ /api/v1/key/parts"]
        B2["批次2: LMR14/LMR16\n→ /api/v1/key/parts"]
        B3["批次3: ADP230/MCP163\n→ /api/v1/key/parts"]
        B4["批次N: ..."]
    end

    DEDUP["结果汇聚 + MPN 去重\n(≤150个候选)"]

    subgraph MAPPING["PartIR 字段规范化"]
        M1["mpn → part_number (直接)"]
        M2["manufacturer.name → manufacturer (直接)"]
        M3["attributes[] → Vin/Vout/Iout (正则解析)"]
        M4["lifecycleStatus → lifecycle_status (直接)"]
        M5["description → automotive_grade (关键词提取)"]
        M6["mpn后缀 → output_voltage_v (型号规则推断)"]
    end

    FILTER["约束条件预过滤\nVin 容差 ±8%\nIout ≥ 需求电流\n生命周期 ≠ EOL(仅警告标记)"]

    ENRICH["Top-8 候选详情富化\n/api/v1/part/{id}\n补充: 开关频率/静态电流/封装/效率"]

    OUT["候选 PartIR 列表\n(待评分)"]

    RC --> KW --> PARALLEL
    B1 & B2 & B3 & B4 --> DEDUP --> MAPPING
    M1 & M2 & M3 & M4 & M5 & M6 --> FILTER --> ENRICH --> OUT

    RATE["令牌桶速率控制\nrate=4/s, burst=4\n(平滑限速)"]
    CACHE["双层 LRU 缓存\n关键词缓存500条/24h\n详情缓存200条/24h"]
    PARALLEL <-->|"API 请求"| RATE
    RATE <-->|"命中时直接返回"| CACHE
```

---

## 图4：评分计算与安全约束核查

```mermaid
flowchart LR
    subgraph SCORING["多维评分计算"]
        D1["D1: 功能与参数适配\n电压裕量/电流裕量/拓扑一致"]
        D2["D2: 可靠性与环境\n温度裕量/降额系数"]
        D3["D3: 质量与资格\n制造商可信度/认证等级"]
        D4["D4: 供应与生命周期\n库存状态/生命周期阶段"]
        D5["D5: 制造与集成\n封装类型/引脚兼容"]
        D6["D6: 合规与可持续\nRoHS合规/危险物质"]
        D7["D7: 商业与成本\n单价/可采购性"]
        F["适配度 F\n= 几何加权聚合(D1..D7)\n场景化权重(工业/车规/消费)"]
        R["风险分 R\n= R1–R9加权求和\n+ 尾部修正"]
        C["可信度 C\n= 来源可靠度×时效×完整性"]
        B["稳健性 B\n= 权重扰动下排序稳定性"]
        RS["推荐分 RS\n= 100×F^α×(1-R/100)^β×C^γ×B^δ\nα=0.55 β=0.25 γ=0.10 δ=0.10"]
        D1 & D2 & D3 & D4 & D5 & D6 & D7 --> F
        F & R & C & B --> RS
    end

    subgraph GATE_CHECK["安全约束逐项核查 (按顺序执行)"]
        G1{"G1: 电气边界\nVin/Vout/Iout\n是否在规格范围内?"}
        G2{"G2: 温度覆盖\n器件温度范围\n是否覆盖需求温区?"}
        G3{"G3: 等级认证\n车规需求是否\n具备AEC-Q证据?"}
        G4{"G4: 生命周期\n是否EOL/Obsolete?"}
        G5{"G5: 数据完整性\nMPN和厂商\n字段是否存在?"}
        G6{"G6: 适用边界\n是否极端参数\n或超出拓扑能力?"}
        COND["CONDITIONAL\n附带风险提示标识\n建议工程师复核"]
        PASS["PASS\n进入最终推荐列表"]
        NOTRECOM["NOT_RECOMMENDED\n排除 / 证据分=0\n标注违规规则"]
        G1 -->|"通过"| G2 -->|"通过"| G3 -->|"通过"| G4 -->|"通过"| G5 -->|"通过"| G6
        G6 -->|"通过"| PASS
        G6 -->|"边界触发"| COND
        G1 & G2 & G3 & G4 & G5 -->|"不满足"| NOTRECOM
    end

    RS -->|"评分完成"| G1
```

---

## 图5：多轮对话约束累积状态机

```mermaid
stateDiagram-v2
    [*] --> EMPTY: 新会话开始

    EMPTY: 约束状态为空\nconstraint_store[sid] = {}
    PARTIAL: 部分约束已累积\n{ Vin=12V, Vout=3.3V }
    COMPLETE: 所有必填约束已收集\n{ Vin, Vout, Iout 均非 null }
    SELECTION: 触发选型流程
    DONE: 选型完成\n状态清空(可开始新轮次)

    EMPTY --> PARTIAL: 用户提供部分参数\nextract_constraints() 提取\nmerge_constraints() 合并\n写回 DB 持久化

    PARTIAL --> PARTIAL: 继续提供参数\n(含指代消解: LLM处理\n"就是刚才说的3.3V")

    PARTIAL --> PARTIAL: 缺失必填字段\n→ 生成针对性追问\n(仅询问缺失字段)

    PARTIAL --> COMPLETE: 所有 P0 字段\n(Vin/Vout/Iout) 均已提供

    COMPLETE --> SELECTION: check_completeness() 返回True\n自动触发 _stream_unified 选型路径

    SELECTION --> DONE: 选型报告生成完成\n约束状态清空

    DONE --> EMPTY: 用户开始新选型需求

    note right of PARTIAL
        每轮更新后同步写入 DB:
        ChatSession.accumulated_constraints
        服务重启后可从 DB 恢复
    end note
```

---

## 图6：证据链生成与来源标注

```mermaid
flowchart TD
    SP["已通过核查的 ScoredPart 列表"]

    subgraph BUILD["证据条目构建 (per PartIR)"]
        E1A["电压证据\n来源: ezplm_api\n置信度: 0.95\n声明: '输入电压范围Xmin–Xmax V'"]
        E1B["电流证据\n来源: ezplm_api\n置信度: 0.90\n声明: '最大输出电流 XA'"]
        E1C["温度证据\n来源: ezplm_api\n置信度: 0.95\n声明: '工作温度 Tmin–Tmax°C'"]
        E1D["生命周期证据\n来源: ezplm_api\n置信度: 0.95\n声明: '生命周期状态: Active'"]
        E2A["车规认证证据\n来源: automotive_cert\n置信度: 0.85 (有依据) / 0.50 (推断)"]
        E3A["输出电压证据(推断)\n来源: inferred\n置信度: 0.65\n声明: '通过型号命名规则推断'"]
    end

    CLASSIFY["来源分类标注\nE1: 平台结构化数据 (confidence≥0.90)\nE2: 技术手册/认证文档 (0.75–0.85)\nE3: 规则推断 / 型号规则 (0.50–0.65)"]

    REVIEW["need_human_review 标记\n触发条件:\n- 零库存\n- EOL 状态\n- 主要参数为 E3 来源\n- 证据可信度 C < 0.6"]

    REPORT["选型报告\n每个推荐参数附带:\n- 数据来源类别 (E1/E2/E3)\n- 原始字段名\n- 置信度数值\n- 人工复核标记(如需)"]

    SP --> BUILD
    E1A & E1B & E1C & E1D & E2A & E3A --> CLASSIFY --> REVIEW --> REPORT

    CONSTRAINT["⚠️ LLM 角色限制\nLLM 不生成器件参数数值\n仅对已有结构化证据进行\n自然语言汇总与风险说明"]
    REPORT --> CONSTRAINT
```

---

## AI 图像生成提示词（视觉信息图风格）

以下提示词适用于 Midjourney、DALL-E 3 或 Stable Diffusion，生成适合演示文稿的视觉化架构示意图（非精确技术图，用于 PPT 配图）：

### 图1 总体架构（PPT 封面配图风格）
```
Technical architecture diagram of an AI-powered electronic component selection system, 
four-layer vertical pipeline design, clean white background with blue and teal color scheme, 
flat design style, professional engineering infographic. 
Layer 1: natural language parsing with LLM and rule extraction modules. 
Layer 2: parallel API query to component database with token bucket rate control. 
Layer 3: multi-dimensional scoring (D1-D7) feeding into sequential safety constraint checks. 
Layer 4: evidence chain assembly and report generation with ReAct agent. 
Data flows shown as clean arrows between layers. 
External services (LLM API, eZ-PLM database) shown as cylinders on the side. 
Font: Inter/Helvetica. Style: technical paper figure, IEEE format, high resolution.
```

### 图4 评分与安全核查流（PPT 流程图风格）
```
Clean technical flowchart showing a multi-dimensional scoring pipeline for electronic 
component selection, white background, professional blue and orange color scheme. 
Left side: seven scoring dimensions (D1 through D7) with individual score bars converging 
into a weighted geometric aggregation formula box. Center: multiplicative recommendation 
score formula with Greek letter exponents. Right side: sequential decision tree with six 
diamond-shaped check nodes (G1 electrical, G2 temperature, G3 certification, G4 lifecycle, 
G5 data completeness, G6 boundary), green PASS exit at bottom and red NOT_RECOMMENDED 
exits on the sides. Flat design, rounded rectangles, no shadows. IEEE paper figure style.
```

### 图5 多轮约束累积（状态机可视化）
```
State machine diagram for multi-turn conversation constraint accumulation, minimal design, 
light gray background with white state boxes. Four states: EMPTY (gray), PARTIAL (blue, 
showing accumulated constraints like Vin=12V Vout=3.3V as small tags), COMPLETE (green), 
SELECTION_TRIGGERED (orange). Transitions shown as labeled arrows: "extract + merge" from 
EMPTY to PARTIAL, "clarification question" self-loop on PARTIAL, "all P0 fields filled" 
from PARTIAL to COMPLETE, "auto-trigger pipeline" from COMPLETE to SELECTION. 
Bottom annotation: database icon with "DB persistence on every update". 
Clean sans-serif font, professional technical diagram.
```
