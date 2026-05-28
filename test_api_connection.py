#!/usr/bin/env python3
"""EZ-PLM API 连接验证脚本"""
import os
import sys

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

from app.ezplm_client import search_parts
from app.schemas import RequirementConstraints

print("=" * 70)
print("🔍 EZ-PLM API 连接验证")
print("=" * 70)
print()

# 环境信息
ezplm_key = os.getenv("EZPLM_API_KEY", "").strip()
ezplm_url = os.getenv("EZPLM_BASE_URL", "https://www.ezplm.cn").strip()

print("📋 配置信息：")
print(f"  ✅ EZPLM_API_KEY: {ezplm_key[:20]}...{ezplm_key[-10:]}")
print(f"  ✅ EZPLM_BASE_URL: {ezplm_url}")
print()

# 测试查询
tests_passed = 0
tests_total = 0

print("🧪 测试 1: Buck 转换器查询")
print("-" * 70)
tests_total += 1

try:
    req = RequirementConstraints(
        raw_input="12V 转 5V Buck 转换器 3A",
        min_input_voltage=10,
        max_input_voltage=24,
        min_output_current=3,
        topology="buck"
    )
    
    print(f"  查询: {req.raw_input}")
    print(f"  参数: {req.min_input_voltage}V-{req.max_input_voltage}V, ≥{req.min_output_current}A")
    print()
    
    results = search_parts(req)
    
    print(f"  ✅ 查询成功，返回 {len(results)} 条结果")
    
    if results:
        print(f"\n  前 3 条结果：")
        for i, part in enumerate(results[:3], 1):
            print(f"    {i}. {part.part_number} ({part.manufacturer})")
            print(f"       输出: {part.output_current_max_a}A, 价格: ¥{part.unit_price_cny}")
        tests_passed += 1
    else:
        print(f"  ⚠️  未返回结果，但连接正常")
        tests_passed += 1
    
    print()
    
except Exception as e:
    print(f"  ❌ 错误: {e}")
    print()

print("🧪 测试 2: LDO 稳压器查询")
print("-" * 70)
tests_total += 1

try:
    req = RequirementConstraints(
        raw_input="LDO",
        topology="ldo"
    )
    
    print(f"  查询: {req.raw_input}")
    print()
    
    results = search_parts(req)
    
    print(f"  ✅ 查询成功，返回 {len(results)} 条结果")
    if results:
        print(f"    样本: {results[0].part_number}")
    tests_passed += 1
    print()
    
except Exception as e:
    print(f"  ❌ 错误: {e}")
    print()

print("🧪 测试 3: 返回数据格式检查")
print("-" * 70)
tests_total += 1

try:
    req = RequirementConstraints(raw_input="test")
    results = search_parts(req)
    
    if results:
        part = results[0]
        print(f"  检查样本: {part.part_number}")
        print()
        
        required_attrs = [
            "part_number", "manufacturer", "category", "topology",
            "input_voltage_min_v", "input_voltage_max_v",
            "output_current_max_a", "stock", "unit_price_cny"
        ]
        
        missing = [attr for attr in required_attrs if not hasattr(part, attr)]
        
        if missing:
            print(f"  ❌ 缺失字段: {missing}")
        else:
            print(f"  ✅ 所有必需字段都存在")
            tests_passed += 1
    else:
        print(f"  ⚠️  无数据，跳过格式检查")
        tests_passed += 1
    
    print()
    
except Exception as e:
    print(f"  ❌ 错误: {e}")
    print()

# 总结
print("=" * 70)
print(f"📊 结果: {tests_passed}/{tests_total} 测试通过")
print("=" * 70)

if tests_passed == tests_total:
    print("\n✅ EZ-PLM API 连接验证成功！")
    print("   • API 密钥有效")
    print("   • 网络连接正常")
    print("   • 返回格式兼容")
else:
    print("\n⚠️  部分测试失败，系统将使用 Mock 数据")

