// Conexão com o mundo (/world): snapshot, deltas e linhas de Inner World. Reconecta sozinha.
export const TOKEN = new URLSearchParams(location.search).get("token") || "";

export function connectWorld({ onWorld, onEvent, onFeed, onStatus }) {
  let ws = null;
  let delay = 500;
  const api = {
    requestFeed(alterEgo) {
      if (ws && ws.readyState === 1) ws.send(JSON.stringify({ type: "feed", alter_ego: alterEgo }));
    },
  };
  function open() {
    ws = new WebSocket(`ws://${location.host}/world?token=${encodeURIComponent(TOKEN)}`);
    ws.onopen = () => { delay = 500; onStatus(true); };
    ws.onclose = () => { onStatus(false); setTimeout(open, delay); delay = Math.min(delay * 2, 8000); };
    ws.onmessage = (m) => {
      const msg = JSON.parse(m.data);
      if (msg.channel === "world") onWorld(msg.world);
      else if (msg.channel === "event") onEvent(msg.event);
      else if (msg.channel === "feed") onFeed(msg.alter_ego, msg.events);
    };
  }
  open();
  return api;
}

export function openTerminalSocket({ realm, provider, model }) {
  const q = new URLSearchParams({ token: TOKEN, realm, provider, model: model || "" });
  return new WebSocket(`ws://${location.host}/ws?${q}`);
}
