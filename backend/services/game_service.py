import random

from sqlalchemy.orm import Session

from backend.models import Character, InventoryItem, Log, User, utc_now
from backend.services.realm_service import (
    base_combat_stats,
    base_mana_cap,
    current_index,
    current_step,
    is_major_breakthrough,
    next_step,
    normalize_realm,
    normalize_title,
    unlocked_titles,
)
from backend.services.sect_service import identity_status, sect_position
from backend.services.spiritual_root_service import root_rate

ITEM_POOL = ["止血草", "聚气散", "玄铁碎片", "妖兽内丹", "残破玉简", "清心符", "回灵丹"]
BACKPACK_SLOT_COUNT = 81

TRAIN_MANA_COST = 12
EXPLORE_MANA_COST = 18
BREAKTHROUGH_MANA_COST = 35
MEDITATE_MANA_RECOVERY = 30
SPIRIT_STONE_MANA_RECOVERY = 60
SPIRIT_STONE_RECOVERY_COST = 10
PILL_MANA_RECOVERY = 120
MANA_HELP_TEXT = "法力不足，可通过打坐恢复法力、吸收灵石恢复法力，或服用丹药恢复法力。"


def add_log(db: Session, user_id: int, content: str) -> None:
    db.add(Log(user_id=user_id, content=content))


def computed_stats(character: Character) -> dict:
    normalize_realm(character)
    attack_base, defense_base = base_combat_stats(character.realm)
    attack_bonus = character.cultivation_method_attack_bonus + character.magic_treasure_attack_bonus
    defense_bonus = character.cultivation_method_defense_bonus + character.magic_treasure_defense_bonus
    mana_bonus = character.cultivation_method_mana_bonus + character.magic_treasure_mana_bonus
    max_mana = base_mana_cap(character.realm) + mana_bonus
    character.lifespan = realm_lifespan(character)
    character.mana = min(character.mana, max_mana)
    return {
        "attack_base": attack_base,
        "defense_base": defense_base,
        "attack_bonus": attack_bonus,
        "defense_bonus": defense_bonus,
        "mana_bonus": mana_bonus,
        "attack": attack_base + attack_bonus,
        "defense": defense_base + defense_bonus,
        "max_mana": max_mana,
    }


def realm_lifespan(character: Character) -> int:
    normalize_realm(character)
    # normalize_realm already writes the realm lifespan cap onto the character.
    return character.lifespan


def character_payload(character: Character) -> dict:
    normalize_realm(character)
    normalize_title(character)
    stats = computed_stats(character)
    return {
        "title": character.title,
        "unlocked_titles": unlocked_titles(character.realm),
        "life_status": "陨落" if character.hp <= 0 else "存活",
        "sect_name": character.sect_name,
        "sect_branch": character.sect_branch,
        "sect_position": sect_position(character),
        "identity_status": identity_status(character),
        "realm": character.realm,
        "cultivation": character.cultivation,
        "cultivation_cap": character.cultivation_cap,
        "spiritual_root": character.spiritual_root,
        "age": character.age,
        "lifespan": character.lifespan,
        "hp": character.hp,
        "mana": character.mana,
        "max_mana": stats["max_mana"],
        "attack": stats["attack"],
        "defense": stats["defense"],
        "spirit_stones": character.spirit_stones,
        "attack_base": stats["attack_base"],
        "defense_base": stats["defense_base"],
        "attack_bonus": stats["attack_bonus"],
        "defense_bonus": stats["defense_bonus"],
        "mana_bonus": stats["mana_bonus"],
    }


def inventory_payload(user: User) -> list[dict]:
    slots = [{"slot_index": index, "name": None, "quantity": 0} for index in range(1, BACKPACK_SLOT_COUNT + 1)]
    for index, item in enumerate(sorted(user.inventory, key=lambda value: (value.created_at, value.id)), start=1):
        if index > BACKPACK_SLOT_COUNT:
            break
        slots[index - 1] = {"slot_index": index, "name": item.name, "quantity": item.quantity}
    return slots


def me_payload(user: User) -> dict:
    return {
        "username": user.username,
        "character": character_payload(user.character),
        "inventory": inventory_payload(user),
    }


def set_title(db: Session, user: User, title: str) -> dict:
    character = user.character
    normalize_title(character)
    available = unlocked_titles(character.realm)
    if title not in available:
        message = f"称号「{title}」尚未解锁。"
        add_log(db, user.id, message)
        db.commit()
        return {"message": message, "character": character_payload(character), "inventory": inventory_payload(user)}

    character.title = title
    character.updated_at = utc_now()
    message = f"你将称号改为「{title}」。"
    add_log(db, user.id, message)
    db.commit()
    db.refresh(character)
    return {"message": message, "character": character_payload(character), "inventory": inventory_payload(user)}


