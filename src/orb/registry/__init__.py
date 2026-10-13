"""Registro local do Orb (R36, D-062) e preferências (R29): o que é do próprio Orb, na pasta dele."""
from .paths import orb_home
from .preferences import (
    PREFERENCES_FILE,
    SETTINGS,
    Preferences,
    PreferencesFile,
    Setting,
)
from .store import REGISTRY_FILE, LocalRegistry

__all__ = ["PREFERENCES_FILE", "REGISTRY_FILE", "SETTINGS", "LocalRegistry", "Preferences", "PreferencesFile", "Setting", "orb_home"]
