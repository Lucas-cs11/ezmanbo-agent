# eZ-PLM Component Risk Agent — 评测报告

**生成时间**：2026-05-29 15:54:13  
**用例总数**：20  
**通过**：18 ✅  |  **失败**：2 ❌  
**通过率**：90.0%  
**评测模式**：纯规则模式，无 LLM 依赖  

---

## 📊 总览

| 用例 ID | 输入摘要 | 解析通过 | 推荐数 | 风险等级 | 耗时(ms) |
|---------|----------|----------|--------|----------|----------|
| dc_dc_001 | 我需要一个 12V 转 5V、3A 的车规级降压芯片，工作温度 -40°C 到 ... | ✅ | 5 | ⚪ high | 16744ms |
| dc_dc_002 | 需要 24V 转 12V、2A 的降压方案，工作温度 -40°C 到 85°C。 | ✅ | 5 | ⚪ medium | 57ms |
| dc_dc_003 | 我需要 12V 转 5V、4A 的降压芯片，非车规，室温使用。 | ✅ | 1 | ⚪ medium | 70ms |
| dc_dc_004 | 12V转5V，3A，温度范围 -20C 到 85C，优先低供应链风险。 | ✅ | 5 | ⚪ low | 38ms |
| dc_dc_005 | 请给我一个 5V 到 3.3V 的降压芯片，输出 1A。 | ✅ | 5 | ⚪ medium | 65ms |
| dc_dc_006 | 需要 48V 转 12V、1.5A 的降压模块，用于工业温度 -40°C 到 8... | ✅ | 5 | ⚪ medium | 50ms |
| dc_dc_007 | 找一个 9V 转 5V、2A 的降压，温度 0°C 到 70°C，非车规。 | ✅ | 5 | ⚪ low | 18ms |
| dc_dc_008 | 需要 12V 到 5V、3A 的车规级降压（automotive）。 | ✅ | 5 | ⚪ high | 62ms |
| dc_dc_009 | 5V转3.3V，输出 0.5A，优先低供应链风险。 | ✅ | 5 | ⚪ medium | 67ms |
| dc_dc_010 | 输入 24V，输出 5V，电流 10A，高功率场景。 | ✅ | 0 | ⚪ high | 83ms |
| dc_dc_011 | 找一个 18V 转 5V、6A 的车规级降压芯片，工作温度 -40°C 到 12... | ✅ | 0 | ⚪ high | 70ms |
| dc_dc_012 | 需要 28V 转 12V、2A 的降压芯片，工业温度 -40°C 到 105°C... | ✅ | 5 | ⚪ medium | 66ms |
| dc_dc_013 | 36V 输入，输出 5V、8A，大功率 DC-DC，希望库存充足。 | ❌ | 0 | ⚪ high | 45ms |
| dc_dc_014 | 需要一个 3.3V 转 1.8V、0.6A 的降压芯片，温度 -40°C 到 8... | ✅ | 5 | ⚪ medium | 84ms |
| dc_dc_015 | 12V 转 5V、1.2A 降压，室温使用，要求成本最低。 | ✅ | 5 | ⚪ low | 53ms |
| dc_dc_016 | 需要 24V 转 5V、4A 的车规级 AEC-Q100 降压，-40°C 到 ... | ✅ | 1 | ⚪ high | 66ms |
| dc_dc_017 | 48V 转 5V、3A 工业级电源方案，工作温度 -40°C 到 85°C，库存... | ❌ | 5 | ⚪ medium | 54ms |
| dc_dc_018 | 请找一个 12V 转 3.3V、1.5A 的降压，温度 -40°C 到 85°C... | ✅ | 5 | ⚪ medium | 39ms |
| dc_dc_019 | 需要一个 5V 转 1.2V、0.3A 的低压降压芯片，温度 -40°C 到 8... | ✅ | 5 | ⚪ medium | 15ms |
| dc_dc_020 | 30V 输入，输出 12V、6A 的车规级 DC-DC，工作温度 -40°C 到... | ✅ | 0 | ⚪ high | 46ms |

---

## 📋 逐用例详情

### 1. dc_dc_001 ✅

**输入**：我需要一个 12V 转 5V、3A 的车规级降压芯片，工作温度 -40°C 到 125°C，优先国产替代。  
**耗时**：16744ms  

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

**候选评分明细**（共 15 个）：

| # | 型号 | 厂商 | 国产 | 车规 | 总分 | 参数 | 供应 | 成本 | 国产 | 证据 | 推荐等级 |
|---|------|------|------|------|------|------|------|------|------|------|----------|
| 1 | MOCK-BUCK-005 | MockPower | 🇨🇳 | - | **93** | 92 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 2 | TPS1100D | Texas Instruments Incorporated | 🌍 | - | **87** | 83 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 3 | TPS1100DR | Texas Instruments Incorporated | 🌍 | - | **87** | 83 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 4 | TPS1100PWR | Texas Instruments Incorporated | 🌍 | - | **87** | 83 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 5 | TPS1101D | Texas Instruments Incorporated | 🌍 | - | **87** | 83 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 6 | TPS1101DR | Texas Instruments Incorporated | 🌍 | - | **87** | 83 | 100 | 0 | 0 | 0 | 🟡 backup |
| 7 | TPS1101PWR | Texas Instruments Incorporated | 🌍 | - | **87** | 83 | 100 | 0 | 0 | 0 | 🟡 backup |
| 8 | TPS1120D | Texas Instruments Incorporated | 🌍 | - | **87** | 83 | 100 | 0 | 0 | 0 | 🟡 backup |
| 9 | TPS1120DR | Texas Instruments Incorporated | 🌍 | - | **87** | 83 | 100 | 0 | 0 | 0 | 🟡 backup |
| 10 | TPS12110AQDGXRQ1 | Texas Instruments Incorporated | 🌍 | - | **87** | 83 | 100 | 0 | 0 | 0 | 🟡 backup |
| 11 | TPS12111LQDGXRQ1 | Texas Instruments Incorporated | 🌍 | - | **87** | 83 | 100 | 0 | 0 | 0 | 🟡 backup |
| 12 | TPS12112AQDGXRQ1 | Texas Instruments Incorporated | 🌍 | - | **87** | 83 | 100 | 0 | 0 | 0 | 🟡 backup |
| 13 | TPS16410DRCR | Texas Instruments Incorporated | 🌍 | - | **87** | 83 | 100 | 0 | 0 | 0 | 🟡 backup |
| 14 | TPS16411DRCR | Texas Instruments Incorporated | 🌍 | - | **87** | 83 | 100 | 0 | 0 | 0 | 🟡 backup |
| 15 | TPS16412DRCR | Texas Instruments Incorporated | 🌍 | - | **87** | 83 | 100 | 0 | 0 | 0 | 🟡 backup |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（7.0–40.0V 含标称 12.0V）
- 输出电压匹配 ✓（5.0V = 需求 5.0V）
- 输出电流满足 ✓（4.0A，余量 33%）
- 温度范围覆盖 ✓（-40.0–125.0°C）
- 库存充足（4000 件）
- 生命周期：在产
- 有数据手册

**证据链**（共 122 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| MOCK-BUCK-005 | `mock_data` | 输入电压范围 7.0–40.0V | 95% |  |
| MOCK-BUCK-005 | `mock_data` | 最大输出电流 4.0A | 90% |  |
| MOCK-BUCK-005 | `mock_data` | 工作温度范围 -40.0–125.0°C | 95% |  |
| MOCK-BUCK-005 | `mock_data` | 当前库存 4000 件 | 90% |  |
| MOCK-BUCK-005 | `mock_data` | 生命周期状态：active | 95% |  |
| MOCK-BUCK-005 | `automotive_cert` | MOCK-BUCK-005 未标注车规认证，但需求要求车规等级，需人工确认是否可用 | 30% | ⚠️ |
| MOCK-BUCK-005 | `domestic_origin` | MOCK-BUCK-005 为国产器件（MockPower），满足国产化替代需求 | 90% |  |
| MOCK-BUCK-005 | `mock_data` | 参考单价 ¥6.0（人民币，仅供参考） | 80% |  |
| MOCK-BUCK-005 | `datasheet` | MOCK-BUCK-005 数据手册可查，规格参数可进一步核实 | 95% |  |
| TPS1100D | `mock_data` | 输入电压范围 5.0–36.0V | 95% |  |
| ... | ... | _(共 122 条，仅展示前 10 条)_ | ... | ... |

