# 修仙游戏自动研发Agent - 问题诊断与状态报告
更新时间：2026-05-10 20:45

## 问题概述

用户希望搭建两个 AI Agent（研发 + QA）交替自动工作的闭环：
- 通过 Windows 定时任务调用 opencode CLI 执行脚本
- 研发 Agent 读 spec.md + feedback → 写代码 → 更新 generator-log.md
- QA Agent 读 spec.md + generator-log.md → 写 feedback/*.md
- 循环迭代推进 v2.0 生活技能系统开发

## 遇到的问题

### 问题1：bat 文件编码问题（BOM 导致）
- **现象**：`UTF-8` 编码的 bat 文件带 BOM 头，导致 `cmd.exe` 执行时报错 `'锘緻echo' 不是内部或外部命令`
- **解决**：使用 `[System.IO.File]::WriteAllText` 写入纯 ASCII 编码的 bat 文件

### 问题2：中文消息参数在计划任务环境失效
- **现象**：bat 文件里的中文参数 `"请读取并执行附件中的指令"` 在手动 PowerShell 可以工作，但通过 `cmd.exe /c` 或计划任务执行时参数被破坏
- **尝试**：
  - 用 `--dir .` 替代绝对路径 → 报错 "You must provide a message"
  - 用 `--file prompts/dev-agent-prompt.md` 相对路径 → 缺少消息内容报错
- **原因**：opencode run 需要参数和消息同时存在，且路径需要在正确的工作目录

### 问题3：定时任务配置问题
- **现象**：首次注册的定时任务用了 `-Once -At (Get-Date)` 导致任务只执行一次就停止
- **解决**：用正确的重复配置重新注册任务：
  ```powershell
  -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 20) -RepetitionDuration (New-TimeSpan -Days 9999)
  ```

### 问题4：后端服务无法在计划任务环境启动
- **现象**：QA Agent 需要启动 `uvicorn main:app --port 8000`，但在计划任务上下文里启动失败（ConnectionRefused）
- **原因**：opencode 通过计划任务执行时，工作目录和 Python 模块路径可能不匹配；且 server 启动后进程可能立即退出
- **现状**：测试代码已经在执行（smoke_test 跑了），但部分断言失败是因为后端没启动成功

### 问题5：LastTaskResult: 1（任务失败）
- **现象**：两个定时任务（xiuxian-dev、xiuxian-qa）每次运行后 `LastTaskResult: 1`
- **分析**：bat 文件编码问题导致参数传递失败，opencode 实际上没有正确接收到参数
- **状态**：已修复 bat 文件（ASCII 编码），待验证

## 当前架构

### 文件结构
```
D:\opencode\xiuxian-game\xiuxian-mmo-game-main\xiuxian-mmo-game-main\
├── prompts\
│   ├── dev-agent-prompt.md     # 研发 Agent 提示词
│   └── qa-agent-prompt.md      # QA Agent 提示词
├── feedback\                   # QA 评审报告目录
│   ├── feedback-202605101000.md
│   └── feedback-202605101430.md
├── run-dev-agent.bat           # 研发任务启动脚本
├── run-qa-agent.bat            # QA任务启动脚本
├── generator-log.md           # 研发日志（追加模式）
└── spec.md                     # 开发大纲
```

### bat 文件内容（ASCII 编码）
```bat
@echo off
opencode run --file prompts\dev-agent-prompt.md --dir . -m minimax-cn-coding-plan/MiniMax-M2.7
```

```bat
@echo off
opencode run --file prompts\qa-agent-prompt.md --dir . -m minimax-cn-coding-plan/MiniMax-M2.7
```

### 定时任务配置
```
xiuxian-dev  - 每20分钟 - 执行 run-dev-agent.bat
xiuxian-qa   - 每20分钟（错开10分钟） - 执行 run-qa-agent.bat
```

## 待解决的问题

1. **bat 文件还需要再次验证**：刚刚修复的 ASCII bat 文件需要验证是否能正常执行
2. **消息内容缺失**：当前 bat 缺少 `"请读取并执行附件中的指令"` 这个消息参数，可能导致 opencode 认为没有提供消息
3. **后端启动问题**：QA Agent 需要先启动后端才能运行测试，需要在提示词里解决服务启动问题

## 建议的修复步骤

1. 验证 bat 文件能否正常工作：
   ```powershell
   cmd.exe /c "D:\opencode\xiuxian-game\xiuxian-mmo-game-main\xiuxian-mmo-game-main\run-dev-agent.bat"
   ```

2. 如果 bat 仍报错，需要同时提供消息参数和文件路径

3. QA Agent 提示词需要简化后端启动逻辑，或者在系统已经运行后端的情况下执行

## v2.0 开发进度

| 阶段 | 状态 | 说明 |
|------|------|------|
| v2.0.1 统一配方系统基础版 | ✅ 完成 | recipes.py, life_skill_service.py, 4个action_type |
| v2.0.2 炼丹系统 | 进行中 | 材料掉落已配置，丹药效果待实现 |
| v2.0.3 符箓系统 | 待开始 | |
| v2.0.4 炼器系统 | 待开始 | |
| v2.0.5 阵法系统 | 待开始 | |

## 下一步行动

1. 手动测试 bat 文件是否正常工作
2. 如果正常，手动跑一次研发和 QA 完整流程
3. 确认循环可以跑通后，让定时任务自动运行
4. 定期检查 generator-log.md（追加模式）和 feedback/ 目录（新文件）确认状态

## 模型配置

- 研发 Agent：minimax-cn-coding-plan/MiniMax-M2.7（codingplan 会员）
- QA Agent：minimax-cn-coding-plan/MiniMax-M2.7（两个 Agent 共用同一模型）

## 相关文件路径

- 项目根目录：`D:\opencode\xiuxian-game\xiuxian-mmo-game-main\xiuxian-mmo-game-main`
- 研发脚本：`D:\opencode\xiuxian-game\xiuxian-mmo-game-main\xiuxian-mmo-game-main\run-dev-agent.bat`
- QA 脚本：`D:\opencode\xiuxian-game\xiuxian-mmo-game-main\xiuxian-mmo-game-main\run-qa-agent.bat`