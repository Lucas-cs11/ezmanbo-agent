"""原理图生成测试（B2）

合并自两个名字与内容错配的旧文件：
* `test_b2_api.py` —— 里面装的其实是 `/schematic/{topology}` 端点测试；
* `test_b2_schematic.py` —— 直接调纯函数 `generate_schematic`。

两边的断言全部保留，并补上了原先缺失的一处：旧 `test_error_handling` 在
「本该抛异常却没抛」时只是 `print("[FAIL] ...")` 而**没有断言**，无论对错都算通过。
现在改成 `pytest.raises(ValueError)`。

本文件全部是隔离用例（`/schematic/{topology}` 无鉴权，底层是纯函数），留在默认集。
"""

import re

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schematic_generator import generate_schematic

# (topology, Vin, Vout, Iout, 说明)
_TOPOLOGIES = [
    ("buck", 12, 5, 3, "Buck 12V->5V @ 3A"),
    ("boost", 5, 12, 2, "Boost 5V->12V @ 2A"),
    ("ldo", 12, 3.3, 1, "LDO 12V->3.3V @ 1A"),
]

_SVG_SIZE_FLOOR = 1000


@pytest.fixture
def schematic_client():
    return TestClient(app)


# ── 纯函数层 ────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("topology,vin,vout,iout,desc", _TOPOLOGIES, ids=[t[4] for t in _TOPOLOGIES])
def test_generate_schematic_all_topologies(topology, vin, vout, iout, desc):
    """三种拓扑都能生成合法的 SVG。"""
    svg = generate_schematic(topology, vin, vout, iout)

    assert isinstance(svg, str), f"期望 str，实际 {type(svg)}"
    assert "<svg" in svg, "SVG tag missing"
    assert len(svg) > _SVG_SIZE_FLOOR, f"SVG too small: {len(svg)} chars"


def test_generate_schematic_buck_labels_calculated_values():
    """Buck 的 SVG 标签里必须带上算出来的电感/电容值。"""
    svg = generate_schematic("buck", 12, 5, 3)

    assert "uH" in svg, "Inductance not in SVG"
    assert "uF" in svg, "Capacitance not in SVG"


def test_generate_schematic_invalid_topology_raises():
    """非法拓扑必须抛 ValueError，而不是悄悄返回一张图。"""
    with pytest.raises(ValueError):
        generate_schematic("invalid", 12, 5, 3)


# ── HTTP 端点层 ─────────────────────────────────────────────────────────────


@pytest.mark.parametrize("topology,vin,vout,iout,desc", _TOPOLOGIES, ids=[t[4] for t in _TOPOLOGIES])
def test_schematic_endpoint_returns_svg(schematic_client, topology, vin, vout, iout, desc):
    """`GET /schematic/{topology}` 返回 SVG，且体积合理。"""
    response = schematic_client.get(
        f"/schematic/{topology}", params={"Vin": vin, "Vout": vout, "Iout": iout}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/svg+xml", (
        f"Content-Type: {response.headers.get('content-type')}"
    )

    svg_content = response.text
    assert "<svg" in svg_content, "SVG tag missing"
    assert len(svg_content) > _SVG_SIZE_FLOOR, f"SVG too small: {len(svg_content)}"


@pytest.mark.parametrize("topology,vin,vout,iout,desc", _TOPOLOGIES, ids=[t[4] for t in _TOPOLOGIES])
def test_schematic_endpoint_matches_pure_function(schematic_client, topology, vin, vout, iout, desc):
    """端点返回的就是 `generate_schematic` 的输出，中间不能有静默改写。

    注意要传 float：端点的查询参数声明为 `float`，而 `generate_schematic` 对
    int / float 输入会算出**不同**的几何尺寸（例如 Vin=12 与 12.0 得到不同宽度）。
    这是当前实现的既有行为，此处按端点的真实入参类型来比对。
    """
    response = schematic_client.get(
        f"/schematic/{topology}", params={"Vin": vin, "Vout": vout, "Iout": iout}
    )
    assert response.status_code == 200
    assert response.text == generate_schematic(
        topology, float(vin), float(vout), float(iout)
    )


def test_schematic_endpoint_invalid_topology_returns_400(schematic_client):
    """非法拓扑应返回 400。"""
    response = schematic_client.get(
        "/schematic/invalid", params={"Vin": 12, "Vout": 5, "Iout": 3}
    )
    assert response.status_code == 400, f"Expected 400, got {response.status_code}"


