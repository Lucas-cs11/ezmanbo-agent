# eZ-PLM Component Risk Agent — 评测报告

**生成时间**：2026-05-28 16:11:25  
**用例总数**：20  
**通过**：18 ✅  |  **失败**：2 ❌  
**通过率**：90.0%  
**评测模式**：纯规则模式，无 LLM 依赖  

---

## 📊 总览

| 用例 ID | 输入摘要 | 解析通过 | 推荐数 | 风险等级 | 耗时(ms) |
|---------|----------|----------|--------|----------|----------|
| dc_dc_001 | 我需要一个 12V 转 5V、3A 的车规级降压芯片，工作温度 -40°C 到 ... | ✅ | 10 | ⚪ medium | 6ms |
| dc_dc_002 | 需要 24V 转 12V、2A 的降压方案，工作温度 -40°C 到 85°C。 | ✅ | 15 | ⚪ medium | 2ms |
| dc_dc_003 | 我需要 12V 转 5V、4A 的降压芯片，非车规，室温使用。 | ✅ | 4 | ⚪ low | 1ms |
| dc_dc_004 | 12V转5V，3A，温度范围 -20C 到 85C，优先低供应链风险。 | ✅ | 11 | ⚪ low | 2ms |
| dc_dc_005 | 请给我一个 5V 到 3.3V 的降压芯片，输出 1A。 | ✅ | 6 | ⚪ low | 1ms |
| dc_dc_006 | 需要 48V 转 12V、1.5A 的降压模块，用于工业温度 -40°C 到 8... | ✅ | 2 | ⚪ low | 1ms |
| dc_dc_007 | 找一个 9V 转 5V、2A 的降压，温度 0°C 到 70°C，非车规。 | ✅ | 7 | ⚪ medium | 1ms |
| dc_dc_008 | 需要 12V 到 5V、3A 的车规级降压（automotive）。 | ✅ | 9 | ⚪ low | 1ms |
| dc_dc_009 | 5V转3.3V，输出 0.5A，优先低供应链风险。 | ✅ | 8 | ⚪ low | 1ms |
| dc_dc_010 | 输入 24V，输出 5V，电流 10A，高功率场景。 | ✅ | 2 | ⚪ low | 1ms |
| dc_dc_011 | 找一个 18V 转 5V、6A 的车规级降压芯片，工作温度 -40°C 到 12... | ✅ | 1 | ⚪ medium | 1ms |
| dc_dc_012 | 需要 28V 转 12V、2A 的降压芯片，工业温度 -40°C 到 105°C... | ✅ | 9 | ⚪ medium | 1ms |
| dc_dc_013 | 36V 输入，输出 5V、8A，大功率 DC-DC，希望库存充足。 | ❌ | 0 | ⚪ high | 1ms |
| dc_dc_014 | 需要一个 3.3V 转 1.8V、0.6A 的降压芯片，温度 -40°C 到 8... | ✅ | 2 | ⚪ low | 1ms |
| dc_dc_015 | 12V 转 5V、1.2A 降压，室温使用，要求成本最低。 | ✅ | 13 | ⚪ low | 2ms |
| dc_dc_016 | 需要 24V 转 5V、4A 的车规级 AEC-Q100 降压，-40°C 到 ... | ✅ | 4 | ⚪ low | 2ms |
| dc_dc_017 | 48V 转 5V、3A 工业级电源方案，工作温度 -40°C 到 85°C，库存... | ❌ | 1 | ⚪ medium | 1ms |
| dc_dc_018 | 请找一个 12V 转 3.3V、1.5A 的降压，温度 -40°C 到 85°C... | ✅ | 14 | ⚪ medium | 2ms |
| dc_dc_019 | 需要一个 5V 转 1.2V、0.3A 的低压降压芯片，温度 -40°C 到 8... | ✅ | 8 | ⚪ low | 1ms |
| dc_dc_020 | 30V 输入，输出 12V、6A 的车规级 DC-DC，工作温度 -40°C 到... | ✅ | 2 | ⚪ low | 1ms |

---

## 📋 逐用例详情

### 1. dc_dc_001 ✅

**输入**：我需要一个 12V 转 5V、3A 的车规级降压芯片，工作温度 -40°C 到 125°C，优先国产替代。  
**耗时**：6ms  

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

**候选评分明细**（共 13 个）：

| # | 型号 | 厂商 | 国产 | 车规 | 总分 | 参数 | 供应 | 成本 | 国产 | 证据 | 推荐等级 |
|---|------|------|------|------|------|------|------|------|------|------|----------|
| 1 | MOCK-BUCK-AEC-001 | MockSemi | 🇨🇳 | 🚗 | **98** | 94 | 100 | 96 | 100 | 100 | ⭐ recommended |
| 2 | MOCK-BUCK-AEC-003 | MockSemi | 🇨🇳 | 🚗 | **98** | 100 | 100 | 79 | 100 | 100 | ⭐ recommended |
| 3 | MOCK-BUCK-015 | NanoPower | 🇨🇳 | 🚗 | **97** | 100 | 100 | 75 | 100 | 100 | ⭐ recommended |
| 4 | MOCK-BUCK-007 | LocalSemi | 🇨🇳 | 🚗 | **97** | 94 | 100 | 86 | 100 | 100 | ⭐ recommended |
| 5 | MOCK-BUCK-006 | LocalSemi | 🇨🇳 | 🚗 | **95** | 84 | 100 | 100 | 100 | 100 | ⭐ recommended |
| 6 | MOCK-BUCK-011 | MiniPower | 🇨🇳 | 🚗 | **95** | 84 | 100 | 95 | 100 | 100 | ⭐ recommended |
| 7 | MOCK-BUCK-004 | MockPower | 🇨🇳 | 🚗 | **94** | 83 | 100 | 93 | 100 | 100 | ⭐ recommended |
| 8 | MOCK-BUCK-009 | MockCore | 🇨🇳 | 🚗 | **93** | 83 | 100 | 81 | 100 | 100 | ⭐ recommended |
| 9 | MOCK-BUCK-022 | DragonIC | 🇨🇳 | 🚗 | **93** | 83 | 100 | 75 | 100 | 100 | ⭐ recommended |
| 10 | MOCK-BUCK-020 | StarPower | 🇨🇳 | 🚗 | **79** | 83 | 40 | 88 | 100 | 100 | ⭐ recommended |
| 11 | IMPORT-BUCK-007 | OverseaChip | 🌍 | 🚗 | **58** | 100 | 70 | 0 | 0 | 100 | 🟡 backup |
| 12 | IMPORT-BUCK-004 | TechPower | 🌍 | 🚗 | **52** | 94 | 40 | 41 | 0 | 100 | 🟡 backup |
| 13 | IMPORT-BUCK-002 | ImportPower | 🌍 | 🚗 | **50** | 83 | 40 | 54 | 0 | 100 | 🟡 backup |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（4.5–36.0V 含标称 12.0V）
- 输出电流满足 ✓（5.0A，余量 67%）
- 温度范围覆盖 ✓（-40.0–125.0°C）
- 库存充足（12000 件）
- 生命周期：在产
- 单价 4.8 元（较低）
- 国产器件 ✓（MockSemi）
- 有数据手册

**证据链**（共 65 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| MOCK-BUCK-AEC-001 | `mock_ezplm_field` | supports temperature range -40.0C to 125.0C | 95% |  |
| MOCK-BUCK-AEC-001 | `mock_ezplm_field` | input voltage range 4.5V to 36.0V | 95% |  |
| MOCK-BUCK-AEC-001 | `mock_ezplm_field` | output current max 5.0A | 90% |  |
| MOCK-BUCK-AEC-001 | `mock_ezplm_field` | stock 12000 | 90% |  |
| MOCK-BUCK-AEC-001 | `mock_ezplm_field` | lifecycle active | 90% |  |
| MOCK-BUCK-AEC-003 | `mock_ezplm_field` | supports temperature range -40.0C to 125.0C | 95% |  |
| MOCK-BUCK-AEC-003 | `mock_ezplm_field` | input voltage range 9.0V to 16.0V | 95% |  |
| MOCK-BUCK-AEC-003 | `mock_ezplm_field` | output current max 6.0A | 90% |  |
| MOCK-BUCK-AEC-003 | `mock_ezplm_field` | stock 3000 | 90% |  |
| MOCK-BUCK-AEC-003 | `mock_ezplm_field` | lifecycle active | 90% |  |
| ... | ... | _(共 65 条，仅展示前 10 条)_ | ... | ... |

**风险评估**：⚪ medium

- ⚪ **medium** — 部分推荐器件库存偏低（MOCK-BUCK-020）。 _(缓解: 关注上述器件库存动态，提前预定。)_

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

**候选评分明细**（共 19 个）：

