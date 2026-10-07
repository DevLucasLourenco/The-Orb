# Orb IA — IDEAS (backlog completo)

> **Todas** as ideias discutidas, do começo ao fim, com o status de cada uma. Nada é descartado
> aqui: o que não está no MVP fica guardado para depois. Todas respeitam o princípio 10 de
> [CONTEXT.md](CONTEXT.md) (o Orb só visualiza; a única porta de escrita é o Intrusive Thought).
> Escopo do MVP: [MVP.md](MVP.md).

Última atualização: 2026-10-06

**Status:** `MVP` = no escopo do primeiro MVP · `Próximo` = logo depois do MVP · `Backlog` =
guardado · `Pesquisa` = precisa ser investigado antes · `Decidido` = já está em CONTEXT/PROTOCOL.

---

## 1. Núcleo (telemetria e hospedagem)

| Ideia | Resumo | Status |
|---|---|---|
| Terminal nativo por CLI | Abrir um terminal real e chamar nele o CLI original (claude, codex, hermes), escolhido automaticamente pelo modelo do Alter Ego, no contexto do realm. **Nada de TUI criada do zero** | **MVP** (validado no Spike 1) |
| Telemetria paralela | Hooks + transcript → adapter → eventos universais | **MVP** |
| Nível 0 de pegada | Só ler o transcript, sem instalar nada | **MVP** |
| Nível 1 de pegada | Hooks observadores injetados **por sessão** via `--settings` (nunca no `settings.json` do Lucas): tempo real, aprovações, subagentes. Validado no Spike 3; transporte via `command` async + `curl` para um Orb travado não atrasar o agente | Próximo (validado, com restrições) |
| Receptor de hooks sempre responsivo | Processo mínimo que só enfileira e responde `{}` na hora, isolado do resto do Orb | Próximo |
| Eventos de hook ainda não exercitados | TaskCreated/Completed, Notification, PostToolUseFailure, PermissionDenied, StopFailure, Pre/PostCompact, CwdChanged | Pesquisa |
| Event Protocol versionado | Contrato único de eventos, estados e `fidelity` | **MVP** |
| Painel 2D de validação | Árvore Realm → Alter Ego → Subagente → Atividade, provando a telemetria | **MVP** |
| Adapter Codex | Observador de um **app-server próprio do Orb** (`codex app-server --listen ws://127.0.0.1:PORTA`) com a TUI nativa conectada por `codex --remote`; sem tocar no `config.toml`. Validado no Spike 4 com cliente programático | Próximo (validado, com restrições) |
| Adapter Hermes | Mesma interface; CLI **não instalado** nesta máquina, só pesquisa de documentação | Backlog |
| Verificar assinante passivo vs. aprovações do Codex | O que o servidor faz quando o observador ignora um `ServerRequest` de aprovação (crítico para o princípio 10) | Pesquisa (prioridade) |
| Classificador de comandos do Codex | Tabela declarativa que transforma `Get-Content`, `git`, `pytest` etc. em categorias (`read`, `execute`, `test`) | Próximo |
| Orb passa o modelo explicitamente ao Codex | O padrão do `config.toml` do Lucas (`gpt-6-luna`) não é aceito com conta ChatGPT; modelos reais: `gpt-5.6-sol/terra/luna` | Próximo |
| Diálogos da TUI são do Lucas | O Orb nunca responde atualização, confiança de diretório/hooks nem aprovações; detectar diálogos e avisar na UI | Decidido |
| Sessões do Codex grandes | Tail incremental a partir do fim (há rollouts de 145 MB) | Próximo |
| Adapters para outros CLIs | Gemini CLI, OpenCode, Cursor, qualquer modelo com CLI, agentes próprios, OpenAI Agents SDK | Backlog |
| Modo Observar | Ler sessões iniciadas fora do Orb (claude direto no terminal do Lucas) | Próximo |
| Modo Hospedar via stream JSON | Alternativa à TUI (stream estruturado) para quando a TUI não servir | Backlog |
| Chat espelhado | Painel que mostra a conversa a partir dos eventos | Próximo |
| Sessão visível por Alter Ego | Título da sessão sobre o personagem, subagentes agrupados | Pesquisa |
| Webhooks de saída do Hermes | Receber telemetria do Hermes direto por HTTP | Pesquisa |
| Fontes de vida real extras | Docker, Jira/Issues além de git, GitHub e CI | Backlog |

