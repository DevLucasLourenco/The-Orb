// Um Realm: o prédio do projeto, com o Rooftop Room de vidro no teto e as 5 áreas do Environment.
import * as THREE from "three";
import { CSS2DObject } from "three/addons/renderers/CSS2DRenderer.js";
import { el, metricsText } from "./providers.js";

export const ROOF = 18;          // lado do Rooftop Room e do último andar do prédio: a sala é sempre do mesmo tamanho
export const LEVEL_H = 3;        // altura de um nível (uma fileira de janelas)
export const ROOM_H = 5.5;
const GROUND_Y = 1.2;            // topo da base (o pódio chão) onde o primeiro andar começa
const FACADE_ROWS = 22;          // fileiras de janelas da textura da fachada (uma por nível)

// A forma de cada classe de prédio (VISUAL.md §8, R41): os blocos de baixo para cima, cada um com a largura e a fração
// da altura em que termina. O mundo manda a classe e os níveis; o cliente só desenha. Largura máxima 30 (o lote tem 46).
// `canopy`: marquise no térreo; `crown`: coroa no topo. As formas são neutras (sem cor de significado).
export const SHAPES = {
  "Casa":        { tiers: [[18, 1]] },
  "Sobrado":     { tiers: [[26, 0.4], [22, 1]] },       // o corpo (22) é mais largo que a sala (18): terraço em volta dela
  "Prédio":      { tiers: [[20, 1]], canopy: 26 },
  "Edifício":    { tiers: [[26, 0.65], [20, 1]] },
  "Torre":       { tiers: [[30, 0.12], [22, 0.6], [20, 0.85], [18, 1]] },
  "Arranha-céu": { tiers: [[30, 0.08], [26, 0.4], [22, 0.65], [20, 0.85], [18, 1]], crown: 21 },
};
const NO_COUNT = { tiers: [[18, 1]], flat: true };      // realm sem contagem de linhas: só uma laje lisa, sem janelas, classe nem marcas (não parece uma Casa)
const FLAT_H = 1;
const ANTENNA_H = 22;

// Áreas do Environment no piso do quartinho (x, z, largura, profundidade, cor). +z = frente.
export const AREAS = {
  "Development Center": { x: -4.7, z: 3.9, w: 6.6, d: 5.2, color: 0x3aa0ff },
  "Testing Lab":        { x: 4.7,  z: 3.9, w: 6.6, d: 5.2, color: 0x8be04e },
  "Research Center":    { x: -4.7, z: -3.9, w: 6.6, d: 5.2, color: 0x9d7bff },
  "Code Review":        { x: 4.7,  z: -3.9, w: 6.6, d: 5.2, color: 0xffcc4d },
  "Task Board":         { x: 0,    z: -7.3, w: 3.2, d: 2.2, color: 0xff6fa5 },
};
const LOBBY = { x: 0, z: 0.2, r: 1.9 };          // quem não está numa área (pensando, parado, esperando)
const UP = new THREE.Vector3(0, 1, 0);
const DORM = { z: 7.9, x0: -7.6, x1: 7.6 };      // sessões dormindo: fileira na frente do quartinho

function windowTexture(seed) {
  const c = document.createElement("canvas");
  c.width = 128; c.height = 256;
  const g = c.getContext("2d");
  g.fillStyle = "#000"; g.fillRect(0, 0, 128, 256);
  let s = seed;
  const rnd = () => ((s = (s * 9301 + 49297) % 233280) / 233280);
  for (let row = 0; row < FACADE_ROWS; row++) {
    for (let col = 0; col < 8; col++) {
      const lit = rnd();
      if (lit < 0.42) continue;
      const warm = rnd() < 0.55;
      const a = 0.35 + rnd() * 0.65;
      g.fillStyle = warm ? `rgba(255,196,128,${a})` : `rgba(140,200,255,${a})`;
      g.fillRect(6 + col * 15, 5 + row * 11.3, 8, 6);
    }
  }
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 4;
  return tex;
}

function hash(text) {
  let h = 2166136261;
  for (const ch of text) h = Math.imul(h ^ ch.charCodeAt(0), 16777619);
  return Math.abs(h) % 100000;
}

// Quantos níveis tem cada bloco da forma: cada um termina na sua fração da altura e tem pelo menos um nível.
export function tierLevels(tiers, levels) {
  const out = [];
  let used = 0;
  tiers.forEach(([, end], i) => {
    const left = tiers.length - 1 - i;
    const upTo = i === tiers.length - 1 ? levels : Math.min(levels - left, Math.max(used + 1, Math.round(end * levels)));
    out.push(Math.max(1, upTo - used));
    used = upTo;
  });
  return out;
}