def add_item(db: Session, user_id: int, name: str, quantity: int = 1) -> None:
    item_count = db.query(InventoryItem).filter(InventoryItem.user_id == user_id).count()
    item = db.query(InventoryItem).filter(InventoryItem.user_id == user_id, InventoryItem.name == name).first()
    if item:
        item.quantity += quantity
    elif item_count < BACKPACK_SLOT_COUNT:
        db.add(InventoryItem(user_id=user_id, name=name, quantity=quantity))


def spend_mana(character: Character, cost: int) -> tuple[bool, str | None]:
    max_mana = computed_stats(character)["max_mana"]
    character.mana = min(character.mana, max_mana)
    if character.mana < cost:
        return False, f"法力不足，本次需要 {cost} 点，当前只有 {character.mana} 点。{MANA_HELP_TEXT}"
    character.mana -= cost
    return True, None


def recover_mana(character: Character, amount: int) -> int:
    max_mana = computed_stats(character)["max_mana"]
    before = character.mana
    character.mana = min(max_mana, character.mana + amount)
    return character.mana - before


def train(db: Session, user: User) -> dict:
    character = user.character
    ok, error = spend_mana(character, TRAIN_MANA_COST)
    if not ok:
        add_log(db, user.id, error or MANA_HELP_TEXT)
        db.commit()
        return {"message": error, "character": character_payload(character), "inventory": inventory_payload(user)}

    gain = int(random.randint(16, 28) * root_rate(character.spiritual_root) + computed_stats(character)["max_mana"] * 0.03)
    character.cultivation = min(character.cultivation_cap, character.cultivation + gain)
    character.inner_demon = min(100, character.inner_demon + random.choice([0, 0, 1]))
    character.updated_at = utc_now()

    message = f"打坐修炼消耗 {TRAIN_MANA_COST} 点法力，炼化灵气，修为增加 {gain}。"
    add_log(db, user.id, message)
    db.commit()
    db.refresh(character)
    return {"message": message, "character": character_payload(character), "inventory": inventory_payload(user)}


def run_battle(character: Character) -> tuple[bool, list[str]]:
    normalize_realm(character)
    stats = computed_stats(character)
    enemy_name = random.choice(["山魈", "散修劫匪", "黑鳞妖蛇", "迷雾鬼修"])
    realm_power = current_index(character)
    enemy_hp = random.randint(42, 82) + realm_power * 10
    enemy_attack = random.randint(8, 18) + realm_power * 3
    hp = character.hp
    rounds: list[str] = [f"遭遇{enemy_name}，斗法开始。"]

    for round_index in range(1, 7):
        damage = max(1, stats["attack"] + random.randint(0, 8) - random.randint(0, 5))
        enemy_hp -= damage
        rounds.append(f"第{round_index}回合，你造成 {damage} 伤害。")
        if enemy_hp <= 0:
            rounds.append(f"{enemy_name}败退。")
            return True, rounds

        taken = max(1, enemy_attack + random.randint(0, 6) - stats["defense"])
        hp -= taken
        rounds.append(f"{enemy_name}反击，你损失 {taken} 气血。")
        if hp <= 0:
            rounds.append("你气血耗尽，身死道消。")
            character.hp = 0
            character.inner_demon = min(100, character.inner_demon + 12)
            return False, rounds

    character.hp = max(0, hp)
    won = enemy_hp <= 0 or random.random() < 0.35
    rounds.append("战斗久拖不决，你抓住破绽脱身。" if won else "你被迫退走，心神受损。")
    if not won:
        character.inner_demon = min(100, character.inner_demon + 5)
    return won, rounds


def explore(db: Session, user: User) -> dict:
    character = user.character
    ok, error = spend_mana(character, EXPLORE_MANA_COST)
    if not ok:
        add_log(db, user.id, error or MANA_HELP_TEXT)
        db.commit()
        return {"message": error, "character": character_payload(character), "inventory": inventory_payload(user)}

    roll = random.random()
    if roll < 0.38:
        stones = random.randint(18, 68) + character.luck // 5
        character.spirit_stones += stones
        message = f"外出探索消耗 {EXPLORE_MANA_COST} 点法力，发现废弃矿脉，获得 {stones} 灵石。"
    elif roll < 0.68:
        item_name = random.choice(ITEM_POOL)
        quantity = random.randint(1, 3)
        add_item(db, user.id, item_name, quantity)
        message = f"外出探索消耗 {EXPLORE_MANA_COST} 点法力，采得 {item_name} x{quantity}。"
    else:
        won, rounds = run_battle(character)
        if won:
            reward = random.randint(28, 88)
            character.spirit_stones += reward
            if random.random() < 0.45:
                add_item(db, user.id, random.choice(ITEM_POOL), 1)
            message = f"外出探索消耗 {EXPLORE_MANA_COST} 点法力。" + " ".join(rounds) + f" 战后搜得 {reward} 灵石。"
        else:
            message = f"外出探索消耗 {EXPLORE_MANA_COST} 点法力。" + " ".join(rounds)

    character.cultivation = min(character.cultivation_cap, character.cultivation + random.randint(4, 16))
    character.updated_at = utc_now()
    add_log(db, user.id, message)
    db.commit()
    db.refresh(character)
    return {"message": message, "character": character_payload(character), "inventory": inventory_payload(user)}


