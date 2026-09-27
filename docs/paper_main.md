# eZmanbo：面向 eZ-PLM 平台的电子元器件智能选型系统

---

## 摘要

电子元器件选型是硬件系统设计中的关键环节，涉及电气参数匹配、可靠性认证、产品生命周期与供应链稳定性等多维工程约束。将大语言模型（Large Language Model, LLM）直接应用于器件推荐，存在输出型号无法在真实数据库中验证的固有局限，且通用 LLM 缺乏对温度覆盖、停产状态等工程安全条件的系统性检查机制。本文提出 eZmanbo，一个基于 eZ-PLM 平台结构化数据的电子元器件智能选型系统。系统采用四层流水线架构，将 LLM 严格限定于自然语言理解与文本生成角色，以 eZ-PLM 平台 API 返回的结构化数据作为候选器件的唯一来源，通过统一内部数据模型（PartIR）完成异构 API 字段的规范化映射。系统对每个候选器件逐一核查电气边界、工作温度范围、认证等级和产品生命周期等安全条件，仅允许全部满足约束的器件进入推荐列表，并为每条推荐参数标注其数据来源（平台结构化数据、技术手册或规则推断），实现推荐过程的可追溯与可审计。此外，本文提出并实现了多轮对话中结构化约束的服务端持久化累积机制，解决了渐进式参数输入场景下约束信息跨轮丢失的问题。

**关键词：** 电子元器件选型；大语言模型；工具调用；多轮对话约束累积；供应链风险

---

## Abstract

Electronic component selection is a critical stage in hardware system design, involving multi-dimensional engineering constraints such as electrical parameter matching, reliability certification, product lifecycle status, and supply chain stability. Directly applying large language models (LLMs) to component recommendation suffers from the inherent limitation that generated part numbers are often unverifiable in real component databases, and general-purpose LLMs lack systematic checks for engineering safety conditions such as temperature coverage and obsolescence. This paper presents eZmanbo, an intelligent component selection system grounded in the structured data of the eZ-PLM platform. The system adopts a four-layer pipeline architecture that strictly confines LLMs to natural language understanding and text generation roles, using eZ-PLM API responses as the sole source of candidate parts. All API data is normalized through a unified internal data model (PartIR). Before finalizing recommendations, the system sequentially verifies each candidate against electrical boundaries, temperature range, grade certification, and lifecycle status, permitting only fully compliant parts into the output list. Every recommended parameter is annotated with its data source (platform structured data, datasheet, or rule inference) to ensure traceability and auditability. Furthermore, we design and implement a server-side persistent constraint accumulation mechanism for multi-turn dialogues, which resolves the problem of constraint information loss across conversation turns in incremental parameter input scenarios.

**Keywords:** Electronic component selection; Large language model; Tool-augmented reasoning; Multi-turn constraint accumulation; Supply chain risk

---

## 1. 引言

### 1.1 问题背景

电子元器件选型是硬件设计流程中对下游质量影响最显著的决策环节之一。以电源转换芯片为例，工程师在选型时需要同时满足输入/输出电压范围、最大输出电流、工作温度范围、拓扑类型、封装兼容性、车规或工业级认证要求、产品生命周期状态，以及供应商库存与交期等约束。一个典型的电源模块选型往往需要查阅多份技术手册、在分销商平台比对参数，耗费工程师数小时至数天时间。

在量产阶段，选型错误的代价尤其高昂：若所选器件的工作温度范围不覆盖实际使用环境，或器件在进入量产前已转为停产（EOL）状态，则可能导致停线、重新认证或成本剧增。

### 1.2 现有方法的局限

**参数筛选平台**（如各厂商官网选型工具、分销商参数搜索引擎）能够对结构化参数进行精确过滤，但要求用户将需求手动转化为参数查询，无法理解自然语言表达的隐含偏好，对非专业用户存在较高使用门槛。

**直接使用 LLM 推荐**近年来受到关注。通用大语言模型具备出色的自然语言理解能力，能从描述性文本中归纳选型意图。然而，其训练数据中器件信息的时效性和准确性无法保证，生成的型号（MPN）大量不存在于实际可采购数据库中 [1, 2]；此外，LLM 对工程安全条件（如认证等级、停产风险）缺乏系统性检查。

