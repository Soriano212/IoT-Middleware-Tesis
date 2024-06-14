from typing import Dict, List

from src.core.device_managment.equipment_controller import EquipmentController


class PluginService:
    def __init__(self):
        self.equipment_control = EquipmentController()

    def get_plugin_names_by_actuator_type(self, actuator_type: str) -> List[str]:
        actuator_class = self.equipment_control.actuator_factory.actuator_classes.get(
            actuator_type
        )

        if not actuator_class:
            return []

        interface = actuator_class.PLUGIN_INTERFACE

        plugins = (
            self.equipment_control.plugin_loader.get_plugin_names_by_interface_name(
                interface.__name__
            )
        )
        return plugins

    def get_plugin_configuration_params(self, plugin_name: str) -> Dict[str, str]:
        plugin = self.equipment_control.plugin_loader.get_plugin_by_class_name(
            plugin_name
        )
        return plugin.params
