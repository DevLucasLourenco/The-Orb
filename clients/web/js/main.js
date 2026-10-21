// The Orb — o mundo. Junta o palco 3D, os realms, os personagens, o HUD e o Inner World.
import * as THREE from "three";
import { Stage } from "./scene.js";
import { RealmBuilding } from "./realm3d.js";
import { Avatar } from "./avatar.js";
import { renderHistory, renderOverview, renderProgress, renderRealmList, renderSettings, renderTopbar, summarize } from "./hud.js";
import { InnerWorld } from "./innerworld.js";
import { connectWorld } from "./net.js";
import { PROVIDERS } from "./providers.js";

const stage = new Stage(document.getElementById("scene"));
const inner = new InnerWorld();
const buildings = new Map();     // realm -> RealmBuilding
const avatars = new Map();       // alter ego / subagente -> Avatar
const egoIndex = new Map();      // alter ego -> { ego, realm }
let world = { realms: [] };
let selectedRealm = null;
const realmHistory = new Map();  // realm -> sessões que já saíram da sala (Histórico do realm)
let roomCount = -1;              // quantas sessões o realm selecionado tem na sala: se mudar, o Histórico muda
const NEAR = 120;                 // distância da câmera em que os detalhes aparecem
const LEAVE_WINDOW_MS = 30000;    // o subagente só caminha até o líder se terminou há menos que isto (não ao abrir a página depois)

// ---------------------------------------------------------------------------------------------
// A cidade retangular (R32): o mundo calcula bairros, lotes, deslocamento e giro; aqui só se posiciona o que ele mandou.
function layout() {
  stage.setCity(world.city);
  for (const realm of world.realms) buildings.get(realm.id)?.setPlace(realm.place);
}

// Na sala ficam só as sessões dos últimos 10 dias (R28a); o mundo marca quem já saiu (`in_room`) e as
// mais antigas aparecem no Histórico do realm, nunca no prédio.
function roomOnly(next) {
  return { ...next, realms: next.realms.map((r) => ({ ...r, alter_egos: r.alter_egos.filter((e) => e.in_room !== false) })) };
}

function syncWorld(raw) {
  const next = roomOnly(raw);
  world = next;
  const seen = new Set();
  for (const realm of world.realms) {
    let b = buildings.get(realm.id);
    if (!b) buildings.set(realm.id, (b = new RealmBuilding(realm, stage.scene)));
    seen.add(realm.id);
  }
  for (const [id, b] of buildings) if (!seen.has(id)) { b.dispose(); buildings.delete(id); }
  layout();

  const alive = new Set();
  egoIndex.clear();
  for (const realm of world.realms) {
    const b = buildings.get(realm.id);
    b.setData(realm, summarize(realm));
    for (const ego of realm.alter_egos) {
      egoIndex.set(ego.id, { ego, realm });
      let a = avatars.get(ego.id);
      if (!a) avatars.set(ego.id, (a = new Avatar(stage.scene, { id: ego.id, providerName: ego.provider })));
      a.setEgo(ego);
      a.realm = realm.id;
      alive.add(ego.id);
      inner.updateEgo(ego);
      if (ego.ended) continue;       // sessão encerrada: a Team também terminou
      // Líder dormindo não esconde a Team: o subagente "sem sinal" fica cinza no lugar (R7), não some.
      for (const sub of ego.team) {
        const key = `${ego.id}/${sub.id}`;
        if (!sub.active) {
          // O subagente que terminou (R51): se já estava em cena, caminha até o líder e só então sai; sem o sinal de fim vale o cinza (R7).
          const mine = avatars.get(key);
          const recent = sub.ended_at && Date.parse(world.generated_at) - Date.parse(sub.ended_at) < LEAVE_WINDOW_MS;
          if (mine && recent) { mine.leaveTo(avatars.get(ego.id).group.position); alive.add(key); }
          continue;
        }
        let s = avatars.get(key);
        if (!s) avatars.set(key, (s = new Avatar(stage.scene, { id: key, providerName: ego.provider, sub: true })));
        s.setSub(sub);
        s.realm = realm.id;
        alive.add(key);
      }
    }
    // A sala cheia (R33): o mundo diz quem aparece em cada lugar (até 8) e quantos ficaram de fora; o resto some de cena e vira o "+N".
    const shown = new Set();
    for (const [place, info] of Object.entries(realm.room)) {
      info.shown.forEach((key, i) => { shown.add(key); avatars.get(key)?.moveTo(b.slot(place, i, info.shown.length)); });
      b.setOverflow(place, info.more);
    }
    for (const [key, a] of avatars) if (a.realm === realm.id && !a.leaving) a.setHidden(!shown.has(key));
  }
  for (const [id, a] of avatars) if (!alive.has(id)) { a.dispose(); avatars.delete(id); }

  if (selectedRealm && !world.realms.some((r) => r.id === selectedRealm)) overview();     // o realm foi escondido: fecha o overview e o Inner World
  else if (inner.current?.kind === "ego" && !egoIndex.has(inner.current.ego.id)) inner.close();                    // a sessão saiu da sala (prazo menor): idem
  renderTopbar(world);
  renderRealmList(world, selectedRealm, selectRealm);
  renderOverview(world.realms.find((r) => r.id === selectedRealm), openEgo);
  const here = world.realms.find((r) => r.id === selectedRealm);
  if (here && here.alter_egos.length !== roomCount) {      // uma sessão entrou ou saiu da sala: o Histórico pode ter mudado
    if (roomCount !== -1) net.requestHistory(selectedRealm);
    roomCount = here.alter_egos.length;
  }
}

