#!/usr/bin/env python3
"""把新的数据库口令安全地同步进仓库根目录的 `.env`。

**为什么需要它**：口令里只要出现 `@ : / # ? & =` 这类字符，写进 `DATABASE_URL`
就必须做百分号编码，手改极易写坏；写坏 `.env` 的后果是线上连不上库。

**它不做什么**：不执行 `ALTER ROLE`、不改库里的口令。口令改在哪里由你决定
（RDS 控制台，或库内 `\\password`）；本脚本只负责把 `.env` 里 `DATABASE_URL`
所用**那个用户**的新口令同步进去——所以请先确认你改的就是这个用户。

用法（在仓库根目录下）：

    venv/bin/python scripts/sync_db_password.py            # 交互输入新口令（不回显）
    venv/bin/python scripts/sync_db_password.py --dry-run  # 只看将要写什么，不落盘

可选参数：

    --no-verify   跳过「用新凭据实连验证」这一步（仅在库暂时连不上时使用）
    --env PATH    指定 `.env` 路径（默认仓库根目录）

**安全约定**：口令全程不回显、不写日志、不进 shell 历史；**写盘前先用新凭据实连
一次**，连得上才替换 `.env`；替换是原子的（同目录临时文件 + `os.replace`），旧文件
留备份（`.env.bak.<UTC 时间戳>`），文件权限保持不变。

`.env` 里若出现**多行**绑定同一个键（包括 `export DATABASE_URL=...` 这种写法），
python-dotenv 是「后者胜」，所以本脚本改的是**最后一行**——也就是应用真正会读到的那行
——并就把前面几行的行号报警给你。

「哪一行算了绑定这个键」不由本脚本自己判定，而是整份文件交给 dotenv 的解析器、直接用它
给出的行号。原因是这里栽过三次：自写规则漏掉 `export` 前缀；把每一行**单独**喂给流解析器，
而引号可以跨行把后面的行吞进值里。三次的后果都是同一个——脚本打印「已写入」并返回 0，
应用读到的却是另一行，重跑也不自愈。

因此写盘前还有最后一道闸门：**用 dotenv 把改完的内容复读一遍**，读到的必须就是新连接串，
否则中止且 `.env` 一字不动。带 BOM 的文件、值跨行的文件，脚本直接拒绝而不是猜。
"""

import argparse
import getpass
import io
import os
import re
import shutil
import stat
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit, urlunsplit

from dotenv import dotenv_values
from dotenv.parser import parse_stream

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ENV = REPO_ROOT / ".env"
KEY = "DATABASE_URL"
MIN_PASSWORD_LEN = 8


def _quote_style(raw: str) -> str:
    """原行用的引号（只用于保持外观；**值**一律以 dotenv 解析出来的为准）。"""
    s = raw.lstrip()
    if s[:1] in ('"', "'") and s[:1] in s[1:]:
        return s[0]
    return ""


# dotenv 认的行界就是这三个（见 dotenv.parser._newline）
_NEWLINE = re.compile(r"\r\n|\n|\r")
_TRAILING_NEWLINE = re.compile(r"(?:\r\n|\n|\r)\Z")


def _split_lines(content: str) -> list[str]:
    """按 dotenv 认的行界切行并保留行尾。

    刻意不用 `str.splitlines()`：它还会在 `\\v`、`\\f`、`\\x85` 等处切，比 dotenv 多切出
    一些行，行号就跟 dotenv 对不上了——而这里的行号要拿去改文件。
    """
    parts, last = [], 0
    for m in _NEWLINE.finditer(content):
        parts.append(content[last : m.end()])
        last = m.end()
    if last < len(content):
        parts.append(content[last:])
    return parts


def _line_index(content: str, offset: int) -> int:
    """字符偏移 → 0 起算的行号。"""
    return len(_NEWLINE.findall(content, 0, offset))


