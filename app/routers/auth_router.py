import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from ..database import get_db
from ..models_db import User
from ..auth import (
    DUMMY_PASSWORD_HASH, verify_password, parse_user_id,
    create_access_token, create_refresh_token, decode_refresh_token,
    get_current_user, GUEST_TOKEN_EXPIRE_MINUTES,
)
from ..rate_limit import rate_limit

router = APIRouter(prefix="/auth", tags=["auth"])

# 这些入口无成本就能换来一个可用令牌，是配额被白嫖的主要路径，故按 IP 限速
_guest_limit = rate_limit("guest", max_requests=10, window_seconds=600)
_login_limit = rate_limit("login", max_requests=20, window_seconds=600, message="登录尝试过于频繁，请 10 分钟后再试")
_register_limit = rate_limit("register", max_requests=5, window_seconds=3600)
# 此前 refresh 是 auth 路由里唯一没有限流的入口，且无需认证
_refresh_limit = rate_limit("refresh", max_requests=60, window_seconds=600)


class RegisterBody(BaseModel):
    username: str
    password: str


class LoginBody(BaseModel):
    username: str
    password: str


class RefreshBody(BaseModel):
    # 必须声明为 str：此前用裸 dict 接收，refresh_token 传成 list/dict 时会一路走到
    # jose 的 jwt.decode 对非字符串调 .rsplit，抛 AttributeError 变成 500。
    # 而本路由无需认证，等于给了一个免费的报错放大器。类型交给 Pydantic 挡在入口。
    refresh_token: Optional[str] = None


def _user_out(u) -> dict:
    return {
        "id": u.id,
        "username": u.username,
        "email": getattr(u, "email", "") or "",
        "is_admin": u.is_admin,
        "is_guest": getattr(u, "is_guest", False),
        "dual_model_enabled": bool(getattr(u, "dual_model_enabled", False)),
    }


@router.post("/register")
def register(body: RegisterBody, _rl=Depends(_register_limit)):
    """公开注册已永久关闭：账号一律由管理员在后台创建。

    保留该路由而非删除，是为了让老前端的调用拿到明确原因，而不是一个费解的 404。
    """
    raise HTTPException(403, "注册通道已关闭，账号由管理员在后台创建，请联系管理员获取访问权限")


@router.post("/login")
def login(body: LoginBody, db: Session = Depends(get_db), _rl=Depends(_login_limit)):
    user = db.query(User).filter(User.username == body.username).first()
    if user:
        ok = verify_password(body.password, user.hashed_password)
    else:
        # 用户名不存在时也跑一次等价开销的校验：否则「存在的用户名慢、不存在的快」
        # 这个响应时间差本身就是账号枚举信道。
        verify_password(body.password, DUMMY_PASSWORD_HASH)
        ok = False
    if not ok:
        raise HTTPException(401, "用户名或密码错误")
    if not user.is_active:
        raise HTTPException(403, "账号已被禁用，请联系管理员")

    token = create_access_token({"sub": str(user.id), "username": user.username, "is_admin": user.is_admin})
    refresh = create_refresh_token({"sub": str(user.id), "username": user.username, "is_admin": user.is_admin})
    return {"token": token, "refresh_token": refresh, "user": _user_out(user)}


@router.post("/refresh")
def refresh_token(body: RefreshBody, db: Session = Depends(get_db), _rl=Depends(_refresh_limit)):
    """P2-2: Exchange a valid refresh token for a new access + refresh token pair (sliding expiry)."""
    rt = (body.refresh_token or "").strip()
    if not rt:
        raise HTTPException(400, "缺少 refresh_token")
    payload = decode_refresh_token(rt)
    if payload.get("is_guest"):
        # 游客令牌短时效且不持久化，本就不该续期
        raise HTTPException(401, "游客会话不支持续期，请重新进入")
    # 非数字或越界的 sub（历史游客令牌、被构造的巨型整数等）一律 401，
    # 不让 int()/数据库类型转换抛成 500
    uid = parse_user_id(payload.get("sub"))
    if uid is None:
        raise HTTPException(401, "刷新令牌无效")
    from ..models_db import User as _User
    user = db.query(_User).filter(_User.id == uid, _User.is_active == True).first()
    if not user:
        raise HTTPException(401, "用户不存在或已被禁用")
    token = create_access_token({"sub": str(user.id), "username": user.username, "is_admin": user.is_admin})
    new_refresh = create_refresh_token({"sub": str(user.id), "username": user.username, "is_admin": user.is_admin})
    return {"token": token, "refresh_token": new_refresh}


@router.post("/guest")
def guest_login(_rl=Depends(_guest_limit)):
    """游客进入：无需账号，任何人可进。对话不会保存到数据库。

    不依赖系统是否已初始化管理员，否则全新部署时谁都进不来。
    签发短时效令牌（默认 2 小时），避免被脚本批量铸造后长期白嫖配额。
    """
    # sub 每次唯一：游客之间的会话态据此隔离
    guest_scope = f"guest-{uuid.uuid4().hex[:12]}"
    token = create_access_token(
        {"sub": guest_scope, "is_guest": True, "username": "游客"},
        expires_minutes=GUEST_TOKEN_EXPIRE_MINUTES,
    )
    return {"token": token, "user": {"id": 0, "username": "游客", "email": "", "is_admin": False, "is_guest": True}}


@router.get("/me")
def me(current_user=Depends(get_current_user)):
    return _user_out(current_user)


@router.post("/me/dual-model")
def toggle_dual_model(
    body: dict,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """用户开关双模型验证。需要管理员先配置验证模型。"""
    if getattr(current_user, "is_guest", False):
        raise HTTPException(403, "游客不支持此功能")
    enabled = bool((body or {}).get("enabled", False))
    if enabled:
        from ..models_db import AdminConfig
        cfg = db.query(AdminConfig).first()
        if not cfg or not (cfg.verifier_model or "").strip():
            raise HTTPException(403, "管理员未授权此功能")
    user = db.query(User).filter(User.id == current_user.id).first()
    if not user:
        raise HTTPException(404, "用户不存在")
    user.dual_model_enabled = enabled
    db.commit()
    return {"dual_model_enabled": user.dual_model_enabled}