def breakthrough(db: Session, user: User) -> dict:
    character = user.character
    normalize_realm(character)
    if character.cultivation < character.cultivation_cap:
        message = f"修为尚未圆满，至少需要 {character.cultivation_cap} 修为。"
        add_log(db, user.id, message)
        db.commit()
        return {"message": message, "character": character_payload(character), "inventory": inventory_payload(user)}

    target_step = next_step(character)
    if not target_step:
        message = "你已抵达当前版本最高境界，暂无法继续突破。"
        add_log(db, user.id, message)
        db.commit()
        return {"message": message, "character": character_payload(character), "inventory": inventory_payload(user)}

    ok, error = spend_mana(character, BREAKTHROUGH_MANA_COST)
    if not ok:
        add_log(db, user.id, error or MANA_HELP_TEXT)
        db.commit()
        return {"message": error, "character": character_payload(character), "inventory": inventory_payload(user)}

    source_step = current_step(character)
    success_rate = source_step.breakthrough_rate + character.luck * 0.0018 - character.inner_demon * 0.0035
    if source_step.name == "结丹后期":
        success_rate -= 0.04
    if source_step.name.startswith("元婴") or source_step.name.startswith("化神"):
        success_rate -= 0.03
    success_rate = max(0.02, min(0.9, success_rate))

    forced_success = character.luck >= 100
    forced_failure = character.inner_demon >= 100

    if forced_success or (not forced_failure and random.random() <= success_rate):
        from_realm = character.realm
        character.realm = target_step.name
        character.cultivation = 0
        character.cultivation_cap = target_step.cultivation_cap
        normalize_realm(character)
        character.mana = computed_stats(character)["max_mana"]
        character.inner_demon = max(0, character.inner_demon - 10)
        if is_major_breakthrough(from_realm, character.realm):
            message = f"突破消耗 {BREAKTHROUGH_MANA_COST} 点法力。大境界突破成功！你踏入「{character.realm}」，寿元上限与法力大涨。"
        else:
            message = f"突破消耗 {BREAKTHROUGH_MANA_COST} 点法力。突破成功！你踏入「{character.realm}」。"
    else:
        character.cultivation = int(character.cultivation_cap * 0.42)
        character.inner_demon = min(100, character.inner_demon + random.randint(10, 18))
        character.hp = max(20, character.hp - random.randint(8, 22))
        message = f"突破消耗 {BREAKTHROUGH_MANA_COST} 点法力。突破失败，心魔反噬。当前突破成功率约 {int(success_rate * 100)}%。"

    character.updated_at = utc_now()
    add_log(db, user.id, message)
    db.commit()
    db.refresh(character)
    return {"message": message, "character": character_payload(character), "inventory": inventory_payload(user)}


def meditate_restore_mana(db: Session, user: User) -> dict:
    recovered = recover_mana(user.character, MEDITATE_MANA_RECOVERY)
    message = f"静坐调息，恢复 {recovered} 点法力。"
    add_log(db, user.id, message)
    db.commit()
    db.refresh(user.character)
    return {"message": message, "character": character_payload(user.character), "inventory": inventory_payload(user)}


def spirit_stone_restore_mana(db: Session, user: User) -> dict:
    character = user.character
    if character.spirit_stones < SPIRIT_STONE_RECOVERY_COST:
        message = f"灵石不足，吸收灵石恢复法力需要 {SPIRIT_STONE_RECOVERY_COST} 枚灵石。"
        add_log(db, user.id, message)
        db.commit()
        return {"message": message, "character": character_payload(character), "inventory": inventory_payload(user)}
    character.spirit_stones -= SPIRIT_STONE_RECOVERY_COST
    recovered = recover_mana(character, SPIRIT_STONE_MANA_RECOVERY)
    message = f"手握灵石吸取灵力，消耗 {SPIRIT_STONE_RECOVERY_COST} 灵石，恢复 {recovered} 点法力。"
    add_log(db, user.id, message)
    db.commit()
    db.refresh(character)
    return {"message": message, "character": character_payload(character), "inventory": inventory_payload(user)}


def pill_restore_mana(db: Session, user: User) -> dict:
    pill = db.query(InventoryItem).filter(InventoryItem.user_id == user.id, InventoryItem.name == "回灵丹", InventoryItem.quantity > 0).first()
    if not pill:
        message = "没有可服用的回灵丹，可通过探索获得丹药。"
        add_log(db, user.id, message)
        db.commit()
        return {"message": message, "character": character_payload(user.character), "inventory": inventory_payload(user)}
    pill.quantity -= 1
    recovered = recover_mana(user.character, PILL_MANA_RECOVERY)
    message = f"服下一枚回灵丹，恢复 {recovered} 点法力。"
    add_log(db, user.id, message)
    db.commit()
    db.refresh(user.character)
    return {"message": message, "character": character_payload(user.character), "inventory": inventory_payload(user)}
