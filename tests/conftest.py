"""pytest 全局配置：把测试进程与生产环境彻底隔离。

这里最关键的一件事，是**阻止仓库里的 .env 生效**。

`app/main.py` 第 3 行是 `load_dotenv(override=True)`，而仓库根目录的 .env 里有生产
RDS 的 `DATABASE_URL` 和真实的 EZPLM / LLM 凭据。`override=True` 意味着它会**盖掉**
测试进程自己设的环境变量；`app/database.py` 又在导入时就按 `DATABASE_URL` 建好引擎。
两者相加的结果是：任何碰数据库的测试都会连上生产库，并可能往里写。

所以在导入任何 `app.*` 之前，先把 `dotenv.load_dotenv` 换成空操作。pytest 在收集
测试模块之前会先导入 conftest.py，时机是够的（测试模块里的 `from app.main import app`
发生在之后）。

**第二条隔离线（2026-09-27 补）**：本目录就是生产运行目录，而
`SemanticCache` / `RAGStore` 的默认持久化路径都写死在仓库内的 `data/` 下，且
`get_semantic_cache()` / `get_rag_store()` 是**懒创建**的单例——只在调用时才落到默认
路径。曾经因此出过一次真实事故：某个测试无条件
`shutil.rmtree("data/chroma_cache")`，把线上语义缓存删掉了。所以现在做了三层防护：

1. 顶层把 `chromadb.PersistentClient` 的路径改道：凡指向临时目录之外的，一律改写到
   临时目录下（见 `_redirect_chroma_path`）。这会拦下**一切经 chromadb 落盘**的写入。
   ⚠️ **已知盲区（2026-09-27 复验查出，尚未修）**：它**拦不住不经 chromadb 的写入**。
   `SemanticCache.set_exact()` 是直接以普通文件写 `<persist_dir>/selection-v2/` 的，
   `SemanticCache.__init__` 也会对原始路径 `mkdir` —— 全程不碰 chromadb，因此不吃这道改道。
   目前所有调用点都显式传了临时目录（单例由第 3 层提前钉死，测试用 `isolated_semantic_cache`），
   所以**当前不会写生产**；但若将来有人裸构造 `SemanticCache()` 并 `set_exact()`，
   就会直接写到生产的 `data/chroma_cache/selection-v2/` —— 而那正是**现在在用**的精确缓存路径
   （旧 chroma 路径已废弃）。修法：把同样的改道施加到 `SemanticCache.__init__` 的 `persist_dir` 上，
   或让 `_redirect_chroma_path` 复用到它。已记入总纲待办。
2. 会话级 fixture 把两个单例**提前**指到临时目录，而不是等它被创建后再替换。
3. 会话开始即断言以上两条都已生效，不成立就整体终止。

需要跑真实链路（要真密钥、真外呼、连真库）时，显式打开逃生门：

    EZMANBO_TEST_REAL_NET=1 PYTHONPATH=. python -m pytest -m integration

注意：那会读仓库的 .env，也就是说会连生产库、真的会写。只在明确知道后果时使用。
"""

import os
import shutil
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# ── 1. 中和 .env —— 必须在导入 app.* 之前完成 ──────────────────────────

ALLOW_REAL_NET = os.environ.get("EZMANBO_TEST_REAL_NET") == "1"

import dotenv  # noqa: E402

if not ALLOW_REAL_NET:
    # 所有 `from dotenv import load_dotenv` / `dotenv.load_dotenv(...)` 一律变成空操作
    dotenv.load_dotenv = lambda *args, **kwargs: False

TMP_ROOT = Path(tempfile.mkdtemp(prefix="ezmanbo-pytest-")).resolve()


def _read_path_only_env(key: str):
    """从仓库 .env 里读一个**纯路径类**配置项。

    只应该传入上面白名单里的键。存在的意义是：.env 被中和之后，仍然需要
    HF_HOME 这类「不含秘密、但决定模型能否离线加载」的配置；而
    EZPLM_API_KEY / DATABASE_URL 这类必须继续被无视，否则隔离就白做了。
    """
    env_file = REPO_ROOT / ".env"
    if not env_file.exists():
        return None
    try:
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"').strip("'") or None
    except OSError:
        return None
    return None


