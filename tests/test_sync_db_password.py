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
from urllib.parse import quote, unquote

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
        mod, "_verify_connection", verify if verify is not None else (lambda *a, **k: None)
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


def _assert_invariant(path):
    """本脚本对外承诺的不变量：改完之后，**应用会读到的那一行**就是新口令。"""
    got = dotenv_values(path)[mod.KEY]
    assert got is not None, "dotenv 读不到 DATABASE_URL 了"
    assert unquote(make_url(got).password or "") == NEW_PW, (
        f"dotenv 实际读到的不是新口令：{got!r}"
    )


# 各种「dotenv 会怎么解析」的写法，跑完都必须满足上面那条不变量
TRICKY_ENVS = {
    "单行": f"{mod.KEY}={OLD_URL}\n",
    "export 前缀": f"export {mod.KEY}={OLD_URL}\n",
    "export 后多空格": f"export   {mod.KEY}={OLD_URL}\n",
    "缩进 + export": f"   export  {mod.KEY}={OLD_URL}\n",
    "等号两侧留白": f"{mod.KEY} = {OLD_URL}\n",
    "单引号值": f"{mod.KEY}='{OLD_URL}'\n",
    "双引号值": f'{mod.KEY}="{OLD_URL}"\n',
    "单引号键": f"'{mod.KEY}'={OLD_URL}\n",
    "行尾注释": f"{mod.KEY}={OLD_URL} # 旧口令\n",
    "两行普通（后者胜）": f"{mod.KEY}=postgresql://u:a@h:5432/d\n{mod.KEY}={OLD_URL}\n",
    "普通 + export": f"{mod.KEY}=postgresql://u:a@h:5432/d\nexport {mod.KEY}={OLD_URL}\n",
    "中间夹一堆无关键": (
        f"# 注释\n\n{mod.KEY}={OLD_URL}\nJWT=x\nOTHER=y\n\n# 尾注\n"
    ),
    "CRLF": f"JWT=x\r\n{mod.KEY}={OLD_URL}\r\n",
    "末行无换行": f"JWT=x\n{mod.KEY}={OLD_URL}",
    # 前面那行的引号没闭合、把中间吞进值里，但**最后一个**绑定仍是普通行：
    # dotenv 取后者，脚本就该改后者（这一条曾经被我误判成「必须拒绝」）
    "跨行值在前 + 正常行在后": (
        f'{mod.KEY}="postgresql://u:Old@h:5432/d\n继续"\n{mod.KEY}={OLD_URL}\n'
    ),
}


@pytest.mark.parametrize("name", sorted(TRICKY_ENVS))
def test_invariant_holds_for_every_env_shape(tmp_path, monkeypatch, name):
    """不变量：无论 `.env` 长什么样，跑完 dotenv 读回的必须是新口令。

    这条用例比「改没改某一行」更贴近承诺——上一版把每一行单独喂给流解析器，在「引号
    跨行」的 `.env` 上就会改错行，而脚本照样返回 0、打印「已写入」。
    """
    path = tmp_path / ".env"
    path.write_text(TRICKY_ENVS[name])
    os.chmod(path, 0o600)

    assert _run(tmp_path, monkeypatch, path) == 0
    _assert_invariant(path)


@pytest.mark.parametrize(
    "body",
    [
        # 引号不闭合：dotenv 会把后面那行当成同一个值，全文只绑定第一行
        f'{mod.KEY}="x\n{mod.KEY}={OLD_URL}\n"\n',
        # 唯一那个绑定自身跨行（值里有换行），改哪一行都说不清
        f'JWT=x\n{mod.KEY}="postgresql://u:Old@h:5432/d\n继续"\n',
        # 带 BOM：不同版本 dotenv 对「哪一行生效」判断不同，脚本不猜
        f"\ufeff{mod.KEY}={OLD_URL}\n",
    ],
)
def test_refuses_ambiguous_or_bom_env_untouched(tmp_path, monkeypatch, body):
    """这些形态脚本**拒绝执行**，且 `.env` 逐字节不动——拒绝是正确行为，不是失败。"""
    path = tmp_path / ".env"
    path.write_text(body, encoding="utf-8")
    os.chmod(path, 0o600)
    before = path.read_bytes()

    with pytest.raises(SystemExit):
        _run(tmp_path, monkeypatch, path)

    assert path.read_bytes() == before, "拒绝执行时不许动文件"
    assert not [p for p in tmp_path.iterdir() if p.name.startswith(".env.bak.")]


