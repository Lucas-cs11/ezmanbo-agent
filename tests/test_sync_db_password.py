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
from dotenv import dotenv_values
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
        mod, "_verify_connection", verify if verify is not None else (lambda url, secret: None)
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


def test_edits_the_line_dotenv_actually_uses(tmp_path, monkeypatch, capsys):
    """`.env` 里有两行 `DATABASE_URL` 时，dotenv 是「后者胜」——所以必须改**最后一行**。

    改错行的后果很坏：脚本打印「新凭据实连成功」并返回 0，而生产读到的仍是旧口令，
    于是「脚本说成功了、服务却连不上库」，且重跑永远不自愈。
    """
    stale = "postgresql://app_user:StalePw@db.example.com:5432/ezmanbo"
    path = tmp_path / ".env"
    path.write_text(f"{mod.KEY}={stale}\nJWT_SECRET_KEY=abc\n{mod.KEY}={OLD_URL}\n")
    os.chmod(path, 0o600)

    assert _run(tmp_path, monkeypatch, path) == 0

    lines = path.read_text().splitlines()
    assert "StalePw" in lines[0], "前面那行不许被动"
    assert make_url(lines[2].split("=", 1)[1]).password == NEW_PW
    assert make_url(dotenv_values(path)[mod.KEY]).password == NEW_PW, (
        "dotenv 实际读回来的必须就是新口令"
    )
    assert "2 行" in capsys.readouterr().out, "重复这件事必须说出来，不能默默改一行了事"


def test_export_prefixed_line_is_the_one_dotenv_uses(tmp_path, monkeypatch, capsys):
    """`export DATABASE_URL=...` dotenv 是认的——脚本必须认同一行。

    「哪一行绑定了这个键」必须由 dotenv 自己的语法决定；一旦脚本另立规则，
    就会出现「改了一行、应用读另一行」的假成功（上一版正是栽在这里）。
    """
    stale = "postgresql://app_user:StalePw@db.example.com:5432/ezmanbo"
    path = tmp_path / ".env"
    path.write_text(f"{mod.KEY}={stale}\nexport {mod.KEY}={OLD_URL}\n")
    os.chmod(path, 0o600)

    assert _run(tmp_path, monkeypatch, path) == 0

    lines = path.read_text().splitlines()
    assert "StalePw" in lines[0], "前面那行不许被动"
    assert lines[1].startswith(f"export {mod.KEY}="), "`export ` 前缀必须原样保留"
    assert make_url(dotenv_values(path)[mod.KEY]).password == NEW_PW, (
        "dotenv 实际读回来的必须就是新口令"
    )
    assert "2 行" in capsys.readouterr().out, "重复这件事必须说出来"


def test_export_prefixed_line_alone_is_found(tmp_path, monkeypatch):
    """只有一行 `export DATABASE_URL=...` 时也要认出来，而不是报「找不到」。"""
    path = tmp_path / ".env"
    path.write_text(f"export {mod.KEY}={OLD_URL}\n")
    os.chmod(path, 0o600)
    assert _run(tmp_path, monkeypatch, path) == 0
    assert make_url(dotenv_values(path)[mod.KEY]).password == NEW_PW


def test_quoted_and_commented_keys_are_not_touched(tmp_path, monkeypatch):
    """这些写法 dotenv **不**绑定 `DATABASE_URL`，脚本也必须同样无视它们。"""
    path = tmp_path / ".env"
    path.write_text(
        '#DATABASE_URL=postgresql://u:Commented@h:5432/d\n'
        'EXPORT DATABASE_URL=postgresql://u:Upper@h:5432/d\n'
        'database_url=postgresql://u:Lower@h:5432/d\n'
        f'{mod.KEY}={OLD_URL}\n'
    )
    os.chmod(path, 0o600)
    assert _run(tmp_path, monkeypatch, path) == 0
    out = path.read_text()
    assert "Commented" in out and "Upper" in out and "Lower" in out, "无关行不许被动"
    assert make_url(dotenv_values(path)[mod.KEY]).password == NEW_PW


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

    def boom(url, secret):
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
        mod._verify_connection(OLD_URL, NEW_PW)
    assert "不一致" in str(err.value)