if not ALLOW_REAL_NET:
    # 一切可写状态都落在临时目录，退出即弃
    os.environ["DATA_DIR"] = str(TMP_ROOT)
    os.environ["DATABASE_URL"] = f"sqlite:///{TMP_ROOT}/test.db"

    # 仅测试用的签名密钥；长度满足 auth._load_secret_key 的 >=32 字符下限
    os.environ["JWT_SECRET_KEY"] = "test-only-secret-not-used-in-production-0123456789"
    os.environ["SECRET_KEY"] = os.environ["JWT_SECRET_KEY"]
    os.environ["ENVIRONMENT"] = "test"

    # 抹掉所有外呼凭据：宁可让依赖外部的用例显式失败，也不要误打真接口。
    # EZPLM_API_KEY 留空是刻意的——ezplm_client 见空会直接返回「未配置」，
    # 不会发出请求。
    for _key in (
        "EZPLM_API_KEY",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "OPENAI_BASE_URL",
        "ANTHROPIC_BASE_URL",
        "REDIS_URL",
    ):
        os.environ[_key] = ""
    # 再上一道保险：即便某条路径仍去请求，也打不到真服务
    os.environ["EZPLM_BASE_URL"] = "http://127.0.0.1:9"

    # 向量模型只读本地缓存，避免测试期联网下载。
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    os.environ["ANONYMIZED_TELEMETRY"] = "False"

    # 上面把 .env 整个中和掉了，连带丢掉了 HF_HOME——而本机的模型缓存并不在
    # 默认的 ~/.cache/huggingface 下（见 .env）。丢了它，离线的向量模型就会
    # 加载失败，把「模型确实能加载」这一层真实覆盖误判成失败。
    # 所以按**白名单**把纯路径类配置捞回来：只认这几个键，绝不去读任何可能是
    # 凭据的项（EZPLM_API_KEY / OPENAI_API_KEY / DATABASE_URL 等一律不碰）。
    for _key in ("HF_HOME", "HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_DATASETS_OFFLINE"):
        if not os.environ.get(_key):
            _value = _read_path_only_env(_key)
            if _value:
                os.environ[_key] = _value

# ── 2. 把 chromadb 的落盘路径改道到临时目录 ─────────────────────────────
#
# SemanticCache 与 RAGStore 都把 chromadb 的持久化目录写在 data/ 下，
# 且用的是懒加载单例。与其指望每个测试自己传对路径，不如在客户端这一层兜住：
# 只要路径在临时目录之外，就改写进临时目录。
#
# ⚠️ 2026-09-27 修正 —— 独立验收查出的**阻塞缺陷**，原文如下：
#   这里原先写的是 `chromadb.PersistentClient.__init__ = _guarded_init`。
#   但 `chromadb.PersistentClient` 自 chroma 0.5 起就是**函数**而非类
#   （实测 chromadb 1.5.9：`inspect.isfunction(...) is True`）。给一个**函数对象**
#   挂 `__init__` 属性，函数被调用时根本不会去读它 —— 那一层防护**从未生效**，
#   是一段看起来很像防护的死代码。
#   后果不是理论风险：任何真正走到 RAGStore 的测试（例如本项目文档里明确写着的
#   `-m integration`）都会**直接写生产的 data/chroma_db**。验收过程中确实发生了。
#   当时默认集之所以看起来「安全」，只是因为默认集恰好没有任何用例走到那条路径 ——
#   那叫运气，不叫隔离。
#
# 现在改成替换模块属性上的**函数本身**。app 侧两个调用点都是
# `import chromadb` + `chromadb.PersistentClient(...)`（见 app/rag.py:55、
# app/semantic_cache.py:157），全仓不存在 `from chromadb import PersistentClient`，
# 因此替换模块属性即可全局生效。
#
# 并且——这是关键——_hermetic_guard 里会**实测这个机制本身**，而不是假设它成立。
# 上一版的教训正是：断言了「单例的路径在临时目录」，却从未验证「改道机制是否真的拦得住」。

