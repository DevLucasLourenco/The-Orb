// O palco 3D: renderizador, câmera estilo RTS, luzes, o disco do Orb, brilho e rótulos.
import * as THREE from "three";
import { MapControls } from "three/addons/controls/MapControls.js";
import { CSS2DRenderer } from "three/addons/renderers/CSS2DRenderer.js";
import { EffectComposer } from "three/addons/postprocessing/EffectComposer.js";
import { RenderPass } from "three/addons/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "three/addons/postprocessing/UnrealBloomPass.js";
import { OutputPass } from "three/addons/postprocessing/OutputPass.js";

const SKY = 0x070b16;
const ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);

export class Stage {
  constructor(container) {
    this.container = container;
    const renderer = (this.renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" }));
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.05;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    container.appendChild(renderer.domElement);

    const scene = (this.scene = new THREE.Scene());
    scene.background = skyTexture();
    scene.fog = new THREE.FogExp2(0x0a1222, 0.0016);

    const camera = (this.camera = new THREE.PerspectiveCamera(42, container.clientWidth / container.clientHeight, 0.5, 5000));
    camera.position.set(0, 170, 210);

    this.labels = new CSS2DRenderer();
    this.labels.setSize(container.clientWidth, container.clientHeight);
    Object.assign(this.labels.domElement.style, { position: "absolute", top: "0", left: "0", pointerEvents: "none" });
    container.appendChild(this.labels.domElement);

    const controls = (this.controls = new MapControls(camera, renderer.domElement));
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.screenSpacePanning = false;
    controls.minDistance = 14;
    controls.maxDistance = 900;
    controls.maxPolarAngle = 1.38;
    controls.target.set(0, 20, 0);
    controls.addEventListener("start", () => (this.flight = null));

    this._lights();
    this._ground();
    this._stars();

    this.composer = new EffectComposer(renderer);
    this.composer.addPass(new RenderPass(scene, camera));
    this.bloom = new UnrealBloomPass(new THREE.Vector2(container.clientWidth, container.clientHeight), 0.8, 0.55, 0.78);
    this.composer.addPass(this.bloom);
    this.composer.addPass(new OutputPass());

    this.clock = new THREE.Clock();
    this.keys = new Set();
    this.flight = null;
    this.raycaster = new THREE.Raycaster();
    this.onFrame = () => {};
    window.addEventListener("resize", () => this.resize());
    window.addEventListener("keydown", (e) => { if (!isTyping(e)) this.keys.add(e.key.toLowerCase()); });
    window.addEventListener("keyup", (e) => this.keys.delete(e.key.toLowerCase()));
    window.addEventListener("blur", () => this.keys.clear());
  }

  _lights() {
    this.scene.add(new THREE.HemisphereLight(0x9cc2ff, 0x141a2c, 1.1));
    this.scene.add(new THREE.AmbientLight(0x26324f, 0.9));
    const moon = (this.moon = new THREE.DirectionalLight(0xd6e2ff, 1.9));
    moon.position.set(-160, 260, 120);
    moon.castShadow = true;
    moon.shadow.mapSize.set(2048, 2048);
    const s = moon.shadow.camera;
    s.left = -260; s.right = 260; s.top = 260; s.bottom = -260; s.near = 10; s.far = 800;
    moon.shadow.bias = -0.0005;
    this.scene.add(moon);
  }

  _ground() {
    // O Orb: um disco flutuante, com borda de luz e uma grade discreta.
    const group = (this.ground = new THREE.Group());
    const disc = new THREE.Mesh(
      new THREE.CylinderGeometry(1, 1, 6, 128, 1),
      new THREE.MeshStandardMaterial({ color: 0x15213a, roughness: 0.85, metalness: 0.2, emissive: 0x0a1630, emissiveIntensity: 0.6 }),
    );
    disc.position.y = -3;
    disc.receiveShadow = true;
    const rim = new THREE.Mesh(
      new THREE.TorusGeometry(1, 0.006, 8, 256),
      new THREE.MeshBasicMaterial({ color: 0x5fb6ff, toneMapped: false }),
    );
    rim.rotation.x = Math.PI / 2;
    const grid = new THREE.PolarGridHelper(1, 24, 12, 128, 0x2a5a96, 0x1d3d66);
    grid.position.y = 0.02;
    grid.material.transparent = true;
    grid.material.opacity = 0.6;
    group.add(disc, rim, grid);
    this.scene.add(group);
    this.setGroundRadius(160);
  }

  _stars() {
    const n = 1800;
    const pos = new Float32Array(n * 3);
    for (let i = 0; i < n; i++) {
      const v = new THREE.Vector3().randomDirection().multiplyScalar(1500 + Math.random() * 600);
      v.y = Math.abs(v.y) * 0.9 + 40;
      pos.set([v.x, v.y, v.z], i * 3);
    }
    const geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    const stars = new THREE.Points(geo, new THREE.PointsMaterial({ color: 0xaecbff, size: 2.2, sizeAttenuation: false, fog: false, transparent: true, opacity: 0.75 }));
    this.scene.add(stars);
  }

  setGroundRadius(r) {
    this.ground.scale.set(r, 1, r);
    this.ground.children[1].scale.set(1, 1, 1);
    this.groundRadius = r;
  }

  resize() {
    const w = this.container.clientWidth, h = this.container.clientHeight;
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(w, h);
    this.labels.setSize(w, h);
    this.composer.setSize(w, h);
  }

  // Voa até um ponto, mantendo o ângulo horizontal atual da câmera.
  flyTo(target, distance, elevation = 0.82) {
    const azimuth = Math.atan2(this.camera.position.x - this.controls.target.x, this.camera.position.z - this.controls.target.z);
    const to = new THREE.Vector3(
      target.x + Math.sin(azimuth) * Math.cos(elevation) * distance,
      target.y + Math.sin(elevation) * distance,
      target.z + Math.cos(azimuth) * Math.cos(elevation) * distance,
    );
    // O voo avança pelo relógio real: não fica lento quando o navegador reduz a taxa de quadros.
    this.flight = { start: performance.now(), dur: 1100, fromPos: this.camera.position.clone(), toPos: to,
                    fromTarget: this.controls.target.clone(), toTarget: target.clone() };
  }

  pick(clientX, clientY, objects) {
    const rect = this.renderer.domElement.getBoundingClientRect();
    const ndc = new THREE.Vector2(((clientX - rect.left) / rect.width) * 2 - 1, -((clientY - rect.top) / rect.height) * 2 + 1);
    this.raycaster.setFromCamera(ndc, this.camera);
    return this.raycaster.intersectObjects(objects, true)[0] || null;
  }

  distance() {
    return this.camera.position.distanceTo(this.controls.target);
  }

  _keyboard(dt) {
    if (!this.keys.size) return;
    const k = this.keys;
    const target = this.controls.target, cam = this.camera.position;
    const forward = new THREE.Vector3().subVectors(target, cam).setY(0).normalize();
    const right = new THREE.Vector3().crossVectors(forward, new THREE.Vector3(0, 1, 0)).normalize();
    const speed = Math.max(30, this.distance()) * 0.9 * dt;
    const move = new THREE.Vector3();
    if (k.has("w")) move.add(forward);
    if (k.has("s")) move.sub(forward);
    if (k.has("d")) move.add(right);
    if (k.has("a")) move.sub(right);
    if (move.lengthSq()) {
      move.normalize().multiplyScalar(speed);
      cam.add(move);
      target.add(move);
      this.flight = null;
    }
    const turn = (k.has("q") ? 1 : 0) - (k.has("e") ? 1 : 0);
    if (turn) {
      const offset = new THREE.Vector3().subVectors(cam, target).applyAxisAngle(new THREE.Vector3(0, 1, 0), turn * 1.4 * dt);
      cam.copy(target).add(offset);
      this.flight = null;
    }
  }

  start() {
    const loop = () => {
      const dt = Math.min(this.clock.getDelta(), 0.25);   // movimento pelo tempo real, mesmo com poucos quadros
      const t = this.clock.elapsedTime;
      if (this.flight) {
        const f = this.flight;
        const k = Math.min(1, (performance.now() - f.start) / f.dur);
        const e = ease(k);
        this.camera.position.lerpVectors(f.fromPos, f.toPos, e);
        this.controls.target.lerpVectors(f.fromTarget, f.toTarget, e);
        if (k >= 1) this.flight = null;
      }
      this._keyboard(dt);
      this.controls.update();
      this.onFrame(dt, t);
      this.composer.render();
      this.labels.render(this.scene, this.camera);
      requestAnimationFrame(loop);
    };
    requestAnimationFrame(loop);
  }
}

function skyTexture() {
  // Céu noturno em degradê: azul profundo no alto, um brilho frio no horizonte.
  const c = document.createElement("canvas");
  c.width = 4; c.height = 512;
  const g = c.getContext("2d");
  const grad = g.createLinearGradient(0, 0, 0, 512);
  grad.addColorStop(0, "#03050c");
  grad.addColorStop(0.55, "#0a1430");
  grad.addColorStop(0.8, "#16244a");
  grad.addColorStop(1, "#1b2a52");
  g.fillStyle = grad;
  g.fillRect(0, 0, 4, 512);
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

function isTyping(e) {
  const tag = (e.target && e.target.tagName) || "";
  return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || (e.target && e.target.closest && e.target.closest(".xterm"));
}
