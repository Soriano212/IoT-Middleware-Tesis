import os
import importlib.util

from typing import List, Dict

from src.core.plugin_management.plugin import Plugin
from src.core.actuator_management.actuator_factory import ActuatorFactory
from src.core.utils.singleton import SingletonMeta
from src.common.plugin_interfaces.sensor_plugin_interface import SensorPluginInterface
from src.common.plugin_interfaces.channel_plugin_interface import ChannelPluginInterface


class PluginController(metaclass=SingletonMeta):
    def __init__(self, plugin_path: str) -> None:
        self.plugins_type_index: Dict[str, List[Plugin]] = {}
        self.plugins_class_index: Dict[str, Plugin] = {}
        self.plugin_interfaces_index: Dict[str, type] = {}
        self.plugin_interfaces: List[type] = [
            ChannelPluginInterface,
            SensorPluginInterface,
        ]

        self.plugins_folder: str = plugin_path
        self.plugins_root_module = self._convert_path_to_module(self.plugins_folder)

        self.actuator_factory = ActuatorFactory()

        self._initialize_plugins_type_index()
        self.load_plugins()

    def _convert_path_to_module(self, path: str):
        if path.startswith("./"):
            path = path[2:]

        if path.endswith("/"):
            path = path[:-1]

        module_path = path.replace(os.path.sep, ".")

        return module_path

    def _initialize_plugins_type_index(self):

        for actuator_subclass in self.actuator_factory.actuator_classes.values():
            self.plugin_interfaces.append(actuator_subclass.PLUGIN_INTERFACE)

        for plugin_interface in self.plugin_interfaces:
            self.plugins_type_index[plugin_interface.__name__] = []
            self.plugin_interfaces_index[plugin_interface.__name__] = plugin_interface

    def load_plugins(self):
        for root, __, files in os.walk(self.plugins_folder):

            for filename in files:

                if filename.endswith(".py") and filename != "__init__.py":
                    module_name = filename[:-3]
                    file_path = os.path.join(root, filename)
                    spec = importlib.util.spec_from_file_location(
                        module_name, file_path
                    )
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    for attribute_name in dir(module):
                        attribute = getattr(module, attribute_name)

                        if not isinstance(attribute, type):
                            continue

                        for interface_class in self.plugin_interfaces:
                            if (
                                issubclass(attribute, interface_class)
                                and attribute is not interface_class
                            ):

                                if self.plugins_class_index.get(attribute.__name__):
                                    break

                                new_plugin = Plugin(
                                    cls_name=attribute.__name__,
                                    module_name=module_name,
                                    cls=attribute,
                                )

                                self.plugins_type_index[
                                    interface_class.__name__
                                ].append(new_plugin)

                                self.plugins_class_index[attribute.__name__] = (
                                    new_plugin
                                )

                                break

    def get_plugin_by_class_name(self, plugin_class_name: str) -> Plugin:
        return self.plugins_class_index.get(plugin_class_name)

    def get_plugins_by_interface_type(self, plugin_type: str) -> List[Plugin]:
        return self.plugins_type_index.get(plugin_type)

    def get_plugin_names_by_interface_name(self, interface_name: str) -> List[str]:
        return [
            plugin.class_name for plugin in self.plugins_type_index.get(interface_name)
        ]