**风险评估**：⚪ high

- ⚪ **high** — 需求要求车规等级，但所有推荐器件均非车规认证，不可直接用于车载产品。 _(缓解: 重新筛选 AEC-Q100 认证器件，或向制造商确认车规版本。)_

---

### 2. dc_dc_002 ✅

**输入**：需要 24V 转 12V、2A 的降压方案，工作温度 -40°C 到 85°C。  
**耗时**：57ms  

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

**候选评分明细**（共 15 个）：

| # | 型号 | 厂商 | 国产 | 车规 | 总分 | 参数 | 供应 | 成本 | 国产 | 证据 | 推荐等级 |
|---|------|------|------|------|------|------|------|------|------|------|----------|
| 1 | TPS1100D | Texas Instruments Incorporated | 🌍 | - | **93** | 92 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 2 | TPS1100DR | Texas Instruments Incorporated | 🌍 | - | **93** | 92 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 3 | TPS1100PWR | Texas Instruments Incorporated | 🌍 | - | **93** | 92 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 4 | TPS1101D | Texas Instruments Incorporated | 🌍 | - | **93** | 92 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 5 | TPS1101DR | Texas Instruments Incorporated | 🌍 | - | **93** | 92 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 6 | TPS1101PWR | Texas Instruments Incorporated | 🌍 | - | **93** | 92 | 100 | 0 | 0 | 0 | 🟡 backup |
| 7 | TPS1120D | Texas Instruments Incorporated | 🌍 | - | **93** | 92 | 100 | 0 | 0 | 0 | 🟡 backup |
| 8 | TPS1120DR | Texas Instruments Incorporated | 🌍 | - | **93** | 92 | 100 | 0 | 0 | 0 | 🟡 backup |
| 9 | TPS12110AQDGXRQ1 | Texas Instruments Incorporated | 🌍 | - | **93** | 92 | 100 | 0 | 0 | 0 | 🟡 backup |
| 10 | TPS12111LQDGXRQ1 | Texas Instruments Incorporated | 🌍 | - | **93** | 92 | 100 | 0 | 0 | 0 | 🟡 backup |
| 11 | TPS12112AQDGXRQ1 | Texas Instruments Incorporated | 🌍 | - | **93** | 92 | 100 | 0 | 0 | 0 | 🟡 backup |
| 12 | TPS16410DRCR | Texas Instruments Incorporated | 🌍 | - | **93** | 92 | 100 | 0 | 0 | 0 | 🟡 backup |
| 13 | TPS16411DRCR | Texas Instruments Incorporated | 🌍 | - | **93** | 92 | 100 | 0 | 0 | 0 | 🟡 backup |
| 14 | TPS16412DRCR | Texas Instruments Incorporated | 🌍 | - | **93** | 92 | 100 | 0 | 0 | 0 | 🟡 backup |
| 15 | TPS16413DRCR | Texas Instruments Incorporated | 🌍 | - | **93** | 92 | 100 | 0 | 0 | 0 | 🟡 backup |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（5.0–36.0V 含标称 24.0V）
- 输出电流满足 ✓（3.0A，余量 50%）
- 温度范围覆盖 ✓（-40.0–125.0°C）
- 库存充足（5000 件）
- 生命周期：在产
- 有数据手册

**证据链**（共 106 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| TPS1100D | `mock_data` | 输入电压范围 5.0–36.0V | 95% |  |
| TPS1100D | `mock_data` | 最大输出电流 3.0A | 90% |  |
| TPS1100D | `mock_data` | 工作温度范围 -40.0–125.0°C | 95% |  |
| TPS1100D | `mock_data` | 当前库存 5000 件 | 90% |  |
| TPS1100D | `mock_data` | 生命周期状态：active | 95% |  |
| TPS1100D | `mock_data` | 参考单价 ¥5.0（人民币，仅供参考） | 80% |  |
| TPS1100D | `datasheet` | TPS1100D 数据手册可查，规格参数可进一步核实 | 95% |  |
| TPS1100DR | `mock_data` | 输入电压范围 5.0–36.0V | 95% |  |
| TPS1100DR | `mock_data` | 最大输出电流 3.0A | 90% |  |
| TPS1100DR | `mock_data` | 工作温度范围 -40.0–125.0°C | 95% |  |
| ... | ... | _(共 106 条，仅展示前 10 条)_ | ... | ... |

**风险评估**：⚪ medium

- ⚪ **medium** — 推荐器件全部来自同一制造商（Texas Instruments Incorporated），存在供应商集中风险。 _(缓解: 建议引入第二供应商，降低单一来源依赖。)_
- ⚪ **medium** — 推荐器件全部来自境外单一供应商 Texas Instruments Incorporated，存在贸易管制/关税变动的地缘政治风险。 _(缓解: 纳入至少 1 家国产兼容型号作为第二供应源，或评估非美国来源替代方案。)_

---

### 3. dc_dc_003 ✅

**输入**：我需要 12V 转 5V、4A 的降压芯片，非车规，室温使用。  
**耗时**：70ms  

**解析约束**：

| 字段 | 值 |
|------|-----|
| category | dc_dc_converter |
| topology | buck |
| grade | industrial |
| input_voltage_nominal_v | 12.0 |
| output_voltage_v | 5.0 |
| output_current_a | 4.0 |

**候选评分明细**（共 1 个）：

| # | 型号 | 厂商 | 国产 | 车规 | 总分 | 参数 | 供应 | 成本 | 国产 | 证据 | 推荐等级 |
|---|------|------|------|------|------|------|------|------|------|------|----------|
| 1 | MOCK-BUCK-005 | MockPower | 🇨🇳 | - | **87** | 83 | 100 | 0 | 0 | 0 | ⭐ recommended |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（7.0–40.0V 含标称 12.0V）
- 输出电压匹配 ✓（5.0V = 需求 5.0V）
- 输出电流满足 ✓（4.0A，余量 0%）
- 库存充足（4000 件）
- 生命周期：在产
- 有数据手册

**证据链**（共 9 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| MOCK-BUCK-005 | `mock_data` | 输入电压范围 7.0–40.0V | 95% |  |
| MOCK-BUCK-005 | `mock_data` | 最大输出电流 4.0A | 90% |  |
| MOCK-BUCK-005 | `mock_data` | 工作温度范围 -40.0–125.0°C | 95% |  |
| MOCK-BUCK-005 | `mock_data` | 当前库存 4000 件 | 90% |  |
| MOCK-BUCK-005 | `mock_data` | 生命周期状态：active | 95% |  |
| MOCK-BUCK-005 | `domestic_origin` | MOCK-BUCK-005 为国产器件（MockPower），满足国产化替代需求 | 90% |  |
| MOCK-BUCK-005 | `mock_data` | 参考单价 ¥6.0（人民币，仅供参考） | 80% |  |
| MOCK-BUCK-005 | `datasheet` | MOCK-BUCK-005 数据手册可查，规格参数可进一步核实 | 95% |  |
| None | `rag_knowledge` | 已从工程知识库检索到 5 条相关参考知识，用于增强选型决策。 | 84% |  |

**风险评估**：⚪ medium

- ⚪ **medium** — 仅 1 款推荐器件（MOCK-BUCK-005），备选方案不足。 _(缓解: 纳入 backup 级器件作为冗余，或向供应商确认长期备货计划。)_

---

### 4. dc_dc_004 ✅

**输入**：12V转5V，3A，温度范围 -20C 到 85C，优先低供应链风险。  
**耗时**：38ms  

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

**候选评分明细**（共 15 个）：