**LLM 结合检索增强生成（RAG）**的方案 [3] 通过引入技术手册文档检索来提高回答的事实性。但检索到的文档片段仍可能被模型错误解读，且 RAG 本身不提供候选级别的安全约束核查——即使检索到了正确的数据手册，系统仍可能因解读偏差而忽略车规要求或温度边界等关键约束。

上述局限说明：电子元器件智能选型的核心挑战不仅在于"能否给出推荐"，而在于推荐结果是否可验证、是否满足工程安全条件，以及推荐依据是否可审计。

### 1.3 本文贡献

本文提出的 eZmanbo 系统针对上述挑战，做出以下技术贡献：

1. **基于平台数据的候选生成策略**：系统从结构化约束中自动生成多厂商 MPN 前缀关键词，通过 eZ-PLM API 逐一检索，确保所有候选器件来自可查询的真实数据库，从根本上避免 LLM 幻觉型号进入推荐流程。

2. **多维评分与保守筛选机制**：采用七维适配度（D1–D7）的几何加权聚合评分，综合反映参数匹配、可靠性、供应链、成本等多个工程维度；评分策略遵循保守原则——当关键数据字段缺失时，以惩罚而非默认优值处理，避免因信息不完整而给出虚假的高分推荐。随后对候选器件逐一执行六条安全约束核查（电气边界、温度覆盖、认证等级、生命周期状态、数据完整性、适用边界），不满足任一条件的器件被标记为不推荐。

3. **证据链来源标注**：为每条推荐参数标注其数据来源类别（平台 API 结构化数据、关联技术手册、规则推断），使推荐结果可供工程师复核与第三方审计。

4. **服务端多轮约束累积**：设计并实现了服务端结构化约束状态机，在多轮对话中持久化地累积用户分批提供的约束参数，并将状态持久化到数据库，解决了服务重启后约束信息丢失的问题。

---

## 2. 相关工作

### 2.1 工具增强的语言模型

ReAct [4] 将推理（Reasoning）与行动（Acting）交织在同一生成轨迹中，使语言模型能够在每步推理后调用外部工具、观察结果并据此继续推理。这一框架已被广泛应用于问答、信息检索和任务规划等场景。LangChain [5] 在工程层面对 ReAct 模式进行了标准化封装，提供工具定义、历史对话管理和链式调用等基础设施。eZmanbo 的交互式选型模块以 ReAct 框架为基础，定义了器件检索、工程知识查询、替代料查找和报告生成四类工具，使系统在工具返回空结果时能够诚实降级（honest degradation）而非凭空生成推荐。

### 2.2 检索增强生成

Lewis 等人 [3] 提出的 RAG 框架通过在生成时检索相关文档，显著提升了语言模型在知识密集型任务上的事实性。然而，RAG 的检索对象通常是文档片段，模型在解读和整合多个片段时仍可能引入错误。eZmanbo 的设计差异在于：系统不依赖 RAG 生成器件事实，而是直接以 eZ-PLM API 的结构化字段作为候选参数的来源；RAG 仅用于补充工程设计知识（如电路拓扑公式、PCB 布局建议），不参与候选器件的事实性决策。

### 2.3 大语言模型在电子设计中的应用

近年来，研究者开始探索将 LLM 应用于电子设计自动化（EDA）领域，包括硬件描述语言（HDL）代码生成 [6]、电路设计优化和元器件知识问答等任务。在器件选型场景中，已有研究尝试基于 LLM 进行参数提取和型号推荐 [1]，但可验证性和工程安全约束方面的挑战尚未得到系统性解决。eZmanbo 聚焦于这一工程落地问题，通过严格的数据接地策略确保推荐型号的可验证性。

### 2.4 信息检索中的混合检索

