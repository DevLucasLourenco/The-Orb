"""A pasta do Orb: onde ficam o registro local (R36) e, depois, o arquivo de preferências (R29)."""
from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path

FOLDER_NAME = "the-orb"


def orb_home(env: Mapping[str, str] | None = None, home: Path | None = None) -> Path:
    """`%LOCALAPPDATA%\the-orb` no Windows; fora dele, `$XDG_DATA_HOME/the-orb` ou `~/.local/share/the-orb`.
    Ambiente e home entram por parâmetro (testes nunca tocam a pasta real); a pasta só é criada por quem grava nela."""
    env = os.environ if env is None else env
    if env.get("LOCALAPPDATA"):
        return Path(env["LOCALAPPDATA"]) / FOLDER_NAME
    if env.get("XDG_DATA_HOME"):
        return Path(env["XDG_DATA_HOME"]) / FOLDER_NAME
    return (home or Path.home()) / ".local" / "share" / FOLDER_NAME