def test_effective_value_gate_blocks_the_write(tmp_path, monkeypatch):
    """最后那道闸门必须承重：万一改完 dotenv 读到的不是新连接串，就不许写盘。

    这是防「定位逻辑又跑偏」的兜底——闸门失效的话，前面所有定位代码的正确性就没人守了。
    """
    env = _write_env(tmp_path)
    before = env.read_bytes()
    monkeypatch.setattr(mod, "_effective_value", lambda content: "postgresql://u:Stale@h/db")

    with pytest.raises(SystemExit) as err:
        _run(tmp_path, monkeypatch, env)

    assert "未改动" in str(err.value)
    assert env.read_bytes() == before
    assert not [p for p in tmp_path.iterdir() if p.name.startswith(".env.bak.")]


def test_gate_failure_never_echoes_the_stale_value(tmp_path, monkeypatch, capsys):
    """闸门失败时的提示不许把「读到的那段内容」打出来——那可能是旧口令。"""
    env = _write_env(tmp_path)
    monkeypatch.setattr(mod, "_effective_value", lambda content: "postgresql://u:LeakyOldPw@h/db")

    with pytest.raises(SystemExit) as err:
        _run(tmp_path, monkeypatch, env)

    assert "LeakyOldPw" not in str(err.value)
    assert "LeakyOldPw" not in capsys.readouterr().out


def test_split_lines_matches_dotenv_line_boundaries():
    """切行必须与 dotenv 的行界一致，否则行号会错位（`splitlines` 会多切 \\v、\\x85）。"""
    content = "A=1\r\nB=2\rC=3\nD=4"
    assert mod._split_lines(content) == ["A=1\r\n", "B=2\r", "C=3\n", "D=4"]
    assert "".join(mod._split_lines(content)) == content, "切了再拼必须逐字节还原"
    assert mod._line_index(content, 0) == 0
    assert mod._line_index(content, len("A=1\r\nB=2\r")) == 2


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

    def boom(url, *secrets):
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


# 口令被同时写在 query 里：`_compose` 对 query 是**逐字保留**的，所以那里留下的是旧口令。
# 两种写法各钉一条：query 里是**编码形态**、以及 query 里是**原文**（userinfo 里反而是编码）。
# 后者是第五轮验收的变异 M3 暴露出来的——`_variants` 少列「原文」这一格时，只有它变红。
PASSWORD_IN_QUERY_URL = (
    "postgresql+psycopg2://app_user:OldPw%40x@db.example.com:5432/ezmanbo?password=OldPw%40x"
)
RAW_PW_IN_QUERY_URL = (
    "postgresql+psycopg2://app_user:OldPw%40x@db.example.com:5432/ezmanbo?password=OldPw@x"
)
OLD_PW_FORMS = ("OldPw@x", "OldPw%40x")


def test_masked_url_scrubs_password_repeated_in_query():
    """换掉 userinfo 段盖不住写在同一串 query 里的那份口令（第四轮验收查出的低级泄漏）。

    这里 query 里的是**旧**口令——`_compose` 逐字保留 query——所以调用方必须把旧口令
    交给 `_mask`，它才知道要擦什么。
    """
    new = mod._compose(NEW_PW, PASSWORD_IN_QUERY_URL)
    masked = mod._mask(new, mod._password_of(PASSWORD_IN_QUERY_URL))
    for form in (*OLD_PW_FORMS, NEW_PW, quote(NEW_PW, safe="")):
        assert form not in masked, f"掩码后仍泄漏：{form}"
    assert "***" in masked and "app_user" in masked


def test_old_password_repeated_in_query_is_never_printed(tmp_path, monkeypatch, capsys):
    """同一件事走完整 `main()`：终端上不许出现旧口令或新口令的任一形态。"""
    env = _write_env(tmp_path, value=PASSWORD_IN_QUERY_URL)
    assert _run(tmp_path, monkeypatch, env) == 0
    out = capsys.readouterr()
    for form in (*OLD_PW_FORMS, NEW_PW, quote(NEW_PW, safe="")):
        assert form not in out.out, f"stdout 泄漏了口令：{form}"
        assert form not in out.err, f"stderr 泄漏了口令：{form}"


def test_raw_old_password_in_query_is_never_printed(tmp_path, monkeypatch, capsys):
    """query 里写的是旧口令的**原文**——只认编码形态的实现会在这里漏。"""
    env = _write_env(tmp_path, value=RAW_PW_IN_QUERY_URL)
    assert _run(tmp_path, monkeypatch, env) == 0
    out = capsys.readouterr()
    for form in (*OLD_PW_FORMS, NEW_PW):
        assert form not in out.out, f"stdout 泄漏了口令：{form}"
        assert form not in out.err, f"stderr 泄漏了口令：{form}"


