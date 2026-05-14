# TEST_DISCIPLINE

## 目的

任何代码修改完成后必须测试，不能用"待执行"代替测试。

## 最低测试要求

每次代码修改后必须执行：

1. git branch --show-current
2. git rev-parse --short HEAD
3. git status --short
4. git diff --name-status
5. git diff --stat
6. 确认无 deleted 文件
7. python -m compileall backend
8. smoke_test

## 前端改动额外要求

如果修改 frontend/index.html 或 JS：

1. 前端 JS 静态语法检查
2. 浏览器自动验收或手动验收说明
3. 控制台无明显 JS 错误
4. 关键按钮 action_type 不回归

必须检查：

- explore
- train / practice
- breakthrough
- use_item
- learn_method
- equip_artifact
- alchemy
- talisman
- crafting
- formation
- sect task
- sect shop
- active_effects

## 接口改动额外要求

如果修改接口：

1. curl 或脚本实测接口
2. 检查返回字段
3. 检查错误提示
4. 检查是否误连旧服务

## 数值 / 收益 / 消耗改动额外要求

如果修改数值、配方、材料、效果、calc_service：

必须跑 simulation：

1. 3h with_sect=true
2. 12h with_sect=true
3. 24h with_sect=true

必须检查：

1. 探索占比是否健康
2. 修炼占比是否健康
3. 生活技能占比是否异常升高
4. 是否出现只修炼最优
5. 是否出现只炼丹最优
6. 是否出现只符箓最优
7. 是否出现只炼器最优
8. 是否出现只阵法最优
9. 是否法力循环失控
10. 是否材料循环失控
11. 宗门任务是否仍推进正常

## 禁止话术

禁止用以下话术作为完成结论：

- 待执行
- 需要用户启动后端
- 需要 Codex 后续测试
- 理论上可用
- 建议之后验证
- 未运行但应该没问题

## 如果测试无法运行

必须报告：

1. 具体命令
2. 报错原文
3. 尝试过哪些替代方案
4. 是否可能误连旧服务
5. 当前后端端口和 PID
6. 需要用户提供什么条件

## 硬规则

测试没跑完，不允许说完成。
测试失败，不允许绕过断言。
旧功能断言不允许随意删除或弱化。