# ── 公网端点的资源边界（2026-09-27，ROADMAP 2.8）────────────────────────────
#
# 这个端点公开、无鉴权，前端以不带令牌的 fetch 取用（`SchematicPanel.tsx`），
# 所以它必须自己带上限。下面几条钉的是**性质**而不是"机制存在"：参数窗口真的挡住了
# 溢出、绘图真的跑在专用池的线程上、在途名额满了真的会拒、缓存真的按精确参数命中、
# 失败真的不回显异常。


def _label_texts(svg: str) -> str:
    """把 SVG 里的文本节点内容拼起来，用于检查标尺/标签。

    不能直接在整份 SVG 里搜 "nan"：`dominant-baseline` 这个属性名本身就含 "nan"，
    那样每次都会误报。真正的垃圾标签长这样：`<tspan ...>L=-infuH</tspan>`。
    """
    return "\n".join(re.findall(r"<text[^>]*>(.*?)</text>", svg, re.S))


@pytest.mark.parametrize(
    "params,desc",
    [
        ({"Vin": 0, "Vout": 5, "Iout": 2}, "Vin=0（原实现是 division by zero → 500）"),
        ({"Vin": 12, "Vout": 5, "Iout": 0}, "Iout=0（原实现是 division by zero → 500）"),
        ({"Vin": -12, "Vout": 5, "Iout": 2}, "负输入电压"),
        ({"Vin": 12, "Vout": -5, "Iout": 2}, "负输出电压"),
        ({"Vin": 12, "Vout": 5, "Iout": -2}, "负输出电流"),
        ({"Vin": "nan", "Vout": 5, "Iout": 2}, "NaN"),
        ({"Vin": "inf", "Vout": 5, "Iout": 2}, "Infinity"),
        ({"Vin": 12, "Vout": 5, "Iout": "inf"}, "Infinity（出现在 Iout）"),
    ],
)
def test_schematic_rejects_invalid_params(schematic_client, params, desc):
    """非有限或非正的参数必须在进绘图之前被拒（422），不能变成 500。"""
    response = schematic_client.get("/schematic/buck", params=params)

    assert response.status_code == 422, (
        f"{desc}: 期望 422，实际 {response.status_code} —— {response.text[:160]}"
    )
    assert "division by zero" not in response.text
    assert "Traceback" not in response.text


@pytest.mark.parametrize(
    "params,desc",
    [
        ({"Vin": 1e-9, "Vout": 5, "Iout": 2}, "Vin 低于窗口下界（会让 D=Vout/Vin 溢出）"),
        ({"Vin": 1e7, "Vout": 5, "Iout": 2}, "Vin 高于窗口上界"),
        ({"Vin": 12, "Vout": 1e-9, "Iout": 2}, "Vout 低于下界"),
        ({"Vin": 12, "Vout": 5, "Iout": 1e-9}, "Iout 低于下界"),
        ({"Vin": 12, "Vout": 5, "Iout": 1e9}, "Iout 高于上界"),
    ],
)
def test_schematic_rejects_out_of_window_params(schematic_client, params, desc):
    """窗口外的参数直接 422 —— 它们会把派生量（比值/乘积）推到浮点范围外。"""
    response = schematic_client.get("/schematic/buck", params=params)

    assert response.status_code == 422, (
        f"{desc}: 期望 422，实际 {response.status_code} —— {response.text[:160]}"
    )


