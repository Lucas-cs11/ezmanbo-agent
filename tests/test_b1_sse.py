"""B1 SSE 流式输出接口测试 —— `/analyze/stream`

这个文件曾经是个「假绿」脚本：用 `requests` 打 `http://localhost:8000`（**生产后端**），
函数 `return True/False` 而没有任何 `assert`。pytest 不检查返回值，所以无论成败都算
通过——实测它打印着「请求失败，状态码 401」却依然 PASS。

现在改成两层：

* **默认集（隔离、不外呼）**：只验证鉴权与请求体校验这两件发生在流水线之前的事。
* ``@pytest.mark.integration``：真正跑通流水线、逐事件断言 SSE 契约。

两层都有真实断言，不再有「没有断言、永远通过」的用例。
"""

import json

import pytest

# SSE 主干事件：不依赖是否有候选器件，任何一次成功的分析都会发出。
# （`score_update` / `text_delta` 只在检索到候选器件时才出现，不能拿来断言。）
_BACKBONE_EVENTS = ["parse_done", "search_done", "evidence_done", "risk_done", "done"]


def _parse_sse(raw_text: str):
    """把 SSE 报文解析成 [(event_name, data_dict), ...]。

    同时校验帧格式：非空行必须是 `event: ` 或 `data: ` 开头。
    格式跑偏会让前端的 EventSource 静默失效，所以这里要硬断言。
    """
    events = []
    current_event = None
    pending_data = []

    for line in raw_text.splitlines():
        if not line.strip():
            # 空行 = 一个事件的结束
            if current_event is not None:
                payload = "\n".join(pending_data)
                try:
                    parsed = json.loads(payload) if payload else {}
                except json.JSONDecodeError:
                    parsed = {"__raw__": payload}
                events.append((current_event, parsed))
            current_event, pending_data = None, []
            continue

        assert line.startswith("event: ") or line.startswith("data: "), (
            f"SSE 帧格式非法：{line!r}"
        )

        if line.startswith("event: "):
            current_event = line[len("event: "):].strip()
        else:
            pending_data.append(line[len("data: "):])

    if current_event is not None:
        payload = "\n".join(pending_data)
        try:
            parsed = json.loads(payload) if payload else {}
        except json.JSONDecodeError:
            parsed = {"__raw__": payload}
        events.append((current_event, parsed))

    return events


# ── 默认集：鉴权与请求体校验（流水线之前）────────────────────────────────────


def test_stream_requires_auth(client):
    """未鉴权访问 /analyze/stream 必须被挡下 —— 这正是旧脚本里那次 401。"""
    response = client.post("/analyze/stream", json={"user_input": "Buck 12V转5V"})
    assert response.status_code == 401


def test_stream_rejects_missing_user_input(member_client):
    """缺少 user_input：请求体校验先于流水线，应为 422。"""
    response = member_client.post("/analyze/stream", json={})
    assert response.status_code in [400, 422]


def test_stream_rejects_malformed_json(member_client):
    """畸形 JSON 应被挡下，而不是进入流水线。"""
    response = member_client.post(
        "/analyze/stream",
        content=b"{not valid json",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code in [400, 422]


# ── integration：真正跑通流水线，逐事件断言 SSE 契约 ─────────────────────────


@pytest.mark.integration
def test_sse_stream_event_contract(member_client):
    """跑通一次真实分析，断言 SSE 的响应头、帧格式与主干事件序列。"""
    payload = {
        "user_input": "我需要一个24V输入的5V/3A的降压器芯片，要求成本低、供应充足"
    }

    response = member_client.post("/analyze/stream", json=payload)

    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")

    events = _parse_sse(response.text)
    assert events, "没有收到任何 SSE 事件"

    names = [name for name, _ in events]

    # 主干事件必须全部出现（顺序按流水线阶段推进）
    for expected in _BACKBONE_EVENTS:
        assert expected in names, (
            f"SSE 流里缺少主干事件 {expected!r}；实际收到：{names}"
        )

    positions = [names.index(e) for e in _BACKBONE_EVENTS]
    assert positions == sorted(positions), (
        f"主干事件顺序错乱：{list(zip(_BACKBONE_EVENTS, positions))}"
    )

    # 不应出现 error 事件
    assert "error" not in names, (
        f"SSE 流里出现了 error 事件：{[d for n, d in events if n == 'error']}"
    )


@pytest.mark.integration
def test_sse_done_event_reports_a_real_summary(member_client):
    """done 事件必须带着完整的分析结果摘要，而不是空壳。"""
    response = member_client.post(
        "/analyze/stream", json={"user_input": "Buck 12V转5V"}
    )
    assert response.status_code == 200

    events = _parse_sse(response.text)
    done_payloads = [data for name, data in events if name == "done"]
    assert done_payloads, "SSE 流没有以 done 事件收尾"

    done = done_payloads[-1]
    assert done.get("status") == "分析完成"
    assert isinstance(done.get("elapsed_s"), (int, float))
    assert done["elapsed_s"] >= 0
    assert done.get("request_id")

    # 计数必须是非负整数，且与返回的列表长度自洽
    assert isinstance(done.get("candidate_count"), int)
    assert done["candidate_count"] >= 0
    assert isinstance(done.get("recommended_count"), int)
    assert done["recommended_count"] >= 0
    assert done["recommended_count"] <= done["candidate_count"]

    assert isinstance(done.get("candidates"), list)
    assert len(done["candidates"]) == done["candidate_count"]
