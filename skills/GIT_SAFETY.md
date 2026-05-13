# GIT_SAFETY

## 目的

防止 AI Agent 误删项目、污染 main、错误合并、提交临时文件。

## 绝对禁止

1. git reset --hard
2. git clean
3. git push --force
4. git push -f
5. git merge origin/dev/next-major
6. git rebase main
7. 直接在 main 开发
8. 删除分支
9. 删除核心目录
10. 删除数据库或迁移文件
11. 提交临时脚本
12. 提交截图
13. 提交缓存文件
14. 提交错误目录
15. 未经确认修改 backend/database.py、models、schemas

## 每轮开始必须检查

1. 当前分支：
 git branch --show-current

2. 当前 commit：
 git rev-parse --short HEAD

3. 工作区：
 git status --short

4. 最近提交：
 git log --oneline -10

## 每轮结束必须检查

1. git diff --name-status
2. git diff --stat
3. 是否有 deleted 文件
4. 是否有异常未跟踪文件
5. 是否只修改允许文件
6. 是否有临时文件
7. 是否误建错误目录
8. 是否修改 main
9. 是否需要拆分提交

## 临时文件规则

以下文件默认不应提交：

- _run8000.bat
- _run_server.bat
- _run_smoke_test.py
- _test_v2.py
- _sim_check.py
- *.png
- *.tmp
- *.log
- __pycache__/
- .pytest_cache/
- node_modules/
- 临时 JSON 验收产物

## 提交前必须明确

1. 哪些文件加入 commit
2. 哪些文件排除
3. 是否需要拆成多个 commit
4. 是否可以 push 到实验分支
5. 是否需要 Codex 审查

## 硬规则

不确定就不要提交。
不确定就不要 push。
不能让 main 处于不清楚状态。