REDIRECTED_CHROMA_PATHS: list[tuple[str, str]] = []
CHROMA_REDIRECT_APPLIED = False


def _redirect_chroma_path(original_path):
    """把临时目录之外的 chroma 路径改写进临时目录，返回改写后的路径。"""
    resolved = Path(str(original_path)).resolve()
    if resolved.is_relative_to(TMP_ROOT):
        return str(resolved)
    safe = TMP_ROOT / "redirected_chroma" / str(resolved).lstrip("/").replace("/", "_")
    safe.mkdir(parents=True, exist_ok=True)
    REDIRECTED_CHROMA_PATHS.append((str(resolved), str(safe)))
    return str(safe)


if not ALLOW_REAL_NET:
    try:
        import chromadb  # noqa: E402

        _ORIGINAL_PERSISTENT_CLIENT = chromadb.PersistentClient

        def _guarded_persistent_client(path="./chroma", *args, **kwargs):
            return _ORIGINAL_PERSISTENT_CLIENT(
                _redirect_chroma_path(path), *args, **kwargs
            )

        chromadb.PersistentClient = _guarded_persistent_client
        CHROMA_REDIRECT_APPLIED = True
    except Exception:  # pragma: no cover - chromadb 缺失时不影响纯逻辑用例
        pass

# ── 3. fixtures ────────────────────────────────────────────────────────

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture(scope="session")
def tmp_root() -> Path:
    """本会话专属的临时根目录。"""
    return TMP_ROOT


@pytest.fixture(scope="session")
def app():
    """FastAPI 应用对象。

    不做 `with TestClient(...)`，因此不会触发 lifespan/startup，
    避免启动期副作用（真实链路预热）进入测试。
    """
    from app.main import app as fastapi_app

    return fastapi_app


@pytest.fixture(scope="session", autouse=True)
def _hermetic_guard():
    """把两个懒加载单例提前钉在临时目录，并断言隔离确实生效。

    顺序很重要：这里必须在任何测试用到 `get_semantic_cache()` /
    `get_rag_store()` 之前把全局变量换掉。等它自己被创建出来再替换是来不及的——
    那一次创建就已经把状态写进生产目录了（这正是 2026-09-27 那次事故的成因）。
    """
    if not ALLOW_REAL_NET:
        from app.database import SQLALCHEMY_DATABASE_URL

        assert SQLALCHEMY_DATABASE_URL.startswith("sqlite:///" + str(TMP_ROOT)), (
            f"测试没有与生产库隔离，实际连的是：{SQLALCHEMY_DATABASE_URL}"
        )

        # ── 实测「chroma 落盘改道」这个机制本身 ───────────────────────────
        # 这里刻意**不**断言「某个单例的路径在临时目录」——上一版就是这么断言的，
        # 而它照样漏掉了「改道根本没生效」这件事。现在直接拿一个生产形状的路径去创建
        # 客户端，看它有没有被改写。探针路径取在 /tmp 下、绝不指向 data/，
        # 这样万一机制失灵，被创建的最坏也只是 /tmp 里一个无害目录，不会碰生产。
        assert CHROMA_REDIRECT_APPLIED, (
            "chroma 落盘改道没有安装成功，测试可能写到生产 data/ 目录，已终止"
        )
        import chromadb as _chromadb_probe

        _probe_target = str(TMP_ROOT.parent / "ezmanbo-redirect-probe")
        _before = len(REDIRECTED_CHROMA_PATHS)
        _chromadb_probe.PersistentClient(path=_probe_target)
        assert len(REDIRECTED_CHROMA_PATHS) > _before, (
            f"chroma 落盘改道**未生效**：指向 {_probe_target} 的 PersistentClient "
            "没有被拦下。这意味着任何走到 RAGStore 的测试都会写生产 data/chroma_db，"
            "已终止本次会话。"
        )

        import app.semantic_cache as semantic_cache_mod

        semantic_cache_mod._semantic_cache = semantic_cache_mod.SemanticCache(
            persist_dir=str(TMP_ROOT / "chroma_cache")
        )

    # app.rag 会在构造时加载嵌入模型，较重；只在它已被导入时替换。
    # 即便这一条没命中（默认集就是如此，因为默认集不导入 app.rag），
    # 它底下的 chromadb 客户端也已被第 2 节的改道**实测**兜住——见上面的探针。
    rag_mod = sys.modules.get("app.rag")
    if rag_mod is not None and not ALLOW_REAL_NET:
        rag_mod._rag_store = rag_mod.RAGStore(persist_dir=str(TMP_ROOT / "chroma_db"))

    if not ALLOW_REAL_NET:
        from app import semantic_cache as _sc

        assert str(_sc._semantic_cache._persist_dir).startswith(str(TMP_ROOT)), (
            f"语义缓存没有指向临时目录：{_sc._semantic_cache._persist_dir}"
        )

    yield

    if REDIRECTED_CHROMA_PATHS:
        print(
            "\n[conftest] 以下 chroma 路径被自动改道到临时目录"
            "（说明有代码在请求生产路径，已拦下）："
        )
        for requested, actual in sorted(set(REDIRECTED_CHROMA_PATHS)):
            print(f"  请求 {requested}\n  → 改用 {actual}")

    # 会话专属的临时目录用完即弃。此前没有这一步，每跑一次测试就在 /tmp 留下一个
    # 目录（实测已累积 72 个），虽不碰生产，但属于无谓的垃圾。
    shutil.rmtree(TMP_ROOT, ignore_errors=True)


