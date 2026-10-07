// Um Realm: o prédio do projeto, com o Rooftop Room de vidro no teto e as 5 áreas do Environment.
import * as THREE from "three";
import { CSS2DObject } from "three/addons/renderers/CSS2DRenderer.js";
import { el } from "./providers.js";

export const ROOF = 18;          // lado do prédio e do quartinho
export const TOWER_H = 36;
export const ROOM_H = 5.5;
const FLOOR_Y = TOWER_H + 0.55;  // piso do Rooftop Room

// Áreas do Environment no piso do quartinho (x, z, largura, profundidade, cor). +z = frente.
export const AREAS = {
  "Development Center": { x: -4.7, z: 3.9, w: 6.6, d: 5.2, color: 0x3aa0ff },
  "Testing Lab":        { x: 4.7,  z: 3.9, w: 6.6, d: 5.2, color: 0x8be04e },
  "Research Center":    { x: -4.7, z: -3.9, w: 6.6, d: 5.2, color: 0x9d7bff },
  "Code Review":        { x: 4.7,  z: -3.9, w: 6.6, d: 5.2, color: 0xffcc4d },
  "Task Board":         { x: 0,    z: -7.3, w: 3.2, d: 2.2, color: 0xff6fa5 },
};
const LOBBY = { x: 0, z: 0.2, r: 1.9 };          // quem não está numa área (pensando, parado, esperando)
const DORM = { z: 7.9, x0: -7.6, x1: 7.6 };      // sessões dormindo: fileira na frente do quartinho

