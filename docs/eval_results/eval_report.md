# eZ-PLM Component Risk Agent — 评测报告

**生成时间**：2026-05-29 16:37:21  
**用例总数**：20  
**通过**：18 ✅  |  **失败**：2 ❌  
**通过率**：90.0%  
**评测模式**：纯规则模式，无 LLM 依赖  

---

## 📊 总览

| 用例 ID | 输入摘要 | 解析通过 | 推荐数 | 风险等级 | 耗时(ms) |
|---------|----------|----------|--------|----------|----------|
| dc_dc_001 | 我需要一个 12V 转 5V、3A 的车规级降压芯片，工作温度 -40°C 到 ... | ✅ | 4 | ⚪ high | 3ms |
| dc_dc_002 | 需要 24V 转 12V、2A 的降压方案，工作温度 -40°C 到 85°C。 | ✅ | 2 | ⚪ medium | 2ms |
| dc_dc_003 | 我需要 12V 转 5V、4A 的降压芯片，非车规，室温使用。 | ✅ | 0 | ⚪ high | 2ms |
| dc_dc_004 | 12V转5V，3A，温度范围 -20C 到 85C，优先低供应链风险。 | ✅ | 4 | ⚪ medium | 2ms |
| dc_dc_005 | 请给我一个 5V 到 3.3V 的降压芯片，输出 1A。 | ✅ | 5 | ⚪ medium | 2ms |
| dc_dc_006 | 需要 48V 转 12V、1.5A 的降压模块，用于工业温度 -40°C 到 8... | ✅ | 0 | ⚪ high | 2ms |
| dc_dc_007 | 找一个 9V 转 5V、2A 的降压，温度 0°C 到 70°C，非车规。 | ✅ | 4 | ⚪ medium | 2ms |
| dc_dc_008 | 需要 12V 到 5V、3A 的车规级降压（automotive）。 | ✅ | 4 | ⚪ high | 2ms |
| dc_dc_009 | 5V转3.3V，输出 0.5A，优先低供应链风险。 | ✅ | 5 | ⚪ medium | 2ms |
| dc_dc_010 | 输入 24V，输出 5V，电流 10A，高功率场景。 | ✅ | 0 | ⚪ high | 2ms |
| dc_dc_011 | 找一个 18V 转 5V、6A 的车规级降压芯片，工作温度 -40°C 到 12... | ✅ | 0 | ⚪ high | 2ms |
| dc_dc_012 | 需要 28V 转 12V、2A 的降压芯片，工业温度 -40°C 到 105°C... | ✅ | 2 | ⚪ medium | 2ms |
| dc_dc_013 | 36V 输入，输出 5V、8A，大功率 DC-DC，希望库存充足。 | ❌ | 1 | ⚪ medium | 2ms |
| dc_dc_014 | 需要一个 3.3V 转 1.8V、0.6A 的降压芯片，温度 -40°C 到 8... | ✅ | 5 | ⚪ medium | 2ms |
| dc_dc_015 | 12V 转 5V、1.2A 降压，室温使用，要求成本最低。 | ✅ | 5 | ⚪ medium | 2ms |
| dc_dc_016 | 需要 24V 转 5V、4A 的车规级 AEC-Q100 降压，-40°C 到 ... | ✅ | 0 | ⚪ high | 2ms |
| dc_dc_017 | 48V 转 5V、3A 工业级电源方案，工作温度 -40°C 到 85°C，库存... | ❌ | 1 | ⚪ medium | 2ms |
| dc_dc_018 | 请找一个 12V 转 3.3V、1.5A 的降压，温度 -40°C 到 85°C... | ✅ | 5 | ⚪ medium | 2ms |
| dc_dc_019 | 需要一个 5V 转 1.2V、0.3A 的低压降压芯片，温度 -40°C 到 8... | ✅ | 5 | ⚪ medium | 2ms |
| dc_dc_020 | 30V 输入，输出 12V、6A 的车规级 DC-DC，工作温度 -40°C 到... | ✅ | 0 | ⚪ high | 2ms |

---

## 📋 逐用例详情

### 1. dc_dc_001 ✅

**输入**：我需要一个 12V 转 5V、3A 的车规级降压芯片，工作温度 -40°C 到 125°C，优先国产替代。  
**耗时**：3ms  

**解析约束**：

| 字段 | 值 |
|------|-----|
| category | dc_dc_converter |
| topology | buck |
| grade | automotive |
| input_voltage_nominal_v | 12.0 |
| output_voltage_v | 5.0 |
| output_current_a | 3.0 |
| temperature_min_c | -40 |
| temperature_max_c | 125 |
| preferences | domestic_alternative |

**候选评分明细**（共 4 个）：

| # | 型号 | 厂商 | 国产 | 车规 | 总分 | 参数 | 供应 | 成本 | 国产 | 证据 | 推荐等级 |
|---|------|------|------|------|------|------|------|------|------|------|----------|
| 1 | LM2576HVT-5.0/LF03 | Texas Instruments Incorporated | 🌍 | - | **80** | 88 | 50 | 0 | 0 | 0 | ⭐ recommended |
| 2 | LM2576S-5.0/NOPB | Texas Instruments Incorporated | 🌍 | - | **80** | 88 | 50 | 0 | 0 | 0 | ⭐ recommended |
| 3 | LM2576SX-5.0/NOPB | Texas Instruments Incorporated | 🌍 | - | **80** | 88 | 50 | 0 | 0 | 0 | ⭐ recommended |
| 4 | LM2576T-5.0/LF02 | Texas Instruments Incorporated | 🌍 | - | **80** | 88 | 50 | 0 | 0 | 0 | ⭐ recommended |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（4.0–60.0V 含标称 12.0V）
- 输出电压匹配 ✓（5.0V = 需求 5.0V）
- 输出电流满足 ✓（3.0A，余量 0%）
- 温度范围覆盖 ✓（-40.0–125.0°C）
- 有数据手册
- 同类变体：LM2576HVT-5.0/NOPB

**证据链**（共 20 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| LM2576HVT-5.0/LF03 | `ezplm_api` | 输入电压范围 4.0–60.0V | 95% |  |
| LM2576HVT-5.0/LF03 | `ezplm_api` | 最大输出电流 3.0A | 90% |  |
| LM2576HVT-5.0/LF03 | `ezplm_api` | 工作温度范围 -40.0–125.0°C | 95% |  |
| LM2576HVT-5.0/LF03 | `automotive_cert` | LM2576HVT-5.0/LF03 未标注车规认证，但需求要求车规等级，需人工确认是否可用 | 30% | ⚠️ |
| LM2576HVT-5.0/LF03 | `datasheet` | LM2576HVT-5.0/LF03 数据手册可查，规格参数可进一步核实 | 95% |  |
| LM2576S-5.0/NOPB | `ezplm_api` | 输入电压范围 4.0–40.0V | 95% |  |
| LM2576S-5.0/NOPB | `ezplm_api` | 最大输出电流 3.0A | 90% |  |
| LM2576S-5.0/NOPB | `ezplm_api` | 工作温度范围 -40.0–125.0°C | 95% |  |
| LM2576S-5.0/NOPB | `automotive_cert` | LM2576S-5.0/NOPB 未标注车规认证，但需求要求车规等级，需人工确认是否可用 | 30% | ⚠️ |
| LM2576S-5.0/NOPB | `datasheet` | LM2576S-5.0/NOPB 数据手册可查，规格参数可进一步核实 | 95% |  |
| ... | ... | _(共 20 条，仅展示前 10 条)_ | ... | ... |

**风险评估**：⚪ high

- ⚪ **medium** — 推荐器件全部来自同一制造商（Texas Instruments Incorporated），存在供应商集中风险。 _(缓解: 建议引入第二供应商，降低单一来源依赖。)_
- ⚪ **medium** — 用户偏好国产替代，但当前推荐器件均为进口，国产化目标未达成。 _(缓解: 扩充国产器件库，或联系国产厂商获取样品评估。)_
- ⚪ **high** — 需求要求车规等级，但所有推荐器件均非车规认证，不可直接用于车载产品。 _(缓解: 重新筛选 AEC-Q100 认证器件，或向制造商确认车规版本。)_
- ⚪ **medium** — 全部 4 条候选器件的生命周期状态未知，无法评估停产/断供风险。 _(缓解: 从制造商官网或授权分销商处确认各器件当前生命周期状态（Active/NRND/EOL）。)_
- ⚪ **medium** — 全部候选器件的当前库存信息缺失，无法评估现货供应能力与交期。 _(缓解: 通过 eZ-PLM API 或分销商接口获取实时库存数据。)_
- ⚪ **low** — 全部候选器件的封装信息缺失，PCB Layout 评估缺少依据。 _(缓解: 从数据手册或制造商网站获取封装代码与推荐焊盘图纸。)_
- ⚪ **medium** — 推荐器件全部来自境外单一供应商 Texas Instruments Incorporated，存在贸易管制/关税变动的地缘政治风险。 _(缓解: 纳入至少 1 家国产兼容型号作为第二供应源，或评估非美国来源替代方案。)_

