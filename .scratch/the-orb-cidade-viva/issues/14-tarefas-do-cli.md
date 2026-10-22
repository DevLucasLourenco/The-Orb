# 14: Tarefas do CLI

Status: ready-for-agent
Blocked by: 09
Origem: R50, R49; D-093, D-097
Spec: [../spec.md](../spec.md)

## O que construir

O overview mostra o progresso da tarefa de cada sessão ("7 de 12") a partir da lista que o próprio
CLI mantém, e a área Task Board mostra as tarefas concluídas. O rótulo do prédio mostra as tarefas
abertas. Sem lista gravada pelo provider, nada aparece.

## Critérios de aceite

- [x] Formato da lista de tarefas levantado só pela estrutura em cada CLI (TodoWrite do Claude, plano do Codex, `todowrite` do opencode; Hermes se houver) e registrado nos documentos dos adapters.
- [x] Sinal `tasks.updated` no protocolo 0.3, produzido pelos adapters que têm a lista.
- [x] Overview: "concluídas de total" e uma barra por sessão.
- [x] Task Board: as tarefas concluídas da sessão.
- [x] Rótulo do prédio: tarefas abertas, quando houver dado.
- [x] Nada estimado: sem lista, nenhum progresso.

## Testes

Ponto de teste: os leitores dos CLIs (amostras sintéticas → `tasks.updated`) e o mundo.

## Pronto quando

- Critérios acima cumpridos, com testes pelo ponto de teste indicado (D-099), sem rede e sem CLI real.
- Documentação atualizada (regra, VISUAL.md, adapter ou arquitetura, conforme o caso) e a coluna
  Situação das regras revista em RULES.md.
- Invariantes intactos: só telemetria real (R12), somente leitura (R16), nenhum diálogo respondido
  (ADR 0006), nenhum token (R38), nenhuma credencial lida, nenhuma fixture real versionada.
- Uma branch e um PR para este ticket (D-114).

## Comments

- **Implementação (2026-10-22):** sinal `tasks.updated` (protocolo 0.3), leitura comum em `adapters/_shared/tasks.py`, leitores do `TodoWrite` (Claude), do `todowrite` (opencode) e do `turn/plan/updated` (app-server do Codex), `core/tasks.py` (resumo do realm e Task Board) e o cliente (linha "tarefas" no cartão, tarefas abertas no rótulo e quadro sobre o Task Board).
- **Levantamento só pela estrutura:** opencode (18 blocos `todowrite`, chaves e valores de `status`); Claude e Codex nos rollouts: nenhuma lista vista nesta máquina; Hermes: nenhuma ferramenta de lista entre as chamadas. O formato do Claude (`TodoWrite`) vem da documentação oficial e o do Codex do esquema do app-server; está nos documentos de adapter com a confiança de cada um.
- **Verificado:** suíte inteira; no preview, com um snapshot feito de eventos sintéticos: "7 de 7" e "2 de 5" nos cartões, "3 tarefas abertas" no rótulo, o quadro com 5 concluídas e "+4"; sessão sem lista sem a linha. O 404 e o erro de JSON do console vêm da página de prévia (sem `/config` nem ícone), não do app.
- **Não verificado:** nenhuma sessão ou CLI real; os leitores só foram exercitados com amostras sintéticas; `TaskCreate`/`TaskUpdate` do Claude, o plano do Codex nos rollouts e o Hermes não têm leitor (Q-T14-1, Q-T14-3). As decisões Q-T14-1 a Q-T14-9 aguardam o Lucas.
