// A camada 2D sobre o mundo: números de Mankind, lista de realms e o overview do realm.
import { STATE_LABEL, ago, el, isAsleep, provider, sessionTitle, tokens } from "./providers.js";

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

function sessionCard(ego, onOpen) {
  const p = provider(ego.provider);
  const asleep = isAsleep(ego);
  const waiting = ego.waiting.length > 0 || ego.state === "WAITING";
  const card = el("div", `card${waiting ? " waiting" : ""}${asleep ? " asleep" : ""}`);
  card.style.setProperty("--pc", p.color);
  const top = el("div", "card-top");
  if (ego.name) top.append(el("span", "ego-name", ego.name));
  top.append(el("span", "prov", p.label), el("span", "title", sessionTitle(ego)),
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
  const team = ego.team.filter((sub) => sub.active);     // inclui os "sem sinal": ficam listados, em cinza
  if (team.length) {
    const t = el("div", "team");
    for (const sub of team) {
      t.append(el("span", "sub", `${sub.kind || "subagente"} · ${STATE_LABEL[sub.state] || sub.state}`));
    }
    card.append(t);
  }
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
export function renderSettings(settings, onChange) {
  const body = document.getElementById("settings-body");
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
  body.replaceChildren(realms, options);
  if (settings.error) body.append(el("div", "setting-error", settings.error));
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
