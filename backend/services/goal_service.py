# Goal Chain Service
# MVP - read-only goal generation, no player state modification

from typing import List
from sqlalchemy.orm import Session

from backend.configs.goals import (
    BREAKTHROUGH_APPROACH_THRESHOLD,
    MAX_LONG_TERM,
    MAX_SHORT_TERM,
    MAX_TOTAL_GOALS,
    PRIORITY_BREAKTHROUGH,
    PRIORITY_LIFE_SKILL,
    PRIORITY_MANA_ACTION,
    PRIORITY_MATERIAL_EXPLORE,
    PRIORITY_SECT_PROMOTION,
    PRIORITY_SECT_TASK,
    SECT_PROMOTION_APPROACH_THRESHOLD,
)
from backend.configs.realms import REALM_BY_NAME, REALM_NAMES
from backend.configs.sects import POSITION_NAMES, PROMOTION_RULES
from backend.configs.items import ITEM_TEMPLATES
from backend.models import Character
from backend.services.display_service import item_name


ITEMS_BY_CODE = {item["code"]: item for item in ITEM_TEMPLATES}


def get_current_goals(db: Session, character: Character) -> List[dict]:
    """
    Generate goal recommendations for player.
    READ-ONLY: This function does NOT modify any player state.
    """
    goals = []

    # Build each goal type
    sect_task_goal = _build_sect_task_goal(db, character)
    if sect_task_goal:
        goals.append(sect_task_goal)

    material_goal = _build_material_explore_goal(db, character)
    if material_goal:
        goals.append(material_goal)

    life_skill_goal = _build_life_skill_goal(db, character)
    if life_skill_goal:
        goals.append(life_skill_goal)

    mana_goal = _build_mana_action_goal(db, character, goals)
    if mana_goal:
        goals.append(mana_goal)

    breakthrough_goal = _build_breakthrough_goal(character)
    if breakthrough_goal:
        goals.append(breakthrough_goal)

    sect_promotion_goal = _build_sect_promotion_goal(db, character)
    if sect_promotion_goal:
        goals.append(sect_promotion_goal)

    # Sort by priority (higher first)
    goals.sort(key=lambda g: g["priority"], reverse=True)

    # Separate short_term and long_term
    short_term_goals = [g for g in goals if g["category"] == "short_term"]
    long_term_goals = [g for g in goals if g["category"] == "long_term"]

    # Apply limits
    short_term_goals = short_term_goals[:MAX_SHORT_TERM]
    long_term_goals = long_term_goals[:MAX_LONG_TERM]

    # Combine and limit total
    result = (short_term_goals + long_term_goals)[:MAX_TOTAL_GOALS]

    # Sanitize payload - remove internal fields from response
    return [_sanitize_goal(g) for g in result]


def _sanitize_goal(goal: dict) -> dict:
    """Remove internal-only fields from goal"""
    return {
        "id": goal["id"],
        "category": goal["category"],
        "title": goal["title"],
        "reason": goal["reason"],
        "progress_text": goal.get("progress_text"),
        "requirements": goal.get("requirements", []),
        "recommended_action": goal["recommended_action"],
        "benefits": goal["benefits"],
        "priority": goal["priority"],
    }


def _build_sect_task_goal(db: Session, character: Character) -> dict | None:
    """Generate goal for current sect task"""
    from backend.services.sect_service import active_member, position_name
    from backend.models import Sect, SectTask

    member = active_member(db, character)
    if not member:
        return None

    # Explicitly load sect to avoid lazy-load issues
    sect = db.query(Sect).filter(Sect.id == member.sect_id).first()
    if not sect:
        return None

    # Get current active task
    task = (
        db.query(SectTask)
        .filter(
            SectTask.character_id == character.id,
            SectTask.sect_id == member.sect_id,
            SectTask.status == "active",
        )
        .first()
    )
    if not task:
        return None

    # Get task config for display
    from backend.services.sect_service import _task_config

    config = _task_config(task.task_code) or {}
    name = config.get("name", task.task_code)
    description = config.get("description", "")
    target = config.get("target", config.get("target_count", 1))
    reward = config.get("reward", {})

    reward_text = ""
    if reward.get("contribution"):
        reward_text += f"贡献 {reward['contribution']}"
    if reward.get("spirit_stones"):
        if reward_text:
            reward_text += " · "
        reward_text += f"灵石 {reward['spirit_stones']}"

    progress_text = f"进度：{task.progress} / {target}"
    if task.task_type == "donate_spirit_stones":
        stones = config.get("required_spirit_stones", 0)
        progress_text = f"需要捐献：灵石 {stones}"

    requirements = []
    gap = target - task.progress
    if task.task_type == "donate_spirit_stones":
        stones = config.get("required_spirit_stones", 0)
        gap = stones - task.progress if task.progress < stones else 0
        if gap > 0:
            requirements.append(f"需要捐献灵石 {gap}")
    elif gap > 0:
        requirements.append(f"还需完成 {gap} 个目标")

    return {
        "id": "sect_task_current",
        "category": "short_term",
        "title": f"完成宗门任务：{name}",
        "reason": "完成宗门任务是获取贡献和阵营声望的重要途径，是宗门成长的核心路径。",
        "progress_text": progress_text,
        "requirements": requirements,
        "recommended_action": "可以在宗门页面查看任务详情，完成相应目标后提交任务。",
        "benefits": f"完成后可获得宗门贡献和声望。{'奖励：' + reward_text if reward_text else ''}",
        "priority": PRIORITY_SECT_TASK,
    }


