"""`scripts/sync_db_password.py` 的用例。

**不需要数据库**：真正连库那一步（`_verify_connection`）在用例里一律被替换掉，
所以这里覆盖的是「口令编码、.env 改写的保真与原子性、以及三条安全属性」：

1. 写盘前验证失败 → `.env` **一个字节都不动**；
2. 口令**从不回显**（含 stdout 与备份文件名）；
3. 除 `DATABASE_URL` 那一行外，其余内容逐字保留，引号风格与文件权限不变。
"""

import os
import stat

import pytest
import sqlalchemy
from sqlalchemy.engine import make_url
from urllib.parse import quote

from scripts import sync_db_password as mod

OLD_URL = "postgresql+psycopg2://app_user:OldPw%40x@db.example.com:5432/ezmanbo?sslmode=require"
NEW_PW = "N3w/pw@ss:#1?&=%"  # 故意塞满 URL 里有特殊含义的字符


def _write_env(tmp_path, value=OLD_URL, quote_char=""):
    body = (
        "# 注释行\n"
        "JWT_SECRET_KEY=abc\n"
        f"{mod.KEY}={quote_char}{value}{quote_char}\n"
        "HF_HOME=/mnt/data/.cache/huggingface\n"
        "\n"
    )
    path = tmp_path / ".env"
    path.write_text(body)
    os.chmod(path, 0o600)
    return path


def _run(tmp_path, monkeypatch, env_path, argv=(), verify=None, password=NEW_PW):
    monkeypatch.setattr(mod, "_prompt_password", lambda: password)
    monkeypatch.setattr(
        mod, "_verify_connection", verify if verify is not None else (lambda url: None)
    )
    return mod.main(["--env", str(env_path), *argv])


def _value_of(path):
    for line in path.read_text().splitlines():
        if line.strip().split("=", 1)[0].strip() == mod.KEY:
            return line.split("=", 1)[1].strip()
    raise AssertionError("DATABASE_URL 不见了")


# ── 口令编码：拿 SQLAlchemy 自己的解析器当裁判 ──────────────────────────


def test_compose_percent_encodes_password():
    url = mod._compose(NEW_PW, OLD_URL)
    assert make_url(url).password == NEW_PW, "SQLAlchemy 解出来的口令必须与输入逐字相同"
    assert f":{NEW_PW}@" not in url, "原始口令不得原样出现在连接串里"
    segment = url.split("://", 1)[1].split("@", 1)[0].split(":", 1)[1]
    assert segment == quote(NEW_PW, safe=""), "口令段必须与 quote(safe='') 逐字一致"
    for ch in "/@:#?&=":
        assert ch not in segment, f"{ch!r} 必须被百分号编码"


def test_compose_preserves_host_db_and_query():
    url = mod._compose(NEW_PW, OLD_URL)
    parsed = make_url(url)
    assert parsed.drivername == "postgresql+psycopg2"
    assert parsed.host == "db.example.com"
    assert parsed.port == 5432
    assert parsed.database == "ezmanbo"
    assert parsed.query == {"sslmode": "require"}, "查询参数必须原样保留"


def test_compose_unquotes_username_from_old_url():
    url = mod._compose(NEW_PW, "postgresql://app%20user:pw@h.example.com:5432/db")
    assert make_url(url).username == "app user"


def test_compose_refuses_url_without_password():
    with pytest.raises(SystemExit):
        mod._compose(NEW_PW, "postgresql://app_user@h.example.com:5432/db")


# ── .env 改写的保真与原子性 ────────────────────────────────────────────


def test_write_replaces_only_database_url_line(tmp_path, monkeypatch):
    env = _write_env(tmp_path)
    assert _run(tmp_path, monkeypatch, env) == 0

    text = env.read_text()
    assert "# 注释行" in text
    assert "JWT_SECRET_KEY=abc" in text
    assert "HF_HOME=/mnt/data/.cache/huggingface" in text
    assert make_url(_value_of(env)).password == NEW_PW


@pytest.mark.parametrize("quote_char", ["", '"', "'"])
def test_quote_style_is_preserved(tmp_path, monkeypatch, quote_char):
    env = _write_env(tmp_path, quote_char=quote_char)
    _run(tmp_path, monkeypatch, env)
    raw = _value_of(env)
    assert raw.startswith(f"{quote_char}postgresql") and raw.endswith(quote_char)


def test_line_ending_is_preserved(tmp_path, monkeypatch):
    """该行的行尾（CRLF / 无换行）原样保留，不要把文件写成混合行尾。"""
    path = tmp_path / ".env"
    path.write_bytes(f"JWT_SECRET_KEY=abc\r\n{mod.KEY}={OLD_URL}".encode())
    os.chmod(path, 0o600)
    _run(tmp_path, monkeypatch, path)
    raw = path.read_bytes()
    assert raw.startswith(b"JWT_SECRET_KEY=abc\r\n"), "其它行的行尾不许被动"
    assert raw.split(b"\r\n", 1)[1].count(b"\n") == 0, "该行不该被换成裸 LF"
    assert not raw.endswith(b"\n"), "原本结尾无换行，改完也不该凭空加一个"


