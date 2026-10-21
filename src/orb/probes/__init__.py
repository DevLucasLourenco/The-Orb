"""Probes: leituras do mundo real (git, linhas de código…), só leitura (docs/ARCHITECTURE.md §3)."""
from .changes import (
    Change,
    ChangeSet,
    changes_fingerprint,
    git_changes,
    parse_numstat,
    parse_status,
)
from .commits import CommitQuery, commits_fingerprint, git_commits, main_branch
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

__all__ = ["MAX_FILE_BYTES", "Change", "ChangeSet", "CommitQuery", "Count", "Entry", "Filter", "changes_fingerprint", "commits_fingerprint", "count_lines", "fingerprint", "git_changes", "git_commits", "git_tracked_files", "list_countable", "main_branch", "parse_numstat", "parse_status"]
