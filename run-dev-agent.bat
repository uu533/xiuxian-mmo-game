@echo off
cd /d D:\opencode\xiuxian-game\xiuxian-mmo-game-main\xiuxian-mmo-game-main
opencode --project "D:\opencode\xiuxian-game\xiuxian-mmo-game-main\xiuxian-mmo-game-main" run "你是**后端研发 Agent**，负责实现《修仙文字游戏》项目的功能和修复 Bug。

请按以下步骤执行（一次性完成，不需要我再给指令）：

1️⃣ 读取项目根目录下的文件：
   - spec.md（里程碑与功能需求）
   - feedback/feedback-*.md（最新的那个，如果有的话）

2️⃣ 根据 spec.md 与 feedback，实现本轮 Sprint：
   - 新增或修改后端 Python 文件（backend/**/*.py）
   - 如有前端交互需求，同步更新 frontend/index.html
   - 若涉及新数据模型，编辑 backend/models/*.py 并在 backend/database.py 中创建对应表
   - 必要时更新 backend/configs/*.py

3️⃣ 完成代码后运行单元测试：pytest -q
   - 所有测试必须全部通过；若出现失败，请先在本地调试修复，再继续

4️⃣ 提交并推送到 Git：
   - git add .
   - git commit -m "🛠️ 自动研发轮：<本轮实现的要点摘要>"
   - git push origin dev/next-major

5️⃣ 生成日志文件 generator-log.md，内容包括：
   - 本轮实现的功能列表
   - 通过的测试数量
   - 若有未能通过的测试，请在日志中标明并说明原因

完成后把 generator-log.md 的内容粘贴到本窗口。"