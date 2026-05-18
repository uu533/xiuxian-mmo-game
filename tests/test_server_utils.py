"""
测试服务器管理工具：自动启动 / 关闭 uvicorn，测试脚本入口处调用 ensure_test_server()
同一台机器上只启动一个实例，多个测试共享。
"""
import atexit
import os
import subprocess
import sys
import threading
import time
import urllib.request
import urllib.error

PYTHON = sys.executable
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_URL = "http://127.0.0.1:8000"

# 全局单例：只允许一个 uvicorn 进程
_server_proc = None
_server_lock = threading.Lock()
_server_started = False

LOG_DIR = os.path.join(ROOT, "debug_logs")
UV_OUT = os.path.join(LOG_DIR, "test_uvicorn_stdout.log")
UV_ERR = os.path.join(LOG_DIR, "test_uvicorn_stderr.log")
os.makedirs(LOG_DIR, exist_ok=True)


def _log(msg):
    """写日志到文件，测试脚本自己会用 file 输出所以这里不用 print"""
    with open(os.path.join(LOG_DIR, "test_server_utils.log"), "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")


def stop_test_server(proc):
    """强制终止 uvicorn 进程。"""
    if proc is None:
        return
    try:
        proc.terminate()
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
    except Exception:
        pass


def _kill_port_8000():
    """杀死占用 8000 端口的进程（清理残留）。"""
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             "(netstat -ano | findstr ':8000 LISTENING').Split()[(-1)]"],
            capture_output=True, text=True, timeout=5
        )
        pid = result.stdout.strip()
        if pid and pid.isdigit():
            _log(f"Killing port 8000 process PID={pid}")
            subprocess.run(["taskkill", "/F", "/PID", pid], timeout=5, capture_output=True)
    except Exception:
        pass


def _is_correct_project_server():
    """验证 8000 端口上跑的是本项目后端，而非其他服务。"""
    try:
        # 优先用 /docs（FastAPI Swagger）验证
        for path in ["/docs", "/openapi.json"]:
            try:
                req = urllib.request.Request(BASE_URL + path, timeout=3)
                resp = urllib.request.urlopen(req, timeout=3)
                body = resp.read().decode("utf-8", errors="ignore")
                if "openapi" in body or "swagger" in body:
                    return True
            except Exception:
                pass
        # 兜底：检查根路径是否为本项目响应
        req = urllib.request.Request(BASE_URL + "/", timeout=3)
        resp = urllib.request.urlopen(req, timeout=3)
        body = resp.read().decode("utf-8", errors="ignore")
        return "xiuxian" in body.lower() or "openapi" in body.lower() or '"character"' in body
    except Exception:
        return False


def start_test_server():
    """
    启动 uvicorn 外部进程，等待健康检查。
    启动成功返回 (proc, is_new)；已有服务可用返回 (None, False)。
    启动失败抛出 RuntimeError。
    """
    global _server_proc, _server_started

    # 1. 检查是否已有本项目服务运行
    for attempt in range(3):
        try:
            if _is_correct_project_server():
                _log(f"Correct project server already running at {BASE_URL}")
                return None, False
        except Exception:
            pass
        time.sleep(0.5)

    # 2. 检查 8000 被非本项目服务占用 → 报错提示
    try:
        urllib.request.urlopen(BASE_URL + "/", timeout=3)
        if not _is_correct_project_server():
            raise RuntimeError(
                f"Port 8000 is occupied by a non-project server.\n"
                f"Please stop the other service first: taskkill /F /PID <pid>\n"
                f"Then re-run the test."
            )
    except urllib.error.URLError:
        pass  # 端口空闲，继续启动
    except RuntimeError:
        raise

    # 2. 清理残留进程
    _log("Cleaning up old processes on port 8000...")
    _kill_port_8000()
    time.sleep(1)

    # 3. 启动 uvicorn
    _log("Starting uvicorn...")

    # 清空旧日志
    for path in [UV_OUT, UV_ERR]:
        try:
            open(path, "w").close()
        except Exception:
            pass

    env = os.environ.copy()
    env["ENABLE_DEV_ROUTES"] = "1"
    env["PYTHONPATH"] = ROOT

    _server_proc = subprocess.Popen(
        [PYTHON, "-m", "uvicorn", "backend.main:app",
         "--host", "127.0.0.1", "--port", "8000"],
        cwd=ROOT,
        stdout=open(UV_OUT, "w", encoding="utf-8"),
        stderr=subprocess.STDOUT,
        env=env,
    )

    _log(f"uvicorn started, PID={_server_proc.pid}")

    # 4. 健康检查（最多 15 秒）
    ready = False
    for i in range(15):
        time.sleep(1)
        if _server_proc.poll() is not None:
            # 进程已退出
            with open(UV_OUT, "r", encoding="utf-8") as f:
                lines = f.readlines()
            last = "".join(lines[-100:])
            _log(f"uvicorn exited early. stdout last 100 lines:\n{last}")
            raise RuntimeError(
                f"uvicorn process exited with code {_server_proc.returncode}.\n"
                f"stdout tail:\n{last}"
            )
        try:
            resp = urllib.request.urlopen(BASE_URL + "/", timeout=3)
            _log(f"Server ready after {i+1}s (status={resp.status})")
            ready = True
            break
        except Exception:
            _log(f"  health check {i+1}/15: {type(Exception).__name__}")

    if not ready:
        # 超时，终止并输出日志
        stop_test_server(_server_proc)
        with open(UV_OUT, "r", encoding="utf-8") as f:
            lines = f.readlines()
        last = "".join(lines[-100:])
        raise RuntimeError(
            f"Server did not become ready after 15 seconds.\n"
            f"stdout tail:\n{last}"
        )

    _server_started = True
    return _server_proc, True


def ensure_test_server():
    """
    测试脚本入口调用：确保 8000 端口有服务运行。
    已有则不启动；没有则自动启动。
    返回 None 表示使用已有服务；返回 proc 表示新启动（调用方不需要管理）。
    注册 atexit 自动清理。
    """
    global _server_proc

    with _server_lock:
        proc, is_new = start_test_server()

    if is_new and _server_proc is not None:
        atexit.register(stop_test_server, _server_proc)
        _log("Registered atexit cleanup for uvicorn")

    return proc


def kill_test_server():
    """
    手动清理：强制终止当前测试服务器。
    用于测试脚本自行结束时清理。
    """
    global _server_proc
    with _server_lock:
        if _server_proc is not None:
            stop_test_server(_server_proc)
            _server_proc = None
            _log("Server manually stopped.")


if __name__ == "__main__":
    # 独立运行：启动服务器保持运行
    ensure_test_server()
    print("Test server running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        kill_test_server()