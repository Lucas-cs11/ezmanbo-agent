"""原理图生成测试（B2）

合并自两个名字与内容错配的旧文件：
* `test_b2_api.py` —— 里面装的其实是 `/schematic/{topology}` 端点测试；
* `test_b2_schematic.py` —— 直接调纯函数 `generate_schematic`。

两边的断言全部保留，并补上了原先缺失的一处：旧 `test_error_handling` 在
「本该抛异常却没抛」时只是 `print("[FAIL] ...")` 而**没有断言**，无论对错都算通过。
现在改成 `pytest.raises(ValueError)`。

本文件全部是隔离用例（`/schematic/{topology}` 无鉴权，底层是纯函数），留在默认集。
"""

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
