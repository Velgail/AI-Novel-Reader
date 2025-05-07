class BasePlugin:
    def __init__(self, name):
        self.name = name

    def execute(self, *args, **kwargs):
        raise NotImplementedError("Execute method must be implemented by the plugin.")