def test_leaking_exception_is_scrubbed(monkeypatch):
    """`_scrub` 是防御层：这里用构造出来的「会带出口令的异常」钉住它的契约。

    注意：在当前 SQLAlchemy 上，真实的失败路径（解析失败 / 驱动不存在 / 端口非法 /
    连接被拒）**都没有**回显口令，所以这条用例是**防回归**，不是对一个已知泄漏的复现。
    """
    url = mod._compose(NEW_PW, OLD_URL)

    def explode(*a, **k):
        from sqlalchemy.exc import ArgumentError

        raise ArgumentError(f"Could not parse SQLAlchemy URL from string '{url}'")

    monkeypatch.setattr(sqlalchemy, "create_engine", explode)
    with pytest.raises(SystemExit) as err:
        mod._verify_connection(url, NEW_PW)

    message = str(err.value)
    assert NEW_PW not in message, "原始口令不得出现在报错里"
    assert quote(NEW_PW, safe="") not in message, "百分号编码后的口令同样不得出现"
    assert "***" in message, "应当留下擦除痕迹，而不是把整行删掉"
    assert "未改动" in message, "必须告诉使用者 .env 没被动过"


def test_dry_run_touches_nothing(tmp_path, monkeypatch):
    env = _write_env(tmp_path)
    before = env.read_bytes()
    assert _run(tmp_path, monkeypatch, env, argv=["--dry-run"]) == 0
    assert env.read_bytes() == before
    assert not [p for p in tmp_path.iterdir() if p.name.startswith(".env.bak.")]


def test_password_is_never_printed(tmp_path, monkeypatch, capsys):
    """stdout/stderr 与备份文件名里都不许出现口令——**编码形态同样算口令**
    （`N3w%2Fpw%40ss...` 是能直接拿去连库的凭据，不是「已脱敏」）。"""
    env = _write_env(tmp_path)
    _run(tmp_path, monkeypatch, env)
    out = capsys.readouterr()
    for form in (NEW_PW, quote(NEW_PW, safe="")):
        assert form not in out.out, f"stdout 泄漏了口令：{form}"
        assert form not in out.err, f"stderr 泄漏了口令：{form}"
    for p in tmp_path.iterdir():
        assert NEW_PW not in p.name, "备份文件名里也不能带口令"


def test_masked_url_hides_password_and_keeps_port():
    masked = mod._mask(mod._compose(NEW_PW, OLD_URL))
    assert NEW_PW not in masked and quote(NEW_PW, safe="") not in masked
    assert "***" in masked and "app_user" in masked
    assert "db.example.com:5432" in masked, "掩码后的展示信息不该丢掉端口"


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


def test_refuses_non_numeric_port(tmp_path, monkeypatch):
    """端口非法要给一句人能看懂的话，而不是 `urlsplit` 的裸 ValueError traceback。"""
    env = _write_env(tmp_path, value="postgresql://app_user:pw@db.example.com:notaport/ezmanbo")
    before = env.read_bytes()
    with pytest.raises(SystemExit) as err:
        _run(tmp_path, monkeypatch, env)
    assert "端口" in str(err.value)
    assert env.read_bytes() == before


@pytest.mark.skipif(os.geteuid() == 0, reason="root 无视目录权限，这条测不出来")
def test_readonly_dir_is_refused_cleanly(tmp_path, monkeypatch):
    """目录只读（连临时文件都建不出来）：.env 原样，不留任何残留。

    注意这条覆盖的是「一开始就写不了」；「写到一半失败」由下面两条 rename 用例覆盖。
    """
    env = _write_env(tmp_path)
    before = env.read_bytes()
    os.chmod(tmp_path, 0o500)
    try:
        with pytest.raises(SystemExit) as err:
            _run(tmp_path, monkeypatch, env)
    finally:
        os.chmod(tmp_path, 0o700)

    assert "写" in str(err.value), "要说清是写盘失败"
    assert env.read_bytes() == before
    assert not _leftovers(tmp_path), f"留下了残留：{_leftovers(tmp_path)}"


