"""O terminal REAL de um Inner World: PowerShell numa pseudo-console (ConPTY), com o CLI chamado
dentro dele. O Orb não cria TUI: só abre, transporta bytes, redimensiona e encerra. Não interpreta o
que é digitado nem o que o CLI imprime (ADR 0004).
"""
from __future__ import annotations

import shutil
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol

from .env import clean_env
from .launch import PROVIDERS, Launch, ProviderNotInstalled, available_providers


class Pty(Protocol):
    def read(self, size: int) -> str: ...
    def write(self, data: str) -> Any: ...
    def isalive(self) -> bool: ...
    def setwinsize(self, rows: int, cols: int) -> Any: ...
    def terminate(self, force: bool = False) -> Any: ...


PtyFactory = Callable[[list[str], str, dict[str, str], tuple[int, int]], Pty]


def winpty_factory(argv: list[str], cwd: str, env: dict[str, str], dimensions: tuple[int, int]) -> Pty:
    from winpty import PtyProcess      # import tardio: os testes rodam sem ConPTY

    return PtyProcess.spawn(argv, cwd=cwd, env=env, dimensions=dimensions)


def default_shell() -> list[str]:
    return [shutil.which("pwsh") or "powershell.exe", "-NoLogo"]


@dataclass
class HostedTerminal:
    """Um terminal real. Com `launch`, o CLI é digitado nele automaticamente ao abrir."""
    cwd: str
    launch: Launch | None = None       # None = só o terminal, sem CLI
    cols: int = 120
    rows: int = 32
    on_output: Callable[[str], None] = lambda _data: None
    on_exit: Callable[[int | None], None] = lambda _code: None
    pty_factory: PtyFactory = winpty_factory
    check_installed: bool = True
    _proc: Pty | None = field(default=None, init=False, repr=False)
    _closed: threading.Event = field(default_factory=threading.Event, init=False, repr=False)

    def start(self) -> None:
        line = None
        if self.launch is not None:
            line = self.launch.line()      # valida antes de abrir qualquer processo
            if self.check_installed and not available_providers().get(self.launch.provider, False):
                raise ProviderNotInstalled(self.launch.provider)
        self._proc = self.pty_factory(default_shell(), self.cwd, clean_env(), (self.rows, self.cols))
        threading.Thread(target=self._read_loop, name="pty-reader", daemon=True).start()
        if line:
            self._proc.write(line + "\r")  # o shell enfileira: o CLI sobe quando ele estiver pronto

    def _read_loop(self) -> None:
        proc = self._proc
        assert proc is not None
        try:
            while not self._closed.is_set():
                data = proc.read(65536)
                if not data:
                    if not proc.isalive():
                        break
                    continue
                self.on_output(data)
        except Exception:  # noqa: BLE001 - EOF/falha do terminal não pode derrubar o servidor
            pass
        finally:
            code = getattr(proc, "exitstatus", None)
            self.on_exit(code if isinstance(code, int) else None)

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


__all__ = ["HostedTerminal", "PROVIDERS", "Pty", "PtyFactory", "default_shell", "winpty_factory"]
