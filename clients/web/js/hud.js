// A camada 2D sobre o mundo: números de Mankind, lista de realms e o overview do realm.
import { STATE_LABEL, ago, el, isAsleep, metricsText, provider, sessionTitle, tokens } from "./providers.js";

export function summarize(realm) {
  const egos = realm.alter_egos || [];
  const awake = egos.filter((e) => !isAsleep(e));
  return {
    sessions: egos.length,
    active: awake.filter((e) => !["IDLE", "COMPLETED"].includes(e.state)).length,
    waiting: egos.filter((e) => e.waiting.length || e.state === "WAITING").length,
    subagents: egos.reduce((n, e) => n + e.active_subagents, 0),
    tokens: egos.reduce((n, e) => n + (e.usage.input_tokens || 0) + (e.usage.output_tokens || 0), 0),
    cost: egos.reduce((n, e) => n + (e.usage.cost_usd || 0), 0),
  };
}

function stat(label, value, cls = "") {
  const s = el("div", `stat ${cls}`);
  s.append(el("b", null, value), el("span", null, label));
  return s;
}

export function renderTopbar(world) {
  const totals = world.realms.map(summarize).reduce((a, s) => {
    for (const k of Object.keys(s)) a[k] = (a[k] || 0) + s[k];
    return a;
  }, {});
  const box = document.getElementById("mankind");
  box.replaceChildren(
    stat("realms", world.realms.length),
    stat("sessões", totals.sessions || 0),
    stat("ativas", totals.active || 0),
    stat("esperando você", totals.waiting || 0, totals.waiting ? "wait" : ""),
    stat("subagentes", totals.subagents || 0),
    stat("tokens", tokens({ input_tokens: totals.tokens || 0 }).replace(" tok", "")),
  );
}

// Só redesenha quando o conteúdo muda (o mundo chega várias vezes por segundo).
const lastDrawn = {};
function changed(slot, value) {
  const key = JSON.stringify(value);
  if (lastDrawn[slot] === key) return false;
  lastDrawn[slot] = key;
  return true;
}

export function renderRealmList(world, selected, onSelect) {
  const nav = document.getElementById("realms");
  const shape = world.realms.map((r) => [r.id, r.name, r.alter_egos.map((e) => [e.provider, e.state, e.waiting.length, isAsleep(e)])]);
  if (!changed("realms", [selected, shape])) return;
  nav.replaceChildren(...world.realms.map((realm, i) => {
    const s = summarize(realm);
    const btn = el("button", `realm-btn${realm.id === selected ? " active" : ""}${s.sessions ? "" : " empty"}`);
    btn.append(el("span", "realm-key", i < 9 ? String(i + 1) : ""), el("span", "realm-name", realm.name || realm.id));
    btn.append(s.waiting ? el("span", "badge-wait", s.waiting) : el("span", "muted", s.sessions ? String(s.sessions) : ""));
    const dots = el("div", "dots");
    for (const ego of realm.alter_egos) {
      const d = el("span", "dot");
      d.style.background = provider(ego.provider).color;
      d.style.opacity = isAsleep(ego) ? 0.3 : 1;
      d.title = `${ego.name ? ego.name + " · " : ""}${provider(ego.provider).label} · ${sessionTitle(ego)}`;
      dots.append(d);
    }
    btn.append(dots);
    btn.onclick = () => onSelect(realm.id);
    return btn;
  }));
}

// Atributos por área (R40, D-096, V-HUD-16): uma barra por área com a parcela do trabalho da sessão. É a contagem do mundo, não pontuação.
function attributeBars(attributes) {
  const box = el("div", "attrs");
  box.title = `${attributes.total} atividades contadas`;
  for (const a of attributes.areas) {
    const pct = Math.round(a.share * 100);
    const fill = el("i");
    fill.style.width = `${pct}%`;
    const bar = el("span", "bar");
    bar.append(fill);
    box.append(el("span", "attr-name", a.area), bar, el("span", "attr-pct", `${pct}%`));
  }
  return box;
}

const MAX_INDENT = 6;       // uma Team muito funda não empurra o cartão para fora do painel

