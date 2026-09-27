"""rate_limit.py — 轻量 IP 限流（进程内滑动窗口）

用途：给登录、游客签发这类「无成本伪造身份」的入口加一道速度限制，
避免脚本无限刷令牌去白嫖 LLM 与 eZ-PLM 配额。

局限（重要）：状态在进程内存里，多 worker / 多实例时每个进程各算一份，
届时需换成 Redis 实现（可参考 session_store.py 的降级写法）。

客户端 IP 取 nginx 写入的 X-Real-IP（值为 $remote_addr，客户端无法伪造），
而非 X-Forwarded-For（nginx 用 $proxy_add_x_forwarded_for 会保留客户端自带值，可伪造）。
后端应只监听 127.0.0.1，否则直连 8000 端口可绕过本限流。
"""
from __future__ import annotations

import threading
import time
from collections import OrderedDict, deque
from typing import Callable, Deque, Dict

from fastapi import HTTPException, Request

_MAX_KEYS = 10_000  # 防止被大量不同 IP 撑爆内存


class IpRateLimiter:
    def __init__(self, max_requests: int, window_seconds: float) -> None:
        self._max = max_requests
        self._window = window_seconds
        # 必须用 OrderedDict：淘汰依赖插入顺序，热点 key 需要 move_to_end 保位
        self._hits: "OrderedDict[str, Deque[float]]" = OrderedDict()
        self._lock = threading.Lock()

    def _evict_if_needed(self) -> None:
        if len(self._hits) <= _MAX_KEYS:
            return
        # 保序字典：丢掉最早出现的一批 key
        for _ in range(len(self._hits) - _MAX_KEYS + 100):
            try:
                self._hits.popitem(last=False)
            except KeyError:
                break

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        cutoff = now - self._window
        with self._lock:
            bucket = self._hits.get(key)
            if bucket is None:
                self._evict_if_needed()
                bucket = self._hits[key] = deque()
            else:
                # 保证 key 的插入顺序反映最近活跃，避免热点 key 被优先淘汰
                self._hits.move_to_end(key)
            while bucket and bucket[0] < cutoff:
                bucket.popleft()
            if len(bucket) >= self._max:
                return False
            bucket.append(now)
            return True


def client_ip(request: Request) -> str:
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else "unknown"


def rate_limit(name: str, max_requests: int, window_seconds: float, message: str = "请求过于频繁，请稍后再试") -> Callable:
    """构造一个 FastAPI 依赖，按客户端 IP 限制 name 这个动作的调用频率。"""
    limiter = IpRateLimiter(max_requests, window_seconds)

    async def _dependency(request: Request) -> None:
        if not limiter.allow(client_ip(request)):
            raise HTTPException(status_code=429, detail=message)

    _dependency.__name__ = f"rate_limit_{name}"
    return _dependency
