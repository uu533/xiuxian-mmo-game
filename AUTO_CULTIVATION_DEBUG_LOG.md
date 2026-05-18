# AUTO_CULTIVATION_MVP_DEBUG_LOG.md

> 本文档记录自动修行 MVP v2.0 开发过程中卡住的问题、排查过程和根因分析。
> 每次遇到连续 3 次未解决的问题，必须先写文档再继续。

---

## 项目规则（强制）

1. **新增 `character_payload` 字段时**，必须同步检查 `backend/schemas/character.py` 的 `CharacterResponse` Pydantic model，缺失字段会导致 FastAPI 静默丢弃该字段。
2. **新增 `action_type` handler 时**，必须检查 `_result()` 的完整参数签名 `(db, user, success, message, cost, rewards, logs, action_type, data=None)`，漏传 `action_type` 会导致 `TypeError`。
3. **测试失败时**，必须先区分错误类型：业务 API 错误 / schema 错误 / 测试脚本错误 / Python 环境错误，再决定修复方向。
4. **同一问题连续 3 次未解决**，必须停止修改、写入本文档、汇报给用户，再继续。

---

## 问题列表

### 问题 1：CharacterResponse schema 缺少 auto_cultivation

| 项目 | 内容 |
|------|------|
| **触发方式** | 调用 `GET /character/me`，返回的 `character` 对象中不包含 `auto_cultivation` 字段 |
| **报错信息** | 无明显报错，FastAPI 静默丢弃字段。PowerShell 查看 `$data.character.PSObject.Properties.Name` 显示缺少 `auto_cultivation` |
| **根因判断** | `backend/services/character_service.py` 的 `character_payload()` 返回了 `auto_cultivation`，但 `backend/schemas/character.py` 的 `CharacterResponse` Pydantic model 没有定义该字段，FastAPI 自动过滤了未知字段 |
| **已修复方式** | 在 `backend/schemas/character.py` 的 `CharacterResponse` 中添加了 `auto_cultivation: dict | None = None` |
| **如何防止** | 规则 #1 |
| **当前状态** | ✅ 已修复 |

---

### 问题 2：`_result()` 漏传 `action_type` 参数

| 项目 | 内容 |
|------|------|
| **触发方式** | 调用 `/action/execute`，action_type 为 `auto_cultivation_config` |
| **报错信息** | `TypeError: _result() missing 1 required positional argument: 'action_type'` |
| **根因判断** | `backend/services/action_service.py` 中新增的 4 个 auto_cultivation action handler（_auto_cultivation_config / settle / pause / resume）调用 `_result()` 时，漏传了 `action_type` 参数（倒数第二个参数） |
| **已修复方式** | 为 4 个 handler 的 `_result()` 调用补上了 `action_type` 字符串（分别为 `"auto_cultivation_config"` / `"auto_cultivation_settle"` / `"auto_cultivation_pause"` / `"auto_cultivation_resume"`） |
| **如何防止** | 规则 #2 |
| **当前状态** | ✅ 已修复 |

---

### 问题 3：测试脚本 urllib.request import / Python 解释器路径问题

| 项目 | 内容 |
|------|------|
| **触发方式** | 运行 `python tests/auto_cultivation_player_flow_test.py` |
| **报错信息** | `ModuleNotFoundError: No module named 'encodings'` 或 `HTTPError` 无详情 |
| **根因判断** | `python` 命令在 PowerShell 中指向的 Python 解释器路径不稳定，可能指向非完整安装的 Python。直接用 `C:\Users\WTT\AppData\Local\Programs\Python\Python311\python.exe` 可以正常 import urllib.request |
| **已修复方式** | `test_server_utils.py` 改用 `sys.executable`，不再硬编码用户机器路径 |
| **如何防止** | 测试脚本中统一使用 `sys.executable` 获取 Python 路径 |
| **当前状态** | ✅ 已修复 |

---

### 问题 4：auto_cultivation_resume 500 Internal Server Error