def _key_bindings(content: str) -> list[tuple[int, int, str | None]]:
    """所有**真正绑定** KEY 的位置，返回 [(关键行号, 该 binding 的结束行号, 解析出的值)]。

    判定完全交给 python-dotenv 的**整文件**解析。这里踩过三次坑：先自己写「`=` 左边等于
    key」的规则（漏掉 `export DATABASE_URL=`）；再把每一行单独喂给 `parse_stream`——而它是
    **流**解析器，引号能跨行把后面的行吞进值里，逐行 ≠ 整文件；最后是拿 `endpos` 数行号，
    在 CRLF 上把结尾的 `\\r` 当成一个换行。三次的后果都是「脚本改一行、应用读另一行」，
    所以现在行号按 binding 原文内部的换行数推算，值也直接取 dotenv 解析出来的结果。
    """
    out: list[tuple[int, int, str | None]] = []
    offset = 0
    for binding in parse_stream(io.StringIO(content)):
        text = binding.original.string
        start, offset = offset, offset + len(text)
        if binding.error or binding.key != KEY:
            continue
        # 一个 binding 的原文可能带前导空白（含换行），键本身在它之后
        lead = re.match(r"\s*", text).end()
        key_line = _line_index(content, start + lead)
        inner = len(_NEWLINE.findall(text, lead))  # 键之后该 binding 内部的换行数
        if inner == 0:
            end_line = key_line
        elif _TRAILING_NEWLINE.search(text):
            end_line = key_line + inner - 1  # 结尾那个换行只负责收掉最后一行
        else:
            end_line = key_line + inner
        out.append((key_line, end_line, binding.value))
    return out


def _effective_value(content: str) -> str | None:
    """**用应用自己的方式**读一遍：python-dotenv 解析这份内容时，最终给 KEY 什么值。

    `load_dotenv(override=True)` 与 `dotenv_values` 在这件事上取的都是「最后一个绑定」，
    且默认都做 `${VAR}` 插值，所以拿它当判据与应用一致。
    """
    return dotenv_values(stream=io.StringIO(content)).get(KEY)


def _assert_effective(content: str, want: str, key_line: int) -> None:
    """写盘前的硬闸门：改完之后用 dotenv 复读，拿到的必须**就是**新连接串。

    这是本脚本唯一的正确性支柱。定位逻辑一旦与 dotenv 分歧（历史上发生过三次），
    就在这里被拦下——**宁可不写**，也不写出一份「脚本说成功、应用读到的却是别的」
    的 `.env`。失败信息里不回显读到的东西，那可能是旧口令。
    """
    got = _effective_value(content)
    if got != want:
        where = "空" if got is None else "另一段内容"
        raise SystemExit(
            f"❌ 改完第 {key_line + 1} 行后用 python-dotenv 复读，读到的**不是**新连接串"
            f"（读到的是{where}）。\n"
            "   已中止，.env **未改动**。这个 .env 里有脚本没料到的写法，请手工改这一行。"
        )


def _port_of(parts) -> int | None:
    """取端口；`urlsplit` 遇到非数字端口才抛错，这里换成能看懂的提示。"""
    try:
        return parts.port
    except ValueError:
        raise SystemExit(
            "❌ DATABASE_URL 里的端口不是数字。请在 .env 里先手工修好再跑本脚本"
            "（未改动任何文件）。"
        ) from None


def _compose(new_password: str, old_url: str) -> str:
    """用新口令重组成连接串，其中口令做百分号编码。其余部分逐字保留。"""
    parts = urlsplit(old_url)
    if parts.password is None:
        raise SystemExit("❌ 当前 DATABASE_URL 里没有口令字段，无法同步（是否用了 IAM 认证？）。")
    user = unquote(parts.username or "")
    netloc = f"{quote(user, safe='')}:{quote(new_password, safe='')}@{parts.hostname or ''}"
    port = _port_of(parts)
    if port:
        netloc += f":{port}"
    return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))


def _assert_env_safe(url: str, quote_char: str) -> None:
    """拒绝会被 .env 读法改写的写法。

    `python-dotenv` 对**有引号和无引号**的值都会做 `${VAR}` 展开，所以 `$` 一律不许
    出现；无引号时还会被空白与 `#` 截断。
    """
    bad = []
    if "$" in url:
        bad.append("$（dotenv 会当成变量展开）")
    if "\n" in url or "\r" in url:
        bad.append("换行")
    if quote_char:
        if quote_char in url:
            bad.append(f"{quote_char}（会提前闭合引号）")
    else:
        for ch in " \t#'\"":
            if ch in url:
                bad.append(repr(ch))
    if bad:
        raise SystemExit(
            "❌ 拼好的连接串含有不适合写进 .env 的字符："
            + "、".join(sorted(set(bad)))
            + "\n   请检查 DATABASE_URL 里除口令外的部分（手工修好后再跑本脚本）。"
        )


def _password_of(url: str) -> str:
    return unquote(urlsplit(url).password or "")


def _mask(url: str, *also_secrets: str) -> str:
    """展示用的连接串：userinfo 段的口令换成 `***`，另外把 `also_secrets` 也一并擦掉。

    只换 userinfo 是不够的：口令可能同时被写在 path/query 里（少见但合法），而
    `_compose` 对 query 是逐字保留的——那里留着的往往是**上一个**口令，所以调用方必须
    把旧口令也交进来，否则它会被原样打到终端。
    """
    parts = urlsplit(url)
    if parts.password is None:
        return url
    netloc = f"{parts.username}:***@{parts.hostname or ''}"
    port = _port_of(parts)
    if port:
        netloc += f":{port}"
    masked = urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))
    return _scrub(masked, _password_of(url), *also_secrets)