---

### 2. dc_dc_002 ✅

**输入**：需要 24V 转 12V、2A 的降压方案，工作温度 -40°C 到 85°C。  
**耗时**：2ms  

**解析约束**：

| 字段 | 值 |
|------|-----|
| category | dc_dc_converter |
| topology | buck |
| input_voltage_nominal_v | 24.0 |
| output_voltage_v | 12.0 |
| output_current_a | 2.0 |
| temperature_min_c | -40 |
| temperature_max_c | 85 |

**候选评分明细**（共 2 个）：

| # | 型号 | 厂商 | 国产 | 车规 | 总分 | 参数 | 供应 | 成本 | 国产 | 证据 | 推荐等级 |
|---|------|------|------|------|------|------|------|------|------|------|----------|
| 1 | LM2576S-12/NOPB | Texas Instruments Incorporated | 🌍 | - | **85** | 94 | 50 | 0 | 0 | 0 | ⭐ recommended |
| 2 | LM2576T-12/LF03 | Texas Instruments Incorporated | 🌍 | - | **85** | 94 | 50 | 0 | 0 | 0 | ⭐ recommended |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（4.0–40.0V 含标称 24.0V）
- 输出电压匹配 ✓（12.0V = 需求 12.0V）
- 输出电流满足 ✓（3.0A，余量 50%）
- 温度范围覆盖 ✓（-40.0–125.0°C）
- 有数据手册

**证据链**（共 8 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| LM2576S-12/NOPB | `ezplm_api` | 输入电压范围 4.0–40.0V | 95% |  |
| LM2576S-12/NOPB | `ezplm_api` | 最大输出电流 3.0A | 90% |  |
| LM2576S-12/NOPB | `ezplm_api` | 工作温度范围 -40.0–125.0°C | 95% |  |
| LM2576S-12/NOPB | `datasheet` | LM2576S-12/NOPB 数据手册可查，规格参数可进一步核实 | 95% |  |
| LM2576T-12/LF03 | `ezplm_api` | 输入电压范围 4.0–40.0V | 95% |  |
| LM2576T-12/LF03 | `ezplm_api` | 最大输出电流 3.0A | 90% |  |
| LM2576T-12/LF03 | `ezplm_api` | 工作温度范围 -40.0–125.0°C | 95% |  |
| LM2576T-12/LF03 | `datasheet` | LM2576T-12/LF03 数据手册可查，规格参数可进一步核实 | 95% |  |

**风险评估**：⚪ medium

- ⚪ **medium** — 全部 2 条候选器件的生命周期状态未知，无法评估停产/断供风险。 _(缓解: 从制造商官网或授权分销商处确认各器件当前生命周期状态（Active/NRND/EOL）。)_
- ⚪ **medium** — 全部候选器件的当前库存信息缺失，无法评估现货供应能力与交期。 _(缓解: 通过 eZ-PLM API 或分销商接口获取实时库存数据。)_
- ⚪ **low** — 全部候选器件的封装信息缺失，PCB Layout 评估缺少依据。 _(缓解: 从数据手册或制造商网站获取封装代码与推荐焊盘图纸。)_
- ⚪ **medium** — 推荐器件全部来自境外单一供应商 Texas Instruments Incorporated，存在贸易管制/关税变动的地缘政治风险。 _(缓解: 纳入至少 1 家国产兼容型号作为第二供应源，或评估非美国来源替代方案。)_

---

### 3. dc_dc_003 ✅

**输入**：我需要 12V 转 5V、4A 的降压芯片，非车规，室温使用。  
**耗时**：2ms  

**解析约束**：

| 字段 | 值 |
|------|-----|
| category | dc_dc_converter |
| topology | buck |
| grade | industrial |
| input_voltage_nominal_v | 12.0 |
| output_voltage_v | 5.0 |
| output_current_a | 4.0 |

**风险评估**：⚪ high

- ⚪ **high** — 检索无结果，请确认类别/拓扑约束或扩充数据源。 _(缓解: 检查 EZ-PLM API 白名单覆盖情况，或补充 mock 数据。)_

---

### 4. dc_dc_004 ✅

**输入**：12V转5V，3A，温度范围 -20C 到 85C，优先低供应链风险。  
**耗时**：2ms  

**解析约束**：

| 字段 | 值 |
|------|-----|
| category | dc_dc_converter |
| topology | buck |
| input_voltage_nominal_v | 12.0 |
| output_voltage_v | 5.0 |
| output_current_a | 3.0 |
| temperature_min_c | -20 |
| temperature_max_c | 85 |
| preferences | low_supply_risk |

**候选评分明细**（共 4 个）：

| # | 型号 | 厂商 | 国产 | 车规 | 总分 | 参数 | 供应 | 成本 | 国产 | 证据 | 推荐等级 |
|---|------|------|------|------|------|------|------|------|------|------|----------|
| 1 | LM2576HVT-5.0/LF03 | Texas Instruments Incorporated | 🌍 | - | **80** | 88 | 50 | 0 | 0 | 0 | ⭐ recommended |
| 2 | LM2576S-5.0/NOPB | Texas Instruments Incorporated | 🌍 | - | **80** | 88 | 50 | 0 | 0 | 0 | ⭐ recommended |
| 3 | LM2576SX-5.0/NOPB | Texas Instruments Incorporated | 🌍 | - | **80** | 88 | 50 | 0 | 0 | 0 | ⭐ recommended |
| 4 | LM2576T-5.0/LF02 | Texas Instruments Incorporated | 🌍 | - | **80** | 88 | 50 | 0 | 0 | 0 | ⭐ recommended |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（4.0–60.0V 含标称 12.0V）
- 输出电压匹配 ✓（5.0V = 需求 5.0V）
- 输出电流满足 ✓（3.0A，余量 0%）
- 温度范围覆盖 ✓（-40.0–125.0°C）
- 有数据手册
- 同类变体：LM2576HVT-5.0/NOPB

**证据链**（共 16 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| LM2576HVT-5.0/LF03 | `ezplm_api` | 输入电压范围 4.0–60.0V | 95% |  |
| LM2576HVT-5.0/LF03 | `ezplm_api` | 最大输出电流 3.0A | 90% |  |
| LM2576HVT-5.0/LF03 | `ezplm_api` | 工作温度范围 -40.0–125.0°C | 95% |  |
| LM2576HVT-5.0/LF03 | `datasheet` | LM2576HVT-5.0/LF03 数据手册可查，规格参数可进一步核实 | 95% |  |
| LM2576S-5.0/NOPB | `ezplm_api` | 输入电压范围 4.0–40.0V | 95% |  |
| LM2576S-5.0/NOPB | `ezplm_api` | 最大输出电流 3.0A | 90% |  |
| LM2576S-5.0/NOPB | `ezplm_api` | 工作温度范围 -40.0–125.0°C | 95% |  |
| LM2576S-5.0/NOPB | `datasheet` | LM2576S-5.0/NOPB 数据手册可查，规格参数可进一步核实 | 95% |  |
| LM2576SX-5.0/NOPB | `ezplm_api` | 输入电压范围 4.0–40.0V | 95% |  |
| LM2576SX-5.0/NOPB | `ezplm_api` | 最大输出电流 3.0A | 90% |  |
| ... | ... | _(共 16 条，仅展示前 10 条)_ | ... | ... |

**风险评估**：⚪ medium

- ⚪ **medium** — 推荐器件全部来自同一制造商（Texas Instruments Incorporated），存在供应商集中风险。 _(缓解: 建议引入第二供应商，降低单一来源依赖。)_
- ⚪ **medium** — 全部 4 条候选器件的生命周期状态未知，无法评估停产/断供风险。 _(缓解: 从制造商官网或授权分销商处确认各器件当前生命周期状态（Active/NRND/EOL）。)_
- ⚪ **medium** — 全部候选器件的当前库存信息缺失，无法评估现货供应能力与交期。 _(缓解: 通过 eZ-PLM API 或分销商接口获取实时库存数据。)_
- ⚪ **low** — 全部候选器件的封装信息缺失，PCB Layout 评估缺少依据。 _(缓解: 从数据手册或制造商网站获取封装代码与推荐焊盘图纸。)_
- ⚪ **medium** — 推荐器件全部来自境外单一供应商 Texas Instruments Incorporated，存在贸易管制/关税变动的地缘政治风险。 _(缓解: 纳入至少 1 家国产兼容型号作为第二供应源，或评估非美国来源替代方案。)_

---

### 5. dc_dc_005 ✅

**输入**：请给我一个 5V 到 3.3V 的降压芯片，输出 1A。  
**耗时**：2ms  

**解析约束**：

| 字段 | 值 |
|------|-----|
| category | dc_dc_converter |
| topology | buck |
| input_voltage_nominal_v | 5.0 |
| output_voltage_v | 3.3 |
| output_current_a | 1.0 |

