from typing import List
from uuid import UUID

from src.core.application_management.equipment_controller import EquipmentController
from src.core.service_gateway.api.schemas.equipment_schema import EquipmentSchema
from src.core.service_gateway.api.schemas.equipment_creating_schema import (
    EquipmentCreatingSchema,
)


class EquipmentService:
    def __init__(self):
        self.equipment_control = EquipmentController()

    def get_equipment_by_id(self, equipment_id: UUID) -> EquipmentSchema | None:
        equipment = self.equipment_control.get_equipment_by_id(equipment_id)

        if equipment:
            return equipment.to_dict()

        return None

    def get_equipments(self) -> List[EquipmentSchema]:
        return [
            equipment.to_dict()
            for equipment in self.equipment_control.equipments_index.values()
        ]

    def create_equipment(self, equipment_create: EquipmentCreatingSchema):
        equipment = self.equipment_control.create_equipment(
            **equipment_create.model_dump()
        )

        if equipment:
            return equipment.to_dict()

        return None
