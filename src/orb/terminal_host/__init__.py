"""Terminal Host: o terminal real do Inner World (ADR 0004). Não conhece o domínio.
Providers (lista fixa): claude, codex, hermes, opencode."""
from .env import INHERITED_MARKERS, clean_env
from .launch import (MODEL_PREFIXES, PROVIDERS, InvalidLaunchValue, Launch, ProviderNotInstalled,
                     UnknownProvider, available_providers, resolve_provider)
from .terminal import HostedTerminal, default_shell, winpty_factory

__all__ = ["HostedTerminal", "INHERITED_MARKERS", "InvalidLaunchValue", "Launch", "MODEL_PREFIXES",
           "PROVIDERS", "ProviderNotInstalled", "UnknownProvider", "available_providers", "clean_env",
           "default_shell", "resolve_provider", "winpty_factory"]