**候选评分明细**（共 13 个）：

| # | 型号 | 厂商 | 国产 | 车规 | 总分 | 参数 | 供应 | 成本 | 国产 | 证据 | 推荐等级 |
|---|------|------|------|------|------|------|------|------|------|------|----------|
| 1 | MCP1700T-5002E/MBVAO | Microchip Technology Inc. | 🌍 | - | **90** | 100 | 50 | 0 | 0 | 0 | ⭐ recommended |
| 2 | LM2576HVT-ADJ/LF03 | Texas Instruments Incorporated | 🌍 | - | **90** | 100 | 50 | 0 | 0 | 0 | ⭐ recommended |
| 3 | LM2576S-3.3/NOPB | Texas Instruments Incorporated | 🌍 | - | **90** | 100 | 50 | 0 | 0 | 0 | ⭐ recommended |
| 4 | LM2576SX-3.3/NOPB | Texas Instruments Incorporated | 🌍 | - | **90** | 100 | 50 | 0 | 0 | 0 | ⭐ recommended |
| 5 | LM2576T-3.3/LF03 | Texas Instruments Incorporated | 🌍 | - | **90** | 100 | 50 | 0 | 0 | 0 | ⭐ recommended |
| 6 | TPS62063DSGR | Texas Instruments Incorporated | 🌍 | - | **85** | 93 | 50 | 0 | 0 | 0 | 🟡 backup |
| 7 | TPS54200DDCR | Texas Instruments Incorporated | 🌍 | - | **80** | 88 | 50 | 0 | 0 | 0 | 🟡 backup |
| 8 | TPS54200DDCT | Texas Instruments Incorporated | 🌍 | - | **80** | 88 | 50 | 0 | 0 | 0 | 🟡 backup |
| 9 | TPS54201DDCR | Texas Instruments Incorporated | 🌍 | - | **80** | 88 | 50 | 0 | 0 | 0 | 🟡 backup |
| 10 | TPS54201DDCT | Texas Instruments Incorporated | 🌍 | - | **80** | 88 | 50 | 0 | 0 | 0 | 🟡 backup |
| 11 | TPS62046DGQ | Texas Instruments Incorporated | 🌍 | - | **79** | 87 | 50 | 0 | 0 | 0 | 🟡 backup |
| 12 | TPS62046DGQR | Texas Instruments Incorporated | 🌍 | - | **79** | 87 | 50 | 0 | 0 | 0 | 🟡 backup |
| 13 | TPS62046DRCR | Texas Instruments Incorporated | 🌍 | - | **79** | 87 | 50 | 0 | 0 | 0 | 🟡 backup |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（2.3–6.0V 含标称 5.0V）
- 输出电流满足 ✓（250.0A，余量 24900%）
- 有数据手册

**证据链**（共 51 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| MCP1700T-5002E/MBVAO | `ezplm_api` | 输入电压范围 2.3–6.0V | 95% |  |
| MCP1700T-5002E/MBVAO | `ezplm_api` | 最大输出电流 250.0A | 90% |  |
| MCP1700T-5002E/MBVAO | `datasheet` | MCP1700T-5002E/MBVAO 数据手册可查，规格参数可进一步核实 | 95% |  |
| LM2576HVT-ADJ/LF03 | `ezplm_api` | 输入电压范围 4.0–60.0V | 95% |  |
| LM2576HVT-ADJ/LF03 | `ezplm_api` | 最大输出电流 3.0A | 90% |  |
| LM2576HVT-ADJ/LF03 | `ezplm_api` | 工作温度范围 -40.0–125.0°C | 95% |  |
| LM2576HVT-ADJ/LF03 | `datasheet` | LM2576HVT-ADJ/LF03 数据手册可查，规格参数可进一步核实 | 95% |  |
| LM2576S-3.3/NOPB | `ezplm_api` | 输入电压范围 4.0–40.0V | 95% |  |
| LM2576S-3.3/NOPB | `ezplm_api` | 最大输出电流 3.0A | 90% |  |
| LM2576S-3.3/NOPB | `ezplm_api` | 工作温度范围 -40.0–125.0°C | 95% |  |
| ... | ... | _(共 51 条，仅展示前 10 条)_ | ... | ... |

**风险评估**：⚪ medium

- ⚪ **medium** — 全部 13 条候选器件的生命周期状态未知，无法评估停产/断供风险。 _(缓解: 从制造商官网或授权分销商处确认各器件当前生命周期状态（Active/NRND/EOL）。)_
- ⚪ **medium** — 全部候选器件的当前库存信息缺失，无法评估现货供应能力与交期。 _(缓解: 通过 eZ-PLM API 或分销商接口获取实时库存数据。)_
- ⚪ **low** — 全部候选器件的封装信息缺失，PCB Layout 评估缺少依据。 _(缓解: 从数据手册或制造商网站获取封装代码与推荐焊盘图纸。)_

---

### 6. dc_dc_006 ✅

**输入**：需要 48V 转 12V、1.5A 的降压模块，用于工业温度 -40°C 到 85°C，优先国产。  
**耗时**：2ms  

**解析约束**：

| 字段 | 值 |
|------|-----|
| category | dc_dc_converter |
| topology | buck |
| input_voltage_nominal_v | 48.0 |
| output_voltage_v | 12.0 |
| output_current_a | 1.5 |
| temperature_min_c | -40 |
| temperature_max_c | 85 |
| preferences | domestic_alternative |

**风险评估**：⚪ high

- ⚪ **high** — 检索无结果，请确认类别/拓扑约束或扩充数据源。 _(缓解: 检查 EZ-PLM API 白名单覆盖情况，或补充 mock 数据。)_

---

### 7. dc_dc_007 ✅

**输入**：找一个 9V 转 5V、2A 的降压，温度 0°C 到 70°C，非车规。  
**耗时**：2ms  

**解析约束**：

| 字段 | 值 |
|------|-----|
| category | dc_dc_converter |
| topology | buck |
| grade | industrial |
| input_voltage_nominal_v | 9.0 |
| output_voltage_v | 5.0 |
| output_current_a | 2.0 |
| temperature_min_c | 0 |
| temperature_max_c | 70 |

**候选评分明细**（共 4 个）：

| # | 型号 | 厂商 | 国产 | 车规 | 总分 | 参数 | 供应 | 成本 | 国产 | 证据 | 推荐等级 |
|---|------|------|------|------|------|------|------|------|------|------|----------|
| 1 | LM2576HVT-5.0/LF03 | Texas Instruments Incorporated | 🌍 | - | **85** | 94 | 50 | 0 | 0 | 0 | ⭐ recommended |
| 2 | LM2576S-5.0/NOPB | Texas Instruments Incorporated | 🌍 | - | **85** | 94 | 50 | 0 | 0 | 0 | ⭐ recommended |
| 3 | LM2576SX-5.0/NOPB | Texas Instruments Incorporated | 🌍 | - | **85** | 94 | 50 | 0 | 0 | 0 | ⭐ recommended |
| 4 | LM2576T-5.0/LF02 | Texas Instruments Incorporated | 🌍 | - | **85** | 94 | 50 | 0 | 0 | 0 | ⭐ recommended |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（4.0–60.0V 含标称 9.0V）
- 输出电压匹配 ✓（5.0V = 需求 5.0V）
- 输出电流满足 ✓（3.0A，余量 50%）
- 温度范围覆盖 ✓（-40.0–125.0°C）
- 有数据手册
- 同类变体：LM2576HVT-5.0/NOPB

**证据链**（共 16 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| LM2576HVT-5.0/LF03 | `ezplm_api` | 输入电压范围 4.0–60.0V | 95% |  |
| LM2576HVT-5.0/LF03 | `ezplm_api` | 最大输出电流 3.0A | 90% |  |
| LM2576HVT-5.0/LF03 | `ezplm_api` | 工作温度范围 -40.0–125.0°C | 95% |  |
| LM2576HVT-5.0/LF03 | `datasheet` | LM2576HVT-5.0/LF03 数据手册可查，规格参数可进一步核实 | 95% |  |
| LM2576S-5.0/NOPB | `ezplm_api` | 输入电压范围 4.0–40.0V | 95% |  |
| LM2576S-5.0/NOPB | `ezplm_api` | 最大输出电流 3.0A | 90% |  |
| LM2576S-5.0/NOPB | `ezplm_api` | 工作温度范围 -40.0–125.0°C | 95% |  |
| LM2576S-5.0/NOPB | `datasheet` | LM2576S-5.0/NOPB 数据手册可查，规格参数可进一步核实 | 95% |  |
| LM2576SX-5.0/NOPB | `ezplm_api` | 输入电压范围 4.0–40.0V | 95% |  |
| LM2576SX-5.0/NOPB | `ezplm_api` | 最大输出电流 3.0A | 90% |  |
| ... | ... | _(共 16 条，仅展示前 10 条)_ | ... | ... |

