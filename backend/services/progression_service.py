import random

from sqlalchemy.orm import Session

from backend.configs.artifacts import ARTIFACT_UPGRADE
from backend.configs.methods import METHOD_LEVEL_EXP, METHOD_PRACTICE
from backend.models import Character, CharacterArtifact, CharacterMethod
from backend.services.inventory_service import get_main_slot, put_instance_into_main_bag, take_slot_item


def methods_payload(character: Character) -> list[dict]:
    return [
        {
            "id": method.id,
            "method_code": method.method_code,
            "name": method.item_instance.template.name if method.item_instance else method.method_code,
            "level": method.level,
            "exp": method.exp,
            "next_exp": METHOD_LEVEL_EXP.get(method.level),
            "equipped": method.equipped,
            "effects": method.item_instance.template.effects_json if method.item_instance else {},
        }
        for method in sorted(character.methods, key=lambda item: item.id)
    ]


def artifacts_payload(character: Character) -> list[dict]:
    return [
        {
            "id": artifact.id,
            "slot_type": artifact.slot_type,
            "equipped": artifact.equipped,
            "item_instance_id": artifact.item_instance_id,
            "code": artifact.item_instance.template.code if artifact.item_instance else None,
            "name": artifact.item_instance.template.name if artifact.item_instance else None,
            "level": artifact.item_instance.level if artifact.item_instance else 1,
            "rarity": artifact.item_instance.rarity if artifact.item_instance else "白",
            "durability": artifact.item_instance.durability if artifact.item_instance else 100,
            "effects": artifact.item_instance.template.effects_json if artifact.item_instance else {},
        }
        for artifact in sorted(character.artifacts, key=lambda item: item.id)
    ]


def learn_method_from_slot(db: Session, character: Character, slot_index: int) -> tuple[bool, str, dict]:
    slot = get_main_slot(db, character, slot_index)
    template = slot.item_template if slot else None
    if not slot or not template:
        return False, "该格子没有可学习的功法。", {"reason": "invalid_slot"}
    if template.type != "cultivation_method":
        return False, f"{template.name} 不是功法，无法学习。", {"reason": "not_method", "item": template.code}
    if any(method.method_code == template.code for method in character.methods):
        return False, f"你已经学过「{template.name}」。", {"reason": "already_learned", "method": template.code}
    ok, _message, template, instance = take_slot_item(db, character, slot_index, 1)
    method = CharacterMethod(character_id=character.id, item_instance_id=instance.id if instance else None, method_code=template.code)
    db.add(method)
    db.flush()
    return True, f"你参悟玉简，学会了「{template.name}」。", {"method_id": method.id, "method_code": template.code}


def equip_method(db: Session, character: Character, method_id: int) -> tuple[bool, str, dict]:
    method = db.query(CharacterMethod).filter(CharacterMethod.character_id == character.id, CharacterMethod.id == method_id).first()
    if not method:
        return False, "未找到该功法。", {"reason": "method_not_found"}
    for value in character.methods:
        value.equipped = False
    method.equipped = True
    db.flush()
    name = method.item_instance.template.name if method.item_instance else method.method_code
    return True, f"你将「{name}」设为主修功法。", {"method_id": method.id, "method_code": method.method_code}


def practice_method(db: Session, character: Character, method_id: int | None = None) -> tuple[bool, str, dict]:
    method_id = int(method_id) if method_id else None
    method = _target_method(character, method_id)
    if not method:
        return False, "请先装备一门主修功法。", {"reason": "no_method"}
    if method.level >= METHOD_PRACTICE["max_level"]:
        return False, "该功法已修炼至当前版本上限。", {"reason": "method_max_level"}
    gain = random.randint(*METHOD_PRACTICE["exp_gain"])
    method.exp += gain
    leveled = False
    while method.level < METHOD_PRACTICE["max_level"] and method.exp >= METHOD_LEVEL_EXP.get(method.level, 10**9):
        method.exp -= METHOD_LEVEL_EXP[method.level]
        method.level += 1
        leveled = True
    db.flush()
    name = method.item_instance.template.name if method.item_instance else method.method_code
    message = f"你修习「{name}」，功法经验增加 {gain}。"
    if leveled:
        message += f" 功法提升至 {method.level} 层。"
    return True, message, {"method_id": method.id, "exp_gain": gain, "level": method.level, "leveled": leveled}


