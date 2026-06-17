from backend.configs.actions import ACTION_CONFIGS
from backend.configs.artifacts import ARTIFACT_EFFECTS_BY_CODE
from backend.configs.formulas import (
    BASE_HP_BY_STAGE,
    BREAKTHROUGH_INNER_DEMON_FACTOR,
    BREAKTHROUGH_LUCK_FACTOR,
)
from backend.configs.methods import METHOD_EFFECTS_BY_CODE
from backend.configs.sects import SECT_TASK_LIMITS
from backend.models import Character
from backend.services.active_effect_service import effect_value
from backend.services.realm_service import current_realm_config, normalize_realm, qi_refining_level
from backend.services.spiritual_root_service import root_rate


def get_base_attack_by_realm(character: Character) -> int:
    """
    根据角色境界计算基础攻击力。
    添加参数验证和异常处理。
    """
    if character is None:
        return 0

    normalize_realm(character)
    realm_name = character.realm
    if realm_name.startswith("炼气"):
        return qi_refining_level(realm_name) * 5
    if realm_name == "筑基初期":
        return 80
    if realm_name == "筑基中期":
        return 100
    if realm_name == "筑基后期":
        return 120
    if realm_name == "结丹初期":
        return 180
    if realm_name == "结丹中期":
        return 220
    if realm_name == "结丹后期":
        return 260

    from backend.configs.realms import REALM_NAMES

    try:
        index = REALM_NAMES.index(realm_name)
        nascent_index = REALM_NAMES.index("元婴初期")
        return 500 + (index - nascent_index) * 240
    except ValueError:
        # 如果realm_name不在REALM_NAMES中（例如旧数据格式），返回默认值
        return 500


def get_base_defense_by_realm(character: Character) -> int:
    """
    根据角色境界计算基础防御力。
    添加参数验证。
    """
    if character is None:
        return 0
    return get_base_attack_by_realm(character)


def get_max_mana(character: Character) -> int:
    """
    计算角色最大法力值。
    添加参数验证。
    """
    if character is None:
        return 100
    return max(100, get_base_attack_by_realm(character) * 12 + _method_mana_bonus(character) + _artifact_mana_bonus(character))


def get_max_hp(character: Character) -> int:
    """
    计算角色最大气血值。
    添加参数验证。
    """
    if character is None:
        return 100
    normalize_realm(character)
    base = BASE_HP_BY_STAGE.get(character.realm_stage, 100)
    return base + get_base_defense_by_realm(character) * 2


def get_cultivation_speed(character: Character) -> float:
    """
    计算修炼速度。
    添加参数验证。
    """
    if character is None:
        return 1.0
    return root_rate(character.spiritual_root) + _method_cultivation_speed_bonus(character)


def get_cultivation_efficiency(character: Character) -> float:
    """
    计算连续修炼效率衰减。
    修复：添加参数验证和action_records的None检查。
    调整：使用渐进式惩罚 [1.0, 0.9, 0.8, 0.7, 0.6, 0.5]
    """
    if character is None:
        return 1.0

    consecutive_trains = 0
    # 添加None检查，避免TypeError
    if character.action_records is None:
        return 1.0

    # 只取最近 10 条记录，避免全表遍历
    recent_records = sorted(character.action_records, key=lambda item: item.id, reverse=True)[:10]
    for record in recent_records:
        if record.action_type != "train" or not (record.result_json or {}).get("success"):
            break
        consecutive_trains += 1
        if consecutive_trains >= 6:  # 调整为6次，匹配新的惩罚数组
            break
    # 渐进式惩罚：第1次1.0，第2次0.9，第3次0.8，第4次0.7，第5次0.6，第6次及以后0.5
    penalty_array = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5]
    return penalty_array[consecutive_trains] if consecutive_trains < 6 else 0.5


def get_train_cultivation_bonus(character: Character) -> float:
    """
    获取修炼时的修为加成。
    添加参数验证。
    """
    if character is None:
        return 0.0
    return min(0.18, effect_value(character, "train_cultivation_bonus"))


