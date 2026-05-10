#!/usr/bin/env bash
set -euo pipefail
cd "$(pwd)"

# 启动后端（若已在运行则跳过）
if ! lsof -i:8000 > /dev/null 2>&1; then
  echo "启动 FastAPI..."
  nohup uvicorn main:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &
  sleep 5
fi

# 启动前端（若已在运行则跳过）
if ! lsof -i:5173 > /dev/null 2>&1; then
  echo "启动前端..."
  nohup python -m http.server 5173 --bind 0.0.0.0 > frontend.log 2>&1 &
  sleep 3
fi

# 读取最新 spec（用于评价）
if [[ -f spec.md ]]; then
  echo "读取 spec.md"
else
  echo "未找到 spec.md，使用默认评审"
fi

# 调用产品/测试 Agent（使用 minimax-2.7）
output=$(claude -p --model minimax-2.7 "
你是 QA / 产品经理。使用 Playwright 对 http://localhost:8000 进行完整功能测试，包括登录、角色创建、探索、功法学习、炼丹等流程。按 GAN‑harness 四项评分（设计、原创、工艺、功能）给出 1‑10 分，并写出改进建议。将结果写入 feedback-$(date +%Y%m%d%H%M).md。
")

# 将评审写入文件
logfile="feedback/feedback-$(date +%Y%m%d%H%M).md"
echo "$output" > "$logfile"

echo "评审已写入 $logfile"