// ---------------------------------------------------------------------------------------------
function selectRealm(id, fly = true) {
  selectedRealm = id;
  roomCount = -1;
  renderHistory(realmHistory.get(id));
  net.requestHistory(id);
  renderRealmList(world, selectedRealm, selectRealm);
  renderOverview(world.realms.find((r) => r.id === id), openEgo);
  const b = buildings.get(id);
  if (b && fly) stage.flyTo(b.center(), 46, 0.62);
}

function overview() {
  selectedRealm = null;
  renderHistory(null);
  inner.close();
  renderRealmList(world, null, selectRealm);
  renderOverview(null);
  const r = stage.groundRadius || 160;
  stage.flyTo(new THREE.Vector3(0, 20, 0), Math.max(170, r * 1.55), 0.86);
}

function openEgo(id) {
  const entry = egoIndex.get(id);
  if (!entry) return;
  if (selectedRealm !== entry.realm.id) selectRealm(entry.realm.id, false);
  inner.openEgo(entry.ego, (egoId) => net.requestFeed(egoId));
  const a = avatars.get(id);
  if (a) stage.flyTo(a.group.position.clone().add(new THREE.Vector3(0, 1.5, 0)), 24, 0.5);
}

// ---------------------------------------------------------------------------------------------
const net = connectWorld({
  onWorld: (w) => {
    const first = !world.realms.length;
    syncWorld(w);
    if (first && w.realms.length === 1) selectRealm(w.realms[0].id);
    else if (first && w.realms.length) overview();          // a cidade inteira já na primeira vista
  },
  onEvent: (event) => inner.push(event),
  onFeed: (egoId, events) => inner.setFeed(egoId, events),
  onSettings: (settings) => renderSettings(settings, (changes) => net.savePreferences(changes)),
  onXp: (extract) => renderProgress(extract, world),         // `world` é lido na hora: o placar e o nível são os do último mundo recebido
  onHistory: (realm, sessions, total) => {
    realmHistory.set(realm, { sessions, total });
    if (realm === selectedRealm) renderHistory({ sessions, total });
  },
  onStatus: (ok) => {
    const c = document.getElementById("conn");
    c.textContent = ok ? "ao vivo" : "reconectando…";
    c.className = `conn ${ok ? "ok" : "bad"}`;
    if (ok && selectedRealm) net.requestHistory(selectedRealm);
  },
});

// Clique: personagem abre o Inner World; prédio seleciona o realm.
let down = null;
stage.renderer.domElement.addEventListener("pointerdown", (e) => (down = { x: e.clientX, y: e.clientY }));
stage.renderer.domElement.addEventListener("pointerup", (e) => {
  if (!down || Math.hypot(e.clientX - down.x, e.clientY - down.y) > 5 || e.button !== 0) return;
  const pickables = [...[...avatars.values()].filter((a) => !a.hidden).flatMap((a) => a.pickables), ...[...buildings.values()].flatMap((b) => b.pickables)];
  const hit = stage.pick(e.clientX, e.clientY, pickables);
  if (!hit) return;
  const avatarId = hit.object.userData.avatarId;
  if (avatarId) openEgo(avatarId.split("/")[0]);
  else if (hit.object.userData.realmId) selectRealm(hit.object.userData.realmId);
});