BM25 [7] 是基于词频的概率检索模型，在精确关键词匹配场景下表现优秀。Sentence-BERT [8] 通过孪生网络对 BERT 进行微调，生成语义相近的句子向量，适用于语义相似性检索。Cormack 等人 [9] 提出的倒数排名融合（Reciprocal Rank Fusion, RRF）方法通过融合多个检索系统的排名列表来提升综合检索质量。eZmanbo 的工程知识库检索模块采用 BM25 与向量检索相结合、RRF 融合的混合检索策略，兼顾精确型号匹配（如 "LMR14030SDDAR"）与语义知识检索（如 "Buck 电感计算方法"）两种场景的需求。

---

## 3. 系统总体设计

### 3.1 设计原则

eZmanbo 的设计遵循以下三项原则：

**数据接地**：所有进入推荐流程的候选器件均来自 eZ-PLM 平台 API 的真实查询结果。LLM 不被允许在最终输出中直接生成器件型号，其作用限定于解析自然语言需求和生成文本摘要。

**约束优先于推荐数量**：在多维评分完成后、推荐输出前，系统对每个候选器件执行工程安全条件核查。这一步骤的设计原则是"宁少推荐，不放行违规"：被核查排除的器件标记为不推荐，不进入最终列表。

**保守推断**：当候选器件的某一关键参数字段在平台数据中缺失时，系统不假设该参数优良，而是在评分中施加惩罚，并在推荐依据中明确标注为"待验证"。这一策略避免了因数据不完整而产生的误导性高分推荐。

### 3.2 系统架构

系统采用四层流水线架构，各层之间通过 Pydantic 数据模型进行数据交换，实现层间解耦。

**第一层：需求解析层**。接收用户的自然语言需求描述，输出结构化的 RequirementConstraints 对象，包含器件类别（category）、拓扑类型（topology）、输入/输出电压（Vin/Vout）、输出电流（Iout）、温度范围、应用等级（grade）和封装偏好等字段。

**第二层：候选召回与映射层**。从 RequirementConstraints 中自动生成多厂商 MPN 前缀关键词列表，通过 eZ-PLM API 进行并发查询，并将 API 返回的原始 JSON 字段映射到统一的 PartIR 内部数据格式。

**第三层：评分与安全决策层**。对排名靠前的候选通过器件详情接口补充缺失字段，随后计算七维综合评分，并对每个候选逐一执行六条安全约束核查，输出 PASS / CONDITIONAL / NOT_RECOMMENDED 三种状态。

**第四层：输出与 Agent 层**。将通过核查的候选器件组装证据链（标注参数来源和置信度），生成包含推荐列表、风险等级和参数匹配依据的选型报告；ReAct Agent 模块提供多轮交互式选型能力，支持工具调用与诚实降级响应。

---

## 4. 核心模块实现

### 4.1 自然语言约束解析

约束解析模块将用户的自然语言需求转换为结构化的 RequirementConstraints 对象。模块采用 LLM 语义理解与正则规则提取两层架构：LLM 负责识别需求的整体语义、判断器件类别和隐含偏好；规则层从 LLM 输出中提取标准化数值字段，执行单位换算（如将 mA 转换为 A），并完成等级关键词到温度区间的映射（如"工业级"对应 -40～85 °C，"车规级"对应 -40～125 °C，并同时触发认证等级需求标记）。

两层协作的设计动机在于：纯 LLM 输出存在格式不稳定、数值单位混淆等问题；纯正则规则无法处理描述性、隐含性的需求表达（如"给 STM32 供电"隐含 3.3 V 输出电压）。规则层对 LLM 输出进行后处理校验，同时提供独立的正则兜底路径，确保在 LLM 调用失败时系统仍能提取部分参数。

解析结果进入约束完整性检查：必填字段（Vin、Vout、Iout）缺失时系统生成追问，选填字段（温度范围、应用等级）缺失时在选型完成后的建议中提示，不阻塞主流程。

### 4.2 候选器件召回与数据规范化

**多前缀关键词生成**：系统根据器件类别（category）和拓扑类型（topology）从预维护的关键词表中生成多厂商 MPN 前缀列表。例如，降压（Buck）转换器类型会生成涵盖 Texas Instruments（TPS5x、LMR1x、LMR2x）、Analog Devices（ADP23xx）、Microchip（MCP16xx）等主流厂商的前缀；当用户指定厂商偏好时，系统自动将关键词列表收窄至对应厂商前缀。

