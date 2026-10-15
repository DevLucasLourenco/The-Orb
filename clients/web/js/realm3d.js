// Um Realm: o prédio do projeto, com o Rooftop Room de vidro no teto e as 5 áreas do Environment.
import * as THREE from "three";
import { CSS2DObject } from "three/addons/renderers/CSS2DRenderer.js";
import { WAIT_COLOR, el, metricsText } from "./providers.js";
import { areaDecal } from "./areaicons.js";

export const ROOF = 18;          // lado do Rooftop Room e do último andar do prédio: a sala é sempre do mesmo tamanho
export const LEVEL_H = 3;        // altura de um nível (uma fileira de janelas)
export const ROOM_H = 5.5;
const GROUND_Y = 1.2;            // topo da base (o pódio chão) onde o primeiro andar começa

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

// O céu sobre o prédio (Weather, R42, VISUAL.md V-REALM-16): céu limpo = uma lua branca; chuva = uma nuvem cinza com chuva. Só tons neutros,
// fora do orçamento de cores. O mundo diz qual dos dois (ou nenhum); o cliente só desenha.
const SKY_LABEL = { clear: "céu limpo", rain: "chuva" };
const RAIN_STREAKS = 36;
const RAIN_DEPTH = 12;

// Áreas do Environment no piso do quartinho (x, z, largura, profundidade). +z = frente. Sem cor própria (R20c, D-187): o piso é neutro e
// cada área se identifica pelo ícone, pelo nome e por um padrão (areaicons.js).
export const AREAS = {
  "Development Center": { x: -4.7, z: 3.9, w: 6.6, d: 5.2 },
  "Testing Lab":        { x: 4.7,  z: 3.9, w: 6.6, d: 5.2 },
  "Research Center":    { x: -4.7, z: -3.9, w: 6.6, d: 5.2 },
  "Code Review":        { x: 4.7,  z: -3.9, w: 6.6, d: 5.2 },
  "Task Board":         { x: 0,    z: -7.3, w: 3.2, d: 2.2 },
};
const AREA_FLOOR = 0x2a3550;      // piso neutro de todas as áreas (cinza-azulado, o mesmo para as cinco)
const AREA_EDGE = 0xaebbd4;       // aresta neutra das áreas
const LOBBY = { x: 0, z: 0.2, r: 1.9 };          // quem não está numa área (pensando, parado, esperando)
const UP = new THREE.Vector3(0, 1, 0);
const DORM = { z: 7.9, x0: -7.6, x1: 7.6 };      // sessões dormindo: fileira na frente do quartinho

// As janelas (R20, VISUAL.md §5 e §6): cada janela acesa é um pacote de alterações locais do git, na cor do tipo de alteração
// (a paleta do git do VS Code). A janela só tem dois estados, acesa ou apagada, com brilho fixo. O mundo diz quais acendem e onde.
export const CHANGE_COLORS = {
  modified: "#E2C08D", added: "#81B88B", untracked: "#73C991", renamed: "#73C991", deleted: "#C74E39", conflict: "#E4676B",
};
const FACE_MATERIAL = [4, 0, 5, 1];      // lado 0..3 do mundo -> posição do material na caixa (+z, +x, -z, -x)
const PANE = 16;                         // pixels de uma janela na textura
const LIT_INTENSITY = 1.1;               // brilho fixo da janela acesa (D-115: a atividade não acende a fachada)

function canvasTexture(canvas) {
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 4;
  return tex;
}

function blank(cols, rows, color) {
  const c = document.createElement("canvas");
  c.width = cols * PANE; c.height = rows * PANE;
  const g = c.getContext("2d");
  g.fillStyle = color; g.fillRect(0, 0, c.width, c.height);
  return [c, g];
}

// O vidro de um bloco: a parede com o vidro apagado de cada janela (todas as posições têm dado: "nada mudou"). É igual nos 4 lados.
function glassTexture(cols, rows) {
  const [canvas, g] = blank(cols, rows, "#0c1322");
  g.fillStyle = "#22345a";
  for (let row = 0; row < rows; row++) {
    for (let col = 0; col < cols; col++) g.fillRect(col * PANE + 2, row * PANE + 2, PANE - 4, PANE - 4);
  }
  return canvasTexture(canvas);
}