**风险评估**：⚪ medium

- ⚪ **medium** — 推荐器件全部来自同一制造商（Texas Instruments Incorporated），存在供应商集中风险。 _(缓解: 建议引入第二供应商，降低单一来源依赖。)_
- ⚪ **medium** — 全部 4 条候选器件的生命周期状态未知，无法评估停产/断供风险。 _(缓解: 从制造商官网或授权分销商处确认各器件当前生命周期状态（Active/NRND/EOL）。)_
- ⚪ **medium** — 全部候选器件的当前库存信息缺失，无法评估现货供应能力与交期。 _(缓解: 通过 eZ-PLM API 或分销商接口获取实时库存数据。)_
- ⚪ **low** — 全部候选器件的封装信息缺失，PCB Layout 评估缺少依据。 _(缓解: 从数据手册或制造商网站获取封装代码与推荐焊盘图纸。)_
- ⚪ **medium** — 推荐器件全部来自境外单一供应商 Texas Instruments Incorporated，存在贸易管制/关税变动的地缘政治风险。 _(缓解: 纳入至少 1 家国产兼容型号作为第二供应源，或评估非美国来源替代方案。)_

---

### 8. dc_dc_008 ✅

**输入**：需要 12V 到 5V、3A 的车规级降压（automotive）。  
**耗时**：2ms  

**解析约束**：

| 字段 | 值 |
|------|-----|
| category | dc_dc_converter |
| topology | buck |
| grade | automotive |
| input_voltage_nominal_v | 12.0 |
| output_voltage_v | 5.0 |
| output_current_a | 3.0 |

**候选评分明细**（共 4 个）：

| # | 型号 | 厂商 | 国产 | 车规 | 总分 | 参数 | 供应 | 成本 | 国产 | 证据 | 推荐等级 |
|---|------|------|------|------|------|------|------|------|------|------|----------|
| 1 | LM2576HVT-5.0/LF03 | Texas Instruments Incorporated | 🌍 | - | **77** | 83 | 50 | 0 | 0 | 0 | ⭐ recommended |
| 2 | LM2576S-5.0/NOPB | Texas Instruments Incorporated | 🌍 | - | **77** | 83 | 50 | 0 | 0 | 0 | ⭐ recommended |
| 3 | LM2576SX-5.0/NOPB | Texas Instruments Incorporated | 🌍 | - | **77** | 83 | 50 | 0 | 0 | 0 | ⭐ recommended |
| 4 | LM2576T-5.0/LF02 | Texas Instruments Incorporated | 🌍 | - | **77** | 83 | 50 | 0 | 0 | 0 | ⭐ recommended |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（4.0–60.0V 含标称 12.0V）
- 输出电压匹配 ✓（5.0V = 需求 5.0V）
- 输出电流满足 ✓（3.0A，余量 0%）
- 有数据手册
- 同类变体：LM2576HVT-5.0/NOPB

**证据链**（共 20 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| LM2576HVT-5.0/LF03 | `ezplm_api` | 输入电压范围 4.0–60.0V | 95% |  |
| LM2576HVT-5.0/LF03 | `ezplm_api` | 最大输出电流 3.0A | 90% |  |
| LM2576HVT-5.0/LF03 | `ezplm_api` | 工作温度范围 -40.0–125.0°C | 95% |  |
| LM2576HVT-5.0/LF03 | `automotive_cert` | LM2576HVT-5.0/LF03 未标注车规认证，但需求要求车规等级，需人工确认是否可用 | 30% | ⚠️ |
| LM2576HVT-5.0/LF03 | `datasheet` | LM2576HVT-5.0/LF03 数据手册可查，规格参数可进一步核实 | 95% |  |
| LM2576S-5.0/NOPB | `ezplm_api` | 输入电压范围 4.0–40.0V | 95% |  |
| LM2576S-5.0/NOPB | `ezplm_api` | 最大输出电流 3.0A | 90% |  |
| LM2576S-5.0/NOPB | `ezplm_api` | 工作温度范围 -40.0–125.0°C | 95% |  |
| LM2576S-5.0/NOPB | `automotive_cert` | LM2576S-5.0/NOPB 未标注车规认证，但需求要求车规等级，需人工确认是否可用 | 30% | ⚠️ |
| LM2576S-5.0/NOPB | `datasheet` | LM2576S-5.0/NOPB 数据手册可查，规格参数可进一步核实 | 95% |  |
| ... | ... | _(共 20 条，仅展示前 10 条)_ | ... | ... |

**风险评估**：⚪ high

- ⚪ **medium** — 推荐器件全部来自同一制造商（Texas Instruments Incorporated），存在供应商集中风险。 _(缓解: 建议引入第二供应商，降低单一来源依赖。)_
- ⚪ **high** — 需求要求车规等级，但所有推荐器件均非车规认证，不可直接用于车载产品。 _(缓解: 重新筛选 AEC-Q100 认证器件，或向制造商确认车规版本。)_
- ⚪ **medium** — 全部 4 条候选器件的生命周期状态未知，无法评估停产/断供风险。 _(缓解: 从制造商官网或授权分销商处确认各器件当前生命周期状态（Active/NRND/EOL）。)_
- ⚪ **medium** — 全部候选器件的当前库存信息缺失，无法评估现货供应能力与交期。 _(缓解: 通过 eZ-PLM API 或分销商接口获取实时库存数据。)_
- ⚪ **low** — 全部候选器件的封装信息缺失，PCB Layout 评估缺少依据。 _(缓解: 从数据手册或制造商网站获取封装代码与推荐焊盘图纸。)_
- ⚪ **medium** — 推荐器件全部来自境外单一供应商 Texas Instruments Incorporated，存在贸易管制/关税变动的地缘政治风险。 _(缓解: 纳入至少 1 家国产兼容型号作为第二供应源，或评估非美国来源替代方案。)_

---

### 9. dc_dc_009 ✅

**输入**：5V转3.3V，输出 0.5A，优先低供应链风险。  
**耗时**：2ms  

**解析约束**：

| 字段 | 值 |
|------|-----|
| category | dc_dc_converter |
| topology | buck |
| input_voltage_nominal_v | 5.0 |
| output_voltage_v | 3.3 |
| output_current_a | 0.5 |
| preferences | low_supply_risk |

**候选评分明细**（共 15 个）：

| # | 型号 | 厂商 | 国产 | 车规 | 总分 | 参数 | 供应 | 成本 | 国产 | 证据 | 推荐等级 |
|---|------|------|------|------|------|------|------|------|------|------|----------|
| 1 | MCP1700T-5002E/MBVAO | Microchip Technology Inc. | 🌍 | - | **90** | 100 | 50 | 0 | 0 | 0 | ⭐ recommended |
| 2 | LM2576HVT-ADJ/LF03 | Texas Instruments Incorporated | 🌍 | - | **90** | 100 | 50 | 0 | 0 | 0 | ⭐ recommended |
| 3 | LM2576S-3.3/NOPB | Texas Instruments Incorporated | 🌍 | - | **90** | 100 | 50 | 0 | 0 | 0 | ⭐ recommended |
| 4 | LM2576SX-3.3/NOPB | Texas Instruments Incorporated | 🌍 | - | **90** | 100 | 50 | 0 | 0 | 0 | ⭐ recommended |
| 5 | LM2576T-3.3/LF03 | Texas Instruments Incorporated | 🌍 | - | **90** | 100 | 50 | 0 | 0 | 0 | ⭐ recommended |
| 6 | TPS54200DDCR | Texas Instruments Incorporated | 🌍 | - | **90** | 100 | 50 | 0 | 0 | 0 | 🟡 backup |
| 7 | TPS54200DDCT | Texas Instruments Incorporated | 🌍 | - | **90** | 100 | 50 | 0 | 0 | 0 | 🟡 backup |
| 8 | TPS54201DDCR | Texas Instruments Incorporated | 🌍 | - | **90** | 100 | 50 | 0 | 0 | 0 | 🟡 backup |
| 9 | TPS54201DDCT | Texas Instruments Incorporated | 🌍 | - | **90** | 100 | 50 | 0 | 0 | 0 | 🟡 backup |
| 10 | TPS62046DGQ | Texas Instruments Incorporated | 🌍 | - | **90** | 100 | 50 | 0 | 0 | 0 | 🟡 backup |
| 11 | TPS62046DGQR | Texas Instruments Incorporated | 🌍 | - | **90** | 100 | 50 | 0 | 0 | 0 | 🟡 backup |
| 12 | TPS62046DRCR | Texas Instruments Incorporated | 🌍 | - | **90** | 100 | 50 | 0 | 0 | 0 | 🟡 backup |
| 13 | TPS62063DSGR | Texas Instruments Incorporated | 🌍 | - | **90** | 100 | 50 | 0 | 0 | 0 | 🟡 backup |
| 14 | TPS62056DGS | Texas Instruments Incorporated | 🌍 | - | **85** | 93 | 50 | 0 | 0 | 0 | 🟡 backup |
| 15 | TPS62056DGSR | Texas Instruments Incorporated | 🌍 | - | **85** | 93 | 50 | 0 | 0 | 0 | 🟡 backup |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（2.3–6.0V 含标称 5.0V）
- 输出电流满足 ✓（250.0A，余量 49900%）
- 有数据手册

