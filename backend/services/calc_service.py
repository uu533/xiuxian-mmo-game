from backend.configs.actions import ACTION_CONFIGS
from backend.configs.formulas import (
    BASE_HP_BY_STAGE,
    BREAKTHROUGH_INNER_DEMON_FACTOR,
    BREAKTHROUGH_LUCK_FACTOR,
)
from backend.models import Character
from backend.services.realm_service import current_realm_config, normalize_realm, qi_refining_level
from backend.services.spiritual_root_service import root_rate


def get_base_attack_by_realm(character: Character) -> int:
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

    index = REALM_NAMES.index(realm_name)
    nascent_index = REALM_NAMES.index("元婴初期")
    return 500 + (index - nascent_index) * 240


def get_base_defense_by_realm(character: Character) -> int:
    return get_base_attack_by_realm(character)


def get_max_mana(character: Character) -> int:
    return max(100, get_base_attack_by_realm(character) * 12 + _method_mana_bonus(character) + _artifact_mana_bonus(character))


def get_max_hp(character: Character) -> int:
    normalize_realm(character)
    base = BASE_HP_BY_STAGE.get(character.realm_stage, 100)
    return base + get_base_defense_by_realm(character) * 2


def get_cultivation_speed(character: Character) -> float:
    return root_rate(character.spiritual_root)


def get_breakthrough_rate(character: Character) -> float:
    config = current_realm_config(character)
    rate = config.breakthrough_rate
    rate += character.hidden_luck * BREAKTHROUGH_LUCK_FACTOR
    rate -= character.hidden_inner_demon * BREAKTHROUGH_INNER_DEMON_FACTOR
    if character.realm == "结丹后期":
        rate -= 0.04
    if character.realm.startswith("元婴") or character.realm.startswith("化神"):
        rate -= 0.03
    return max(0.02, min(0.9, rate))


def get_final_attack(character: Character) -> int:
    return get_base_attack_by_realm(character) + _method_attack_bonus(character) + _artifact_attack_bonus(character)


def get_final_defense(character: Character) -> int:
    return get_base_defense_by_realm(character) + _method_defense_bonus(character) + _artifact_defense_bonus(character)


def get_action_mana_cost(character: Character, action_type: str) -> int:
    _ = character
    return int(ACTION_CONFIGS.get(action_type, {}).get("mana_cost", 0))


def apply_item_effects(character: Character, effects: dict) -> dict:
    applied: dict = {}
    if effects.get("recover_mana"):
        before = character.mana
        character.mana = min(character.max_mana, character.mana + int(effects["recover_mana"]))
        applied["recover_mana"] = character.mana - before
    if effects.get("cultivation"):
        gain = int(effects["cultivation"])
        character.cultivation = min(character.cultivation_cap, character.cultivation + gain)
        applied["cultivation"] = gain
    return applied


def sync_base_and_caps(character: Character) -> None:
    normalize_realm(character)
    character.base_attack = get_base_attack_by_realm(character)
    character.base_defense = get_base_defense_by_realm(character)
    character.max_mana = get_max_mana(character)
    character.max_hp = get_max_hp(character)
    character.mana = min(character.mana, character.max_mana)
    character.hp = min(character.hp, character.max_hp)


def derived_stats(character: Character) -> dict:
    sync_base_and_caps(character)
    return {
        "final_attack": get_final_attack(character),
        "final_defense": get_final_defense(character),
        "final_mana": character.max_mana,
        "cultivation_speed": get_cultivation_speed(character),
        "breakthrough_bonus": round(get_breakthrough_rate(character) - current_realm_config(character).breakthrough_rate, 4),
    }


def _method_attack_bonus(character: Character) -> int:
    return sum(method.level * 2 for method in character.methods if method.equipped)


def _method_defense_bonus(character: Character) -> int:
    return sum(method.level for method in character.methods if method.equipped)


def _method_mana_bonus(character: Character) -> int:
    return sum(method.level * 20 for method in character.methods if method.equipped)


def _artifact_attack_bonus(character: Character) -> int:
    return sum((artifact.item_instance.level if artifact.item_instance else 1) * 5 for artifact in character.artifacts if artifact.equipped)


def _artifact_defense_bonus(character: Character) -> int:
    return sum((artifact.item_instance.level if artifact.item_instance else 1) * 3 for artifact in character.artifacts if artifact.equipped)


def _artifact_mana_bonus(character: Character) -> int:
    return sum((artifact.item_instance.level if artifact.item_instance else 1) * 10 for artifact in character.artifacts if artifact.equipped)
