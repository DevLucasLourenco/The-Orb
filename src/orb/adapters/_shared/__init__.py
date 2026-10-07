"""Peças genéricas compartilhadas pelos adapters (nenhuma conhece um provider)."""
from .base import (Capabilities, EventFactory, RealmOf, alter_ego_id, iso_from_ms, norm_path, now_iso,
                   realm_id_for, realm_resolver, single_realm, stable_key)
from .commands import classify_command
from .jsonl import JsonlFollower
from .sqlite import connect_readonly, table_columns

__all__ = ["Capabilities", "EventFactory", "JsonlFollower", "alter_ego_id", "classify_command",
           "connect_readonly", "iso_from_ms", "norm_path", "now_iso", "RealmOf", "realm_id_for",
           "realm_resolver", "single_realm", "stable_key", "table_columns"]
