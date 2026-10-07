"""Que CLI chamar e com que linha de comando (lista FIXA de executáveis).

A linha é DIGITADA num shell real, então só contém valores controlados pelo Orb e validados aqui:
nome do executável da tabela, UUID, nome de sessão e modelo com caracteres restritos.
"""
from __future__ import annotations

import re
import shutil
import uuid
from dataclasses import dataclass


class UnknownProvider(ValueError):
    pass


class ProviderNotInstalled(RuntimeError):
    pass


class InvalidLaunchValue(ValueError):
    pass


# Provider -> executável. O Orb nunca executa um comando arbitrário.
PROVIDERS: dict[str, str] = {"claude": "claude", "codex": "codex", "hermes": "hermes"}

# Prefixo do modelo -> provider (escolha automática pelo modelo da sessão).
MODEL_PREFIXES: tuple[tuple[str, str], ...] = (
    ("claude", "claude"), ("opus", "claude"), ("sonnet", "claude"), ("haiku", "claude"), ("fable", "claude"),
    ("gpt", "codex"), ("codex", "codex"), ("o1", "codex"), ("o3", "codex"), ("o4", "codex"),
    ("hermes", "hermes"),
)

_SAFE_MODEL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/\-\[\]]{0,79}$")
_SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._\-]{0,63}$")
_SAFE_URL = re.compile(r"^ws://127\.0\.0\.1:\d{2,5}$")


def resolve_provider(provider: str | None = None, model: str | None = None) -> str:
    """Provider explícito vence; senão é deduzido do nome do modelo."""
    if provider:
        if provider not in PROVIDERS:
            raise UnknownProvider(provider)
        return provider
    name = (model or "").lower().strip()
    for prefix, resolved in MODEL_PREFIXES:
        if name.startswith(prefix):
            return resolved
    raise UnknownProvider(model or "")


def available_providers() -> dict[str, bool]:
    """Quais CLIs estão instalados nesta máquina."""
    return {name: shutil.which(exe) is not None for name, exe in PROVIDERS.items()}


def _check(value: str | None, pattern: re.Pattern[str], what: str) -> str | None:
    if value is None or value == "":
        return None
    if not pattern.match(value):
        raise InvalidLaunchValue(f"{what} inválido: {value!r}")
    return value


@dataclass(frozen=True)
class Launch:
    """Como abrir uma sessão (um Alter Ego) de um provider."""
    provider: str
    model: str | None = None
    session_id: str | None = None      # Claude: o Orb escolhe o id e sabe qual é o transcript
    session_name: str | None = None
    resume: bool = False               # reabrir a sessão `session_id` (reabrir um Alter Ego)
    remote_url: str | None = None      # Codex nível 1: app-server próprio do Orb

    def line(self) -> str:
        if self.provider not in PROVIDERS:
            raise UnknownProvider(self.provider)
        model = _check(self.model, _SAFE_MODEL, "modelo")
        name = _check(self.session_name, _SAFE_NAME, "nome de sessão")
        if self.session_id is not None:
            try:
                session_id = str(uuid.UUID(self.session_id))
            except ValueError as exc:
                raise InvalidLaunchValue(f"id de sessão inválido: {self.session_id!r}") from exc
        else:
            session_id = None
        parts = [PROVIDERS[self.provider]]
        if self.provider == "claude":
            if session_id and self.resume:
                parts += ["--resume", session_id]
            elif session_id:
                parts += ["--session-id", session_id]
            if name:
                parts += ["-n", name]
            if model:
                parts += ["--model", model]
        elif self.provider == "codex":
            if self.resume and session_id:
                parts += ["resume", session_id]
            remote = _check(self.remote_url, _SAFE_URL, "endereço do app-server")
            if remote:
                parts += ["--remote", remote]
            if model:
                parts += ["-m", model]      # o padrão do config.toml do Lucas pode não ser aceito
        elif self.provider == "hermes":
            if model:
                parts += ["-m", model]
        return " ".join(parts)