| # | 型号 | 厂商 | 国产 | 车规 | 总分 | 参数 | 供应 | 成本 | 国产 | 证据 | 推荐等级 |
|---|------|------|------|------|------|------|------|------|------|------|----------|
| 1 | MOCK-BUCK-AEC-001 | MockSemi | 🇨🇳 | 🚗 | **99** | 100 | 100 | 92 | 100 | 100 | ⭐ recommended |
| 2 | MOCK-BUCK-005 | MockPower | 🇨🇳 | - | **98** | 100 | 100 | 87 | 100 | 100 | ⭐ recommended |
| 3 | MOCK-BUCK-007 | LocalSemi | 🇨🇳 | 🚗 | **97** | 100 | 100 | 83 | 100 | 100 | ⭐ recommended |
| 4 | MOCK-BUCK-AEC-002 | MockSemi | 🇨🇳 | - | **96** | 96 | 100 | 85 | 100 | 100 | ⭐ recommended |
| 5 | MOCK-BUCK-011 | MiniPower | 🇨🇳 | 🚗 | **96** | 93 | 100 | 90 | 100 | 100 | ⭐ recommended |
| 6 | MOCK-BUCK-015 | NanoPower | 🇨🇳 | 🚗 | **96** | 100 | 100 | 71 | 100 | 100 | ⭐ recommended |
| 7 | MOCK-BUCK-008 | MockCore | 🇨🇳 | - | **96** | 88 | 100 | 100 | 100 | 100 | ⭐ recommended |
| 8 | MOCK-BUCK-004 | MockPower | 🇨🇳 | 🚗 | **95** | 92 | 100 | 89 | 100 | 100 | ⭐ recommended |
| 9 | MOCK-BUCK-017 | PowerChina | 🇨🇳 | 🚗 | **95** | 100 | 100 | 67 | 100 | 100 | ⭐ recommended |
| 10 | MOCK-BUCK-009 | MockCore | 🇨🇳 | 🚗 | **94** | 92 | 100 | 77 | 100 | 100 | ⭐ recommended |
| 11 | MOCK-BUCK-HP-001 | SinoIC | 🇨🇳 | - | **93** | 100 | 100 | 54 | 100 | 100 | ⭐ recommended |
| 12 | MOCK-BUCK-022 | DragonIC | 🇨🇳 | 🚗 | **93** | 92 | 100 | 72 | 100 | 100 | ⭐ recommended |
| 13 | MOCK-BUCK-019 | SinoIC | 🇨🇳 | - | **92** | 100 | 100 | 46 | 100 | 100 | ⭐ recommended |
| 14 | MOCK-BUCK-HP-002 | PowerChina | 🇨🇳 | - | **91** | 100 | 100 | 40 | 100 | 100 | ⭐ recommended |
| 15 | MOCK-BUCK-020 | StarPower | 🇨🇳 | 🚗 | **80** | 92 | 40 | 84 | 100 | 100 | ⭐ recommended |
| 16 | MOCK-BUCK-013 | MicroSemi | 🌍 | - | **69** | 85 | 70 | 80 | 0 | 100 | 🟡 backup |
| 17 | IMPORT-BUCK-007 | OverseaChip | 🌍 | 🚗 | **62** | 100 | 70 | 0 | 0 | 100 | 🟡 backup |
| 18 | IMPORT-BUCK-004 | TechPower | 🌍 | 🚗 | **61** | 100 | 40 | 40 | 0 | 100 | 🟡 backup |
| 19 | IMPORT-BUCK-005 | TechPower | 🌍 | 🚗 | **51** | 100 | 10 | 24 | 0 | 100 | 🟡 backup |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（4.5–36.0V 含标称 24.0V）
- 输出电流满足 ✓（5.0A，余量 150%）
- 温度范围覆盖 ✓（-40.0–125.0°C）
- 库存充足（12000 件）
- 生命周期：在产
- 单价 4.8 元（较低）
- 国产器件 ✓（MockSemi）
- 有数据手册

**证据链**（共 95 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| MOCK-BUCK-AEC-001 | `mock_ezplm_field` | supports temperature range -40.0C to 125.0C | 95% |  |
| MOCK-BUCK-AEC-001 | `mock_ezplm_field` | input voltage range 4.5V to 36.0V | 95% |  |
| MOCK-BUCK-AEC-001 | `mock_ezplm_field` | output current max 5.0A | 90% |  |
| MOCK-BUCK-AEC-001 | `mock_ezplm_field` | stock 12000 | 90% |  |
| MOCK-BUCK-AEC-001 | `mock_ezplm_field` | lifecycle active | 90% |  |
| MOCK-BUCK-005 | `mock_ezplm_field` | supports temperature range -40.0C to 125.0C | 95% |  |
| MOCK-BUCK-005 | `mock_ezplm_field` | input voltage range 7.0V to 40.0V | 95% |  |
| MOCK-BUCK-005 | `mock_ezplm_field` | output current max 4.0A | 90% |  |
| MOCK-BUCK-005 | `mock_ezplm_field` | stock 4000 | 90% |  |
| MOCK-BUCK-005 | `mock_ezplm_field` | lifecycle active | 90% |  |
| ... | ... | _(共 95 条，仅展示前 10 条)_ | ... | ... |

**风险评估**：⚪ medium

- ⚪ **medium** — 部分推荐器件库存偏低（MOCK-BUCK-020）。 _(缓解: 关注上述器件库存动态，提前预定。)_

---

### 3. dc_dc_003 ✅

**输入**：我需要 12V 转 5V、4A 的降压芯片，非车规，室温使用。  
**耗时**：1ms  

**解析约束**：

| 字段 | 值 |
|------|-----|
| category | dc_dc_converter |
| topology | buck |
| grade | automotive |
| input_voltage_nominal_v | 12.0 |
| output_voltage_v | 5.0 |
| output_current_a | 4.0 |

**候选评分明细**（共 6 个）：

| # | 型号 | 厂商 | 国产 | 车规 | 总分 | 参数 | 供应 | 成本 | 国产 | 证据 | 推荐等级 |
|---|------|------|------|------|------|------|------|------|------|------|----------|
| 1 | MOCK-BUCK-AEC-001 | MockSemi | 🇨🇳 | 🚗 | **84** | 54 | 100 | 100 | 100 | 100 | ⭐ recommended |
| 2 | MOCK-BUCK-AEC-003 | MockSemi | 🇨🇳 | 🚗 | **83** | 58 | 100 | 82 | 100 | 100 | ⭐ recommended |
| 3 | MOCK-BUCK-007 | LocalSemi | 🇨🇳 | 🚗 | **82** | 54 | 100 | 90 | 100 | 100 | ⭐ recommended |
| 4 | MOCK-BUCK-015 | NanoPower | 🇨🇳 | 🚗 | **82** | 58 | 100 | 78 | 100 | 100 | ⭐ recommended |
| 5 | IMPORT-BUCK-007 | OverseaChip | 🌍 | 🚗 | **48** | 58 | 70 | 0 | 0 | 100 | 🔴 not_recommended |
| 6 | IMPORT-BUCK-004 | TechPower | 🌍 | 🚗 | **45** | 54 | 40 | 43 | 0 | 100 | 🔴 not_recommended |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（4.5–36.0V 含标称 12.0V）
- 输出电流满足 ✓（5.0A，余量 25%）
- 库存充足（12000 件）
- 生命周期：在产
- 单价 4.8 元（较低）
- 国产器件 ✓（MockSemi）
- 有数据手册

**证据链**（共 30 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| MOCK-BUCK-AEC-001 | `mock_ezplm_field` | supports temperature range -40.0C to 125.0C | 95% |  |
| MOCK-BUCK-AEC-001 | `mock_ezplm_field` | input voltage range 4.5V to 36.0V | 95% |  |
| MOCK-BUCK-AEC-001 | `mock_ezplm_field` | output current max 5.0A | 90% |  |
| MOCK-BUCK-AEC-001 | `mock_ezplm_field` | stock 12000 | 90% |  |
| MOCK-BUCK-AEC-001 | `mock_ezplm_field` | lifecycle active | 90% |  |
| MOCK-BUCK-AEC-003 | `mock_ezplm_field` | supports temperature range -40.0C to 125.0C | 95% |  |
| MOCK-BUCK-AEC-003 | `mock_ezplm_field` | input voltage range 9.0V to 16.0V | 95% |  |
| MOCK-BUCK-AEC-003 | `mock_ezplm_field` | output current max 6.0A | 90% |  |
| MOCK-BUCK-AEC-003 | `mock_ezplm_field` | stock 3000 | 90% |  |
| MOCK-BUCK-AEC-003 | `mock_ezplm_field` | lifecycle active | 90% |  |
| ... | ... | _(共 30 条，仅展示前 10 条)_ | ... | ... |

**风险评估**：⚪ low


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

**候选评分明细**（共 19 个）：

