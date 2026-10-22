"""Peças genéricas compartilhadas pelos adapters (nenhuma conhece um provider)."""
from .base import (Capabilities, EventFactory, RealmOf, alter_ego_id, iso_from_ms, norm_path, now_iso,
                   realm_id_for, realm_resolver, single_realm, stable_key)
from .commands import classify_command, exit_code_of, is_git_commit, result_signal
from .index import SessionIndex, SessionMeta, iso_from_seconds
from .jsonl import JsonlFollower
from .sqlite import connect_readonly, table_columns
from .tasks import native_pairs, tasks_signal

__all__ = ["Capabilities", "EventFactory", "JsonlFollower", "SessionIndex", "SessionMeta", "alter_ego_id", "classify_command",
           "connect_readonly", "exit_code_of", "is_git_commit", "iso_from_ms", "iso_from_seconds", "native_pairs", "norm_path", "now_iso", "RealmOf", "realm_id_for",
           "realm_resolver", "result_signal", "single_realm", "stable_key", "table_columns", "tasks_signal"]
