"""Probes: leituras do mundo real (git, linhas de código…), só leitura (docs/ARCHITECTURE.md §3)."""
from .changes import (
    Change,
    ChangeSet,
    changes_fingerprint,
    git_changes,
    parse_numstat,
    parse_status,
)
from .lines import (
    MAX_FILE_BYTES,
    Count,
    Entry,
    Filter,
    count_lines,
    fingerprint,
    git_tracked_files,
    list_countable,
)

__all__ = ["MAX_FILE_BYTES", "Change", "ChangeSet", "Count", "Entry", "Filter", "changes_fingerprint", "count_lines", "fingerprint", "git_changes", "git_tracked_files", "list_countable", "parse_numstat", "parse_status"]