// A Team em árvore (R57, D-116, V-HUD-17): o mundo manda a lista na ordem da árvore, com a profundidade de cada um. Ficam os
// ativos (os "sem sinal" também, em cinza) e os pais deles, para a árvore não perder o fio.
function teamTree(team) {
  const shown = team.map((sub) => sub.active);
  for (let i = team.length - 1; i >= 0; i--) {
    for (let j = i + 1; j < team.length && team[j].depth > team[i].depth; j++) if (shown[j]) shown[i] = true;
  }
  const box = el("div", "team");
  team.forEach((sub, i) => {
    if (!shown[i]) return;
    const row = el("span", `sub${sub.active ? "" : " done"}`, `${sub.depth ? "└ " : ""}${sub.kind || "subagente"} · ${sub.active ? STATE_LABEL[sub.state] || sub.state : "concluído"}`);
    row.style.marginLeft = `${Math.min(sub.depth, MAX_INDENT) * 14}px`;
    box.append(row);
  });
  return box.children.length ? box : null;
}

function sessionCard(ego, onOpen) {
  const p = provider(ego.provider);
  const asleep = isAsleep(ego);
  const waiting = ego.waiting.length > 0 || ego.state === "WAITING";
  const card = el("div", `card${waiting ? " waiting" : ""}${asleep ? " asleep" : ""}`);
  card.style.setProperty("--pc", p.color);
  const top = el("div", "card-top");
  if (ego.name) top.append(el("span", "ego-name", ego.name));
  top.append(el("span", "prov", p.label), ...(ego.role ? [el("span", "role", ego.role)] : []), el("span", "title", sessionTitle(ego)),
             el("span", `chip ${ego.state}`, asleep ? "dormindo" : STATE_LABEL[ego.state] || ego.state));
  card.append(top);
  if (waiting) {
    card.append(el("div", "alert", `⏳ esperando você: ${ego.waiting[0]?.action || "aprovação"}`));
  }
  const now = el("div", "now");
  if (ego.area) now.append(el("span", "area", `${ego.area} · `));
  now.append(ego.last_action || (asleep ? "sem atividade recente" : "—"));
  now.title = ego.last_action || "";
  card.append(now);
  if (ego.attributes) card.append(attributeBars(ego.attributes));
  const tree = teamTree(ego.team);
  if (tree) card.append(tree);
  const meta = el("div", "meta");
  meta.append(el("span", null, ego.model || "modelo ?"), el("span", null, tokens(ego.usage)));
  if (ego.usage.cost_usd) meta.append(el("span", null, `US$ ${ego.usage.cost_usd.toFixed(2)}`));
  meta.append(el("span", null, ago(ego.last_ts)));
  card.append(meta);
  card.onclick = () => onOpen(ego.id);
  return card;
}

function shortDate(iso) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  const sameYear = d.getFullYear() === new Date().getFullYear();
  return d.toLocaleDateString("pt-BR", sameYear ? { day: "2-digit", month: "short" } : { day: "2-digit", month: "short", year: "numeric" });
}

// Histórico do realm (R28a, V-HUD-6): as sessões que já saíram da sala. Nenhuma some; só mudam de lugar.
export function renderHistory(history) {
  const box = document.getElementById("ov-history");
  const sessions = history ? history.sessions : null;
  if (!sessions || !sessions.length) {
    box.classList.add("hidden");
    changed("history", null);
    return;
  }
  if (!changed("history", history)) return;
  box.classList.remove("hidden");
  const total = history.total || sessions.length;
  const count = total > sessions.length ? `${sessions.length} de ${total}` : String(total);      // nada é escondido sem avisar
  box.replaceChildren(el("h3", null, `Histórico do realm · ${count}`), ...sessions.map((s) => {
    const row = el("div", "hist-row");
    row.style.setProperty("--pc", provider(s.provider).color);
    if (s.name) row.append(el("span", "ego-name", s.name));
    row.append(el("span", "prov", provider(s.provider).label), el("span", "title", s.title || s.session.slice(0, 8)),
               el("span", "when", `${shortDate(s.started_at)} → ${shortDate(s.updated_at)}`));
    return row;
  }));
}

