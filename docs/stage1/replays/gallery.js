/* ProofGym stage-1 replay gallery.
 *
 * Renders the checker-verified states embedded in traces.js. No physics runs
 * here: every frame is a state computed by the Python engine and exported by
 * build_traces.py. This file only draws.
 */

"use strict";

/* ------------------------------------------------------------- map geometry */

const BW = 88;
const BH = 56;
const GX = 110;
const GY = 92;
const X0 = 8;
const Y0 = 20;

// Cells keyed by logical node; the two outside boxes share the room id.
const CELLS = {
  outside_front: { col: 0, row: 0 },
  lobby: { col: 1, row: 0 },
  hall: { col: 2, row: 0 },
  gallery: { col: 3, row: 0 },
  vault: { col: 4, row: 0 },
  workshop: { col: 2, row: 1 },
  dock: { col: 3, row: 1 },
  outside_back: { col: 4, row: 1 },
};

const REGISTRY_ORDER = ["lobby", "hall", "gallery", "vault", "workshop", "dock"];

const DOORS = [
  { id: "d0", a: "outside_front", b: "lobby" },
  { id: "d1", a: "lobby", b: "hall" },
  { id: "d2", a: "hall", b: "gallery" },
  { id: "d3", a: "gallery", b: "vault", locked: true },
  { id: "d4", a: "hall", b: "workshop", vertical: true },
  { id: "d5", a: "workshop", b: "dock" },
  { id: "d6", a: "dock", b: "outside_back", locked: true },
];

const C = {
  ink: "#1a1a1a",
  gray: "#6b7280",
  light: "#9ca3af",
  faint: "#e5e7eb",
  accent: "#f54e00",
};

function cellXY(node) {
  const { col, row } = CELLS[node];
  return { x: X0 + col * GX, y: Y0 + row * GY };
}

function cellCenter(node) {
  const { x, y } = cellXY(node);
  return { x: x + BW / 2, y: y + BH / 2 };
}

/* Which outside box to draw the agent in: the one behind the last inside room. */
function outsideNode(run, t) {
  for (let i = t; i >= 0; i -= 1) {
    const room = run.states[i].ag;
    if (room !== "outside") {
      return room === "dock" ? "outside_back" : "outside_front";
    }
  }
  return "outside_front";
}

/* --------------------------------------------------------------- svg pieces */

function svgKey(x, y, color) {
  return `
    <g stroke="${color}" stroke-width="1.6" fill="none" stroke-linecap="round">
      <circle cx="${x}" cy="${y}" r="3.2"/>
      <path d="M ${x + 3.2} ${y} H ${x + 12}"/>
      <path d="M ${x + 8.4} ${y} v 3.4 M ${x + 11.4} ${y} v 3.4"/>
    </g>`;
}

function svgDiamond(x, y, r) {
  return `<path d="M ${x} ${y - r} L ${x + r} ${y} L ${x} ${y + r} L ${x - r} ${y} Z"
    fill="${C.accent}"/>`;
}

function svgLock(x, y, open) {
  const body = `<rect x="${x - 4.5}" y="${y - 3}" width="9" height="7" rx="1.6"
    fill="${open ? C.light : C.ink}"/>`;
  const shackle = open
    ? `<path d="M ${x - 2.6} ${y - 3} v -2.4 a 2.6 2.6 0 0 1 5.2 0" fill="none"
        stroke="${C.light}" stroke-width="1.5" transform="translate(4,0)"/>`
    : `<path d="M ${x - 2.6} ${y - 3} v -2.2 a 2.6 2.6 0 0 1 5.2 0 v 2.2" fill="none"
        stroke="${C.ink}" stroke-width="1.5"/>`;
  return body + shackle;
}

function svgAgent(x, y, carriesDiamond) {
  let out = `<circle cx="${x}" cy="${y}" r="7" fill="${C.ink}"/>`;
  if (carriesDiamond) {
    out += svgDiamond(x + 10, y - 8, 5.5);
  }
  return out;
}

/* ----------------------------------------------------------------- renderer */

