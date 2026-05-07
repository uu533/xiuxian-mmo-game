from sqlalchemy.orm import Session

from backend.models import ActionRecord, GameLog, User


def write_log(db: Session, user: User, log_type: str, content: str, data: dict | None = None) -> GameLog:
    log = GameLog(
        user_id=user.id,
        character_id=user.character.id,
        type=log_type,
        content=content,
        data_json=data or {},
    )
    db.add(log)
    return log


def write_action_record(db: Session, character_id: int, action_type: str, cost: dict, result: dict) -> ActionRecord:
    record = ActionRecord(character_id=character_id, action_type=action_type, cost_json=cost, result_json=result)
    db.add(record)
    return record
