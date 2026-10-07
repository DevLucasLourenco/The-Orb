"""Adapters: um por provider (claude, codex, hermes). Leem a fonte nativa, somente leitura, e
produzem eventos com o nativo intacto + sinal de mundo + entrada de Inner World (ADR 0002).
Adapters não importam uns aos outros; o que compartilham é genérico e fica em `_shared`."""