@pytest.mark.parametrize("topology", ["buck", "boost", "ldo"])
def test_schematic_window_corners_produce_finite_labels(schematic_client, topology):
    """窗口的角点必须产出**有限**的标签 —— 这是设这个窗口的唯一理由。

    实测（2026-09-27）：窗口外 `buck?Vin=1e-308` 会画出 `L=-infuH`，
    `buck?Iout=1e-308` 会画出 `L=infuH` 与 `infOhm`：图照出，标尺是垃圾。
    所以这里逐个走窗口的极端组合，断言没有 inf/nan 标签溜进图里 —— 测的是
    「边界真的成立」，而不只是「有个边界参数」。

    窗口的上下界**取自模块常量**而不是写死：这样把窗口放宽（例如改回 1e-308）会
    让这条直接变红，而不是悄悄地又把垃圾图放回来。
    """
    from app import main as app_main

    lo, hi = app_main.SCHEMATIC_PARAM_MIN, app_main.SCHEMATIC_PARAM_MAX
    corners = [
        (lo, lo, lo), (lo, hi, hi), (hi, lo, lo), (hi, hi, hi),
        (lo, hi, lo), (hi, lo, hi), (1.0, hi, lo), (lo, 1.0, hi),
    ]

    for vin, vout, iout in corners:
        response = schematic_client.get(
            f"/schematic/{topology}",
            params={"Vin": vin, "Vout": vout, "Iout": iout},
        )

        assert response.status_code == 200, (
            f"{topology} Vin={vin:g} Vout={vout:g} Iout={iout:g}: "
            f"窗口内参数不该被拒，实际 {response.status_code}"
        )
        labels = _label_texts(response.text)
        assert not re.search(r"inf|nan", labels, re.I), (
            f"{topology} Vin={vin:g} Vout={vout:g} Iout={iout:g}: "
            f"标签里出现了 inf/nan —— {labels[:200]}"
        )


def test_schematic_render_runs_on_dedicated_pool_threads(monkeypatch):
    """绘图必须跑在专用池的 `schematic_*` 线程上，而不是调用方（事件循环）线程。

    这一条**刻意只断言线程名，不断言并发峰值**。原因是 2026-09-27 独立验收指出的：
    本测试用 4 个各自独立事件循环的 TestClient，于是「同步直呼」和「池无上限」两种
    故障都会给出峰值 4，峰值在这里分不开；线程名才是「确实挪出了调用方线程」的直接
    证据。并发上限改由 `test_schematic_rejects_when_inflight_is_full` 钉住。
    """
    import threading

    from app import main as app_main

    seen: list[str] = []
    lock = threading.Lock()

    def record_render(topology, vin, vout, iout):
        with lock:
            seen.append(threading.current_thread().name)
        return "<svg xmlns='http://www.w3.org/2000/svg'><rect/></svg>"

    monkeypatch.setattr(app_main, "_render_schematic_cached", record_render)

    results = []
    barrier = threading.Barrier(4)

    def fire():
        client = TestClient(app)
        barrier.wait()  # 尽量让 4 个请求同时到达
        r = client.get("/schematic/buck", params={"Vin": 12, "Vout": 5, "Iout": 2})
        results.append(r.status_code)
        client.close()

    workers = [threading.Thread(target=fire) for _ in range(4)]
    for w in workers:
        w.start()
    for w in workers:
        w.join(timeout=30)

    assert results == [200, 200, 200, 200], f"四个并发请求都应成功，实际 {results}"
    assert len(seen) == 4, f"四次请求应各绘制一次，实际 {len(seen)} 次"
    assert all(name.startswith("schematic") for name in seen), (
        f"绘制应发生在专用池的 schematic_* 线程上，实际 {seen}"
    )


def test_schematic_rejects_when_inflight_is_full(monkeypatch):
    """在途名额满了必须**当场 503**（带 Retry-After），而不是无限排队。

    这是 2.8 最关键的一条：`ThreadPoolExecutor` 的任务队列是无界的，只限并发等于把
    「无界并发」换成「无界排队」——唯一参数洪水仍能积压成持续 CPU 燃烧。

    编排用**事件**而不是 sleep，因此完全确定：先让两个请求占住两个名额并卡在绘图里，
    此时再发两个必然被拒；随后放行，先前两个必须正常完成（名额确实归还、没有泄漏）。
    线程池与名额都换成测试自己的，与生产默认值解耦。
    """
    import threading
    from concurrent.futures import ThreadPoolExecutor

    from app import main as app_main

    release = threading.Event()
    entered = threading.Semaphore(0)

    def blocking_render(topology, vin, vout, iout):
        entered.release()
        assert release.wait(timeout=20), "测试自身的超时保护被触发"
        return "<svg xmlns='http://www.w3.org/2000/svg'><rect/></svg>"

    pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="schematic-test")
    monkeypatch.setattr(app_main, "_render_schematic_cached", blocking_render)
    monkeypatch.setattr(app_main, "_SCHEMATIC_POOL", pool)
    monkeypatch.setattr(app_main, "_SCHEMATIC_INFLIGHT", threading.BoundedSemaphore(2))

    def call():
        client = TestClient(app)
        try:
            return client.get("/schematic/buck", params={"Vin": 12, "Vout": 5, "Iout": 2})
        finally:
            client.close()

    try:
        holders = []
        threads = [
            threading.Thread(target=lambda: holders.append(call())) for _ in range(2)
        ]
        for t in threads:
            t.start()
        assert entered.acquire(timeout=10), "第 1 个请求应已进入绘图"
        assert entered.acquire(timeout=10), "第 2 个请求应已进入绘图"

        overloaded = [call(), call()]
        assert [r.status_code for r in overloaded] == [503, 503], (
            f"名额已满时应拒绝，实际 {[r.status_code for r in overloaded]}"
        )
        assert all(r.headers.get("retry-after") for r in overloaded), (
            "503 必须带 Retry-After，否则客户端不知道何时重试"
        )

        release.set()
        for t in threads:
            t.join(timeout=20)
        assert sorted(r.status_code for r in holders) == [200, 200], (
            f"占住名额的请求应正常完成，实际 {[r.status_code for r in holders]}"
        )
        assert call().status_code == 200, "名额必须被归还，后续请求仍应正常"
    finally:
        release.set()
        pool.shutdown(wait=False)