@pytest.fixture(scope="session")
def _database(_hermetic_guard):
    """在临时库上建表。"""
    from app.database import init_db

    init_db()
    yield


@pytest.fixture(scope="session")
def test_users(_database) -> dict:
    """建两个测试账号（一个管理员、一个普通用户），返回其 id 与用户名。"""
    from app.auth import hash_password
    from app.database import SessionLocal
    from app.models_db import User

    db = SessionLocal()
    try:
        admin = User(
            username="pytest-admin",
            email="pytest-admin@example.invalid",
            hashed_password=hash_password("pytest-admin-password"),
            is_admin=True,
            is_active=True,
        )
        member = User(
            username="pytest-user",
            email="pytest-user@example.invalid",
            hashed_password=hash_password("pytest-user-password"),
            is_admin=False,
            is_active=True,
        )
        db.add_all([admin, member])
        db.commit()
        db.refresh(admin)
        db.refresh(member)
        return {
            "admin": {"id": admin.id, "username": admin.username},
            "user": {"id": member.id, "username": member.username},
        }
    finally:
        db.close()


def _bearer(user_id: int) -> dict:
    """为测试用户签一枚真实访问令牌。

    刻意去签真令牌、走完整的 get_current_user 校验，而不是用
    `app.dependency_overrides` 顶掉鉴权依赖——被顶掉的鉴权不会被测试覆盖到，
    而鉴权恰恰是最不能失守的一环。
    """
    from app.auth import create_access_token

    token = create_access_token({"sub": str(user_id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def member_headers(test_users) -> dict:
    return _bearer(test_users["user"]["id"])


@pytest.fixture
def admin_headers(test_users) -> dict:
    return _bearer(test_users["admin"]["id"])


@pytest.fixture
def client(app) -> TestClient:
    """未鉴权的客户端。"""
    return TestClient(app)


@pytest.fixture
def member_client(app, member_headers) -> TestClient:
    """带普通用户身份的客户端。"""
    return TestClient(app, headers=member_headers)


@pytest.fixture
def admin_client(app, admin_headers) -> TestClient:
    """带管理员身份的客户端。"""
    return TestClient(app, headers=admin_headers)


@pytest.fixture
def isolated_semantic_cache(tmp_path):
    """一个完全属于本用例的语义缓存（文件与向量库都落在 tmp_path 下）。"""
    from app.semantic_cache import SemanticCache

    return SemanticCache(persist_dir=str(tmp_path / "chroma_cache"))
