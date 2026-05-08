import json
import random
from collections import Counter
from pathlib import Path

from backend.configs.actions import ACTION_CONFIGS
from backend.configs.artifacts import ARTIFACT_UPGRADE
from backend.configs.breakthrough_requirements import BREAKTHROUGH_REQUIREMENTS
from backend.configs.drop_tables import DROP_TABLES
from backend.configs.methods import METHOD_LEVEL_EXP, METHOD_PRACTICE
from backend.configs.opportunities import LUCKY_EVENT_CONFIG
from backend.configs.realms import REALM_BY_NAME, REALM_NAMES, STARTING_REALM
from backend.configs.recipes_alchemy import ALCHEMY_RECIPES
from backend.configs.recipes_crafting import CRAFTING_RECIPES
from backend.configs.recipes_talisman import TALISMAN_RECIPES
from backend.configs.sects import SECT_TASKS
from backend.database import BASE_DIR
from backend.services.calc_service import get_sect_reward_multiplier, scale_reward_value
from backend.services.realm_service import qi_refining_level
from backend.utils.random_utils import weighted_choice

SIMULATION_RESULT_PATH = BASE_DIR / "simulation_result.json"


def run_simulation(hours: float = 1, with_sect: bool = False) -> dict:
    minutes = max(1, int(hours * 60))
    state = _new_state()
    state["sect_enabled"] = with_sect
    stats = {
        "actions": Counter(),
        "drops": Counter(),
        "warnings": [],
        "breakthrough_attempts": 0,
        "breakthrough_successes": 0,
        "breakthrough_failures_in_row": 0,
        "mana_blocked_minutes": 0,
        "mana_recovered": 0,
        "spirit_stones_spent_on_mana": 0,
        "bag_slots_used_peak": 0,
        "total_spirit_stones_gained": 0,
        "total_cultivation_gained": 0,
        "bottleneck_reasons": Counter(),
        "sect_tasks_completed": 0,
        "sect_contribution_gained": 0,
        "sect_reward_stones": 0,
        "sect_reputation_change": Counter(),
        "sect_task_type_distribution": Counter(),
        "sect_reward_by_type": Counter(),
        "sect_decay_reasons": Counter(),
        "life_skill_outputs": Counter(),
        "life_skill_reward_value": 0,
        "life_skill_by_type": Counter(),
    }

    for minute in range(minutes):
        _auto_prepare(state, stats)
        if with_sect:
            _simulate_sect_layer(state, stats, minute)
        action = _choose_action(state, stats)
        if state["mana"] < _mana_cost(action, state):
            stats["mana_blocked_minutes"] += 1
            _recover_mana(state, stats, _mana_cost(action, state))
            continue
        if action == "train":
            _simulate_train(state, stats)
        elif action == "breakthrough":
            _simulate_breakthrough(state, stats)
        elif action == "practice_method":
            _simulate_practice_method(state, stats)
        elif action in {"alchemy", "talisman", "crafting"}:
            _simulate_life_skill_action(state, stats, action)
        else:
            _simulate_explore(state, stats)
        stats["bag_slots_used_peak"] = max(stats["bag_slots_used_peak"], len(state["items"]))

    result = _build_result(hours, state, stats, minutes, with_sect)
    SIMULATION_RESULT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def _new_state() -> dict:
    return {
        "realm": STARTING_REALM.name,
        "realm_stage": STARTING_REALM.stage,
        "cultivation": 0,
        "cultivation_cap": STARTING_REALM.cultivation_cap,
        "mana": 100,
        "max_mana": 100,
        "hp": 110,
        "max_hp": 110,
        "hidden_luck": 58,
        "hidden_inner_demon": 0,
        "spirit_stones": 100,
        "items": Counter(),
        "method_level": 0,
        "method_exp": 0,
        "method_equipped": False,
        "artifact_level": 0,
        "artifact_equipped": False,
        "scout_talisman_charges": 0,
        "guard_talisman_charges": 0,
        "swift_talisman_charges": 0,
        "artifact_rarity": "白",
        "consecutive_train": 0,
        "explore_count": 0,
        "sect_joined": False,
        "sect_contribution": 0,
        "sect_enabled": False,
        "sect_task_status": None,
        "sect_position": "outer_disciple",
        "sect_recent_task_codes": [],
        "sect_recent_task_types": [],
        "sect_task_type_counts": Counter(),
        "sect_completed_today": 0,
        "sect_task_code": None,
        "sect_task_type": None,
        "sect_task_progress": 0,
        "sect_task_target": 2,
        "last_event_type": None,
        "last_drop_codes": [],
        "last_battle_won": False,
    }