## 2. O mundo (Orb, Realm, Environment)

| Ideia | Resumo | Status |
|---|---|---|
| Orb como cidade | Mundo conceitual que contém os realms; foco do projeto é o 3D | **Decidido** |
| Realm = prédio, altura = LOC | Altura calculada, sempre ignorando o `.gitignore`, filtro de `.md` | **Decidido** |
| Escala comprimida (raiz/log) | Evitar skyline ilegível quando há repos de tamanhos muito diferentes | Pesquisa |
| Rooftop Room | Quartinho no teto com as 5 áreas obrigatórias (Dev, Testing, Research, Review, Task Board) | **Decidido** |
| Estilo temático por realm | TriSafe industrial, CLARA biblioteca, UTC CONECTA+ estação de comunicação | Backlog |
| Mapa/minimap | Visão geral rápida do Orb | Backlog |
| Cidade/campus como hub | Tela inicial com todos os realms e contagem de agentes | Próximo |

## 3. Câmera e controles

| Ideia | Resumo | Status |
|---|---|---|
| Câmera 3/4 de cima, livre | ~40–55° inicial, rotação, zoom, foco | Próximo |
| Controles de câmera | WASD, scroll, Q/E, botão direito orbitar, F focar, duplo clique seguir, ESC visão geral, 1–9 realms | Próximo |
| FREE CAM | Sem limite de inclinação, voar pelo ambiente | Backlog |
| Níveis de detalhe por zoom | Longe: resumo do realm. Médio: personagens. Perto: card detalhado e monitor com código passando | Próximo |
| Personagem "Manager" andando | Controle em terceira pessoa (descartado em favor do top-down; guardado) | Backlog |

## 4. Alter Ego e Mankind

| Ideia | Resumo | Status |
|---|---|---|
| Alter Ego persistente | Persona separada do provider; troca de motor sem mudar de personagem | **Decidido** |
| Subagentes como unidades temporárias | Nascem do pai, vão cumprir missão, voltam e somem | Próximo |
| Estados universais | THINKING, CODING, TESTING, WAITING, BLOCKED… | **MVP** (no painel 2D) |
| Personalidade / stats / nível (XP) | Calculados só com histórico real (testes, PRs, retrabalho, tokens, intervenções) | Backlog |
| Quests, conquistas, evolução de projeto | Camada de jogo | Backlog |
| Quadro de tarefas ligado a issues reais | Task Board alimentado por tickets | Backlog |
| Memorial | Subagentes aposentados deixam marca; linhagem de quem nasceu de quem | Backlog |
| Cerimônias | Commit como entrega, PR merged como celebração | Backlog |

## 5. Inner World e Intrusive Thoughts

| Ideia | Resumo | Status |
|---|---|---|
| Inner World | Ver o pensamento de cada IA; `fidelity` raw/summary/inferred | **Decidido** (implementar após telemetria básica) |
| "Mergulhar" no Alter Ego | Câmera entra e o cenário vira o mundo interno (plano como mapa mental, arquivos lidos como objetos, dúvidas como nós) | Backlog |
| Intrusive Thoughts | Usar um CLI = plantar um pensamento; evento `intrusive_thought` | **MVP** (detecção via transcript) |
| Visual do intrusive thought no 3D | Pensamento "chegando" ao Rooftop Room | Backlog |
| Stat de intervenções humanas | Intervenções por tarefa como métrica real | Backlog |
| Thinking quase vazio no Claude | ~88% dos blocos vêm sem texto; Inner World usa narração, plano e ferramentas | **Decidido** |

