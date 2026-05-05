from backend.models import Character
from backend.services.realm_service import current_index, normalize_realm


DEFAULT_SECT_BRANCH = "青云峰"


def sect_position(character: Character) -> str:
    normalize_realm(character)
    if not character.sect_name:
        return "散修"

    realm = character.realm
    branch = character.sect_branch or DEFAULT_SECT_BRANCH

    if realm.startswith("炼气"):
        level_text = realm.removeprefix("炼气").removesuffix("层")
        level = chinese_level_to_int(level_text)
        if level <= 4:
            return "外门弟子"
        if level <= 9:
            return "内门弟子"
        return "亲传弟子"

    if realm == "筑基初期":
        return "外门执事"
    if realm == "筑基中期":
        return "内门执事"
    if realm == "筑基后期":
        return "副掌门"

    if realm == "结丹初期":
        return f"{branch}长老"
    if realm == "结丹中期":
        ratio = cultivation_ratio(character)
        return "普通长老" if ratio < 0.5 else "高阶长老"
    if realm == "结丹后期":
        ratio = cultivation_ratio(character)
        if ratio < 0.34:
            return "核心长老"
        if ratio < 0.67:
            return "名义长老"
        return "供奉长老"

    if realm == "元婴初期":
        return "太上长老"
    if realm == "元婴中期":
        return "大长老"
    if realm == "元婴后期":
        return "宗门领袖"

    if realm.startswith("化神"):
        return "宗门领袖"

    return "门人"


def identity_status(character: Character) -> str:
    if not character.sect_name:
        return "散修"
    return f"{character.sect_name} · {sect_position(character)}"


def cultivation_ratio(character: Character) -> float:
    return max(0.0, min(1.0, character.cultivation / max(1, character.cultivation_cap)))


def chinese_level_to_int(text: str) -> int:
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
    return mapping.get(text, max(0, current_index_from_realm_text(text)))


def current_index_from_realm_text(text: str) -> int:
    try:
        return int(text)
    except ValueError:
        return 1