| # | 型号 | 厂商 | 国产 | 车规 | 总分 | 参数 | 供应 | 成本 | 国产 | 证据 | 推荐等级 |
|---|------|------|------|------|------|------|------|------|------|------|----------|
| 1 | MOCK-BUCK-AEC-003 | MockSemi | 🇨🇳 | 🚗 | **98** | 100 | 100 | 79 | 100 | 100 | ⭐ recommended |
| 2 | MOCK-BUCK-AEC-001 | MockSemi | 🇨🇳 | 🚗 | **98** | 94 | 100 | 96 | 100 | 100 | ⭐ recommended |
| 3 | MOCK-BUCK-015 | NanoPower | 🇨🇳 | 🚗 | **97** | 100 | 100 | 75 | 100 | 100 | ⭐ recommended |
| 4 | MOCK-BUCK-007 | LocalSemi | 🇨🇳 | 🚗 | **97** | 94 | 100 | 86 | 100 | 100 | ⭐ recommended |
| 5 | MOCK-BUCK-005 | MockPower | 🇨🇳 | - | **95** | 89 | 100 | 91 | 100 | 100 | ⭐ recommended |
| 6 | MOCK-BUCK-006 | LocalSemi | 🇨🇳 | 🚗 | **95** | 84 | 100 | 100 | 100 | 100 | ⭐ recommended |
| 7 | MOCK-BUCK-AEC-002 | MockSemi | 🇨🇳 | - | **94** | 86 | 100 | 89 | 100 | 100 | ⭐ recommended |
| 8 | MOCK-BUCK-011 | MiniPower | 🇨🇳 | 🚗 | **94** | 84 | 100 | 95 | 100 | 100 | ⭐ recommended |
| 9 | MOCK-BUCK-004 | MockPower | 🇨🇳 | 🚗 | **94** | 83 | 100 | 93 | 100 | 100 | ⭐ recommended |
| 10 | MOCK-BUCK-009 | MockCore | 🇨🇳 | 🚗 | **92** | 83 | 100 | 81 | 100 | 100 | ⭐ recommended |
| 11 | MOCK-BUCK-022 | DragonIC | 🇨🇳 | 🚗 | **92** | 83 | 100 | 75 | 100 | 100 | ⭐ recommended |
| 12 | MOCK-BUCK-020 | StarPower | 🇨🇳 | 🚗 | **72** | 83 | 40 | 88 | 100 | 100 | 🟡 backup |
| 13 | MOCK-BUCK-012 | MicroSemi | 🌍 | - | **68** | 92 | 70 | 60 | 0 | 100 | 🟡 backup |
| 14 | IMPORT-BUCK-001 | ImportCo | 🌍 | - | **67** | 89 | 70 | 64 | 0 | 100 | 🟡 backup |
| 15 | IMPORT-BUCK-003 | ImportPower | 🌍 | - | **66** | 83 | 70 | 71 | 0 | 100 | 🟡 backup |
| 16 | IMPORT-BUCK-007 | OverseaChip | 🌍 | 🚗 | **64** | 100 | 70 | 0 | 0 | 100 | 🟡 backup |
| 17 | IMPORT-BUCK-004 | TechPower | 🌍 | 🚗 | **56** | 94 | 40 | 41 | 0 | 100 | 🟡 backup |
| 18 | IMPORT-BUCK-002 | ImportPower | 🌍 | 🚗 | **54** | 83 | 40 | 54 | 0 | 100 | 🟡 backup |
| 19 | IMPORT-BUCK-006 | GlobalPower | 🌍 | - | **45** | 83 | 10 | 77 | 0 | 100 | 🔴 not_recommended |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（9.0–16.0V 含标称 12.0V）
- 输出电流满足 ✓（6.0A，余量 100%）
- 温度范围覆盖 ✓（-40.0–125.0°C）
- 库存充足（3000 件）
- 生命周期：在产
- 单价 9.0 元（较低）
- 国产器件 ✓（MockSemi）
- 有数据手册

**证据链**（共 95 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| MOCK-BUCK-AEC-003 | `mock_ezplm_field` | supports temperature range -40.0C to 125.0C | 95% |  |
| MOCK-BUCK-AEC-003 | `mock_ezplm_field` | input voltage range 9.0V to 16.0V | 95% |  |
| MOCK-BUCK-AEC-003 | `mock_ezplm_field` | output current max 6.0A | 90% |  |
| MOCK-BUCK-AEC-003 | `mock_ezplm_field` | stock 3000 | 90% |  |
| MOCK-BUCK-AEC-003 | `mock_ezplm_field` | lifecycle active | 90% |  |
| MOCK-BUCK-AEC-001 | `mock_ezplm_field` | supports temperature range -40.0C to 125.0C | 95% |  |
| MOCK-BUCK-AEC-001 | `mock_ezplm_field` | input voltage range 4.5V to 36.0V | 95% |  |
| MOCK-BUCK-AEC-001 | `mock_ezplm_field` | output current max 5.0A | 90% |  |
| MOCK-BUCK-AEC-001 | `mock_ezplm_field` | stock 12000 | 90% |  |
| MOCK-BUCK-AEC-001 | `mock_ezplm_field` | lifecycle active | 90% |  |
| ... | ... | _(共 95 条，仅展示前 10 条)_ | ... | ... |

**风险评估**：⚪ low


---

### 5. dc_dc_005 ✅

**输入**：请给我一个 5V 到 3.3V 的降压芯片，输出 1A。  
**耗时**：1ms  

**解析约束**：

| 字段 | 值 |
|------|-----|
| category | dc_dc_converter |
| topology | buck |
| input_voltage_nominal_v | 5.0 |
| output_voltage_v | 3.3 |
| output_current_a | 1.0 |

**候选评分明细**（共 7 个）：

| # | 型号 | 厂商 | 国产 | 车规 | 总分 | 参数 | 供应 | 成本 | 国产 | 证据 | 推荐等级 |
|---|------|------|------|------|------|------|------|------|------|------|----------|
| 1 | MOCK-BUCK-008 | MockCore | 🇨🇳 | - | **85** | 67 | 100 | 78 | 100 | 100 | ⭐ recommended |
| 2 | MOCK-BUCK-010 | MiniPower | 🇨🇳 | - | **84** | 58 | 100 | 87 | 100 | 100 | ⭐ recommended |
| 3 | MOCK-BUCK-006 | LocalSemi | 🇨🇳 | 🚗 | **83** | 67 | 100 | 66 | 100 | 100 | ⭐ recommended |
| 4 | MOCK-BUCK-018 | SinoIC | 🇨🇳 | - | **82** | 50 | 100 | 100 | 100 | 100 | ⭐ recommended |
| 5 | MOCK-BUCK-014 | NanoPower | 🇨🇳 | - | **82** | 50 | 100 | 98 | 100 | 100 | ⭐ recommended |
| 6 | MOCK-BUCK-AEC-001 | MockSemi | 🇨🇳 | 🚗 | **82** | 67 | 100 | 56 | 100 | 100 | ⭐ recommended |
| 7 | MOCK-BUCK-022 | DragonIC | 🇨🇳 | 🚗 | **73** | 67 | 100 | 0 | 100 | 100 | 🟡 backup |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（5.0–24.0V 含标称 5.0V）
- 输出电流满足 ✓（2.5A，余量 150%）
- 库存充足（9000 件）
- 生命周期：在产
- 单价 2.8 元（较低）
- 国产器件 ✓（MockCore）
- 有数据手册

**证据链**（共 35 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| MOCK-BUCK-008 | `mock_ezplm_field` | supports temperature range -40.0C to 105.0C | 95% |  |
| MOCK-BUCK-008 | `mock_ezplm_field` | input voltage range 5.0V to 24.0V | 95% |  |
| MOCK-BUCK-008 | `mock_ezplm_field` | output current max 2.5A | 90% |  |
| MOCK-BUCK-008 | `mock_ezplm_field` | stock 9000 | 90% |  |
| MOCK-BUCK-008 | `mock_ezplm_field` | lifecycle active | 90% |  |
| MOCK-BUCK-010 | `mock_ezplm_field` | supports temperature range -40.0C to 85.0C | 95% |  |
| MOCK-BUCK-010 | `mock_ezplm_field` | input voltage range 4.5V to 18.0V | 95% |  |
| MOCK-BUCK-010 | `mock_ezplm_field` | output current max 1.5A | 90% |  |
| MOCK-BUCK-010 | `mock_ezplm_field` | stock 20000 | 90% |  |
| MOCK-BUCK-010 | `mock_ezplm_field` | lifecycle active | 90% |  |
| ... | ... | _(共 35 条，仅展示前 10 条)_ | ... | ... |

**风险评估**：⚪ low


---

### 6. dc_dc_006 ✅

**输入**：需要 48V 转 12V、1.5A 的降压模块，用于工业温度 -40°C 到 85°C，优先国产。  
**耗时**：1ms  

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

**候选评分明细**（共 2 个）：

| # | 型号 | 厂商 | 国产 | 车规 | 总分 | 参数 | 供应 | 成本 | 国产 | 证据 | 推荐等级 |
|---|------|------|------|------|------|------|------|------|------|------|----------|
| 1 | MOCK-BUCK-016 | PowerChina | 🇨🇳 | - | **97** | 89 | 100 | 100 | 100 | 100 | ⭐ recommended |
| 2 | MOCK-BUCK-022 | DragonIC | 🇨🇳 | 🚗 | **90** | 100 | 100 | 0 | 100 | 100 | ⭐ recommended |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（36.0–60.0V 含标称 48.0V）
- 输出电流满足 ✓（2.0A，余量 33%）
- 温度范围覆盖 ✓（-40.0–85.0°C）
- 库存充足（5000 件）
- 生命周期：在产
- 单价 8.8 元（较低）
- 国产器件 ✓（PowerChina）
- 有数据手册

**证据链**（共 10 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| MOCK-BUCK-016 | `mock_ezplm_field` | supports temperature range -40.0C to 85.0C | 95% |  |
| MOCK-BUCK-016 | `mock_ezplm_field` | input voltage range 36.0V to 60.0V | 95% |  |
| MOCK-BUCK-016 | `mock_ezplm_field` | output current max 2.0A | 90% |  |
| MOCK-BUCK-016 | `mock_ezplm_field` | stock 5000 | 90% |  |
| MOCK-BUCK-016 | `mock_ezplm_field` | lifecycle active | 90% |  |
| MOCK-BUCK-022 | `mock_ezplm_field` | supports temperature range -40.0C to 125.0C | 95% |  |
| MOCK-BUCK-022 | `mock_ezplm_field` | input voltage range 4.5V to 60.0V | 95% |  |
| MOCK-BUCK-022 | `mock_ezplm_field` | output current max 3.0A | 90% |  |
| MOCK-BUCK-022 | `mock_ezplm_field` | stock 8500 | 90% |  |
| MOCK-BUCK-022 | `mock_ezplm_field` | lifecycle active | 90% |  |