**证据链**（共 59 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| MCP1700T-5002E/MBVAO | `ezplm_api` | 输入电压范围 2.3–6.0V | 95% |  |
| MCP1700T-5002E/MBVAO | `ezplm_api` | 最大输出电流 250.0A | 90% |  |
| MCP1700T-5002E/MBVAO | `datasheet` | MCP1700T-5002E/MBVAO 数据手册可查，规格参数可进一步核实 | 95% |  |
| LM2576HVT-ADJ/LF03 | `ezplm_api` | 输入电压范围 4.0–60.0V | 95% |  |
| LM2576HVT-ADJ/LF03 | `ezplm_api` | 最大输出电流 3.0A | 90% |  |
| LM2576HVT-ADJ/LF03 | `ezplm_api` | 工作温度范围 -40.0–125.0°C | 95% |  |
| LM2576HVT-ADJ/LF03 | `datasheet` | LM2576HVT-ADJ/LF03 数据手册可查，规格参数可进一步核实 | 95% |  |
| LM2576S-3.3/NOPB | `ezplm_api` | 输入电压范围 4.0–40.0V | 95% |  |
| LM2576S-3.3/NOPB | `ezplm_api` | 最大输出电流 3.0A | 90% |  |
| LM2576S-3.3/NOPB | `ezplm_api` | 工作温度范围 -40.0–125.0°C | 95% |  |
| ... | ... | _(共 59 条，仅展示前 10 条)_ | ... | ... |

**风险评估**：⚪ medium

- ⚪ **medium** — 全部 15 条候选器件的生命周期状态未知，无法评估停产/断供风险。 _(缓解: 从制造商官网或授权分销商处确认各器件当前生命周期状态（Active/NRND/EOL）。)_
- ⚪ **medium** — 全部候选器件的当前库存信息缺失，无法评估现货供应能力与交期。 _(缓解: 通过 eZ-PLM API 或分销商接口获取实时库存数据。)_
- ⚪ **low** — 全部候选器件的封装信息缺失，PCB Layout 评估缺少依据。 _(缓解: 从数据手册或制造商网站获取封装代码与推荐焊盘图纸。)_

---

### 10. dc_dc_010 ✅

**输入**：输入 24V，输出 5V，电流 10A，高功率场景。  
**耗时**：2ms  

**解析约束**：

| 字段 | 值 |
|------|-----|
| category | dc_dc_converter |
| topology | buck |
| input_voltage_nominal_v | 24.0 |
| output_voltage_v | 5.0 |
| output_current_a | 10.0 |

**风险评估**：⚪ high

- ⚪ **high** — 检索无结果，请确认类别/拓扑约束或扩充数据源。 _(缓解: 检查 EZ-PLM API 白名单覆盖情况，或补充 mock 数据。)_

---

### 11. dc_dc_011 ✅

**输入**：找一个 18V 转 5V、6A 的车规级降压芯片，工作温度 -40°C 到 125°C，必须国产，低供应风险。  
**耗时**：2ms  

**解析约束**：

| 字段 | 值 |
|------|-----|
| category | dc_dc_converter |
| topology | buck |
| grade | automotive |
| input_voltage_nominal_v | 18.0 |
| output_voltage_v | 5.0 |
| output_current_a | 6.0 |
| temperature_min_c | -40 |
| temperature_max_c | 125 |
| preferences | domestic_alternative, low_supply_risk |
| must_have | domestic |

**风险评估**：⚪ high

- ⚪ **high** — 检索无结果，请确认类别/拓扑约束或扩充数据源。 _(缓解: 检查 EZ-PLM API 白名单覆盖情况，或补充 mock 数据。)_

---

### 12. dc_dc_012 ✅

**输入**：需要 28V 转 12V、2A 的降压芯片，工业温度 -40°C 到 105°C，非车规，必须国产。  
**耗时**：2ms  

**解析约束**：

| 字段 | 值 |
|------|-----|
| category | dc_dc_converter |
| topology | buck |
| grade | industrial |
| input_voltage_nominal_v | 28.0 |
| output_voltage_v | 12.0 |
| output_current_a | 2.0 |
| temperature_min_c | -40 |
| temperature_max_c | 105 |
| preferences | domestic_alternative |
| must_have | domestic |

**候选评分明细**（共 2 个）：

| # | 型号 | 厂商 | 国产 | 车规 | 总分 | 参数 | 供应 | 成本 | 国产 | 证据 | 推荐等级 |
|---|------|------|------|------|------|------|------|------|------|------|----------|
| 1 | LM2576S-12/NOPB | Texas Instruments Incorporated | 🌍 | - | **85** | 94 | 50 | 0 | 0 | 0 | ⭐ recommended |
| 2 | LM2576T-12/LF03 | Texas Instruments Incorporated | 🌍 | - | **85** | 94 | 50 | 0 | 0 | 0 | ⭐ recommended |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（4.0–40.0V 含标称 28.0V）
- 输出电压匹配 ✓（12.0V = 需求 12.0V）
- 输出电流满足 ✓（3.0A，余量 50%）
- 温度范围覆盖 ✓（-40.0–125.0°C）
- 有数据手册

**证据链**（共 8 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| LM2576S-12/NOPB | `ezplm_api` | 输入电压范围 4.0–40.0V | 95% |  |
| LM2576S-12/NOPB | `ezplm_api` | 最大输出电流 3.0A | 90% |  |
| LM2576S-12/NOPB | `ezplm_api` | 工作温度范围 -40.0–125.0°C | 95% |  |
| LM2576S-12/NOPB | `datasheet` | LM2576S-12/NOPB 数据手册可查，规格参数可进一步核实 | 95% |  |
| LM2576T-12/LF03 | `ezplm_api` | 输入电压范围 4.0–40.0V | 95% |  |
| LM2576T-12/LF03 | `ezplm_api` | 最大输出电流 3.0A | 90% |  |
| LM2576T-12/LF03 | `ezplm_api` | 工作温度范围 -40.0–125.0°C | 95% |  |
| LM2576T-12/LF03 | `datasheet` | LM2576T-12/LF03 数据手册可查，规格参数可进一步核实 | 95% |  |

**风险评估**：⚪ medium

- ⚪ **medium** — 用户偏好国产替代，但当前推荐器件均为进口，国产化目标未达成。 _(缓解: 扩充国产器件库，或联系国产厂商获取样品评估。)_
- ⚪ **medium** — 全部 2 条候选器件的生命周期状态未知，无法评估停产/断供风险。 _(缓解: 从制造商官网或授权分销商处确认各器件当前生命周期状态（Active/NRND/EOL）。)_
- ⚪ **medium** — 全部候选器件的当前库存信息缺失，无法评估现货供应能力与交期。 _(缓解: 通过 eZ-PLM API 或分销商接口获取实时库存数据。)_
- ⚪ **low** — 全部候选器件的封装信息缺失，PCB Layout 评估缺少依据。 _(缓解: 从数据手册或制造商网站获取封装代码与推荐焊盘图纸。)_
- ⚪ **medium** — 推荐器件全部来自境外单一供应商 Texas Instruments Incorporated，存在贸易管制/关税变动的地缘政治风险。 _(缓解: 纳入至少 1 家国产兼容型号作为第二供应源，或评估非美国来源替代方案。)_

---

### 13. dc_dc_013 ❌

**输入**：36V 输入，输出 5V、8A，大功率 DC-DC，希望库存充足。  
**耗时**：2ms  

**解析失败项**：
- ❌ preference 'low_supply_risk' missing (got [])

**解析约束**：

| 字段 | 值 |
|------|-----|
| category | dc_dc_converter |
| topology | buck |
| input_voltage_nominal_v | 5.0 |
| output_voltage_v | 5.0 |
| output_current_a | 8.0 |

**候选评分明细**（共 1 个）：

| # | 型号 | 厂商 | 国产 | 车规 | 总分 | 参数 | 供应 | 成本 | 国产 | 证据 | 推荐等级 |
|---|------|------|------|------|------|------|------|------|------|------|----------|
| 1 | MCP1700T-5002E/MBVAO | Microchip Technology Inc. | 🌍 | - | **90** | 100 | 50 | 0 | 0 | 0 | ⭐ recommended |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（2.3–6.0V 含标称 5.0V）
- 输出电流满足 ✓（250.0A，余量 3025%）
- 有数据手册
- 同类变体：MCP1700T-5002E/TT