| # | 型号 | 厂商 | 国产 | 车规 | 总分 | 参数 | 供应 | 成本 | 国产 | 证据 | 推荐等级 |
|---|------|------|------|------|------|------|------|------|------|------|----------|
| 1 | MOCK-BUCK-005 | MockPower | 🇨🇳 | - | **93** | 92 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 2 | TPS1100D | Texas Instruments Incorporated | 🌍 | - | **87** | 83 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 3 | TPS1100DR | Texas Instruments Incorporated | 🌍 | - | **87** | 83 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 4 | TPS1100PWR | Texas Instruments Incorporated | 🌍 | - | **87** | 83 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 5 | TPS1101D | Texas Instruments Incorporated | 🌍 | - | **87** | 83 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 6 | TPS1101DR | Texas Instruments Incorporated | 🌍 | - | **87** | 83 | 100 | 0 | 0 | 0 | 🟡 backup |
| 7 | TPS1101PWR | Texas Instruments Incorporated | 🌍 | - | **87** | 83 | 100 | 0 | 0 | 0 | 🟡 backup |
| 8 | TPS1120D | Texas Instruments Incorporated | 🌍 | - | **87** | 83 | 100 | 0 | 0 | 0 | 🟡 backup |
| 9 | TPS1120DR | Texas Instruments Incorporated | 🌍 | - | **87** | 83 | 100 | 0 | 0 | 0 | 🟡 backup |
| 10 | TPS12110AQDGXRQ1 | Texas Instruments Incorporated | 🌍 | - | **87** | 83 | 100 | 0 | 0 | 0 | 🟡 backup |
| 11 | TPS12111LQDGXRQ1 | Texas Instruments Incorporated | 🌍 | - | **87** | 83 | 100 | 0 | 0 | 0 | 🟡 backup |
| 12 | TPS12112AQDGXRQ1 | Texas Instruments Incorporated | 🌍 | - | **87** | 83 | 100 | 0 | 0 | 0 | 🟡 backup |
| 13 | TPS16410DRCR | Texas Instruments Incorporated | 🌍 | - | **87** | 83 | 100 | 0 | 0 | 0 | 🟡 backup |
| 14 | TPS16411DRCR | Texas Instruments Incorporated | 🌍 | - | **87** | 83 | 100 | 0 | 0 | 0 | 🟡 backup |
| 15 | TPS16412DRCR | Texas Instruments Incorporated | 🌍 | - | **87** | 83 | 100 | 0 | 0 | 0 | 🟡 backup |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（7.0–40.0V 含标称 12.0V）
- 输出电压匹配 ✓（5.0V = 需求 5.0V）
- 输出电流满足 ✓（4.0A，余量 33%）
- 温度范围覆盖 ✓（-40.0–125.0°C）
- 库存充足（4000 件）
- 生命周期：在产
- 有数据手册

**证据链**（共 107 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| MOCK-BUCK-005 | `mock_data` | 输入电压范围 7.0–40.0V | 95% |  |
| MOCK-BUCK-005 | `mock_data` | 最大输出电流 4.0A | 90% |  |
| MOCK-BUCK-005 | `mock_data` | 工作温度范围 -40.0–125.0°C | 95% |  |
| MOCK-BUCK-005 | `mock_data` | 当前库存 4000 件 | 90% |  |
| MOCK-BUCK-005 | `mock_data` | 生命周期状态：active | 95% |  |
| MOCK-BUCK-005 | `domestic_origin` | MOCK-BUCK-005 为国产器件（MockPower），满足国产化替代需求 | 90% |  |
| MOCK-BUCK-005 | `mock_data` | 参考单价 ¥6.0（人民币，仅供参考） | 80% |  |
| MOCK-BUCK-005 | `datasheet` | MOCK-BUCK-005 数据手册可查，规格参数可进一步核实 | 95% |  |
| TPS1100D | `mock_data` | 输入电压范围 5.0–36.0V | 95% |  |
| TPS1100D | `mock_data` | 最大输出电流 3.0A | 90% |  |
| ... | ... | _(共 107 条，仅展示前 10 条)_ | ... | ... |

**风险评估**：⚪ low


---

### 5. dc_dc_005 ✅

**输入**：请给我一个 5V 到 3.3V 的降压芯片，输出 1A。  
**耗时**：65ms  

**解析约束**：

| 字段 | 值 |
|------|-----|
| category | dc_dc_converter |
| topology | buck |
| input_voltage_nominal_v | 5.0 |
| output_voltage_v | 3.3 |
| output_current_a | 1.0 |

**候选评分明细**（共 15 个）：

| # | 型号 | 厂商 | 国产 | 车规 | 总分 | 参数 | 供应 | 成本 | 国产 | 证据 | 推荐等级 |
|---|------|------|------|------|------|------|------|------|------|------|----------|
| 1 | TPS1100D | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 2 | TPS1100DR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 3 | TPS1100PWR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 4 | TPS1101D | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 5 | TPS1101DR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 6 | TPS1101PWR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 7 | TPS1120D | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 8 | TPS1120DR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 9 | TPS12110AQDGXRQ1 | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 10 | TPS12111LQDGXRQ1 | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 11 | TPS12112AQDGXRQ1 | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 12 | TPS16410DRCR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 13 | TPS16411DRCR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 14 | TPS16412DRCR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 15 | TPS16413DRCR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（5.0–36.0V 含标称 5.0V）
- 输出电流满足 ✓（3.0A，余量 200%）
- 库存充足（5000 件）
- 生命周期：在产
- 有数据手册

**证据链**（共 106 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| TPS1100D | `mock_data` | 输入电压范围 5.0–36.0V | 95% |  |
| TPS1100D | `mock_data` | 最大输出电流 3.0A | 90% |  |
| TPS1100D | `mock_data` | 工作温度范围 -40.0–125.0°C | 95% |  |
| TPS1100D | `mock_data` | 当前库存 5000 件 | 90% |  |
| TPS1100D | `mock_data` | 生命周期状态：active | 95% |  |
| TPS1100D | `mock_data` | 参考单价 ¥5.0（人民币，仅供参考） | 80% |  |
| TPS1100D | `datasheet` | TPS1100D 数据手册可查，规格参数可进一步核实 | 95% |  |
| TPS1100DR | `mock_data` | 输入电压范围 5.0–36.0V | 95% |  |
| TPS1100DR | `mock_data` | 最大输出电流 3.0A | 90% |  |
| TPS1100DR | `mock_data` | 工作温度范围 -40.0–125.0°C | 95% |  |
| ... | ... | _(共 106 条，仅展示前 10 条)_ | ... | ... |

**风险评估**：⚪ medium

- ⚪ **medium** — 推荐器件全部来自同一制造商（Texas Instruments Incorporated），存在供应商集中风险。 _(缓解: 建议引入第二供应商，降低单一来源依赖。)_
- ⚪ **medium** — 推荐器件全部来自境外单一供应商 Texas Instruments Incorporated，存在贸易管制/关税变动的地缘政治风险。 _(缓解: 纳入至少 1 家国产兼容型号作为第二供应源，或评估非美国来源替代方案。)_

---

### 6. dc_dc_006 ✅

**输入**：需要 48V 转 12V、1.5A 的降压模块，用于工业温度 -40°C 到 85°C，优先国产。  
**耗时**：50ms  

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

**候选评分明细**（共 13 个）：

| # | 型号 | 厂商 | 国产 | 车规 | 总分 | 参数 | 供应 | 成本 | 国产 | 证据 | 推荐等级 |
|---|------|------|------|------|------|------|------|------|------|------|----------|
| 1 | TPS16530PWPR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 2 | TPS16530RGER | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 3 | TPS16630PWPR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 4 | TPS16630PWPT | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 5 | TPS16630RGER | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 6 | TPS16630RGET | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 7 | TPS16632RGER | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 8 | TPS16632RGET | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 9 | TPS16637PWPR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 10 | TPS16637RGER | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 11 | LM317HVH | Texas Instruments Incorporated | 🌍 | - | **87** | 83 | 100 | 0 | 0 | 0 | 🟡 backup |
| 12 | LM317HVK STEEL | Texas Instruments Incorporated | 🌍 | - | **87** | 83 | 100 | 0 | 0 | 0 | 🟡 backup |
| 13 | LM317HVT/NOPB | Texas Instruments Incorporated | 🌍 | - | **87** | 83 | 100 | 0 | 0 | 0 | 🟡 backup |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（4.5–58.0V 含标称 48.0V）
- 输出电流满足 ✓（3.0A，余量 100%）
- 温度范围覆盖 ✓（-40.0–125.0°C）
- 库存充足（5000 件）
- 生命周期：在产
- 有数据手册

