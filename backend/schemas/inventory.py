from pydantic import BaseModel


class InventorySlotResponse(BaseModel):
    slot_index: int
    container_type: str
    container_id: int
    item_template_id: int | None
    item_instance_id: int | None
    code: str | None
    name: str | None
    type: str | None
    grade: int | None
    quantity: int
    stackable: bool


InventoryResponse = InventorySlotResponse
