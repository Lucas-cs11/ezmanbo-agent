"""鉴权契约测试 —— 遍历式，防止「给端点加了鉴权却漏改调用方」这类回归重演。

背景：曾经出过一次真实故障——某个端点在服务端加了 `Depends(get_current_user)`，
但调用方（前端/脚本）没有同步带上令牌，于是线上直接 401。逐个端点写用例挡不住
这种问题：新加的端点不会有人想起来补测试。所以这里改成**遍历 `app.routes`**：

1. 递归解析每条路由的依赖图，找出它是否依赖 `get_current_user` / `get_current_admin`；
2. 凡依赖 `get_current_user` 的，不带令牌请求 → 必须 401；
3. 凡依赖 `get_current_admin` 的，带**普通用户**令牌请求 → 必须 403。

并且显式断言「确实扫到了路由」以及「几条关键路由确实在清单里」——否则一旦路由
枚举本身失效（例如 FastAPI 换了内部结构），这个文件会因为一条都没扫到而**静默
全绿**，那正是我们要避免的假绿。

注意：FastAPI 0.141 把 `include_router` 加进来的子路由包成了 `_IncludedRouter`
懒加载对象，`app.routes` 里看不到它们的具体路径，必须经 `original_router` 递归下钻。
不这么做会漏掉 `/auth/*`、`/admin/*`、`/api/setup/*` 等一大片受保护路由。
"""

import re
from pathlib import Path

import pytest

from app.auth import get_current_admin, get_current_user
from app.main import app

# ── 路由遍历 ────────────────────────────────────────────────────────────────

_PATH_PARAM_RE = re.compile(r"\{([^}]+)\}")


def _dependency_calls(dependant, _seen=None):
    """递归收集一个 Dependant 上挂着的所有可调用依赖。"""
    if _seen is None:
        _seen = set()
    if id(dependant) in _seen:
        return []
    _seen.add(id(dependant))

    found = []
    call = getattr(dependant, "call", None)
    if call is not None:
        found.append(call)
    for sub in getattr(dependant, "dependencies", None) or []:
        found.extend(_dependency_calls(sub, _seen))
    return found


def _iter_api_routes(router):
    """递归遍历出所有真正的 API 路由（APIRoute），自动下钻被 include 的子路由。"""
    out = []
    stack = list(getattr(router, "routes", []) or [])
    visited = set()

    while stack:
        route = stack.pop()
        if id(route) in visited:
            continue
        visited.add(id(route))

        cls = type(route).__name__

        # FastAPI >= 0.14x：include_router 进来的是懒加载包装，真身挂在 original_router
        if cls == "_IncludedRouter":
            original = getattr(route, "original_router", None)
            if original is not None:
                stack.extend(getattr(original, "routes", []) or [])
            continue

        # 普通 APIRouter（嵌套 include 的情况）
        if cls == "APIRouter":
            stack.extend(getattr(route, "routes", []) or [])
            continue

        # 静态挂载点 / WebSocket 不是 HTTP API，跳过
        if cls in ("Mount", "WebSocketRoute"):
            continue

        if getattr(route, "path", None) is None:
            continue
        if not hasattr(route, "dependant") or route.dependant is None:
            continue

        out.append(route)

    return out


def _auth_requirements(route):
    """返回 (是否需要普通用户鉴权, 是否需要管理员鉴权)。"""
    calls = _dependency_calls(route.dependant)
    return (get_current_user in calls, get_current_admin in calls)


def _fill_path_params(path: str) -> str:
    """把路径参数填成占位值，避免 404/405 干扰鉴权判定。

    取值本身无关紧要——我们只关心「没带令牌时必须是 401」，所以统一填 "1"。
    """
    return _PATH_PARAM_RE.sub("1", path)


def _request_method(route) -> str:
    methods = sorted((getattr(route, "methods", None) or set()) - {"HEAD", "OPTIONS"})
    assert methods, f"路由 {route.path} 没有可用的 HTTP 方法"
    return methods[0]


def _collect_protected_routes():
    """收集所有受保护路由，产出 pytest 参数。"""
    collected = []
    for route in _iter_api_routes(app):
        needs_user, needs_admin = _auth_requirements(route)
        if not (needs_user or needs_admin):
            continue
        collected.append(
            pytest.param(
                _request_method(route),
                _fill_path_params(route.path),
                needs_admin,
                id=f"{_request_method(route)}-{route.path}",
            )
        )
    return collected


_PROTECTED_ROUTES = _collect_protected_routes()


