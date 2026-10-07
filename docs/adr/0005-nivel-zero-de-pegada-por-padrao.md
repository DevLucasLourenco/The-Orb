# Nível 0 de pegada por padrão; nível 1 só por sessão

Status: aceita (2026-10-06, Spikes 3 e 4)

Por padrão o Orb só **lê** o que o provider já grava (transcript do Claude, rollout do Codex).
Observação em tempo real (nível 1) é opcional por Alter Ego e **nunca** altera a configuração do
Lucas: no Claude, hooks injetados só naquela sessão com `claude --settings`; no Codex, um
app-server próprio do Orb com a TUI conectada por `codex --remote` e um observador que nunca
responde pedidos do servidor.

## Opções consideradas

- **Hooks no `settings.json` / `config.toml` do Lucas:** muda o ambiente dele para todas as
  sessões; no Codex ainda exige confiança do usuário.
- **Hooks `http` síncronos:** medido no Spike 3: um Orb travado atrasou o agente de ~7 s para
  21,5 s. Por isso o transporte do nível 1 do Claude é hook `command` assíncrono com `curl` de
  timeout curto, para um receptor mínimo que só enfileira.