def test_backup_holds_old_content_and_mode(tmp_path, monkeypatch):
    env = _write_env(tmp_path)
    before = env.read_text()
    _run(tmp_path, monkeypatch, env)

    backups = [p for p in tmp_path.iterdir() if p.name.startswith(".env.bak.")]
    assert len(backups) == 1
    assert backups[0].read_text() == before
    assert stat.S_IMODE(backups[0].stat().st_mode) == 0o600
    assert stat.S_IMODE(env.stat().st_mode) == 0o600, "替换后权限不能变松"


def test_no_temp_file_left_behind(tmp_path, monkeypatch):
    env = _write_env(tmp_path)
    _run(tmp_path, monkeypatch, env)
    assert not [p for p in tmp_path.iterdir() if p.name.startswith(".env.tmp.")]


# ── 三条安全属性 ──────────────────────────────────────────────────────


def test_verify_failure_leaves_env_untouched(tmp_path, monkeypatch):
    """最重要的一条：连不上就一个字节都不许改，也不许留备份。"""
    env = _write_env(tmp_path)
    before = env.read_bytes()

    def boom(url):
        raise SystemExit("❌ 用新凭据连接失败：模拟")

    with pytest.raises(SystemExit):
        _run(tmp_path, monkeypatch, env, verify=boom)

    assert env.read_bytes() == before
    assert not [p for p in tmp_path.iterdir() if p.name.startswith(".env.bak.")]


def test_verify_detects_wrong_user(tmp_path, monkeypatch):
    """改错了用户（改的是别人）必须被拦下，而不是写进 .env。"""

    class _Result:
        def scalar(self):
            return "some_other_user"

    class _Conn:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def execute(self, *a, **k):
            return _Result()

    class _Engine:
        def connect(self):
            return _Conn()

        def dispose(self):
            pass

    monkeypatch.setattr(sqlalchemy, "create_engine", lambda *a, **k: _Engine())
    with pytest.raises(SystemExit) as err:
        mod._verify_connection(OLD_URL)
    assert "不一致" in str(err.value)


def test_dry_run_touches_nothing(tmp_path, monkeypatch):
    env = _write_env(tmp_path)
    before = env.read_bytes()
    assert _run(tmp_path, monkeypatch, env, argv=["--dry-run"]) == 0
    assert env.read_bytes() == before
    assert not [p for p in tmp_path.iterdir() if p.name.startswith(".env.bak.")]


def test_password_is_never_printed(tmp_path, monkeypatch, capsys):
    env = _write_env(tmp_path)
    _run(tmp_path, monkeypatch, env)
    out = capsys.readouterr()
    assert NEW_PW not in out.out and NEW_PW not in out.err
    for p in tmp_path.iterdir():
        assert NEW_PW not in p.name, "备份文件名里也不能带口令"


def test_masked_url_hides_password():
    masked = mod._mask(mod._compose(NEW_PW, OLD_URL))
    assert NEW_PW not in masked
    assert "***" in masked and "app_user" in masked


# ── 该拒绝的输入 ──────────────────────────────────────────────────────


def test_refuses_url_unsafe_for_dotenv(tmp_path, monkeypatch):
    """`$` 会被 dotenv 当变量展开，必须拒绝而不是写进去。"""
    env = _write_env(tmp_path, value="postgresql://u:p@h.example.com:5432/db?opt=$HOME")
    with pytest.raises(SystemExit) as err:
        _run(tmp_path, monkeypatch, env)
    assert "$" in str(err.value)
    assert env.read_bytes().decode().count("$HOME") == 1, "文件必须没被动过"


def test_refuses_missing_key(tmp_path, monkeypatch):
    path = tmp_path / ".env"
    path.write_text("JWT_SECRET_KEY=abc\n")
    with pytest.raises(SystemExit):
        _run(tmp_path, monkeypatch, path)


def test_refuses_short_password(tmp_path):
    monkeypatch_seq = iter(["short", "short"])
    orig = mod.getpass.getpass
    mod.getpass.getpass = lambda *a, **k: next(monkeypatch_seq)
    try:
        with pytest.raises(SystemExit):
            mod._prompt_password()
    finally:
        mod.getpass.getpass = orig


def test_refuses_mismatched_confirmation(tmp_path):
    seq = iter(["longenough1", "longenough2"])
    orig = mod.getpass.getpass
    mod.getpass.getpass = lambda *a, **k: next(seq)
    try:
        with pytest.raises(SystemExit):
            mod._prompt_password()
    finally:
        mod.getpass.getpass = orig