# 路由枚举必须真的扫到东西。这几条是「绝不能失守」的关键端点，若清单里没有它们，
# 说明枚举逻辑失效了 —— 那就该让测试红，而不是静默通过。
_SENTINEL_ROUTES = {
    "/analyze",
    "/replacement",
    "/analyze/stream",
    "/chat/stream",
    "/auth/me",
    "/api/setup/status",
}

# ── 冻结的受保护路由全清单（不是哨兵，是全量） ───────────────────────────────
#
# 为什么必须**写死**：`_PROTECTED_ROUTES` 是从活着的 `app.routes` 现算出来的。
# 于是「把某条端点的鉴权摘掉」这件事，恰好会让那条路由从清单里**消失** ——
# 没有任何用例会为它运行，测试全绿。也就是说，只靠现算清单，本文件对
# 「摘鉴权」这一类回归**没有拦截力**，只有下面 6 条哨兵和 `len>=20` 兜着。
#
# 独立验收时实测过这一点：把**非哨兵**路由 `/classify` 的 `Depends(get_current_user)`
# 摘掉，结果 121 passed、exit 0，测试毫无反应。
#
# 所以这里把「应当受保护的全部端点」冻结下来逐条比对。代价是新增/删除受保护端点时
# 必须同步改这里 —— 而这恰恰是我们想要的：给端点加鉴权是一个**必须被人看见**的动作，
# 当初的线上事故就是「加了鉴权却没同步更新调用方」，让它变红正是本文件存在的理由。
#
# 维护方式：跑 `pytest --collect-only -q tests/test_auth_contract.py` 看实际清单，
# 与下面比对；若是有意的增删，改这里并在提交信息里说明。
_EXPECTED_PROTECTED = {
    # 管理端（需 get_current_admin）
    "GET-/admin/config",
    "GET-/admin/providers",
    "GET-/admin/rag/docs",
    "GET-/admin/rag/status",
    "GET-/admin/users",
    "GET-/admin/verifier-status",
    "POST-/admin/config",
    "POST-/admin/config/test-verifier",
    "POST-/admin/rag/upload",
    "POST-/admin/users",
    "POST-/admin/users/{user_id}/reset-password",
    "POST-/admin/users/{user_id}/toggle",
    "DELETE-/admin/rag/clear",
    # 选型与工作流主链路
    "POST-/analyze",
    "POST-/analyze/stream",
    "POST-/replacement",
    "POST-/recalculate",
    "POST-/select-part",
    "POST-/interpret-selection",
    "POST-/classify",
    "POST-/workflow/generate",
    "POST-/bom/validate",
    "POST-/export/bom",
    "POST-/export/decision-package",
    "POST-/upload/parse",
    "GET-/report/{report_type}",
    # 会话与聊天
    "POST-/agent/chat",
    "POST-/agent/chat/stream",
    "POST-/agent/init_session",
    "GET-/agent/sessions",
    "POST-/chat/stream",
    # 身份
    "GET-/auth/me",
    "POST-/auth/me/dual-model",
    # 配置与模型管理
    "GET-/api/models",
    "POST-/api/models/switch",
    "GET-/api/permissions",
    "POST-/api/permissions",
    "GET-/api/setup/status",
    "POST-/api/setup/ezplm",
    "POST-/api/setup/provider",
    "POST-/api/setup/test-llm",
    "POST-/api/setup/user-profile",
    "GET-/api/health/full",
}


def _protected_paths():
    return {param.values[1] for param in _PROTECTED_ROUTES}


# ── 契约本体 ────────────────────────────────────────────────────────────────


def test_route_enumeration_finds_protected_routes():
    """防假绿：确认确实扫到了受保护路由，且关键端点都在清单里。"""
    assert _PROTECTED_ROUTES, (
        "没有扫描到任何受保护路由 —— 路由枚举逻辑已失效，"
        "本文件的其余断言都在空跑"
    )
    assert len(_PROTECTED_ROUTES) >= 20, (
        f"只扫到 {len(_PROTECTED_ROUTES)} 条受保护路由，明显偏少，疑似枚举漏了子路由"
    )

    found_paths = {_fill_path_params(r) for r in _protected_paths()}
    missing = _SENTINEL_ROUTES - found_paths
    assert not missing, (
        f"这些关键受保护端点没有被扫描到：{sorted(missing)}；"
        "路由枚举逻辑很可能漏掉了 include_router 进来的子路由"
    )


