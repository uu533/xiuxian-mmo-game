# OpenClaw 会话启动检查清单

> 每次新会话启动时，必须按顺序执行以下检查，然后输出"上下文恢复报告"，等待用户明确任务后再开发。
>
> **禁止在未完成检查前直接开始开发。**

---

## 检查步骤

### 第一步：读取长期记忆和固定技能

```
1. 读取 MEMORY.md
2. 读取 memory/YYYY-MM-DD.md（当天日期）
3. 读取 generator-log.md
4. 读取 BRANCH_POLICY.md
5. 读取 AI_WORKSPACE_RULES.md
6. 读取 skills/ 下所有技能文档：
   - skills/QUEST_ANTI_DEADLOCK.md
   - skills/LOCALIZATION_ZH_CHECK.md
   - skills/PLAYER_FLOW_QA.md
   - skills/TEST_DISCIPLINE.md
   - skills/GIT_SAFETY.md
   - skills/COMPLETION_REPORT_TEMPLATE.md
```

如果 MEMORY.md、generator-log.md、skills/ 任一缺失，必须先报告，不要直接开发。

### 第二步：Git 状态检查

```bash
# 检查当前分支
git branch --show-current

# 检查当前 commit
git rev-parse --short HEAD

# 检查工作区
git status --short

# 查看最近 10 条 commit
git log --oneline -10
```

### 第三步：上下文确认

1. 当前分支是否为 `ai/lab-life-skills-content`（或用户指定的实验分支）
2. main 分支不允许直接修改
3. 是否有未提交的修改（如果有，先报告）
4. 最近是否有合并 main 的记录

### 第四步：输出报告

输出格式如下：

```
# 上下文恢复报告

## 基本信息
- 项目路径：E:\opencolw\game\xiuxian-mmo-game
- 当前分支：xxx
- 当前 commit：xxx
- 最近 commit：xxx

## 文件状态
- MEMORY.md：✅/❌
- memory/YYYY-MM-DD.md：✅/❌
- generator-log.md：✅/❌
- 其他检查项...

## 未完成事项（如有）
- ...

## 可以继续的工作（如有）
- ...

## 禁止操作确认
- ❌ merge main
- ❌ push main
- ❌ force push
- ❌ reset --hard
- ❌ git clean
- ❌ 删除文件
- ❌ 开发新功能（未获任务前）
```

---

## 决策规则

### 如果一切正常
→ 输出"上下文恢复报告"，等待用户任务。

### 如果发现以下情况
→ 立即停止，报告问题：
- 当前分支是 main
- 有大量未跟踪/删除的文件
- 核心文件（backend/、frontend/、tests/）被删除
- 需要 force push / reset / clean
- git 仓库损坏

### 如果有未提交修改
→ 先报告未提交内容，问用户是否要提交或暂存。

---

## 常见场景

### 场景 A：刚完成合并，用户想继续开发
1. 读取当天 memory/YYYY-MM-DD.md
2. 读取 generator-log.md 确认最新进度
3. 检查分支状态
4. 确认是否可以开新实验分支
5. 等待用户明确任务

### 场景 B：Codex 合并完成，需要开新分支
1. 确认 main 已更新
2. 从 main 拉出新实验分支（由用户/Codex 执行）
3. 读取 MEMORY.md 了解项目上下文
4. 等待任务分配

### 场景 C：模型重启后首次对话
1. 按本清单完整执行
2. 确认当前分支和 commit
3. 输出"上下文恢复报告"
4. 等待用户任务

---

## 长期记忆更新规则

每轮任务结束后，必须更新：

| 文件 | 更新时机 |
|------|----------|
| `memory/YYYY-MM-DD.md` | 每天结束时 |
| `MEMORY.md` | 重要上下文变更时 |
| `generator-log.md` | 每轮任务结束时 |

---

## 禁止事项

- ❌ 不读 MEMORY.md 就开始开发
- ❌ 直接 git push main
- ❌ 不检查分支就 commit
- ❌ 假设上次的工作还在继续
- ❌ 在未恢复上下文前就开始写代码
