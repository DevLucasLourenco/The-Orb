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

// Sessão parada há mais que isso aparece "dormindo" (só apresentação; o Core não tem relógio).
export const ASLEEP_AFTER_MS = 15 * 60 * 1000;

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

// Subagente sem atividade há mais que isso sai de cena. No nível 0 o fim de um subagente em segundo
// plano não é observável (docs/adapters/CLAUDE.md §1.6): sem isso ele ficaria "trabalhando" para sempre.
export const SUB_IDLE_AFTER_MS = 5 * 60 * 1000;

export function subVisible(sub) {
  return sub.active && ageMs(sub.last_ts) < SUB_IDLE_AFTER_MS;
}

export function isAsleep(ego) {
  return ego.ended || (ego.state === "IDLE" && ageMs(ego.last_ts) > ASLEEP_AFTER_MS);
}

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

export function sessionTitle(ego) {
  return ego.title || `${provider(ego.provider).label} · ${ego.session.slice(0, 8)}`;
}
