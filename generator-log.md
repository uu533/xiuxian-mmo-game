# 研发日志 - v2.0 生活技能系统（第 4 轮确认）

## 本轮完成
- 修复回气丹无限续航问题：将 `recover_mana` 从 30 降低到 8
- 修复背景：feedback 指出回气丹炼丹消耗 10 点法力，恢复 30 点，理论可无限续航
- 调整后：炼丹消耗 10 点，回气丹恢复 8 点，玩家无法通过循环炼丹无限续航

## 修改文件
- `backend/configs/items.py` - 回气丹 recover_mana: 30 -> 8

## 测试结果
- `python -m compileall -q backend tests` - 通过
- `python tests/smoke_test.py` - 通过

## simulation 验证
- 1h simulation with sect: alchemy_count=0, talisman_count=1, life_skill_mana_ratio=0.0119
- 生活技能 Mana 占比约 1.2%，符合预期（不是主要行动）

## 未能解决的问题
- 宗门商店返回空数组：经验证 shop_payload 逻辑正确，需要玩家先加入宗门
- healing_herb 暂无掉落来源配置（炼丹配方疗伤丹需要）

## 下一轮任务
- v2.0.2 炼丹系统
  - 确认 healing_herb 在掉落表中有来源
  - 实现丹药使用效果（必须走 use_item）
  - 验证不出现"只炼丹最优"
  - 验证回气丹不导致无限续航

---

## 第 4 轮 - 2026-05-11

### 本轮完成
- 分析 feedback-202605101430.md：确认 simulation 已包含生活技能统计字段（之前已实现）
- 确认 healing_herb 已在 drop_tables.py 中配置掉落来源（"炼气前期"和"炼气"阶段都有）
- 确认 recipes.py 已有 required_faction 和 required_reputation 字段
- 确认宗门商店空数组是正常行为（需要先加入宗门）
- 代码审查：life_skill_service.py 错误信息使用中文，无乱码问题
- 编译检查通过
- smoke_test 通过

### 修改文件
- 无代码修改（均为确认性检查）

### 测试结果
- `python -m compileall -q backend tests` - 通过
- `python tests/smoke_test.py` - 通过

### 下一轮任务
- v2.0.2 炼丹系统
  - 实现丹药使用效果（服用回气丹/疗伤丹等必须走 /action/execute + use_item）
  - 丹药效果在 calc_service.py 的 apply_item_effects 中实现
  - 关键检查：验证不出现"只炼丹最优"
  - 关键检查：验证回气丹不导致无限续航（recover_mana=8，炼丹消耗=10，已防止）