def test_main_hands_the_old_password_to_verify_so_errors_are_scrubbed(tmp_path, monkeypatch):
    """真用 `_verify_connection`，让第三方异常回显整条 URL。

    这条钉的是「`main` 必须把旧口令交给 `_verify_connection`」：少传一个参数，报错里
    就会重新出现 query 里的旧口令（第五轮验收的变异 M6 就是靠这个存活的）。
    """
    env = _write_env(tmp_path, value=RAW_PW_IN_QUERY_URL)
    before = env.read_bytes()
    new_url = mod._compose(NEW_PW, RAW_PW_IN_QUERY_URL)

    def explode(*a, **k):
        from sqlalchemy.exc import ArgumentError

        raise ArgumentError(f"Could not parse SQLAlchemy URL from string '{new_url}'")

    monkeypatch.setattr(mod, "_prompt_password", lambda: NEW_PW)
    monkeypatch.setattr(sqlalchemy, "create_engine", explode)

    with pytest.raises(SystemExit) as err:
        mod.main(["--env", str(env)])

    message = str(err.value)
    for form in (*OLD_PW_FORMS, NEW_PW, quote(NEW_PW, safe="")):
        assert form not in message, f"报错里泄漏了口令：{form}"
    assert "未改动" in message, "必须告诉使用者 .env 没被动过"
    assert env.read_bytes() == before, "验证失败时 .env 一个字节都不许改"


def test_scrub_covers_lowercase_hex_escapes():
    """同一段口令，有的库编码成 `%2F`、有的编码成 `%2f`——两种都得算口令。"""
    secret = "p/w@d"
    textured = f"boom {quote(secret, safe='').lower()}"
    scrubbed = mod._scrub(textured, secret)
    assert quote(secret, safe="").lower() not in scrubbed
    assert "***" in scrubbed, "应当留下擦除痕迹，而不是把整行删掉"


def test_variants_covers_password_that_itself_contains_a_percent():
    """口令自身含 `%` 时，`%25` 会先被非重叠匹配吃掉，十六进制降级产不出小写形态。

    也就是第五轮验收查出的「`%25` 盲区」：`abc%2Fdef` 编码成 `abc%252Fdef`，缺的是
    `abc%252fdef`。`_variants` 里那个整串 `.lower()` 就是补这一格。
    """
    secret = "abc%2Fdef"
    assert "abc%252fdef" in mod._variants(secret), "小写十六进制形态必须在列"
    scrubbed = mod._scrub("boom abc%252fdef", secret)
    assert "abc%252fdef" not in scrubbed
    assert "***" in scrubbed


def test_mask_scrubs_the_secrets_it_is_given_even_without_a_userinfo_password():
    """没有 userinfo 口令时也不许静默跳过擦除——「传了 secret 却没擦」是个静默的坑。"""
    masked = mod._mask("postgresql://db.internal:5432/ezmanbo?password=OldPw@x", "OldPw@x")
    assert "OldPw@x" not in masked


def test_scrub_ignores_an_empty_secret():
    """空串不是口令：`text.replace("", …)` 会在每个字符之间插 `***`，把信息毁掉。

    `_password_of` 在 URL 没有口令字段时返回 `""`，而 `_mask` 现在无条件把 secret 交给
    `_scrub`——所以这层守卫是活的，不是摆设。
    """
    assert mod._scrub("boom", "") == "boom"


# 口令被写在 URL 的 **path** 里（少见但合法，`_mask` 的 docstring 自己就这么说）。
# 第六轮验收的 `repro_leak.py` 就是拿它打穿了旧版：展示行里有一句**没走 `_mask`** 的
# `库：{path}`，于是原文直接打到终端。三种形态（原文/大写编码/小写编码）全中。
PATH_PW_URL = "postgresql://app_user:OldPw%2Fxy@db.example.com:5432/OldPw/xy"
PATH_PW_FORMS = ("OldPw/xy", "OldPw%2Fxy", "OldPw%2fxy")


def test_mask_hides_a_path_that_carries_the_password():
    """path 里的口令是**整段隐去**，不是逐字擦——逐字擦要先知道它的编码形态。"""
    masked = mod._mask(PATH_PW_URL, mod._password_of(PATH_PW_URL))
    for form in PATH_PW_FORMS:
        assert form not in masked, f"掩码后仍泄漏：{form}"
    assert "db.example.com:5432" in masked, "主机与端口仍应可见"
    assert "/***" in masked, "被隐去的 path 要留下痕迹，让人看得出这里被掩了"


