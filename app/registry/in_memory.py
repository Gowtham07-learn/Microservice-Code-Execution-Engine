from app.core.interfaces.language_plugin import LanguagePlugin
from app.core.interfaces.plugin_registry import PluginRegistry


class InMemoryPluginRegistry(PluginRegistry):
    def __init__(self) -> None:
        self._plugins: dict[str, LanguagePlugin] = {}

    def register(self, plugin: LanguagePlugin) -> None:
        key = plugin.language().strip().lower()
        self._plugins[key] = plugin

    def get(self, language: str) -> LanguagePlugin | None:
        return self._plugins.get(language.strip().lower())

    def list_plugins(self) -> list[LanguagePlugin]:
        return list(self._plugins.values())
