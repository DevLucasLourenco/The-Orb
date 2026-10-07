"""Core: o mundo puro (docs/ARCHITECTURE.md §3). Só depende do Protocol."""
from .rules import AREA_BY_STATE, area_for
from .world import AlterEgo, Subagent, World

__all__ = ["AREA_BY_STATE", "AlterEgo", "Subagent", "World", "area_for"]