**风险评估**：⚪ low


---

### 7. dc_dc_007 ✅

**输入**：找一个 9V 转 5V、2A 的降压，温度 0°C 到 70°C，非车规。  
**耗时**：1ms  

**解析约束**：

| 字段 | 值 |
|------|-----|
| category | dc_dc_converter |
| topology | buck |
| grade | automotive |
| input_voltage_nominal_v | 9.0 |
| output_voltage_v | 5.0 |
| output_current_a | 2.0 |
| temperature_min_c | 0 |
| temperature_max_c | 70 |

**候选评分明细**（共 9 个）：

| # | 型号 | 厂商 | 国产 | 车规 | 总分 | 参数 | 供应 | 成本 | 国产 | 证据 | 推荐等级 |
|---|------|------|------|------|------|------|------|------|------|------|----------|
| 1 | MOCK-BUCK-AEC-001 | MockSemi | 🇨🇳 | 🚗 | **99** | 100 | 100 | 96 | 100 | 100 | ⭐ recommended |
| 2 | MOCK-BUCK-007 | LocalSemi | 🇨🇳 | 🚗 | **98** | 100 | 100 | 86 | 100 | 100 | ⭐ recommended |
| 3 | MOCK-BUCK-006 | LocalSemi | 🇨🇳 | 🚗 | **98** | 93 | 100 | 100 | 100 | 100 | ⭐ recommended |
| 4 | MOCK-BUCK-011 | MiniPower | 🇨🇳 | 🚗 | **97** | 93 | 100 | 95 | 100 | 100 | ⭐ recommended |
| 5 | MOCK-BUCK-AEC-003 | MockSemi | 🇨🇳 | 🚗 | **97** | 100 | 100 | 79 | 100 | 100 | ⭐ recommended |
| 6 | MOCK-BUCK-022 | DragonIC | 🇨🇳 | 🚗 | **93** | 92 | 100 | 75 | 100 | 100 | ⭐ recommended |
| 7 | MOCK-BUCK-020 | StarPower | 🇨🇳 | 🚗 | **80** | 92 | 40 | 88 | 100 | 100 | ⭐ recommended |
| 8 | IMPORT-BUCK-007 | OverseaChip | 🌍 | 🚗 | **62** | 100 | 70 | 0 | 0 | 100 | 🟡 backup |
| 9 | IMPORT-BUCK-004 | TechPower | 🌍 | 🚗 | **61** | 100 | 40 | 41 | 0 | 100 | 🟡 backup |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（4.5–36.0V 含标称 9.0V）
- 输出电流满足 ✓（5.0A，余量 150%）
- 温度范围覆盖 ✓（-40.0–125.0°C）
- 库存充足（12000 件）
- 生命周期：在产
- 单价 4.8 元（较低）
- 国产器件 ✓（MockSemi）
- 有数据手册

**证据链**（共 45 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| MOCK-BUCK-AEC-001 | `mock_ezplm_field` | supports temperature range -40.0C to 125.0C | 95% |  |
| MOCK-BUCK-AEC-001 | `mock_ezplm_field` | input voltage range 4.5V to 36.0V | 95% |  |
| MOCK-BUCK-AEC-001 | `mock_ezplm_field` | output current max 5.0A | 90% |  |
| MOCK-BUCK-AEC-001 | `mock_ezplm_field` | stock 12000 | 90% |  |
| MOCK-BUCK-AEC-001 | `mock_ezplm_field` | lifecycle active | 90% |  |
| MOCK-BUCK-007 | `mock_ezplm_field` | supports temperature range -40.0C to 125.0C | 95% |  |
| MOCK-BUCK-007 | `mock_ezplm_field` | input voltage range 9.0V to 36.0V | 95% |  |
| MOCK-BUCK-007 | `mock_ezplm_field` | output current max 5.0A | 90% |  |
| MOCK-BUCK-007 | `mock_ezplm_field` | stock 6000 | 90% |  |
| MOCK-BUCK-007 | `mock_ezplm_field` | lifecycle active | 90% |  |
| ... | ... | _(共 45 条，仅展示前 10 条)_ | ... | ... |

**风险评估**：⚪ medium

- ⚪ **medium** — 部分推荐器件库存偏低（MOCK-BUCK-020）。 _(缓解: 关注上述器件库存动态，提前预定。)_

---

### 8. dc_dc_008 ✅

**输入**：需要 12V 到 5V、3A 的车规级降压（automotive）。  
**耗时**：1ms  

**解析约束**：

| 字段 | 值 |
|------|-----|
| category | dc_dc_converter |
| topology | buck |
| grade | automotive |
| input_voltage_nominal_v | 12.0 |
| output_voltage_v | 5.0 |
| output_current_a | 3.0 |

**候选评分明细**（共 13 个）：

| # | 型号 | 厂商 | 国产 | 车规 | 总分 | 参数 | 供应 | 成本 | 国产 | 证据 | 推荐等级 |
|---|------|------|------|------|------|------|------|------|------|------|----------|
| 1 | MOCK-BUCK-AEC-001 | MockSemi | 🇨🇳 | 🚗 | **86** | 61 | 100 | 96 | 100 | 100 | ⭐ recommended |
| 2 | MOCK-BUCK-AEC-003 | MockSemi | 🇨🇳 | 🚗 | **85** | 67 | 100 | 79 | 100 | 100 | ⭐ recommended |
| 3 | MOCK-BUCK-015 | NanoPower | 🇨🇳 | 🚗 | **85** | 67 | 100 | 75 | 100 | 100 | ⭐ recommended |
| 4 | MOCK-BUCK-007 | LocalSemi | 🇨🇳 | 🚗 | **84** | 61 | 100 | 86 | 100 | 100 | ⭐ recommended |
| 5 | MOCK-BUCK-006 | LocalSemi | 🇨🇳 | 🚗 | **83** | 51 | 100 | 100 | 100 | 100 | ⭐ recommended |
| 6 | MOCK-BUCK-011 | MiniPower | 🇨🇳 | 🚗 | **82** | 51 | 100 | 95 | 100 | 100 | ⭐ recommended |
| 7 | MOCK-BUCK-004 | MockPower | 🇨🇳 | 🚗 | **82** | 50 | 100 | 93 | 100 | 100 | ⭐ recommended |
| 8 | MOCK-BUCK-009 | MockCore | 🇨🇳 | 🚗 | **80** | 50 | 100 | 81 | 100 | 100 | ⭐ recommended |
| 9 | MOCK-BUCK-022 | DragonIC | 🇨🇳 | 🚗 | **79** | 50 | 100 | 75 | 100 | 100 | ⭐ recommended |
| 10 | MOCK-BUCK-020 | StarPower | 🇨🇳 | 🚗 | **66** | 50 | 40 | 88 | 100 | 100 | 🟡 backup |
| 11 | IMPORT-BUCK-007 | OverseaChip | 🌍 | 🚗 | **51** | 67 | 70 | 0 | 0 | 100 | 🟡 backup |
| 12 | IMPORT-BUCK-004 | TechPower | 🌍 | 🚗 | **48** | 61 | 40 | 41 | 0 | 100 | 🔴 not_recommended |
| 13 | IMPORT-BUCK-002 | ImportPower | 🌍 | 🚗 | **46** | 50 | 40 | 54 | 0 | 100 | 🔴 not_recommended |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（4.5–36.0V 含标称 12.0V）
- 输出电流满足 ✓（5.0A，余量 67%）
- 库存充足（12000 件）
- 生命周期：在产
- 单价 4.8 元（较低）
- 国产器件 ✓（MockSemi）
- 有数据手册

**证据链**（共 65 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| MOCK-BUCK-AEC-001 | `mock_ezplm_field` | supports temperature range -40.0C to 125.0C | 95% |  |
| MOCK-BUCK-AEC-001 | `mock_ezplm_field` | input voltage range 4.5V to 36.0V | 95% |  |
| MOCK-BUCK-AEC-001 | `mock_ezplm_field` | output current max 5.0A | 90% |  |
| MOCK-BUCK-AEC-001 | `mock_ezplm_field` | stock 12000 | 90% |  |
| MOCK-BUCK-AEC-001 | `mock_ezplm_field` | lifecycle active | 90% |  |
| MOCK-BUCK-AEC-003 | `mock_ezplm_field` | supports temperature range -40.0C to 125.0C | 95% |  |
| MOCK-BUCK-AEC-003 | `mock_ezplm_field` | input voltage range 9.0V to 16.0V | 95% |  |
| MOCK-BUCK-AEC-003 | `mock_ezplm_field` | output current max 6.0A | 90% |  |
| MOCK-BUCK-AEC-003 | `mock_ezplm_field` | stock 3000 | 90% |  |
| MOCK-BUCK-AEC-003 | `mock_ezplm_field` | lifecycle active | 90% |  |
| ... | ... | _(共 65 条，仅展示前 10 条)_ | ... | ... |

**风险评估**：⚪ low


---

### 9. dc_dc_009 ✅

**输入**：5V转3.3V，输出 0.5A，优先低供应链风险。  
**耗时**：1ms  

**解析约束**：

| 字段 | 值 |
|------|-----|
| category | dc_dc_converter |
| topology | buck |
| input_voltage_nominal_v | 5.0 |
| output_voltage_v | 3.3 |
| output_current_a | 0.5 |
| preferences | low_supply_risk |

**候选评分明细**（共 8 个）：