**证据链**（共 92 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| TPS16530PWPR | `mock_data` | 输入电压范围 4.5–58.0V | 95% |  |
| TPS16530PWPR | `mock_data` | 最大输出电流 3.0A | 90% |  |
| TPS16530PWPR | `mock_data` | 工作温度范围 -40.0–125.0°C | 95% |  |
| TPS16530PWPR | `mock_data` | 当前库存 5000 件 | 90% |  |
| TPS16530PWPR | `mock_data` | 生命周期状态：active | 95% |  |
| TPS16530PWPR | `mock_data` | 参考单价 ¥5.0（人民币，仅供参考） | 80% |  |
| TPS16530PWPR | `datasheet` | TPS16530PWPR 数据手册可查，规格参数可进一步核实 | 95% |  |
| TPS16530RGER | `mock_data` | 输入电压范围 4.5–58.0V | 95% |  |
| TPS16530RGER | `mock_data` | 最大输出电流 3.0A | 90% |  |
| TPS16530RGER | `mock_data` | 工作温度范围 -40.0–125.0°C | 95% |  |
| ... | ... | _(共 92 条，仅展示前 10 条)_ | ... | ... |

**风险评估**：⚪ medium

- ⚪ **medium** — 推荐器件全部来自同一制造商（Texas Instruments Incorporated），存在供应商集中风险。 _(缓解: 建议引入第二供应商，降低单一来源依赖。)_
- ⚪ **medium** — 用户偏好国产替代，但当前推荐器件均为进口，国产化目标未达成。 _(缓解: 扩充国产器件库，或联系国产厂商获取样品评估。)_
- ⚪ **medium** — 推荐器件全部来自境外单一供应商 Texas Instruments Incorporated，存在贸易管制/关税变动的地缘政治风险。 _(缓解: 纳入至少 1 家国产兼容型号作为第二供应源，或评估非美国来源替代方案。)_

---

### 7. dc_dc_007 ✅

**输入**：找一个 9V 转 5V、2A 的降压，温度 0°C 到 70°C，非车规。  
**耗时**：18ms  

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

**候选评分明细**（共 15 个）：

| # | 型号 | 厂商 | 国产 | 车规 | 总分 | 参数 | 供应 | 成本 | 国产 | 证据 | 推荐等级 |
|---|------|------|------|------|------|------|------|------|------|------|----------|
| 1 | MOCK-BUCK-005 | MockPower | 🇨🇳 | - | **100** | 100 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 2 | TPS1100D | Texas Instruments Incorporated | 🌍 | - | **93** | 92 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 3 | TPS1100DR | Texas Instruments Incorporated | 🌍 | - | **93** | 92 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 4 | TPS1100PWR | Texas Instruments Incorporated | 🌍 | - | **93** | 92 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 5 | TPS1101D | Texas Instruments Incorporated | 🌍 | - | **93** | 92 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 6 | TPS1101DR | Texas Instruments Incorporated | 🌍 | - | **93** | 92 | 100 | 0 | 0 | 0 | 🟡 backup |
| 7 | TPS1101PWR | Texas Instruments Incorporated | 🌍 | - | **93** | 92 | 100 | 0 | 0 | 0 | 🟡 backup |
| 8 | TPS1120D | Texas Instruments Incorporated | 🌍 | - | **93** | 92 | 100 | 0 | 0 | 0 | 🟡 backup |
| 9 | TPS1120DR | Texas Instruments Incorporated | 🌍 | - | **93** | 92 | 100 | 0 | 0 | 0 | 🟡 backup |
| 10 | TPS12110AQDGXRQ1 | Texas Instruments Incorporated | 🌍 | - | **93** | 92 | 100 | 0 | 0 | 0 | 🟡 backup |
| 11 | TPS12111LQDGXRQ1 | Texas Instruments Incorporated | 🌍 | - | **93** | 92 | 100 | 0 | 0 | 0 | 🟡 backup |
| 12 | TPS12112AQDGXRQ1 | Texas Instruments Incorporated | 🌍 | - | **93** | 92 | 100 | 0 | 0 | 0 | 🟡 backup |
| 13 | TPS16410DRCR | Texas Instruments Incorporated | 🌍 | - | **93** | 92 | 100 | 0 | 0 | 0 | 🟡 backup |
| 14 | TPS16411DRCR | Texas Instruments Incorporated | 🌍 | - | **93** | 92 | 100 | 0 | 0 | 0 | 🟡 backup |
| 15 | TPS16412DRCR | Texas Instruments Incorporated | 🌍 | - | **93** | 92 | 100 | 0 | 0 | 0 | 🟡 backup |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（7.0–40.0V 含标称 9.0V）
- 输出电压匹配 ✓（5.0V = 需求 5.0V）
- 输出电流满足 ✓（4.0A，余量 100%）
- 温度范围覆盖 ✓（-40.0–125.0°C）
- 库存充足（4000 件）
- 生命周期：在产
- 有数据手册

**证据链**（共 107 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| MOCK-BUCK-005 | `mock_data` | 输入电压范围 7.0–40.0V | 95% |  |
| MOCK-BUCK-005 | `mock_data` | 最大输出电流 4.0A | 90% |  |
| MOCK-BUCK-005 | `mock_data` | 工作温度范围 -40.0–125.0°C | 95% |  |
| MOCK-BUCK-005 | `mock_data` | 当前库存 4000 件 | 90% |  |
| MOCK-BUCK-005 | `mock_data` | 生命周期状态：active | 95% |  |
| MOCK-BUCK-005 | `domestic_origin` | MOCK-BUCK-005 为国产器件（MockPower），满足国产化替代需求 | 90% |  |
| MOCK-BUCK-005 | `mock_data` | 参考单价 ¥6.0（人民币，仅供参考） | 80% |  |
| MOCK-BUCK-005 | `datasheet` | MOCK-BUCK-005 数据手册可查，规格参数可进一步核实 | 95% |  |
| TPS1100D | `mock_data` | 输入电压范围 5.0–36.0V | 95% |  |
| TPS1100D | `mock_data` | 最大输出电流 3.0A | 90% |  |
| ... | ... | _(共 107 条，仅展示前 10 条)_ | ... | ... |

**风险评估**：⚪ low


---

### 8. dc_dc_008 ✅

**输入**：需要 12V 到 5V、3A 的车规级降压（automotive）。  
**耗时**：62ms  

**解析约束**：

| 字段 | 值 |
|------|-----|
| category | dc_dc_converter |
| topology | buck |
| grade | automotive |
| input_voltage_nominal_v | 12.0 |
| output_voltage_v | 5.0 |
| output_current_a | 3.0 |

**候选评分明细**（共 15 个）：

