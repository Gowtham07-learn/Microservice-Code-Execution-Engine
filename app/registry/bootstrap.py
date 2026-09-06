"""Plugin discovery. Junior 1 registers PythonPlugin and CPlugin here.

The core stays language-agnostic: adding C++ means implementing LanguagePlugin
and calling registry.register(CppPlugin()) — no core execution changes.
"""

from app.core.interfaces.plugin_registry import PluginRegistry


def register_plugins(registry: PluginRegistry) -> None:
    _try_register(registry, "plugins.python.plugin", "PythonPlugin")
    _try_register(registry, "plugins.c.plugin", "CPlugin")


def _try_register(registry: PluginRegistry, module_name: str, class_name: str) -> None:
    try:
        module = __import__(module_name, fromlist=[class_name])
        plugin_cls = getattr(module, class_name)
        plugin = plugin_cls()
        if getattr(plugin, "PLUGIN_READY", False):
            registry.register(plugin)
    except (ImportError, AttributeError, TypeError, NotImplementedError):
        return
