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
"""

import argparse
import getpass
import os
import shutil
import stat
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit, urlunsplit

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ENV = REPO_ROOT / ".env"
KEY = "DATABASE_URL"
MIN_PASSWORD_LEN = 8


def _split_value(raw: str) -> tuple[str, str]:
    """把 `KEY=` 右侧拆成 (值, 引号)。只认整体包裹的引号，保持原文件的风格。"""
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        return raw[1:-1], raw[0]
    return raw, ""


def _find_key_line(lines: list[str], key: str = KEY) -> int:
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and stripped.split("=", 1)[0].strip() == key:
            return i
    raise SystemExit(f"❌ .env 里找不到 {key}= 这一行，无法同步。")


def _compose(new_password: str, old_url: str) -> str:
    """用新口令重组成连接串，其中口令做百分号编码。其余部分逐字保留。"""
    parts = urlsplit(old_url)
    if parts.password is None:
        raise SystemExit("❌ 当前 DATABASE_URL 里没有口令字段，无法同步（是否用了 IAM 认证？）。")
    user = unquote(parts.username or "")
    netloc = f"{quote(user, safe='')}:{quote(new_password, safe='')}@{parts.hostname or ''}"
    if parts.port:
        netloc += f":{parts.port}"
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
    masked = urlunsplit(
        (parts.scheme, f"{parts.username}:***@{parts.hostname}", parts.path, parts.query, parts.fragment)
    )
    return masked


def _prompt_password() -> str:
    pw = getpass.getpass("数据库新口令（输入时不回显）: ")
    if len(pw) < MIN_PASSWORD_LEN:
        raise SystemExit(f"❌ 口令至少 {MIN_PASSWORD_LEN} 位")
    if pw != getpass.getpass("再输入一次确认: "):
        raise SystemExit("❌ 两次输入不一致")
    return pw


def _verify_connection(url: str) -> None:
    """用新凭据真的连一次：既证明 URL 拼对了，也证明你改的正是这个用户。"""
    from sqlalchemy import create_engine, text

    engine = create_engine(url)
    try:
        with engine.connect() as conn:
            who = conn.execute(text("SELECT current_user")).scalar()
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 - 原样报给使用者
        raise SystemExit(
            f"❌ 用新凭据连接失败：{type(exc).__name__}: {exc}\n"
            "   .env **未改动**。请先确认库里那个用户的口令已经改成你刚输入的值。"
        ) from exc
    finally:
        engine.dispose()
    want = unquote(urlsplit(url).username or "")
    if who != want:
        raise SystemExit(
            f"❌ 连上了，但当用户是 {who!r}，与 URL 里的 {want!r} 不一致——"
            "你可能改的是另一个用户的口令。.env **未改动**。"
        )


def _write_env(env_path: Path, lines: list[str]) -> Path:
    """原子替换并留备份，文件权限保持不变。"""
    mode = stat.S_IMODE(env_path.stat().st_mode)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = env_path.with_name(f"{env_path.name}.bak.{stamp}")
    shutil.copy2(env_path, backup)
    os.chmod(backup, mode)

    fd, tmp = tempfile.mkstemp(dir=str(env_path.parent), prefix=".env.tmp.")
    try:
        with os.fdopen(fd, "w") as f:
            f.writelines(lines)
        os.chmod(tmp, mode)
        os.replace(tmp, env_path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
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
    idx = _find_key_line(lines)
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
        _verify_connection(new_url)
        print("  ✅ 新凭据实连成功")

    lines[idx] = f"{lhs}={quote_char}{new_url}{quote_char}{ending}"
    backup = _write_env(env_path, lines)
    print(f"✅ 已写入 {env_path}（备份：{backup.name}）。权限保持不变。")
    print("下一步：sudo systemctl restart ezmanbo-backend")
    return 0


if __name__ == "__main__":
    sys.exit(main())