// Tela de configurações (R29, V-HUD-5, V-HUD-7). As opções numéricas vêm da tabela do servidor (`options`): os tickets
// que acrescentam uma opção só acrescentam uma linha lá, esta tela já sabe desenhá-la.
// Filtro de tipos e exclusões da contagem de linhas (R19, D-054, D-056), para todos os realms ou por realm.
let linesRealm = "";           // o realm escolhido na seção "Por realm" (some a cada reabertura da janela, de propósito)

function lineControls(idPrefix, filter, onApply) {
  const box = el("div");
  const row = el("div", "setting-row");
  const md = document.createElement("input");
  md.type = "checkbox";
  md.id = `${idPrefix}-md`;
  md.checked = Boolean(filter.include_markdown);
  const label = el("label", null, "Contar arquivos .md");
  label.htmlFor = md.id;
  row.append(md, label);
  const patterns = document.createElement("textarea");
  patterns.id = `${idPrefix}-exclude`;
  patterns.rows = 5;
  patterns.value = filter.exclude.join("\n");
  patterns.setAttribute("aria-label", "Exclusões: um padrão por linha");
  const apply = () => onApply({ include_markdown: md.checked, exclude: patterns.value.split("\n").map((p) => p.trim()).filter(Boolean) });
  md.onchange = apply;
  patterns.onchange = apply;
  box.append(row, el("p", "hint", "Exclusões, um padrão por linha. Sem barra vale para o nome em qualquer pasta (ex.: *.min.js); com barra, para o caminho (ex.: dist/*)."), patterns);
  return box;
}

function renderLineSettings(settings, onChange) {
  const section = el("div");
  section.append(el("legend", null, "Contagem de linhas"),
    el("p", "hint", "As linhas não vazias dos arquivos que o git acompanha, sem os ignorados e sem estas exclusões. É o que dá a altura (classe) do prédio."));
  section.append(lineControls("lines", settings.lines, (parts) => onChange({ lines: parts })));
  const reset = el("button", "btn", "Restaurar a lista padrão");
  reset.onclick = () => onChange({ lines: { exclude: settings.lines.default_exclude } });
  section.append(reset);
  const pick = document.createElement("select");
  pick.id = "lines-realm";
  pick.setAttribute("aria-label", "Realm com filtro próprio");
  pick.append(new Option("Por realm: escolha um realm…", ""), ...settings.realms.map((r) => new Option(r.name || r.id, r.id)));
  pick.value = settings.realms.some((r) => r.id === linesRealm) ? linesRealm : "";
  pick.onchange = () => { linesRealm = pick.value; renderLineSettings(settings, onChange); };
  const own = el("div");
  const realm = settings.realms.find((r) => r.id === pick.value);
  if (realm?.lines_note) own.append(el("p", "hint", `Sem número de linhas: ${realm.lines_note}`));
  if (realm) {
    const useGeneral = document.createElement("input");
    useGeneral.type = "checkbox";
    useGeneral.id = "lines-general";
    useGeneral.checked = !realm.lines;
    useGeneral.onchange = () => onChange({ realm_lines: { [realm.id]: useGeneral.checked ? null : { include_markdown: settings.lines.include_markdown, exclude: settings.lines.exclude } } });
    const row = el("div", "setting-row");
    const label = el("label", null, "Este realm usa o filtro de todos");
    label.htmlFor = useGeneral.id;
    row.append(useGeneral, label);
    own.append(row);
    if (realm.lines) {
      const effective = { include_markdown: realm.lines.include_markdown ?? settings.lines.include_markdown, exclude: realm.lines.exclude ?? settings.lines.exclude };
      own.append(lineControls("realm-lines", effective, (parts) => onChange({ realm_lines: { [realm.id]: parts } })));
    }
  }
  section.append(pick, own);
  const host = document.getElementById("settings-lines");
  host.replaceChildren(...section.childNodes);
}

