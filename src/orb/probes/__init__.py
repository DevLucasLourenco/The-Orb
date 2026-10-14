"""Probes: leituras do mundo real (git, linhas de código…), só leitura (docs/ARCHITECTURE.md §3)."""
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

__all__ = ["MAX_FILE_BYTES", "Count", "Entry", "Filter", "count_lines", "fingerprint", "git_tracked_files", "list_countable"]
