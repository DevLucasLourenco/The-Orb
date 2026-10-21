// Personagens: o Alter Ego (uma sessão, o líder) e os subagentes da Team. A cor é a do provider.
import * as THREE from "three";
import { CSS2DObject } from "three/addons/renderers/CSS2DRenderer.js";
import { STATE_LABEL, WAIT_COLOR, el, isAsleep, provider, sessionTitle } from "./providers.js";

const WORKING = new Set(["READING", "RESEARCHING", "CODING", "EXECUTING", "TESTING", "REVIEWING"]);
// Subagente sem sinal (R7, D-050): cinza neutro, translúcido, sem halo e com o ícone de sinal cortado.
const NO_SIGNAL_COLOR = new THREE.Color(0x8a909c);
const NO_SIGNAL_OPACITY = 0.4;
// A cabeça é o tom do corpo clareado.
const headTone = (color) => color.clone().lerp(new THREE.Color(0xffffff), 0.35);

// Os ícones neutros sobre a cabeça (R52, D-095, V-EGO-15): nunca em vermelho (o vermelho é do git). São sprites: sempre de frente para a câmera.
function iconSprite(draw) {
  const canvas = document.createElement("canvas");
  canvas.width = canvas.height = 64;
  draw(canvas.getContext("2d"));
  const map = new THREE.CanvasTexture(canvas);
  map.colorSpace = THREE.SRGBColorSpace;
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map, transparent: true, depthWrite: false, toneMapped: false }));
  sprite.scale.setScalar(1.1);
  sprite.visible = false;
  return sprite;
}

// Sinal cortado (barras de sinal e um traço): o subagente sem sinal (V-EGO-10) e o líder sem sinal.
const lostSignalSprite = () => iconSprite((g) => {
  g.fillStyle = "#c9d0dc";
  [14, 26, 38].forEach((h, i) => g.fillRect(10 + 16 * i, 54 - h, 10, h));
  g.lineCap = "round";
  g.beginPath(); g.moveTo(8, 56); g.lineTo(56, 8);
  g.strokeStyle = "#0b1020"; g.lineWidth = 11; g.stroke();
  g.strokeStyle = "#ffffff"; g.lineWidth = 5; g.stroke();
});

// Erro: um triângulo branco com "!".
const errorSprite = () => iconSprite((g) => {
  g.lineJoin = "round";
  g.beginPath(); g.moveTo(32, 6); g.lineTo(58, 54); g.lineTo(6, 54); g.closePath();
  g.fillStyle = "#f4f6fb"; g.fill();
  g.strokeStyle = "#0b1020"; g.lineWidth = 3; g.stroke();
  g.fillStyle = "#0b1020";
  g.fillRect(29, 22, 6, 18);
  g.beginPath(); g.arc(32, 46, 3.6, 0, Math.PI * 2); g.fill();
});

// Bloqueado: um cadeado branco.
const lockSprite = () => iconSprite((g) => {
  g.strokeStyle = "#f4f6fb"; g.lineWidth = 6; g.lineCap = "round";
  g.beginPath(); g.moveTo(20, 30); g.lineTo(20, 22); g.arc(32, 22, 12, Math.PI, 0); g.lineTo(44, 30); g.stroke();
  g.fillStyle = "#f4f6fb"; g.beginPath(); g.roundRect(14, 30, 36, 26, 5); g.fill();
  g.fillStyle = "#0b1020"; g.beginPath(); g.arc(32, 41, 3.8, 0, Math.PI * 2); g.fill(); g.fillRect(30, 41, 4, 9);
});

// Os estados do líder que deixam o corpo apagado (erro e sem sinal); os ícones de cada estado saem de `update`.
const DIM_STATES = new Set(["ERROR", "NO_SIGNAL"]);
const LEAVE_REACH = 0.7;      // o subagente que terminou chega ao líder quando está a esta distância dele (R51)