| # | 型号 | 厂商 | 国产 | 车规 | 总分 | 参数 | 供应 | 成本 | 国产 | 证据 | 推荐等级 |
|---|------|------|------|------|------|------|------|------|------|------|----------|
| 1 | MOCK-BUCK-018 | SinoIC | 🇨🇳 | - | **88** | 67 | 100 | 98 | 100 | 100 | ⭐ recommended |
| 2 | MOCK-BUCK-014 | NanoPower | 🇨🇳 | - | **88** | 67 | 100 | 96 | 100 | 100 | ⭐ recommended |
| 3 | MOCK-BUCK-010 | MiniPower | 🇨🇳 | - | **87** | 67 | 100 | 86 | 100 | 100 | ⭐ recommended |
| 4 | MOCK-BUCK-008 | MockCore | 🇨🇳 | - | **86** | 67 | 100 | 76 | 100 | 100 | ⭐ recommended |
| 5 | MOCK-BUCK-006 | LocalSemi | 🇨🇳 | 🚗 | **85** | 67 | 100 | 64 | 100 | 100 | ⭐ recommended |
| 6 | MOCK-BUCK-AEC-001 | MockSemi | 🇨🇳 | 🚗 | **84** | 67 | 100 | 55 | 100 | 100 | ⭐ recommended |
| 7 | MOCK-BUCK-021 | StarPower | 🇨🇳 | - | **84** | 53 | 100 | 100 | 100 | 100 | ⭐ recommended |
| 8 | MOCK-BUCK-022 | DragonIC | 🇨🇳 | 🚗 | **78** | 67 | 100 | 0 | 100 | 100 | ⭐ recommended |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（4.5–6.0V 含标称 5.0V）
- 输出电流满足 ✓（1.0A，余量 100%）
- 库存充足（30000 件）
- 生命周期：在产
- 单价 0.75 元（较低）
- 国产器件 ✓（SinoIC）
- 有数据手册

**证据链**（共 40 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| MOCK-BUCK-018 | `mock_ezplm_field` | supports temperature range -40.0C to 85.0C | 95% |  |
| MOCK-BUCK-018 | `mock_ezplm_field` | input voltage range 4.5V to 6.0V | 95% |  |
| MOCK-BUCK-018 | `mock_ezplm_field` | output current max 1.0A | 90% |  |
| MOCK-BUCK-018 | `mock_ezplm_field` | stock 30000 | 90% |  |
| MOCK-BUCK-018 | `mock_ezplm_field` | lifecycle active | 90% |  |
| MOCK-BUCK-014 | `mock_ezplm_field` | supports temperature range -40.0C to 85.0C | 95% |  |
| MOCK-BUCK-014 | `mock_ezplm_field` | input voltage range 3.3V to 5.0V | 95% |  |
| MOCK-BUCK-014 | `mock_ezplm_field` | output current max 1.0A | 90% |  |
| MOCK-BUCK-014 | `mock_ezplm_field` | stock 25000 | 90% |  |
| MOCK-BUCK-014 | `mock_ezplm_field` | lifecycle active | 90% |  |
| ... | ... | _(共 40 条，仅展示前 10 条)_ | ... | ... |

**风险评估**：⚪ low


---

### 10. dc_dc_010 ✅

**输入**：输入 24V，输出 5V，电流 10A，高功率场景。  
**耗时**：1ms  

**解析约束**：

| 字段 | 值 |
|------|-----|
| category | dc_dc_converter |
| topology | buck |
| input_voltage_nominal_v | 24.0 |
| output_voltage_v | 5.0 |
| output_current_a | 10.0 |

**候选评分明细**（共 3 个）：

| # | 型号 | 厂商 | 国产 | 车规 | 总分 | 参数 | 供应 | 成本 | 国产 | 证据 | 推荐等级 |
|---|------|------|------|------|------|------|------|------|------|------|----------|
| 1 | MOCK-BUCK-HP-001 | SinoIC | 🇨🇳 | - | **84** | 53 | 100 | 100 | 100 | 100 | ⭐ recommended |
| 2 | MOCK-BUCK-019 | SinoIC | 🇨🇳 | - | **75** | 53 | 100 | 43 | 100 | 100 | ⭐ recommended |
| 3 | MOCK-BUCK-HP-002 | PowerChina | 🇨🇳 | - | **70** | 58 | 100 | 0 | 100 | 100 | 🟡 backup |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（18.0–36.0V 含标称 24.0V）
- 输出电流满足 ✓（12.0A，余量 20%）
- 库存充足（3000 件）
- 生命周期：在产
- 单价 14.5 元（较低）
- 国产器件 ✓（SinoIC）
- 有数据手册

**证据链**（共 15 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| MOCK-BUCK-HP-001 | `mock_ezplm_field` | supports temperature range -40.0C to 125.0C | 95% |  |
| MOCK-BUCK-HP-001 | `mock_ezplm_field` | input voltage range 18.0V to 36.0V | 95% |  |
| MOCK-BUCK-HP-001 | `mock_ezplm_field` | output current max 12.0A | 90% |  |
| MOCK-BUCK-HP-001 | `mock_ezplm_field` | stock 3000 | 90% |  |
| MOCK-BUCK-HP-001 | `mock_ezplm_field` | lifecycle active | 90% |  |
| MOCK-BUCK-019 | `mock_ezplm_field` | supports temperature range -40.0C to 125.0C | 95% |  |
| MOCK-BUCK-019 | `mock_ezplm_field` | input voltage range 20.0V to 30.0V | 95% |  |
| MOCK-BUCK-019 | `mock_ezplm_field` | output current max 12.0A | 90% |  |
| MOCK-BUCK-019 | `mock_ezplm_field` | stock 1200 | 90% |  |
| MOCK-BUCK-019 | `mock_ezplm_field` | lifecycle active | 90% |  |
| ... | ... | _(共 15 条，仅展示前 10 条)_ | ... | ... |

**风险评估**：⚪ low


---

### 11. dc_dc_011 ✅

**输入**：找一个 18V 转 5V、6A 的车规级降压芯片，工作温度 -40°C 到 125°C，必须国产，低供应风险。  
**耗时**：1ms  

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

**候选评分明细**（共 2 个）：

| # | 型号 | 厂商 | 国产 | 车规 | 总分 | 参数 | 供应 | 成本 | 国产 | 证据 | 推荐等级 |
|---|------|------|------|------|------|------|------|------|------|------|----------|
| 1 | MOCK-BUCK-015 | NanoPower | 🇨🇳 | 🚗 | **95** | 83 | 100 | 100 | 100 | 100 | ⭐ recommended |
| 2 | IMPORT-BUCK-007 | OverseaChip | 🌍 | 🚗 | **54** | 83 | 70 | 0 | 0 | 100 | 🟡 backup |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（12.0–36.0V 含标称 18.0V）
- 输出电流满足 ✓（6.0A，余量 0%）
- 温度范围覆盖 ✓（-40.0–125.0°C）
- 库存充足（1800 件）
- 生命周期：在产
- 单价 10.0 元（较低）
- 国产器件 ✓（NanoPower）
- 有数据手册

**证据链**（共 10 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| MOCK-BUCK-015 | `mock_ezplm_field` | supports temperature range -40.0C to 125.0C | 95% |  |
| MOCK-BUCK-015 | `mock_ezplm_field` | input voltage range 12.0V to 36.0V | 95% |  |
| MOCK-BUCK-015 | `mock_ezplm_field` | output current max 6.0A | 90% |  |
| MOCK-BUCK-015 | `mock_ezplm_field` | stock 1800 | 90% |  |
| MOCK-BUCK-015 | `mock_ezplm_field` | lifecycle active | 90% |  |
| IMPORT-BUCK-007 | `mock_ezplm_field` | supports temperature range -40.0C to 125.0C | 95% |  |
| IMPORT-BUCK-007 | `mock_ezplm_field` | input voltage range 6.0V to 42.0V | 95% |  |
| IMPORT-BUCK-007 | `mock_ezplm_field` | output current max 6.0A | 90% |  |
| IMPORT-BUCK-007 | `mock_ezplm_field` | stock 400 | 90% |  |
| IMPORT-BUCK-007 | `mock_ezplm_field` | lifecycle active | 90% |  |

**风险评估**：⚪ medium

- ⚪ **medium** — 仅 1 款推荐器件（MOCK-BUCK-015），备选方案不足。 _(缓解: 纳入 backup 级器件作为冗余，或向供应商确认长期备货计划。)_

---

### 12. dc_dc_012 ✅

**输入**：需要 28V 转 12V、2A 的降压芯片，工业温度 -40°C 到 105°C，非车规，必须国产。  
**耗时**：1ms  

**解析约束**：

| 字段 | 值 |
|------|-----|
| category | dc_dc_converter |
| topology | buck |
| grade | automotive |
| input_voltage_nominal_v | 28.0 |
| output_voltage_v | 12.0 |
| output_current_a | 2.0 |
| temperature_min_c | -40 |
| temperature_max_c | 105 |
| preferences | domestic_alternative |
| must_have | automotive_grade, domestic |

**候选评分明细**（共 12 个）：