## 6. Camadas vivas (visualização de dados reais)

| Ideia | Resumo | Status |
|---|---|---|
| Janelas acesas e andares | Andares = módulos; janelas acendem onde houve edição recente | Próximo (1ª da fila) |
| Gate | Portão central: vê aprovações pendentes de todos os realms **e envia prompts** a qualquer Alter Ego (escreve no terminal dele; nunca aprova nem decide sozinho) | Próximo (2ª) |
| Team | Alter Ego principal + subagentes como equipe, agrupada e endereçável como um todo; subagentes dentro de subagentes | Próximo |
| Orb como centralizador de IAs | Terminal, Intrusive Thought e Gate como três portas para o mesmo terminal | **Decidido** |
| Chronicle | Replay da cidade no tempo, usando o log + histórico do git | Próximo (3ª) |
| Weather | CI verde = céu limpo, falhando = tempestade, testes falhando = rachaduras, parado = noite | Próximo (4ª) |
| Energy | Tokens e custo como recursos por realm e por Mankind | Próximo (5ª) |
| Archive | Memória do Alter Ego só para ver: contexto, skills, `CLAUDE.md`, memória; somente leitura, metadados por padrão | Próximo (6ª) |
| Estradas entre realms | Dependências entre projetos como estradas; agentes viajando | Backlog |
| Ciclo dia/noite ligado à atividade | Cidade acesa onde há trabalho, apagada quando parada | Backlog |
| Testes como integridade estrutural | Falhas viram rachaduras/andaimes | Backlog |
| Som ambiente | Sound design do trabalho (digitação, testes) | Backlog |

## 7. Interação e controle (sempre pelo terminal)

| Ideia | Resumo | Status |
|---|---|---|
| Menu de interação com o agente | Falar, mudar prioridade, pausar, criar subagente, ver terminal, ver diff, aprovar | Backlog (todo "controle" = escrita no terminal) |
| Enviar mensagem pelo painel | `terminal.write` → vira `intrusive_thought` com `channel: panel` | Próximo |
| Terminal cru como aba | A TUI original embutida no realm, ao lado do painel | **MVP** (é o próprio Terminal Host) |

## 8. Clientes

| Ideia | Resumo | Status |
|---|---|---|
| Cliente Godot 4 (3D) | Foco do produto | Próximo (após validar o terminal) |
| Cliente web (R3F/Three.js) | Prova rápida; também pode ser o fallback se embutir terminal no Godot for ruim | Pesquisa |
| Embutir terminal no Godot | godot-xterm exibindo bytes do Terminal Host em Python (opção B); validado em 2D e 3D | **Decidido** (Spike 2) |
| Monitor 3D no Rooftop Room | O terminal real como textura de um monitor dentro do prédio (`SubViewport` num quad); teclado encaminhado | **Decidido** (validado) |
| Clique do mouse no monitor 3D | Interagir clicando na tela do monitor (foco, seleção de texto) | Pesquisa |
| Glifos de caixa/bloco do terminal | `─ █ ▐` saem com espaços; desenhar esses glifos manualmente | Backlog (cosmético) |
| Vários monitores 3D ao mesmo tempo | Desempenho com um terminal por Alter Ego numa cena grande | Pesquisa |

---

## Ordem sugerida das camadas vivas

Janelas acesas → Gate → Chronicle → Weather → Energy → Archive. As quatro primeiras só
dependem de eventos já previstos no protocolo; Archive exige o leitor somente leitura e a
política de privacidade.

## Regra de ouro para este arquivo

Quando uma ideia é decidida e entra no plano, ela vai para CONTEXT.md/PROTOCOL.md **e continua
listada aqui** com o status atualizado. Nada é apagado.