def _leftovers(tmp_path):
    return [p.name for p in tmp_path.iterdir() if p.name.startswith(".env.tmp.")]


def _flaky_replace(monkeypatch, fail_on: int):
    """让第 fail_on 次 `os.replace` 报 ENOSPC（模拟写满/换名失败）。"""
    real = os.replace
    state = {"n": 0}

    def flaky(src, dst):
        state["n"] += 1
        if state["n"] == fail_on:
            raise OSError(28, "No space left on device")
        return real(src, dst)

    monkeypatch.setattr(mod.os, "replace", flaky)


def test_rename_failure_on_backup_leaves_env_intact(tmp_path, monkeypatch):
    """备份那一步就换名失败：.env 原样，且不许留下临时文件。"""
    env = _write_env(tmp_path)
    before = env.read_bytes()
    _flaky_replace(monkeypatch, fail_on=1)

    with pytest.raises(SystemExit):
        _run(tmp_path, monkeypatch, env)

    assert env.read_bytes() == before
    assert not _leftovers(tmp_path), f"留下了孤儿临时文件：{_leftovers(tmp_path)}"
    assert not [p for p in tmp_path.iterdir() if p.name.startswith(".env.bak.")]


def test_rename_failure_on_env_after_backup(tmp_path, monkeypatch):
    """备份成功、替换 .env 时才换名失败：.env 原样、备份完好、无孤儿临时文件。"""
    env = _write_env(tmp_path)
    before = env.read_bytes()
    _flaky_replace(monkeypatch, fail_on=2)

    with pytest.raises(SystemExit) as err:
        _run(tmp_path, monkeypatch, env)

    assert "写" in str(err.value)
    assert env.read_bytes() == before
    assert not _leftovers(tmp_path), f"留下了孤儿临时文件：{_leftovers(tmp_path)}"
    backups = [p for p in tmp_path.iterdir() if p.name.startswith(".env.bak.")]
    assert len(backups) == 1 and backups[0].read_bytes() == before


def test_stage_failure_leaves_no_leftovers(tmp_path, monkeypatch):
    """内容写到一半就失败（copyfile 报 ENOSPC）：.env 原样，临时文件自己收掉。"""
    env = _write_env(tmp_path)
    before = env.read_bytes()

    def boom(*a, **k):
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(mod.shutil, "copyfile", boom)
    with pytest.raises(SystemExit):
        _run(tmp_path, monkeypatch, env)

    assert env.read_bytes() == before
    assert not _leftovers(tmp_path), f"留下了孤儿临时文件：{_leftovers(tmp_path)}"


class _FrozenDatetime:
    """把备份时间戳钉死在同一秒，用来验证「同秒两次运行」的行为。"""

    @staticmethod
    def now(tz=None):
        from datetime import datetime as _dt
        from datetime import timezone as _tz

        return _dt(2026, 9, 27, 12, 0, 0, tzinfo=_tz.utc)


def test_backup_names_do_not_collide_within_one_second(tmp_path, monkeypatch):
    """备份名精确到秒，同一秒内跑两次**不许静默覆盖**——否则最初的状态就丢了。"""
    monkeypatch.setattr(mod, "datetime", _FrozenDatetime)
    env = _write_env(tmp_path)
    original = env.read_text()

    _run(tmp_path, monkeypatch, env)
    after_first = env.read_text()
    _run(tmp_path, monkeypatch, env)

    names = sorted(p.name for p in tmp_path.iterdir() if p.name.startswith(".env.bak."))
    assert len(names) == 2, f"两次运行必须留两份备份，实际只有：{names}"
    assert (tmp_path / names[0]).read_text() == original, "最早那份备份必须还是最初的内容"
    assert (tmp_path / names[1]).read_text() == after_first


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
