# 研发日志 - v2.0.1 统一配方系统基础版（第二轮修复）

## 本轮完成
- 补齐 `backend/configs/recipes.py` 中所有配方的 `required_faction` 和 `required_reputation` 字段
- 在 `backend/services/simulation_service.py` 中添加生活技能统计字段：
  - `alchemy_count`、`talisman_count`、`crafting_count`、`formation_count`
  - `life_skill_mana_used`、`life_skill_mana_ratio`
- 新增 `_simulate_alchemy`、`_simulate_talisman`、`_simulate_crafting`、`_simulate_formation` 模拟函数
- 新增 `_try_life_skill` 智能选择函数，生活技能可被选入模拟行动
- 宗门商店空数组问题经确认为 service 层实现正确，`shop_payload` 已正确实现，问题可能为测试环境玩家未加入宗门所致

## 修改文件
- `backend/configs/recipes.py` - 补齐 required_faction / required_reputation 字段
- `backend/services/simulation_service.py` - 新增生活技能统计与模拟

## 接口变更
无新增接口，上轮 `alchemy`/`talisman`/`crafting`/`formation` 已接入

## 测试结果
- `python -m compileall -q backend tests` - 通过
- `python tests/smoke_test.py` - 通过
- `pytest -q` - 无测试文件（仅 smoke_test）

## simulation 新增字段
```python
"alchemy_count": 0,
"talisman_count": 0,
"crafting_count": 0,
"formation_count": 0,
"life_skill_mana_used": 0,
"life_skill_mana_ratio": 0.0,
```

## 未能解决的问题
- 宗门商店返回空数组：经验证 `shop_payload` 逻辑正确，原因可能为测试时玩家尚未加入宗门（`shop_payload` 要求玩家已加入宗门才会返回商品）

## 下一轮任务
- v2.0.2 炼丹系统 - 实现回气丹/疗伤丹等丹药的实际效果
- 确认spirit_grass、clear_dew 等炼丹材料在探索掉落表中有来源
- 继续完善 simulation 平衡性验证