**并发检索**：模块通过 `asyncio.Semaphore` 控制并发度（默认并发 4 个关键词批次），对每个关键词批次向 eZ-PLM API 发起请求，结果汇聚后去重，单次选型最多累积 150 个候选。API 访问采用令牌桶算法（token bucket）进行速率控制，相对于简单的固定间隔 sleep，令牌桶允许在低负载时累积令牌进行批量突发，同时在高负载时平滑限速，更好地适配 API 的真实速率限制特征。

**PartIR 数据规范化**：eZ-PLM API 在不同端点（关键词搜索 / 器件详情 / 参考设计）返回的字段结构存在差异。PartIR 作为内部统一数据格式，定义了标准字段集（part_number、manufacturer、input_voltage_min/max_v、output_current_max_a、temperature_min/max_c、lifecycle_status、automotive_grade 等），并通过映射规则将原始字段转换为内部字段。对于无法直接映射的字段（如输出电压需从型号命名规则后缀推断），映射规则标注推断置信度，供后续证据链生成使用。经规范化的 PartIR 对象供评分和安全检查模块直接使用，屏蔽了下游模块对外部 API 数据格式的直接依赖。

### 4.3 多维评分与候选筛选

**评分框架**：系统从四个维度计算候选器件的综合推荐分 RS：

$$RS = F^{\alpha} \times (1 - R/100)^{\beta} \times C^{\gamma} \times B^{\delta} \times 100$$

其中 F 为七维适配度（取值 0–1，由 D1–D7 几何加权聚合），R 为九维风险分（0–100，越低越好），C 为可信度（0–1），B 为权重扰动下排序稳定性（0–1）。指数 α、β、γ、δ 之和为 1，默认场景下分别取 0.55、0.25、0.10、0.10。

七个适配度维度为：D1 功能与参数适配（电压裕量、电流裕量、拓扑一致性）、D2 可靠性与环境（温度裕量、降额系数）、D3 质量与资格证据（制造商可信度、认证等级）、D4 供应与生命周期（库存状态、生命周期阶段）、D5 制造与集成（封装类型、引脚兼容性）、D6 合规与可持续性（RoHS 合规、危险物质限制）、D7 商业与成本（单价、可采购性）。不同应用场景（工业级、车规级、消费级）使用不同的维度权重配置。

乘法聚合公式的工程含义在于：高分维度无法完全补偿低分维度——若器件在供应链（D4）上存在零库存风险，该维度的低分会通过乘法显著拉低综合推荐分，正确反映"没有现货就无法交付"的工程现实，而加法聚合则可能让其他维度的高分掩盖这一致命缺陷。

**保守评分策略**：当评分所需的某字段在 PartIR 中为 None 时，系统不假设最优值，而是在该字段对应的维度上施加惩罚（取该维度得分的 50%），并在证据链中将该参数来源标注为"待验证"。

**安全约束核查**：评分完成后，系统对每个候选器件按顺序执行以下六条规则（G1–G6），任一规则不满足即停止并标记为 NOT_RECOMMENDED：G1 电气边界（Vin/Vout/Iout 是否在规格范围内）、G2 温度覆盖（器件温度范围是否覆盖需求温度区间）、G3 等级认证（车规需求是否具备 AEC-Q 认证证据）、G4 生命周期（是否处于 EOL 或 Obsolete 状态）、G5 数据完整性（MPN 和厂商字段是否存在）、G6 适用边界（极端参数或超出拓扑能力的需求触发人工复核标记）。仅通过全部规则或触发 CONDITIONAL 状态（部分信息缺失但未违反硬性约束）的器件进入最终推荐列表，CONDITIONAL 状态的器件附带风险提示标识，建议工程师人工复核。

### 4.4 证据链生成

证据链模块为每个推荐器件的关键参数生成可追溯的来源标注。系统将参数数据来源分为三类：**E1** 为平台结构化数据，参数直接来自 eZ-PLM API 返回的属性字段；**E2** 为技术手册，参数来自平台关联的 PDF 技术文档；**E3** 为规则推断，参数由系统根据型号命名规则或器件族特征推断。

