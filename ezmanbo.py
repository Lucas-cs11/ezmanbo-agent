#!/usr/bin/env python3
"""
eZmanbo CLI — 智能电子元器件选型助手

用法:
  ezmanbo                启动 CLI 终端对话模式（默认）
  ezmanbo chat           进入终端 REPL 交互
  ezmanbo chat "需求"    单次问询
  ezmanbo open           启动服务 + 打开浏览器
  ezmanbo start          仅启动后端与前端服务
  ezmanbo stop           停止所有服务
  ezmanbo status         查看服务运行状态
  ezmanbo backend        仅启动后端 API (端口 8000)
  ezmanbo frontend       仅启动前端 (端口 3000)
"""

import sys
import os
import subprocess
import time
import signal
import socket
import webbrowser
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
PID_DIR = PROJECT_ROOT / ".pids"
PID_DIR.mkdir(exist_ok=True)

BACKEND_PORT = 8000
FRONTEND_PORT = 3000


def _is_port_in_use(port: int) -> bool:
    """检查端口是否已被占用。"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def _read_pid(name: str) -> int | None:
    """读取已保存的 PID。"""
    pid_file = PID_DIR / f"{name}.pid"
    if pid_file.exists():
        try:
            return int(pid_file.read_text().strip())
        except ValueError:
            pass
    return None


def _write_pid(name: str, pid: int):
    """保存 PID。"""
    (PID_DIR / f"{name}.pid").write_text(str(pid))


def _remove_pid(name: str):
    """删除 PID 文件。"""
    (PID_DIR / f"{name}.pid").unlink(missing_ok=True)


def _kill_process(name: str):
    """按 PID 文件终止进程。"""
    pid = _read_pid(name)
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(0.5)
            # 强制终止
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        except ProcessLookupError:
            pass
    _remove_pid(name)


def cmd_start():
    """启动后端 + 前端服务。"""
    # ── 欢迎屏（对齐 Claude Code LogoV2） ──
    try:
        from ezmanbo_cli.header import print_condensed_header
        from rich.console import Console
        print_condensed_header(Console(), cwd=str(PROJECT_ROOT),
                               model_name="DeepSeek-V3")
        from ezmanbo_cli.figures import BLACK_CIRCLE, FLAG_ICON, DIAMOND_FILLED
        _use_ui = True
    except ImportError:
        print("eZmanbo — 智能元器件选型助手")
        print("=" * 42)
        _use_ui = False

    # 后端
    if _use_ui:
        status_icon = BLACK_CIRCLE if _is_port_in_use(BACKEND_PORT) else DIAMOND_FILLED

    if _is_port_in_use(BACKEND_PORT):
        if _use_ui:
            print(f"  {BLACK_CIRCLE} Backend : already running on :{BACKEND_PORT}")
        else:
            print(f"  Backend  : already running on :{BACKEND_PORT}")
    else:
        proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app",
             "--host", "0.0.0.0", "--port", str(BACKEND_PORT)],
            cwd=str(PROJECT_ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        _write_pid("backend", proc.pid)
        if _use_ui:
            print(f"  {DIAMOND_FILLED} Backend : started on http://localhost:{BACKEND_PORT} (PID {proc.pid})")
        else:
            print(f"  Backend  : started on http://localhost:{BACKEND_PORT} (PID {proc.pid})")

    # 等待后端就绪
    for _ in range(10):
        if _is_port_in_use(BACKEND_PORT):
            break
        time.sleep(0.5)

    # 前端
    if _is_port_in_use(FRONTEND_PORT):
        if _use_ui:
            print(f"  {BLACK_CIRCLE} Frontend : already running on :{FRONTEND_PORT}")
        else:
            print(f"  Frontend : already running on :{FRONTEND_PORT}")
    else:
        frontend_dir = PROJECT_ROOT / "frontend" / "web"
        proc = subprocess.Popen(
            ["npx", "next", "dev", "-p", str(FRONTEND_PORT)],
            cwd=str(frontend_dir),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        _write_pid("frontend", proc.pid)
        if _use_ui:
            print(f"  {DIAMOND_FILLED} Frontend : starting on http://localhost:{FRONTEND_PORT} (PID {proc.pid})")
        else:
            print(f"  Frontend : starting on http://localhost:{FRONTEND_PORT} (PID {proc.pid})")

    print()
    if _use_ui:
        from ezmanbo_cli.figures import HEAVY_HORIZONTAL
        print(f"  Open: http://localhost:{FRONTEND_PORT}")
        print(f"  API:  http://localhost:{BACKEND_PORT}/docs")
        print(f"  {HEAVY_HORIZONTAL * 40}")
    else:
        print(f"  Open: http://localhost:{FRONTEND_PORT}")
        print(f"  API:  http://localhost:{BACKEND_PORT}/docs")
        print("=" * 42)


def cmd_stop():
    """停止所有服务。"""
    print("Stopping eZmanbo services...")
    for name in ("backend", "frontend"):
        _kill_process(name)
    # 额外清理可能残留的端口占用
    for port in (BACKEND_PORT, FRONTEND_PORT):
        if _is_port_in_use(port):
            os.system(f"lsof -ti:{port} | xargs kill -9 2>/dev/null")
    print("All services stopped.")


def cmd_status():
    """查看服务状态。"""
    be_ok = _is_port_in_use(BACKEND_PORT)
    fe_ok = _is_port_in_use(FRONTEND_PORT)
    print(f"  Backend  (:{BACKEND_PORT}): {'RUNNING' if be_ok else 'STOPPED'}")
    print(f"  Frontend (:{FRONTEND_PORT}): {'RUNNING' if fe_ok else 'STOPPED'}")
    if be_ok or fe_ok:
        print(f"  Open: http://localhost:{FRONTEND_PORT}")


def cmd_open():
    """启动（如需要）并打开浏览器。"""
    if not _is_port_in_use(BACKEND_PORT) or not _is_port_in_use(FRONTEND_PORT):
        cmd_start()
        print("\nWaiting for frontend to be ready...")
        for _ in range(20):
            if _is_port_in_use(FRONTEND_PORT):
                break
            time.sleep(1)
    webbrowser.open(f"http://localhost:{FRONTEND_PORT}")


def cmd_backend():
    """仅启动后端。"""
    if _is_port_in_use(BACKEND_PORT):
        print(f"Backend already running on :{BACKEND_PORT}")
        return
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app",
         "--host", "0.0.0.0", "--port", str(BACKEND_PORT)],
        cwd=str(PROJECT_ROOT),
    )
    _write_pid("backend", proc.pid)
    print(f"Backend started: http://localhost:{BACKEND_PORT}")


def cmd_frontend():
    """仅启动前端。"""
    if _is_port_in_use(FRONTEND_PORT):
        print(f"Frontend already running on :{FRONTEND_PORT}")
        return
    frontend_dir = PROJECT_ROOT / "frontend" / "web"
    proc = subprocess.Popen(
        ["npx", "next", "dev", "-p", str(FRONTEND_PORT)],
        cwd=str(frontend_dir),
    )
    _write_pid("frontend", proc.pid)
    print(f"Frontend starting: http://localhost:{FRONTEND_PORT}")


# ═══════════════════════════════════════════════════════════════
# 入口
# ═══════════════════════════════════════════════════════════════

COMMANDS = {
    "start":    cmd_start,
    "stop":     cmd_stop,
    "status":   cmd_status,
    "backend":  cmd_backend,
    "frontend": cmd_frontend,
}

def cmd_chat():
    """启动 CLI 对话 REPL。"""
    if not _is_port_in_use(BACKEND_PORT):
        cmd_start()
        for _ in range(15):
            if _is_port_in_use(BACKEND_PORT): break
            time.sleep(0.5)
    from ezmanbo_cli_chat import repl
    repl()


def main():
    os.chdir(PROJECT_ROOT)

    cmd = sys.argv[1] if len(sys.argv) > 1 else "chat"
    rest = sys.argv[2:]

    if cmd in COMMANDS:
        COMMANDS[cmd]()
    elif cmd == "chat":
        if rest:
            if not _is_port_in_use(BACKEND_PORT):
                cmd_start()
                for _ in range(15):
                    if _is_port_in_use(BACKEND_PORT): break
                    time.sleep(0.5)
            from ezmanbo_cli_chat import single_query
            single_query(" ".join(rest))
        else:
            cmd_chat()
    elif cmd == "open":
        cmd_open()
    else:
        # 未知命令 — 当做单次查询
        if not _is_port_in_use(BACKEND_PORT):
            print("Starting backend...")
            cmd_start()
            for _ in range(15):
                if _is_port_in_use(BACKEND_PORT):
                    break
                time.sleep(0.5)
        from ezmanbo_cli_chat import single_query
        single_query(" ".join(sys.argv[1:]))


if __name__ == "__main__":
    main()