| # | 型号 | 厂商 | 国产 | 车规 | 总分 | 参数 | 供应 | 成本 | 国产 | 证据 | 推荐等级 |
|---|------|------|------|------|------|------|------|------|------|------|----------|
| 1 | MOCK-BUCK-005 | MockPower | 🇨🇳 | - | **91** | 89 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 2 | TPS1100D | Texas Instruments Incorporated | 🌍 | - | **80** | 75 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 3 | TPS1100DR | Texas Instruments Incorporated | 🌍 | - | **80** | 75 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 4 | TPS1100PWR | Texas Instruments Incorporated | 🌍 | - | **80** | 75 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 5 | TPS1101D | Texas Instruments Incorporated | 🌍 | - | **80** | 75 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 6 | TPS1101DR | Texas Instruments Incorporated | 🌍 | - | **80** | 75 | 100 | 0 | 0 | 0 | 🟡 backup |
| 7 | TPS1101PWR | Texas Instruments Incorporated | 🌍 | - | **80** | 75 | 100 | 0 | 0 | 0 | 🟡 backup |
| 8 | TPS1120D | Texas Instruments Incorporated | 🌍 | - | **80** | 75 | 100 | 0 | 0 | 0 | 🟡 backup |
| 9 | TPS1120DR | Texas Instruments Incorporated | 🌍 | - | **80** | 75 | 100 | 0 | 0 | 0 | 🟡 backup |
| 10 | TPS12110AQDGXRQ1 | Texas Instruments Incorporated | 🌍 | - | **80** | 75 | 100 | 0 | 0 | 0 | 🟡 backup |
| 11 | TPS12111LQDGXRQ1 | Texas Instruments Incorporated | 🌍 | - | **80** | 75 | 100 | 0 | 0 | 0 | 🟡 backup |
| 12 | TPS12112AQDGXRQ1 | Texas Instruments Incorporated | 🌍 | - | **80** | 75 | 100 | 0 | 0 | 0 | 🟡 backup |
| 13 | TPS16410DRCR | Texas Instruments Incorporated | 🌍 | - | **80** | 75 | 100 | 0 | 0 | 0 | 🟡 backup |
| 14 | TPS16411DRCR | Texas Instruments Incorporated | 🌍 | - | **80** | 75 | 100 | 0 | 0 | 0 | 🟡 backup |
| 15 | TPS16412DRCR | Texas Instruments Incorporated | 🌍 | - | **80** | 75 | 100 | 0 | 0 | 0 | 🟡 backup |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（7.0–40.0V 含标称 12.0V）
- 输出电压匹配 ✓（5.0V = 需求 5.0V）
- 输出电流满足 ✓（4.0A，余量 33%）
- 库存充足（4000 件）
- 生命周期：在产
- 有数据手册

**证据链**（共 122 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| MOCK-BUCK-005 | `mock_data` | 输入电压范围 7.0–40.0V | 95% |  |
| MOCK-BUCK-005 | `mock_data` | 最大输出电流 4.0A | 90% |  |
| MOCK-BUCK-005 | `mock_data` | 工作温度范围 -40.0–125.0°C | 95% |  |
| MOCK-BUCK-005 | `mock_data` | 当前库存 4000 件 | 90% |  |
| MOCK-BUCK-005 | `mock_data` | 生命周期状态：active | 95% |  |
| MOCK-BUCK-005 | `automotive_cert` | MOCK-BUCK-005 未标注车规认证，但需求要求车规等级，需人工确认是否可用 | 30% | ⚠️ |
| MOCK-BUCK-005 | `domestic_origin` | MOCK-BUCK-005 为国产器件（MockPower），满足国产化替代需求 | 90% |  |
| MOCK-BUCK-005 | `mock_data` | 参考单价 ¥6.0（人民币，仅供参考） | 80% |  |
| MOCK-BUCK-005 | `datasheet` | MOCK-BUCK-005 数据手册可查，规格参数可进一步核实 | 95% |  |
| TPS1100D | `mock_data` | 输入电压范围 5.0–36.0V | 95% |  |
| ... | ... | _(共 122 条，仅展示前 10 条)_ | ... | ... |

**风险评估**：⚪ high

- ⚪ **high** — 需求要求车规等级，但所有推荐器件均非车规认证，不可直接用于车载产品。 _(缓解: 重新筛选 AEC-Q100 认证器件，或向制造商确认车规版本。)_

---

### 9. dc_dc_009 ✅

**输入**：5V转3.3V，输出 0.5A，优先低供应链风险。  
**耗时**：67ms  

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
| 1 | TPS1100D | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 2 | TPS1100DR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 3 | TPS1100PWR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 4 | TPS1101D | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 5 | TPS1101DR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 6 | TPS1101PWR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 7 | TPS1120D | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 8 | TPS1120DR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 9 | TPS12110AQDGXRQ1 | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 10 | TPS12111LQDGXRQ1 | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 11 | TPS12112AQDGXRQ1 | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 12 | TPS16410DRCR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 13 | TPS16411DRCR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 14 | TPS16412DRCR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 15 | TPS16413DRCR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（5.0–36.0V 含标称 5.0V）
- 输出电流满足 ✓（3.0A，余量 500%）
- 库存充足（5000 件）
- 生命周期：在产
- 有数据手册

**证据链**（共 106 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| TPS1100D | `mock_data` | 输入电压范围 5.0–36.0V | 95% |  |
| TPS1100D | `mock_data` | 最大输出电流 3.0A | 90% |  |
| TPS1100D | `mock_data` | 工作温度范围 -40.0–125.0°C | 95% |  |
| TPS1100D | `mock_data` | 当前库存 5000 件 | 90% |  |
| TPS1100D | `mock_data` | 生命周期状态：active | 95% |  |
| TPS1100D | `mock_data` | 参考单价 ¥5.0（人民币，仅供参考） | 80% |  |
| TPS1100D | `datasheet` | TPS1100D 数据手册可查，规格参数可进一步核实 | 95% |  |
| TPS1100DR | `mock_data` | 输入电压范围 5.0–36.0V | 95% |  |
| TPS1100DR | `mock_data` | 最大输出电流 3.0A | 90% |  |
| TPS1100DR | `mock_data` | 工作温度范围 -40.0–125.0°C | 95% |  |
| ... | ... | _(共 106 条，仅展示前 10 条)_ | ... | ... |

**风险评估**：⚪ medium

- ⚪ **medium** — 推荐器件全部来自同一制造商（Texas Instruments Incorporated），存在供应商集中风险。 _(缓解: 建议引入第二供应商，降低单一来源依赖。)_
- ⚪ **medium** — 推荐器件全部来自境外单一供应商 Texas Instruments Incorporated，存在贸易管制/关税变动的地缘政治风险。 _(缓解: 纳入至少 1 家国产兼容型号作为第二供应源，或评估非美国来源替代方案。)_

---

### 10. dc_dc_010 ✅

**输入**：输入 24V，输出 5V，电流 10A，高功率场景。  
**耗时**：83ms  

**解析约束**：

| 字段 | 值 |
|------|-----|
| category | dc_dc_converter |
| topology | buck |
| input_voltage_nominal_v | 24.0 |
| output_voltage_v | 5.0 |
| output_current_a | 10.0 |

**证据链**（共 1 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| None | `rag_knowledge` | 已从工程知识库检索到 5 条相关参考知识，用于增强选型决策。 | 82% |  |

**风险评估**：⚪ high

- ⚪ **high** — 检索无结果，请确认类别/拓扑约束或扩充数据源。 _(缓解: 检查 EZ-PLM API 白名单覆盖情况，或补充 mock 数据。)_

---

### 11. dc_dc_011 ✅

**输入**：找一个 18V 转 5V、6A 的车规级降压芯片，工作温度 -40°C 到 125°C，必须国产，低供应风险。  
**耗时**：70ms  

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
| must_have | automotive_grade, domestic |

**证据链**（共 1 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| None | `rag_knowledge` | 已从工程知识库检索到 5 条相关参考知识，用于增强选型决策。 | 79% |  |

**风险评估**：⚪ high

- ⚪ **high** — 检索无结果，请确认类别/拓扑约束或扩充数据源。 _(缓解: 检查 EZ-PLM API 白名单覆盖情况，或补充 mock 数据。)_

---

### 12. dc_dc_012 ✅

**输入**：需要 28V 转 12V、2A 的降压芯片，工业温度 -40°C 到 105°C，非车规，必须国产。  
**耗时**：66ms  

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
| must_have | automotive_grade, domestic |

**候选评分明细**（共 15 个）：