每条证据记录包含器件型号、参数声明文本、来源类别、原始字段名和置信度（E1: 0.90–0.95，E2: 0.75–0.85，E3: 0.50–0.65）。当某参数主要依赖 E3 推断时，系统在推荐报告中显式标注"推断值，建议工程师核验"，并将该器件的证据可信度得分（C 维度）相应降低。

此设计的关键约束是：LLM 不被允许作为器件参数的事实提供者——LLM 在证据链中的唯一作用是对已有结构化证据进行自然语言汇总，其生成的所有数值均来源于 PartIR 中已存在的非 LLM 字段。这一约束在代码层面通过将证据组装逻辑与 LLM 文本生成分离为独立模块来强制执行。

### 4.5 多轮对话约束累积

在实际使用场景中，用户往往分多轮逐步提供选型参数（如第一轮说明输入电压，第二轮补充输出电流，第三轮指定应用等级）。若每轮对话独立处理，系统将在每轮重新追问已提供过的参数，造成重复交互。

**约束状态管理**：系统在服务端为每个会话维护一个结构化约束字典（constraint_store），以会话 ID 为键持久化存储已提取的约束字段。每轮对话结束后，新提取的约束通过合并操作更新到状态字典，新值优先覆盖旧值。完整性检查在每轮合并后执行，当所有必填字段均已收集时自动触发选型流程，否则仅生成针对剩余缺失字段的追问。

**持久化策略**：约束状态除存储在进程内存外，同步持久化到数据库的 `ChatSession.accumulated_constraints` 字段。服务重启后，系统在首次接收该会话的请求时从数据库恢复约束状态，确保多轮累积在服务重启场景下不丢失。

**指代消解处理**：用户在多轮对话中可能以指代性表达补充参数（如"就是你刚才提到的 3.3V"）。当正则规则无法直接从文本提取数值时，系统将当前轮用户输入和已累积约束一同传入 LLM，由 LLM 完成语义层面的指代消解，返回更新后的结构化约束字典，随后将结果写回 constraint_store。这一机制使约束合并操作的覆盖范围超越了单纯的显式数值提取。

### 4.6 ReAct Agent 工具编排

ReAct Agent [4] 模块为系统提供交互式多轮选型能力。Agent 定义了四个工具：`search_components`（根据约束在 eZ-PLM 中检索器件）、`query_design_knowledge`（在本地工程知识库中检索设计公式和 PCB 布局建议）、`find_alternative_parts`（根据指定型号查找替代料）和 `generate_full_report`（触发完整选型流水线并生成报告）。

Agent 的推理-行动循环在每步先输出思考过程（Thought），再调用工具（Action），观察返回结果（Observation），然后决定是否继续调用工具或直接生成最终回答。当工具返回空结果时（如平台中无法检索到满足条件的器件），Agent 输出诚实降级响应（如"当前数据不足以提供符合要求的推荐，建议调整约束或联系供应商"），而非基于 LLM 训练知识生成无依据的型号，确保输出与平台实际数据一致。

---

## 5. 工程实现

### 5.1 API 接入与缓存

eZ-PLM API 采用 HMAC-SHA256 签名认证，每次请求携带时间戳和随机 nonce 防止重放攻击。系统在接口层维护双层 LRU 缓存：关键词搜索缓存（容量 500 条，TTL 24 小时）和器件详情缓存（容量 200 条，TTL 24 小时），利用 eZ-PLM 数据库日更新周期特性降低重复请求开销。

API 调用速率通过令牌桶算法控制，稳态速率 4 次/秒，允许短时突发。认证失败时系统停止当前请求并记录告警（不将认证错误误判为无候选），429 速率超限时优先从过期缓存中返回已有数据而不追加新请求。

### 5.2 流式响应与进度推送

