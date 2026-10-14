// Identidade visual de cada provider. O personagem carrega a cor do CLI da sua sessão.
export const PROVIDERS = {
  claude:   { label: "Claude",   color: "#e8845c" },
  codex:    { label: "Codex",    color: "#2fd3a2" },
  hermes:   { label: "Hermes",   color: "#b18cff" },
  opencode: { label: "opencode", color: "#5aa8ff" },
};
const UNKNOWN = { label: "?", color: "#9aa7bd" };

export const provider = (name) => PROVIDERS[name] || UNKNOWN;

export const STATE_LABEL = {
  IDLE: "parado", THINKING: "pensando", READING: "lendo", RESEARCHING: "pesquisando", CODING: "editando",
  EXECUTING: "executando", TESTING: "testando", REVIEWING: "revisando", DELEGATING: "delegando",
  WAITING: "esperando você", BLOCKED: "bloqueado", ERROR: "erro", COMPLETED: "concluído", NO_SIGNAL: "sem sinal",
};

// Só para mostrar "há Xs" nos cartões. Quem decide dormindo e sem sinal é o mundo (R47), não o cliente.
export function ageMs(ts) {
  const t = Date.parse(ts || "");
  return Number.isFinite(t) ? Date.now() - t : Infinity;
}

export function ago(ts) {
  const ms = ageMs(ts);
  if (!Number.isFinite(ms)) return "—";
  const s = Math.max(0, Math.round(ms / 1000));
  if (s < 60) return `há ${s}s`;
  if (s < 3600) return `há ${Math.round(s / 60)} min`;
  if (s < 86400) return `há ${Math.round(s / 3600)} h`;
  return `há ${Math.round(s / 86400)} d`;
}

// Dormindo: a decisão vem do mundo (`asleep`); o cliente só desenha.
export const isAsleep = (ego) => Boolean(ego.asleep);

export function tokens(usage) {
  const n = (usage?.input_tokens || 0) + (usage?.output_tokens || 0);
  if (n >= 1e6) return `${(n / 1e6).toFixed(1)}M tok`;
  if (n >= 1e3) return `${Math.round(n / 1e3)}k tok`;
  return `${n} tok`;
}

export function el(tag, cls, text) {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text !== undefined && text !== null) node.textContent = String(text);
  return node;
}

// "48 mil linhas": o número real de linhas do projeto, só formatado (a classe vem pronta do mundo).
export function formatLines(n) {
  if (n < 1000) return `${n} linhas`;
  // Sempre para baixo: 499.999 nunca vira "500 mil" ao lado da classe Torre.
  if (n < 10000) return `${(Math.floor(n / 100) / 10).toFixed(1).replace(".", ",")} mil linhas`;
  return `${Math.floor(n / 1000)} mil linhas`;
}

export function metricsText(realm) {
  return realm.metrics ? `${formatLines(realm.metrics.loc)} · ${realm.metrics.class}` : null;
}

export function sessionTitle(ego) {
  return ego.title || `${provider(ego.provider).label} · ${ego.session.slice(0, 8)}`;
}
