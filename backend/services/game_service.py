import random
from datetime import timedelta

from sqlalchemy.orm import Session

from backend.models import Character, InventoryItem, Log, User, utc_now
from backend.services.realm_service import current_index, current_step, is_major_breakthrough, next_step, normalize_realm, normalize_title, unlocked_titles
from backend.services.spiritual_root_service import root_rate

ITEM_POOL = ["止血草", "聚气散", "玄铁碎片", "妖兽内丹", "残破玉简", "清心符"]

ACTION_RECOVERY_SECONDS = 10 * 60
ACTION_RECOVERY_AMOUNT = 5
ACTIONS_PER_YEAR = 1000
TRAIN_ACTION_COST = 10
EXPLORE_ACTION_COST = 15
BREAKTHROUGH_ACTION_COST = 30


def add_log(db: Session, user_id: int, content: str) -> None:
    db.add(Log(user_id=user_id, content=content))


def character_payload(character: Character) -> dict:
    normalize_realm(character)
    normalize_title(character)
    recover_action_points(character)
    return {
        "title": character.title,
        "unlocked_titles": unlocked_titles(character.realm),
        "life_status": "陨落" if character.hp <= 0 else "存活",
        "realm": character.realm,
        "cultivation": character.cultivation,
        "cultivation_cap": character.cultivation_cap,
        "spiritual_root": character.spiritual_root,
        "age": character.age,
        "lifespan": character.lifespan,
        "hp": character.hp,
        "mana": character.mana,
        "attack": character.attack,
        "defense": character.defense,
        "inner_demon": character.inner_demon,
        "luck": character.luck,
        "spirit_stones": character.spirit_stones,
        "action_points": character.action_points,
        "max_action_points": character.max_action_points,
        "action_spent_total": character.action_spent_total,
        "age_progress": character.age_progress,
    }


def inventory_payload(user: User) -> list[dict]:
    return [{"name": item.name, "quantity": item.quantity} for item in sorted(user.inventory, key=lambda value: value.name)]


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
    item = db.query(InventoryItem).filter(InventoryItem.user_id == user_id, InventoryItem.name == name).first()
    if item:
        item.quantity += quantity
    else:
        db.add(InventoryItem(user_id=user_id, name=name, quantity=quantity))


def recover_action_points(character: Character) -> None:
    now = utc_now()
    last_recovered = character.last_action_recovered_at or now
    if last_recovered.tzinfo is None:
        last_recovered = last_recovered.replace(tzinfo=now.tzinfo)

    elapsed_seconds = max(0, int((now - last_recovered).total_seconds()))
    intervals = elapsed_seconds // ACTION_RECOVERY_SECONDS
    if intervals <= 0:
        return

    before = character.action_points
    recovered = intervals * ACTION_RECOVERY_AMOUNT
    character.action_points = min(character.max_action_points, character.action_points + recovered)
    if character.action_points >= character.max_action_points:
        character.last_action_recovered_at = now
    elif character.action_points > before:
        character.last_action_recovered_at = last_recovered + timedelta(seconds=intervals * ACTION_RECOVERY_SECONDS)


def spend_action_points(character: Character, cost: int) -> tuple[bool, str | None]:
    recover_action_points(character)
    if character.action_points < cost:
        return False, f"行动力不足，本次需要 {cost} 点，当前只有 {character.action_points} 点。"

    character.action_points -= cost
    character.action_spent_total += cost
    character.age_progress += cost

    if character.age_progress >= ACTIONS_PER_YEAR:
        years = character.age_progress // ACTIONS_PER_YEAR
        character.age += years
        character.age_progress %= ACTIONS_PER_YEAR
        if character.age >= character.lifespan:
            character.hp = max(1, character.hp - 12 * years)
            character.inner_demon = min(100, character.inner_demon + 4 * years)

    return True, None


def train(db: Session, user: User) -> dict:
    character = user.character
    normalize_realm(character)
    ok, error = spend_action_points(character, TRAIN_ACTION_COST)
    if not ok:
        add_log(db, user.id, error or "行动力不足。")
        db.commit()
        return {"message": error, "character": character_payload(character), "inventory": inventory_payload(user)}

    gain = int(random.randint(16, 28) * root_rate(character.spiritual_root) + character.mana * 0.08)
    character.cultivation = min(character.cultivation_cap, character.cultivation + gain)
    character.mana = min(999, character.mana + random.randint(1, 4))
    character.inner_demon = min(100, character.inner_demon + random.choice([0, 0, 1]))
    character.updated_at = utc_now()

    message = f"打坐修炼消耗 {TRAIN_ACTION_COST} 点行动力，吸纳灵气，修为增加 {gain}。"
    add_log(db, user.id, message)
    db.commit()
    db.refresh(character)
    return {"message": message, "character": character_payload(character), "inventory": inventory_payload(user)}