def test_protected_route_set_matches_frozen_snapshot():
    """防假绿（关键）：实际受保护的路由集合必须与冻结清单逐条一致。

    这是本文件真正的拦截力所在。上面那些「逐条断言未鉴权返回 401」的用例是**按现算
    清单**参数化的，所以摘掉某条端点的鉴权时，那条路由会从清单里消失、用例随之消失，
    于是全绿 —— 这个陷阱在独立验收里被实测证实（摘掉 `/classify` 的鉴权，121 passed）。

    这里做两个方向的比对：
      * 冻清单里有、实际没有 → 有人**摘掉了鉴权**（或有路由被删/改名）→ 必须红；
      * 实际有、冻清单里没有 → 有人**新增了受保护端点** → 也要红，请同步更新
        `_EXPECTED_PROTECTED` 并确认调用方已带上令牌（这正是当初线上 401 事故的成因）。
    """
    live = {param.id for param in _PROTECTED_ROUTES}
    removed = _EXPECTED_PROTECTED - live
    added = live - _EXPECTED_PROTECTED

    assert not removed, (
        "以下端点原本受鉴权保护，现在不在受保护清单里了 —— 要么鉴权被摘掉，"
        f"要么路由被删/改名，请逐一核实：{sorted(removed)}"
    )
    assert not added, (
        "出现了冻结清单之外的受保护端点。若是有意新增鉴权，请更新 _EXPECTED_PROTECTED，"
        f"并确认调用方已同步带上令牌：{sorted(added)}"
    )


@pytest.mark.parametrize("method,path,needs_admin", _PROTECTED_ROUTES)
def test_protected_route_rejects_anonymous(client, method, path, needs_admin):
    """受保护路由：不带令牌 → 401，绝不能放行。"""
    response = client.request(method, path, json={} if method != "GET" else None)
    assert response.status_code == 401, (
        f"{method} {path} 在未鉴权时返回了 {response.status_code}，期望 401。"
        f"若该端点是刚加的鉴权，请同步更新调用方。响应：{response.text[:200]}"
    )


_ADMIN_ROUTES = [p for p in _PROTECTED_ROUTES if p.values[2]]


def test_admin_routes_are_discovered():
    """防假绿：管理员路由同样必须被扫到。"""
    assert _ADMIN_ROUTES, "没有扫描到任何需要管理员权限的路由"


@pytest.mark.parametrize("method,path,needs_admin", _ADMIN_ROUTES)
def test_admin_route_rejects_member(member_client, method, path, needs_admin):
    """管理员路由：普通用户令牌 → 403（已鉴权但权限不足，不是 401）。"""
    response = member_client.request(method, path, json={} if method != "GET" else None)
    assert response.status_code == 403, (
        f"{method} {path} 用普通用户令牌访问返回了 {response.status_code}，期望 403。"
        f"响应：{response.text[:200]}"
    )


# ── 隔离契约：防止将来有人把测试环境改回生产路径 ─────────────────────────────


def test_semantic_cache_is_confined_to_tmp_root(tmp_root):
    """语义缓存的落盘目录必须在会话临时目录之下。

    这条是防回归用的：`semantic_cache` 的默认持久化路径写死在仓库的 `data/` 下，
    而本仓库同时是生产运行目录。一旦隔离被改坏，测试就会直接写生产。
    """
    from app.semantic_cache import get_semantic_cache

    cache = get_semantic_cache()
    persist_dir = Path(str(cache._persist_dir)).resolve()
    assert persist_dir.is_relative_to(tmp_root), (
        f"语义缓存没有落在临时目录：{persist_dir}（临时根目录 {tmp_root}）"
    )


def test_database_is_confined_to_tmp_root(tmp_root):
    """数据库连接串必须指向临时目录，绝不能连生产库。"""
    from app.database import SQLALCHEMY_DATABASE_URL

    assert SQLALCHEMY_DATABASE_URL.startswith(f"sqlite:///{tmp_root}"), (
        f"测试连的不是隔离库：{SQLALCHEMY_DATABASE_URL}"
    )


def test_rag_store_is_confined_when_imported(tmp_root):
    """若 `app.rag` 已被导入，其单例目录同样必须在临时目录之下。"""
    import sys

    rag_mod = sys.modules.get("app.rag")
    if rag_mod is None:
        pytest.skip("app.rag 未被导入，本用例不适用")

    store = rag_mod.get_rag_store()
    persist_dir = Path(str(store._persist_dir)).resolve()
    assert persist_dir.is_relative_to(tmp_root), (
        f"RAG 存储没有落在临时目录：{persist_dir}（临时根目录 {tmp_root}）"
    )
