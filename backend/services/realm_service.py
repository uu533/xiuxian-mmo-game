from backend.configs.realms import LEGACY_REALM_MAP, REALM_BY_NAME, REALM_NAMES, REALMS, STARTING_REALM, TITLE_UNLOCKS
from backend.models import Character


def normalize_realm(character: Character) -> None:
    if character.realm in LEGACY_REALM_MAP:
        character.realm = LEGACY_REALM_MAP[character.realm]
    if character.realm not in REALM_BY_NAME:
        character.realm = STARTING_REALM.name
    config = current_realm_config(character)
    character.realm_stage = config.stage
    if character.cultivation_cap < config.cultivation_cap:
        character.cultivation_cap = config.cultivation_cap
    character.lifespan = get_lifespan_by_realm(character.realm)


def current_realm_config(character: Character):
    return REALM_BY_NAME.get(character.realm, STARTING_REALM)


def current_index(character: Character) -> int:
    normalize_realm(character)
    return REALM_NAMES.index(character.realm)


def next_realm_config(character: Character):
    index = current_index(character)
    if index >= len(REALMS) - 1:
        return None
    return REALMS[index + 1]


def get_realm_stage(realm_name: str) -> str:
    return REALM_BY_NAME.get(realm_name, STARTING_REALM).stage


def is_major_breakthrough(from_name: str, to_name: str) -> bool:
    return get_realm_stage(from_name) != get_realm_stage(to_name)


def unlocked_titles(realm_name: str) -> list[str]:
    stage = get_realm_stage(realm_name)
    return TITLE_UNLOCKS.get(stage, TITLE_UNLOCKS["炼气"])


def normalize_title(character: Character) -> None:
    normalize_realm(character)
    available = unlocked_titles(character.realm)
    if not character.title or character.title not in available:
        character.title = available[0]


def get_lifespan_by_realm(realm_name: str) -> int:
    if realm_name in {"炼气一层", "炼气二层", "炼气三层", "炼气四层", "炼气五层"}:
        return 100
    if realm_name.startswith("炼气"):
        return 130
    if realm_name.startswith("筑基"):
        return 200
    if realm_name.startswith("结丹"):
        return 500
    if realm_name.startswith("元婴"):
        return 1000
    return 3000


def qi_refining_level(realm_name: str) -> int:
    level_text = realm_name.removeprefix("炼气").removesuffix("层")
    mapping = {
        "一": 1,
        "二": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "六": 6,
        "七": 7,
        "八": 8,
        "九": 9,
        "十": 10,
        "十一": 11,
        "十二": 12,
    }
    return mapping.get(level_text, 1)
