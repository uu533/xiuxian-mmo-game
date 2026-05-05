from backend.models import Character
from backend.services.realm_service import normalize_realm, qi_refining_level


def derive_sect_position(character: Character) -> str:
    normalize_realm(character)
    if not character.sect_id:
        return "散修"
    if character.sect_position and character.sect_position != "散修":
        return character.sect_position

    realm = character.realm
    if realm.startswith("炼气"):
        level = qi_refining_level(realm)
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
        return "长老"
    if realm == "结丹中期":
        return "高阶长老"
    if realm == "结丹后期":
        return "核心长老"
    if realm == "元婴初期":
        return "太上长老"
    if realm == "元婴中期":
        return "大长老"
    return "宗门领袖"


def identity_status(character: Character) -> str:
    if not character.sect_id or not character.sect:
        return "散修"
    return f"{character.sect.name} · {derive_sect_position(character)}"
