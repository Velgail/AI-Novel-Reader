import importlib
import os
import sys
from core.logger_setup import setup_logger
from core.base_plugin import BasePlugin

logger = setup_logger()

class PluginManager:
    def __init__(self, plugin_directory="plugins"):
        self.plugin_directory = plugin_directory
        self.plugins = {}
        self.load_plugins()

    def load_plugins(self):
        if not os.path.isdir(self.plugin_directory):
            logger.warning(f"Plugin directory {self.plugin_directory} does not exist.")
            return

        sys.path.insert(0, self.plugin_directory)
        for filename in os.listdir(self.plugin_directory):
            if filename.endswith(".py") and filename != "__init__.py":
                plugin_name = filename[:-3]
                try:
                    module = importlib.import_module(plugin_name)
                    for attr in dir(module):
                        plugin_class = getattr(module, attr)
                        if isinstance(plugin_class, type) and issubclass(plugin_class, BasePlugin) and plugin_class is not BasePlugin:
                            self.plugins[plugin_name] = plugin_class()
                            logger.info(f"Loaded plugin: {plugin_name}")
                except Exception as e:
                    logger.error(f"Failed to load plugin {plugin_name}: {e}")

    def get_plugin(self, plugin_name):
        return self.plugins.get(plugin_name)

    def execute_plugin(self, plugin_name, *args, **kwargs):
        plugin = self.get_plugin(plugin_name)
        if plugin:
            try:
                plugin.execute(*args, **kwargs)
                logger.info(f"Executed plugin: {plugin_name}")
            except Exception as e:
                logger.error(f"Failed to execute plugin {plugin_name}: {e}")
        else:
            logger.warning(f"Plugin {plugin_name} not found.")
