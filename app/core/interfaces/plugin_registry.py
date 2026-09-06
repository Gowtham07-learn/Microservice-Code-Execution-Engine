from abc import ABC, abstractmethod

from app.core.interfaces.language_plugin import LanguagePlugin


class PluginRegistry(ABC):
    """Language-agnostic plugin lookup. Supported languages come from registration."""

    @abstractmethod
    def register(self, plugin: LanguagePlugin) -> None:
        """Register or replace a plugin by its language() id."""

    @abstractmethod
    def get(self, language: str) -> LanguagePlugin | None:
        """Return the plugin for a language id, or None if unsupported."""

    @abstractmethod
    def list_plugins(self) -> list[LanguagePlugin]:
        """Return all registered plugins."""
