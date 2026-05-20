"""
前端语法检查：检测游离 await、SyntaxError 等基础 JS 问题。
不依赖 Playwright，只用 Node.js 做语法检查。

使用方式：
    python tests/frontend_syntax_check.py
"""

import os, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRONTEND_PATH = ROOT / "frontend" / "index.html"
NODE_TEST_SCRIPT = ROOT / "_temp_js_syntax_check.mjs"


def extract_script(html_path: Path) -> str | None:
    """提取 <script>...</script> 内容（最后一个 script 标签内容）"""
    text = html_path.read_text(encoding="utf-8")
    # 找到最后一个 <script> 到 </script> 之间的内容（排除空标签）
    matches = re.findall(r'<script>(.*?)</script>', text, re.DOTALL)
    if not matches:
        return None
    # 返回最后一个 script 块（通常是主逻辑）
    return matches[-1].strip()


def check_with_node(script: str) -> tuple[bool, str]:
    """用 node --check 做语法检查，返回 (ok, message)"""
    NODE_TEST_SCRIPT.write_text(script, encoding="utf-8")
    result = subprocess.run(
        ["node", "--check", str(NODE_TEST_SCRIPT)],
        capture_output=True,
        text=True,
        timeout=15,
    )
    if NODE_TEST_SCRIPT.exists():
        try:
            NODE_TEST_SCRIPT.unlink()
        except Exception:
            pass
    if result.returncode == 0:
        return True, "语法检查通过"
    else:
        return False, result.stderr.strip()


def check_free_await(script: str) -> tuple[bool, list[str]]:
    """检测游离 await（不在 async function 内）

    策略：先找出所有"合法的 async 函数声明/回调"上下文，
    其余 top-level await（不在任何函数体内）为游离。
    """
    issues = []

    lines = script.split("\n")

    # 标记每行是否在"合法 async 上下文"中
    # 上下文类型：
    #   - function.async X(...) { ... }
    #   - const X = async (...) => { ... }
    #   - setInterval(async () => { ... })
    #   - setTimeout(async () => { ... })
    #   - Promise.all(async () => ...)
    #
    # 我们用括号深度来追踪是否在合法 async 上下文中。
    # 任何不在 {} 块内的 await 都是游离的。

    # 计算行级别的 brace_depth（累计）
    line_brace_depth = 0
    # 我们追踪"进入 async 上下文"的状态
    # 当 brace_depth > 0 时，我们在某个函数体内，await 合法
    # 当 brace_depth == 0 时，我们在 script 顶层

    prev_brace_depth = 0  # 上一行的 brace_depth

    for lineno, line in enumerate(lines, 1):
        stripped = line.strip()

        if stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
            continue

        # 更新 brace_depth（累计，跨行）
        open_count = stripped.count('{')
        close_count = stripped.count('}')

        if open_count > 0:
            line_brace_depth += open_count

        # 关键检测：在 brace_depth == 0 时发现 await → 游离
        # 但要排除单行函数声明（`async function name() {}` 这种情况很少见）
        if line_brace_depth == 0:
            # 不在任何函数体内
            if 'await ' in stripped:
                # 排除函数声明行（可能有 async 关键字但还没进函数体）
                if not (re.search(r'(async\s+)?function\s+\w+\s*\(', stripped) and '{' not in stripped):
                    issues.append(f"  Line {lineno}: 游离 await（不在任何函数体内）: {stripped[:100]}")

        if close_count > 0:
            line_brace_depth -= close_count
            if line_brace_depth < 0:
                line_brace_depth = 0

    return issues


def main():
    print("=== 前端语法检查 ===")
    print(f"检查文件: {FRONTEND_PATH}")

    if not FRONTEND_PATH.exists():
        print(f"[SKIP] 文件不存在: {FRONTEND_PATH}")
        sys.exit(0)

    # 检查 Node.js 是否可用
    try:
        subprocess.run(["node", "--version"], capture_output=True, timeout=5, check=True)
        node_ok = True
    except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.CalledProcessError):
        node_ok = False

    script = extract_script(FRONTEND_PATH)
    if not script:
        print("[SKIP] 未找到 <script> 标签")
        sys.exit(0)

    print(f"提取到 JS 代码 {len(script)} 字符")

    all_passed = True

    # 1. Node.js 语法检查
    if node_ok:
        ok, msg = check_with_node(script)
        if ok:
            print(f"[PASS] node --check 语法检查通过")
        else:
            print(f"[FAIL] node --check 发现语法错误:")
            print(msg)
            all_passed = False
    else:
        print("[SKIP] Node.js 未安装，跳过 --check 语法检查")
        print("       请安装 Node.js 以启用自动语法检查")

    # 2. 游离 await 检测（不依赖 Node）
    issues = check_free_await(script)
    if issues:
        print(f"[FAIL] 发现 {len(issues)} 个游离 await 问题:")
        for issue in issues:
            print(issue)
        all_passed = False
    else:
        print(f"[PASS] 无游离 await")

    print()
    if all_passed:
        print("=== 检查全部通过 ===")
        sys.exit(0)
    else:
        print("=== 检查失败 ===")
        sys.exit(1)


if __name__ == "__main__":
    main()