| # | 型号 | 厂商 | 国产 | 车规 | 总分 | 参数 | 供应 | 成本 | 国产 | 证据 | 推荐等级 |
|---|------|------|------|------|------|------|------|------|------|------|----------|
| 1 | TPS1100D | Texas Instruments Incorporated | 🌍 | - | **93** | 92 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 2 | TPS1100DR | Texas Instruments Incorporated | 🌍 | - | **93** | 92 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 3 | TPS1100PWR | Texas Instruments Incorporated | 🌍 | - | **93** | 92 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 4 | TPS1101D | Texas Instruments Incorporated | 🌍 | - | **93** | 92 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 5 | TPS1101DR | Texas Instruments Incorporated | 🌍 | - | **93** | 92 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 6 | TPS1101PWR | Texas Instruments Incorporated | 🌍 | - | **93** | 92 | 100 | 0 | 0 | 0 | 🟡 backup |
| 7 | TPS1120D | Texas Instruments Incorporated | 🌍 | - | **93** | 92 | 100 | 0 | 0 | 0 | 🟡 backup |
| 8 | TPS1120DR | Texas Instruments Incorporated | 🌍 | - | **93** | 92 | 100 | 0 | 0 | 0 | 🟡 backup |
| 9 | TPS12110AQDGXRQ1 | Texas Instruments Incorporated | 🌍 | - | **93** | 92 | 100 | 0 | 0 | 0 | 🟡 backup |
| 10 | TPS12111LQDGXRQ1 | Texas Instruments Incorporated | 🌍 | - | **93** | 92 | 100 | 0 | 0 | 0 | 🟡 backup |
| 11 | TPS12112AQDGXRQ1 | Texas Instruments Incorporated | 🌍 | - | **93** | 92 | 100 | 0 | 0 | 0 | 🟡 backup |
| 12 | TPS16410DRCR | Texas Instruments Incorporated | 🌍 | - | **93** | 92 | 100 | 0 | 0 | 0 | 🟡 backup |
| 13 | TPS16411DRCR | Texas Instruments Incorporated | 🌍 | - | **93** | 92 | 100 | 0 | 0 | 0 | 🟡 backup |
| 14 | TPS16412DRCR | Texas Instruments Incorporated | 🌍 | - | **93** | 92 | 100 | 0 | 0 | 0 | 🟡 backup |
| 15 | TPS16413DRCR | Texas Instruments Incorporated | 🌍 | - | **93** | 92 | 100 | 0 | 0 | 0 | 🟡 backup |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（5.0–36.0V 含标称 28.0V）
- 输出电流满足 ✓（3.0A，余量 50%）
- 温度范围覆盖 ✓（-40.0–125.0°C）
- 库存充足（5000 件）
- 生命周期：在产
- 有数据手册

**证据链**（共 106 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| TPS1100D | `mock_data` | 输入电压范围 5.0–36.0V | 95% |  |
| TPS1100D | `mock_data` | 最大输出电流 3.0A | 90% |  |
| TPS1100D | `mock_data` | 工作温度范围 -40.0–125.0°C | 95% |  |
| TPS1100D | `mock_data` | 当前库存 5000 件 | 90% |  |
| TPS1100D | `mock_data` | 生命周期状态：active | 95% |  |
| TPS1100D | `mock_data` | 参考单价 ¥5.0（人民币，仅供参考） | 80% |  |
| TPS1100D | `datasheet` | TPS1100D 数据手册可查，规格参数可进一步核实 | 95% |  |
| TPS1100DR | `mock_data` | 输入电压范围 5.0–36.0V | 95% |  |
| TPS1100DR | `mock_data` | 最大输出电流 3.0A | 90% |  |
| TPS1100DR | `mock_data` | 工作温度范围 -40.0–125.0°C | 95% |  |
| ... | ... | _(共 106 条，仅展示前 10 条)_ | ... | ... |

**风险评估**：⚪ medium

- ⚪ **medium** — 推荐器件全部来自同一制造商（Texas Instruments Incorporated），存在供应商集中风险。 _(缓解: 建议引入第二供应商，降低单一来源依赖。)_
- ⚪ **medium** — 用户偏好国产替代，但当前推荐器件均为进口，国产化目标未达成。 _(缓解: 扩充国产器件库，或联系国产厂商获取样品评估。)_
- ⚪ **medium** — 推荐器件全部来自境外单一供应商 Texas Instruments Incorporated，存在贸易管制/关税变动的地缘政治风险。 _(缓解: 纳入至少 1 家国产兼容型号作为第二供应源，或评估非美国来源替代方案。)_

---

### 13. dc_dc_013 ❌

**输入**：36V 输入，输出 5V、8A，大功率 DC-DC，希望库存充足。  
**耗时**：45ms  

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

**证据链**（共 1 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| None | `rag_knowledge` | 已从工程知识库检索到 5 条相关参考知识，用于增强选型决策。 | 81% |  |

**风险评估**：⚪ high

- ⚪ **high** — 检索无结果，请确认类别/拓扑约束或扩充数据源。 _(缓解: 检查 EZ-PLM API 白名单覆盖情况，或补充 mock 数据。)_

---

### 14. dc_dc_014 ✅

**输入**：需要一个 3.3V 转 1.8V、0.6A 的降压芯片，温度 -40°C 到 85°C，优先国产。  
**耗时**：84ms  

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

**候选评分明细**（共 15 个）：

| # | 型号 | 厂商 | 国产 | 车规 | 总分 | 参数 | 供应 | 成本 | 国产 | 证据 | 推荐等级 |
|---|------|------|------|------|------|------|------|------|------|------|----------|
| 1 | TPS16410DRCR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 2 | TPS16411DRCR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 3 | TPS16412DRCR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 4 | TPS16413DRCR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 5 | TPS16414DRCR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 6 | TPS16415DRCR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 7 | TPS16416DRCR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 8 | TPS16417DRCR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 9 | LM317AEMP/NOPB | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 10 | LM317AEMPX/NOPB | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 11 | LM317AH | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 12 | LM317AMDT/NOPB | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 13 | LM317AMDTX/NOPB | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 14 | LM317AT/NOPB | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 15 | LM317DCY | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（2.7–40.0V 含标称 3.3V）
- 输出电流满足 ✓（3.0A，余量 400%）
- 温度范围覆盖 ✓（-40.0–125.0°C）
- 库存充足（5000 件）
- 生命周期：在产
- 有数据手册

**证据链**（共 106 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| TPS16410DRCR | `mock_data` | 输入电压范围 2.7–40.0V | 95% |  |
| TPS16410DRCR | `mock_data` | 最大输出电流 3.0A | 90% |  |
| TPS16410DRCR | `mock_data` | 工作温度范围 -40.0–125.0°C | 95% |  |
| TPS16410DRCR | `mock_data` | 当前库存 5000 件 | 90% |  |
| TPS16410DRCR | `mock_data` | 生命周期状态：active | 95% |  |
| TPS16410DRCR | `mock_data` | 参考单价 ¥5.0（人民币，仅供参考） | 80% |  |
| TPS16410DRCR | `datasheet` | TPS16410DRCR 数据手册可查，规格参数可进一步核实 | 95% |  |
| TPS16411DRCR | `mock_data` | 输入电压范围 2.7–40.0V | 95% |  |
| TPS16411DRCR | `mock_data` | 最大输出电流 3.0A | 90% |  |
| TPS16411DRCR | `mock_data` | 工作温度范围 -40.0–125.0°C | 95% |  |
| ... | ... | _(共 106 条，仅展示前 10 条)_ | ... | ... |

**风险评估**：⚪ medium

- ⚪ **medium** — 推荐器件全部来自同一制造商（Texas Instruments Incorporated），存在供应商集中风险。 _(缓解: 建议引入第二供应商，降低单一来源依赖。)_
- ⚪ **medium** — 用户偏好国产替代，但当前推荐器件均为进口，国产化目标未达成。 _(缓解: 扩充国产器件库，或联系国产厂商获取样品评估。)_
- ⚪ **medium** — 推荐器件全部来自境外单一供应商 Texas Instruments Incorporated，存在贸易管制/关税变动的地缘政治风险。 _(缓解: 纳入至少 1 家国产兼容型号作为第二供应源，或评估非美国来源替代方案。)_

---

### 15. dc_dc_015 ✅

**输入**：12V 转 5V、1.2A 降压，室温使用，要求成本最低。  
**耗时**：53ms  

**解析约束**：