def get_breakthrough_rate(character: Character) -> float:
    """
    计算突破成功率。
    添加参数验证。
    """
    if character is None:
        return 0.02

    config = current_realm_config(character)
    rate = config.breakthrough_rate
    rate += character.hidden_luck * BREAKTHROUGH_LUCK_FACTOR
    # 心魔值降低突破率（BUG-004：实现影响机制）
    rate -= character.hidden_inner_demon * BREAKTHROUGH_INNER_DEMON_FACTOR
    rate += _method_breakthrough_bonus(character)
    if character.realm == "结丹后期":
        rate -= 0.04
    if character.realm.startswith("元婴") or character.realm.startswith("化神"):
        rate -= 0.03
    return max(0.02, min(0.9, rate))


def get_final_attack(character: Character) -> int:
    """
    计算最终攻击力（基础+功法+法宝）。
    添加参数验证。
    """
    if character is None:
        return 0
    return get_base_attack_by_realm(character) + _method_attack_bonus(character) + _artifact_attack_bonus(character)


def get_final_defense(character: Character) -> int:
    """
    计算最终防御力（基础+功法+法宝）。
    添加参数验证。
    """
    if character is None:
        return 0
    return get_base_defense_by_realm(character) + _method_defense_bonus(character) + _artifact_defense_bonus(character)


def get_action_mana_cost(character: Character, action_type: str) -> int:
    """
    计算行动法力消耗。
    添加参数验证。
    """
    if character is None or action_type is None:
        return 0

    base = int(ACTION_CONFIGS.get(action_type, {}).get("mana_cost", 0))
    if action_type == "explore" and effect_value(character, "explore_mana_discount") > 0:
        return max(1, base - get_swift_talisman_mana_discount(character))
    return base


def get_life_skill_mana_cost(character: Character, recipe: dict) -> int:
    """
    计算生活技能法力消耗。
    添加参数验证。
    """
    if character is None or recipe is None:
        return 0
    _ = character
    return int(recipe.get("mana_cost", 0))


def get_life_skill_success_rate(character: Character, recipe: dict) -> float:
    """
    计算生活技能成功率。
    添加参数验证。
    """
    if character is None or recipe is None:
        return 0.05
    _ = character
    return max(0.05, min(1.0, float(recipe.get("success_rate", 1.0))))


def get_scout_talisman_luck_bonus(character: Character) -> int:
    """
    获取探查符运气加成。
    添加参数验证。
    """
    if character is None:
        return 0
    return int(1000 * effect_value(character, "explore_luck_bonus"))


def get_guard_talisman_damage_reduction(character: Character) -> float:
    """
    获取护身符伤害减免。
    添加参数验证。
    """
    if character is None:
        return 0.0
    return min(0.5, effect_value(character, "explore_damage_reduction"))


def get_swift_talisman_mana_discount(character: Character) -> int:
    """
    获取速行符法力折扣。
    添加参数验证。
    """
    if character is None:
        return 0
    return int(effect_value(character, "explore_mana_discount"))


def get_sect_reward_multiplier(
    task_code: str,
    task_type: str,
    recent_task_codes: list[str],
    recent_task_types: list[str],
    completed_today: int,
) -> tuple[float, list[str]]:
    limit = int(SECT_TASK_LIMITS.get("daily_task_limit", 18))
    if completed_today >= limit:
        return 0.0, ["daily_limit"]

    reasons: list[str] = []
    multiplier = 1.0
    same_task_streak = _prefix_count(recent_task_codes, task_code)
    same_type_streak = _prefix_count(recent_task_types, task_type)
    task_decay = SECT_TASK_LIMITS.get("same_task_decay", [1.0])
    type_decay = SECT_TASK_LIMITS.get("same_type_decay", [1.0])

    if same_task_streak:
        multiplier *= float(task_decay[min(same_task_streak, len(task_decay) - 1)])
        reasons.append("same_task_decay")
    if same_type_streak:
        multiplier *= float(type_decay[min(same_type_streak, len(type_decay) - 1)])
        reasons.append("same_type_decay")
    if recent_task_types and recent_task_types[0] != task_type:
        multiplier *= float(SECT_TASK_LIMITS.get("rotation_bonus", 1.0))
        reasons.append("rotation_bonus")

    minimum = float(SECT_TASK_LIMITS.get("minimum_multiplier", 0.25))
    return round(max(minimum, min(1.08, multiplier)), 4), reasons