def test_main_never_prints_a_path_carried_password(tmp_path, monkeypatch, capsys):
    """这条走完整 `main()`：终端上不许出现 path 里那份口令的任何形态。

    旧版在这里打印 `库：OldPw/xy`——**根本没经过 `_mask`**。所以光钉 `_mask` 不够，
    必须钉住「终端输出里不含它」，否则删掉那一行 print 又加回来也没人拦。
    """
    env = _write_env(tmp_path, value=PATH_PW_URL)
    assert _run(tmp_path, monkeypatch, env, argv=("--dry-run",)) == 0
    out = capsys.readouterr()
    both = out.out + out.err
    for form in (*PATH_PW_FORMS, NEW_PW, quote(NEW_PW, safe="")):
        assert form not in both, f"终端泄漏了口令：{form}"
    assert "库：" not in out.out, "库名不再单独打印（那一行是漏的源头）"
    # 第七轮验收指出：`用户：` / `主机：` 两行也不走 `_mask`，且与「将写入」那行信息
    # 重复、造成「同一屏里主机一处掩、一处不掩」的展示不一致。已删，这里钉住它不再回来。
    assert "用户：" not in out.out and "主机：" not in out.out, "那两行不该再打印"


# 口令不是「整体编码」而是**部分编码**时，逐形态擦除同样认不出来。第六轮验收自造的
# `A%20B/c`（空格编码、斜杠不编码）与 `A+B%2Fc`（表单编码）两种写法都漏了。
# `_decodes_to_secret` 解到不动点，就是为这一类准备的。
PARTIAL_PW = "A B/c"


@pytest.mark.parametrize("spelling", ["A%20B/c", "A+B%2Fc", "A%20B%2Fc", "A B/c"])
def test_mask_hides_partially_encoded_password_in_query(spelling):
    url = f"postgresql://u:Old@h:5432/db?password={spelling}"
    masked = mod._mask(url, PARTIAL_PW)
    assert spelling not in masked, f"掩码后仍泄漏：{spelling}"
    assert "?***" in masked, "query 整段隐去后要留下痕迹"


def test_mask_hides_nested_encoding_in_path():
    """嵌套编码要盖住：口令 `x/y` 编码成 `x%2Fy`、再整体编码成 `x%252Fy`。

    解一层得到 `x%2Fy`（仍不是原文），解两层才得到 `x/y`——所以逐形态比对必然漏，
    只有解到不动点才认得出。
    """
    url = f"postgresql://h:5432/db/{quote(quote('x/y', safe=''), safe='')}"
    assert url.endswith("x%252Fy"), "构造前提：path 里是两层编码形态"
    masked = mod._mask(url, "x/y")
    assert "x%252Fy" not in masked, "两层形态不许留"
    assert "x%2Fy" not in masked, "解一层后的形态也不许留"
    assert "/***" in masked


# 第七轮验收实测出的残留：原先解码**封顶 4 层**（`_MAX_DECODE_LAYERS`），于是 5 层嵌套
# 就漏掩了——终端会把 5 层编码形态原样打出来。修法不是把 4 改成 8，而是**去掉层数上限**：
# 每次有效解码都让串变短，解到不动点必然在 len(component) 步内结束（论证见脚本 docstring）。
@pytest.mark.parametrize("layers", [5, 8, 12])
def test_mask_hides_deeply_nested_encoding(layers):
    spelling = "a/b"
    encoded = spelling
    for _ in range(layers):
        encoded = quote(encoded, safe="")
    assert encoded != spelling and encoded.count("%25") >= 1, "构造前提：确实被编码过"
    # 逐层数清「真的嵌了这么多层」：少解一层就还原不出原文，多解一层刚好还原。
    # （比数 `%25` 的个数可靠——`%25` 是**非重叠**匹配，层数一多就数不准。）
    partial = encoded
    for _ in range(layers - 1):
        partial = unquote(partial)
    assert partial != spelling, f"构造前提：{layers} 层编码少解一层不该到原文"
    assert unquote(partial) == spelling, f"构造前提：再解一层才是原文"
    url = f"postgresql://h:5432/db/{encoded}"
    masked = mod._mask(url, spelling)
    assert encoded not in masked, f"{layers} 层嵌套形态不许留"
    assert "/***" in masked, f"{layers} 层嵌套没被认出来——这正是第七轮报的漏掩"


def test_decodes_to_secret_terminates_on_hostile_input():
    """兜底上界必须真的存在：由 `%` 与 `+` 堆成的长串不能把解码循环转死或转爆。

    这条守的是「去掉层数上限」引入的新风险——上限没了，万一某个输入不收敛就是死循环。
    """
    hostile = "%25" * 500 + "+" * 500
    assert mod._decodes_to_secret(hostile, "绝不会出现的口令") is False


def test_mask_keeps_harmless_path_and_query_readable():
    """反向的钉子：掩码不是把整串打成 `***`。

    本用例守住过度掩码——把 `/ezmanbo?sslmode=require` 也抹掉，使用者就失去了「我改的
    是不是这个库」这唯一的人眼确认点。
    """
    masked = mod._mask(mod._compose(NEW_PW, OLD_URL))
    assert "/ezmanbo" in masked and "sslmode=require" in masked
    assert "/***" not in masked and "?***" not in masked


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