| # | 型号 | 厂商 | 国产 | 车规 | 总分 | 参数 | 供应 | 成本 | 国产 | 证据 | 推荐等级 |
|---|------|------|------|------|------|------|------|------|------|------|----------|
| 1 | MOCK-BUCK-AEC-001 | MockSemi | 🇨🇳 | 🚗 | **100** | 100 | 100 | 100 | 100 | 100 | ⭐ recommended |
| 2 | MOCK-BUCK-007 | LocalSemi | 🇨🇳 | 🚗 | **99** | 100 | 100 | 90 | 100 | 100 | ⭐ recommended |
| 3 | MOCK-BUCK-011 | MiniPower | 🇨🇳 | 🚗 | **98** | 93 | 100 | 98 | 100 | 100 | ⭐ recommended |
| 4 | MOCK-BUCK-015 | NanoPower | 🇨🇳 | 🚗 | **98** | 100 | 100 | 78 | 100 | 100 | ⭐ recommended |
| 5 | MOCK-BUCK-017 | PowerChina | 🇨🇳 | 🚗 | **97** | 100 | 100 | 72 | 100 | 100 | ⭐ recommended |
| 6 | MOCK-BUCK-004 | MockPower | 🇨🇳 | 🚗 | **97** | 92 | 100 | 97 | 100 | 100 | ⭐ recommended |
| 7 | MOCK-BUCK-009 | MockCore | 🇨🇳 | 🚗 | **96** | 92 | 100 | 84 | 100 | 100 | ⭐ recommended |
| 8 | MOCK-BUCK-022 | DragonIC | 🇨🇳 | 🚗 | **95** | 92 | 100 | 78 | 100 | 100 | ⭐ recommended |
| 9 | MOCK-BUCK-020 | StarPower | 🇨🇳 | 🚗 | **82** | 92 | 40 | 91 | 100 | 100 | ⭐ recommended |
| 10 | IMPORT-BUCK-007 | OverseaChip | 🌍 | 🚗 | **58** | 100 | 70 | 0 | 0 | 100 | 🟡 backup |
| 11 | IMPORT-BUCK-004 | TechPower | 🌍 | 🚗 | **54** | 100 | 40 | 43 | 0 | 100 | 🟡 backup |
| 12 | IMPORT-BUCK-005 | TechPower | 🌍 | 🚗 | **45** | 100 | 10 | 26 | 0 | 100 | 🔴 not_recommended |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（4.5–36.0V 含标称 28.0V）
- 输出电流满足 ✓（5.0A，余量 150%）
- 温度范围覆盖 ✓（-40.0–125.0°C）
- 库存充足（12000 件）
- 生命周期：在产
- 单价 4.8 元（较低）
- 国产器件 ✓（MockSemi）
- 有数据手册

**证据链**（共 60 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| MOCK-BUCK-AEC-001 | `mock_ezplm_field` | supports temperature range -40.0C to 125.0C | 95% |  |
| MOCK-BUCK-AEC-001 | `mock_ezplm_field` | input voltage range 4.5V to 36.0V | 95% |  |
| MOCK-BUCK-AEC-001 | `mock_ezplm_field` | output current max 5.0A | 90% |  |
| MOCK-BUCK-AEC-001 | `mock_ezplm_field` | stock 12000 | 90% |  |
| MOCK-BUCK-AEC-001 | `mock_ezplm_field` | lifecycle active | 90% |  |
| MOCK-BUCK-007 | `mock_ezplm_field` | supports temperature range -40.0C to 125.0C | 95% |  |
| MOCK-BUCK-007 | `mock_ezplm_field` | input voltage range 9.0V to 36.0V | 95% |  |
| MOCK-BUCK-007 | `mock_ezplm_field` | output current max 5.0A | 90% |  |
| MOCK-BUCK-007 | `mock_ezplm_field` | stock 6000 | 90% |  |
| MOCK-BUCK-007 | `mock_ezplm_field` | lifecycle active | 90% |  |
| ... | ... | _(共 60 条，仅展示前 10 条)_ | ... | ... |

**风险评估**：⚪ medium

- ⚪ **medium** — 部分推荐器件库存偏低（MOCK-BUCK-020）。 _(缓解: 关注上述器件库存动态，提前预定。)_

---

### 13. dc_dc_013 ❌

**输入**：36V 输入，输出 5V、8A，大功率 DC-DC，希望库存充足。  
**耗时**：1ms  

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

**风险评估**：⚪ high

- ⚪ **high** — 检索无结果，请确认类别/拓扑约束或扩充数据源。 _(缓解: 检查 EZ-PLM API 白名单覆盖情况，或补充 mock 数据。)_

---

### 14. dc_dc_014 ✅

**输入**：需要一个 3.3V 转 1.8V、0.6A 的降压芯片，温度 -40°C 到 85°C，优先国产。  
**耗时**：1ms  

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

**候选评分明细**（共 2 个）：

| # | 型号 | 厂商 | 国产 | 车规 | 总分 | 参数 | 供应 | 成本 | 国产 | 证据 | 推荐等级 |
|---|------|------|------|------|------|------|------|------|------|------|----------|
| 1 | MOCK-BUCK-021 | StarPower | 🇨🇳 | - | **95** | 83 | 100 | 100 | 100 | 100 | ⭐ recommended |
| 2 | MOCK-BUCK-014 | NanoPower | 🇨🇳 | - | **88** | 94 | 100 | 0 | 100 | 100 | ⭐ recommended |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（2.5–5.5V 含标称 3.3V）
- 输出电流满足 ✓（0.6A，余量 0%）
- 温度范围覆盖 ✓（-40.0–85.0°C）
- 库存充足（50000 件）
- 生命周期：在产
- 单价 0.55 元（较低）
- 国产器件 ✓（StarPower）
- 有数据手册

**证据链**（共 10 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| MOCK-BUCK-021 | `mock_ezplm_field` | supports temperature range -40.0C to 85.0C | 95% |  |
| MOCK-BUCK-021 | `mock_ezplm_field` | input voltage range 2.5V to 5.5V | 95% |  |
| MOCK-BUCK-021 | `mock_ezplm_field` | output current max 0.6A | 90% |  |
| MOCK-BUCK-021 | `mock_ezplm_field` | stock 50000 | 90% |  |
| MOCK-BUCK-021 | `mock_ezplm_field` | lifecycle active | 90% |  |
| MOCK-BUCK-014 | `mock_ezplm_field` | supports temperature range -40.0C to 85.0C | 95% |  |
| MOCK-BUCK-014 | `mock_ezplm_field` | input voltage range 3.3V to 5.0V | 95% |  |
| MOCK-BUCK-014 | `mock_ezplm_field` | output current max 1.0A | 90% |  |
| MOCK-BUCK-014 | `mock_ezplm_field` | stock 25000 | 90% |  |
| MOCK-BUCK-014 | `mock_ezplm_field` | lifecycle active | 90% |  |

**风险评估**：⚪ low


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

**候选评分明细**（共 22 个）：

| # | 型号 | 厂商 | 国产 | 车规 | 总分 | 参数 | 供应 | 成本 | 国产 | 证据 | 推荐等级 |
|---|------|------|------|------|------|------|------|------|------|------|----------|
| 1 | MOCK-BUCK-008 | MockCore | 🇨🇳 | - | **88** | 67 | 100 | 97 | 100 | 100 | ⭐ recommended |
| 2 | MOCK-BUCK-006 | LocalSemi | 🇨🇳 | 🚗 | **87** | 67 | 100 | 92 | 100 | 100 | ⭐ recommended |
| 3 | MOCK-BUCK-AEC-001 | MockSemi | 🇨🇳 | 🚗 | **87** | 67 | 100 | 89 | 100 | 100 | ⭐ recommended |
| 4 | MOCK-BUCK-011 | MiniPower | 🇨🇳 | 🚗 | **86** | 67 | 100 | 87 | 100 | 100 | ⭐ recommended |
| 5 | MOCK-BUCK-004 | MockPower | 🇨🇳 | 🚗 | **86** | 67 | 100 | 86 | 100 | 100 | ⭐ recommended |
| 6 | MOCK-BUCK-005 | MockPower | 🇨🇳 | - | **86** | 67 | 100 | 84 | 100 | 100 | ⭐ recommended |
| 7 | MOCK-BUCK-AEC-002 | MockSemi | 🇨🇳 | - | **86** | 67 | 100 | 82 | 100 | 100 | ⭐ recommended |
| 8 | MOCK-BUCK-007 | LocalSemi | 🇨🇳 | 🚗 | **85** | 67 | 100 | 80 | 100 | 100 | ⭐ recommended |
| 9 | MOCK-BUCK-009 | MockCore | 🇨🇳 | 🚗 | **85** | 67 | 100 | 75 | 100 | 100 | ⭐ recommended |
| 10 | MOCK-BUCK-AEC-003 | MockSemi | 🇨🇳 | 🚗 | **84** | 67 | 100 | 73 | 100 | 100 | ⭐ recommended |
| 11 | MOCK-BUCK-010 | MiniPower | 🇨🇳 | - | **84** | 54 | 100 | 100 | 100 | 100 | ⭐ recommended |
| 12 | MOCK-BUCK-022 | DragonIC | 🇨🇳 | 🚗 | **84** | 67 | 100 | 69 | 100 | 100 | ⭐ recommended |
| 13 | MOCK-BUCK-015 | NanoPower | 🇨🇳 | 🚗 | **84** | 67 | 100 | 69 | 100 | 100 | ⭐ recommended |
| 14 | MOCK-BUCK-020 | StarPower | 🇨🇳 | 🚗 | **71** | 67 | 40 | 81 | 100 | 100 | 🟡 backup |
| 15 | MOCK-BUCK-013 | MicroSemi | 🌍 | - | **61** | 64 | 70 | 77 | 0 | 100 | 🟡 backup |
| 16 | IMPORT-BUCK-003 | ImportPower | 🌍 | - | **61** | 67 | 70 | 65 | 0 | 100 | 🟡 backup |
| 17 | IMPORT-BUCK-001 | ImportCo | 🌍 | - | **60** | 67 | 70 | 59 | 0 | 100 | 🟡 backup |
| 18 | MOCK-BUCK-012 | MicroSemi | 🌍 | - | **59** | 67 | 70 | 56 | 0 | 100 | 🟡 backup |
| 19 | IMPORT-BUCK-007 | OverseaChip | 🌍 | 🚗 | **51** | 67 | 70 | 0 | 0 | 100 | 🟡 backup |
| 20 | IMPORT-BUCK-002 | ImportPower | 🌍 | 🚗 | **51** | 67 | 40 | 50 | 0 | 100 | 🟡 backup |
| 21 | IMPORT-BUCK-004 | TechPower | 🌍 | 🚗 | **49** | 67 | 40 | 38 | 0 | 100 | 🔴 not_recommended |
| 22 | IMPORT-BUCK-006 | GlobalPower | 🌍 | - | **46** | 67 | 10 | 71 | 0 | 100 | 🔴 not_recommended |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（5.0–24.0V 含标称 12.0V）
- 输出电流满足 ✓（2.5A，余量 108%）
- 库存充足（9000 件）
- 生命周期：在产
- 单价 2.8 元（较低）
- 国产器件 ✓（MockCore）
- 有数据手册