function disposeTree(root) {
  root.traverse((o) => {
    o.geometry?.dispose?.();
    const mats = Array.isArray(o.material) ? o.material : o.material ? [o.material] : [];
    mats.forEach((m) => { m.emissiveMap?.dispose?.(); m.dispose?.(); });
    if (o.isCSS2DObject) o.element.remove();
  });
}

export class RealmBuilding {
  constructor(realm, scene) {
    this.id = realm.id;
    this.scene = scene;
    this.group = new THREE.Group();
    this.pickables = [];
    this.activity = 0;           // 0..1, acende as janelas
    this.waiting = 0;
    this.windowMap = windowTexture(hash(realm.id));

    this.plinth = new THREE.Mesh(new THREE.BoxGeometry(1, 1.2, 1),
      new THREE.MeshStandardMaterial({ color: 0x0e1626, roughness: 0.8, metalness: 0.2 }));
    this.plinth.position.y = 0.6;
    this.plinth.receiveShadow = true;
    this.plinth.userData.realmId = this.id;

    // Rooftop Room: vidro com arestas de luz. Fica num grupo próprio, que sobe e desce com a altura do prédio.
    this.room = new THREE.Group();
    const roomGeo = new THREE.BoxGeometry(ROOF, ROOM_H, ROOF);
    // Vidro sem iluminação: não reflete a luz interna (os reflexos viravam pontos estourados).
    const glass = new THREE.Mesh(roomGeo, new THREE.MeshBasicMaterial({
      color: 0x9cc8ff, transparent: true, opacity: 0.05, side: THREE.DoubleSide, depthWrite: false,
    }));
    glass.position.y = ROOM_H / 2;
    glass.userData.realmId = this.id;
    this.roomEdges = new THREE.LineSegments(new THREE.EdgesGeometry(roomGeo),
      new THREE.LineBasicMaterial({ color: 0x7cc4ff, toneMapped: false, transparent: true, opacity: 0.85 }));
    this.roomEdges.position.copy(glass.position);
    this.glass = glass;
    this.light = new THREE.PointLight(0x9cc8ff, 22, 30, 1.4);
    this.light.position.y = ROOM_H + 2.5;
    this.night = false;          // "noite" (D-059): nenhuma sessão nos últimos 10 dias; o mundo diz, aqui só se desenha

    this.room.add(glass, this.roomEdges, this.light);
    this.group.add(this.plinth, this.room);
    this._areas();
    this._beacon();

    // Rótulo do prédio (visível de longe).
    this.labelEl = el("div", "lbl-realm");
    this.label = new CSS2DObject(this.labelEl);
    this.label.position.y = ROOM_H + 3.5;
    this.room.add(this.label);

    this.bodyKey = null;
    this._body(realm.metrics);
    scene.add(this.group);
  }

