import random

from sqlalchemy.orm import Session

from backend.configs.events import EXPLORE_EVENTS
from backend.models import Character
from backend.services.calc_service import get_final_attack, get_final_defense
from backend.services.inventory_service import add_item_to_main_bag
from backend.utils.random_utils import weighted_choice


def pick_explore_event(character: Character) -> dict:
    luck = character.hidden_luck

    def event_weight(event: dict) -> float:
        weight = float(event["weight"])
        if event["type"] == "hidden_opportunity":
            weight *= 1 + luck / 100
        if event["type"] in {"trap", "empty"}:
            weight *= max(0.35, 1 - luck / 180)
        return weight

    return weighted_choice(EXPLORE_EVENTS, event_weight)


def resolve_explore_event(db: Session, character: Character) -> dict:
    event = pick_explore_event(character)
    rewards: list[dict] = []
    messages: list[str] = []
    data: dict = {"event": event["code"], "event_type": event["type"], "rewards": []}

    if event["type"] == "reward_spirit_stones":
        amount = _roll_range(event["rewards"]["spirit_stones"]) + character.hidden_luck // 5
        character.spirit_stones += amount
        rewards.append({"type": "spirit_stones", "quantity": amount})
        messages.append(f"你发现一处废弃矿脉，获得 {amount} 灵石。")

    elif event["type"] == "reward_item":
        for item_reward in event["rewards"].get("items", []):
            quantity = _roll_range(item_reward["quantity"])
            ok, msg, reward = add_item_to_main_bag(db, character, item_reward["code"], quantity)
            messages.append(msg)
            if ok and reward:
                rewards.append({"type": "item", **reward})

    elif event["type"] == "battle":
        battle_result = resolve_battle(character)
        data["battle"] = battle_result
        messages.append(battle_result["message"])
        if battle_result["won"]:
            amount = _roll_range(event["rewards"].get("spirit_stones", [20, 50]))
            character.spirit_stones += amount
            rewards.append({"type": "spirit_stones", "quantity": amount})
            messages.append(f"战后搜得 {amount} 灵石。")
            for item_reward in event["rewards"].get("items", []):
                if random.random() <= item_reward.get("chance", 1):
                    quantity = _roll_range(item_reward["quantity"])
                    ok, msg, reward = add_item_to_main_bag(db, character, item_reward["code"], quantity)
                    messages.append(msg)
                    if ok and reward:
                        rewards.append({"type": "item", **reward})

    elif event["type"] == "hidden_opportunity":
        amount = _roll_range(event["rewards"].get("spirit_stones", [0, 0]))
        if amount:
            character.spirit_stones += amount
            rewards.append({"type": "spirit_stones", "quantity": amount})
        for item_reward in event["rewards"].get("items", []):
            quantity = _roll_range(item_reward["quantity"])
            ok, msg, reward = add_item_to_main_bag(db, character, item_reward["code"], quantity)
            messages.append(msg)
            if ok and reward:
                rewards.append({"type": "item", **reward})
        messages.insert(0, f"你遇到机缘「{event['name']}」。")

    elif event["type"] == "trap":
        damage = _roll_range(event["risks"].get("hp_damage", [1, 1]))
        character.hp = max(0, character.hp - damage)
        messages.append(f"你误入迷阵，损失 {damage} 气血。")

    else:
        messages.append("你在山野间寻觅许久，空手而归。")

    data["rewards"] = rewards
    return {"event": event, "message": " ".join(messages), "rewards": rewards, "data": data}


def resolve_battle(character: Character) -> dict:
    enemy = random.choice(["青毛妖狼", "黑鳞妖蛇", "散修劫匪", "山魈"])
    enemy_hp = random.randint(42, 82)
    enemy_attack = random.randint(8, 18)
    player_attack = get_final_attack(character)
    player_defense = get_final_defense(character)
    damage_taken = 0
    rounds: list[str] = []
    won = False
    for index in range(1, 7):
        enemy_hp -= max(1, player_attack + random.randint(0, 8) - random.randint(0, 5))
        if enemy_hp <= 0:
            won = True
            rounds.append(f"第{index}回合击退{enemy}")
            break
        taken = max(1, enemy_attack + random.randint(0, 6) - player_defense)
        damage_taken += taken
        character.hp = max(0, character.hp - taken)
        if character.hp <= 0:
            break
    if won:
        message = f"你遭遇了一只{enemy}，苦战后获胜。"
    else:
        message = f"你遭遇了一只{enemy}，负伤后撤退。"
        character.hidden_inner_demon = min(100, character.hidden_inner_demon + 4)
    return {"enemy": enemy, "won": won, "damage_taken": damage_taken, "rounds": rounds, "message": message}


def _roll_range(value: list[int] | tuple[int, int]) -> int:
    return random.randint(int(value[0]), int(value[1]))
