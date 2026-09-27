#!/usr/bin/env python3
"""manage_users.py — 账号后台管理（公开注册已关闭，账号一律由后台创建）

用法（在仓库根目录执行）：
  venv/bin/python scripts/manage_users.py list
  venv/bin/python scripts/manage_users.py create-admin  <用户名>     # 建管理员
  venv/bin/python scripts/manage_users.py create-user   <用户名>     # 建普通用户
  venv/bin/python scripts/manage_users.py reset-password <用户名>
  venv/bin/python scripts/manage_users.py deactivate    <用户名>

密码一律交互式输入，不接受命令行参数：否则会留在 shell 历史和进程列表里。
"""

import getpass
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv  # noqa: E402

# 必须在 import app.* 之前加载：database.py 在导入时即读取 DATABASE_URL
load_dotenv(REPO_ROOT / ".env")

import bcrypt  # noqa: E402

from app.database import SessionLocal, init_db  # noqa: E402
from app.models_db import User  # noqa: E402

MIN_PASSWORD_LEN = 8


def _hash_password(password: str) -> str:
    """就地实现而不复用 app.auth.hash_password。

    app.auth 在导入时就会校验 JWT_SECRET_KEY 并在缺失时抛错；而本脚本正是全新
    部署、密钥还没配好时唯一的建号入口，不能被它挡住。bcrypt 哈希格式一致，
    服务端 auth.verify_password 能正常校验。
    """
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _prompt_password() -> str:
    pw = getpass.getpass("密码（输入时不回显）: ")
    if len(pw) < MIN_PASSWORD_LEN:
        sys.exit(f"密码至少 {MIN_PASSWORD_LEN} 位")
    if pw != getpass.getpass("再输入一次确认: "):
        sys.exit("两次输入不一致")
    return pw


def _validate_username(name: str) -> str:
    name = name.strip()
    if not 2 <= len(name) <= 30:
        sys.exit("用户名长度须在 2–30 字符之间")
    return name


def cmd_list(_args):
    db = SessionLocal()
    try:
        users = db.query(User).order_by(User.id).all()
        if not users:
            print("（暂无账号。用 create-admin 建第一个管理员）")
            return
        print(f"{'ID':<5} {'用户名':<20} {'角色':<8} {'状态':<6} 创建时间")
        for u in users:
            role = "管理员" if u.is_admin else "普通用户"
            status = "启用" if u.is_active else "已禁用"
            created = u.created_at.strftime("%Y-%m-%d %H:%M") if u.created_at else "-"
            print(f"{u.id:<5} {u.username:<20} {role:<8} {status:<6} {created}")
    finally:
        db.close()


def _create(username: str, is_admin: bool):
    username = _validate_username(username)
    db = SessionLocal()
    try:
        # 先确认用户名可用再要密码，否则重名时要白输两遍
        if db.query(User).filter(User.username == username).first():
            sys.exit(f"用户名已存在：{username}")
        password = _prompt_password()
        user = User(
            username=username,
            email="",
            hashed_password=_hash_password(password),
            is_admin=is_admin,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        role = "管理员" if is_admin else "普通用户"
        print(f"已创建{role}：{user.username}（id={user.id}）")
    finally:
        db.close()


def cmd_create_admin(args):
    _create(_need(args), True)


def cmd_create_user(args):
    _create(_need(args), False)


def cmd_reset_password(args):
    username = _need(args)
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            sys.exit(f"用户不存在：{username}")
        user.hashed_password = _hash_password(_prompt_password())
        db.commit()
        print(f"已重置密码：{user.username}")
    finally:
        db.close()


def cmd_deactivate(args):
    username = _need(args)
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            sys.exit(f"用户不存在：{username}")
        if user.is_active is False:
            print(f"{user.username} 已是禁用状态")
            return
        user.is_active = False
        db.commit()
        print(f"已禁用：{user.username}")
    finally:
        db.close()


def _need(args) -> str:
    if not args:
        sys.exit("缺少用户名参数")
    return args[0]


COMMANDS = {
    "list": cmd_list,
    "create-admin": cmd_create_admin,
    "create-user": cmd_create_user,
    "reset-password": cmd_reset_password,
    "deactivate": cmd_deactivate,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        sys.exit(__doc__)
    init_db()
    COMMANDS[sys.argv[1]](sys.argv[2:])


if __name__ == "__main__":
    main()
