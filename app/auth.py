import os
import bcrypt as _bcrypt
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from .database import get_db

def _load_secret_key() -> str:
    """读取 JWT 签名密钥，缺失或过短时启动即失败。

    绝不回落到硬编码默认值：本仓库公开，默认值等同没有密钥，
    任何人都能签出管理员令牌。
    """
    key = (os.getenv("JWT_SECRET_KEY") or os.getenv("SECRET_KEY") or "").strip()
    if len(key) < 32:
        raise RuntimeError(
            "缺少 JWT 签名密钥：请在 .env 中设置 JWT_SECRET_KEY（或 SECRET_KEY），"
            "长度不少于 32 字符。服务拒绝以可预测的密钥启动。"
        )
    return key


SECRET_KEY = _load_secret_key()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7
REFRESH_TOKEN_EXPIRE_DAYS = 30  # P2-2: long-lived refresh token
GUEST_TOKEN_EXPIRE_MINUTES = int(os.getenv("GUEST_TOKEN_EXPIRE_MINUTES", "120"))  # 游客令牌短时效

security = HTTPBearer(auto_error=False)


def verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")


def create_access_token(data: dict, expires_minutes: Optional[int] = None) -> str:
    payload = data.copy()
    lifetime = timedelta(minutes=expires_minutes) if expires_minutes else timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    payload["exp"] = datetime.utcnow() + lifetime
    payload["type"] = "access"
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """P2-2: 30-day refresh token with sliding expiry on use."""
    payload = {k: v for k, v in data.items() if k != "exp"}
    payload["exp"] = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload["type"] = "refresh"
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_refresh_token(token: str) -> dict:
    """Decode and validate a refresh token. Raises HTTPException on failure."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="不是有效的刷新令牌")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="刷新令牌无效或已过期，请重新登录")


def _decode(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="无效或已过期的令牌，请重新登录")
    # 30 天的刷新令牌不得当作访问令牌使用，否则短时效访问令牌形同虚设
    if payload.get("type") == "refresh":
        raise HTTPException(status_code=401, detail="刷新令牌不能用于访问接口")
    return payload


class GuestUser:
    """游客伪用户对象，不持久化到数据库。

    session_scope 取自令牌的 sub（每次游客登录都不同），使不同游客的会话态
    互相隔离；否则所有游客共用 id=0，会彼此看到对方的选型报告。
    """

    id = 0
    is_admin = False
    is_active = True
    is_guest = True

    def __init__(self, scope: str = "guest") -> None:
        self.session_scope = scope
        self.username = "游客"
        self.email = ""


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
):
    if not credentials:
        raise HTTPException(status_code=401, detail="未提供认证令牌，请先登录")
    payload = _decode(credentials.credentials)

    if payload.get("is_guest"):
        return GuestUser(payload.get("sub") or "guest")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="令牌格式错误")
    from .models_db import User
    user = db.query(User).filter(User.id == int(user_id), User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在或已被禁用")
    return user


def get_current_admin(user=Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
):
    if not credentials:
        return None
    try:
        payload = _decode(credentials.credentials)
        if payload.get("is_guest"):
            return GuestUser(payload.get("sub") or "guest")
        user_id = payload.get("sub")
        if not user_id:
            return None
        from .models_db import User
        return db.query(User).filter(User.id == int(user_id), User.is_active == True).first()
    except Exception:
        return None

