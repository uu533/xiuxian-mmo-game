#!/usr/bin/env bash
set -euo pipefail
cd "$(pwd)"

# 读取最新 feedback（若不存在则视为首次）
latest=$(ls -t feedback/feedback-*.md 2>/dev/null | head -n1 || echo "")
if [[ -n "$latest" ]]; then
  echo "读取反馈 $latest"
else
  echo "首次生成，无历史反馈"
fi

# 调用研发 Agent（使用已配置的 minimax-2.7 模型）
claude -p --model minimax-2.7 "
你是后端研发Agent。读取 spec.md 与最新的 feedback-*.md（如果有），完成本轮 Sprint 中的所有功能实现或 bug 修复。要求：
1️⃣ 只修改/新增 Python/HTML 文件；
2️⃣ 完成后运行 pytest -q，确保全部通过；
3️⃣ 将本轮要点写入 generator-log.md；
4️⃣ 若有依赖变更，更新 requirements.txt。
"

# 自动提交到 Git
if git status --porcelain | grep .; then
  git add .
  git commit -m "🛠️ 自动研发轮：$(date +%Y%m%d%H%M)"
  git push origin dev/next-major
else
  echo "没有文件变化，不需要提交"
fi