| 字段 | 值 |
|------|-----|
| category | dc_dc_converter |
| topology | buck |
| input_voltage_nominal_v | 12.0 |
| output_voltage_v | 5.0 |
| output_current_a | 1.2 |

**候选评分明细**（共 15 个）：

| # | 型号 | 厂商 | 国产 | 车规 | 总分 | 参数 | 供应 | 成本 | 国产 | 证据 | 推荐等级 |
|---|------|------|------|------|------|------|------|------|------|------|----------|
| 1 | MOCK-BUCK-005 | MockPower | 🇨🇳 | - | **100** | 100 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 2 | TPS1100D | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 3 | TPS1100DR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 4 | TPS1100PWR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 5 | TPS1101D | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 6 | TPS1101DR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 7 | TPS1101PWR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 8 | TPS1120D | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 9 | TPS1120DR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 10 | TPS12110AQDGXRQ1 | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 11 | TPS12111LQDGXRQ1 | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 12 | TPS12112AQDGXRQ1 | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 13 | TPS16410DRCR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 14 | TPS16411DRCR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 15 | TPS16412DRCR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（7.0–40.0V 含标称 12.0V）
- 输出电压匹配 ✓（5.0V = 需求 5.0V）
- 输出电流满足 ✓（4.0A，余量 233%）
- 库存充足（4000 件）
- 生命周期：在产
- 有数据手册

**证据链**（共 107 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| MOCK-BUCK-005 | `mock_data` | 输入电压范围 7.0–40.0V | 95% |  |
| MOCK-BUCK-005 | `mock_data` | 最大输出电流 4.0A | 90% |  |
| MOCK-BUCK-005 | `mock_data` | 工作温度范围 -40.0–125.0°C | 95% |  |
| MOCK-BUCK-005 | `mock_data` | 当前库存 4000 件 | 90% |  |
| MOCK-BUCK-005 | `mock_data` | 生命周期状态：active | 95% |  |
| MOCK-BUCK-005 | `domestic_origin` | MOCK-BUCK-005 为国产器件（MockPower），满足国产化替代需求 | 90% |  |
| MOCK-BUCK-005 | `mock_data` | 参考单价 ¥6.0（人民币，仅供参考） | 80% |  |
| MOCK-BUCK-005 | `datasheet` | MOCK-BUCK-005 数据手册可查，规格参数可进一步核实 | 95% |  |
| TPS1100D | `mock_data` | 输入电压范围 5.0–36.0V | 95% |  |
| TPS1100D | `mock_data` | 最大输出电流 3.0A | 90% |  |
| ... | ... | _(共 107 条，仅展示前 10 条)_ | ... | ... |

**风险评估**：⚪ low


---

### 16. dc_dc_016 ✅

**输入**：需要 24V 转 5V、4A 的车规级 AEC-Q100 降压，-40°C 到 125°C，优先国产替代方案。  
**耗时**：66ms  

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

**候选评分明细**（共 2 个）：

| # | 型号 | 厂商 | 国产 | 车规 | 总分 | 参数 | 供应 | 成本 | 国产 | 证据 | 推荐等级 |
|---|------|------|------|------|------|------|------|------|------|------|----------|
| 1 | MOCK-BUCK-005 | MockPower | 🇨🇳 | - | **90** | 88 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 2 | IMPORT-BUCK-005 | TechPower | 🌍 | 🚗 | **72** | 88 | 10 | 0 | 0 | 0 | 🟡 backup |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（7.0–40.0V 含标称 24.0V）
- 输出电压匹配 ✓（5.0V = 需求 5.0V）
- 输出电流满足 ✓（4.0A，余量 0%）
- 温度范围覆盖 ✓（-40.0–125.0°C）
- 库存充足（4000 件）
- 生命周期：在产
- 有数据手册

**证据链**（共 18 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| MOCK-BUCK-005 | `mock_data` | 输入电压范围 7.0–40.0V | 95% |  |
| MOCK-BUCK-005 | `mock_data` | 最大输出电流 4.0A | 90% |  |
| MOCK-BUCK-005 | `mock_data` | 工作温度范围 -40.0–125.0°C | 95% |  |
| MOCK-BUCK-005 | `mock_data` | 当前库存 4000 件 | 90% |  |
| MOCK-BUCK-005 | `mock_data` | 生命周期状态：active | 95% |  |
| MOCK-BUCK-005 | `automotive_cert` | MOCK-BUCK-005 未标注车规认证，但需求要求车规等级，需人工确认是否可用 | 30% | ⚠️ |
| MOCK-BUCK-005 | `domestic_origin` | MOCK-BUCK-005 为国产器件（MockPower），满足国产化替代需求 | 90% |  |
| MOCK-BUCK-005 | `mock_data` | 参考单价 ¥6.0（人民币，仅供参考） | 80% |  |
| MOCK-BUCK-005 | `datasheet` | MOCK-BUCK-005 数据手册可查，规格参数可进一步核实 | 95% |  |
| IMPORT-BUCK-005 | `mock_data` | 输入电压范围 20.0–30.0V | 95% |  |
| ... | ... | _(共 18 条，仅展示前 10 条)_ | ... | ... |

**风险评估**：⚪ high

- ⚪ **medium** — 仅 1 款推荐器件（MOCK-BUCK-005），备选方案不足。 _(缓解: 纳入 backup 级器件作为冗余，或向供应商确认长期备货计划。)_
- ⚪ **high** — 需求要求车规等级，但所有推荐器件均非车规认证，不可直接用于车载产品。 _(缓解: 重新筛选 AEC-Q100 认证器件，或向制造商确认车规版本。)_

---

### 17. dc_dc_017 ❌

**输入**：48V 转 5V、3A 工业级电源方案，工作温度 -40°C 到 85°C，库存优先。  
**耗时**：54ms  

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

**候选评分明细**（共 10 个）：

| # | 型号 | 厂商 | 国产 | 车规 | 总分 | 参数 | 供应 | 成本 | 国产 | 证据 | 推荐等级 |
|---|------|------|------|------|------|------|------|------|------|------|----------|
| 1 | TPS16530PWPR | Texas Instruments Incorporated | 🌍 | - | **87** | 83 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 2 | TPS16530RGER | Texas Instruments Incorporated | 🌍 | - | **87** | 83 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 3 | TPS16630PWPR | Texas Instruments Incorporated | 🌍 | - | **87** | 83 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 4 | TPS16630PWPT | Texas Instruments Incorporated | 🌍 | - | **87** | 83 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 5 | TPS16630RGER | Texas Instruments Incorporated | 🌍 | - | **87** | 83 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 6 | TPS16630RGET | Texas Instruments Incorporated | 🌍 | - | **87** | 83 | 100 | 0 | 0 | 0 | 🟡 backup |
| 7 | TPS16632RGER | Texas Instruments Incorporated | 🌍 | - | **87** | 83 | 100 | 0 | 0 | 0 | 🟡 backup |
| 8 | TPS16632RGET | Texas Instruments Incorporated | 🌍 | - | **87** | 83 | 100 | 0 | 0 | 0 | 🟡 backup |
| 9 | TPS16637PWPR | Texas Instruments Incorporated | 🌍 | - | **87** | 83 | 100 | 0 | 0 | 0 | 🟡 backup |
| 10 | TPS16637RGER | Texas Instruments Incorporated | 🌍 | - | **87** | 83 | 100 | 0 | 0 | 0 | 🟡 backup |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（4.5–58.0V 含标称 48.0V）
- 输出电流满足 ✓（3.0A，余量 0%）
- 温度范围覆盖 ✓（-40.0–125.0°C）
- 库存充足（5000 件）
- 生命周期：在产
- 有数据手册

