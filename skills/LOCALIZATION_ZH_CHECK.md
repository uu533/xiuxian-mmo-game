# LOCALIZATION_ZH_CHECK

## 目的

玩家可见内容必须中文优先，内部 id 可以是英文，但玩家界面不能出现未翻译英文。

## 必查范围

每次任务完成前，必须检查以下玩家可见内容：

1. 任务名
2. 任务描述
3. 任务目标
4. 任务奖励
5. 任务状态
6. 物品名
7. 材料名
8. 丹药名
9. 符箓名
10. 法器名
11. 阵法名
12. 功法名
13. 宗门名
14. 按钮文案
15. 成功提示
16. 失败提示
17. 错误信息
18. 奖励描述
19. 日志
20. active_effect 名称和描述
21. 生活技能配方名称
22. 生活技能效用说明

## 搜索关键词

每轮完成前必须搜索以下关键词，判断是否为玩家可见英文：

- Missing
- Not enough
- Recipe
- material
- Foundation
- Talisman
- Supply
- Formula
- low_material
- mana_pill
- Huiqi
- Juqi
- Pill
- Dan
- Beast Core
- Explore Puppet
- success
- failed
- requirement
- No active
- Already has
- Task

## 允许情况

允许内部 id 使用英文，例如：

- low_material
- foundation_pill
- swift_talisman
- explore_luck_bonus

但玩家看到的 name / description / message 必须是中文。

## 示例

错误：

Missing material: low_material x2

正确：

缺少材料：低阶炼器材 x2

错误：

Not enough mana

正确：

法力不足

错误：

Talisman Supply

正确：

符箓补给

## 硬规则

只要玩家界面能看到英文，就必须修复或在报告中明确说明为什么暂时不能修。