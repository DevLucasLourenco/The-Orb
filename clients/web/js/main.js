// The Orb — o mundo. Junta o palco 3D, os realms, os personagens, o HUD e o Inner World.
import * as THREE from "three";
import { Stage } from "./scene.js";
import { RealmBuilding } from "./realm3d.js";
import { Avatar } from "./avatar.js";
import { renderOverview, renderRealmList, renderTopbar, summarize } from "./hud.js";
import { InnerWorld } from "./innerworld.js";
import { connectWorld } from "./net.js";
import { PROVIDERS, isAsleep, subVisible } from "./providers.js";

const stage = new Stage(document.getElementById("scene"));
const inner = new InnerWorld();
const buildings = new Map();     // realm -> RealmBuilding
const avatars = new Map();       // alter ego / subagente -> Avatar
const egoIndex = new Map();      // alter ego -> { ego, realm }
let world = { realms: [] };
let selectedRealm = null;
let layoutKey = "";
const NEAR = 120;                 // distância da câmera em que os detalhes aparecem

// ---------------------------------------------------------------------------------------------
// Layout da cidade: os realms em anel no disco do Orb.
function layout() {
  const ids = world.realms.map((r) => r.id);
  const key = ids.join("|");
  if (key === layoutKey) return;
  layoutKey = key;
  const n = ids.length;
  const radius = n <= 1 ? 0 : Math.max(46, n * 13);
  ids.forEach((id, i) => {
    const a = (i / Math.max(1, n)) * Math.PI * 2 - Math.PI / 2;
    buildings.get(id)?.setPosition(Math.cos(a) * radius, Math.sin(a) * radius);
  });
  stage.setGroundRadius(radius + 52);
}

function syncWorld(next) {
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
    // Quem está em cada área (líderes e subagentes juntos), para distribuir os lugares.
    const groups = new Map();
    const place = (key, area) => { if (!groups.has(area)) groups.set(area, []); groups.get(area).push(key); };
    for (const ego of realm.alter_egos) {
      egoIndex.set(ego.id, { ego, realm });
      const asleep = isAsleep(ego);
      place(ego.id, asleep ? "__dorm" : ego.area || "__lobby");
      let a = avatars.get(ego.id);
      if (!a) avatars.set(ego.id, (a = new Avatar(stage.scene, { id: ego.id, providerName: ego.provider })));
      a.setEgo(ego);
      a.realm = realm.id;
      alive.add(ego.id);
      inner.updateEgo(ego);
      if (asleep) continue;
      for (const sub of ego.team.filter(subVisible)) {
        const key = `${ego.id}/${sub.id}`;
        place(key, sub.area || "__lobby");
        let s = avatars.get(key);
        if (!s) avatars.set(key, (s = new Avatar(stage.scene, { id: key, providerName: ego.provider, sub: true })));
        s.setSub(sub);
        s.realm = realm.id;
        alive.add(key);
      }
    }
    for (const [area, keys] of groups) {
      keys.sort().forEach((key, i) => avatars.get(key).moveTo(b.slot(area, i, keys.length)));
    }
  }
  for (const [id, a] of avatars) if (!alive.has(id)) { a.dispose(); avatars.delete(id); }

  renderTopbar(world);
  renderRealmList(world, selectedRealm, selectRealm);
  renderOverview(world.realms.find((r) => r.id === selectedRealm), openEgo);
}

// ---------------------------------------------------------------------------------------------
function selectRealm(id, fly = true) {
  selectedRealm = id;
  renderRealmList(world, selectedRealm, selectRealm);
  renderOverview(world.realms.find((r) => r.id === id), openEgo);
  const b = buildings.get(id);
  if (b && fly) stage.flyTo(b.center(), 46, 0.62);
}

function overview() {
  selectedRealm = null;
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
  },
  onEvent: (event) => inner.push(event),
  onFeed: (egoId, events) => inner.setFeed(egoId, events),
  onStatus: (ok) => {
    const c = document.getElementById("conn");
    c.textContent = ok ? "ao vivo" : "reconectando…";
    c.className = `conn ${ok ? "ok" : "bad"}`;
  },
});

// Clique: personagem abre o Inner World; prédio seleciona o realm.
let down = null;
stage.renderer.domElement.addEventListener("pointerdown", (e) => (down = { x: e.clientX, y: e.clientY }));
stage.renderer.domElement.addEventListener("pointerup", (e) => {
  if (!down || Math.hypot(e.clientX - down.x, e.clientY - down.y) > 5 || e.button !== 0) return;
  const pickables = [...[...avatars.values()].flatMap((a) => a.pickables), ...[...buildings.values()].flatMap((b) => b.pickables)];
  const hit = stage.pick(e.clientX, e.clientY, pickables);
  if (!hit) return;
  const avatarId = hit.object.userData.avatarId;
  if (avatarId) openEgo(avatarId.split("/")[0]);
  else if (hit.object.userData.realmId) selectRealm(hit.object.userData.realmId);
});

window.addEventListener("keydown", (e) => {
  const tag = e.target?.tagName;
  if (tag === "INPUT" || tag === "SELECT" || e.target?.closest?.(".xterm")) return;
  if (e.key === "Escape") overview();
  else if (/^[1-9]$/.test(e.key) && world.realms[Number(e.key) - 1]) selectRealm(world.realms[Number(e.key) - 1].id);
  else if (e.key.toLowerCase() === "f" && selectedRealm) selectRealm(selectedRealm);
});
document.getElementById("ov-close").onclick = overview;

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
  for (const a of avatars.values()) a.update(dt, t, near && (!selectedRealm || a.realm === selectedRealm));
};
stage.start();
// Sessões "dormem" com o tempo: reavalia sem esperar o próximo evento.
setInterval(() => world.realms.length && syncWorld(world), 30000);