def _choose_action(state: dict, stats: dict) -> str:
    if state.get("sect_task_status") == "active" and state.get("sect_task_type") in {"alchemy", "talisman", "crafting"}:
        recipe = _sect_life_skill_recipe(state["sect_task_type"])
        if recipe and state["mana"] >= _mana_cost(state["sect_task_type"], state) and _has_recipe_materials(state, recipe):
            return state["sect_task_type"]
    if state.get("sect_task_status") == "active" and state.get("sect_task_type") == "train_method" and state["method_equipped"]:
        return "practice_method"
    if state["cultivation"] >= state["cultivation_cap"]:
        return "breakthrough" if _can_attempt_breakthrough(state, stats) else "explore"
    if _needs_exploration(state):
        return "explore"
    if state["consecutive_train"] >= 1:
        return "explore"
    return "train"


def _needs_exploration(state: dict) -> bool:
    if not state["method_equipped"] or not state["artifact_equipped"]:
        return True
    target = _next_realm_name(state["realm"])
    requirement = BREAKTHROUGH_REQUIREMENTS.get(target or "")
    if requirement and state["explore_count"] < requirement.get("min_explore_count", 0):
        return state["cultivation"] >= int(state["cultivation_cap"] * 0.45)
    return False


def _mana_cost(action: str, state: dict | None = None) -> int:
    if action in {"alchemy", "talisman", "crafting"}:
        recipe = _sect_life_skill_recipe(action)
        return int(recipe["mana_cost"]) if recipe else 0
    cost = {"train": 12, "explore": 18, "breakthrough": 35, "practice_method": 10}.get(action, 0)
    if action == "explore" and state and state.get("swift_talisman_charges", 0) > 0:
        return max(1, cost - 6)
    return cost


def _auto_prepare(state: dict, stats: dict) -> None:
    _auto_life_skills(state, stats)
    if not state["method_equipped"] and state["items"]["low_method"] > 0:
        state["items"]["low_method"] -= 1
        state["method_equipped"] = True
        state["method_level"] = max(1, state["method_level"])
        stats["actions"]["learn_method"] += 1
        stats["actions"]["equip_method"] += 1
    artifact_code = _best_available_artifact(state)
    if not state["artifact_equipped"] and artifact_code:
        state["items"][artifact_code] -= 1
        state["artifact_equipped"] = True
        state["artifact_level"] = max(1, state["artifact_level"])
        stats["actions"]["equip_artifact"] += 1
    if state["method_equipped"] and state["method_level"] < 3 and state["mana"] >= 10:
        _simulate_practice_method(state, stats)
    if state["artifact_equipped"] and state["artifact_level"] < 3 and state["spirit_stones"] >= _artifact_upgrade_cost(state):
        _simulate_upgrade_artifact(state, stats)