后端选型流程通过 Server-Sent Events（SSE）将进度实时推送到前端，事件类型包括 `parse_done`（需求解析完成）、`search_done`（候选搜索完成）、`score_update`（评分进度）、`evidence_done`（证据链构建完成）、`risk_done`（风险评估完成）、`text_delta`（报告文本增量）和 `done`（选型完成）。SSE 相比 WebSocket 具有更简单的反向代理穿透特性，且单向推送满足本场景需求。系统在 SSE 生成器上叠加心跳机制（每 15 秒发送 ping 事件），避免长时选型任务中代理服务器因超时而关闭连接。

### 5.3 系统可靠性

在多工作进程部署场景下，进程内存中的会话约束状态不在进程间共享。系统通过将约束状态持久化到数据库来解决此问题——每个请求从数据库恢复约束状态，处理完成后写回，使不同进程均能访问一致的会话状态，无需引入额外的分布式缓存依赖。

LLM 调用采用指数退避重试策略（429 和 5xx 错误最多重试 3 次，退避间隔 1/2/4 秒），上下文超限时抛出专用异常类型供上层路由到降级响应而非直接报错。

---

## 6. 总结与展望

本文设计并实现了 eZmanbo，一个以 eZ-PLM 平台结构化数据为推荐事实来源的电子元器件智能选型系统。系统的核心设计决策是将 LLM 的角色严格限定在自然语言理解和文本生成，以平台 API 数据作为唯一候选来源，通过数据规范化、多维评分、安全约束核查和证据来源标注，构建可验证、可审计的推荐流程。

系统当前存在以下局限：推荐质量上界由 eZ-PLM 平台的数据覆盖范围决定，对于平台收录不完整的小批量或国产器件，系统可能无法给出充分的候选；极端参数场景（如超高压或超大电流需求）下的约束提取准确率有待提升；安全约束核查规则基于人工定义，尚未结合历史选型案例进行数据驱动的规则优化。

后续工作方向包括：扩展对更多器件类别（运算放大器、接口芯片、MCU）的支持，引入用户反馈机制改进评分权重，以及探索基于历史选型数据的约束规则自动学习。

---

## 参考文献

[1] Ji Z, Lee N, Frieske R, et al. Survey of Hallucination in Natural Language Generation[J]. ACM Computing Surveys, 2023, 55(12): 1-38.

[2] Huang L, Yu W, Ma W, et al. A Survey on Hallucination in Large Language Models: Principles, Taxonomy, Challenges, and Open Questions[J]. arXiv preprint arXiv:2311.05232, 2023.

[3] Lewis P, Perez E, Piktus A, et al. Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks[C]// Advances in Neural Information Processing Systems (NeurIPS). 2020: 9459-9474.

[4] Yao S, Zhao J, Yu D, et al. ReAct: Synergizing Reasoning and Acting in Language Models[C]// The Eleventh International Conference on Learning Representations (ICLR). 2023.

[5] Chase H. LangChain[EB/OL]. (2022). https://github.com/langchain-ai/langchain.

[6] Liu M, Ene F, Kirby R, et al. ChipNeMo: Domain-Adapted LLMs for Chip Design[J]. arXiv preprint arXiv:2311.00176, 2023.

[7] Robertson S, Zaragoza H. The Probabilistic Relevance Framework: BM25 and Beyond[J]. Foundations and Trends in Information Retrieval, 2009, 3(4): 333-389.

[8] Reimers N, Gurevych I. Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks[C]// Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing (EMNLP). 2019: 3982-3992.

[9] Cormack G V, Clarke C L A, Buettcher S. Reciprocal Rank Fusion Outperforms Condorcet and Individual Rank Learning Methods[C]// Proceedings of the 32nd International ACM SIGIR Conference on Research and Development in Information Retrieval. 2009: 758-759.

[10] Wei J, Wang X, Schuurmans D, et al. Chain-of-Thought Prompting Elicits Reasoning in Large Language Models[C]// Advances in Neural Information Processing Systems (NeurIPS). 2022.

[11] OpenAI. GPT-4 Technical Report[J]. arXiv preprint arXiv:2303.08774, 2023.

[12] IEC 62402:2019 Obsolescence Management – Application Guide[S]. Geneva: International Electrotechnical Commission, 2019.