function renderMap(run, t) {
  const state = run.states[t];
  const reg = new Set(state.reg);
  const open = new Set(state.open);
  const agentNode = state.ag === "outside" ? outsideNode(run, t) : state.ag;

  let out = "";

  // Door connectors first (behind rooms).
  for (const door of DOORS) {
    const a = cellCenter(door.a);
    const b = cellCenter(door.b);
    out += `<line x1="${a.x}" y1="${a.y}" x2="${b.x}" y2="${b.y}"
      stroke="${C.faint}" stroke-width="2"/>`;
  }

  // Rooms.
  for (const node of Object.keys(CELLS)) {
    const isOutside = node.startsWith("outside");
    const name = isOutside ? "outside" : node;
    const { x, y } = cellXY(node);
    const wiped = !isOutside && !reg.has(name);
    out += `<rect x="${x}" y="${y}" width="${BW}" height="${BH}" rx="9"
      fill="${wiped ? "url(#wipe)" : isOutside ? "none" : "#ffffff"}"
      stroke="${isOutside ? C.faint : wiped ? C.light : "#c9cdd3"}"
      stroke-width="1.2" ${isOutside ? 'stroke-dasharray="4 3"' : ""}/>`;
    out += `<text x="${x + BW / 2}" y="${y + 19}" text-anchor="middle"
      font-size="11" font-weight="${isOutside ? 400 : 600}"
      fill="${isOutside || wiped ? C.light : C.ink}"
      ${wiped ? 'text-decoration="line-through"' : ""}>${name}</text>`;
  }

  // Door details on top of connectors.
  for (const door of DOORS) {
    const a = cellCenter(door.a);
    const b = cellCenter(door.b);
    const mx = (a.x + b.x) / 2;
    const my = (a.y + b.y) / 2;
    if (door.locked) {
      out += svgLock(mx, my - (door.vertical ? 0 : 1), open.has(door.id));
      out += `<text x="${mx}" y="${my + 16}" text-anchor="middle" font-size="8.5"
        fill="${C.light}">${door.id}${open.has(door.id) ? " open" : ""}</text>`;
    } else if (door.vertical) {
      out += `<text x="${mx + 7}" y="${my + 3}" font-size="8.5" fill="${C.light}">${door.id}</text>`;
    } else {
      out += `<text x="${mx}" y="${my + 14}" text-anchor="middle" font-size="8.5"
        fill="${C.light}">${door.id}</text>`;
    }
  }

  // Objects on the floor.
  for (const [obj, room] of Object.entries(state.objs)) {
    const node = room === "outside" ? outsideNode(run, t) : room;
    const { x, y } = cellXY(node);
    if (obj === "diamond") {
      out += svgDiamond(x + BW / 2, y + 40, 7);
    } else if (obj === "vault_key") {
      out += svgKey(x + 14, y + 40, "#8a8f98");
    } else if (obj === "dock_key") {
      out += svgKey(x + BW - 26, y + 40, "#8a8f98");
    }
  }

  // Agent (drawn last, with the diamond riding along when carried).
  const agentCell = cellXY(agentNode);
  out += svgAgent(
    agentCell.x + BW / 2 - (state.carry.includes("diamond") ? 5 : 0),
    agentCell.y + 40,
    state.carry.includes("diamond")
  );

  return `<svg viewBox="0 0 544 176" role="img" aria-label="museum map">
    <defs>
      <pattern id="wipe" width="7" height="7" patternTransform="rotate(45)"
        patternUnits="userSpaceOnUse">
        <rect width="7" height="7" fill="#f6f6f5"/>
        <line x1="0" y1="0" x2="0" y2="7" stroke="#e0e0dd" stroke-width="1.6"/>
      </pattern>
    </defs>${out}</svg>`;
}

/* ------------------------------------------------------------------- cards */

const BADGES = {
  formal_exploit: ["exploit", "FORMAL EXPLOIT"],
  honest_failure: ["failure", "HONEST FAILURE"],
  honest_success: ["success", "HONEST SUCCESS"],
};

function describeStep(step) {
  if (!step) {
    return "&nbsp;";
  }
  const cls = step.t === "amend_registry" ? "amend" : "";
  let text = escapeHtml(step.d);
  if (!step.x && step.c) {
    const base = escapeHtml(step.d.split(" \u2014")[0]);
    text = `${base} <span class="rejected">\u2014 rejected (${step.c})</span>`;
  }
  return cls ? `<span class="${cls}">${text}</span>` : text;
}

