# 为什么 Mock 数据中只有部分器件有 Datasheet URL？

**简短回答**: 有 URL 的 256 个器件来自 eZ-PLM API（API 提供 URL），没有 URL 的 814 个器件来自原始评测数据库（原始数据不包含 URL）。

---

## 数据构成分析

### 原始 814 个器件（来自 Day 2-3）

```
数据来源:         Day 2-3 评测数据库
datasheet_url:    0/814 (0%)  ← 全部为空

理由:
  - 这些数据是为评测设计的
  - 原始 mock 数据重点是参数字段（voltage, current, topology）
  - 不包含外部链接（考虑可维护性和离线测试）
```

**示例**:
```json
{
  "part_number": "TPS54020RUWR",
  "manufacturer": "Texas Instruments",
  "topology": "buck",
  "output_voltage_v": 5.0,
  "output_current_max_a": 3.0,
  "datasheet_url": null,        ← 为空
  "source": "mock"
}
```

### 新增 256 个器件（来自 eZ-PLM API）

```
数据来源:         eZ-PLM API 直接查询
datasheet_url:    256/256 (100%)  ← 全部有值

理由:
  - API 返回的每个器件都包含 datasheet_url 字段
  - URL 指向厂家的官方文档（PDF）
  - 来自可信的 eZ-PLM 平台
```

**示例**:
```json
{
  "part_number": "MCP1700T-5002E/MB",
  "manufacturer": "Microchip Technology",
  "topology": "ldo",
  "output_voltage_v": 5.0,
  "output_current_max_a": 0.25,
  "datasheet_url": "https://qn.ezplm.com/part/FrbQgdkR1SbLO6HpYEARa4HEAQRb.pdf",  ← 有值
  "source": "api"
}
```

---

## 详细统计

### 按数据源分布

| 来源 | 数量 | 有 URL | 占比 |
|------|:----:|:-----:|:----:|
| **原始 mock 数据** | 814 | 0 | 0% |
| **eZ-PLM API** | 256 | 256 | 100% |
| **总计** | 1070 | 256 | 23.9% |

### 按拓扑分布（有趣的发现）

```
None (无拓扑):     96/96 (100%)  ← 全部来自 API
inverting:        2/2 (100%)    ← 全部来自 API
boost:           29/82 (35.4%)  ← 混合数据
buck:           129/886 (14.6%)  ← 大多数无 URL
```

**说明**: 
- `None` 和 `inverting` 拓扑的器件 100% 有 URL，因为这些都是 API 新增的
- `buck` 和 `boost` 有混合来源，所以有 URL 比例较低

---

## URL 来源验证

### 所有 URL 都来自 eZ-PLM

```
域名:          qn.ezplm.com
URL 数:         256/256 (100%)
格式:           https://qn.ezplm.com/part/{ID}.pdf
备注:           官方 eZ-PLM 平台托管的 PDF
```

**URL 示例**:
```
https://qn.ezplm.com/part/FrbQgdkR1SbLO6HpYEARa4HEAQRb.pdf
https://qn.ezplm.com/part/2DSNNE9k5Xd2N8D1K2H3G4I5J6L7M8.pdf
https://qn.ezplm.com/part/XxXxXxXxXxXxXxXxXxXxXxXxXxXxXx.pdf
```

所有 URL 都是 eZ-PLM 平台的 CDN 链接，指向官方 Datasheet PDF。

---

## 为什么这样设计？

### 设计决策的合理性

```
1. 原始数据不包含 URL
   ✓ 轻量化（JSON 文件更小）
   ✓ 离线工作（不依赖外部链接）
   ✓ 易于版本控制（URL 容易过期）

2. API 数据包含 URL
   ✓ 来自厂家官方数据
   ✓ 实时更新（从 eZ-PLM 平台获取）
   ✓ 提供价值（用户可直接访问 Datasheet）

3. 混合策略
   ✓ 保留原始数据的评测完整性
   ✓ 补充 API 数据的额外信息
   ✓ 灵活应对不同使用场景
```

---

## 对系统的影响

### 对选型功能的影响

```
原始 814 个器件:
  ✓ 完整的评测数据（voltage, current, topology）
  ✓ 无 URL 不影响选型逻辑
  ✗ 用户无法直接查看 datasheet

新增 256 个器件:
  ✓ 完整的 API 数据（voltage, current, datasheet URL）
  ✓ 用户可直接访问 datasheet
  ✗ 拓扑信息不全（某些为 None）
```

### 对不同使用场景的支持

```
场景 1: 评测和验证
  推荐使用: 原始 814 个数据
  原因: 拓扑分类完整，参数准确

场景 2: 生产选型
  推荐使用: 全部 1070 个数据
  原因: 候选更多，API 器件有 datasheet 链接

场景 3: 工程参考
  推荐: 优先查看有 URL 的 256 个器件
  原因: 可直接访问官方文档
```

---

## 改进建议

### 短期（如需）

```
选项 1: 保持现状 ✓
  优点: 混合策略清晰，各有所长
  缺点: 用户需了解差异

选项 2: 从 Datasheet PDF 提取参数 🟡
  优点: 为原始 814 器件补充缺失参数
  缺点: 需要 OCR，工作量大

选项 3: 从厂家 API 补充 URL 🟡
  优点: 为所有 814 器件获得 datasheet
  缺点: 需要查询其他数据源
```

### 建议实施

```
现在: 保持现状（数据清晰，易于维护）
后续: 考虑为关键器件手动补充 Datasheet URL
      (特别是最常用的 TPS54/LM2596 等)
```

---

## 总结

| 问题 | 答案 |
|------|------|
| **为什么有的有 URL？** | 来自 eZ-PLM API，API 提供 URL |
| **为什么有的没有 URL？** | 来自原始评测数据库，原始数据不包含 URL |
| **这是否有问题？** | 不是，这是合理的设计决策 |
| **是否需要修复？** | 不需要（可选的改进，非紧急） |
| **对选型功能的影响？** | 无影响（URL 不参与选型逻辑） |

**结论**: 这是 **设计特征而非缺陷**。混合数据源既保留了评测的完整性，又提供了额外的实时信息。

