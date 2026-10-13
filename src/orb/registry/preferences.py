"""O arquivo de preferências do Orb (R29, D-030, D-032): JSON na pasta do próprio Orb, nunca nos providers.

Quem edita é a tela de configurações; nada vem de linha de comando. As opções numéricas ficam numa tabela
(`SETTINGS`): a tela é montada a partir dela, então os tickets 09 (filtro de linhas) e 11 (x das janelas) só
acrescentam linhas. Opções que esta versão não conhece são guardadas como estão (`extra`) e voltam no próximo
salvamento: um Orb mais antigo não apaga a opção de um mais novo.

Arquivo ilegível não derruba nada: valem os padrões, `error` diz o motivo e o arquivo é guardado ao lado
(`.bad`) antes de o próximo salvamento escrever por cima.
"""
from __future__ import annotations

import json
import math
import os
import shutil
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

PREFERENCES_FILE = "preferences.json"
VERSION = 1


@dataclass(frozen=True)
class Setting:
    """Uma opção numérica da tela de configurações."""
    key: str
    label: str
    unit: str
    default: float
    minimum: float
    maximum: float
    kind: str = "number"          # como a tela desenha a opção; os tickets 09 e 11 acrescentam outros tipos aqui


SETTINGS: tuple[Setting, ...] = (
    Setting("recent_days", "Sessões recentes na sala", "dias", 10, 1, 365),      # R28a, D-027
)
_BY_KEY = {setting.key: setting for setting in SETTINGS}


def _number(setting: Setting, value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{setting.label}: precisa ser um número")
    if not setting.minimum <= value <= setting.maximum:
        raise ValueError(f"{setting.label}: entre {setting.minimum:g} e {setting.maximum:g} {setting.unit}")
    return value


def _paths(value: Any) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
        raise ValueError("realms escondidos: precisa ser uma lista")  # noqa: TRY004 - todo valor inválido é ValueError
    return tuple(sorted({item for item in value if isinstance(item, str) and item}))


@dataclass(frozen=True)
class Preferences:
    hidden_realms: tuple[str, ...] = ()          # projetos escondidos da cidade (R3c), pelo caminho normalizado
    options: Mapping[str, float] = field(default_factory=lambda: {s.key: s.default for s in SETTINGS})   # uma por linha de SETTINGS
    extra: Mapping[str, Any] = field(default_factory=dict)

    @property
    def recent_days(self) -> float:
        return self.options["recent_days"]

    @property
    def recent_seconds(self) -> float:
        return self.recent_days * 24 * 3600

    def updated(self, /, **changes: Any) -> Preferences:
        """Uma cópia com as mudanças; valor fora da faixa ou opção desconhecida levanta `ValueError`."""
        out = self
        for key, value in changes.items():
            if key == "hidden_realms":
                out = replace(out, hidden_realms=_paths(value))
            elif key in _BY_KEY:
                out = replace(out, options={**out.options, key: _number(_BY_KEY[key], value)})
            else:
                raise ValueError(f"opção desconhecida: {key}")
        return out

    def as_dict(self) -> dict[str, Any]:
        return {**self.extra, "version": VERSION, "hidden_realms": list(self.hidden_realms), **self.options}


class PreferencesFile:
    """Lê e grava `preferences.json` na pasta do Orb. `error` guarda o último problema de leitura (ou None)."""

    def __init__(self, folder: Path) -> None:
        self.path = Path(folder) / PREFERENCES_FILE
        self.error: str | None = None

    def load(self) -> Preferences:
        self.error = None
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return Preferences()
        except (OSError, ValueError) as exc:
            # Sem o texto do erro do sistema: ele traz o caminho local e vai até a tela.
            detail = type(exc).__name__ if isinstance(exc, OSError) else f"{type(exc).__name__}: {exc}"
            self.error = f"preferências ilegíveis, valem os padrões: {detail}"
            return Preferences()
        if not isinstance(raw, dict):
            self.error = "preferências ilegíveis, valem os padrões: o arquivo não é um objeto"
            return Preferences()
        known = {"version", "hidden_realms", *_BY_KEY}
        prefs = Preferences(extra={k: v for k, v in raw.items() if k not in known})
        ignored = []
        for key in ("hidden_realms", *_BY_KEY):
            if key in raw:
                try:
                    prefs = prefs.updated(**{key: raw[key]})
                except ValueError:
                    ignored.append(key)        # valor inválido: fica o padrão daquela opção, as outras valem
        if ignored:
            self.error = f"valor inválido no arquivo, vale o padrão: {', '.join(ignored)}"
        return prefs

    def save(self, prefs: Preferences) -> None:
        """Grava de uma vez (arquivo temporário e troca): nunca fica um arquivo pela metade."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.error and self.path.is_file():
            shutil.copy2(self.path, self.path.with_name(PREFERENCES_FILE + ".bad"))
        temp = self.path.with_name(PREFERENCES_FILE + ".tmp")
        try:
            temp.write_text(json.dumps(prefs.as_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(temp, self.path)
        finally:
            temp.unlink(missing_ok=True)       # se a troca falhou, não deixa o temporário para trás
        self.error = None