def test_schematic_pool_and_inflight_follow_config():
    """池的线程数与缓存容量必须真的取自那三个常量，不许各写各的。"""
    from app import main as app_main

    assert app_main.SCHEMATIC_MAX_WORKERS >= 1, "线程数至少为 1"
    assert app_main.SCHEMATIC_MAX_INFLIGHT > app_main.SCHEMATIC_MAX_WORKERS, (
        "在途名额必须大于线程数，否则一点排队余量都没有"
    )
    assert app_main._SCHEMATIC_POOL._max_workers == app_main.SCHEMATIC_MAX_WORKERS, (
        "池的线程数必须来自 SCHEMATIC_MAX_WORKERS"
    )
    assert (
        app_main._render_schematic_cached.cache_info().maxsize
        == app_main.SCHEMATIC_CACHE_SIZE
    ), "缓存的 maxsize 必须来自 SCHEMATIC_CACHE_SIZE"


def test_schematic_render_is_cached_by_exact_params(schematic_client):
    """同一组参数第二次请求必须命中缓存（不重画），且两个响应逐字节相同。"""
    from app.main import _render_schematic_cached

    _render_schematic_cached.cache_clear()
    params = {"Vin": 3.3, "Vout": 1.8, "Iout": 0.5}

    before = _render_schematic_cached.cache_info()
    first = schematic_client.get("/schematic/buck", params=params)
    after_first = _render_schematic_cached.cache_info()
    second = schematic_client.get("/schematic/buck", params=params)
    after_second = _render_schematic_cached.cache_info()

    assert first.status_code == 200 and second.status_code == 200
    assert first.text == second.text, "缓存不能改变输出"
    assert after_first.misses - before.misses == 1, "首次请求应是一次未命中"
    assert after_second.hits - after_first.hits == 1, "第二次相同参数应命中缓存"
    assert after_second.misses - after_first.misses == 0, "第二次不应再重画"


def test_schematic_sets_cache_control(schematic_client):
    """输出只由查询参数决定，应当允许浏览器/CDN 缓存。"""
    response = schematic_client.get(
        "/schematic/buck", params={"Vin": 9, "Vout": 3.3, "Iout": 1}
    )

    assert response.status_code == 200
    assert "max-age" in response.headers.get("cache-control", ""), (
        f"缺 Cache-Control: {response.headers.get('cache-control')}"
    )


def test_schematic_500_does_not_echo_exception(monkeypatch, schematic_client):
    """500 不能把原始异常文本回显出去 —— 这是公网无鉴权端点。"""
    from app import main as app_main

    def boom(topology, vin, vout, iout):
        raise RuntimeError("内部细节: ECHO_MARKER_9f3")

    monkeypatch.setattr(app_main, "_render_schematic_cached", boom)

    response = schematic_client.get(
        "/schematic/buck", params={"Vin": 12, "Vout": 5, "Iout": 3}
    )

    assert response.status_code == 500
    assert "ECHO_MARKER_9f3" not in response.text, "原始异常文本被回显了"
    assert response.json()["detail"] == "电路图生成失败"