**证据链**（共 3 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| MCP1700T-5002E/MBVAO | `ezplm_api` | 输入电压范围 2.3–6.0V | 95% |  |
| MCP1700T-5002E/MBVAO | `ezplm_api` | 最大输出电流 250.0A | 90% |  |
| MCP1700T-5002E/MBVAO | `datasheet` | MCP1700T-5002E/MBVAO 数据手册可查，规格参数可进一步核实 | 95% |  |

**风险评估**：⚪ medium

- ⚪ **medium** — 仅 1 款推荐器件（MCP1700T-5002E/MBVAO），备选方案不足。 _(缓解: 纳入 backup 级器件作为冗余，或向供应商确认长期备货计划。)_
- ⚪ **medium** — 全部 1 条候选器件的生命周期状态未知，无法评估停产/断供风险。 _(缓解: 从制造商官网或授权分销商处确认各器件当前生命周期状态（Active/NRND/EOL）。)_
- ⚪ **medium** — 全部候选器件的当前库存信息缺失，无法评估现货供应能力与交期。 _(缓解: 通过 eZ-PLM API 或分销商接口获取实时库存数据。)_
- ⚪ **low** — 全部候选器件的封装信息缺失，PCB Layout 评估缺少依据。 _(缓解: 从数据手册或制造商网站获取封装代码与推荐焊盘图纸。)_

---

### 14. dc_dc_014 ✅

**输入**：需要一个 3.3V 转 1.8V、0.6A 的降压芯片，温度 -40°C 到 85°C，优先国产。  
**耗时**：2ms  

**解析约束**：

| 字段 | 值 |
|------|-----|
| category | dc_dc_converter |
| topology | buck |
| input_voltage_nominal_v | 3.3 |
| output_voltage_v | 1.8 |
| output_current_a | 0.6 |
| temperature_min_c | -40 |
| temperature_max_c | 85 |
| preferences | domestic_alternative |

**候选评分明细**（共 7 个）：

| # | 型号 | 厂商 | 国产 | 车规 | 总分 | 参数 | 供应 | 成本 | 国产 | 证据 | 推荐等级 |
|---|------|------|------|------|------|------|------|------|------|------|----------|
| 1 | TPS62044DGQ | Texas Instruments Incorporated | 🌍 | - | **90** | 100 | 50 | 0 | 0 | 0 | ⭐ recommended |
| 2 | TPS62044DGQR | Texas Instruments Incorporated | 🌍 | - | **90** | 100 | 50 | 0 | 0 | 0 | ⭐ recommended |
| 3 | TPS62044DRCR | Texas Instruments Incorporated | 🌍 | - | **90** | 100 | 50 | 0 | 0 | 0 | ⭐ recommended |
| 4 | TPS62061DSGR | Texas Instruments Incorporated | 🌍 | - | **90** | 100 | 50 | 0 | 0 | 0 | ⭐ recommended |
| 5 | TPS62061DSGT | Texas Instruments Incorporated | 🌍 | - | **90** | 100 | 50 | 0 | 0 | 0 | ⭐ recommended |
| 6 | TPS62054DGS | Texas Instruments Incorporated | 🌍 | - | **83** | 92 | 50 | 0 | 0 | 0 | 🟡 backup |
| 7 | TPS62054DGSR | Texas Instruments Incorporated | 🌍 | - | **83** | 92 | 50 | 0 | 0 | 0 | 🟡 backup |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（2.5–6.0V 含标称 3.3V）
- 输出电压匹配 ✓（1.8V = 需求 1.8V）
- 输出电流满足 ✓（1.2A，余量 100%）
- 温度范围覆盖 ✓（-40.0–85.0°C）
- 有数据手册

**证据链**（共 28 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| TPS62044DGQ | `ezplm_api` | 输入电压范围 2.5–6.0V | 95% |  |
| TPS62044DGQ | `ezplm_api` | 最大输出电流 1.2A | 90% |  |
| TPS62044DGQ | `ezplm_api` | 工作温度范围 -40.0–85.0°C | 95% |  |
| TPS62044DGQ | `datasheet` | TPS62044DGQ 数据手册可查，规格参数可进一步核实 | 95% |  |
| TPS62044DGQR | `ezplm_api` | 输入电压范围 2.5–6.0V | 95% |  |
| TPS62044DGQR | `ezplm_api` | 最大输出电流 1.2A | 90% |  |
| TPS62044DGQR | `ezplm_api` | 工作温度范围 -40.0–85.0°C | 95% |  |
| TPS62044DGQR | `datasheet` | TPS62044DGQR 数据手册可查，规格参数可进一步核实 | 95% |  |
| TPS62044DRCR | `ezplm_api` | 输入电压范围 2.5–6.0V | 95% |  |
| TPS62044DRCR | `ezplm_api` | 最大输出电流 1.2A | 90% |  |
| ... | ... | _(共 28 条，仅展示前 10 条)_ | ... | ... |

**风险评估**：⚪ medium

- ⚪ **medium** — 推荐器件全部来自同一制造商（Texas Instruments Incorporated），存在供应商集中风险。 _(缓解: 建议引入第二供应商，降低单一来源依赖。)_
- ⚪ **medium** — 用户偏好国产替代，但当前推荐器件均为进口，国产化目标未达成。 _(缓解: 扩充国产器件库，或联系国产厂商获取样品评估。)_
- ⚪ **medium** — 全部 7 条候选器件的生命周期状态未知，无法评估停产/断供风险。 _(缓解: 从制造商官网或授权分销商处确认各器件当前生命周期状态（Active/NRND/EOL）。)_
- ⚪ **medium** — 全部候选器件的当前库存信息缺失，无法评估现货供应能力与交期。 _(缓解: 通过 eZ-PLM API 或分销商接口获取实时库存数据。)_
- ⚪ **low** — 全部候选器件的封装信息缺失，PCB Layout 评估缺少依据。 _(缓解: 从数据手册或制造商网站获取封装代码与推荐焊盘图纸。)_
- ⚪ **medium** — 推荐器件全部来自境外单一供应商 Texas Instruments Incorporated，存在贸易管制/关税变动的地缘政治风险。 _(缓解: 纳入至少 1 家国产兼容型号作为第二供应源，或评估非美国来源替代方案。)_

---

### 15. dc_dc_015 ✅

**输入**：12V 转 5V、1.2A 降压，室温使用，要求成本最低。  
**耗时**：2ms  

**解析约束**：

| 字段 | 值 |
|------|-----|
| category | dc_dc_converter |
| topology | buck |
| input_voltage_nominal_v | 12.0 |
| output_voltage_v | 5.0 |
| output_current_a | 1.2 |

**候选评分明细**（共 8 个）：

| # | 型号 | 厂商 | 国产 | 车规 | 总分 | 参数 | 供应 | 成本 | 国产 | 证据 | 推荐等级 |
|---|------|------|------|------|------|------|------|------|------|------|----------|
| 1 | LM2576HVT-5.0/LF03 | Texas Instruments Incorporated | 🌍 | - | **90** | 100 | 50 | 0 | 0 | 0 | ⭐ recommended |
| 2 | LM2576S-5.0/NOPB | Texas Instruments Incorporated | 🌍 | - | **90** | 100 | 50 | 0 | 0 | 0 | ⭐ recommended |
| 3 | LM2576SX-5.0/NOPB | Texas Instruments Incorporated | 🌍 | - | **90** | 100 | 50 | 0 | 0 | 0 | ⭐ recommended |
| 4 | LM2576T-5.0/LF02 | Texas Instruments Incorporated | 🌍 | - | **90** | 100 | 50 | 0 | 0 | 0 | ⭐ recommended |
| 5 | TPS54200DDCR | Texas Instruments Incorporated | 🌍 | - | **75** | 81 | 50 | 0 | 0 | 0 | ⭐ recommended |
| 6 | TPS54200DDCT | Texas Instruments Incorporated | 🌍 | - | **75** | 81 | 50 | 0 | 0 | 0 | 🟡 backup |
| 7 | TPS54201DDCR | Texas Instruments Incorporated | 🌍 | - | **75** | 81 | 50 | 0 | 0 | 0 | 🟡 backup |
| 8 | TPS54201DDCT | Texas Instruments Incorporated | 🌍 | - | **75** | 81 | 50 | 0 | 0 | 0 | 🟡 backup |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（4.0–60.0V 含标称 12.0V）
- 输出电压匹配 ✓（5.0V = 需求 5.0V）
- 输出电流满足 ✓（3.0A，余量 150%）
- 有数据手册
- 同类变体：LM2576HVT-5.0/NOPB

