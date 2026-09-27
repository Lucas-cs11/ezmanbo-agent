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
——并就把前面几行的行号报警给你。「哪一行算绑定了这个键」一律由 dotenv 自己的解析器
判定，不另立规则。
"""

import argparse
import getpass
import io
import os
import shutil
import stat
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit, urlunsplit

from dotenv.parser import parse_stream

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ENV = REPO_ROOT / ".env"
KEY = "DATABASE_URL"
MIN_PASSWORD_LEN = 8


def _split_value(raw: str) -> tuple[str, str]:
    """把 `KEY=` 右侧拆成 (值, 引号)。只认整体包裹的引号，保持原文件的风格。"""
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        return raw[1:-1], raw[0]
    return raw, ""


def _key_lines(lines: list[str], key: str = KEY) -> list[int]:
    """所有**真正绑定**该 key 的行号（跳过注释行），按出现顺序。

    这里刻意用 python-dotenv **自己的解析器**逐行判断，而不是另写一套「`=` 左边等于 key」
    的规则：两者一旦分歧，脚本就会改一行、应用读另一行——曾经的真实缺陷正是
    `export DATABASE_URL=...`（dotenv 认，自制规则不认）。
    """
    found = []
    for i, line in enumerate(lines):
        for binding in parse_stream(io.StringIO(line)):
            if binding.error is False and binding.key == key:
                found.append(i)
                break
    return found


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


def _mask(url: str) -> str:
    parts = urlsplit(url)
    if parts.password is None:
        return url
    netloc = f"{parts.username}:***@{parts.hostname or ''}"
    port = _port_of(parts)
    if port:
        netloc += f":{port}"
    return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))


def _prompt_password() -> str:
    pw = getpass.getpass("数据库新口令（输入时不回显）: ")
    if len(pw) < MIN_PASSWORD_LEN:
        raise SystemExit(f"❌ 口令至少 {MIN_PASSWORD_LEN} 位")
    if pw != getpass.getpass("再输入一次确认: "):
        raise SystemExit("❌ 两次输入不一致")
    return pw


def _scrub(text: str, secret: str) -> str:
    """把可能夹在异常文本里的口令擦掉（原文与百分号编码两种形态）。

    这是**防御性**的一层，不是已证实的必需品：在本项目的 SQLAlchemy 版本上，我试过的
    失败路径（URL 解析失败、驱动不存在、端口非法、连接被拒）都不回显口令，SQLAlchemy
    自己的 URL 表示也已把口令显示成 `***`。留着它是因为异常文本来自第三方库、版本会变，
    万一哪天真带上口令，代价就是生产口令进了终端与日志。
    """
    for variant in {secret, quote(secret, safe="")}:
        if variant:
            text = text.replace(variant, "***")
    return text


def _verify_connection(url: str, secret: str) -> None:
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
            f"❌ 用新凭据连接失败：{_scrub(f'{type(exc).__name__}: {exc}', secret)}\n"
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
    # 那条「保留该行原有行尾」的逻辑会形同虚设。
    with env_path.open(encoding="utf-8", newline="") as f:
        lines = f.readlines()
    found = _key_lines(lines)
    if not found:
        raise SystemExit(f"❌ {env_path} 里找不到 {KEY}= 这一行，无法同步。")
    # python-dotenv 是「后者胜」：应用读到的是**最后一行**，所以必须改它，
    # 否则实连验证会证明「库里确实有这个口令」，而生产用的仍是旧口令。
    idx = found[-1]
    if len(found) > 1:
        earlier = "、".join(str(i + 1) for i in found[:-1])
        print(f"⚠️  {env_path} 里有 {len(found)} 行 {KEY}=（第 {earlier}、{idx + 1} 行）。")
        print(f"    dotenv 取最后一行，本脚本改的就是第 {idx + 1} 行；"
              f"第 {earlier} 行仍是旧口令，建议你顺手删掉。")
    lhs, rhs = lines[idx].split("=", 1)
    ending = rhs[len(rhs.rstrip("\r\n")) :]  # 保留该行原本的行尾（LF/CRLF/无）
    old_value, quote_char = _split_value(rhs.strip())

    new_password = _prompt_password()
    new_url = _compose(new_password, old_value)
    _assert_env_safe(new_url, quote_char)

    parts = urlsplit(new_url)
    print(f"  用户：{unquote(parts.username or '')}")
    print(f"  主机：{parts.hostname}   库：{parts.path.lstrip('/')}")
    print(f"  将写入：{KEY}={_mask(new_url)}")

    if args.dry_run:
        print("（--dry-run：未改动任何文件）")
        return 0

    if not args.no_verify:
        _verify_connection(new_url, new_password)
        print("  ✅ 新凭据实连成功")

    lines[idx] = f"{lhs}={quote_char}{new_url}{quote_char}{ending}"
    backup = _write_env(env_path, lines)
    print(f"✅ 已写入 {env_path}（备份：{backup.name}）。权限保持不变。")
    print("下一步：sudo systemctl restart ezmanbo-backend")
    return 0


if __name__ == "__main__":
    sys.exit(main())
