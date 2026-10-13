# 01: O mundo calcula o tempo

Status: implementado
Blocked by: None (can start immediately)
Origem: R47, R31, R7; D-044, D-045, D-050, D-086
Spec: [../spec.md](../spec.md)

## O que construir

O Lucas vê "dormindo" e o subagente "sem sinal" decididos pelo servidor, iguais em qualquer
cliente. O mundo passa a devolver o estado para uma hora dada e, com uma tabela de limites, deriva o
que depende do tempo; o cliente para de calcular e só desenha. O subagente sem sinal deixa de sumir:
fica cinza translúcido, sem halo e com o ícone de sinal cortado.

## Critérios de aceite

- [x] O estado do mundo é pedido com uma hora; o mundo não lê relógio nenhum.
- [x] Os limites (dormindo 15 min, sem sinal 5 min) ficam numa tabela de regras do mundo.
- [x] Sessão parada há mais de 15 min aparece "dormindo" no estado do mundo; o cliente só desenha.
- [x] Subagente sem atividade há 5 min e sem sinal de fim aparece "sem sinal" (não some); o opencode continua cinza sólido com halo.
- [x] O cliente não tem mais nenhum cálculo de tempo para esses estados.
- [x] O servidor envia o estado com a hora dele e reavalia periodicamente, sem esperar evento novo.

## Testes

Ponto de teste: o mundo (eventos sintéticos + horas diferentes → estados).

## Pronto quando

- Critérios acima cumpridos, com testes pelo ponto de teste indicado (D-099), sem rede e sem CLI real.
- Documentação atualizada (regra, VISUAL.md, adapter ou arquitetura, conforme o caso) e a coluna
  Situação das regras revista em RULES.md.
- Invariantes intactos: só telemetria real (R12), somente leitura (R16), nenhum diálogo respondido
  (ADR 0006), nenhum token (R38), nenhuma credencial lida, nenhuma fixture real versionada.
- Uma branch e um PR para este ticket (D-114).

## Comments

Implementado em 2026-10-09 na branch `ticket/01-mundo-calcula-o-tempo`; falta a revisão do Lucas e o merge.

**O que ficou decidido na implementação, sem estar escrito antes** (agora em DECISIONS.md, rodada
Q-T01-1 a 5; **confirmadas pelo Lucas em D-119 a D-123**): o "sem sinal" não segura o líder em `DELEGATING`; qualquer evento
do subagente é atividade; os totais não contam os sem sinal; líder dormindo não esconde a Team;
só dorme quem está `IDLE`. Também: a hora do snapshot precisa ter fuso e o snapshot do servidor
leva `generated_at`; data ilegível no evento não quebra nada (o mundo não afirma nada).

**Revisão (/code-review, padrões e spec), tratada neste ticket:** a regra "subagente ativo e com
sinal" ficou só no mundo (`active_subagents`), o cliente deixou de calculá-la; os subagentes não somem
com o líder dormindo; a chave do que só o tempo muda (`time_key`) mora no mundo; o laço do servidor
tem teste; as cores do "sem sinal" estão em VISUAL.md §5.

**O critério "o opencode continua cinza sólido com halo" só vale depois do ticket 05** (R30): hoje o
opencode é azul. Nada no ticket 01 mexe na cor dos providers; o "sem sinal" é cinza neutro,
translúcido, sem halo e com o ícone, então já se distingue do opencode (sólido, com halo).

**Verificação ao vivo (2026-10-09, dados reais):** console do navegador sem erros; o canal `/world`
entrega `asleep`, `no_signal`, `active_subagents` e `generated_at`; sem nenhum evento novo o servidor
empurrou o mundo com `no_signal` subindo de 0 a 117 e os subagentes ativos de Mankind caindo de 119
a 3. No 3D (realm ATIA), os dois subagentes sem sinal aparecem cinza translúcido, sem halo e com o
ícone de sinal cortado, ao lado do líder.

**Observação para o ticket 06:** o primeiro poll com os 19 realms demora mais de 100 s e aplica
~10 mil eventos antes de aparecer a primeira sessão (já era assim; é o que a leitura em duas
camadas, R48, resolve). Outra: o ritmo de leitura do servidor continua em 500 ms (D-087 pede 250 ms, ticket 06).

**Achado ao vivo (para o ticket 02 ou 03, não é deste):** os eventos de abertura de sessão e de
subagente do Claude e do Hermes não trazem hora do evento e usam a **hora da leitura**. Um subagente
descoberto agora parece "recém-ativo" mesmo que tenha começado horas atrás, e só vira "sem sinal" 5 min
depois. Na máquina do Lucas, 117 dos 120 subagentes ativos ficaram "sem sinal" 5 min depois do
primeiro poll (a maioria, subagentes antigos que nunca avisam o fim). Com R7 ("não some"), o 3D vai
mostrar esses 117 em cinza até o ticket 13 limitar a 8 por área e mostrar "+N".