def run_battle(character: Character) -> tuple[bool, list[str]]:
    normalize_realm(character)
    enemy_name = random.choice(["山魈", "散修劫匪", "黑鳞妖蛇", "迷雾鬼修"])
    realm_power = current_index(character)
    enemy_hp = random.randint(42, 82) + realm_power * 10
    enemy_attack = random.randint(8, 18) + realm_power * 3
    hp = character.hp
    rounds: list[str] = [f"遭遇{enemy_name}，战斗开始。"]

    for round_index in range(1, 7):
        damage = max(1, character.attack + random.randint(0, 8) - random.randint(0, 5))
        enemy_hp -= damage
        rounds.append(f"第{round_index}回合，你造成 {damage} 伤害。")
        if enemy_hp <= 0:
            rounds.append(f"{enemy_name}败退。")
            return True, rounds

        taken = max(1, enemy_attack + random.randint(0, 6) - character.defense)
        hp -= taken
        rounds.append(f"{enemy_name}反击，你损失 {taken} 气血。")
        if hp <= 0:
            rounds.append("你重伤遁走。")
            character.hp = max(10, character.hp // 2)
            character.inner_demon = min(100, character.inner_demon + 8)
            return False, rounds

    character.hp = max(10, hp)
    won = enemy_hp <= 0 or random.random() < 0.35
    rounds.append("战斗久拖不决，你抓住破绽脱身。" if won else "你被迫退走，心神受损。")
    if not won:
        character.inner_demon = min(100, character.inner_demon + 5)
    return won, rounds


def explore(db: Session, user: User) -> dict:
    character = user.character
    normalize_realm(character)
    ok, error = spend_action_points(character, EXPLORE_ACTION_COST)
    if not ok:
        add_log(db, user.id, error or "行动力不足。")
        db.commit()
        return {"message": error, "character": character_payload(character), "inventory": inventory_payload(user)}

    roll = random.random()
    if roll < 0.38:
        stones = random.randint(18, 68) + character.luck // 5
        character.spirit_stones += stones
        message = f"外出探索消耗 {EXPLORE_ACTION_COST} 点行动力，发现废弃矿脉，获得 {stones} 灵石。"
    elif roll < 0.68:
        item_name = random.choice(ITEM_POOL)
        quantity = random.randint(1, 3)
        add_item(db, user.id, item_name, quantity)
        message = f"外出探索消耗 {EXPLORE_ACTION_COST} 点行动力，采得 {item_name} x{quantity}。"
    else:
        won, rounds = run_battle(character)
        if won:
            reward = random.randint(28, 88)
            character.spirit_stones += reward
            if random.random() < 0.45:
                add_item(db, user.id, random.choice(ITEM_POOL), 1)
            message = f"外出探索消耗 {EXPLORE_ACTION_COST} 点行动力。" + " ".join(rounds) + f" 战后搜得 {reward} 灵石。"
        else:
            message = f"外出探索消耗 {EXPLORE_ACTION_COST} 点行动力。" + " ".join(rounds)

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

    source_step = current_step(character)
    success_rate = source_step.breakthrough_rate + character.luck * 0.0018 - character.inner_demon * 0.0035
    if source_step.name == "结丹后期":
        success_rate -= 0.04
    if source_step.name.startswith("元婴") or source_step.name.startswith("化神"):
        success_rate -= 0.03
    success_rate = max(0.02, min(0.9, success_rate))
    ok, error = spend_action_points(character, BREAKTHROUGH_ACTION_COST)
    if not ok:
        add_log(db, user.id, error or "行动力不足。")
        db.commit()
        return {"message": error, "character": character_payload(character), "inventory": inventory_payload(user)}

    forced_success = character.luck >= 100
    forced_failure = character.inner_demon >= 100

    if forced_success or (not forced_failure and random.random() <= success_rate):
        from_realm = character.realm
        character.realm = target_step.name
        character.cultivation = 0
        character.cultivation_cap = target_step.cultivation_cap
        character.lifespan += target_step.lifespan_bonus
        character.hp += target_step.hp_bonus
        character.mana += target_step.mana_bonus
        character.attack += target_step.attack_bonus
        character.defense += target_step.defense_bonus
        character.inner_demon = max(0, character.inner_demon - 10)
        if is_major_breakthrough(from_realm, character.realm):
            message = f"突破消耗 {BREAKTHROUGH_ACTION_COST} 点行动力。大境界突破成功！你踏入「{character.realm}」，寿元上限与法力大涨。"
        else:
            message = f"突破消耗 {BREAKTHROUGH_ACTION_COST} 点行动力。突破成功！你踏入「{character.realm}」。"
    else:
        character.cultivation = int(character.cultivation_cap * 0.42)
        character.inner_demon = min(100, character.inner_demon + random.randint(10, 18))
        character.hp = max(20, character.hp - random.randint(8, 22))
        message = f"突破消耗 {BREAKTHROUGH_ACTION_COST} 点行动力。突破失败，心魔反噬。当前突破成功率约 {int(success_rate * 100)}%。"

    character.updated_at = utc_now()
    add_log(db, user.id, message)
    db.commit()
    db.refresh(character)
    return {"message": message, "character": character_payload(character), "inventory": inventory_payload(user)}