  // O corpo do prédio (VISUAL.md §8): a forma da classe, na altura em níveis que o mundo calculou, com a laje do teto, as
  // cintas de luz neutra e, no Arranha-céu, a coroa e a antena. Sem contagem de linhas, um volume liso de um nível.
  _body(metrics) {
    const key = metrics ? `${metrics.class}:${metrics.levels}` : "";
    if (key === this.bodyKey) return;
    this.bodyKey = key;
    if (this.body) { this.group.remove(this.body); disposeTree(this.body); }
    const shape = (metrics && SHAPES[metrics.class]) || NO_COUNT;
    const levels = metrics ? metrics.levels : 1;      // (a laje lisa ignora os níveis)
    const body = (this.body = new THREE.Group());
    const plain = new THREE.MeshStandardMaterial({ color: 0x0c1322, roughness: 0.6, metalness: 0.45 });
    const stone = new THREE.MeshStandardMaterial({ color: 0x131d31, roughness: 0.92, metalness: 0.1 });
    this.windowMats = [];
    this.pickables.length = 0;
    this.pickables.push(this.plinth, this.glass);

    const widest = Math.max(...shape.tiers.map(([w]) => w));
    this.plinth.scale.set(widest + 6, 1, widest + 6);

    let y = GROUND_Y;
    const spans = tierLevels(shape.tiers, levels);
    shape.tiers.forEach(([w], i) => {
      const h = shape.flat ? FLAT_H : spans[i] * LEVEL_H;
      const windows = shape.flat ? plain : new THREE.MeshStandardMaterial({
        color: 0x0d1526, roughness: 0.45, metalness: 0.55, emissive: 0xffffff, emissiveIntensity: 0.35,
        emissiveMap: this._facade(spans[i]),
      });
      if (!shape.flat) this.windowMats.push(windows);
      const block = new THREE.Mesh(new THREE.BoxGeometry(w, h, w), [windows, windows, plain, plain, windows, windows]);
      block.position.y = y + h / 2;
      block.castShadow = true;
      block.receiveShadow = true;
      block.userData.realmId = this.id;
      const edges = new THREE.LineSegments(new THREE.EdgesGeometry(block.geometry),
        new THREE.LineBasicMaterial({ color: 0x2c5a92, transparent: true, opacity: 0.55 }));
      edges.position.copy(block.position);
      body.add(block, edges);
      this.pickables.push(block);
      y += h;
    });
    const top = y;
    const topWidth = shape.tiers[shape.tiers.length - 1][0];

    if (shape.canopy) {            // marquise sobre o térreo (Prédio)
      const canopy = new THREE.Mesh(new THREE.BoxGeometry(shape.canopy, 0.5, shape.canopy), stone);
      canopy.position.y = GROUND_Y + LEVEL_H + 0.25;
      canopy.receiveShadow = true;
      body.add(canopy);
    }
    if (shape.crown) {             // coroa no topo (Arranha-céu)
      const crown = new THREE.Mesh(new THREE.BoxGeometry(shape.crown, 1.4, shape.crown), stone);
      crown.position.y = top - 0.7;
      crown.castShadow = true;
      body.add(crown);
    }
    // As cintas de luz neutra, logo abaixo do Rooftop Room: uma a mais a cada classe (o mundo diz quantas).
    const band = new THREE.MeshBasicMaterial({ color: 0xffffff, toneMapped: false, transparent: true, opacity: 0.9 });
    const bandWidth = (shape.crown || topWidth) + 0.5;
    for (let i = 0; i < (metrics ? metrics.bands : 0); i++) {
      const ring = new THREE.Mesh(new THREE.BoxGeometry(bandWidth, 0.35, bandWidth), band);
      ring.position.y = top - 1.9 - i * 0.9;
      body.add(ring);
    }
    const slab = new THREE.Mesh(new THREE.BoxGeometry(ROOF + 0.8, 0.5, ROOF + 0.8), stone);
    slab.position.y = top + 0.05;
    slab.receiveShadow = true;
    body.add(slab);
    this.floorY = slab.position.y + 0.3;           // piso do Rooftop Room
    this.room.position.y = this.floorY;
    if (metrics && metrics.antenna) {              // antena do Arranha-céu, saindo do teto da sala
      const mast = new THREE.Mesh(new THREE.CylinderGeometry(0.25, 0.4, ANTENNA_H, 8),
        new THREE.MeshStandardMaterial({ color: 0xaab4c4, roughness: 0.5, metalness: 0.6 }));
      mast.position.y = this.floorY + ROOM_H + ANTENNA_H / 2;
      const tip = new THREE.Mesh(new THREE.SphereGeometry(0.6, 12, 8), new THREE.MeshBasicMaterial({ color: 0xffffff, toneMapped: false }));
      tip.position.y = this.floorY + ROOM_H + ANTENNA_H;
      body.add(mast, tip);
    }
    this.group.add(body);
  }

  // A fachada de um bloco: uma fileira de janelas por nível (hoje a textura ainda é decoração; as janelas de verdade chegam no ticket 11).
  _facade(levels) {
    const map = this.windowMap.clone();
    map.wrapT = THREE.RepeatWrapping;
    map.repeat.set(1, levels / FACADE_ROWS);
    map.needsUpdate = true;
    return map;
  }

  _areas() {
    this.areaLabels = [];
    this.roomLights = [];        // o que se apaga de noite: pisos das áreas e anel do lobby
    for (const [name, a] of Object.entries(AREAS)) {
      const pad = new THREE.Mesh(new THREE.BoxGeometry(a.w, 0.12, a.d),
        new THREE.MeshStandardMaterial({ color: a.color, emissive: a.color, emissiveIntensity: 0.18, transparent: true, opacity: 0.35, roughness: 0.4 }));
      pad.position.set(a.x, 0.06, a.z);
      pad.receiveShadow = true;
      const edge = new THREE.LineSegments(new THREE.EdgesGeometry(pad.geometry),
        new THREE.LineBasicMaterial({ color: a.color, toneMapped: false, transparent: true, opacity: 0.9 }));
      edge.position.copy(pad.position);
      const label = new CSS2DObject(el("div", "lbl-area", name));
      label.position.set(a.x, 0.2, a.z + a.d / 2 - 0.4);
      this.areaLabels.push(label);
      this.roomLights.push(pad, edge);
      this.room.add(pad, edge, label);
    }
    const lobby = new THREE.Mesh(new THREE.RingGeometry(LOBBY.r - 0.12, LOBBY.r, 48),
      new THREE.MeshBasicMaterial({ color: 0x7cc4ff, toneMapped: false, transparent: true, opacity: 0.5, side: THREE.DoubleSide }));
    lobby.rotation.x = -Math.PI / 2;
    lobby.position.set(LOBBY.x, 0.03, LOBBY.z);
    this.roomLights.push(lobby);
    this.room.add(lobby);
  }