export class Avatar {
  constructor(scene, { id, providerName, sub = false }) {
    this.scene = scene;
    this.id = id;
    this.sub = sub;
    this.state = "IDLE";
    this.asleep = false;
    this.waiting = false;
    this.noSignal = false;
    this.hidden = false;          // a sala cheia (R33): quem passou dos 8 de um lugar não aparece, só conta no "+N"
    this.leaving = false;         // o subagente que terminou caminha até o líder e então sai (R51)
    this.gone = false;
    this.target = null;
    this.phase = Math.random() * Math.PI * 2;

    const color = new THREE.Color(provider(providerName).color);
    this.color = color;
    const group = (this.group = new THREE.Group());
    const body = (this.body = new THREE.Mesh(new THREE.CapsuleGeometry(0.46, 0.95, 6, 14),
      new THREE.MeshStandardMaterial({ color, roughness: 0.42, metalness: 0.1, emissive: color, emissiveIntensity: 0.12 })));
    body.position.y = 0.95;
    this.headColor = headTone(color);
    const head = (this.head = new THREE.Mesh(new THREE.SphereGeometry(0.4, 24, 16),
      new THREE.MeshStandardMaterial({ color: this.headColor, roughness: 0.35 })));
    head.position.y = 2.0;
    const visor = new THREE.Mesh(new THREE.BoxGeometry(0.46, 0.14, 0.12),
      new THREE.MeshBasicMaterial({ color: 0xe8f4ff, toneMapped: false }));
    visor.position.set(0, 2.03, 0.35);
    this.halo = new THREE.Mesh(new THREE.TorusGeometry(0.42, 0.05, 8, 40),
      new THREE.MeshBasicMaterial({ color, toneMapped: false }));
    this.halo.rotation.x = Math.PI / 2;
    this.halo.position.y = 2.72;
    // Marcador de espera: um losango magenta girando sobre a cabeça.
    this.alert = new THREE.Mesh(new THREE.OctahedronGeometry(0.34),
      new THREE.MeshBasicMaterial({ color: new THREE.Color(WAIT_COLOR), toneMapped: false, transparent: true }));
    this.alert.position.y = 3.35;
    this.alert.visible = false;
    // Sem sinal (subagente ou líder), erro e bloqueado (só o líder): ícone neutro sobre a cabeça.
    this.lostSignal = lostSignalSprite();
    this.errorIcon = errorSprite();
    this.lockIcon = lockSprite();
    for (const icon of [this.lostSignal, this.errorIcon, this.lockIcon]) icon.position.y = 3.3;
    // Pensando: três pontos orbitando.
    this.thoughts = new THREE.Group();
    for (let i = 0; i < 3; i++) {
      const dot = new THREE.Mesh(new THREE.SphereGeometry(0.08, 8, 8), new THREE.MeshBasicMaterial({ color: 0xdff0ff, toneMapped: false }));
      dot.userData.i = i;
      this.thoughts.add(dot);
    }
    this.thoughts.position.y = 2.75;
    this.thoughts.visible = false;
    const shadow = new THREE.Mesh(new THREE.CircleGeometry(0.62, 24),
      new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.35, depthWrite: false }));
    shadow.rotation.x = -Math.PI / 2;
    shadow.position.y = 0.04;
    group.add(body, head, visor, this.halo, this.alert, this.lostSignal, this.errorIcon, this.lockIcon, this.thoughts, shadow);
    body.castShadow = head.castShadow = true;
    if (sub) group.scale.setScalar(0.62);

    this.pickables = [body, head];
    for (const mesh of this.pickables) mesh.userData.avatarId = id;

    if (!sub) {
      this.labelEl = el("div", "lbl-ego");
      this.labelEl.style.setProperty("--pc", provider(providerName).color);
      this.label = new CSS2DObject(this.labelEl);
      this.label.position.y = 3.9;
      group.add(this.label);
    }
    scene.add(group);
  }

  placeAt(position) {
    this.group.position.copy(position);
    this.target = position.clone();
  }

  moveTo(position) {
    if (!this.target) this.placeAt(position);
    else this.target.copy(position);
  }

  setEgo(ego) {
    this.state = ego.state;
    this.asleep = isAsleep(ego);
    this.waiting = ego.state === "WAITING" || (ego.waiting && ego.waiting.length > 0);
    if (!this.labelEl) return;
    this.labelEl.classList.toggle("waiting", this.waiting);
    this.labelEl.classList.toggle("named", Boolean(ego.name));       // sem nome, o título continua sendo a linha forte
    const status = this.waiting
      ? `esperando você · ${ego.waiting?.[0]?.action || ""}`
      : `${STATE_LABEL[ego.state] || ego.state}${ego.last_action ? " · " + ego.last_action : ""}`;
    // Nome histórico em destaque (identidade, V-EGO-11); embaixo "provider · título"; depois atividade e última ação (V-EGO-8).
    const lines = [el("div", "t", `${provider(ego.provider).label} · ${sessionTitle(ego)}`), el("div", "s", status)];
    if (ego.name) lines.unshift(el("div", "n", `${ego.name} · ${ego.xp.level}`));       // o nível ao lado do nome (V-EGO-13)
    this.labelEl.replaceChildren(...lines);
  }

  // O mundo decide quem está sem sinal (`no_signal`); aqui só se desenha.
  setSub(sub) {
    this.state = sub.state;
    this.asleep = !sub.active;
    this._setNoSignal(Boolean(sub.no_signal));
  }

  // A sala cheia: o personagem que não coube fica fora de cena (e do clique); o overview continua listando.
  setHidden(on) {
    this.hidden = on;
    this.group.visible = !on;
  }

  // O subagente que terminou (`subagent.ended`): caminha até o líder, e quando chega o Avatar fica `gone` para quem o criou tirá-lo de cena.
  leaveTo(position) {
    this.leaving = true;
    this.setHidden(false);
    this.moveTo(position);
  }

  _setNoSignal(on) {
    if (on === this.noSignal) return;
    this.noSignal = on;
    const body = on ? NO_SIGNAL_COLOR : this.color;
    this.body.material.color.copy(body);
    this.body.material.emissive.copy(body);
    this.head.material.color.copy(on ? headTone(NO_SIGNAL_COLOR) : this.headColor);
    this.head.material.transparent = on;
    this.head.material.opacity = on ? NO_SIGNAL_OPACITY : 1;
  }

  update(dt, t, showLabel) {
    const g = this.group;
    if (this.target) {
      const delta = new THREE.Vector3().subVectors(this.target, g.position).setY(0);
      const dist = delta.length();
      if (dist > 0.05) {
        const step = Math.min(dist, (this.sub ? 7 : 6) * dt);
        g.position.addScaledVector(delta.normalize(), step);
        const yaw = Math.atan2(delta.x, delta.z);
        g.rotation.y += shortAngle(yaw - g.rotation.y) * Math.min(1, dt * 10);
      }
      g.position.y = this.target.y;
    }
    if (this.leaving && this.target && g.position.distanceTo(this.target) < LEAVE_REACH) this.gone = true;
    const walking = this.target && g.position.distanceTo(this.target) > 0.1;
    const working = WORKING.has(this.state);
    const bob = walking ? Math.abs(Math.sin(t * 9 + this.phase)) * 0.18 : working ? Math.sin(t * 5 + this.phase) * 0.06 : Math.sin(t * 1.6 + this.phase) * 0.03;
    this.body.position.y = 0.95 + bob;
    this.head.position.y = 2.0 + bob;
    this.head.rotation.x = this.asleep ? 0.5 : working ? Math.sin(t * 2.2 + this.phase) * 0.08 : 0;
    const leaderDim = !this.sub && DIM_STATES.has(this.state);          // erro e sem sinal do líder: corpo apagado, sem halo (R52)
    this.halo.visible = !this.asleep && !this.noSignal && !leaderDim;
    this.halo.rotation.z += dt * (working ? 2.4 : 0.6);
    this.halo.position.y = 2.72 + bob;
    const faded = this.asleep || this.noSignal || leaderDim;
    this.body.material.emissiveIntensity = faded ? 0.02 : working ? 0.32 : 0.12;
    this.body.material.transparent = faded;
    this.body.material.opacity = this.noSignal ? NO_SIGNAL_OPACITY : this.asleep ? 0.45 : leaderDim ? 0.7 : 1;
    const leader = !this.sub;
    this.lostSignal.visible = this.noSignal || (leader && this.state === "NO_SIGNAL");
    this.errorIcon.visible = leader && this.state === "ERROR";
    this.lockIcon.visible = leader && this.state === "BLOCKED";
    for (const icon of [this.lostSignal, this.errorIcon, this.lockIcon]) if (icon.visible) icon.position.y = 3.3 + Math.sin(t * 2) * 0.06;
    this.alert.visible = this.waiting;                                  // o magenta de quem espera o Lucas nunca some (R30)
    if (this.waiting) {
      this.alert.rotation.y += dt * 2.5;
      this.alert.material.opacity = 0.6 + 0.4 * (0.5 + 0.5 * Math.sin(t * 3.2));      // pulsa no mesmo ritmo do feixe e do anel
      this.alert.position.y = 3.35 + Math.sin(t * 4) * 0.12;
    }
    this.thoughts.visible = this.state === "THINKING" && !this.asleep;
    if (this.thoughts.visible) {
      for (const dot of this.thoughts.children) {
        const a = t * 2.4 + dot.userData.i * 2.09;
        dot.position.set(Math.cos(a) * 0.55, 0.15 + Math.sin(t * 3 + dot.userData.i) * 0.08, Math.sin(a) * 0.55);
      }
    }
    if (this.label) this.label.visible = showLabel && !this.hidden;
  }

  dispose() {
    this.scene.remove(this.group);
    this.group.traverse((o) => {
      o.geometry?.dispose?.();
      o.material?.map?.dispose?.();
      o.material?.dispose?.();
      if (o.isCSS2DObject) o.element.remove();
    });
  }
}

function shortAngle(a) {
  return Math.atan2(Math.sin(a), Math.cos(a));
}
