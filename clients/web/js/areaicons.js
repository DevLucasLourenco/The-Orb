// As áreas do Rooftop Room não têm cor própria (R20c, D-187): o piso é neutro e cada área se identifica pelo ícone, pelo nome e por um
// padrão desenhado no piso. Aqui só se desenha: o ícone e o padrão de cada área, num decalque transparente sobre o piso.
import * as THREE from "three";

const PX_PER_UNIT = 40;             // resolução do decalque: pixels por unidade do mundo
const INK = "#dfe7f5";              // traço do ícone (neutro)
const PATTERN_INK = "#9fb0cc";      // traço do padrão (neutro, bem fraco)
const PATTERN_ALPHA = 0.16;
const STEP = 30;                    // espaço entre as marcas do padrão, em pixels

// Ícones numa grade de 64 x 64 (traço, sem preenchimento): código, frasco, lupa, olho, quadro de tarefas.
const ICONS = {
  code: (g) => {
    g.moveTo(22, 20); g.lineTo(10, 32); g.lineTo(22, 44);
    g.moveTo(42, 20); g.lineTo(54, 32); g.lineTo(42, 44);
    g.moveTo(36, 16); g.lineTo(28, 48);
  },
  flask: (g) => {
    g.moveTo(24, 10); g.lineTo(40, 10);
    g.moveTo(28, 10); g.lineTo(28, 28); g.lineTo(14, 52); g.lineTo(50, 52); g.lineTo(36, 28); g.lineTo(36, 10);
    g.moveTo(20, 42); g.lineTo(44, 42);
  },
  lens: (g) => {
    g.moveTo(42, 28); g.arc(28, 28, 14, 0, Math.PI * 2);
    g.moveTo(38, 38); g.lineTo(52, 52);
  },
  eye: (g) => {
    g.moveTo(8, 32); g.quadraticCurveTo(32, 6, 56, 32); g.quadraticCurveTo(32, 58, 8, 32);
    g.moveTo(39, 32); g.arc(32, 32, 7, 0, Math.PI * 2);
  },
  board: (g) => {
    g.rect(10, 12, 44, 40);
    g.moveTo(24, 12); g.lineTo(24, 52); g.moveTo(40, 12); g.lineTo(40, 52);
    g.rect(13, 17, 8, 8); g.rect(13, 29, 8, 8); g.rect(27, 17, 10, 8); g.rect(43, 17, 8, 8); g.rect(43, 29, 8, 8);
  },
};

// Padrões do piso, um por área: diagonais, pontos, grade, listras e xadrez. `filled`: as marcas são preenchidas, não traçadas.
const PATTERNS = {
  diagonal: { filled: false, draw: (g, w, h) => { for (let i = -h; i < w; i += STEP) { g.moveTo(i, h); g.lineTo(i + h, 0); } } },
  dots: { filled: true, draw: (g, w, h) => {
    for (let x = STEP / 2; x < w; x += STEP) for (let y = STEP / 2; y < h; y += STEP) { g.moveTo(x + 3, y); g.arc(x, y, 3, 0, Math.PI * 2); }
  } },
  grid: { filled: false, draw: (g, w, h) => {
    for (let x = 0; x < w; x += STEP) { g.moveTo(x, 0); g.lineTo(x, h); }
    for (let y = 0; y < h; y += STEP) { g.moveTo(0, y); g.lineTo(w, y); }
  } },
  stripes: { filled: false, draw: (g, w, h) => { for (let y = STEP / 3; y < h; y += STEP * 0.7) { g.moveTo(0, y); g.lineTo(w, y); } } },
  checker: { filled: true, draw: (g, w, h) => {
    for (let x = 0; x < w; x += STEP) for (let y = 0; y < h; y += STEP) if (((x + y) / STEP) % 2 === 0) g.rect(x, y, STEP, STEP);
  } },
};

// Ícone e padrão de cada área (o nome é o do vocabulário do mundo).
export const AREA_MARKS = {
  "Development Center": { icon: "code", pattern: "diagonal" },
  "Testing Lab":        { icon: "flask", pattern: "dots" },
  "Research Center":    { icon: "lens", pattern: "grid" },
  "Code Review":        { icon: "eye", pattern: "stripes" },
  "Task Board":         { icon: "board", pattern: "checker" },
};

// O decalque de uma área (largura x profundidade em unidades do mundo): padrão no piso todo e o ícone no fundo da área, longe do
// nome (que fica na frente) e do lugar onde o personagem para. Transparente: a cor do piso é a do pad (neutra).
export function areaDecal(name, w, d) {
  const mark = AREA_MARKS[name];
  if (!mark) throw new Error(`área sem ícone e padrão em AREA_MARKS: ${name}`);        // AREAS e AREA_MARKS andam juntas
  const canvas = document.createElement("canvas");
  canvas.width = Math.round(w * PX_PER_UNIT);
  canvas.height = Math.round(d * PX_PER_UNIT);
  const g = canvas.getContext("2d");
  const pattern = PATTERNS[mark.pattern];
  g.globalAlpha = PATTERN_ALPHA;
  g.strokeStyle = g.fillStyle = PATTERN_INK;
  g.lineWidth = 1.5;
  g.beginPath();
  pattern.draw(g, canvas.width, canvas.height);
  if (pattern.filled) g.fill(); else g.stroke();
  g.globalAlpha = 0.9;
  const size = Math.min(canvas.width, canvas.height) * 0.42;
  const k = size / 64;
  g.save();
  g.translate((canvas.width - size) / 2, canvas.height * 0.34 - size / 2);
  g.scale(k, k);
  g.strokeStyle = INK;
  g.lineWidth = Math.max(3.2, 2.5 / k);
  g.lineCap = g.lineJoin = "round";
  g.beginPath();
  ICONS[mark.icon](g);
  g.stroke();
  g.restore();
  const map = new THREE.CanvasTexture(canvas);
  map.colorSpace = THREE.SRGBColorSpace;
  map.anisotropy = 4;
  return map;
}
