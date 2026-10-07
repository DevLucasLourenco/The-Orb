"""Terminal Host: abre um terminal REAL (PowerShell) numa pseudo-console e chama o CLI do agente.

O Orb não cria TUI nenhuma: o terminal é o do sistema, e o CLI (claude/codex/hermes) é o original.
Este módulo só abre, transporta bytes, redimensiona e encerra; não interpreta o que é digitado
nem o que o CLI imprime (ver ARCHITECTURE.md).
"""
from __future__ import annotations

import os
import shutil
import threading
from dataclasses import dataclass, field
from typing import Callable

from winpty import PtyProcess

# Provider -> executável. É uma lista fixa: o Orb nunca executa um comando arbitrário.
PROVIDERS: dict[str, str] = {"claude": "claude", "codex": "codex", "hermes": "hermes"}

# Prefixos de modelo -> provider (para escolher o CLI automaticamente pelo modelo do Alter Ego).
_MODEL_PREFIXES: tuple[tuple[str, str], ...] = (
    ("claude", "claude"), ("opus", "claude"), ("sonnet", "claude"), ("haiku", "claude"), ("fable", "claude"),
    ("gpt", "codex"), ("codex", "codex"), ("o1", "codex"), ("o3", "codex"), ("o4", "codex"),
    ("hermes", "hermes"),
)


class UnknownProvider(ValueError):
    pass


class ProviderNotInstalled(RuntimeError):
    pass


def resolve_provider(provider: str | None = None, model: str | None = None) -> str:
    """Escolhe o provider: explícito, senão deduzido do nome do modelo."""
    if provider:
        if provider not in PROVIDERS:
            raise UnknownProvider(provider)
        return provider
    name = (model or "").lower().strip()
    for prefix, resolved in _MODEL_PREFIXES:
        if name.startswith(prefix):
            return resolved
    raise UnknownProvider(model or "")


def available_providers() -> dict[str, bool]:
    """Quais CLIs estão instalados nesta máquina."""
    return {name: shutil.which(exe) is not None for name, exe in PROVIDERS.items()}


def default_shell() -> list[str]:
    return [shutil.which("pwsh") or "powershell.exe", "-NoLogo"]


def build_cli_line(provider: str, session_id: str | None = None, session_name: str | None = None) -> str:
    """Linha de comando digitada no terminal. Só vem de valores controlados pelo Orb."""
    if provider not in PROVIDERS:
        raise UnknownProvider(provider)
    parts = [PROVIDERS[provider]]
    if provider == "claude":
        if session_id:
            parts += ["--session-id", session_id]
        if session_name:
            parts += ["-n", session_name]
    return " ".join(parts)


# Marcadores que o Claude Code injeta no ambiente dos filhos. Se o Orb for iniciado de dentro de
# uma sessão do Claude, herdá-los mudaria o comportamento do CLI hospedado (ex.: não gravar
# transcript). Removê-los garante que ele rode como se aberto pelo Lucas. Configurações do
# usuário (ANTHROPIC_*, CLAUDE_CODE_USE_*, etc.) são preservadas.
_INHERITED_MARKERS = {
    "CLAUDECODE", "CLAUDE_PID", "CLAUDE_EFFORT", "AI_AGENT",
    "CLAUDE_CODE_CHILD_SESSION", "CLAUDE_CODE_SESSION_ID", "CLAUDE_CODE_HOST_SESSION_ID",
    "CLAUDE_CODE_SESSION_ATTENDED", "CLAUDE_CODE_ENTRYPOINT", "CLAUDE_CODE_EXECPATH",
    "CLAUDE_CODE_SIMPLE", "CLAUDE_CODE_DISABLE_CRON", "CLAUDE_CODE_DISABLE_TERMINAL_TITLE",
    "CLAUDE_CODE_MESSAGING_SOCKET", "CLAUDE_CODE_MESSAGING_TOKEN", "CLAUDE_CODE_TERMINAL_MCP_TOOLS",
    "CLAUDE_CODE_SDK_HAS_HOST_AUTH_REFRESH", "CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING",
    "CLAUDE_CODE_EMIT_TOOL_USE_SUMMARIES", "CLAUDE_CODE_REPORT_FINDINGS",
    "CLAUDE_CODE_ENABLE_ASK_USER_QUESTION_TOOL", "CLAUDE_CODE_DESKTOP_APP_VERSION",
    "CLAUDE_PREVIEW_CLASSIFIER_FLOOR", "CLAUDE_AGENT_SDK_VERSION", "CLAUDE_AGENT_SDK_MCP_NO_PREFIX",
}


def clean_env(env: dict[str, str] | None = None) -> dict[str, str]:
    source = dict(os.environ if env is None else env)
    return {k: v for k, v in source.items() if k not in _INHERITED_MARKERS}


@dataclass
class HostedTerminal:
    """Um terminal real. Se `provider` for dado, o CLI é chamado dentro dele automaticamente."""
    cwd: str
    provider: str | None = None     # None = só o terminal, sem chamar nenhum CLI
    cols: int = 120
    rows: int = 32
    session_id: str | None = None   # só claude: o Orb atribui o id, então sabe qual é o transcript
    session_name: str | None = None
    on_output: Callable[[str], None] = lambda _data: None
    on_exit: Callable[[int | None], None] = lambda _code: None
    _proc: PtyProcess | None = field(default=None, init=False, repr=False)
    _reader: threading.Thread | None = field(default=None, init=False, repr=False)
    _closed: threading.Event = field(default_factory=threading.Event, init=False, repr=False)

    def start(self) -> None:
        cli_line = None
        if self.provider is not None:
            if not available_providers().get(self.provider, False) and self.provider in PROVIDERS:
                raise ProviderNotInstalled(self.provider)
            cli_line = build_cli_line(self.provider, self.session_id, self.session_name)
        self._proc = PtyProcess.spawn(default_shell(), cwd=self.cwd, env=clean_env(),
                                      dimensions=(self.rows, self.cols))
        self._reader = threading.Thread(target=self._read_loop, name="pty-reader", daemon=True)
        self._reader.start()
        if cli_line:
            # O terminal enfileira a entrada: o CLI sobe assim que o shell estiver pronto.
            self._proc.write(cli_line + "\r")

    def _read_loop(self) -> None:
        assert self._proc is not None
        try:
            while not self._closed.is_set():
                data = self._proc.read(65536)
                if not data:
                    if not self._proc.isalive():
                        break
                    continue
                self.on_output(data)
        except EOFError:
            pass
        except Exception:  # noqa: BLE001 - falha do terminal não pode derrubar o servidor
            pass
        finally:
            code = None
            try:
                code = self._proc.exitstatus
            except Exception:  # noqa: BLE001
                pass
            self.on_exit(code)

    def write(self, data: str) -> None:
        if self._proc is not None and self._proc.isalive():
            self._proc.write(data)

    def resize(self, cols: int, rows: int) -> None:
        self.cols, self.rows = cols, rows
        if self._proc is not None and self._proc.isalive():
            self._proc.setwinsize(rows, cols)

    def alive(self) -> bool:
        return self._proc is not None and self._proc.isalive()

    def close(self) -> None:
        self._closed.set()
        if self._proc is not None:
            try:
                if self._proc.isalive():
                    self._proc.terminate(force=True)
            except Exception:  # noqa: BLE001
                pass