**证据链**（共 32 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| LM2576HVT-5.0/LF03 | `ezplm_api` | 输入电压范围 4.0–60.0V | 95% |  |
| LM2576HVT-5.0/LF03 | `ezplm_api` | 最大输出电流 3.0A | 90% |  |
| LM2576HVT-5.0/LF03 | `ezplm_api` | 工作温度范围 -40.0–125.0°C | 95% |  |
| LM2576HVT-5.0/LF03 | `datasheet` | LM2576HVT-5.0/LF03 数据手册可查，规格参数可进一步核实 | 95% |  |
| LM2576S-5.0/NOPB | `ezplm_api` | 输入电压范围 4.0–40.0V | 95% |  |
| LM2576S-5.0/NOPB | `ezplm_api` | 最大输出电流 3.0A | 90% |  |
| LM2576S-5.0/NOPB | `ezplm_api` | 工作温度范围 -40.0–125.0°C | 95% |  |
| LM2576S-5.0/NOPB | `datasheet` | LM2576S-5.0/NOPB 数据手册可查，规格参数可进一步核实 | 95% |  |
| LM2576SX-5.0/NOPB | `ezplm_api` | 输入电压范围 4.0–40.0V | 95% |  |
| LM2576SX-5.0/NOPB | `ezplm_api` | 最大输出电流 3.0A | 90% |  |
| ... | ... | _(共 32 条，仅展示前 10 条)_ | ... | ... |

**风险评估**：⚪ medium

- ⚪ **medium** — 推荐器件全部来自同一制造商（Texas Instruments Incorporated），存在供应商集中风险。 _(缓解: 建议引入第二供应商，降低单一来源依赖。)_
- ⚪ **medium** — 全部 8 条候选器件的生命周期状态未知，无法评估停产/断供风险。 _(缓解: 从制造商官网或授权分销商处确认各器件当前生命周期状态（Active/NRND/EOL）。)_
- ⚪ **medium** — 全部候选器件的当前库存信息缺失，无法评估现货供应能力与交期。 _(缓解: 通过 eZ-PLM API 或分销商接口获取实时库存数据。)_
- ⚪ **low** — 全部候选器件的封装信息缺失，PCB Layout 评估缺少依据。 _(缓解: 从数据手册或制造商网站获取封装代码与推荐焊盘图纸。)_
- ⚪ **medium** — 推荐器件全部来自境外单一供应商 Texas Instruments Incorporated，存在贸易管制/关税变动的地缘政治风险。 _(缓解: 纳入至少 1 家国产兼容型号作为第二供应源，或评估非美国来源替代方案。)_

---

### 16. dc_dc_016 ✅

**输入**：需要 24V 转 5V、4A 的车规级 AEC-Q100 降压，-40°C 到 125°C，优先国产替代方案。  
**耗时**：2ms  

**解析约束**：

| 字段 | 值 |
|------|-----|
| category | dc_dc_converter |
| topology | buck |
| grade | automotive |
| input_voltage_nominal_v | 24.0 |
| output_voltage_v | 5.0 |
| output_current_a | 4.0 |
| temperature_min_c | -40 |
| temperature_max_c | 125 |
| preferences | domestic_alternative |

**风险评估**：⚪ high

- ⚪ **high** — 检索无结果，请确认类别/拓扑约束或扩充数据源。 _(缓解: 检查 EZ-PLM API 白名单覆盖情况，或补充 mock 数据。)_

---

### 17. dc_dc_017 ❌

**输入**：48V 转 5V、3A 工业级电源方案，工作温度 -40°C 到 85°C，库存优先。  
**耗时**：2ms  

**解析失败项**：
- ❌ preference 'low_supply_risk' missing (got [])

**解析约束**：

| 字段 | 值 |
|------|-----|
| category | dc_dc_converter |
| topology | buck |
| input_voltage_nominal_v | 48.0 |
| output_voltage_v | 5.0 |
| output_current_a | 3.0 |
| temperature_min_c | -40 |
| temperature_max_c | 85 |

**候选评分明细**（共 1 个）：

| # | 型号 | 厂商 | 国产 | 车规 | 总分 | 参数 | 供应 | 成本 | 国产 | 证据 | 推荐等级 |
|---|------|------|------|------|------|------|------|------|------|------|----------|
| 1 | LM2576HVT-5.0/LF03 | Texas Instruments Incorporated | 🌍 | - | **80** | 88 | 50 | 0 | 0 | 0 | ⭐ recommended |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（4.0–60.0V 含标称 48.0V）
- 输出电压匹配 ✓（5.0V = 需求 5.0V）
- 输出电流满足 ✓（3.0A，余量 0%）
- 温度范围覆盖 ✓（-40.0–125.0°C）
- 有数据手册
- 同类变体：LM2576HVT-5.0/NOPB

**证据链**（共 4 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| LM2576HVT-5.0/LF03 | `ezplm_api` | 输入电压范围 4.0–60.0V | 95% |  |
| LM2576HVT-5.0/LF03 | `ezplm_api` | 最大输出电流 3.0A | 90% |  |
| LM2576HVT-5.0/LF03 | `ezplm_api` | 工作温度范围 -40.0–125.0°C | 95% |  |
| LM2576HVT-5.0/LF03 | `datasheet` | LM2576HVT-5.0/LF03 数据手册可查，规格参数可进一步核实 | 95% |  |

**风险评估**：⚪ medium

- ⚪ **medium** — 仅 1 款推荐器件（LM2576HVT-5.0/LF03），备选方案不足。 _(缓解: 纳入 backup 级器件作为冗余，或向供应商确认长期备货计划。)_
- ⚪ **medium** — 全部 1 条候选器件的生命周期状态未知，无法评估停产/断供风险。 _(缓解: 从制造商官网或授权分销商处确认各器件当前生命周期状态（Active/NRND/EOL）。)_
- ⚪ **medium** — 全部候选器件的当前库存信息缺失，无法评估现货供应能力与交期。 _(缓解: 通过 eZ-PLM API 或分销商接口获取实时库存数据。)_
- ⚪ **low** — 全部候选器件的封装信息缺失，PCB Layout 评估缺少依据。 _(缓解: 从数据手册或制造商网站获取封装代码与推荐焊盘图纸。)_

---

### 18. dc_dc_018 ✅

**输入**：请找一个 12V 转 3.3V、1.5A 的降压，温度 -40°C 到 85°C，SOT-23 封装优先，必须国产。  
**耗时**：2ms  

**解析约束**：

| 字段 | 值 |
|------|-----|
| category | dc_dc_converter |
| topology | buck |
| input_voltage_nominal_v | 12.0 |
| output_voltage_v | 3.3 |
| output_current_a | 1.5 |
| temperature_min_c | -40 |
| temperature_max_c | 85 |
| preferences | domestic_alternative |
| must_have | domestic, package:SOT-23 |

**候选评分明细**（共 8 个）：

| # | 型号 | 厂商 | 国产 | 车规 | 总分 | 参数 | 供应 | 成本 | 国产 | 证据 | 推荐等级 |
|---|------|------|------|------|------|------|------|------|------|------|----------|
| 1 | LM2576HVT-ADJ/LF03 | Texas Instruments Incorporated | 🌍 | - | **90** | 100 | 50 | 0 | 0 | 0 | ⭐ recommended |
| 2 | LM2576S-3.3/NOPB | Texas Instruments Incorporated | 🌍 | - | **90** | 100 | 50 | 0 | 0 | 0 | ⭐ recommended |
| 3 | LM2576SX-3.3/NOPB | Texas Instruments Incorporated | 🌍 | - | **90** | 100 | 50 | 0 | 0 | 0 | ⭐ recommended |
| 4 | LM2576T-3.3/LF03 | Texas Instruments Incorporated | 🌍 | - | **90** | 100 | 50 | 0 | 0 | 0 | ⭐ recommended |
| 5 | TPS54200DDCR | Texas Instruments Incorporated | 🌍 | - | **77** | 83 | 50 | 0 | 0 | 0 | ⭐ recommended |
| 6 | TPS54200DDCT | Texas Instruments Incorporated | 🌍 | - | **77** | 83 | 50 | 0 | 0 | 0 | 🟡 backup |
| 7 | TPS54201DDCR | Texas Instruments Incorporated | 🌍 | - | **77** | 83 | 50 | 0 | 0 | 0 | 🟡 backup |
| 8 | TPS54201DDCT | Texas Instruments Incorporated | 🌍 | - | **77** | 83 | 50 | 0 | 0 | 0 | 🟡 backup |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（4.0–60.0V 含标称 12.0V）
- 输出电压匹配 ✓（3.3V = 需求 3.3V）
- 输出电流满足 ✓（3.0A，余量 100%）
- 温度范围覆盖 ✓（-40.0–125.0°C）
- 有数据手册
- 同类变体：LM2576HVT-ADJ/NOPB