def _auto_life_skills(state: dict, stats: dict) -> None:
    if state["mana"] >= 18 and state["items"]["scout_talisman"] > 0 and state.get("scout_talisman_charges", 0) <= 0:
        state["items"]["scout_talisman"] -= 1
        state["scout_talisman_charges"] = state.get("scout_talisman_charges", 0) + 1
        stats["actions"]["use_scout_talisman"] += 1
    if state["mana"] >= 18 and state["items"]["swift_talisman"] > 0 and state.get("swift_talisman_charges", 0) <= 0:
        state["items"]["swift_talisman"] -= 1
        state["swift_talisman_charges"] = state.get("swift_talisman_charges", 0) + 1
        stats["actions"]["use_swift_talisman"] += 1
    if stats["actions"].get("crafting", 0) < 2:
        _try_recipe(state, stats, "crafting", CRAFTING_RECIPES[0])
    if stats["actions"].get("talisman", 0) < max(1, state["explore_count"] // 30 + 1):
        _try_recipe(state, stats, "talisman", TALISMAN_RECIPES[0])
    if state["items"]["mana_pill"] <= 2 and stats["actions"].get("alchemy", 0) < max(1, state["explore_count"] // 40 + 1):
        _try_recipe(state, stats, "alchemy", ALCHEMY_RECIPES[0])


def _try_recipe(state: dict, stats: dict, skill_type: str, recipe: dict) -> bool:
    if state["mana"] < int(recipe["mana_cost"]):
        return False
    if not _has_recipe_materials(state, recipe):
        return False
    state["mana"] -= int(recipe["mana_cost"])
    for item in recipe.get("required_items", []):
        state["items"][item["code"]] -= int(item.get("quantity", 1))
    output = recipe["output_item_id"]
    quantity = int(recipe.get("output_count", 1))
    state["items"][output] += quantity
    stats["actions"][skill_type] += 1
    stats["life_skill_by_type"][skill_type] += 1
    stats["life_skill_outputs"][output] += quantity
    stats["life_skill_reward_value"] += _life_skill_output_value(output, quantity)
    return True


def _has_recipe_materials(state: dict, recipe: dict) -> bool:
    return all(state["items"][item["code"]] >= int(item.get("quantity", 1)) for item in recipe.get("required_items", []))


def _best_available_artifact(state: dict) -> str | None:
    for code in ("low_artifact", "crafted_low_sword", "gathering_artifact", "explore_puppet"):
        if state["items"][code] > 0:
            return code
    return None


def _life_skill_output_value(output: str, quantity: int) -> int:
    values = {
        "mana_pill": 18,
        "qi_powder": 12,
        "foundation_pill": 80,
        "scout_talisman": 10,
        "guard_talisman": 8,
        "swift_talisman": 8,
        "crafted_low_sword": 45,
        "gathering_artifact": 36,
        "explore_puppet": 42,
    }
    return values.get(output, 6) * quantity


def _simulate_life_skill_action(state: dict, stats: dict, skill_type: str) -> None:
    recipe = _sect_life_skill_recipe(skill_type)
    if not recipe or not _try_recipe(state, stats, skill_type, recipe):
        _simulate_explore(state, stats)
        return
    state["consecutive_train"] = 0
    _simulate_sect_task_progress(state, stats, skill_type)


def _sect_life_skill_recipe(skill_type: str) -> dict | None:
    if skill_type == "alchemy":
        return ALCHEMY_RECIPES[0]
    if skill_type == "talisman":
        return TALISMAN_RECIPES[0]
    if skill_type == "crafting":
        return CRAFTING_RECIPES[0]
    return None


def _simulate_sect_layer(state: dict, stats: dict, minute: int) -> None:
    if not state["sect_joined"] and _realm_rank(state["realm"]) >= _realm_rank("炼气三层"):
        state["sect_joined"] = True
        state["sect_contribution"] += 30
        stats["sect_contribution_gained"] += 30
        stats["sect_reputation_change"]["righteous"] += 10
        stats["sect_reputation_change"]["demonic"] -= 10
        stats["sect_reputation_change"]["ghost"] -= 10
        stats["sect_reputation_change"]["buddhist"] += 3
        stats["actions"]["join_sect"] += 1
    if not state["sect_joined"]:
        return
    if state["sect_task_status"] is None:
        state["sect_task_status"] = "active"
        state["sect_task_progress"] = 0
        state["sect_task_target"] = 2
        stats["actions"]["accept_sect_task"] += 1
        return
    if state["sect_task_status"] != "claimable":
        return
    state["sect_contribution"] += 20
    state["spirit_stones"] += 30
    state["sect_task_status"] = None
    state["sect_task_progress"] = 0
    stats["sect_tasks_completed"] += 1
    stats["sect_contribution_gained"] += 20
    stats["sect_reward_stones"] += 30
    stats["sect_reputation_change"]["righteous"] += 8
    stats["sect_reputation_change"]["demonic"] -= 8
    stats["sect_reputation_change"]["ghost"] -= 8
    stats["sect_reputation_change"]["buddhist"] += 2
    stats["total_spirit_stones_gained"] += 30
    stats["actions"]["complete_sect_task"] += 1


def _simulate_train(state: dict, stats: dict) -> None:
    state["mana"] -= 12
    speed = 1.0 + state["method_level"] * 0.04
    efficiency = [1.0, 0.8, 0.6, 0.4][state["consecutive_train"]] if state["consecutive_train"] < 4 else 0.2
    gain = max(1, int((random.randint(16, 28) * speed + state["max_mana"] * 0.03) * efficiency))
    state["cultivation"] = min(state["cultivation_cap"], state["cultivation"] + gain)
    stats["total_cultivation_gained"] += gain
    stats["actions"]["train"] += 1
    state["consecutive_train"] += 1


def _simulate_explore(state: dict, stats: dict) -> None:
    state["mana"] -= _mana_cost("explore", state)
    state["consecutive_train"] = 0
    state["explore_count"] += 1
    stats["actions"]["explore"] += 1
    _simulate_sect_task_progress(state, stats, "explore")
    luck = state["hidden_luck"] + (28 if state.get("scout_talisman_charges", 0) > 0 else 0)
    if random.random() <= min(LUCKY_EVENT_CONFIG["max_rate"], LUCKY_EVENT_CONFIG["base_rate"] + luck * LUCKY_EVENT_CONFIG["luck_factor"]):
        stats["actions"]["lucky"] += 1
        for _ in range(2):
            _grant_sim_drop(state, stats)
        return
    event_type = random.choices(["stones", "drop", "battle", "empty"], weights=[35, 35, 20, 10], k=1)[0]
    if event_type == "stones":
        stones = random.randint(18, 68) + state["hidden_luck"] // 5
        state["spirit_stones"] += stones
        stats["total_spirit_stones_gained"] += stones
    elif event_type in {"drop", "battle"}:
        rolls = 2 if event_type == "battle" else 1
        for _ in range(rolls):
            _grant_sim_drop(state, stats)


def _simulate_practice_method(state: dict, stats: dict) -> None:
    state["mana"] -= 10
    state["consecutive_train"] = 0
    gain = random.randint(*METHOD_PRACTICE["exp_gain"])
    state["method_exp"] += gain
    while state["method_level"] < METHOD_PRACTICE["max_level"] and state["method_exp"] >= METHOD_LEVEL_EXP.get(state["method_level"], 10**9):
        state["method_exp"] -= METHOD_LEVEL_EXP[state["method_level"]]
        state["method_level"] += 1
    state["max_mana"] = 100 + state["method_level"] * 12
    stats["actions"]["practice_method"] += 1
    _simulate_sect_task_progress(state, stats, "practice_method")


def _simulate_sect_task_progress(state: dict, stats: dict, action_type: str) -> None:
    if not state["sect_enabled"] or not state["sect_joined"] or state["sect_task_status"] != "active":
        return
    if action_type != "explore":
        return
    state["sect_task_progress"] = min(state["sect_task_target"], state["sect_task_progress"] + 1)
    stats["actions"]["sect_task_progress"] += 1
    if state["sect_task_progress"] >= state["sect_task_target"]:
        state["sect_task_status"] = "claimable"


def _simulate_upgrade_artifact(state: dict, stats: dict) -> None:
    cost = _artifact_upgrade_cost(state)
    state["spirit_stones"] -= cost
    rate = ARTIFACT_UPGRADE["success_rate_by_rarity"].get(state["artifact_rarity"], 0.88)
    if random.random() <= rate:
        state["artifact_level"] += 1
    stats["actions"]["upgrade_artifact"] += 1


def _can_attempt_breakthrough(state: dict, stats: dict) -> bool:
    target = _next_realm_name(state["realm"])
    if not target:
        return False
    requirement = BREAKTHROUGH_REQUIREMENTS.get(target)
    if not requirement:
        return True
    for item_code in requirement.get("required_items", []):
        if state["items"][item_code] <= 0:
            stats["bottleneck_reasons"][f"missing_{item_code}"] += 1
            return False
    if state["mana"] < requirement.get("min_mana", 0):
        stats["bottleneck_reasons"]["low_mana"] += 1
        return False
    if state["method_level"] < requirement.get("min_method_level", 0):
        stats["bottleneck_reasons"]["low_method_level"] += 1
        return False
    if state["explore_count"] < requirement.get("min_explore_count", 0):
        stats["bottleneck_reasons"]["low_explore_count"] += 1
        return False
    return True


def _simulate_breakthrough(state: dict, stats: dict) -> None:
    target = _next_realm_name(state["realm"])
    if not target:
        return
    state["mana"] -= 35
    state["consecutive_train"] = 0
    requirement = BREAKTHROUGH_REQUIREMENTS.get(target)
    if requirement:
        for item_code in requirement.get("required_items", []):
            state["items"][item_code] -= 1
    rate = _breakthrough_rate(state)
    stats["breakthrough_attempts"] += 1
    stats["actions"]["breakthrough"] += 1
    if random.random() <= rate:
        config = REALM_BY_NAME[target]
        state["realm"] = config.name
        state["realm_stage"] = config.stage
        state["cultivation"] = 0
        state["cultivation_cap"] = config.cultivation_cap
        state["max_mana"] = max(state["max_mana"], 100 + REALM_NAMES.index(target) * 20 + state["method_level"] * 12)
        state["mana"] = state["max_mana"]
        stats["breakthrough_successes"] += 1
        stats["breakthrough_failures_in_row"] = 0
    else:
        state["cultivation"] = int(state["cultivation_cap"] * 0.42)
        stats["breakthrough_failures_in_row"] += 1


def _recover_mana(state: dict, stats: dict, required_mana: int = 0) -> None:
    state["consecutive_train"] = 0
    missing_to_full = max(0, state["max_mana"] - state["mana"])
    missing_to_action = max(0, required_mana - state["mana"])
    if state["items"]["mana_pill"] > 0 and (missing_to_full >= 60 or missing_to_action > ACTION_CONFIGS["recover_mana_meditate"]["recover_mana"]):
        state["items"]["mana_pill"] -= 1
        amount = int(ACTION_CONFIGS["recover_mana_meditate"].get("recover_mana", 30))
        amount = max(amount, 120)
        before = state["mana"]
        state["mana"] = min(state["max_mana"], state["mana"] + amount)
        stats["mana_recovered"] += state["mana"] - before
        stats["actions"]["use_mana_pill"] += 1
        return
    stone_cost = int(ACTION_CONFIGS["recover_mana_stone"]["spirit_stone_cost"])
    stone_recover = int(ACTION_CONFIGS["recover_mana_stone"]["recover_mana"])
    if state["spirit_stones"] >= stone_cost and missing_to_full >= 45:
        state["spirit_stones"] -= stone_cost
        before = state["mana"]
        state["mana"] = min(state["max_mana"], state["mana"] + stone_recover)
        stats["mana_recovered"] += state["mana"] - before
        stats["spirit_stones_spent_on_mana"] += stone_cost
        stats["actions"]["recover_mana_stone"] += 1
        return
    before = state["mana"]
    state["mana"] = min(state["max_mana"], state["mana"] + int(ACTION_CONFIGS["recover_mana_meditate"]["recover_mana"]))
    stats["mana_recovered"] += state["mana"] - before
    stats["actions"]["recover_mana_meditate"] += 1


def _grant_sim_drop(state: dict, stats: dict) -> None:
    table = DROP_TABLES.get(_drop_table_key(state), DROP_TABLES["炼气"])
    drop = weighted_choice(table, lambda item: item["weight"])
    quantity_range = drop.get("quantity", [1, 1])
    quantity = random.randint(quantity_range[0], quantity_range[1])
    state["items"][drop["item"]] += quantity
    state.setdefault("last_drop_codes", []).extend([drop["item"]] * quantity)
    stats["drops"][drop["item"]] += quantity


def _breakthrough_rate(state: dict) -> float:
    base = REALM_BY_NAME[state["realm"]].breakthrough_rate
    base += state["hidden_luck"] * 0.0018
    base -= state["hidden_inner_demon"] * 0.0035
    base += state["method_level"] * 0.01
    return max(0.02, min(0.9, base))


def _next_realm_name(current: str) -> str | None:
    index = REALM_NAMES.index(current)
    if index >= len(REALM_NAMES) - 1:
        return None
    return REALM_NAMES[index + 1]


def _artifact_upgrade_cost(state: dict) -> int:
    return ARTIFACT_UPGRADE["base_spirit_stone_cost"] + max(0, state["artifact_level"] - 1) * ARTIFACT_UPGRADE["cost_growth"]


def _drop_table_key(state: dict) -> str:
    if state["realm_stage"] == "炼气" and qi_refining_level(state["realm"]) <= 6:
        return "炼气前期"
    return state["realm_stage"]


def _simulate_sect_layer(state: dict, stats: dict, minute: int) -> None:
    if not state["sect_joined"] and _realm_rank(state["realm"]) >= _realm_rank("炼气三层"):
        state["sect_joined"] = True
        state["sect_contribution"] += 30
        stats["sect_contribution_gained"] += 30
        stats["sect_reputation_change"]["righteous"] += 10
        stats["sect_reputation_change"]["demonic"] -= 10
        stats["sect_reputation_change"]["ghost"] -= 10
        stats["sect_reputation_change"]["buddhist"] += 3
        stats["actions"]["join_sect"] += 1
    if not state["sect_joined"]:
        return
    _simulate_sect_promotion_and_exchange(state, stats, minute)
    if state["sect_task_status"] is None:
        task = _choose_sect_task(state)
        if not task:
            return
        state["sect_task_status"] = "active"
        state["sect_task_code"] = task["code"]
        state["sect_task_type"] = task["type"]
        state["sect_task_progress"] = 0
        state["sect_task_target"] = int(task.get("target_count", task.get("target", 1)))
        stats["actions"]["accept_sect_task"] += 1
        return
    if state["sect_task_status"] != "claimable":
        return
    task = _task_by_code(state["sect_task_code"])
    multiplier, reasons = get_sect_reward_multiplier(
        task["code"],
        task["type"],
        state["sect_recent_task_codes"],
        state["sect_recent_task_types"],
        state["sect_completed_today"],
    )
    if multiplier <= 0:
        stats["warnings"].append("宗门日常上限触发，模拟停止领取宗门奖励")
        return
    reward = task.get("reward", {})
    contribution = scale_reward_value(int(reward.get("contribution", 0)), multiplier)
    stones = scale_reward_value(int(reward.get("spirit_stones", 0)), multiplier)
    state["sect_contribution"] += contribution
    state["spirit_stones"] += stones
    for item in reward.get("items", []):
        quantity = int(item.get("quantity", 1))
        state["items"][item["code"]] += quantity
        stats["drops"][item["code"]] += quantity
    state["sect_task_status"] = None
    state["sect_task_progress"] = 0
    state["sect_recent_task_codes"] = [task["code"], *state["sect_recent_task_codes"]][:8]
    state["sect_recent_task_types"] = [task["type"], *state["sect_recent_task_types"]][:8]
    state["sect_completed_today"] += 1
    stats["sect_tasks_completed"] += 1
    stats["sect_contribution_gained"] += contribution
    stats["sect_reward_stones"] += stones
    stats["sect_task_type_distribution"][task["type"]] += 1
    state["sect_task_type_counts"][task["type"]] += 1
    stats["sect_reward_by_type"][task["type"]] += stones
    for reason in reasons:
        stats["sect_decay_reasons"][reason] += 1
    reputation = scale_reward_value(int(task.get("reputation", 0)), multiplier)
    stats["sect_reputation_change"]["righteous"] += reputation
    stats["sect_reputation_change"]["demonic"] -= reputation
    stats["sect_reputation_change"]["ghost"] -= reputation
    stats["sect_reputation_change"]["buddhist"] += max(1, reputation // 3)
    stats["total_spirit_stones_gained"] += stones
    stats["actions"]["complete_sect_task"] += 1


def _simulate_explore(state: dict, stats: dict) -> None:
    state["mana"] -= _mana_cost("explore", state)
    state["consecutive_train"] = 0
    state["explore_count"] += 1
    state["last_event_type"] = None
    state["last_drop_codes"] = []
    state["last_battle_won"] = False
    stats["actions"]["explore"] += 1
    luck = state["hidden_luck"] + (28 if state.get("scout_talisman_charges", 0) > 0 else 0)
    if random.random() <= min(LUCKY_EVENT_CONFIG["max_rate"], LUCKY_EVENT_CONFIG["base_rate"] + luck * LUCKY_EVENT_CONFIG["luck_factor"]):
        state["last_event_type"] = random.choice(["hidden_cave", "rare_item", "hidden_opportunity"])
        stats["actions"]["lucky"] += 1
        for _ in range(2):
            _grant_sim_drop(state, stats)
        _simulate_sect_task_progress(state, stats, "explore")
        _consume_sim_explore_charges(state)
        return
    event_type = random.choices(["stones", "drop", "battle", "empty"], weights=[35, 35, 20, 10], k=1)[0]
    state["last_event_type"] = "reward_spirit_stones" if event_type == "stones" else event_type
    if event_type == "stones":
        stones = random.randint(18, 68) + luck // 5
        state["spirit_stones"] += stones
        stats["total_spirit_stones_gained"] += stones
    elif event_type in {"drop", "battle"}:
        state["last_battle_won"] = event_type == "battle"
        rolls = 2 if event_type == "battle" else 1
        for _ in range(rolls):
            _grant_sim_drop(state, stats)
    _simulate_sect_task_progress(state, stats, "explore")
    _consume_sim_explore_charges(state)


def _simulate_sect_task_progress(state: dict, stats: dict, action_type: str) -> None:
    if not state["sect_enabled"] or not state["sect_joined"] or state["sect_task_status"] != "active":
        return
    task = _task_by_code(state["sect_task_code"])
    amount = _sim_progress_amount(task, action_type, state)
    if amount <= 0:
        return
    state["sect_task_progress"] = min(state["sect_task_target"], state["sect_task_progress"] + amount)
    stats["actions"]["sect_task_progress"] += 1
    if state["sect_task_progress"] >= state["sect_task_target"]:
        state["sect_task_status"] = "claimable"


def _sim_progress_amount(task: dict, action_type: str, state: dict) -> int:
    if action_type != task.get("target_action"):
        return 0
    task_type = task["type"]
    if task_type == "patrol":
        return 1
    if task_type == "train_method":
        return 1
    if task_type == "gather_material":
        allowed = set(task.get("target_item_codes", []))
        return sum(1 for code in state.get("last_drop_codes", []) if code in allowed)
    if task_type == "hunt_beast":
        return 1 if state.get("last_event_type") == "battle" and state.get("last_battle_won") else 0
    if task_type in {"explore_secret", "faction_conflict"}:
        return 1 if state.get("last_event_type") in set(task.get("target_event_types", [])) else 0
    if task_type in {"alchemy", "talisman", "crafting"}:
        return 1
    return 0


def _consume_sim_explore_charges(state: dict) -> None:
    for key in ("scout_talisman_charges", "guard_talisman_charges", "swift_talisman_charges"):
        if state.get(key, 0) > 0:
            state[key] -= 1


def _choose_sect_task(state: dict) -> dict | None:
    available = [task for task in SECT_TASKS if _position_rank(state["sect_position"]) >= _position_rank(task.get("required_position", "outer_disciple"))]
    high_allowed = state["sect_completed_today"] > 0 and state["sect_completed_today"] % 6 == 5
    if not high_allowed:
        available = [task for task in available if task["type"] not in {"explore_secret", "faction_conflict"}]
    else:
        available = [task for task in available if task["type"] != "explore_secret"]
    if not state["method_equipped"]:
        available = [task for task in available if task["type"] != "train_method"]
    if not available:
        return None
    preferred = ["gather_material", "hunt_beast", "patrol", "train_method", "explore_secret", "faction_conflict"]
    recent_window = set(state["sect_recent_task_types"][:2])
    preferred_rank = {task_type: index for index, task_type in enumerate(preferred)}
    fresh = [task for task in available if task["type"] not in recent_window]
    pool = fresh or available
    pool.sort(key=lambda task: (state["sect_task_type_counts"].get(task["type"], 0), preferred_rank.get(task["type"], 99)))
    return pool[0]


def _simulate_sect_promotion_and_exchange(state: dict, stats: dict, minute: int) -> None:
    if state["sect_position"] == "outer_disciple" and state["sect_contribution"] >= 100 and _realm_rank(state["realm"]) >= _realm_rank("炼气五层"):
        state["sect_position"] = "inner_disciple"
        stats["actions"]["promote_sect_position"] += 1
    elif state["sect_position"] == "inner_disciple" and state["sect_contribution"] >= 260 and _realm_rank(state["realm"]) >= _realm_rank("炼气八层"):
        state["sect_position"] = "elite_disciple"
        stats["actions"]["promote_sect_position"] += 1
    if minute and minute % 90 == 0 and state["sect_contribution"] >= 160 and state["items"]["foundation_pill"] == 0:
        state["sect_contribution"] -= 160
        state["items"]["foundation_pill"] += 1
        stats["actions"]["exchange_sect_reward"] += 1


def _task_by_code(code: str | None) -> dict:
    return next((task for task in SECT_TASKS if task["code"] == code), SECT_TASKS[0])


def _position_rank(position: str) -> int:
    order = ["outer_disciple", "inner_disciple", "elite_disciple", "deacon", "elder", "grand_elder", "leader"]
    return order.index(position) if position in order else 0


def _build_result(hours: float, state: dict, stats: dict, minutes: int, with_sect: bool = False) -> dict:
    warnings = _build_warnings(state, stats, minutes)
    attempts = max(1, stats["breakthrough_attempts"])
    growth_actions = {"explore", "train", "practice_method", "breakthrough"}
    counted_actions = sum(count for action, count in stats["actions"].items() if action in growth_actions)
    explore_ratio = stats["actions"].get("explore", 0) / max(1, counted_actions)
    train_ratio = stats["actions"].get("train", 0) / max(1, counted_actions)
    sect_reward_ratio = stats["sect_reward_stones"] / max(1, stats["total_spirit_stones_gained"])
    life_skill_actions = sum(stats["life_skill_by_type"].values())
    total_actions = sum(stats["actions"].values())
    life_skill_reward_ratio = stats["life_skill_reward_value"] / max(
        1,
        stats["life_skill_reward_value"] + stats["total_spirit_stones_gained"] + int(stats["total_cultivation_gained"] * 0.1),
    )
    sect_distribution = dict(stats["sect_task_type_distribution"])
    max_task_type_ratio = max(sect_distribution.values(), default=0) / max(1, stats["sect_tasks_completed"])
    return {
        "time": f"{hours:g}h",
        "realm": state["realm"],
        "cultivation": state["cultivation"],
        "cultivation_cap": state["cultivation_cap"],
        "progress_ratio": round(state["cultivation"] / max(1, state["cultivation_cap"]), 4),
        "spirit_stones": state["spirit_stones"],
        "items": dict(+state["items"]),
        "method_level": state["method_level"],
        "artifact_level": state["artifact_level"],
        "breakthrough_attempts": stats["breakthrough_attempts"],
        "success_rate": round(stats["breakthrough_successes"] / attempts, 4),
        "drop_stats": dict(stats["drops"]),
        "action_counts": dict(stats["actions"]),
        "explore_ratio": round(explore_ratio, 4),
        "train_ratio": round(train_ratio, 4),
        "explore_count": state["explore_count"],
        "average_spirit_stones_per_hour": round(stats["total_spirit_stones_gained"] / max(0.1, hours), 2),
        "average_cultivation_per_hour": round(stats["total_cultivation_gained"] / max(0.1, hours), 2),
        "mana_blocked_ratio": round(stats["mana_blocked_minutes"] / minutes, 4),
        "mana_recovered": stats["mana_recovered"],
        "spirit_stones_spent_on_mana": stats["spirit_stones_spent_on_mana"],
        "bag_fill_ratio_peak": round(stats["bag_slots_used_peak"] / 81, 4),
        "bottleneck_reasons": dict(stats["bottleneck_reasons"]),
        "warnings": warnings,
        "life_skill_action_ratio": round(life_skill_actions / max(1, total_actions), 4),
        "life_skill_reward_ratio": round(life_skill_reward_ratio, 4),
        "life_skill_by_type": dict(stats["life_skill_by_type"]),
        "life_skill_outputs": dict(stats["life_skill_outputs"]),
        "life_skill_only_growth_risk": bool(life_skill_actions and stats["actions"].get("explore", 0) / max(1, life_skill_actions) < 1.5),
        "with_sect": with_sect,
        "sect_joined": state["sect_joined"],
        "sect_tasks_completed": stats["sect_tasks_completed"],
        "sect_contribution": state["sect_contribution"],
        "sect_contribution_gained": stats["sect_contribution_gained"],
        "sect_reward_stones": stats["sect_reward_stones"],
        "sect_reputation_change": dict(stats["sect_reputation_change"]),
        "sect_task_type_distribution": sect_distribution,
        "sect_reward_by_type": dict(stats["sect_reward_by_type"]),
        "sect_decay_reasons": dict(stats["sect_decay_reasons"]),
        "sect_reward_share_by_type": {
            task_type: round(value / max(1, stats["sect_reward_stones"]), 4)
            for task_type, value in stats["sect_reward_by_type"].items()
        },
        "sect_max_task_type_ratio": round(max_task_type_ratio, 4),
        "biased_task_type": max(sect_distribution, key=sect_distribution.get) if max_task_type_ratio > 0.6 else None,
        "sect_reward_ratio": round(sect_reward_ratio, 4),
        "simulation_result_file": str(SIMULATION_RESULT_PATH),
    }


def _build_warnings(state: dict, stats: dict, minutes: int) -> list[str]:
    warnings: list[str] = []
    if minutes >= 60 and stats["actions"].get("explore", 0) == 0:
        warnings.append("严格修炼策略 1 小时内没有探索收益，前期需要任务引导")
    if stats["actions"].get("explore", 0) > 0 and not stats["drops"]:
        warnings.append("探索掉落过低")
    growth_actions = {"explore", "train", "practice_method", "breakthrough"}
    core_total = sum(count for action, count in stats["actions"].items() if action in growth_actions)
    if minutes >= 60 and stats["actions"].get("explore", 0) / max(1, core_total) < 0.3:
        warnings.append("探索占比低于 30%，仍可能偏向单一修炼")
    if state["realm"] == "炼气十二层" and state["items"].get("foundation_pill", 0) <= 0:
        warnings.append("筑基丹掉率过低")
    if stats["breakthrough_failures_in_row"] >= 5:
        warnings.append("连续 5 次突破失败，可能突破卡死")
    if stats["mana_blocked_minutes"] / max(1, minutes) > 0.3:
        warnings.append("法力恢复不足")
    life_skill_actions = sum(stats.get("life_skill_by_type", {}).values())
    if life_skill_actions and stats["actions"].get("explore", 0) / max(1, life_skill_actions) < 1.5:
        warnings.append("生活技能占比过高，可能压过探索主循环")
    if life_skill_actions and stats.get("life_skill_reward_value", 0) / max(1, stats.get("life_skill_reward_value", 0) + stats.get("total_spirit_stones_gained", 0)) > 0.45:
        warnings.append("生活技能收益占比过高，需要提高材料消耗或降低产出")
    if stats["bag_slots_used_peak"] / 81 > 0.8:
        warnings.append("背包接近溢出")
    if stats["bottleneck_reasons"].get("missing_foundation_pill", 0) > 20:
        warnings.append("筑基丹掉率过低")
    if stats.get("sect_reward_stones", 0) / max(1, stats.get("total_spirit_stones_gained", 0)) > 0.45:
        warnings.append("宗门任务灵石奖励占比过高，可能出现只刷宗门任务")
    sect_completed = stats.get("sect_tasks_completed", 0)
    if sect_completed:
        max_type_count = max(stats.get("sect_task_type_distribution", {}).values(), default=0)
        if max_type_count / max(1, sect_completed) > 0.6:
            warnings.append("宗门任务类型偏科，可能出现单一任务刷法")
    if stats.get("sect_reward_stones", 0) / max(1, stats.get("total_spirit_stones_gained", 0)) > 0.35:
        warnings.append("宗门奖励占比超过 35%，需要继续压低宗门直接收益")
    return sorted(set(warnings))


def _realm_rank(name: str) -> int:
    return REALM_NAMES.index(name) if name in REALM_NAMES else 0