function windowTexture(seed) {
  const c = document.createElement("canvas");
  c.width = 128; c.height = 256;
  const g = c.getContext("2d");
  g.fillStyle = "#000"; g.fillRect(0, 0, 128, 256);
  let s = seed;
  const rnd = () => ((s = (s * 9301 + 49297) % 233280) / 233280);
  for (let row = 0; row < 22; row++) {
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

export class RealmBuilding {
  constructor(realm, scene) {
    this.id = realm.id;
    this.scene = scene;
    this.group = new THREE.Group();
    this.pickables = [];
    this.activity = 0;           // 0..1, acende as janelas
    this.waiting = 0;

    const plinth = new THREE.Mesh(new THREE.BoxGeometry(ROOF + 6, 1.2, ROOF + 6),
      new THREE.MeshStandardMaterial({ color: 0x0e1626, roughness: 0.8, metalness: 0.2 }));
    plinth.position.y = 0.6;
    plinth.receiveShadow = true;

    const plain = new THREE.MeshStandardMaterial({ color: 0x0c1322, roughness: 0.6, metalness: 0.45 });
    this.windows = new THREE.MeshStandardMaterial({
      color: 0x0d1526, roughness: 0.45, metalness: 0.55, emissive: 0xffffff,
      emissiveMap: windowTexture(hash(realm.id)), emissiveIntensity: 0.35,
    });
    const tower = new THREE.Mesh(new THREE.BoxGeometry(ROOF, TOWER_H, ROOF),
      [this.windows, this.windows, plain, plain, this.windows, this.windows]);
    tower.position.y = TOWER_H / 2 + 1.2;
    tower.castShadow = true;
    tower.receiveShadow = true;
    const edges = new THREE.LineSegments(new THREE.EdgesGeometry(tower.geometry),
      new THREE.LineBasicMaterial({ color: 0x2c5a92, transparent: true, opacity: 0.55 }));
    edges.position.copy(tower.position);

    const slab = new THREE.Mesh(new THREE.BoxGeometry(ROOF + 0.8, 0.5, ROOF + 0.8),
      new THREE.MeshStandardMaterial({ color: 0x131d31, roughness: 0.92, metalness: 0.1 }));
    slab.position.y = TOWER_H + 1.2 + 0.05;
    slab.receiveShadow = true;
    this.floorY = slab.position.y + 0.3;

    // Rooftop Room: vidro com arestas de luz.
    const roomGeo = new THREE.BoxGeometry(ROOF, ROOM_H, ROOF);
    // Vidro sem iluminação: não reflete a luz interna (os reflexos viravam pontos estourados).
    const glass = new THREE.Mesh(roomGeo, new THREE.MeshBasicMaterial({
      color: 0x9cc8ff, transparent: true, opacity: 0.05, side: THREE.DoubleSide, depthWrite: false,
    }));
    glass.position.y = this.floorY + ROOM_H / 2;
    this.roomEdges = new THREE.LineSegments(new THREE.EdgesGeometry(roomGeo),
      new THREE.LineBasicMaterial({ color: 0x7cc4ff, toneMapped: false, transparent: true, opacity: 0.85 }));
    this.roomEdges.position.copy(glass.position);
    const light = new THREE.PointLight(0x9cc8ff, 22, 30, 1.4);
    light.position.y = this.floorY + ROOM_H + 2.5;

    this.group.add(plinth, tower, edges, slab, glass, this.roomEdges, light);
    this._areas();
    this._beacon();

    // Rótulo do prédio (visível de longe).
    this.labelEl = el("div", "lbl-realm");
    this.label = new CSS2DObject(this.labelEl);
    this.label.position.y = this.floorY + ROOM_H + 3.5;
    this.group.add(this.label);

    for (const mesh of [tower, glass, plinth]) {
      mesh.userData.realmId = this.id;
      this.pickables.push(mesh);
    }
    scene.add(this.group);
  }

  _areas() {
    this.areaLabels = [];
    for (const [name, a] of Object.entries(AREAS)) {
      const pad = new THREE.Mesh(new THREE.BoxGeometry(a.w, 0.12, a.d),
        new THREE.MeshStandardMaterial({ color: a.color, emissive: a.color, emissiveIntensity: 0.18, transparent: true, opacity: 0.35, roughness: 0.4 }));
      pad.position.set(a.x, this.floorY + 0.06, a.z);
      pad.receiveShadow = true;
      const edge = new THREE.LineSegments(new THREE.EdgesGeometry(pad.geometry),
        new THREE.LineBasicMaterial({ color: a.color, toneMapped: false, transparent: true, opacity: 0.9 }));
      edge.position.copy(pad.position);
      const label = new CSS2DObject(el("div", "lbl-area", name));
      label.position.set(a.x, this.floorY + 0.2, a.z + a.d / 2 - 0.4);
      this.areaLabels.push(label);
      this.group.add(pad, edge, label);
    }
    const lobby = new THREE.Mesh(new THREE.RingGeometry(LOBBY.r - 0.12, LOBBY.r, 48),
      new THREE.MeshBasicMaterial({ color: 0x7cc4ff, toneMapped: false, transparent: true, opacity: 0.5, side: THREE.DoubleSide }));
    lobby.rotation.x = -Math.PI / 2;
    lobby.position.set(LOBBY.x, this.floorY + 0.03, LOBBY.z);
    this.group.add(lobby);
  }

  _beacon() {
    // Feixe de luz âmbar: alguém deste realm está esperando o Lucas. Visível da cidade inteira.
    const mat = new THREE.MeshBasicMaterial({ color: 0xffb547, transparent: true, opacity: 0.0, toneMapped: false,
      blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide });
    this.beacon = new THREE.Mesh(new THREE.CylinderGeometry(1.1, 2.4, 140, 24, 1, true), mat);
    this.beacon.position.y = this.floorY + ROOM_H + 70;
    this.beaconRing = new THREE.Mesh(new THREE.TorusGeometry(ROOF * 0.72, 0.12, 8, 96),
      new THREE.MeshBasicMaterial({ color: 0xffb547, toneMapped: false, transparent: true, opacity: 0 }));
    this.beaconRing.rotation.x = Math.PI / 2;
    this.beaconRing.position.y = this.floorY + 0.25;
    this.group.add(this.beacon, this.beaconRing);
  }

  setPosition(x, z) {
    this.group.position.set(x, 0, z);
  }

  center() {
    return new THREE.Vector3(this.group.position.x, this.floorY, this.group.position.z);
  }

  setData(realm, summary) {
    this.activity = Math.min(1, summary.active / 3);
    this.waiting = summary.waiting;
    this.labelEl.replaceChildren(
      el("div", "n", realm.name || realm.id),
      (() => {
        const c = el("div", "c", `${summary.sessions} sessões · ${summary.active} ativas`);
        if (summary.waiting) c.append(" · ", el("span", "w", `${summary.waiting} esperando`));
        return c;
      })(),
    );
  }

  // Lugar no piso para o n-ésimo personagem de uma área (ou do lobby / dormitório).
  slot(area, index, count) {
    const p = this.group.position;
    if (area === "__dorm") {
      const x = count > 1 ? DORM.x0 + (DORM.x1 - DORM.x0) * (index / (count - 1)) : 0;
      return new THREE.Vector3(p.x + x, this.floorY, p.z + DORM.z);
    }
    const a = AREAS[area];
    const cx = a ? a.x : LOBBY.x, cz = a ? a.z : LOBBY.z;
    if (count <= 1) return new THREE.Vector3(p.x + cx, this.floorY, p.z + cz);
    const radius = a ? Math.min(a.w, a.d) * 0.32 : LOBBY.r * 0.75;
    const angle = (index / count) * Math.PI * 2 + 0.6;
    return new THREE.Vector3(p.x + cx + Math.cos(angle) * radius, this.floorY, p.z + cz + Math.sin(angle) * radius);
  }

  update(dt, t, near, focused = false) {
    const target = 0.28 + this.activity * 1.1;
    this.windows.emissiveIntensity += (target - this.windows.emissiveIntensity) * Math.min(1, dt * 2);
    const pulse = this.waiting ? 0.5 + 0.5 * Math.sin(t * 3.2) : 0;
    this.beacon.material.opacity = this.waiting ? 0.10 + 0.14 * pulse : 0;
    this.beaconRing.material.opacity = this.waiting ? 0.35 + 0.5 * pulse : 0;
    this.roomEdges.material.color.setHex(this.waiting ? 0xffc46b : 0x7cc4ff);
    for (const label of this.areaLabels) label.visible = near;
    this.label.visible = !focused;      // de perto o nome do prédio só atrapalha a sala
  }

  dispose() {
    this.scene.remove(this.group);
    this.group.traverse((o) => {
      o.geometry?.dispose?.();
      const mats = Array.isArray(o.material) ? o.material : o.material ? [o.material] : [];
      mats.forEach((m) => { m.emissiveMap?.dispose?.(); m.dispose?.(); });
      if (o.isCSS2DObject) o.element.remove();
    });
  }
}
