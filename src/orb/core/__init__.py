"""Core: o mundo puro (docs/ARCHITECTURE.md §3). Só depende do Protocol."""
from .names import NAMES, NameBag, NameBook, NameSource
from .rules import AREA_BY_STATE, area_for
from .world import AlterEgo, Subagent, World

__all__ = ["AREA_BY_STATE", "NAMES", "AlterEgo", "NameBag", "NameBook", "NameSource", "Subagent", "World", "area_for"]