def _build_material_explore_goal(db: Session, character: Character) -> dict | None:
    """Generate goal for gathering materials through exploration"""
    # Check if player has low materials
    from backend.services.inventory_service import inventory_payload

    inventory = inventory_payload(db, character)
    low_stones = character.spirit_stones < 50
    has_healing_herb = any(
        slot.get("code") == "healing_herb" and slot.get("quantity", 0) > 0
        for slot in inventory
    )
    has_low_material = any(
        slot.get("code") == "low_material" and slot.get("quantity", 0) > 0
        for slot in inventory
    )

    if has_healing_herb and has_low_material and not low_stones:
        return None  # Player has materials, no need

    missing_items = []
    if not has_healing_herb:
        missing_items.append(f"疗伤草")
    if not has_low_material:
        missing_items.append(f"炼器材料")

    if low_stones:
        missing_items.append(f"灵石")

    if not missing_items:
        return None

    reason = "探索是获取修行材料的主要来源，你当前缺少部分关键材料。"
    if low_stones:
        reason = "灵石是修行中的核心资源，探索可帮助你积累灵石。"

    requirements = [f"缺少：{'、'.join(missing_items)}"]
    if low_stones:
        requirements = [f"当前灵石：{character.spirit_stones}，建议积累"]

    return {
        "id": "material_explore",
        "category": "short_term",
        "title": "探索获取修行材料",
        "reason": reason,
        "progress_text": None,
        "requirements": requirements,
        "recommended_action": "消耗法力进行探索，积累炼丹、炼器和突破所需材料。",
        "benefits": "获得灵草、炼器材料等修行资源，为后续成长做准备。",
        "priority": PRIORITY_MATERIAL_EXPLORE,
    }


def _build_life_skill_goal(db: Session, character: Character) -> dict | None:
    """Generate goal for life skill crafting"""
    from backend.services.inventory_service import inventory_payload

    inventory = inventory_payload(db, character)
    char_mana = character.mana

    # Check if player can craft something
    # Key recipes: huichun_pill (14 mana), yangqi_pill (18 mana)
    has_healing_herb = any(
        slot.get("code") == "healing_herb" and slot.get("quantity", 0) > 0
        for slot in inventory
    )
    has_low_stone = any(
        slot.get("code") == "low_spirit_stone" and slot.get("quantity", 0) > 0
        for slot in inventory
    )
    has_low_material = any(
        slot.get("code") == "low_material" and slot.get("quantity", 0) > 0
        for slot in inventory
    )

    # Can craft huichun pill?
    can_craft_huichun = (
        has_healing_herb
        and has_low_stone
        and char_mana >= 14
    )
    # Can craft yangqi pill?
    can_craft_yangqi = (
        has_healing_herb
        and has_low_stone
        and char_mana >= 18
    )

    if not can_craft_huichun and not can_craft_yangqi:
        return None  # Not enough materials/mana

    # Pick the most appropriate one
    if can_craft_huichun:
        herb_count = next(
            (slot.get("quantity", 0) for slot in inventory if slot.get("code") == "healing_herb"),
            0
        )
        stone_count = next(
            (slot.get("quantity", 0) for slot in inventory if slot.get("code") == "low_spirit_stone"),
            0
        )
        return {
            "id": "life_skill_huichun",
            "category": "short_term",
            "title": "炼制回春丹",
            "reason": "回春丹可以恢复气血，炼制后可在探索或紧急时刻使用，提高修行容错。",
            "progress_text": f"材料：疗伤草 {herb_count}、下品灵石 {stone_count}",
            "requirements": ["材料已满足，可进行炼制"],
            "recommended_action": "前往生活技能页面，选择炼丹并炼制回春丹。",
            "benefits": "获得可使用丹药，恢复气血，提高生存能力。",
            "priority": PRIORITY_LIFE_SKILL,
        }
    elif can_craft_yangqi:
        herb_count = next(
            (slot.get("quantity", 0) for slot in inventory if slot.get("code") == "healing_herb"),
            0
        )
        stone_count = next(
            (slot.get("quantity", 0) for slot in inventory if slot.get("code") == "low_spirit_stone"),
            0
        )
        return {
            "id": "life_skill_yangqi",
            "category": "short_term",
            "title": "炼制养气丹",
            "reason": "养气丹可以提升修炼收益，炼制后使用可加速修为积累。",
            "progress_text": f"材料：疗伤草 {herb_count}、下品灵石 {stone_count}",
            "requirements": ["材料已满足，可进行炼制"],
            "recommended_action": "前往生活技能页面，选择炼丹并炼制养气丹。",
            "benefits": "获得可使用丹药，下次修炼获得修为加成。",
            "priority": PRIORITY_LIFE_SKILL - 10,
        }

    return None