// Duplo clique num personagem (R17): a câmera o segue até o Lucas mexer nela.
stage.renderer.domElement.addEventListener("dblclick", (e) => {
  const pickables = [...avatars.values()].filter((a) => !a.hidden).flatMap((a) => a.pickables);
  const hit = stage.pick(e.clientX, e.clientY, pickables);
  const avatar = hit && avatars.get(hit.object.userData.avatarId);
  if (avatar) stage.follow(avatar.group);
});

window.addEventListener("keydown", (e) => {
  if (!settingsBox.classList.contains("hidden")) {      // com a janela aberta, o teclado é dela (Esc fecha, mesmo dentro de um campo)
    if (e.key === "Escape") toggleSettings(false);
    return;
  }
  if (!progressBox.classList.contains("hidden")) {
    if (e.key === "Escape") toggleProgress(false);
    return;
  }
  const tag = e.target?.tagName;
  if (tag === "INPUT" || tag === "SELECT" || e.target?.closest?.(".xterm")) return;
  if (e.key === "Escape") overview();
  else if (/^[1-9]$/.test(e.key) && world.realms[Number(e.key) - 1]) selectRealm(world.realms[Number(e.key) - 1].id);
  else if (e.key.toLowerCase() === "f" && selectedRealm) selectRealm(selectedRealm);
});
document.getElementById("ov-close").onclick = overview;

// Configurações (R29): o servidor manda os realms detectados e as opções; as mudanças voltam como um pedido só.
const settingsBox = document.getElementById("settings");
const settingsButton = document.getElementById("open-settings");
function toggleSettings(open) {
  settingsBox.classList.toggle("hidden", !open);
  if (open) {
    net.requestSettings();
    document.getElementById("settings-close").focus();
  } else {
    settingsButton.focus();                               // o foco volta ao botão que abriu a janela
  }
}
settingsButton.onclick = () => toggleSettings(settingsBox.classList.contains("hidden"));
document.getElementById("settings-close").onclick = () => toggleSettings(false);
settingsBox.addEventListener("pointerdown", (e) => { if (e.target === settingsBox) toggleSettings(false); });

// Progressão (V-HUD-12): o nível de Mankind na barra de cima abre o painel com o placar por provider e o extrato de XP.
const progressBox = document.getElementById("progress");
const progressButton = document.getElementById("open-progress");
let progressTimer = null;
function toggleProgress(open) {
  progressBox.classList.toggle("hidden", !open);
  clearInterval(progressTimer);
  if (open) {
    net.requestXp();
    progressTimer = setInterval(() => net.requestXp(), 5000);          // aberto, o painel se atualiza sozinho (o extrato não vem no mundo)
    document.getElementById("progress-close").focus();
  } else {
    progressButton.focus();
  }
}
progressButton.onclick = () => toggleProgress(progressBox.classList.contains("hidden"));
document.getElementById("progress-close").onclick = () => toggleProgress(false);
progressBox.addEventListener("pointerdown", (e) => { if (e.target === progressBox) toggleProgress(false); });

// Nova sessão: o terminal real abre no realm selecionado; o personagem aparece sozinho.
const select = document.getElementById("new-provider");
fetch("/config").then((r) => r.json()).then((config) => {
  for (const name of [...Object.keys(PROVIDERS), "shell"]) {
    const installed = name === "shell" || config.providers[name];
    const option = new Option(installed ? name : `${name} (não instalado)`, name);
    option.disabled = !installed;
    select.append(option);
  }
});
document.getElementById("new-session").onclick = () => {
  if (!selectedRealm) return;
  inner.openTerminal({ realm: selectedRealm, providerName: select.value });
};

// ---------------------------------------------------------------------------------------------
stage.onFrame = (dt, t) => {
  const distance = stage.distance();
  const near = distance < NEAR;
  for (const b of buildings.values()) {
    const mine = !selectedRealm || b.id === selectedRealm;
    b.update(dt, t, near && mine, near && b.id === selectedRealm && distance < 70);
  }
  for (const [id, a] of avatars) {
    a.update(dt, t, near && (!selectedRealm || a.realm === selectedRealm));
    if (a.gone) { a.dispose(); avatars.delete(id); }              // o subagente que terminou chegou ao líder: sai de cena
  }
};
stage.start();
// Só o "há Xs" do overview depende do tempo que passa; dormindo e sem sinal vêm do mundo.
setInterval(() => selectedRealm && renderOverview(world.realms.find((r) => r.id === selectedRealm), openEgo), 15000);