// As janelas acesas de um lado de um bloco, só elas, na cor do tipo de alteração (um tipo que o cliente não conhece não acende).
function glowTexture(cols, rows, lit) {
  const [canvas, g] = blank(cols, rows, "#000");
  for (const w of lit) {
    if (!CHANGE_COLORS[w.type]) continue;
    g.fillStyle = CHANGE_COLORS[w.type];
    g.fillRect(w.col * PANE + 2, (rows - 1 - w.row) * PANE + 2, PANE - 4, PANE - 4);
  }
  return canvasTexture(canvas);
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
    mats.forEach((m) => { m.map?.dispose?.(); m.emissiveMap?.dispose?.(); m.dispose?.(); });
    if (o.isCSS2DObject) o.element.remove();
  });
}

export class RealmBuilding {
  constructor(realm, scene) {
    this.id = realm.id;
    this.scene = scene;
    this.group = new THREE.Group();
    this.pickables = [];
    this.waiting = 0;

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

    this.sky = new THREE.Group();            // o céu sobre o prédio: troca quando o Weather muda
    this.skyKey = null;
    this.rain = null;
    this.room.add(glass, this.roomEdges, this.light, this.sky);
    this.group.add(this.plinth, this.room);
    this._areas();
    this._beacon();

    // Rótulo do prédio (visível de longe).
    this.labelEl = el("div", "lbl-realm");
    this.label = new CSS2DObject(this.labelEl);
    this.label.position.y = ROOM_H + 3.5;
    this.room.add(this.label);

    this.bodyKey = null;
    this._body(realm);
    this._sky(realm);
    scene.add(this.group);
  }

