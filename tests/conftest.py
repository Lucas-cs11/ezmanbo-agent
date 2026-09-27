"""pytest 全局配置：把测试进程与生产环境彻底隔离。

这里最关键的一件事，是**阻止仓库里的 .env 生效**。

`app/main.py` 第 3 行是 `load_dotenv(override=True)`，而仓库根目录的 .env 里有生产
RDS 的 `DATABASE_URL` 和真实的 EZPLM / LLM 凭据。`override=True` 意味着它会**盖掉**
测试进程自己设的环境变量；`app/database.py` 又在导入时就按 `DATABASE_URL` 建好引擎。
两者相加的结果是：任何碰数据库的测试都会连上生产库，并可能往里写。

所以在导入任何 `app.*` 之前，先把 `dotenv.load_dotenv` 换成空操作。pytest 在收集
测试模块之前会先导入 conftest.py，时机是够的（测试模块里的 `from app.main import app`
发生在之后）。

**第二条隔离线（2026-09-27 补，同日收尾）**：本目录就是生产运行目录，而
`SemanticCache` / `RAGStore` 的默认持久化路径都写死在仓库内的 `data/` 下，且
`get_semantic_cache()` / `get_rag_store()` 是**懒创建**的单例——只在调用时才落到默认
路径。曾经因此出过一次真实事故：某个测试无条件
`shutil.rmtree("data/chroma_cache")`，把线上语义缓存删掉了。所以现在做了三层防护：

1. 顶层把**三处**落盘路径都改道：凡指向临时目录之外的，一律改写到临时目录下
   （见 `_redirect_into_tmp`）——
   `chromadb.PersistentClient` 的 `path`（拦下所有**经 chromadb** 的写入）、
   `SemanticCache.__init__` 的 `persist_dir`、以及 `RAGStore.__init__` 的 `persist_dir`
   （后两者拦下**不经 chromadb** 的普通文件落盘与 mkdir）。
   **曾经的盲区（2026-09-27 已堵上）**：原先只包了 chromadb，于是两个类的 `__init__`
   里在 chroma 客户端**之前**执行的那次 `mkdir`、以及 `SemanticCache.set_exact()` 直接写
   `<persist_dir>/selection-v2/` 的普通文件落盘，全都绕过了防护。
   当时靠「所有调用点都显式传临时目录」侥幸不写生产，但裸构造 `SemanticCache()` 就会写到
   生产的 `data/chroma_cache/selection-v2/` —— 而那正是**正在服务**的精确缓存路径；
   裸构造 `RAGStore()` / `get_rag_store()` 会把 `_persist_dir` 钉在生产 `data/chroma_db`。
   改道落点的目录名现在带**内容哈希**后缀：早先「路径里的 / 换成 _」不是单射，
   `/tmp/coll_a/b` 与 `/tmp/coll_a_b` 会撞进同一个目录，两个用例互相看见对方的缓存。
2. 会话级 fixture 把两个单例**提前**指到临时目录，而不是等它被创建后再替换。
3. 会话开始即**实测**以上机制（三处改道各自拿一个生产形状的路径去试，看有没有被拦下），
   而不是断言「某个对象的路径看起来在临时目录」——不成立就整体终止本次会话。

**本文件**同时用 `atexit` + 会话开始时的**陈旧清扫**（只删自己前缀、且超过 6 小时没动过的
`/tmp/ezmanbo-pytest-*`）保证 `--collect-only` 之类的非 fixture 路径、以及被
pytest-timeout（内部 `os._exit`）掐断的会话都不在 /tmp 留垃圾。

**尚未覆盖的面**（2026-09-27 独立验收列出，**不在收尾项范围内**，已记入 ROADMAP 的
「残留」一节待单独模块处理）：`data/` 之外的落盘点都没有隔离——仓库根 `.env`
（`app/setup_api.py:102`，最危险的一处）、`memory/`、`.sessions/`、`docs/reports/`，
以及 `tests/eval_runner.py` 这条不经 pytest、因而不加载本文件的入口。
默认集、以及 integration 里真正会构造知识库的那个**子集**（`test_b4_integration.py` +
`test_b1_sse.py`）都**实测**不触发它们；整个 `-m integration` 集在本机跑不完（缺密钥/无外呼），
所以那是「子集成立」而不是「全集成立」。

需要跑真实链路（要真密钥、真外呼、连真库）时，显式打开逃生门：

    EZMANBO_TEST_REAL_NET=1 PYTHONPATH=. python -m pytest -m integration

注意：那会读仓库的 .env，也就是说会连生产库、真的会写。只在明确知道后果时使用。
"""