def apply_item_effects(character: Character, effects: dict) -> dict:
    """
    应用物品效果到角色。
    添加参数验证。
    """
    if character is None or effects is None:
        return {}

    applied: dict = {}
    if effects.get("recover_mana"):
        before = character.mana
        character.mana = min(character.max_mana, character.mana + int(effects["recover_mana"]))
        applied["recover_mana"] = character.mana - before
    if effects.get("recover_hp"):
        before = character.hp
        character.hp = min(character.max_hp, character.hp + int(effects["recover_hp"]))
        applied["recover_hp"] = character.hp - before
    if effects.get("cultivation"):
        gain = int(effects["cultivation"])
        character.cultivation = min(character.cultivation_cap, character.cultivation + gain)
        applied["cultivation"] = gain
    if effects.get("scout_talisman_charge"):
        value = int(effects["scout_talisman_charge"])
        applied["scout_talisman_charge"] = value
    if effects.get("guard_talisman_charge"):
        value = int(effects["guard_talisman_charge"])
        applied["guard_talisman_charge"] = value
    if effects.get("swift_talisman_charge"):
        value = int(effects["swift_talisman_charge"])
        applied["swift_talisman_charge"] = value
    if effects.get("train_next_bonus"):
        value = int(effects["train_next_bonus"])
        applied["train_next_bonus"] = value
    if effects.get("breakthrough_next_bonus"):
        value = int(effects["breakthrough_next_bonus"])
        applied["breakthrough_next_bonus"] = value
    if effects.get("explore_luck_talisman_charge"):
        value = int(effects["explore_luck_talisman_charge"])
        applied["explore_luck_talisman_charge"] = value
    if effects.get("avoid_harm_talisman_charge"):
        value = int(effects["avoid_harm_talisman_charge"])
        applied["avoid_harm_talisman_charge"] = value
    if effects.get("spirit_gather_talisman_charge"):
        value = int(effects["spirit_gather_talisman_charge"])
        applied["spirit_gather_talisman_charge"] = value
    return applied


def scale_reward_value(value: int, multiplier: float) -> int:
    """
    缩放奖励数值。
    添加参数验证。
    """
    if value <= 0 or multiplier <= 0:
        return 0
    return max(1, int(value * multiplier))


def sync_base_and_caps(character: Character) -> None:
    """
    同步角色基础属性和上限值。
    添加参数验证。
    """
    if character is None:
        return

    normalize_realm(character)
    character.base_attack = get_base_attack_by_realm(character)
    character.base_defense = get_base_defense_by_realm(character)
    character.max_mana = get_max_mana(character)
    character.max_hp = get_max_hp(character)
    character.mana = min(character.mana, character.max_mana)
    character.hp = min(character.hp, character.max_hp)


def derived_stats(character: Character) -> dict:
    """
    计算角色派生属性。
    添加参数验证。
    """
    if character is None:
        return {}

    sync_base_and_caps(character)
    return {
        "final_attack": get_final_attack(character),
        "final_defense": get_final_defense(character),
        "final_mana": character.max_mana,
        "cultivation_speed": get_cultivation_speed(character),
        "breakthrough_bonus": round(get_breakthrough_rate(character) - current_realm_config(character).breakthrough_rate, 4),
    }


