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
| **已修复方式** | 统一使用完整路径 `C:\Users\WTT\AppData\Local\Programs\Python\Python311\python.exe` |
| **如何防止** | 测试脚本中统一使用完整 Python 解释器路径 |
| **当前状态** | ✅ 已修复（urllib.request 在 Python311 下正常工作）|

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

## 经验记录（2026-05-18）

### Windows Agent 长任务经验

1. **Start-Process + -NoNewWindow + RedirectStandardOutput/RedirectStandardError 可能卡死**
   - 症状：命令在 PowerShell 工具内一直显示"运行中"，无输出，直到超时
   - 原因：PowerShell 对重定向到文件的子进程处理有问题，stdout/stderr 管道可能阻塞
   - 教训：不要在单条 bash 命令里串 Start-Process + 测试 + 日志读取

2. **禁止无保护启动 uvicorn**
   - 必须使用 supervisor 脚本
   - 服务启动最多等待 15 秒
   - HTTP 请求必须 timeout
   - 测试整体必须 timeout（PowerShell Job + Wait-Job -Timeout）
   - stdout/stderr 必须落盘到文件
   - 结束后必须自动清理进程

3. **PowerShell Job 陷阱**
   - `-Command` 参数中的多行脚本容易出现 `$variable` 被 PowerShell 解析为环境变量的 bug
   - 解决：写 PS1 文件，用 `-File` 参数执行

4. **PowerShell Job + 嵌套 Start-Process**
   - 在 Start-Job 内部再 Start-Process uvicorn，stdout/stderr 重定向可能不工作
   - 解决：让 Python 测试脚本内部启动 uvicorn（使用 threading）+ 直接发 HTTP 请求（不依赖外部进程）

5. **卡住超过 30 分钟的处理流程**
   - 自动停止当前命令（Stop-Job / Stop-Process）
   - 收集日志、端口、进程状态
   - 写 Debug Log 并汇报
   - 不继续等待

6. **datetime naive/aware 问题**
   - `datetime.now(timezone.utc)` 返回 aware，`datetime.utcnow()` 返回 naive
   - SQLite 通过 Python 不存储时区信息，总是 naive
   - 不要轻易修改全局 `utc_now()`，在业务服务内做局部兼容处理

7. **测试依赖外部 uvicorn 进程的问题**
   - smoke_test 等期望服务器已运行
   - 解决：使用 Python 内置 threading 在测试进程内启动 uvicorn（不依赖外部进程）

8. **PowerShell 编码问题**
   - `print()` 输出非 ASCII 字符（如中文日志）到 stdout 时可能触发 `UnicodeEncodeError: 'gbk' codec can't encode`
   - 解决：捕获后写入文件，不依赖 stdout 直接 print