export function renderSettings(settings, onChange) {
  const body = document.getElementById("settings-body");
  const focused = document.activeElement && body.contains(document.activeElement) ? document.activeElement.id : null;
  const realms = el("div");
  realms.append(el("h3", null, "Realms"), el("p", "hint", "Desmarcado = não aparece na cidade. O realm continua detectado."));
  for (const realm of settings.realms) {
    const row = el("div", "setting-row");
    const box = document.createElement("input");
    box.type = "checkbox";
    box.id = `realm-${realm.id}`;
    box.checked = !realm.hidden;
    box.onchange = () => onChange({ hidden_realms: settings.realms
      .filter((r) => (r.id === realm.id ? !box.checked : r.hidden)).map((r) => r.id) });
    const label = el("label");
    label.htmlFor = box.id;
    label.append(el("span", null, realm.name || realm.id), el("span", "muted path", realm.cwd || ""));
    row.append(box, label);
    realms.append(row);
  }
  if (!settings.realms.length) realms.append(el("div", "empty", "Nenhum realm detectado ainda."));
  const options = el("div");
  options.append(el("h3", null, "Opções"));
  for (const option of settings.options) {
    if (option.kind !== "number") continue;                      // tipos novos de opção ganham o desenho deles quando o ticket que os cria chegar
    const row = el("div", "setting-row");
    const input = document.createElement("input");
    input.type = "number";
    input.id = `opt-${option.key}`;
    Object.assign(input, { min: option.minimum, max: option.maximum, value: option.value, step: 1 });
    input.onchange = () => onChange({ [option.key]: Number(input.value) });
    const label = el("label", null, option.label);
    label.htmlFor = input.id;
    row.append(label, input, el("span", "muted", option.unit));
    options.append(row);
  }
  const lines = document.createElement("fieldset");         // um grupo com legenda: o leitor de tela sabe a que os controles pertencem
  lines.id = "settings-lines";
  body.replaceChildren(realms, options, lines);
  if (settings.lines) renderLineSettings(settings, onChange);
  if (settings.persistent === false) body.append(el("p", "hint", "Sem pasta do Orb: as mudanças valem só até fechar."));
  if (settings.error) {
    const message = el("div", "setting-error", settings.error);
    message.setAttribute("role", "alert");
    body.append(message);
  }
  if (focused) document.getElementById(focused)?.focus();        // refazer a janela não tira o foco de quem está digitando
}

export function renderOverview(realm, onOpen) {
  const panel = document.getElementById("overview");
  if (!realm) {
    panel.classList.add("hidden");
    changed("overview", null);
    return;
  }
  // "há Xs" muda sozinho: arredonda para não redesenhar a cada segundo.
  if (!changed("overview", [realm, Math.floor(Date.now() / 15000)])) return;
  panel.classList.remove("hidden");
  document.getElementById("ov-title").textContent = realm.name || realm.id;
  document.getElementById("ov-path").textContent = realm.cwd || "";
  document.getElementById("ov-metrics").textContent = metricsText(realm) || "";
  const s = summarize(realm);
  const summary = document.getElementById("ov-summary");
  const cell = (k, v, cls = "") => { const c = el("div"); c.append(el("div", "k", k), el("div", `v ${cls}`, v)); return c; };
  summary.replaceChildren(cell("Sessões", s.sessions), cell("Ativas", s.active),
    cell("Esperando", s.waiting, s.waiting ? "wait" : ""), cell("Tokens", tokens({ input_tokens: s.tokens }).replace(" tok", "")));
  const list = document.getElementById("ov-sessions");
  const egos = [...realm.alter_egos].sort((a, b) => rank(a) - rank(b) || (b.last_ts || "").localeCompare(a.last_ts || ""));
  if (!egos.length) {
    list.replaceChildren(el("div", "empty", "Nenhuma sessão recente neste realm. Abra uma aqui embaixo, ou use o CLI na pasta do projeto: ela aparece sozinha."));
  } else {
    list.replaceChildren(...egos.map((e) => sessionCard(e, onOpen)));
  }
  const errors = Object.entries(realm.errors || {});
  if (errors.length) list.append(el("div", "empty", `Sem sinal de: ${errors.map(([p]) => provider(p).label).join(", ")}`));
}

function rank(ego) {
  if (ego.waiting.length || ego.state === "WAITING") return 0;
  if (isAsleep(ego)) return 3;
  return ["IDLE", "COMPLETED"].includes(ego.state) ? 2 : 1;
}