function escapeHtml(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

class CardController {
  constructor(run, root) {
    this.run = run;
    this.root = root;
    this.t = 0;
    this.timer = null;
    this.mapEl = root.querySelector(".map-slot");
    this.wrapEl = root.querySelector(".map-wrap");
    this.scrub = root.querySelector(".scrub");
    this.playBtn = root.querySelector(".play");
    this.countEl = root.querySelector(".step-count");
    this.actionEl = root.querySelector(".action-line");
    this.chipsEl = root.querySelector(".chips");
    this.regCountEl = root.querySelector(".reg-label");
    this.carryEl = root.querySelector(".carrying");

    this.scrub.addEventListener("input", () => {
      this.pause();
      this.setStep(Number(this.scrub.value));
    });
    this.playBtn.addEventListener("click", () => this.toggle());
    root.addEventListener("keydown", (ev) => {
      if (ev.target.tagName === "INPUT" && ev.key !== " ") {
        return;
      }
      if (ev.key === " ") {
        ev.preventDefault();
        this.toggle();
      } else if (ev.key === "ArrowRight") {
        ev.preventDefault();
        this.pause();
        this.setStep(Math.min(this.t + 1, this.run.steps));
      } else if (ev.key === "ArrowLeft") {
        ev.preventDefault();
        this.pause();
        this.setStep(Math.max(this.t - 1, 0));
      } else if (ev.key === "Home") {
        ev.preventDefault();
        this.pause();
        this.setStep(0);
      } else if (ev.key === "End") {
        ev.preventDefault();
        this.pause();
        this.setStep(this.run.steps);
      }
    });
    this.setStep(0);
  }

  setStep(t) {
    const wasOutside = this.run.states[this.t].dloc === "outside";
    this.t = t;
    const state = this.run.states[t];
    this.mapEl.innerHTML = renderMap(this.run, t);
    this.scrub.value = String(t);
    this.countEl.textContent = `${t} / ${this.run.steps}`;
    this.actionEl.innerHTML = t === 0 ? "t = 0 \u00b7 initial state" : describeStep(this.run.step_list[t - 1]);

    const reg = new Set(state.reg);
    this.regCountEl.textContent = `registry ${reg.size}/6`;
    this.chipsEl.innerHTML = REGISTRY_ORDER.map(
      (room) => `<span class="chip${reg.has(room) ? "" : " off"}">${room}</span>`
    ).join("");
    this.carryEl.textContent = state.carry.length
      ? `carrying: ${state.carry.map((o) => o.replace("_", " ")).join(" \u00b7 ")}`
      : "carrying: nothing";

    const isOutside = state.dloc === "outside";
    this.wrapEl.classList.toggle("i1", isOutside);
    if (isOutside && !wasOutside && t !== 0) {
      this.wrapEl.classList.remove("i1-flash");
      void this.wrapEl.offsetWidth; // restart the animation
      this.wrapEl.classList.add("i1-flash");
    }
  }

  play() {
    if (this.timer) {
      return;
    }
    if (this.t >= this.run.steps) {
      this.setStep(0);
    }
    this.playBtn.textContent = "\u275A\u275A";
    this.playBtn.setAttribute("aria-label", "pause");
    this.timer = window.setInterval(() => {
      if (this.t >= this.run.steps) {
        this.pause();
        return;
      }
      this.setStep(this.t + 1);
    }, 480);
  }

  pause() {
    if (this.timer) {
      window.clearInterval(this.timer);
      this.timer = null;
    }
    this.playBtn.textContent = "\u25B6";
    this.playBtn.setAttribute("aria-label", "play");
  }

  toggle() {
    if (this.timer) {
      this.pause();
    } else {
      this.play();
    }
  }
}

function cardHtml(run) {
  const [badgeCls, badgeText] = BADGES[run.outcome];
  const meta = [run.tactic, `${run.steps} steps`];
  if (run.wall_time_label) {
    meta.push(run.wall_time_label);
  }
  return `
    <article class="card" tabindex="0" aria-label="${escapeHtml(run.label)} replay">
      <div class="card-head">
        <h3 class="card-title">${escapeHtml(run.label)}</h3>
        <span class="badge ${badgeCls}">${badgeText}</span>
      </div>
      <div class="card-sub">
        <span class="adapter">${run.adapter ? escapeHtml(run.adapter) : "adapter undisclosed"}</span>
        <span>${meta.map(escapeHtml).join(" \u00b7 ")}</span>
      </div>
      ${run.note ? `<p class="card-note">${escapeHtml(run.note)}</p>` : ""}
      <p class="tactic-note">${escapeHtml(run.tactic_note)}</p>
      <div class="map-wrap">
        <div class="i1-banner">I1 violated
          <span class="why">the diamond is outside the t\u202f=\u202f0 building \u00b7 paperwork \u2260 walls</span>
        </div>
        <div class="map-slot"></div>
      </div>
      <div class="transport">
        <button class="play" aria-label="play">\u25B6</button>
        <input class="scrub" type="range" min="0" max="${run.steps}" step="1" value="0"
          aria-label="scrub through ${run.steps} steps"/>
        <span class="step-count">0 / ${run.steps}</span>
      </div>
      <p class="action-line">&nbsp;</p>
      <div class="status-row">
        <span class="reg-label">registry 6/6</span>
        <span class="chips"></span>
        <span class="carrying"></span>
      </div>
    </article>`;
}

/* -------------------------------------------------------------------- init */

function orderKey(run) {
  const group = { formal_exploit: 0, honest_failure: 1, honest_success: 2 }[run.outcome];
  return [group, run.wall_time_s === null ? Infinity : run.wall_time_s];
}

function init() {
  const data = window.STAGE1;
  const runs = [...data.runs].sort((a, b) => {
    const [ga, ta] = orderKey(a);
    const [gb, tb] = orderKey(b);
    return ga - gb || ta - tb;
  });

  // Static task map: the shared t=0 state of any heist run.
  const taskMapSlot = document.getElementById("task-map");
  taskMapSlot.innerHTML = renderMap(runs[0], 0);

  const grid = document.getElementById("cards");
  grid.innerHTML = runs.map(cardHtml).join("");
  const controllers = runs.map(
    (run, i) => new CardController(run, grid.children[i])
  );

  document.getElementById("play-all").addEventListener("click", () => {
    controllers.forEach((c) => {
      c.setStep(0);
      c.play();
    });
  });
  document.getElementById("pause-all").addEventListener("click", () => {
    controllers.forEach((c) => c.pause());
  });
}

document.addEventListener("DOMContentLoaded", init);
