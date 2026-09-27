#!/usr/bin/env python3
"""
B1 SSE 流式输出接口的测试脚本
用于验证 /analyze/stream 端点是否能正常推送 SSE 事件
"""

import requests
import json
import time
from datetime import datetime

# 后端地址
API_URL = "http://localhost:8000"

def test_sse_stream():
    """测试 SSE 流式输出"""
    print("=" * 60)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 开始测试 SSE 流式输出接口")
    print("=" * 60)

    # 测试数据
    payload = {
        "user_input": "我需要一个24V输入的5V/3A的降压器芯片，要求成本低、供应充足"
    }

    try:
        # 发起流式请求
        print(f"\n📤 发送请求到 {API_URL}/analyze/stream")
        print(f"请求体: {json.dumps(payload, ensure_ascii=False)}")
        print("\n📥 接收 SSE 事件流：\n")

        response = requests.post(
            f"{API_URL}/analyze/stream",
            json=payload,
            stream=True,
            timeout=30
        )

        # 检查响应状态
        if response.status_code != 200:
            print(f"❌ 请求失败，状态码: {response.status_code}")
            print(f"响应: {response.text}")
            return False

        # 验证 Content-Type
        content_type = response.headers.get("content-type", "")
        if "text/event-stream" not in content_type:
            print(f"⚠️  Content-Type 不是 text/event-stream: {content_type}")
        else:
            print(f"✅ Content-Type 正确: {content_type}")

        # 解析 SSE 事件
        event_count = 0
        event_types = set()
        start_time = time.time()

        for line in response.iter_lines(decode_unicode=True):
            if not line.strip():
                continue

            if line.startswith("event: "):
                event_type = line[7:].strip()
                event_types.add(event_type)
                event_count += 1
                print(f"\n[事件 #{event_count}] 类型: {event_type}")

            elif line.startswith("data: "):
                try:
                    data = json.loads(line[6:])
                    # 格式化输出（避免输出过长的数据）
                    if event_type == "done":
                        print(f"  ✅ 分析完成 - 耗时: {data.get('elapsed_seconds', '?')}s")
                        if 'report' in data:
                            report = data['report']
                            print(f"  📊 报告摘要:")
                            print(f"     - 候选器件数: {len(report.get('candidates', []))}")
                            print(f"     - 推荐器件数: {len(report.get('recommended_parts', []))}")
                    elif event_type == "error":
                        print(f"  ❌ 错误: {data.get('error', 'Unknown error')}")
                    else:
                        # 打印数据摘要
                        keys = list(data.keys())
                        if 'status' in data:
                            print(f"  └─ {data['status']}")
                        if 'candidate_count' in data:
                            print(f"  └─ 候选数: {data['candidate_count']}")
                        if 'score' in data:
                            print(f"  └─ 评分: {data['score']}")
                        if 'evidence_count' in data:
                            print(f"  └─ 证据条数: {data['evidence_count']}")
                except json.JSONDecodeError as e:
                    print(f"  ⚠️  JSON 解析失败: {e}")

        elapsed = time.time() - start_time

        # 输出测试结果
        print("\n" + "=" * 60)
        print("📋 测试结果摘要")
        print("=" * 60)
        print(f"✅ 接收到 {event_count} 个 SSE 事件")
        print(f"✅ 事件类型: {', '.join(sorted(event_types))}")
        print(f"✅ 总耗时: {elapsed:.2f}s")

        # 验证预期的事件
        expected_events = {"parse_done", "search_done", "score_update", "evidence_done", "risk_done", "text_delta", "done"}
        missing = expected_events - event_types
        if missing:
            print(f"⚠️  缺少事件: {', '.join(sorted(missing))}")
        else:
            print(f"✅ 所有预期事件都已收到")

        return True

    except requests.exceptions.ConnectionError:
        print(f"❌ 无法连接到后端服务 ({API_URL})")
        print("   请确保后端已启动: uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys
    success = test_sse_stream()
    sys.exit(0 if success else 1)