import atexit
import hashlib
import os
import shutil
import sys
import tempfile
import time
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

# 会话开始先做一次**陈旧清扫**。atexit 只在解释器正常退出时执行，而被
# pytest-timeout（`timeout_method = thread`，内部直接 `os._exit`）或信号掐断的会话
# 会连整个 TMP_ROOT 一起留在 /tmp（内含被改道进来的 chroma 副本，2026-09-27 实测
# 复现过）。给 os._exit 加信号处理是没用的——它连信号处理都不走；所以改成让**下一次**
# 运行顺手收尸：只删自己这个前缀、mtime 超过 6 小时、**且主人已经不在**的目录。
_STALE_AFTER_SECONDS = 6 * 3600


def _session_owner_is_alive(candidate) -> bool:
    """目录里若有本套件写的 pid 标记、且那个进程还在，就不算「陈旧」。

    只看目录 mtime 有个真实缺口：**正在跑的会话不会更新 TMP_ROOT 自己的 mtime**
    （新文件都落在它下面的 `redirected/` 里），所以一个跑够 6 小时的会话，它的临时
    目录会被并发的下一次运行当成垃圾清掉——2026-09-27 验收实测复现过。所以再加一道
    「主人还活着吗」。
    """
    try:
        pid = int((candidate / "pid").read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # 进程在、但不属于我：保守当作活的
    return True


for _stale in Path(tempfile.gettempdir()).glob("ezmanbo-pytest-*"):
    try:
        if (
            _stale.is_dir()
            and (time.time() - _stale.stat().st_mtime) > _STALE_AFTER_SECONDS
            and not _session_owner_is_alive(_stale)
        ):
            shutil.rmtree(_stale, ignore_errors=True)
    except OSError:
        pass

TMP_ROOT = Path(tempfile.mkdtemp(prefix="ezmanbo-pytest-")).resolve()
# 供上面那次清扫判断「这个目录的主人还在不在」
(TMP_ROOT / "pid").write_text(str(os.getpid()), encoding="utf-8")

# 清理不能只挂在 fixture teardown 上：`pytest --collect-only` 根本不执行 fixture，
# 而这条命令恰恰是本仓库文档里叫人维护「冻结清单」时最常跑的，于是每跑一次就在
# /tmp 留下一个空目录（实测泄漏过）。atexit 在解释器退出时无条件执行，
# 对已删除的目录是幂等的（ignore_errors）。
atexit.register(shutil.rmtree, TMP_ROOT, ignore_errors=True)


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

# ── 2. 把「会落盘的东西」的路径改道到临时目录 ───────────────────────────
#
# `data/` 下的落盘分两类：经 chromadb 的、和不经 chromadb 的普通文件。与其指望每个
# 测试自己传对路径，不如在源头兜住：只要路径在临时目录之外，就改写进临时目录。
# 一共三处改道，每一处都必须配一条探针**实测它拦得住**（见第 3 节的 _hermetic_guard）：
#
#   2a. `chromadb.PersistentClient` 的 path —— 拦下所有**经 chromadb** 的写入
#       （RAGStore 的知识库、SemanticCache 的旧向量集合）。
#   2b. `SemanticCache.__init__` 的 persist_dir —— 拦下它那次**不经 chromadb** 的
#       `mkdir` 与 `set_exact()` 写文件（精确缓存 `selection-v2/`）。
#   2c. `RAGStore.__init__` 的 persist_dir —— 同样拦下它构造 chroma 客户端**之前**
#       的那次 `mkdir`（2a 只拦得到客户端，拦不到这个 mkdir）。
#
# 2b 与 2c 都是后补的：原先只包了 chromadb，于是这两个类的 `__init__` 里在客户端之前
# 执行的 `mkdir` 全都绕过了防护（详见本文件顶部 docstring 的「曾经的盲区」）。
#
# ⚠️ 仍未覆盖的面（2026-09-27 独立验收列出，**不在本轮收尾项范围内**，已记入
#    ROADMAP 的「残留」一节，待单独一个模块处理）：`data/` 之外的落盘点一律没有隔离——
#   仓库根 `.env`（app/setup_api.py:102）、`memory/`、`.sessions/`、`docs/reports/`、
#   以及 `tests/eval_runner.py` 这条不经 pytest、因而不加载本文件的入口。
#    现有的默认集与 integration 集都**实测**不会触发它们（find -newer 全树零写入），
#    所以它们是「下一个测试作者会不会踩到」的面，而不是当下正在发生的写入。
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

# 每次改道的记录（请求路径 → 实际路径）。由 _hermetic_guard 的探针断言其增长，
# 也在会话结束时打印出来，好让「有代码在请求生产路径」这件事可见。
REDIRECTED_PATHS: list[tuple[str, str]] = []
CHROMA_REDIRECT_APPLIED = False
SEMANTIC_CACHE_REDIRECT_APPLIED = False
RAG_REDIRECT_APPLIED = False


def _redirect_target_name(resolved: Path) -> str:
    """给定一个**临时目录之外**的已解析路径，算出它在 `redirected/` 下的目录名。

    单独抽成纯函数，是为了让 _hermetic_guard 能直接断言「这个名字是合法文件名」——
    否则那条断言永远是死代码：名字一旦超长，`_redirect_into_tmp` 里的 `mkdir` 会先
    抛 `OSError: Errno 36`，断言根本没机会执行（2026-09-27 自测发现）。

    落点目录名必须与请求路径**一一对应**。早先直接用「路径里的 / 换成 _」当名字，
    于是 `/tmp/coll_a/b` 与 `/tmp/coll_a_b` 会撞进同一个目录——两个用例就会互相
    看见对方的缓存（2026-09-27 验收实测复现）。前缀保留可读性，后缀是内容哈希，
    保证不同请求路径不再撞名。

    前缀按**字节**截断，不是按字符：路径里可能有中文或 emoji，按字符截 80 个会让
    落点名的字节数远超文件系统的 255 字节上限，改道会直接抛 `OSError: Errno 36`
    （2026-09-27 验收用一个 emoji 路径实测复现）。截到 60 字节、丢掉被切断的半个
    字符，总长 ≤ 60+1+12 = 73 字节，留足余量。
    """
    _slug = (
        str(resolved)
        .lstrip("/")
        .replace("/", "_")
        .encode("utf-8")[:60]
        .decode("utf-8", "ignore")
    )
    _digest = hashlib.sha256(str(resolved).encode("utf-8")).hexdigest()[:12]
    return f"{_slug}-{_digest}"


def _redirect_into_tmp(original_path):
    """把临时目录之外的持久化路径改写进临时目录，返回改写后的路径。

    对 2a / 2b / 2c 通用——三者要的都是同一件事：「不许落在临时目录之外」。
    """
    resolved = Path(str(original_path)).resolve()
    if resolved.is_relative_to(TMP_ROOT):
        return str(resolved)
    safe = TMP_ROOT / "redirected" / _redirect_target_name(resolved)
    safe.mkdir(parents=True, exist_ok=True)
    REDIRECTED_PATHS.append((str(resolved), str(safe)))
    return str(safe)


if not ALLOW_REAL_NET:
    # ── 2a. chromadb 的客户端 ──────────────────────────────────────────
    try:
        import chromadb  # noqa: E402

        _ORIGINAL_PERSISTENT_CLIENT = chromadb.PersistentClient

        def _guarded_persistent_client(path="./chroma", *args, **kwargs):
            return _ORIGINAL_PERSISTENT_CLIENT(
                _redirect_into_tmp(path), *args, **kwargs
            )

        chromadb.PersistentClient = _guarded_persistent_client
        CHROMA_REDIRECT_APPLIED = True
    except Exception:  # pragma: no cover - chromadb 缺失时不影响纯逻辑用例
        pass

    # ── 2b. SemanticCache 的 persist_dir（普通文件落盘，不经 chromadb）──
    #
    # 与 2a 不同，`SemanticCache` 是**真类**，所以包 `__init__` 是有效的；
    # 而 2a 那个 `PersistentClient` 是函数，包 `__init__` 无效——这个区别是本文件
    # 用一次真实事故换来的，改动这一段前请先读上面那段 ⚠️ 注释。
    #
    # 默认值要从**原函数**的 `__defaults__` 里取：若写成自己的字面量，将来生产侧
    # 改了默认目录，这里就会悄悄指向一个过期路径，改道看着还在、实际已经错位。
    try:
        from app.semantic_cache import SemanticCache  # noqa: E402

        _ORIGINAL_SEMANTIC_CACHE_INIT = SemanticCache.__init__
        _ORIGINAL_DEFAULT_PERSIST_DIR = _ORIGINAL_SEMANTIC_CACHE_INIT.__defaults__[0]

        def _guarded_semantic_cache_init(
            self, persist_dir=_ORIGINAL_DEFAULT_PERSIST_DIR, *args, **kwargs
        ):
            return _ORIGINAL_SEMANTIC_CACHE_INIT(
                self, _redirect_into_tmp(persist_dir), *args, **kwargs
            )

        SemanticCache.__init__ = _guarded_semantic_cache_init
        SEMANTIC_CACHE_REDIRECT_APPLIED = True
    except Exception:  # pragma: no cover - 模块缺失时不影响纯逻辑用例
        pass

    # ── 2c. RAGStore 的 persist_dir（它在建 chroma 客户端之前先 mkdir）──
    #
    # 与 2b 同因：`RAGStore.__init__` 先对 `self._persist_dir` 做 `mkdir`，**然后**才
    # 调 `chromadb.PersistentClient`。2a 拦的是后者，所以这个 mkdir 会照原样落在生产
    # 路径上；`self._persist_dir` 也因此指向生产，只有向量写入被改道。
    # 这不是理论问题：`app/rag.py` 的 `get_rag_store()` 默认传的是**相对**路径
    # "data/chroma_db"（按 CWD 解析；生产里 uvicorn 的 CWD 就是仓库根，即生产库），
    # 裸调一次就把 `_persist_dir` 钉在它上面——
    # `tests/test_auth_contract.py::test_rag_store_is_confined_when_imported` 就是为
    # 这件事写的断言，而它此前一直靠「默认集不导入 app.rag」而 skip，等于没生效。
    #
    # 默认值同样从**原函数**的 `__defaults__` 里取，理由见 2b。
    # 构造本身很轻（实测离线 1.2s，`get_or_create_collection` 不加载向量模型），
    # 所以第 3 节的探针可以直接构造一个真的 RAGStore 来验。
    try:
        from app.rag import RAGStore  # noqa: E402

        _ORIGINAL_RAG_STORE_INIT = RAGStore.__init__
        _ORIGINAL_RAG_DEFAULT_PERSIST_DIR = _ORIGINAL_RAG_STORE_INIT.__defaults__[0]

        def _guarded_rag_store_init(
            self, persist_dir=_ORIGINAL_RAG_DEFAULT_PERSIST_DIR, *args, **kwargs
        ):
            return _ORIGINAL_RAG_STORE_INIT(
                self, _redirect_into_tmp(persist_dir), *args, **kwargs
            )

        RAGStore.__init__ = _guarded_rag_store_init
        RAG_REDIRECT_APPLIED = True
    except Exception:  # pragma: no cover - 模块缺失时不影响纯逻辑用例
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

        # ── 实测改道机制本身 ───────────────────────────────────────────────
        # 这里刻意**不**断言「某个单例的路径在临时目录」——上一版就是这么断言的，
        # 而它照样漏掉了「改道根本没生效」这件事。现在直接拿一个生产形状的路径去创建
        # 对象，看它有没有被改写。探针路径取在 /tmp 下、绝不指向 data/，
        # 这样万一机制失灵，被创建的最坏也只是 /tmp 里一个无害目录，不会碰生产。
        #
        # 三处探针都要有，且都不能省：2a / 2b / 2c 是**三套独立的机制**，
        # 历史上正是「只测了 2a 的存在、没测 2b 与 2c 的存在」才让它们长期空着。
        assert CHROMA_REDIRECT_APPLIED, (
            "chroma 落盘改道没有安装成功，测试可能写到生产 data/ 目录，已终止"
        )
        assert SEMANTIC_CACHE_REDIRECT_APPLIED, (
            "SemanticCache.persist_dir 改道没有安装成功，"
            "裸构造 SemanticCache() 会写生产 data/chroma_cache，已终止"
        )
        assert RAG_REDIRECT_APPLIED, (
            "RAGStore.persist_dir 改道没有安装成功，"
            "裸构造 RAGStore() / get_rag_store() 会把 _persist_dir 钉在生产 data/chroma_db，"
            "已终止"
        )

        # 改道落点必须与请求路径**一一对应**，否则两个用例会共享同一个缓存目录而互相
        # 污染。早先的实现直接用「路径里的 / 换成 _」当目录名，不是单射——下面这一对
        # 就是当时实测撞名的反例（2026-09-27 验收查出）。所以这里常驻一条实测。
        _collide_a = _redirect_into_tmp(TMP_ROOT.parent / "coll_a" / "b")
        _collide_b = _redirect_into_tmp(TMP_ROOT.parent / "coll_a_b")
        assert _collide_a != _collide_b, (
            f"改道落点撞名：{TMP_ROOT.parent}/coll_a/b 与 {TMP_ROOT.parent}/coll_a_b "
            f"被写进了同一个目录 {_collide_a}，两个用例会互相看见对方的缓存，"
            "已终止本次会话。"
        )

        # 落点名的字节数必须留有余量。路径里可能有中文或 emoji，若按**字符**截断，
        # 80 个 emoji = 320 字节 > 文件系统的 255 字节上限，`mkdir` 会直接抛
        # `OSError: Errno 36`（2026-09-27 验收实测复现）。这里常驻一条实测。
        #
        # 断言的是**纯函数**而不是 `_redirect_into_tmp`：后者在名字超长时会在内部的
        # `mkdir` 上先抛 Errno 36，断言永远轮不到执行——那就成了「看着像防护的死代码」
        # （2026-09-27 自测发现）。纯函数不会碰文件系统，回归时这条断言必然先失败。
        _unicode_resolved = (TMP_ROOT.parent / ("😀" * 100) / "chroma_cache").resolve()
        _unicode_name = _redirect_target_name(_unicode_resolved)
        assert len(_unicode_name.encode("utf-8")) <= 255, (
            f"改道落点名过长（{len(_unicode_name.encode('utf-8'))} 字节 > 255）："
            f"{_unicode_name!r}。含中文/emoji 的路径会让改道抛 Errno 36，"
            "已终止本次会话。"
        )
        import chromadb as _chromadb_probe

        _probe_target = str(TMP_ROOT.parent / "ezmanbo-redirect-probe")
        _before = len(REDIRECTED_PATHS)
        _chromadb_probe.PersistentClient(path=_probe_target)
        assert len(REDIRECTED_PATHS) > _before, (
            f"chroma 落盘改道**未生效**：指向 {_probe_target} 的 PersistentClient "
            "没有被拦下。这意味着任何走到 RAGStore 的测试都会写生产 data/chroma_db，"
            "已终止本次会话。"
        )

        # 2b 的探针：拿一个「生产形状」的 persist_dir 去构造 SemanticCache，
        # 再确认它的两个落点（_persist_dir 与 set_exact 用的 _exact_dir）都在临时目录下。
        # 只断言「构造函数被包了」是不够的——要断言包完之后路径真的被改了。
        from app.semantic_cache import SemanticCache as _semantic_cache_probe

        _exact_probe_target = str(TMP_ROOT.parent / "ezmanbo-exact-probe" / "chroma_cache")
        _before = len(REDIRECTED_PATHS)
        _exact_probe = _semantic_cache_probe(persist_dir=_exact_probe_target)
        assert len(REDIRECTED_PATHS) > _before, (
            f"SemanticCache 的 persist_dir 改道**未生效**：指向 {_exact_probe_target} "
            "的构造没有被拦下，已终止本次会话。"
        )
        for _name, _path in (
            ("_persist_dir", _exact_probe._persist_dir),
            ("_exact_dir", _exact_probe._exact_dir),
        ):
            assert str(_path).startswith(str(TMP_ROOT)), (
                f"SemanticCache.{_name} 落在了临时目录之外：{_path}。"
                "这正是精确缓存（selection-v2）的落点，会把内容写进正在服务的生产缓存。"
            )

        # 2c 的探针：构造一个真的 RAGStore，确认 persist_dir 被改写。
        # 这里必须**真构造**：2c 拦的是 `__init__` 里客户端之前的那次 mkdir，
        # 光看「类被包过」证明不了它。
        from app.rag import RAGStore as _rag_store_probe

        _rag_probe_target = str(TMP_ROOT.parent / "ezmanbo-rag-probe" / "chroma_db")
        _before = len(REDIRECTED_PATHS)
        _rag_probe = _rag_store_probe(persist_dir=_rag_probe_target)
        assert len(REDIRECTED_PATHS) > _before, (
            f"RAGStore 的 persist_dir 改道**未生效**：指向 {_rag_probe_target} 的构造"
            "没有被拦下，已终止本次会话。"
        )
        assert str(_rag_probe._persist_dir).startswith(str(TMP_ROOT)), (
            f"RAGStore._persist_dir 落在了临时目录之外：{_rag_probe._persist_dir}。"
            "它会在下一次 `get_rag_store()` 时指向生产 data/chroma_db。"
        )

        import app.semantic_cache as semantic_cache_mod

        semantic_cache_mod._semantic_cache = semantic_cache_mod.SemanticCache(
            persist_dir=str(TMP_ROOT / "chroma_cache")
        )

    # 把 RAG 的知识库单例也提前钉在临时目录。2c 的导入已经让 `app.rag` 必然出现在
    # sys.modules 里，所以这一条现在总会命中；它是在 2c 之上的又一道「提前钉住」，
    # 与下面 semantic_cache 那条对称。
    # （原文写的是「app.rag 会在构造时加载嵌入模型，较重」——实测是错的：向量模型在
    #  `_get_embedding_model()` 里懒加载，只有 ingest/query 才碰；`RAGStore.__init__`
    #  只建 chroma 客户端与集合，离线 1.2 秒。2026-09-27 订正。）
    rag_mod = sys.modules.get("app.rag")
    if rag_mod is not None and not ALLOW_REAL_NET:
        rag_mod._rag_store = rag_mod.RAGStore(persist_dir=str(TMP_ROOT / "chroma_db"))

    if not ALLOW_REAL_NET:
        from app import semantic_cache as _sc

        # 这里**故意只断言「种子块跑过了」**，不再断言单例路径落在临时目录——后者是
        # 恒真的死断言：种子块自己传的就是 TMP_ROOT 下的路径，而 `_redirect_into_tmp`
        # 对已在 TMP_ROOT 内的路径原样返回，于是 `startswith(TMP_ROOT)` 永远成立。
        # （2026-09-27 第三轮独立验收用变异实测：2b 改直通 + 删 2b 探针 → 124 passed
        #  全绿，本条一声不响，是「断言了单例路径而非断言改道机制」的活标本。）
        # 单例是否**真的受改道机制约束**由上面 2b 探针负责，那才是承重的那条。
        assert _sc._semantic_cache is not None, (
            "语义缓存单例没有被提前钉住（仍是 None）：说明上面的种子块没执行，"
            "后续第一个调用 get_semantic_cache() 的用例会以生产默认 persist_dir "
            "构造它，已终止本次会话。"
        )

    yield

    # 只把「仓库内路径」当作值得报警的东西：那才是「有代码在请求生产路径」。
    # 测试自己传的 tmp_path 也算「临时目录之外」，同样会被改道，但那是无害的，
    # 混在一起打印会把这个信号淹掉。
    _repo_internal = sorted(
        {
            (requested, actual)
            for requested, actual in REDIRECTED_PATHS
            if Path(requested).is_relative_to(REPO_ROOT)
        }
    )
    if _repo_internal:
        print(
            "\n[conftest] ⚠️ 以下**仓库内**路径被自动改道到临时目录"
            "（说明有代码在请求生产路径，已拦下）："
        )
        for requested, actual in _repo_internal:
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
    """一个完全属于本用例的语义缓存。

    传入的 persist_dir 是 `tmp_path/"chroma_cache"`，但注意它**不会**真的落在
    tmp_path 下：第 2 节的改道会把它统一改写进本会话的 `TMP_ROOT/redirected/` 里
    （每个用例一个不同的子目录）。隔离因此比 tmp_path 更强——整个会话的落点都是
    一次性的、退出即弃。要读的实际落点见会话结束时 conftest 打印的改道记录。
    """
    from app.semantic_cache import SemanticCache

    return SemanticCache(persist_dir=str(tmp_path / "chroma_cache"))
