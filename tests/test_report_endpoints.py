"""`GET /report/{report_type}` 契约测试（3.9）。

## 为什么单独建这个文件

3.9 的缺陷在前端（渲染被删、`session_id` 没传），但**根因是前端与后端的契约没有被
任何用例钉住**：前端少传一个 query 参数，后端不报错、而是**静默退回「默认会话」**，
于是「点 `/risk` 什么都不显示」和「显示了别的会话的报告」这两类问题都不会让测试变红。

所以这里把端点契约本身固定下来，重点是三条**静默**行为：

1. 未选器件 → 400（不是 200 空内容，也不是 500）；
2. 已选器件但无报告 → 404；
3. **不带 `session_id` 时读到的是「默认会话」**——`_sid(user, None)` 会把
   `None` 换成 `_DEFAULT_SESSION_ID`。这一条是这个文件存在的首要理由：它不是
   缺陷（默认会话是设计内的），但它是**前端漏传参数时的静默失败点**，必须有用例
   把它显式写出来，否则下次谁把它「顺手改成报错」或「顺手改成读最新会话」都不会
   有人察觉；而 3.9 的修复正好依赖「带上 session_id 就能读到正确的会话」。

隔离：全部进程内。用**游客令牌**（`is_guest`）而不是真实用户令牌——`GuestUser`
不查数据库，于是这条用例既不碰生产库也不需要造用户。会话态直接注入
`app.main._session_*` 三个字典，用完还原。
"""

import pytest
from fastapi.testclient import TestClient

from app.auth import create_access_token
from app.main import (
    _DEFAULT_SESSION_ID,
    _session_constraints,
    _session_reports,
    _session_selected_part,
    _sid,
    app,
)
from app.schemas import (
    PartIR,
    RequirementConstraints,
    ScoreBreakdown,
    ScoredPart,
    SelectionReport,
)

_SCOPE = "test-report-3.9-guest"
_PN = "TPS54331"


def _guest_headers(scope: str = _SCOPE) -> dict:
    """签一个游客令牌。游客不查库，所以这条链路完全不依赖数据库。"""
    token = create_access_token({"sub": scope, "is_guest": True})
    return {"Authorization": f"Bearer {token}"}


class _Guest:
    """只用于复算 `_sid` 的会话键，与 `GuestUser` 的 scope 取值保持一致。"""

    def __init__(self, scope: str) -> None:
        self.session_scope = scope


def _sample_report() -> SelectionReport:
    """一份最小但字段完整的报告：够三个生成器跑出 Markdown 即可。"""
    scored = ScoredPart(
        part=PartIR(part_number=_PN, manufacturer="TI", category="buck"),
        score=ScoreBreakdown(total_score=88.0),
        rank=1,
    )
    return SelectionReport(
        request_id="req-3.9",
        user_input="12V 转 5V 3A",
        constraints=RequirementConstraints(raw_input="12V 转 5V 3A", topology="buck"),
        candidates=[scored],
        recommended_parts=[scored],
    )


@pytest.fixture
def report_client():
    """注入会话态并在用例结束后还原，避免污染同进程内其它用例。"""
    client = TestClient(app)
    saved = (_session_reports.copy(), _session_constraints.copy(), _session_selected_part.copy())
    yield client
    for d, snapshot in zip(
        (_session_reports, _session_constraints, _session_selected_part), saved
    ):
        d.clear()
        d.update(snapshot)
    client.close()


def _seed(sid: str, *, selected: bool = True, report: bool = True) -> None:
    """按需注入「已选器件」与「有报告」两个条件。"""
    if selected:
        _session_selected_part[sid] = _PN
    if report:
        _session_reports[sid] = _sample_report()
        _session_constraints[sid] = RequirementConstraints(
            raw_input="12V 转 5V 3A", topology="buck"
        )


# ── 正常路径 ────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("report_type", ["bom", "risk", "topology"])
def test_report_returns_markdown_for_each_type(report_client, report_type):
    """三类报告都能生成：200 + 非空 Markdown + type 回显。"""
    sid = _sid(_Guest(_SCOPE), "sess-ok")
    _seed(sid)

    r = report_client.get(
        f"/report/{report_type}", params={"session_id": "sess-ok"}, headers=_guest_headers()
    )

    assert r.status_code == 200, r.text
    body = r.json()
    assert body["type"] == report_type
    assert isinstance(body["content"], str) and body["content"].strip(), "报告内容为空"


# ── 两条失败路径 ────────────────────────────────────────────────────────────

def test_report_without_selected_part_is_400(report_client):
    """未选器件 → 400，且文案要指出「先回编号选器件」。"""
    sid = _sid(_Guest(_SCOPE), "sess-noselect")
    _seed(sid, selected=False, report=True)

    r = report_client.get(
        "/report/risk", params={"session_id": "sess-noselect"}, headers=_guest_headers()
    )

    assert r.status_code == 400, r.text
    assert "请先选择具体器件" in r.json()["detail"]


def test_report_without_analysis_is_404(report_client):
    """已选器件但该会话还没跑过分析 → 404。"""
    sid = _sid(_Guest(_SCOPE), "sess-noreport")
    _seed(sid, selected=True, report=False)

    r = report_client.get(
        "/report/risk", params={"session_id": "sess-noreport"}, headers=_guest_headers()
    )

    assert r.status_code == 404, r.text


def test_unknown_report_type_is_400(report_client):
    sid = _sid(_Guest(_SCOPE), "sess-badtype")
    _seed(sid)

    r = report_client.get(
        "/report/nonsense", params={"session_id": "sess-badtype"}, headers=_guest_headers()
    )

    assert r.status_code == 400, r.text


# ── 本文件的首要理由：默认会话这个静默失败点 ─────────────────────────────────

def test_missing_session_id_reads_default_session(report_client):
    """**不带 `session_id` 读到的是「默认会话」**，不是「当前会话」也不是报错。

    这正是 3.9 那个缺陷的形态：`PdfReportViewer` 原先不带 query，于是报告属于
    默认会话。前端修好之后仍要保留这条断言——它说明「带与不带 session_id 是两
    个不同的会话」，从而保证前端那次修复不是无效的。
    """
    default_sid = _sid(_Guest(_SCOPE), None)
    assert default_sid.endswith(_DEFAULT_SESSION_ID)
    _seed(default_sid)

    # 不带 session_id：读到默认会话的报告
    r = report_client.get("/report/risk", headers=_guest_headers())
    assert r.status_code == 200, r.text
    assert r.json()["content"].strip()

    # 带一个**没注入过**的 session_id：读不到默认会话的东西，必须是 400
    r2 = report_client.get(
        "/report/risk", params={"session_id": "some-other-session"}, headers=_guest_headers()
    )
    assert r2.status_code == 400, (
        "带 session_id 却读到了默认会话的内容——`_sid` 的绑定失效了"
    )


# ── 会话归属隔离（`_sid` 存在的理由）────────────────────────────────────────

def test_another_users_session_is_not_readable(report_client):
    """别的用户/游客拿同一个 session_id 也读不到——`_sid` 把会话键绑到 owner 上。"""
    sid_a = _sid(_Guest(_SCOPE), "shared-id")
    _seed(sid_a)

    r = report_client.get(
        "/report/risk", params={"session_id": "shared-id"}, headers=_guest_headers("another-scope")
    )

    assert r.status_code == 400, "跨用户读到了别人的选型报告"