def equip_artifact_from_slot(db: Session, character: Character, slot_index: int, slot_type: str = "main") -> tuple[bool, str, dict]:
    slot = get_main_slot(db, character, slot_index)
    template = slot.item_template if slot else None
    instance = slot.item_instance if slot else None
    if not slot or not template or not instance:
        return False, "该格子没有可装备的法宝。", {"reason": "invalid_slot"}
    if template.type != "magic_artifact":
        return False, f"{template.name} 不是法宝，无法装备。", {"reason": "not_artifact", "item": template.code}
    ok, _message, template, instance = take_slot_item(db, character, slot_index, 1)
    for artifact in character.artifacts:
        if artifact.slot_type == slot_type:
            artifact.equipped = False
    artifact = CharacterArtifact(character_id=character.id, item_instance_id=instance.id, slot_type=slot_type, equipped=True)
    db.add(artifact)
    db.flush()
    return True, f"你装备了{instance.rarity}品法宝「{template.name}」。", {"artifact_id": artifact.id, "artifact_code": template.code, "rarity": instance.rarity}


def unequip_artifact(db: Session, character: Character, artifact_id: int) -> tuple[bool, str, dict]:
    artifact = db.query(CharacterArtifact).filter(CharacterArtifact.character_id == character.id, CharacterArtifact.id == artifact_id).first()
    if not artifact or not artifact.item_instance:
        return False, "未找到该法宝。", {"reason": "artifact_not_found"}
    instance = artifact.item_instance
    ok, message, reward = put_instance_into_main_bag(db, character, instance)
    if not ok:
        return False, message, {"reason": "bag_full"}
    artifact.equipped = False
    db.delete(artifact)
    db.flush()
    return True, f"你卸下法宝，{message}", {"artifact_id": artifact_id, "returned": reward}


def upgrade_artifact(db: Session, character: Character, artifact_id: int) -> tuple[bool, str, dict]:
    artifact = db.query(CharacterArtifact).filter(CharacterArtifact.character_id == character.id, CharacterArtifact.id == artifact_id).first()
    if not artifact or not artifact.item_instance:
        return False, "未找到该法宝。", {"reason": "artifact_not_found"}
    instance = artifact.item_instance
    if instance.level >= ARTIFACT_UPGRADE["max_level"]:
        return False, "该法宝已强化至当前版本上限。", {"reason": "artifact_max_level"}
    cost = ARTIFACT_UPGRADE["base_spirit_stone_cost"] + (instance.level - 1) * ARTIFACT_UPGRADE["cost_growth"]
    if character.spirit_stones < cost:
        return False, f"灵石不足，强化需要 {cost} 灵石。", {"reason": "insufficient_spirit_stones", "cost": cost}
    character.spirit_stones -= cost
    rate = ARTIFACT_UPGRADE["success_rate_by_rarity"].get(instance.rarity, 0.8)
    success = random.random() <= rate
    if success:
        instance.level += 1
    db.flush()
    name = instance.template.name
    message = f"消耗 {cost} 灵石强化「{name}」，{'成功提升至 +' + str(instance.level) if success else '未能成功'}。"
    return success, message, {"artifact_id": artifact.id, "cost": cost, "success_rate": rate, "upgraded": success, "level": instance.level}


def _target_method(character: Character, method_id: int | None) -> CharacterMethod | None:
    if method_id:
        return next((method for method in character.methods if method.id == method_id), None)
    return next((method for method in character.methods if method.equipped), None)