def _prompt_password() -> str:
    pw = getpass.getpass("数据库新口令（输入时不回显）: ")
    if len(pw) < MIN_PASSWORD_LEN:
        raise SystemExit(f"❌ 口令至少 {MIN_PASSWORD_LEN} 位")
    if pw != getpass.getpass("再输入一次确认: "):
        raise SystemExit("❌ 两次输入不一致")
    return pw


_LOWER_HEX_ESCAPE = re.compile(r"%([0-9A-F]{2})")


def _variants(secret: str) -> set[str]:
    """口令可能出现在异常文本里的几种形态。

    除原文外还有百分号编码后的样子；`%3A`（大写十六进制）与 `%3a`（小写）不同库各用
    一种，两种都要认。这里只把 `%XY` 里的大写十六进制降成小写——`quote` 已经把口令中的
    `%` 编码成 `%25`，所以匹配到的 `%XY` 一定是本函数生成的转义，不会误伤别的内容。
    """
    encoded = quote(secret, safe="")
    return {secret, encoded, _LOWER_HEX_ESCAPE.sub(lambda m: "%" + m.group(1).lower(), encoded)}


def _scrub(text: str, *secrets: str) -> str:
    """把可能夹在异常文本里的口令擦掉（原文与百分号编码两种形态）。

    这是**防御性**的一层，不是已证实的必需品：在本项目的 SQLAlchemy 版本上，我试过的
    失败路径（URL 解析失败、驱动不存在、端口非法、连接被拒）都不回显口令，SQLAlchemy
    自己的 URL 表示也已把口令显示成 `***`。留着它是因为异常文本来自第三方库、版本会变，
    万一哪天真带上口令，代价就是生产口令进了终端与日志。
    """
    for secret in set(secrets):
        for variant in _variants(secret):
            if variant:
                text = text.replace(variant, "***")
    return text


def _verify_connection(url: str, *secrets: str) -> None:
    """用新凭据真的连一次：既证明 URL 拼对了，也证明你改的正是这个用户。"""
    from sqlalchemy import create_engine, text

    engine = None
    try:
        engine = create_engine(url)
        with engine.connect() as conn:
            who = conn.execute(text("SELECT current_user")).scalar()
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 - 擦掉口令后报给使用者
        raise SystemExit(
            f"❌ 用新凭据连接失败：{_scrub(f'{type(exc).__name__}: {exc}', *secrets)}\n"
            "   .env **未改动**。请先确认库里那个用户的口令已经改成你刚输入的值。"
        ) from None
    finally:
        if engine is not None:
            engine.dispose()
    want = unquote(urlsplit(url).username or "")
    if who != want:
        raise SystemExit(
            f"❌ 连上了，但当用户是 {who!r}，与 URL 里的 {want!r} 不一致——"
            "你可能改的是另一个用户的口令。.env **未改动**。"
        )


def _unlink(path) -> None:
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass


def _stage(directory: Path, mode: int, fill) -> str:
    """把内容写进同目录临时文件；失败时自己清理，绝不留半成品。"""
    fd, tmp = tempfile.mkstemp(dir=str(directory), prefix=".env.tmp.")
    try:
        fill(fd, tmp)
        os.chmod(tmp, mode)
    except BaseException:
        _unlink(tmp)
        raise
    return tmp