**证据链**（共 71 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| TPS16530PWPR | `mock_data` | 输入电压范围 4.5–58.0V | 95% |  |
| TPS16530PWPR | `mock_data` | 最大输出电流 3.0A | 90% |  |
| TPS16530PWPR | `mock_data` | 工作温度范围 -40.0–125.0°C | 95% |  |
| TPS16530PWPR | `mock_data` | 当前库存 5000 件 | 90% |  |
| TPS16530PWPR | `mock_data` | 生命周期状态：active | 95% |  |
| TPS16530PWPR | `mock_data` | 参考单价 ¥5.0（人民币，仅供参考） | 80% |  |
| TPS16530PWPR | `datasheet` | TPS16530PWPR 数据手册可查，规格参数可进一步核实 | 95% |  |
| TPS16530RGER | `mock_data` | 输入电压范围 4.5–58.0V | 95% |  |
| TPS16530RGER | `mock_data` | 最大输出电流 3.0A | 90% |  |
| TPS16530RGER | `mock_data` | 工作温度范围 -40.0–125.0°C | 95% |  |
| ... | ... | _(共 71 条，仅展示前 10 条)_ | ... | ... |

**风险评估**：⚪ medium

- ⚪ **medium** — 推荐器件全部来自同一制造商（Texas Instruments Incorporated），存在供应商集中风险。 _(缓解: 建议引入第二供应商，降低单一来源依赖。)_
- ⚪ **medium** — 推荐器件全部来自境外单一供应商 Texas Instruments Incorporated，存在贸易管制/关税变动的地缘政治风险。 _(缓解: 纳入至少 1 家国产兼容型号作为第二供应源，或评估非美国来源替代方案。)_

---

### 18. dc_dc_018 ✅

**输入**：请找一个 12V 转 3.3V、1.5A 的降压，温度 -40°C 到 85°C，SOT-23 封装优先，必须国产。  
**耗时**：39ms  

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

**候选评分明细**（共 15 个）：

| # | 型号 | 厂商 | 国产 | 车规 | 总分 | 参数 | 供应 | 成本 | 国产 | 证据 | 推荐等级 |
|---|------|------|------|------|------|------|------|------|------|------|----------|
| 1 | TPS1100D | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 2 | TPS1100DR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 3 | TPS1100PWR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 4 | TPS1101D | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 5 | TPS1101DR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 6 | TPS1101PWR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 7 | TPS1120D | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 8 | TPS1120DR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 9 | TPS12110AQDGXRQ1 | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 10 | TPS12111LQDGXRQ1 | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 11 | TPS12112AQDGXRQ1 | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 12 | TPS16410DRCR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 13 | TPS16411DRCR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 14 | TPS16412DRCR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 15 | TPS16413DRCR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（5.0–36.0V 含标称 12.0V）
- 输出电流满足 ✓（3.0A，余量 100%）
- 温度范围覆盖 ✓（-40.0–125.0°C）
- 库存充足（5000 件）
- 生命周期：在产
- 有数据手册

**证据链**（共 106 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| TPS1100D | `mock_data` | 输入电压范围 5.0–36.0V | 95% |  |
| TPS1100D | `mock_data` | 最大输出电流 3.0A | 90% |  |
| TPS1100D | `mock_data` | 工作温度范围 -40.0–125.0°C | 95% |  |
| TPS1100D | `mock_data` | 当前库存 5000 件 | 90% |  |
| TPS1100D | `mock_data` | 生命周期状态：active | 95% |  |
| TPS1100D | `mock_data` | 参考单价 ¥5.0（人民币，仅供参考） | 80% |  |
| TPS1100D | `datasheet` | TPS1100D 数据手册可查，规格参数可进一步核实 | 95% |  |
| TPS1100DR | `mock_data` | 输入电压范围 5.0–36.0V | 95% |  |
| TPS1100DR | `mock_data` | 最大输出电流 3.0A | 90% |  |
| TPS1100DR | `mock_data` | 工作温度范围 -40.0–125.0°C | 95% |  |
| ... | ... | _(共 106 条，仅展示前 10 条)_ | ... | ... |

**风险评估**：⚪ medium

- ⚪ **medium** — 推荐器件全部来自同一制造商（Texas Instruments Incorporated），存在供应商集中风险。 _(缓解: 建议引入第二供应商，降低单一来源依赖。)_
- ⚪ **medium** — 用户偏好国产替代，但当前推荐器件均为进口，国产化目标未达成。 _(缓解: 扩充国产器件库，或联系国产厂商获取样品评估。)_
- ⚪ **medium** — 推荐器件全部来自境外单一供应商 Texas Instruments Incorporated，存在贸易管制/关税变动的地缘政治风险。 _(缓解: 纳入至少 1 家国产兼容型号作为第二供应源，或评估非美国来源替代方案。)_

---

### 19. dc_dc_019 ✅

**输入**：需要一个 5V 转 1.2V、0.3A 的低压降压芯片，温度 -40°C 到 85°C，用于消费电子。  
**耗时**：15ms  

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

**候选评分明细**（共 15 个）：

| # | 型号 | 厂商 | 国产 | 车规 | 总分 | 参数 | 供应 | 成本 | 国产 | 证据 | 推荐等级 |
|---|------|------|------|------|------|------|------|------|------|------|----------|
| 1 | TPS1100D | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 2 | TPS1100DR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 3 | TPS1100PWR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 4 | TPS1101D | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 5 | TPS1101DR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | ⭐ recommended |
| 6 | TPS1101PWR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 7 | TPS1120D | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 8 | TPS1120DR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 9 | TPS12110AQDGXRQ1 | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 10 | TPS12111LQDGXRQ1 | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 11 | TPS12112AQDGXRQ1 | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 12 | TPS16410DRCR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 13 | TPS16411DRCR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 14 | TPS16412DRCR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |
| 15 | TPS16413DRCR | Texas Instruments Incorporated | 🌍 | - | **100** | 100 | 100 | 0 | 0 | 0 | 🟡 backup |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（5.0–36.0V 含标称 5.0V）
- 输出电流满足 ✓（3.0A，余量 900%）
- 温度范围覆盖 ✓（-40.0–125.0°C）
- 库存充足（5000 件）
- 生命周期：在产
- 有数据手册

**证据链**（共 106 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| TPS1100D | `mock_data` | 输入电压范围 5.0–36.0V | 95% |  |
| TPS1100D | `mock_data` | 最大输出电流 3.0A | 90% |  |
| TPS1100D | `mock_data` | 工作温度范围 -40.0–125.0°C | 95% |  |
| TPS1100D | `mock_data` | 当前库存 5000 件 | 90% |  |
| TPS1100D | `mock_data` | 生命周期状态：active | 95% |  |
| TPS1100D | `mock_data` | 参考单价 ¥5.0（人民币，仅供参考） | 80% |  |
| TPS1100D | `datasheet` | TPS1100D 数据手册可查，规格参数可进一步核实 | 95% |  |
| TPS1100DR | `mock_data` | 输入电压范围 5.0–36.0V | 95% |  |
| TPS1100DR | `mock_data` | 最大输出电流 3.0A | 90% |  |
| TPS1100DR | `mock_data` | 工作温度范围 -40.0–125.0°C | 95% |  |
| ... | ... | _(共 106 条，仅展示前 10 条)_ | ... | ... |

**风险评估**：⚪ medium

- ⚪ **medium** — 推荐器件全部来自同一制造商（Texas Instruments Incorporated），存在供应商集中风险。 _(缓解: 建议引入第二供应商，降低单一来源依赖。)_
- ⚪ **medium** — 推荐器件全部来自境外单一供应商 Texas Instruments Incorporated，存在贸易管制/关税变动的地缘政治风险。 _(缓解: 纳入至少 1 家国产兼容型号作为第二供应源，或评估非美国来源替代方案。)_

---

### 20. dc_dc_020 ✅

**输入**：30V 输入，输出 12V、6A 的车规级 DC-DC，工作温度 -40°C 到 125°C，优先国产方案和低供应风险。  
**耗时**：46ms  

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

**证据链**（共 1 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| None | `rag_knowledge` | 已从工程知识库检索到 5 条相关参考知识，用于增强选型决策。 | 83% |  |

**风险评估**：⚪ high

- ⚪ **high** — 检索无结果，请确认类别/拓扑约束或扩充数据源。 _(缓解: 检查 EZ-PLM API 白名单覆盖情况，或补充 mock 数据。)_

---


*报告由 `tests/eval_runner.py` 自动生成，IR version: 0.1*