**证据链**（共 110 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| MOCK-BUCK-008 | `mock_ezplm_field` | supports temperature range -40.0C to 105.0C | 95% |  |
| MOCK-BUCK-008 | `mock_ezplm_field` | input voltage range 5.0V to 24.0V | 95% |  |
| MOCK-BUCK-008 | `mock_ezplm_field` | output current max 2.5A | 90% |  |
| MOCK-BUCK-008 | `mock_ezplm_field` | stock 9000 | 90% |  |
| MOCK-BUCK-008 | `mock_ezplm_field` | lifecycle active | 90% |  |
| MOCK-BUCK-006 | `mock_ezplm_field` | supports temperature range -40.0C to 125.0C | 95% |  |
| MOCK-BUCK-006 | `mock_ezplm_field` | input voltage range 4.5V to 22.0V | 95% |  |
| MOCK-BUCK-006 | `mock_ezplm_field` | output current max 3.2A | 90% |  |
| MOCK-BUCK-006 | `mock_ezplm_field` | stock 15000 | 90% |  |
| MOCK-BUCK-006 | `mock_ezplm_field` | lifecycle active | 90% |  |
| ... | ... | _(共 110 条，仅展示前 10 条)_ | ... | ... |

**风险评估**：⚪ low


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

**候选评分明细**（共 7 个）：

| # | 型号 | 厂商 | 国产 | 车规 | 总分 | 参数 | 供应 | 成本 | 国产 | 证据 | 推荐等级 |
|---|------|------|------|------|------|------|------|------|------|------|----------|
| 1 | MOCK-BUCK-AEC-001 | MockSemi | 🇨🇳 | 🚗 | **96** | 88 | 100 | 100 | 100 | 100 | ⭐ recommended |
| 2 | MOCK-BUCK-015 | NanoPower | 🇨🇳 | 🚗 | **95** | 92 | 100 | 78 | 100 | 100 | ⭐ recommended |
| 3 | MOCK-BUCK-007 | LocalSemi | 🇨🇳 | 🚗 | **95** | 88 | 100 | 90 | 100 | 100 | ⭐ recommended |
| 4 | MOCK-BUCK-017 | PowerChina | 🇨🇳 | 🚗 | **93** | 88 | 100 | 72 | 100 | 100 | ⭐ recommended |
| 5 | IMPORT-BUCK-007 | OverseaChip | 🌍 | 🚗 | **55** | 92 | 70 | 0 | 0 | 100 | 🟡 backup |
| 6 | IMPORT-BUCK-004 | TechPower | 🌍 | 🚗 | **51** | 88 | 40 | 43 | 0 | 100 | 🟡 backup |
| 7 | IMPORT-BUCK-005 | TechPower | 🌍 | 🚗 | **40** | 83 | 10 | 26 | 0 | 100 | 🔴 not_recommended |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（4.5–36.0V 含标称 24.0V）
- 输出电流满足 ✓（5.0A，余量 25%）
- 温度范围覆盖 ✓（-40.0–125.0°C）
- 库存充足（12000 件）
- 生命周期：在产
- 单价 4.8 元（较低）
- 国产器件 ✓（MockSemi）
- 有数据手册

**证据链**（共 35 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| MOCK-BUCK-AEC-001 | `mock_ezplm_field` | supports temperature range -40.0C to 125.0C | 95% |  |
| MOCK-BUCK-AEC-001 | `mock_ezplm_field` | input voltage range 4.5V to 36.0V | 95% |  |
| MOCK-BUCK-AEC-001 | `mock_ezplm_field` | output current max 5.0A | 90% |  |
| MOCK-BUCK-AEC-001 | `mock_ezplm_field` | stock 12000 | 90% |  |
| MOCK-BUCK-AEC-001 | `mock_ezplm_field` | lifecycle active | 90% |  |
| MOCK-BUCK-015 | `mock_ezplm_field` | supports temperature range -40.0C to 125.0C | 95% |  |
| MOCK-BUCK-015 | `mock_ezplm_field` | input voltage range 12.0V to 36.0V | 95% |  |
| MOCK-BUCK-015 | `mock_ezplm_field` | output current max 6.0A | 90% |  |
| MOCK-BUCK-015 | `mock_ezplm_field` | stock 1800 | 90% |  |
| MOCK-BUCK-015 | `mock_ezplm_field` | lifecycle active | 90% |  |
| ... | ... | _(共 35 条，仅展示前 10 条)_ | ... | ... |

**风险评估**：⚪ low


---

### 17. dc_dc_017 ❌

**输入**：48V 转 5V、3A 工业级电源方案，工作温度 -40°C 到 85°C，库存优先。  
**耗时**：1ms  

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
| 1 | MOCK-BUCK-022 | DragonIC | 🇨🇳 | 🚗 | **87** | 83 | 100 | 50 | 100 | 100 | ⭐ recommended |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（4.5–60.0V 含标称 48.0V）
- 输出电流满足 ✓（3.0A，余量 0%）
- 温度范围覆盖 ✓（-40.0–125.0°C）
- 库存充足（8500 件）
- 生命周期：在产
- 单价 9.9 元（中等）
- 国产器件 ✓（DragonIC）
- 有数据手册

**证据链**（共 5 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| MOCK-BUCK-022 | `mock_ezplm_field` | supports temperature range -40.0C to 125.0C | 95% |  |
| MOCK-BUCK-022 | `mock_ezplm_field` | input voltage range 4.5V to 60.0V | 95% |  |
| MOCK-BUCK-022 | `mock_ezplm_field` | output current max 3.0A | 90% |  |
| MOCK-BUCK-022 | `mock_ezplm_field` | stock 8500 | 90% |  |
| MOCK-BUCK-022 | `mock_ezplm_field` | lifecycle active | 90% |  |

**风险评估**：⚪ medium

- ⚪ **medium** — 仅 1 款推荐器件（MOCK-BUCK-022），备选方案不足。 _(缓解: 纳入 backup 级器件作为冗余，或向供应商确认长期备货计划。)_

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

**候选评分明细**（共 18 个）：

| # | 型号 | 厂商 | 国产 | 车规 | 总分 | 参数 | 供应 | 成本 | 国产 | 证据 | 推荐等级 |
|---|------|------|------|------|------|------|------|------|------|------|----------|
| 1 | MOCK-BUCK-006 | LocalSemi | 🇨🇳 | 🚗 | **99** | 100 | 100 | 92 | 100 | 100 | ⭐ recommended |
| 2 | MOCK-BUCK-AEC-001 | MockSemi | 🇨🇳 | 🚗 | **99** | 100 | 100 | 89 | 100 | 100 | ⭐ recommended |
| 3 | MOCK-BUCK-011 | MiniPower | 🇨🇳 | 🚗 | **99** | 100 | 100 | 87 | 100 | 100 | ⭐ recommended |
| 4 | MOCK-BUCK-004 | MockPower | 🇨🇳 | 🚗 | **99** | 100 | 100 | 86 | 100 | 100 | ⭐ recommended |
| 5 | MOCK-BUCK-005 | MockPower | 🇨🇳 | - | **98** | 100 | 100 | 84 | 100 | 100 | ⭐ recommended |
| 6 | MOCK-BUCK-AEC-002 | MockSemi | 🇨🇳 | - | **98** | 100 | 100 | 82 | 100 | 100 | ⭐ recommended |
| 7 | MOCK-BUCK-008 | MockCore | 🇨🇳 | - | **98** | 94 | 100 | 97 | 100 | 100 | ⭐ recommended |
| 8 | MOCK-BUCK-007 | LocalSemi | 🇨🇳 | 🚗 | **98** | 100 | 100 | 80 | 100 | 100 | ⭐ recommended |
| 9 | MOCK-BUCK-009 | MockCore | 🇨🇳 | 🚗 | **97** | 100 | 100 | 75 | 100 | 100 | ⭐ recommended |
| 10 | MOCK-BUCK-AEC-003 | MockSemi | 🇨🇳 | 🚗 | **97** | 100 | 100 | 73 | 100 | 100 | ⭐ recommended |
| 11 | MOCK-BUCK-022 | DragonIC | 🇨🇳 | 🚗 | **97** | 100 | 100 | 69 | 100 | 100 | ⭐ recommended |
| 12 | MOCK-BUCK-015 | NanoPower | 🇨🇳 | 🚗 | **97** | 100 | 100 | 69 | 100 | 100 | ⭐ recommended |
| 13 | MOCK-BUCK-010 | MiniPower | 🇨🇳 | - | **95** | 83 | 100 | 100 | 100 | 100 | ⭐ recommended |
| 14 | MOCK-BUCK-020 | StarPower | 🇨🇳 | 🚗 | **83** | 100 | 40 | 81 | 100 | 100 | ⭐ recommended |
| 15 | MOCK-BUCK-013 | MicroSemi | 🌍 | - | **63** | 91 | 70 | 77 | 0 | 100 | 🟡 backup |
| 16 | IMPORT-BUCK-007 | OverseaChip | 🌍 | 🚗 | **58** | 100 | 70 | 0 | 0 | 100 | 🟡 backup |
| 17 | IMPORT-BUCK-002 | ImportPower | 🌍 | 🚗 | **55** | 100 | 40 | 50 | 0 | 100 | 🟡 backup |
| 18 | IMPORT-BUCK-004 | TechPower | 🌍 | 🚗 | **54** | 100 | 40 | 38 | 0 | 100 | 🟡 backup |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（4.5–22.0V 含标称 12.0V）
- 输出电流满足 ✓（3.2A，余量 113%）
- 温度范围覆盖 ✓（-40.0–125.0°C）
- 库存充足（15000 件）
- 生命周期：在产
- 单价 3.9 元（较低）
- 国产器件 ✓（LocalSemi）
- 有数据手册