def _build_mana_action_goal(db: Session, character: Character, existing_goals: List[dict]) -> dict | None:
    """Generate goal for mana-based actions - fallback when no other short-term goals"""
    # Only show mana action if no other short-term goals exist
    short_term_count = sum(1 for g in existing_goals if g["category"] == "short_term")
    if short_term_count >= MAX_SHORT_TERM:
        return None

    # Only show if player has enough mana for basic actions
    if character.mana < 12:
        return None

    mana_status = "法力充足" if character.mana >= 50 else f"法力 {character.mana}"
    action_options = []
    if character.mana >= 12:
        action_options.append("修炼")
    if character.mana >= 18:
        action_options.append("探索")

    if not action_options:
        return None

    return {
        "id": "mana_action",
        "category": "short_term",
        "title": "安排本轮修行行动",
        "reason": f"你的法力可以支持行动，可以选择修炼或探索来积累成长。",
        "progress_text": f"当前状态：{mana_status}",
        "requirements": [],
        "recommended_action": f"想提升修为可选择修炼，想获取材料可选择探索。{' / '.join(action_options)}均可消耗法力执行。",
        "benefits": "稳定提升修为或获得修行资源。",
        "priority": PRIORITY_MANA_ACTION,
    }


def _build_breakthrough_goal(character: Character) -> dict | None:
    """Generate goal for realm breakthrough preparation"""
    cultivation = character.cultivation
    cap = character.cultivation_cap
    progress = cultivation / cap if cap > 0 else 0

    if progress < BREAKTHROUGH_APPROACH_THRESHOLD:
        return None  # Not close enough

    # Check if player has breakthrough item or can explore for it
    from backend.services.inventory_service import inventory_payload

    has_foundation_pill = False  # Will check from inventory if needed

    progress_text = f"修为：{cultivation} / {cap}"
    requirements = []
    if progress >= 0.85:
        requirements.append("境界接近瓶颈，继续积累")
    if progress >= 0.70:
        requirements.append("可开始准备突破资源")

    realm_config = REALM_BY_NAME.get(character.realm)
    realm_name = realm_config.name if realm_config else character.realm

    return {
        "id": "breakthrough_prepare",
        "category": "long_term",
        "title": f"准备突破 {realm_name} 境界",
        "reason": f"你的修为正在接近 {realm_name} 瓶颈，提前准备突破条件会让境界提升更顺畅。",
        "progress_text": progress_text,
        "requirements": requirements if requirements else ["继续修炼积累修为"],
        "recommended_action": "通过修炼提升修为，通过探索和炼丹准备突破所需资源。",
        "benefits": "突破后提升境界上限，增加成长空间和属性。",
        "priority": PRIORITY_BREAKTHROUGH,
    }


def _build_sect_promotion_goal(db: Session, character: Character) -> dict | None:
    """Generate goal for sect position promotion"""
    from backend.services.sect_service import active_member
    from backend.models import Sect

    member = active_member(db, character)
    if not member:
        return None

    # Explicitly load sect to avoid lazy-load issues
    sect = db.query(Sect).filter(Sect.id == member.sect_id).first()
    if not sect:
        return None

    faction = sect.faction
    current_position = member.position
    current_contribution = member.contribution

    # Get promotion rules (keyed by position)
    promotion_rules = PROMOTION_RULES
    next_position = _get_next_position(faction, current_position)
    if not next_position:
        return None  # Already at highest position

    required_contribution = promotion_rules.get(next_position, {}).get("contribution", 0)
    if required_contribution <= 0:
        return None

    progress = current_contribution / required_contribution if required_contribution > 0 else 0
    if progress < SECT_PROMOTION_APPROACH_THRESHOLD:
        return None  # Not close enough

    position_display = POSITION_NAMES.get(faction, POSITION_NAMES["righteous"]).get(next_position, next_position)

    return {
        "id": "sect_promotion",
        "category": "long_term",
        "title": f"积累贡献晋升为 {position_display}",
        "reason": f"你的宗门贡献正在接近晋升要求，晋升后可解锁更高阶任务和宗门资源。",
        "progress_text": f"宗门贡献：{current_contribution} / {required_contribution}",
        "requirements": [f"目标贡献：{required_contribution}，还需 {max(0, required_contribution - current_contribution)}"],
        "recommended_action": "继续完成宗门任务，积累贡献达到晋升要求。",
        "benefits": f"晋升为 {position_display}，解锁更多宗门内容和任务。",
        "priority": PRIORITY_SECT_PROMOTION,
    }


def _get_next_position(faction: str, current: str) -> str | None:
    """Get the next promotion position"""
    from backend.configs.sects import POSITION_ORDER

    order = POSITION_ORDER if faction == "righteous" else POSITION_ORDER
    try:
        idx = order.index(current)
        if idx + 1 < len(order):
            return order[idx + 1]
    except ValueError:
        pass
    return None