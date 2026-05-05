import json
import random
from collections import Counter
from pathlib import Path

from backend.configs.artifacts import ARTIFACT_UPGRADE
from backend.configs.breakthrough_requirements import BREAKTHROUGH_REQUIREMENTS
from backend.configs.drop_tables import DROP_TABLES
from backend.configs.methods import METHOD_LEVEL_EXP, METHOD_PRACTICE
from backend.configs.opportunities import LUCKY_EVENT_CONFIG
from backend.configs.realms import REALM_BY_NAME, REALM_NAMES, STARTING_REALM
from backend.database import BASE_DIR
from backend.services.realm_service import qi_refining_level
from backend.utils.random_utils import weighted_choice

SIMULATION_RESULT_PATH = BASE_DIR / "simulation_result.json"


def run_simulation(hours: float = 1) -> dict:
    minutes = max(1, int(hours * 60))
    state = _new_state()
    stats = {
        "actions": Counter(),
        "drops": Counter(),
        "warnings": [],
        "breakthrough_attempts": 0,
        "breakthrough_successes": 0,
        "breakthrough_failures_in_row": 0,
        "mana_blocked_minutes": 0,
        "bag_slots_used_peak": 0,
        "total_spirit_stones_gained": 0,
        "total_cultivation_gained": 0,
        "bottleneck_reasons": Counter(),
    }

    for _minute in range(minutes):
        _auto_prepare(state, stats)
        action = _choose_action(state, stats)
        if state["mana"] < _mana_cost(action):
            stats["mana_blocked_minutes"] += 1
            _recover_mana(state)
            stats["actions"]["recover_mana_meditate"] += 1
            continue
        if action == "train":
            _simulate_train(state, stats)
        elif action == "breakthrough":
            _simulate_breakthrough(state, stats)
        else:
            _simulate_explore(state, stats)
        stats["bag_slots_used_peak"] = max(stats["bag_slots_used_peak"], len(state["items"]))

    result = _build_result(hours, state, stats, minutes)
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
        "artifact_rarity": "白",
        "consecutive_train": 0,
        "explore_count": 0,
    }


def _choose_action(state: dict, stats: dict) -> str:
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


def _mana_cost(action: str) -> int:
    return {"train": 12, "explore": 18, "breakthrough": 35}.get(action, 0)


def _auto_prepare(state: dict, stats: dict) -> None:
    if not state["method_equipped"] and state["items"]["low_method"] > 0:
        state["items"]["low_method"] -= 1
        state["method_equipped"] = True
        state["method_level"] = max(1, state["method_level"])
        stats["actions"]["learn_method"] += 1
        stats["actions"]["equip_method"] += 1
    if not state["artifact_equipped"] and state["items"]["low_artifact"] > 0:
        state["items"]["low_artifact"] -= 1
        state["artifact_equipped"] = True
        state["artifact_level"] = max(1, state["artifact_level"])
        stats["actions"]["equip_artifact"] += 1
    if state["method_equipped"] and state["method_level"] < 3 and state["mana"] >= 10:
        _simulate_practice_method(state, stats)
    if state["artifact_equipped"] and state["artifact_level"] < 3 and state["spirit_stones"] >= _artifact_upgrade_cost(state):
        _simulate_upgrade_artifact(state, stats)


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
    state["mana"] -= 18
    state["consecutive_train"] = 0
    state["explore_count"] += 1
    stats["actions"]["explore"] += 1
    if random.random() <= min(LUCKY_EVENT_CONFIG["max_rate"], LUCKY_EVENT_CONFIG["base_rate"] + state["hidden_luck"] * LUCKY_EVENT_CONFIG["luck_factor"]):
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


def _recover_mana(state: dict) -> None:
    state["consecutive_train"] = 0
    state["mana"] = min(state["max_mana"], state["mana"] + 30)


def _grant_sim_drop(state: dict, stats: dict) -> None:
    table = DROP_TABLES.get(_drop_table_key(state), DROP_TABLES["炼气"])
    drop = weighted_choice(table, lambda item: item["weight"])
    quantity_range = drop.get("quantity", [1, 1])
    quantity = random.randint(quantity_range[0], quantity_range[1])
    state["items"][drop["item"]] += quantity
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


def _build_result(hours: float, state: dict, stats: dict, minutes: int) -> dict:
    warnings = _build_warnings(state, stats, minutes)
    attempts = max(1, stats["breakthrough_attempts"])
    counted_actions = sum(stats["actions"].values())
    explore_ratio = stats["actions"].get("explore", 0) / max(1, counted_actions)
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
        "explore_count": state["explore_count"],
        "average_spirit_stones_per_hour": round(stats["total_spirit_stones_gained"] / max(0.1, hours), 2),
        "average_cultivation_per_hour": round(stats["total_cultivation_gained"] / max(0.1, hours), 2),
        "mana_blocked_ratio": round(stats["mana_blocked_minutes"] / minutes, 4),
        "bag_fill_ratio_peak": round(stats["bag_slots_used_peak"] / 81, 4),
        "bottleneck_reasons": dict(stats["bottleneck_reasons"]),
        "warnings": warnings,
        "simulation_result_file": str(SIMULATION_RESULT_PATH),
    }


def _build_warnings(state: dict, stats: dict, minutes: int) -> list[str]:
    warnings: list[str] = []
    if minutes >= 60 and stats["actions"].get("explore", 0) == 0:
        warnings.append("严格修炼策略 1 小时内没有探索收益，前期需要任务引导")
    if stats["actions"].get("explore", 0) > 0 and not stats["drops"]:
        warnings.append("探索掉落过低")
    if minutes >= 60 and stats["actions"].get("explore", 0) / max(1, sum(stats["actions"].values())) < 0.3:
        warnings.append("探索占比低于 30%，仍可能偏向单一修炼")
    if state["realm"] == "炼气十二层" and state["items"].get("foundation_pill", 0) <= 0:
        warnings.append("筑基丹掉率过低")
    if stats["breakthrough_failures_in_row"] >= 5:
        warnings.append("连续 5 次突破失败，可能突破卡死")
    if stats["mana_blocked_minutes"] / max(1, minutes) > 0.3:
        warnings.append("法力恢复不足")
    if stats["bag_slots_used_peak"] / 81 > 0.8:
        warnings.append("背包接近溢出")
    if stats["bottleneck_reasons"].get("missing_foundation_pill", 0) > 20:
        warnings.append("筑基丹掉率过低")
    return sorted(set(warnings))
