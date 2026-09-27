"""B4 集成测试：语义缓存与 `agent_orchestrator` / `main.py` 的接线

这个文件曾经也是「假绿」：两个 `test_*` 函数 `return True/False`，而 pytest 不检查
返回值，所以无论成败都算通过。现在全部改成真实断言，并统一打 `@pytest.mark.integration`
——它们要真正跑通选型流水线（真 eZ-PLM + LLM）。

两处刻意的改动（都是**修正陈旧断言**，不是放宽）：

1. 缓存实例改由 `isolated_semantic_cache` 提供。原先断言 `cache.count == 0`，
   依赖「全局单例是空的」这个前提；而单例现在是会话级共享的，别的用例会污染它。
   这里用 `monkeypatch` 把 orchestrator / main 取缓存的那条路径指向独占实例。
2. `X-Cache` 的契约已经变了，旧断言与当前实现不符：
   * `/analyze`（非流式）**固定返回 `MISS`** —— 源码注释写明「原始文本的语义命中
     不算有效的选型报告缓存命中」，所以非流式路径每次都真跑流水线。
   * `/analyze/stream` 返回 **`DEFERRED`** —— 权威的命中信息由流内的 `cache_hit`
     事件给出，响应头只是占位。
   继续断言 `HIT` 只会是错的。

历史注意：这里曾经无条件 `shutil.rmtree("data/chroma_cache")`，而本目录同时是
生产运行目录 —— 那一行删掉的是线上语义缓存。已彻底移除，且不会再写回。
缓存目录现在由 tests/conftest.py 统一改道到临时目录。
"""

import pytest

_CACHE_QUERY = "12V to 5V buck converter"


def _point_cache_at(monkeypatch, cache):
    """让所有 `get_semantic_cache()` 的调用方拿到这个独占实例。

    `agent_orchestrator.analyze` 与 `main.py` 都是在函数体内
    `from .semantic_cache import get_semantic_cache`，即调用时才去模块上取属性，
    所以替换模块属性即可生效。
    """
    monkeypatch.setattr(
        "app.semantic_cache.get_semantic_cache", lambda: cache, raising=True
    )


# ── 1. agent_orchestrator 的缓存接线 ─────────────────────────────────────────


@pytest.mark.integration
def test_agent_orchestrator_cache(monkeypatch, isolated_semantic_cache):
    """`analyze()` 必须把结果写进语义缓存，并在第二次调用时命中。"""
    _point_cache_at(monkeypatch, isolated_semantic_cache)

    from app.agent_orchestrator import analyze

    cache = isolated_semantic_cache
    assert cache.count == 0, "独占缓存实例一开始必须是空的"

    report1 = analyze(_CACHE_QUERY)
    assert isinstance(report1, object)
    assert cache.count > 0, "analyze() 跑完必须往缓存里写"
    assert report1.constraints is not None

    # 第二次同样的 query 应当直接命中缓存
    report2 = analyze(_CACHE_QUERY)

    cache_entry = cache.get(_CACHE_QUERY)
    assert cache_entry is not None, "缓存里应当有这条 query"
    assert cache_entry["cache_hit"] is True
    assert cache_entry["similarity"] >= 0.99, (
        f"完全相同的 query 相似度应当接近 1，实际 {cache_entry['similarity']}"
    )

    # 命中缓存返回的就是当初存进去的那份报告，request_id 应当一致
    assert report2.request_id == report1.request_id, (
        "第二次调用没有走缓存：两次 request_id 不同 "
        f"({report1.request_id} != {report2.request_id})"
    )
    assert report2.model_dump() == report1.model_dump()


# ── 2. main.py 端点的接线 ───────────────────────────────────────────────────


@pytest.mark.integration
def test_main_endpoints(monkeypatch, member_client, isolated_semantic_cache):
    """`/health`、`/analyze`、`/analyze/stream` 三个端点的接线与响应头契约。"""
    _point_cache_at(monkeypatch, isolated_semantic_cache)

    # ── /health ──
    health = member_client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    # ── /analyze 首次调用（缓存未命中）──
    query = "Need a 24V to 12V converter"
    response1 = member_client.post("/analyze", json={"user_input": query})
    assert response1.status_code == 200, response1.text[:400]

    # 非流式路径固定 MISS：原始文本的语义命中不算有效的报告缓存命中。
    assert response1.headers.get("X-Cache") == "MISS"

    data1 = response1.json()
    assert data1["user_input"] == query
    assert isinstance(data1["request_id"], str) and data1["request_id"]
    assert isinstance(data1["candidates"], list)
    assert isinstance(data1["constraints"], dict)

    # ── /analyze 再次调用 ──
    response2 = member_client.post("/analyze", json={"user_input": query})
    assert response2.status_code == 200, response2.text[:400]
    assert response2.headers.get("X-Cache") == "MISS"

    data2 = response2.json()

    # 两次的流水线结论必须一致（request_id 每次新建，不参与比较）
    assert data2["constraints"] == data1["constraints"], (
        "同一个 query 两次解析出的约束不一致"
    )
    assert [c.get("part", {}).get("part_number") for c in data2["candidates"]] == [
        c.get("part", {}).get("part_number") for c in data1["candidates"]
    ], "同一个 query 两次检索出的候选器件不一致"

    # ── /analyze/stream（SSE）──
    stream = member_client.post("/analyze/stream", json={"user_input": "LDO 3.3V output 500mA"})
    assert stream.status_code == 200
    assert "text/event-stream" in stream.headers.get("content-type", "")
    # 权威的命中信息在流内，响应头只是 DEFERRED 占位
    assert stream.headers.get("X-Cache") == "DEFERRED"

    body = stream.text
    assert "event:" in body, "SSE 响应里没有任何事件"

    event_names = {
        line[len("event: "):].strip()
        for line in body.splitlines()
        if line.startswith("event: ")
    }
    assert "cache_hit" in event_names, (
        f"SSE 流里缺少 cache_hit 事件，实际收到：{sorted(event_names)}"
    )
    assert "done" in event_names, (
        f"SSE 流没有以 done 收尾，实际收到：{sorted(event_names)}"
    )


def test_main_endpoints_require_auth(client):
    """`/analyze` 与 `/analyze/stream` 都受保护 —— 未鉴权必须 401。

    鉴权校验发生在流水线之前，因此这是个隔离的、快的用例，留在默认集里。
    """
    assert client.post("/analyze", json={"user_input": "x"}).status_code == 401
    assert client.post("/analyze/stream", json={"user_input": "x"}).status_code == 401
