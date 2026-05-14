from sqlalchemy.orm import Session

from backend.configs.effects import ACTIVE_EFFECT_LIMITS, FORMATION_EFFECTS, ITEM_ACTIVE_EFFECTS
from backend.models import ActiveEffect, Character, User
from backend.services.display_service import active_effect_display
from backend.services.log_service import write_log


def active_effect_payload(effect: ActiveEffect) -> dict:
    return {
        "id": effect.id,
        "effect_type": effect.effect_type,
        "source_item_or_recipe": effect.source_item_or_recipe,
        **active_effect_display(effect.effect_type, effect.source_item_or_recipe),
        "remaining_uses": effect.remaining_uses,
        "value": effect.value,
        "expires_at": effect.expires_at.isoformat() if effect.expires_at else None,
        "created_at": effect.created_at.isoformat() if effect.created_at else None,
    }


def active_effects_payload(character: Character) -> list[dict]:
    return [active_effect_payload(effect) for effect in _active_effects(character)]


def activate_item_effect(db: Session, user: User, item_code: str) -> dict:
    config = ITEM_ACTIVE_EFFECTS.get(item_code)
    if not config:
        return {}
    return activate_effect(db, user, item_code, config)


def activate_formation_effect(db: Session, user: User, recipe_id: str) -> dict:
    config = FORMATION_EFFECTS.get(recipe_id)
    if not config:
        return {}
    return activate_effect(db, user, recipe_id, config)


def activate_effect(db: Session, user: User, source: str, config: dict) -> dict:
    character = user.character
    effect_type = config["effect_type"]
    value = float(config.get("value", 0))
    remaining_uses = int(config.get("remaining_uses", 1))
    current = _best_effect(character, effect_type)
    if current:
        if value > current.value:
            current.value = value
            current.source_item_or_recipe = source
        if ACTIVE_EFFECT_LIMITS.get("refresh_remaining_uses", True):
            current.remaining_uses = max(current.remaining_uses, remaining_uses)
        db.flush()
        payload = active_effect_payload(current)
        write_log(db, user, "effect", f"临时效果已刷新：{payload['effect_name']}。", payload)
        return active_effect_payload(current)
    effect = ActiveEffect(
        effect_type=effect_type,
        source_item_or_recipe=source,
        remaining_uses=remaining_uses,
        value=value,
    )
    character.active_effects.append(effect)
    db.flush()
    payload = active_effect_payload(effect)
    write_log(db, user, "effect", f"临时效果已生效：{payload['effect_name']}。", payload)
    return active_effect_payload(effect)


def effect_value(character: Character, effect_type: str) -> float:
    effect = _best_effect(character, effect_type)
    return float(effect.value) if effect else 0.0


def consume_effects(db: Session, user: User, effect_types: list[str]) -> dict:
    consumed: list[dict] = []
    expired: list[dict] = []
    for effect_type in effect_types:
        effect = _best_effect(user.character, effect_type)
        if not effect:
            continue
        effect.remaining_uses -= 1
        consumed.append(active_effect_payload(effect))
        payload = active_effect_payload(effect)
        write_log(db, user, "effect", f"临时效果已触发：{payload['effect_name']}。", payload)
        if effect.remaining_uses <= 0:
            expired.append(active_effect_payload(effect))
            write_log(db, user, "effect", f"临时效果已耗尽：{payload['effect_name']}。", payload)
            db.delete(effect)
    db.flush()
    return {"consumed": consumed, "expired": expired}


def _best_effect(character: Character, effect_type: str) -> ActiveEffect | None:
    effects = [effect for effect in _active_effects(character) if effect.effect_type == effect_type]
    if not effects:
        return None
    return max(effects, key=lambda item: (item.value, item.remaining_uses, item.id))


def _active_effects(character: Character) -> list[ActiveEffect]:
    return [effect for effect in character.active_effects if effect.remaining_uses > 0]
