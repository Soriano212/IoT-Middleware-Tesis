import inspect
from typing import Dict, Any
from uuid import UUID

from src.core.plugin_management.plugin_controller import PluginController
from src.core.utils.singleton import SingletonMeta
from src.core.device_management.equipment import Equipment, Device
from src.core.actuator_management.actuator import Actuator
from src.core.device_management.sensor import Sensor
from src.core.actuator_management.actuator_factory import ActuatorFactory
from src.core.access_gateway.channel import Channel


class EquipmentController(metaclass=SingletonMeta):
    def __init__(self):
        self.channels_index: Dict[UUID, Equipment] = {}
        self.equipments_index: Dict[UUID, Equipment] = {}
        self.devices_index: Dict[UUID, Device] = {}

        self.plugin_controller = None
        self.actuator_factory = ActuatorFactory()

    @property
    def plugin_controller(self):
        if self._plugin_controller is None:
            self._plugin_controller = PluginController()
        return self._plugin_controller

    @plugin_controller.setter
    def plugin_controller(self, value):
        self._plugin_controller = value

    def create_channel(
        self,
        *,
        label: str,
        description: str,
        plugin_class_name: str,
        config_params: Dict[str, str],
    ) -> Channel:
        plugin = self.plugin_controller.get_plugin_by_class_name(plugin_class_name)

        if not plugin:
            raise ValueError(f"Plugin {plugin_class_name} not found")

        new_channel = Channel(
            label=label,
            description=description,
            plugin_class=plugin.cls,
            config_params=config_params,
        )

        self.channels_index[new_channel.id] = new_channel

        return new_channel

    def create_equipment(self, label: str, description: str, channel_id: UUID):
        channel = self.channels_index.get(channel_id)

        if not channel:
            raise ValueError(f"Channel {channel_id} not found")

        new_equipment = Equipment(label=label, description=description, channel=channel)
        self.equipments_index[new_equipment.id] = new_equipment

        return new_equipment

    def create_actuator(
        self,
        *,
        equipment_id: UUID,
        label: str,
        description: str,
        actuator_type: str,
        plugin_class_name: str,
        brand: str = None,
        model: str = None,
        config_params: Dict[str, Any] = None,
    ) -> Actuator:
        equipment = self.equipments_index.get(equipment_id)

        if not equipment:
            raise ValueError(f"Equipment {equipment_id} not found")

        plugin = self.plugin_controller.get_plugin_by_class_name(plugin_class_name)

        if not plugin:
            raise ValueError(f"Plugin {plugin_class_name} not found")

        new_actuator = self.actuator_factory.create_actuator(
            actuator_type=actuator_type,
            label=label,
            description=description,
            plugin_class=plugin.cls,
            brand=brand,
            model=model,
            config_params=config_params,
            channel=equipment.channel,
        )

        equipment.add_device(new_actuator)
        self.devices_index[new_actuator.id] = new_actuator

        return new_actuator

    def create_sensor(
        self,
        *,
        equipment_id: UUID,
        label: str,
        description: str,
        plugin_class_name: str,
        brand: str = None,
        model: str = None,
        config_params: Dict[str, Any] = None,
    ) -> Sensor:

        equipment = self.equipments_index.get(equipment_id)

        if not equipment:
            raise ValueError(f"Equipment {equipment_id} not found")

        plugin = self.plugin_controller.get_plugin_by_class_name(plugin_class_name)

        if not plugin:
            raise ValueError(f"Plugin {plugin_class_name} not found")

        new_sensor = Sensor(
            label=label,
            description=description,
            brand=brand,
            model=model,
            plugin_class=plugin.cls,
            config_params=config_params,
            channel=equipment.channel,
        )

        equipment.add_device(new_sensor)
        self.devices_index[new_sensor.id] = new_sensor

        return new_sensor

    def get_equipment_by_id(self, equipment_id: UUID):
        return self.equipments_index.get(equipment_id)

    def get_device_by_id(self, device_id: UUID):
        return self.devices_index.get(device_id)

    def get_operations_by_actuator_type(self, actuator_type: str):
        actuator_cls = self.actuator_factory.actuator_classes.get(actuator_type)

        if actuator_cls:
            exclude_methods = {"to_dict", "states_info", "PLUGIN_INTERFACE"}
            methods_info = {}

            for method_name in dir(actuator_cls):

                if (
                    callable(getattr(actuator_cls, method_name))
                    and not method_name.startswith("_")
                    and method_name not in exclude_methods
                ):
                    method = getattr(actuator_cls, method_name)
                    sig = inspect.signature(method)

                    params = {}

                    for name, param in sig.parameters.items():
                        if name != "self":
                            param_type = (
                                param.annotation
                                if param.annotation != inspect._empty
                                else "Unknown"
                            )
                            params[name] = param_type.__name__

                    methods_info[method_name] = params

            return methods_info

        return None

    def do_an_operation_by_actuator_id(
        self, device_id: UUID, operation: str, operation_params: Dict[str, str]
    ) -> bool:
        actuator = self.devices_index.get(device_id)

        if not actuator or not issubclass(actuator.__class__, Actuator):
            return False

        method = getattr(actuator, operation)

        if method is not None and callable(method):
            method(**operation_params)
            return True

        return False