| 项目 | 内容 |
|------|------|
| **触发方式** | 调用 `/action/execute`，action_type 为 `auto_cultivation_resume`，params 为 `{}` |
| **最小复现请求** | ```json POST /action/execute {"action_type":"auto_cultivation_resume","params":{}} ``` |
| **报错信息** | HTTP 500 Internal Server Error |
| **完整 traceback** | ``` |
| | TypeError: can't subtract offset-naive and offset-aware datetimes |
| | File "backend/services/auto_cultivation_service.py", line 47, in get_auto_cultivation_status |
| | elapsed = utc_now() - character.last_auto_settle_at |
| | ``` |
| **根因判断** | `utc_now()` 返回 `datetime.now(timezone.utc)`（timezone-aware），但 SQLite 存储的 `last_auto_settle_at` 是 `datetime.utcnow()`（timezone-naive）。两者不能直接相减。初次修复错误地改成了全局 `datetime.utcnow()`，这是全局危险修改。 |
| **正确修复方式** | 在 `backend/services/auto_cultivation_service.py` 内部做 naive/aware 兼容处理，不改全局 `time_utils.py`。新增 helper `normalize_dt_for_delta()` 处理 nil 和时区，调用处同时做本地 naive 转换。 |
| **如何防止** | 规则 #6：不要轻易修改全局 time_utils.py，优先在业务服务内做 datetime 兼容处理。 |
| **当前状态** | ✅ 已修复（局部修复，auto_cultivation_service.py 内部） |

---

## 排查过程记录

### 2026-05-18 第一轮排查

1. 修复 Schema：添加 `auto_cultivation: dict | None = None` → 成功，`auto_cultivation` 在 `/character/me` 中出现
2. 修复 `_result()`：补上 4 个 handler 的 `action_type` 参数 → `auto_cultivation_config` 和 `auto_cultivation_settle` 的 500 消失，测试通过到 `pause` 后的 `resume`
3. `auto_cultivation_resume` 仍报 500，需要捕获后端日志 traceback

### 2026-05-18 第二轮排查（最小定位）

**Python 环境验证：**
```
C:\Users\WTT\AppData\Local\Programs\Python\Python311\python.exe -c "import urllib.request; print('urllib.request ok')"
→ urllib.request ok ✅
```

**待执行：** 用 Python311 运行测试，看完整的 traceback 输出。

---

## 修复历史

| 日期 | 问题 | 修复文件 |
|------|------|----------|
| 2026-05-18 | Schema 缺少字段 | backend/schemas/character.py |
| 2026-05-18 | _result() 漏 action_type | backend/services/action_service.py |
| 2026-05-18 | 测试脚本 urllib import | tests/auto_cultivation_player_flow_test.py（统一 Python 路径）|

---

## 经验记录（2026-05-19 更新）

### Windows Agent / 测试环境经验

1. **subprocess.Popen 启动 uvicorn 优于 PowerShell Job**
   - Start-Process + -NoNewWindow + RedirectStandardOutput 可能卡死
   - 解决：Python subprocess.Popen + stdout/stderr 落盘到文件 + 健康检查轮询

2. **Python 解释器路径用 `sys.executable`，不要写死**
   - 硬编码 `C:\Users\WTT\...` 只在该机器有效
   - `sys.executable` 自动获取当前 Python 解释器

3. **8000 端口验证**
   - 不能只检查端口是否在监听，必须确认是本项目服务
   - 用 `/docs` 或 `/openapi.json` 的 FastAPI 特征验证
   - 如果被非本项目服务占用，应报错提示用户清理

4. **datetime naive/aware 问题**
   - `datetime.now(timezone.utc)` 返回 aware，`datetime.utcnow()` 返回 naive
   - SQLite 通过 Python 不存储时区信息，总是 naive
   - 不要轻易修改全局 `utc_now()`，在业务服务内做局部兼容处理

5. **PowerShell 编码问题**
   - `print()` 输出中文到 stdout 可能触发 `UnicodeEncodeError: 'gbk' codec can't encode`
   - 解决：输出写入文件而非 stdout

6. **测试基础设施**
   - 共享测试服务器用 `subprocess.Popen` + 健康检查 + `atexit` 清理
   - 禁止用 `taskkill /F /IM python.exe`（会杀父进程）
   - 测试进程内启动 uvicorn，比依赖外部进程更可靠