  _beacon() {
    // Feixe de luz âmbar: alguém deste realm está esperando o Lucas. Visível da cidade inteira.
    const mat = new THREE.MeshBasicMaterial({ color: 0xffb547, transparent: true, opacity: 0.0, toneMapped: false,
      blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide });
    this.beacon = new THREE.Mesh(new THREE.CylinderGeometry(1.1, 2.4, 140, 24, 1, true), mat);
    this.beacon.position.y = ROOM_H + 70;
    this.beaconRing = new THREE.Mesh(new THREE.TorusGeometry(ROOF * 0.72, 0.12, 8, 96),
      new THREE.MeshBasicMaterial({ color: 0xffb547, toneMapped: false, transparent: true, opacity: 0 }));
    this.beaconRing.rotation.x = Math.PI / 2;
    this.beaconRing.position.y = 0.25;
    this.room.add(this.beacon, this.beaconRing);
  }

  // O lote que o mundo deu (R32): posição já com o deslocamento e o giro tirados do nome do realm.
  setPlace(place) {
    this.group.position.set(place.x, 0, place.z);
    this.group.rotation.y = place.turn;
  }

  // Um ponto do prédio (no referencial dele) no mundo: o prédio gira, então as posições do piso giram junto.
  _at(x, y, z) {
    return new THREE.Vector3(x, y, z).applyAxisAngle(UP, this.group.rotation.y).add(this.group.position);
  }

  center() {
    return new THREE.Vector3(this.group.position.x, this.floorY, this.group.position.z);
  }

  setData(realm, summary) {
    this._body(realm.metrics);       // a classe ou a altura mudou (o Probe contou de novo): o corpo é refeito
    this.activity = Math.min(1, summary.active / 3);
    this.waiting = summary.waiting;
    this.night = Boolean(realm.night);
    const size = metricsText(realm);          // "48 mil linhas · Edifício": só aparece quando há contagem real
    this.labelEl.replaceChildren(
      el("div", "n", realm.name || realm.id),
      ...(size ? [el("div", "c", size)] : []),
      (() => {
        const c = el("div", "c", `${summary.sessions} sessões · ${summary.active} ativas`);
        if (summary.waiting) c.append(" · ", el("span", "w", `${summary.waiting} esperando`));
        return c;
      })(),
    );
  }

  // Lugar no piso para o n-ésimo personagem de uma área (ou do lobby / dormitório).
  slot(area, index, count) {
    if (area === "__dorm") {
      const x = count > 1 ? DORM.x0 + (DORM.x1 - DORM.x0) * (index / (count - 1)) : 0;
      return this._at(x, this.floorY, DORM.z);
    }
    const a = AREAS[area];
    const cx = a ? a.x : LOBBY.x, cz = a ? a.z : LOBBY.z;
    if (count <= 1) return this._at(cx, this.floorY, cz);
    const radius = a ? Math.min(a.w, a.d) * 0.32 : LOBBY.r * 0.75;
    const angle = (index / count) * Math.PI * 2 + 0.6;
    return this._at(cx + Math.cos(angle) * radius, this.floorY, cz + Math.sin(angle) * radius);
  }

  update(dt, t, near, focused = false) {
    const target = 0.28 + this.activity * 1.1;
    for (const m of this.windowMats) m.emissiveIntensity += (target - m.emissiveIntensity) * Math.min(1, dt * 2);
    const pulse = this.waiting ? 0.5 + 0.5 * Math.sin(t * 3.2) : 0;
    this.beacon.material.opacity = this.waiting ? 0.10 + 0.14 * pulse : 0;
    this.beaconRing.material.opacity = this.waiting ? 0.35 + 0.5 * pulse : 0;
    this.roomEdges.material.color.setHex(this.waiting ? 0xffc46b : 0x7cc4ff);
    // Noite: a sala do teto apaga (luz, pisos das áreas, arestas); as janelas da fachada seguem como estão.
    const lit = !this.night;
    this.light.visible = lit;
    for (const mesh of this.roomLights) mesh.visible = lit;
    this.roomEdges.visible = lit;
    this.glass.visible = lit;
    for (const label of this.areaLabels) label.visible = near && lit;
    this.label.visible = !focused;      // de perto o nome do prédio só atrapalha a sala
  }

  dispose() {
    this.scene.remove(this.group);
    this.windowMap.dispose();
    disposeTree(this.group);
  }
}