  // O corpo do prédio (VISUAL.md §8): a forma da classe, na altura em níveis que o mundo calculou, com a laje do teto, as
  // cintas de luz neutra e, no Arranha-céu, a coroa e a antena. Sem contagem de linhas, um volume liso de um nível.
  _body(realm) {
    const metrics = realm.metrics;
    const lit = metrics && realm.facade ? realm.facade : null;               // sem leitura do git ou sem andares: sem janelas (nada inventado)
    const key = `${metrics ? `${metrics.class}:${metrics.levels}` : ""}|${lit ? JSON.stringify(lit.windows) : "-"}`;
    if (key === this.bodyKey) return;
    this.bodyKey = key;
    if (this.body) { this.group.remove(this.body); disposeTree(this.body); }
    const shape = (metrics && SHAPES[metrics.class]) || NO_COUNT;
    const levels = metrics ? metrics.levels : 1;      // (a laje lisa ignora os níveis)
    const body = (this.body = new THREE.Group());
    const plain = new THREE.MeshStandardMaterial({ color: 0x0c1322, roughness: 0.6, metalness: 0.45 });
    const stone = new THREE.MeshStandardMaterial({ color: 0x131d31, roughness: 0.92, metalness: 0.1 });
    this.pickables.length = 0;
    this.pickables.push(this.plinth, this.glass);

    const widest = Math.max(...shape.tiers.map(([w]) => w));
    this.plinth.scale.set(widest + 6, 1, widest + 6);

    let y = GROUND_Y;
    let firstLevel = 0;
    const spans = tierLevels(shape.tiers, levels);
    shape.tiers.forEach(([w], i) => {
      const h = shape.flat ? FLAT_H : spans[i] * LEVEL_H;
      const sides = [plain, plain, plain, plain];
      if (lit && !shape.flat) {                  // as janelas deste bloco: as do mundo cujo nível cai nele
        const here = lit.windows.filter((x) => x.level >= firstLevel && x.level < firstLevel + spans[i]).map((x) => ({ ...x, row: x.level - firstLevel }));
        const glass = glassTexture(lit.cols, spans[i]);
        for (let face = 0; face < lit.faces; face++) {
          sides[face] = new THREE.MeshStandardMaterial({
            color: 0xffffff, map: glass, roughness: 0.45, metalness: 0.55, emissive: 0xffffff,
            emissiveMap: glowTexture(lit.cols, spans[i], here.filter((x) => x.face === face)), emissiveIntensity: LIT_INTENSITY,
          });
        }
      }
      firstLevel += spans[i];
      const materials = [plain, plain, plain, plain, plain, plain];            // o topo e o fundo ficam lisos
      sides.forEach((m, face) => { materials[FACE_MATERIAL[face]] = m; });
      const block = new THREE.Mesh(new THREE.BoxGeometry(w, h, w), materials);
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

  // O céu (Weather): uma lua branca ou uma nuvem cinza com chuva, acima da sala (e da antena, se houver). Sem Weather, nada.
  _sky(realm) {
    const sky = realm.weather ? realm.weather.sky : null;
    const antenna = Boolean(realm.metrics && realm.metrics.antenna);
    const key = `${sky}|${antenna}`;
    if (key === this.skyKey) return;
    this.skyKey = key;
    for (const child of [...this.sky.children]) { this.sky.remove(child); disposeTree(child); }
    this.rain = null;
    if (!sky) return;
    this.sky.position.y = ROOM_H + (antenna ? ANTENNA_H + 8 : 16);          // acima do rótulo, que sobe até ROOM_H + 12
    if (sky === "clear") {
      const moon = new THREE.Mesh(new THREE.SphereGeometry(2.4, 24, 16), new THREE.MeshBasicMaterial({ color: 0xf1f4fa, toneMapped: false }));
      const halo = new THREE.Mesh(new THREE.SphereGeometry(4.2, 24, 16),
        new THREE.MeshBasicMaterial({ color: 0xf1f4fa, transparent: true, opacity: 0.12, depthWrite: false, toneMapped: false }));
      this.sky.add(moon, halo);
      return;
    }
    const cloudMaterial = new THREE.MeshBasicMaterial({ color: 0x7b8394, transparent: true, opacity: 0.92, toneMapped: false });
    for (const [x, z, r] of [[-3.2, 0, 3.2], [0, 0.6, 4.2], [3.4, -0.4, 3.4], [0.4, -2.2, 3]]) {
      const puff = new THREE.Mesh(new THREE.SphereGeometry(r, 16, 12), cloudMaterial);
      puff.scale.y = 0.55;
      puff.position.set(x, 0, z);
      this.sky.add(puff);
    }
    // A chuva: riscos que descem da nuvem e voltam ao alto (movimento de cenário, sem dado: o dado é "chuva" ou "não").
    const points = new Float32Array(RAIN_STREAKS * 6);
    const speeds = [];
    for (let i = 0; i < RAIN_STREAKS; i++) {
      const angle = (i * 2.399963) % (Math.PI * 2), radius = 1.5 + 5.5 * Math.sqrt((i + 0.5) / RAIN_STREAKS);
      const y = -((i * 0.6180339) % 1) * RAIN_DEPTH;
      points.set([Math.cos(angle) * radius, y, Math.sin(angle) * radius, Math.cos(angle) * radius, y - 1.4, Math.sin(angle) * radius], i * 6);
      speeds.push(7 + (i % 5));
    }
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.BufferAttribute(points, 3));
    this.sky.add(new THREE.LineSegments(geometry, new THREE.LineBasicMaterial({ color: 0xaab4c4, transparent: true, opacity: 0.65, toneMapped: false })));
    this.rain = { geometry, points, speeds };
  }

  _areas() {
    this.areaLabels = [];
    this.roomLights = [];        // o que se apaga de noite: pisos das áreas e anel do lobby
    for (const [name, a] of Object.entries(AREAS)) {
      const pad = new THREE.Mesh(new THREE.BoxGeometry(a.w, 0.12, a.d),
        new THREE.MeshStandardMaterial({ color: AREA_FLOOR, emissive: AREA_FLOOR, emissiveIntensity: 0.18, transparent: true, opacity: 0.55, roughness: 0.4 }));
      pad.position.set(a.x, 0.06, a.z);
      pad.receiveShadow = true;
      const edge = new THREE.LineSegments(new THREE.EdgesGeometry(pad.geometry),
        new THREE.LineBasicMaterial({ color: AREA_EDGE, toneMapped: false, transparent: true, opacity: 0.5 }));
      edge.position.copy(pad.position);
      // O ícone e o padrão da área, num decalque transparente logo acima do piso (o topo do pad está em y = 0.12).
      const decal = new THREE.Mesh(new THREE.PlaneGeometry(a.w, a.d),
        new THREE.MeshBasicMaterial({ map: areaDecal(name, a.w, a.d), transparent: true, depthWrite: false, toneMapped: false }));
      decal.rotation.x = -Math.PI / 2;
      decal.position.set(a.x, 0.13, a.z);
      const label = new CSS2DObject(el("div", "lbl-area", name));
      label.position.set(a.x, 0.2, a.z + a.d / 2 - 0.4);
      this.areaLabels.push(label);
      this.roomLights.push(pad, edge, decal);
      this.room.add(pad, edge, decal, label);
    }
    const lobby = new THREE.Mesh(new THREE.RingGeometry(LOBBY.r - 0.12, LOBBY.r, 48),
      new THREE.MeshBasicMaterial({ color: 0x7cc4ff, toneMapped: false, transparent: true, opacity: 0.5, side: THREE.DoubleSide }));
    lobby.rotation.x = -Math.PI / 2;
    lobby.position.set(LOBBY.x, 0.03, LOBBY.z);
    this.roomLights.push(lobby);
    this.room.add(lobby);
  }

  _beacon() {
    // Feixe de luz magenta (R20c): alguém deste realm está esperando o Lucas. Visível da cidade inteira.
    const mat = new THREE.MeshBasicMaterial({ color: new THREE.Color(WAIT_COLOR), transparent: true, opacity: 0.0, toneMapped: false,
      blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide });
    this.beacon = new THREE.Mesh(new THREE.CylinderGeometry(1.1, 2.4, 140, 24, 1, true), mat);
    this.beacon.position.y = ROOM_H + 70;
    this.beaconRing = new THREE.Mesh(new THREE.TorusGeometry(ROOF * 0.72, 0.12, 8, 96),
      new THREE.MeshBasicMaterial({ color: new THREE.Color(WAIT_COLOR), toneMapped: false, transparent: true, opacity: 0 }));
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
    this._body(realm);       // a classe, a altura ou as janelas mudaram (os Probes leram de novo): o corpo é refeito
    this._sky(realm);        // o Weather mudou (um teste passou ou falhou): o céu é refeito
    this.waiting = summary.waiting;
    this.night = Boolean(realm.night);
    const size = metricsText(realm);          // "48 mil linhas · Edifício": só aparece quando há contagem real
    this.labelEl.replaceChildren(
      el("div", "n", realm.name || realm.id),
      ...(size ? [el("div", "c", size)] : []),
      ...(realm.weather && SKY_LABEL[realm.weather.sky] ? [el("div", "c", `Weather: ${SKY_LABEL[realm.weather.sky]}`)] : []),
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
    if (this.rain) {                      // a chuva desce e volta ao alto
      const { points, speeds, geometry } = this.rain;
      for (let i = 0; i < speeds.length; i++) {
        const drop = i * 6 + 1;
        const y = -((-(points[drop] - speeds[i] * dt)) % RAIN_DEPTH);          // fica entre -RAIN_DEPTH e 0, qualquer que seja o quadro
        points[drop] = y;
        points[drop + 3] = y - 1.4;
      }
      geometry.attributes.position.needsUpdate = true;
    }
    const pulse = this.waiting ? 0.5 + 0.5 * Math.sin(t * 3.2) : 0;
    this.beacon.material.opacity = this.waiting ? 0.10 + 0.14 * pulse : 0;
    this.beaconRing.material.opacity = this.waiting ? 0.35 + 0.5 * pulse : 0;
    this.roomEdges.material.color.set(this.waiting ? WAIT_COLOR : 0x7cc4ff);
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
    disposeTree(this.group);
  }
}