**证据链**（共 32 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| LM2576HVT-ADJ/LF03 | `ezplm_api` | 输入电压范围 4.0–60.0V | 95% |  |
| LM2576HVT-ADJ/LF03 | `ezplm_api` | 最大输出电流 3.0A | 90% |  |
| LM2576HVT-ADJ/LF03 | `ezplm_api` | 工作温度范围 -40.0–125.0°C | 95% |  |
| LM2576HVT-ADJ/LF03 | `datasheet` | LM2576HVT-ADJ/LF03 数据手册可查，规格参数可进一步核实 | 95% |  |
| LM2576S-3.3/NOPB | `ezplm_api` | 输入电压范围 4.0–40.0V | 95% |  |
| LM2576S-3.3/NOPB | `ezplm_api` | 最大输出电流 3.0A | 90% |  |
| LM2576S-3.3/NOPB | `ezplm_api` | 工作温度范围 -40.0–125.0°C | 95% |  |
| LM2576S-3.3/NOPB | `datasheet` | LM2576S-3.3/NOPB 数据手册可查，规格参数可进一步核实 | 95% |  |
| LM2576SX-3.3/NOPB | `ezplm_api` | 输入电压范围 4.0–40.0V | 95% |  |
| LM2576SX-3.3/NOPB | `ezplm_api` | 最大输出电流 3.0A | 90% |  |
| ... | ... | _(共 32 条，仅展示前 10 条)_ | ... | ... |

**风险评估**：⚪ medium

- ⚪ **medium** — 推荐器件全部来自同一制造商（Texas Instruments Incorporated），存在供应商集中风险。 _(缓解: 建议引入第二供应商，降低单一来源依赖。)_
- ⚪ **medium** — 用户偏好国产替代，但当前推荐器件均为进口，国产化目标未达成。 _(缓解: 扩充国产器件库，或联系国产厂商获取样品评估。)_
- ⚪ **medium** — 全部 8 条候选器件的生命周期状态未知，无法评估停产/断供风险。 _(缓解: 从制造商官网或授权分销商处确认各器件当前生命周期状态（Active/NRND/EOL）。)_
- ⚪ **medium** — 全部候选器件的当前库存信息缺失，无法评估现货供应能力与交期。 _(缓解: 通过 eZ-PLM API 或分销商接口获取实时库存数据。)_
- ⚪ **low** — 全部候选器件的封装信息缺失，PCB Layout 评估缺少依据。 _(缓解: 从数据手册或制造商网站获取封装代码与推荐焊盘图纸。)_
- ⚪ **medium** — 推荐器件全部来自境外单一供应商 Texas Instruments Incorporated，存在贸易管制/关税变动的地缘政治风险。 _(缓解: 纳入至少 1 家国产兼容型号作为第二供应源，或评估非美国来源替代方案。)_

---

### 19. dc_dc_019 ✅

**输入**：需要一个 5V 转 1.2V、0.3A 的低压降压芯片，温度 -40°C 到 85°C，用于消费电子。  
**耗时**：2ms  

**解析约束**：

| 字段 | 值 |
|------|-----|
| category | dc_dc_converter |
| topology | buck |
| input_voltage_nominal_v | 5.0 |
| output_voltage_v | 1.2 |
| output_current_a | 0.3 |
| temperature_min_c | -40 |
| temperature_max_c | 85 |

**候选评分明细**（共 14 个）：

| # | 型号 | 厂商 | 国产 | 车规 | 总分 | 参数 | 供应 | 成本 | 国产 | 证据 | 推荐等级 |
|---|------|------|------|------|------|------|------|------|------|------|----------|
| 1 | TPS54200DDCR | Texas Instruments Incorporated | 🌍 | - | **90** | 100 | 50 | 0 | 0 | 0 | ⭐ recommended |
| 2 | TPS54200DDCT | Texas Instruments Incorporated | 🌍 | - | **90** | 100 | 50 | 0 | 0 | 0 | ⭐ recommended |
| 3 | TPS54201DDCR | Texas Instruments Incorporated | 🌍 | - | **90** | 100 | 50 | 0 | 0 | 0 | ⭐ recommended |
| 4 | TPS54201DDCT | Texas Instruments Incorporated | 🌍 | - | **90** | 100 | 50 | 0 | 0 | 0 | ⭐ recommended |
| 5 | TPS79501DCQ | Texas Instruments Incorporated | 🌍 | - | **87** | 96 | 50 | 0 | 0 | 0 | ⭐ recommended |
| 6 | TPS79501DCQR | Texas Instruments Incorporated | 🌍 | - | **87** | 96 | 50 | 0 | 0 | 0 | 🟡 backup |
| 7 | TPS79501DRBT | Texas Instruments Incorporated | 🌍 | - | **87** | 96 | 50 | 0 | 0 | 0 | 🟡 backup |
| 8 | TPS79501QDRBRQ1 | Texas Instruments Incorporated | 🌍 | - | **87** | 96 | 50 | 0 | 0 | 0 | 🟡 backup |
| 9 | TPS79516DCQ | Texas Instruments Incorporated | 🌍 | - | **87** | 96 | 50 | 0 | 0 | 0 | 🟡 backup |
| 10 | TPS79516DCQR | Texas Instruments Incorporated | 🌍 | - | **87** | 96 | 50 | 0 | 0 | 0 | 🟡 backup |
| 11 | TPS79518DCQ | Texas Instruments Incorporated | 🌍 | - | **87** | 96 | 50 | 0 | 0 | 0 | 🟡 backup |
| 12 | TPS79518DCQR | Texas Instruments Incorporated | 🌍 | - | **87** | 96 | 50 | 0 | 0 | 0 | 🟡 backup |
| 13 | TPS79525DCQR | Texas Instruments Incorporated | 🌍 | - | **87** | 96 | 50 | 0 | 0 | 0 | 🟡 backup |
| 14 | TPS79530DCQR | Texas Instruments Incorporated | 🌍 | - | **87** | 96 | 50 | 0 | 0 | 0 | 🟡 backup |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（4.5–28.0V 含标称 5.0V）
- 输出电流满足 ✓（1.5A，余量 400%）
- 温度范围覆盖 ✓（-40.0–85.0°C）
- 有数据手册

**证据链**（共 56 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| TPS54200DDCR | `ezplm_api` | 输入电压范围 4.5–28.0V | 95% |  |
| TPS54200DDCR | `ezplm_api` | 最大输出电流 1.5A | 90% |  |
| TPS54200DDCR | `ezplm_api` | 工作温度范围 -40.0–85.0°C | 95% |  |
| TPS54200DDCR | `datasheet` | TPS54200DDCR 数据手册可查，规格参数可进一步核实 | 95% |  |
| TPS54200DDCT | `ezplm_api` | 输入电压范围 4.5–28.0V | 95% |  |
| TPS54200DDCT | `ezplm_api` | 最大输出电流 1.5A | 90% |  |
| TPS54200DDCT | `ezplm_api` | 工作温度范围 -40.0–85.0°C | 95% |  |
| TPS54200DDCT | `datasheet` | TPS54200DDCT 数据手册可查，规格参数可进一步核实 | 95% |  |
| TPS54201DDCR | `ezplm_api` | 输入电压范围 4.5–28.0V | 95% |  |
| TPS54201DDCR | `ezplm_api` | 最大输出电流 1.5A | 90% |  |
| ... | ... | _(共 56 条，仅展示前 10 条)_ | ... | ... |

**风险评估**：⚪ medium

- ⚪ **medium** — 推荐器件全部来自同一制造商（Texas Instruments Incorporated），存在供应商集中风险。 _(缓解: 建议引入第二供应商，降低单一来源依赖。)_
- ⚪ **medium** — 全部 14 条候选器件的生命周期状态未知，无法评估停产/断供风险。 _(缓解: 从制造商官网或授权分销商处确认各器件当前生命周期状态（Active/NRND/EOL）。)_
- ⚪ **medium** — 全部候选器件的当前库存信息缺失，无法评估现货供应能力与交期。 _(缓解: 通过 eZ-PLM API 或分销商接口获取实时库存数据。)_
- ⚪ **low** — 全部候选器件的封装信息缺失，PCB Layout 评估缺少依据。 _(缓解: 从数据手册或制造商网站获取封装代码与推荐焊盘图纸。)_
- ⚪ **medium** — 推荐器件全部来自境外单一供应商 Texas Instruments Incorporated，存在贸易管制/关税变动的地缘政治风险。 _(缓解: 纳入至少 1 家国产兼容型号作为第二供应源，或评估非美国来源替代方案。)_

---

### 20. dc_dc_020 ✅

**输入**：30V 输入，输出 12V、6A 的车规级 DC-DC，工作温度 -40°C 到 125°C，优先国产方案和低供应风险。  
**耗时**：2ms  

**解析约束**：

| 字段 | 值 |
|------|-----|
| category | dc_dc_converter |
| topology | buck |
| grade | automotive |
| input_voltage_nominal_v | 12.0 |
| output_voltage_v | 12.0 |
| output_current_a | 6.0 |
| temperature_min_c | -40 |
| temperature_max_c | 125 |
| preferences | domestic_alternative, low_supply_risk |

**风险评估**：⚪ high

- ⚪ **high** — 检索无结果，请确认类别/拓扑约束或扩充数据源。 _(缓解: 检查 EZ-PLM API 白名单覆盖情况，或补充 mock 数据。)_

---


*报告由 `tests/eval_runner.py` 自动生成，IR version: 0.1*
