// Inner World: a linha do tempo da sessão (como o provider grava) e o terminal real do CLI.
import { el, provider, sessionTitle } from "./providers.js";
import { openTerminalSocket } from "./net.js";

const MAX_LINES = 600;

export class InnerWorld {
  constructor() {
    this.root = document.getElementById("inner");
    this.timeline = document.getElementById("iw-timeline");
    this.termBox = document.getElementById("iw-terminal");
    this.who = document.getElementById("iw-who");
    this.feeds = new Map();        // alter_ego -> eventos
    this.terminals = [];           // terminais abertos por este painel
    this.current = null;           // { kind: "ego", ego } | { kind: "terminal", term }
    this.tab = "timeline";
    document.getElementById("iw-close").onclick = () => this.close();
    for (const btn of this.root.querySelectorAll(".tab")) btn.onclick = () => this.showTab(btn.dataset.tab);
    window.addEventListener("resize", () => this._fitTerminal());
  }

  // --- linha do tempo ---------------------------------------------------------------------
  setFeed(egoId, events) {
    this.feeds.set(egoId, events.slice(-MAX_LINES));
    if (this.current?.kind === "ego" && this.current.ego.id === egoId) this._renderTimeline();
  }

  push(event) {
    const id = event.alter_ego;
    const lines = this.feeds.get(id) || [];
    lines.push(event);
    if (lines.length > MAX_LINES) lines.splice(0, lines.length - MAX_LINES);
    this.feeds.set(id, lines);
    if (this.current?.kind === "ego" && this.current.ego.id === id && this.tab === "timeline") {
      const stick = this.timeline.scrollTop + this.timeline.clientHeight >= this.timeline.scrollHeight - 40;
      this.timeline.append(line(event));
      if (stick) this.timeline.scrollTop = this.timeline.scrollHeight;
    }
  }

  _renderTimeline() {
    const lines = this.feeds.get(this.current.ego.id) || [];
    this.timeline.replaceChildren(...(lines.length ? lines.map(line) : [el("div", "terminal-empty", "Ainda sem linhas desta sessão.")]));
    this.timeline.scrollTop = this.timeline.scrollHeight;
  }

  // --- abrir / fechar ----------------------------------------------------------------------
  openEgo(ego, requestFeed) {
    this.current = { kind: "ego", ego };
    this._header(ego.provider, sessionTitle(ego), ego.model);
    this.root.classList.remove("hidden");
    requestFeed(ego.id);
    this._renderTimeline();
    this.showTab(this.terminalFor(ego.id) ? this.tab : "timeline");
  }

  updateEgo(ego) {
    if (this.current?.kind === "ego" && this.current.ego.id === ego.id) {
      this.current.ego = ego;
      this._header(ego.provider, sessionTitle(ego), ego.model);
    }
  }

  close() {
    this.root.classList.add("hidden");
    this.current = null;
  }

  isOpenFor(egoId) {
    return this.current?.kind === "ego" && this.current.ego.id === egoId;
  }

  _header(providerName, title, model) {
    const parts = [];
    if (providerName) {
      const p = provider(providerName);
      const prov = el("span", "prov", p.label);
      prov.style.setProperty("--pc", p.color);
      parts.push(prov);
    }
    this.who.replaceChildren(...parts, el("span", "title", title), el("span", "muted", model || ""));
  }

  showTab(tab) {
    this.tab = tab;
    for (const btn of this.root.querySelectorAll(".tab")) btn.classList.toggle("active", btn.dataset.tab === tab);
    this.timeline.classList.toggle("hidden", tab !== "timeline");
    this.termBox.classList.toggle("hidden", tab !== "terminal");
    if (tab === "terminal") this._renderTerminal();
    if (tab === "timeline" && this.current?.kind === "ego") this._renderTimeline();
  }

  // --- terminais ---------------------------------------------------------------------------
  terminalFor(egoId) {
    return this.terminals.find((t) => t.alterEgo === egoId) || null;
  }

  openTerminal({ realm, providerName }) {
    const host = el("div");
    host.style.height = "100%";
    const term = new Terminal({ fontFamily: "Cascadia Mono, Consolas, monospace", fontSize: 13, cursorBlink: true,
      scrollback: 5000, theme: { background: "#0a0e17" } });
    const fit = new FitAddon.FitAddon();
    term.loadAddon(fit);
    const entry = { realm, providerName, term, fit, host, alterEgo: null, ws: null, opened: false, status: "conectando…" };
    this.terminals.push(entry);
    const ws = (entry.ws = openTerminalSocket({ realm, provider: providerName }));
    ws.onmessage = (m) => {
      const msg = JSON.parse(m.data);
      if (msg.channel === "term") term.write(msg.data);
      else if (msg.channel === "exit") term.write(`\r\n\x1b[90m[processo terminou: ${msg.code}]\x1b[0m\r\n`);
      else if (msg.channel === "system") {
        if (msg.alter_ego) entry.alterEgo = msg.alter_ego;
        if (msg.error) term.write(`\r\n\x1b[31m${msg.error}\x1b[0m\r\n`);
      }
    };
    ws.onopen = () => this._sendSize(entry);
    term.onData((data) => { if (ws.readyState === 1) ws.send(JSON.stringify({ type: "input", data })); });
    this.current = { kind: "terminal", term: entry };
    this._header(providerName === "shell" ? null : providerName, providerName === "shell" ? "Terminal" : "Nova sessão", "");
    this.root.classList.remove("hidden");
    this.showTab("terminal");
    return entry;
  }

  _renderTerminal() {
    const entry = this.current?.kind === "terminal" ? this.current.term
      : this.current?.kind === "ego" ? this.terminalFor(this.current.ego.id) : null;
    if (!entry) {
      this.termBox.replaceChildren(el("div", "terminal-empty",
        "Esta sessão foi aberta fora deste painel: o terminal dela é o lugar onde ela foi aberta. " +
        "Para usar um CLI daqui, abra uma nova sessão pelo overview do realm."));
      return;
    }
    this.termBox.replaceChildren(entry.host);
    if (!entry.opened) {
      entry.term.open(entry.host);
      entry.opened = true;
    }
    this._fitTerminal();
    entry.term.focus();
  }

  _fitTerminal() {
    const entry = this.current?.kind === "terminal" ? this.current.term
      : this.current?.kind === "ego" ? this.terminalFor(this.current.ego.id) : null;
    if (!entry || !entry.opened || this.termBox.classList.contains("hidden")) return;
    requestAnimationFrame(() => { entry.fit.fit(); this._sendSize(entry); });
  }

  _sendSize(entry) {
    if (entry.ws && entry.ws.readyState === 1 && entry.opened) {
      entry.ws.send(JSON.stringify({ type: "resize", cols: entry.term.cols, rows: entry.term.rows }));
    }
  }
}

function line(event) {
  const row = el("div", `line ${event.inner.role}`);
  const kind = el("span", "k", event.native.kind);
  if (event.inner.fidelity) kind.append(el("span", "fid", event.inner.fidelity));
  const who = event.agent ? ` ↳ ${event.agent.slice(0, 6)}` : "";
  row.append(el("span", "t", (event.ts || "").slice(11, 19) + who), kind, el("span", "x", event.inner.text));
  return row;
}