**证据链**（共 90 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| MOCK-BUCK-006 | `mock_ezplm_field` | supports temperature range -40.0C to 125.0C | 95% |  |
| MOCK-BUCK-006 | `mock_ezplm_field` | input voltage range 4.5V to 22.0V | 95% |  |
| MOCK-BUCK-006 | `mock_ezplm_field` | output current max 3.2A | 90% |  |
| MOCK-BUCK-006 | `mock_ezplm_field` | stock 15000 | 90% |  |
| MOCK-BUCK-006 | `mock_ezplm_field` | lifecycle active | 90% |  |
| MOCK-BUCK-AEC-001 | `mock_ezplm_field` | supports temperature range -40.0C to 125.0C | 95% |  |
| MOCK-BUCK-AEC-001 | `mock_ezplm_field` | input voltage range 4.5V to 36.0V | 95% |  |
| MOCK-BUCK-AEC-001 | `mock_ezplm_field` | output current max 5.0A | 90% |  |
| MOCK-BUCK-AEC-001 | `mock_ezplm_field` | stock 12000 | 90% |  |
| MOCK-BUCK-AEC-001 | `mock_ezplm_field` | lifecycle active | 90% |  |
| ... | ... | _(共 90 条，仅展示前 10 条)_ | ... | ... |

**风险评估**：⚪ medium

- ⚪ **medium** — 部分推荐器件库存偏低（MOCK-BUCK-020）。 _(缓解: 关注上述器件库存动态，提前预定。)_

---

### 19. dc_dc_019 ✅

**输入**：需要一个 5V 转 1.2V、0.3A 的低压降压芯片，温度 -40°C 到 85°C，用于消费电子。  
**耗时**：1ms  

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

**候选评分明细**（共 8 个）：

| # | 型号 | 厂商 | 国产 | 车规 | 总分 | 参数 | 供应 | 成本 | 国产 | 证据 | 推荐等级 |
|---|------|------|------|------|------|------|------|------|------|------|----------|
| 1 | MOCK-BUCK-021 | StarPower | 🇨🇳 | - | **100** | 100 | 100 | 100 | 100 | 100 | ⭐ recommended |
| 2 | MOCK-BUCK-018 | SinoIC | 🇨🇳 | - | **100** | 100 | 100 | 98 | 100 | 100 | ⭐ recommended |
| 3 | MOCK-BUCK-014 | NanoPower | 🇨🇳 | - | **99** | 100 | 100 | 96 | 100 | 100 | ⭐ recommended |
| 4 | MOCK-BUCK-010 | MiniPower | 🇨🇳 | - | **98** | 100 | 100 | 86 | 100 | 100 | ⭐ recommended |
| 5 | MOCK-BUCK-008 | MockCore | 🇨🇳 | - | **96** | 100 | 100 | 76 | 100 | 100 | ⭐ recommended |
| 6 | MOCK-BUCK-006 | LocalSemi | 🇨🇳 | 🚗 | **95** | 100 | 100 | 64 | 100 | 100 | ⭐ recommended |
| 7 | MOCK-BUCK-AEC-001 | MockSemi | 🇨🇳 | 🚗 | **93** | 100 | 100 | 55 | 100 | 100 | ⭐ recommended |
| 8 | MOCK-BUCK-022 | DragonIC | 🇨🇳 | 🚗 | **85** | 100 | 100 | 0 | 100 | 100 | ⭐ recommended |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（2.5–5.5V 含标称 5.0V）
- 输出电流满足 ✓（0.6A，余量 100%）
- 温度范围覆盖 ✓（-40.0–85.0°C）
- 库存充足（50000 件）
- 生命周期：在产
- 单价 0.55 元（较低）
- 国产器件 ✓（StarPower）
- 有数据手册

**证据链**（共 40 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| MOCK-BUCK-021 | `mock_ezplm_field` | supports temperature range -40.0C to 85.0C | 95% |  |
| MOCK-BUCK-021 | `mock_ezplm_field` | input voltage range 2.5V to 5.5V | 95% |  |
| MOCK-BUCK-021 | `mock_ezplm_field` | output current max 0.6A | 90% |  |
| MOCK-BUCK-021 | `mock_ezplm_field` | stock 50000 | 90% |  |
| MOCK-BUCK-021 | `mock_ezplm_field` | lifecycle active | 90% |  |
| MOCK-BUCK-018 | `mock_ezplm_field` | supports temperature range -40.0C to 85.0C | 95% |  |
| MOCK-BUCK-018 | `mock_ezplm_field` | input voltage range 4.5V to 6.0V | 95% |  |
| MOCK-BUCK-018 | `mock_ezplm_field` | output current max 1.0A | 90% |  |
| MOCK-BUCK-018 | `mock_ezplm_field` | stock 30000 | 90% |  |
| MOCK-BUCK-018 | `mock_ezplm_field` | lifecycle active | 90% |  |
| ... | ... | _(共 40 条，仅展示前 10 条)_ | ... | ... |

**风险评估**：⚪ low


---

### 20. dc_dc_020 ✅

**输入**：30V 输入，输出 12V、6A 的车规级 DC-DC，工作温度 -40°C 到 125°C，优先国产方案和低供应风险。  
**耗时**：1ms  

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

**候选评分明细**（共 3 个）：

| # | 型号 | 厂商 | 国产 | 车规 | 总分 | 参数 | 供应 | 成本 | 国产 | 证据 | 推荐等级 |
|---|------|------|------|------|------|------|------|------|------|------|----------|
| 1 | MOCK-BUCK-AEC-003 | MockSemi | 🇨🇳 | 🚗 | **95** | 83 | 100 | 100 | 100 | 100 | ⭐ recommended |
| 2 | MOCK-BUCK-015 | NanoPower | 🇨🇳 | 🚗 | **95** | 83 | 100 | 95 | 100 | 100 | ⭐ recommended |
| 3 | IMPORT-BUCK-007 | OverseaChip | 🌍 | 🚗 | **54** | 83 | 70 | 0 | 0 | 100 | 🟡 backup |

**TOP1 评分原因**：
- 输入电压覆盖 ✓（9.0–16.0V 含标称 12.0V）
- 输出电流满足 ✓（6.0A，余量 0%）
- 温度范围覆盖 ✓（-40.0–125.0°C）
- 库存充足（3000 件）
- 生命周期：在产
- 单价 9.0 元（较低）
- 国产器件 ✓（MockSemi）
- 有数据手册

**证据链**（共 15 条）：

| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |
|------|----------|------|--------|--------|
| MOCK-BUCK-AEC-003 | `mock_ezplm_field` | supports temperature range -40.0C to 125.0C | 95% |  |
| MOCK-BUCK-AEC-003 | `mock_ezplm_field` | input voltage range 9.0V to 16.0V | 95% |  |
| MOCK-BUCK-AEC-003 | `mock_ezplm_field` | output current max 6.0A | 90% |  |
| MOCK-BUCK-AEC-003 | `mock_ezplm_field` | stock 3000 | 90% |  |
| MOCK-BUCK-AEC-003 | `mock_ezplm_field` | lifecycle active | 90% |  |
| MOCK-BUCK-015 | `mock_ezplm_field` | supports temperature range -40.0C to 125.0C | 95% |  |
| MOCK-BUCK-015 | `mock_ezplm_field` | input voltage range 12.0V to 36.0V | 95% |  |
| MOCK-BUCK-015 | `mock_ezplm_field` | output current max 6.0A | 90% |  |
| MOCK-BUCK-015 | `mock_ezplm_field` | stock 1800 | 90% |  |
| MOCK-BUCK-015 | `mock_ezplm_field` | lifecycle active | 90% |  |
| ... | ... | _(共 15 条，仅展示前 10 条)_ | ... | ... |

**风险评估**：⚪ low


---


*报告由 `tests/eval_runner.py` 自动生成，IR version: 0.1*