def _write_env(env_path: Path, lines: list[str]) -> Path:
    """原子替换并留备份：两者都先落临时文件再 rename，失败不留半成品。"""
    try:
        mode = stat.S_IMODE(env_path.stat().st_mode)
    except OSError as exc:
        raise SystemExit(f"❌ 读不到 {env_path} 的状态：{exc.strerror or exc}") from None

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = env_path.with_name(f"{env_path.name}.bak.{stamp}")
    seq = 1
    while backup.exists():  # 同一秒内跑两次不许互相覆盖：后面那次加序号
        seq += 1
        backup = env_path.with_name(f"{env_path.name}.bak.{stamp}.{seq}")

    def _copy(fd, tmp):
        os.close(fd)
        shutil.copyfile(env_path, tmp)

    def _write(fd, tmp):
        with os.fdopen(fd, "w") as f:
            f.writelines(lines)

    made_backup = False
    staged = None
    try:
        staged = _stage(env_path.parent, mode, _copy)
        os.replace(staged, backup)
        staged = None
        made_backup = True

        staged = _stage(env_path.parent, mode, _write)
        os.replace(staged, env_path)
        staged = None
    except OSError as exc:
        raise SystemExit(
            f"❌ 写 {env_path} 失败：{exc.strerror or exc}\n"
            "   .env 原样未动；"
            + (f"备份 {backup.name} 已留在原处。" if made_backup else "备份也没生成。")
        ) from None
    finally:
        # rename 失败时临时文件已经建好、没人接手，必须自己收掉
        if staged is not None:
            _unlink(staged)
    return backup


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="把新的数据库口令同步进 .env（只做 .env，不改库内口令）")
    ap.add_argument("--env", default=str(DEFAULT_ENV), help=".env 路径（默认仓库根目录）")
    ap.add_argument("--dry-run", action="store_true", help="只展示将要写入什么，不落盘")
    ap.add_argument("--no-verify", action="store_true", help="跳过用新凭据实连验证")
    args = ap.parse_args(argv)

    env_path = Path(args.env)
    if not env_path.exists():
        raise SystemExit(f"❌ 找不到 {env_path}")

    # newline="" —— 不做通用换行转换，否则 \r\n 在读取时就被规范化成 \n，
    # 「保留该行原有行尾」的逻辑会形同虚设。
    content = env_path.read_text(encoding="utf-8", newline="")
    if content.startswith("﻿"):
        raise SystemExit(
            "❌ 这个 .env 带 UTF-8 BOM。带不带 BOM 会让不同版本的 python-dotenv 对「哪一行"
            "生效」给出不同答案，脚本不猜。\n"
            "   请先用编辑器另存为「UTF-8 无 BOM」，再跑本脚本（未改动任何文件）。"
        )

    lines = _split_lines(content)
    bindings = _key_bindings(content)
    if not bindings:
        raise SystemExit(f"❌ {env_path} 里找不到绑定 {KEY} 的行，无法同步。")
    # python-dotenv 是「后者胜」：应用读到的是**最后一个**绑定，所以必须改它。
    idx, end_line, old_url = bindings[-1]
    if idx != end_line:
        raise SystemExit(
            f"❌ {env_path} 第 {idx + 1} 行的 {KEY} 值跨了多行（多半是引号没闭合），"
            "脚本无法确定该改哪一行。\n   请先手工修好这一行（未改动任何文件）。"
        )
    if len(bindings) > 1:
        earlier = "、".join(str(k + 1) for k, _, _ in bindings[:-1])
        print(f"⚠️  {env_path} 里有 {len(bindings)} 行绑定 {KEY}（第 {earlier}、{idx + 1} 行）。")
        print(f"    dotenv 取最后一行，本脚本改的就是第 {idx + 1} 行；"
              f"第 {earlier} 行仍是旧口令，建议你顺手删掉。")
    if "=" not in lines[idx] or old_url is None:
        raise SystemExit(
            f"❌ {env_path} 第 {idx + 1} 行的 {KEY} 没有 `=` 或没有值，脚本不猜。\n"
            "   请先手工补好这一行（未改动任何文件）。"
        )
    lhs, rhs = lines[idx].split("=", 1)
    ending = rhs[len(rhs.rstrip("\r\n")) :]  # 保留该行原本的行尾（LF/CRLF/无）
    quote_char = _quote_style(rhs)

    new_password = _prompt_password()
    new_url = _compose(new_password, old_url)
    _assert_env_safe(new_url, quote_char)

    new_line = f"{lhs}={quote_char}{new_url}{quote_char}{ending}"
    candidate_lines = list(lines)
    candidate_lines[idx] = new_line
    candidate = "".join(candidate_lines)
    _assert_effective(candidate, new_url, idx)

    parts = urlsplit(new_url)
    print(f"  用户：{unquote(parts.username or '')}")
    print(f"  主机：{parts.hostname}   库：{parts.path.lstrip('/')}")
    print(f"  将写入：{KEY}={_mask(new_url, _password_of(old_url))}")

    if args.dry_run:
        print("（--dry-run：未改动任何文件）")
        return 0

    if not args.no_verify:
        _verify_connection(new_url, new_password, _password_of(old_url))
        print("  ✅ 新凭据实连成功")

    backup = _write_env(env_path, candidate_lines)
    print(f"✅ 已写入 {env_path}（备份：{backup.name}）。权限保持不变。")
    print("下一步：sudo systemctl restart ezmanbo-backend")
    return 0


if __name__ == "__main__":
    sys.exit(main())
