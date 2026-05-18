from sqlalchemy.orm import Session

from backend.models import Character, User, utc_now
from backend.services.calc_service import derived_stats, get_breakthrough_rate, sync_base_and_caps
from backend.services.active_effect_service import active_effects_payload
from backend.services.realm_service import normalize_realm, normalize_title, unlocked_titles
from backend.services.sect_service import derive_sect_position, identity_status
from backend.services.auto_cultivation_service import auto_cultivation_summary


def character_payload(character: Character) -> dict:
    normalize_realm(character)
    normalize_title(character)
    sync_base_and_caps(character)
    stats = derived_stats(character)
    position = derive_sect_position(character)
    return {
        "id": character.id,
        "name": character.name,
        "title": character.title,
        "unlocked_titles": unlocked_titles(character.realm),
        "life_status": "陨落" if character.hp <= 0 else "存活",
        "realm": character.realm,
        "realm_stage": character.realm_stage,
        "cultivation": character.cultivation,
        "cultivation_cap": character.cultivation_cap,
        "spiritual_root": character.spiritual_root,
        "age": character.age,
        "lifespan": character.lifespan,
        "hp": character.hp,
        "max_hp": character.max_hp,
        "mana": character.mana,
        "max_mana": character.max_mana,
        "scout_talisman_charges": _remaining_effect_uses(character, "explore_luck_bonus"),
        "guard_talisman_charges": _remaining_effect_uses(character, "explore_damage_reduction"),
        "swift_talisman_charges": _remaining_effect_uses(character, "explore_mana_discount"),
        "active_effects": active_effects_payload(character),
        "attack": stats["final_attack"],
        "defense": stats["final_defense"],
        "base_attack": character.base_attack,
        "base_defense": character.base_defense,
        "attack_bonus": stats["final_attack"] - character.base_attack,
        "defense_bonus": stats["final_defense"] - character.base_defense,
        "cultivation_speed": stats["cultivation_speed"],
        "breakthrough_rate": get_breakthrough_rate(character),
        "spirit_stones": character.spirit_stones,
        "sect_id": character.sect_id,
        "sect_name": character.sect.name if character.sect else None,
        "sect_position": position,
        "identity_status": identity_status(character),
        "auto_cultivation": auto_cultivation_summary(character),
    }


def _remaining_effect_uses(character: Character, effect_type: str) -> int:
    return sum(effect.remaining_uses for effect in character.active_effects if effect.effect_type == effect_type and effect.remaining_uses > 0)


def set_title(db: Session, user: User, title: str) -> dict:
    character = user.character
    normalize_title(character)
    available = unlocked_titles(character.realm)
    if title not in available:
        message = f"称号「{title}」尚未解锁。"
        return {"success": False, "message": message}
    character.title = title
    character.updated_at = utc_now()
    db.flush()
    return {"success": True, "message": f"你将称号改为「{title}」。"}
