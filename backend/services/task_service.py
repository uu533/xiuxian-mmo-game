from sqlalchemy.orm import Session

from backend.configs.tasks import TASKS, TASK_BY_ID
from backend.models import Character, CharacterTask, User, utc_now
from backend.services.inventory_service import add_item_to_main_bag
from backend.services.log_service import write_log


def ensure_character_tasks(db: Session, character: Character) -> None:
    existing = {task.task_id for task in character.tasks}
    for config in TASKS:
        if config["id"] not in existing:
            db.add(CharacterTask(character_id=character.id, task_id=config["id"], target=config["target"]))
    db.flush()


def tasks_payload(character: Character) -> list[dict]:
    return [task_payload(task) for task in sorted(character.tasks, key=lambda item: item.task_id)]


def active_task_payload(character: Character) -> dict | None:
    active = next((task for task in sorted(character.tasks, key=lambda item: item.task_id) if task.status == "active"), None)
    return task_payload(active) if active else None


def task_payload(task: CharacterTask) -> dict:
    config = TASK_BY_ID.get(task.task_id, {})
    return {
        "id": task.task_id,
        "name": config.get("name", task.task_id),
        "description": config.get("description", ""),
        "type": config.get("type", ""),
        "progress": task.progress,
        "target": task.target,
        "status": task.status,
        "reward": config.get("reward", {}),
    }


def record_task_progress(db: Session, user: User, action_type: str, success: bool, result_data: dict | None = None) -> list[str]:
    if not success:
        return []
    result_data = result_data or {}
    ensure_character_tasks(db, user.character)
    messages: list[str] = []
    task = next((item for item in sorted(user.character.tasks, key=lambda item: item.task_id) if item.status == "active"), None)
    if not task:
        return []
    config = TASK_BY_ID.get(task.task_id)
    if not config or not _task_matches(config, action_type, result_data):
        return []
    task.progress = min(task.target, task.progress + 1)
    if task.progress >= task.target:
        task.status = "completed"
        task.reward_claimed = 1
        task.completed_at = utc_now()
        reward_message = _grant_task_reward(db, user.character, config.get("reward", {}))
        message = f"任务完成：{config['name']}。{reward_message}"
        write_log(db, user, "task", message, {"task_id": task.task_id, "reward": config.get("reward", {})})
        messages.append(message)
    else:
        messages.append(f"任务进度：{config['name']} {task.progress}/{task.target}")
    return messages


def _task_matches(config: dict, action_type: str, result_data: dict) -> bool:
    task_type = config["type"]
    if task_type == action_type:
        return True
    if task_type == "breakthrough_realm" and action_type == "breakthrough":
        return result_data.get("to_realm", "").startswith(config.get("target_realm_stage", ""))
    return False


def _grant_task_reward(db: Session, character: Character, reward: dict) -> str:
    parts: list[str] = []
    stones = int(reward.get("spirit_stones", 0))
    if stones:
        character.spirit_stones += stones
        parts.append(f"获得 {stones} 灵石")
    for item in reward.get("items", []):
        ok, message, _payload = add_item_to_main_bag(db, character, item["code"], int(item.get("quantity", 1)))
        parts.append(message if ok else f"奖励暂存失败：{message}")
    return "；".join(parts) if parts else "暂无额外奖励"