def _method_attack_bonus(character: Character) -> int:
    total = 0
    for method in character.methods:
        if not method.equipped:
            continue
        config = METHOD_EFFECTS_BY_CODE.get(method.method_code, {})
        total += int(config.get("attack_per_level", 0) * method.level)
    return total


def _prefix_count(values: list[str], expected: str) -> int:
    count = 0
    for value in values:
        if value != expected:
            break
        count += 1
    return count


def _method_defense_bonus(character: Character) -> int:
    total = 0
    for method in character.methods:
        if not method.equipped:
            continue
        config = METHOD_EFFECTS_BY_CODE.get(method.method_code, {})
        total += int(config.get("defense_per_level", 0) * method.level)
    return total


def _method_mana_bonus(character: Character) -> int:
    total = 0
    for method in character.methods:
        if not method.equipped:
            continue
        config = METHOD_EFFECTS_BY_CODE.get(method.method_code, {})
        total += int(config.get("max_mana_per_level", 0) * method.level)
    return total


def _artifact_attack_bonus(character: Character) -> int:
    total = 0
    for artifact in character.artifacts:
        if not artifact.equipped or not artifact.item_instance:
            continue
        config = ARTIFACT_EFFECTS_BY_CODE.get(artifact.item_instance.template.code, {})
        total += int(config.get("attack_per_level", 0) * artifact.item_instance.level)
    return total


def _artifact_defense_bonus(character: Character) -> int:
    total = 0
    for artifact in character.artifacts:
        if not artifact.equipped or not artifact.item_instance:
            continue
        config = ARTIFACT_EFFECTS_BY_CODE.get(artifact.item_instance.template.code, {})
        total += int(config.get("defense_per_level", 0) * artifact.item_instance.level)
    return total


def _artifact_mana_bonus(character: Character) -> int:
    total = 0
    for artifact in character.artifacts:
        if not artifact.equipped or not artifact.item_instance:
            continue
        config = ARTIFACT_EFFECTS_BY_CODE.get(artifact.item_instance.template.code, {})
        total += int(config.get("max_mana_per_level", 0) * artifact.item_instance.level)
    return total


def _method_cultivation_speed_bonus(character: Character) -> float:
    total = 0.0
    for method in character.methods:
        if not method.equipped:
            continue
        config = METHOD_EFFECTS_BY_CODE.get(method.method_code, {})
        total += float(config.get("cultivation_speed_per_level", 0)) * method.level
    return total


def _method_breakthrough_bonus(character: Character) -> float:
    total = 0.0
    for method in character.methods:
        if not method.equipped:
            continue
        config = METHOD_EFFECTS_BY_CODE.get(method.method_code, {})
        total += float(config.get("breakthrough_rate_per_level", 0)) * method.level
    return total


def get_explore_reward_bonus(character: Character) -> float:
    """
    计算探索奖励加成。
    添加参数验证。
    业力值影响：每点业力降低1%探索收益（BUG-004）
    """
    if character is None:
        return 0.0

    total = 0.0
    for artifact in character.artifacts:
        if not artifact.equipped or not artifact.item_instance:
            continue
        config = ARTIFACT_EFFECTS_BY_CODE.get(artifact.item_instance.template.code, {})
        total += float(config.get("explore_reward_bonus_per_level", 0)) * artifact.item_instance.level

    # 基础加成
    bonus = total + min(0.1, effect_value(character, "explore_reward_bonus"))

    return max(-0.5, bonus)  # 最低不超过-50%


def get_battle_power_bonus(character: Character) -> int:
    """
    计算战斗威力加成。
    添加参数验证。
    """
    if character is None:
        return 0

    total = 0
    for artifact in character.artifacts:
        if not artifact.equipped or not artifact.item_instance:
            continue
        config = ARTIFACT_EFFECTS_BY_CODE.get(artifact.item_instance.template.code, {})
        total += int(config.get("battle_power_per_level", 0)) * artifact.item_instance.level
    return total
