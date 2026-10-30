// Bonfire Night layer for the Season 9 tides theme (static/js/tides-bg.js).
// Same API as halloween-bg.js: window.createBonfireLayer() -> { palette, sky, land, draw }.
// Additive: the tide scene stays; this adds three things:
//   - a beach bonfire on a sandbar right of the wheel, with onlookers, embers and a smoke plume;
//   - a firework display over the bay, flashing on the sea, watched by a crowd on the clifftop;
//   - three jets turning on the wheel's rim like a Catherine wheel, throwing sparks.
(function () {
  'use strict';

  const GOLD = '#ffd24a';
  const PALETTE = { skyTop: '#050716', skyLow: '#1c1438', win: GOLD, lamp: '255,214,140' };
  const COLORS = ['#ffd24a', '#ff4fa3', '#5cff9d', '#e8f4ff', '#b48cff'];

  function createBonfireLayer() {
    let seed = 5;
    const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
    const spread = g => Math.min(g.moonR * 2.1, g.W * 0.42);
    const phone = g => g.moonX - g.moonR < 60;
    // In the open water right of the wheel (desktop panels cover the left), in front of the boat.
    const fire = g => ({ x: Math.min(g.W - 60, g.moonX + spread(g) * 0.85), y: g.rowY(0.42), s: 1.2 });
    const embers = Array.from({ length: 46 }, () => ({ p: rnd(), s: 0.6 + rnd() * 0.8, dx: rnd() * 2 - 1, w: rnd() * 6.28 }));
    const puffs = Array.from({ length: 10 }, (_, i) => ({ p: i / 10, w: rnd() * 6.28 }));

    // Fireworks. k: sideways offset from the wheel in spread() units; h: height above the wheel
    // centre in radii. Phones: the wheel fills the width and the title sits above it, so bursts
    // hug the side edges instead (ph: side and height).
    const slots = [
      { k: -0.95, h: 0.45, ph: [-0.6, 1.25], P: 4300, off: 2600, kind: 'peony', c: 0 },
      { k: 0.92, h: 0.15, ph: [0.55, 1.15], P: 5200, off: 3700, kind: 'ring', c: 1 },
      { k: -0.55, h: 0.95, ph: [-0.1, 1.45], P: 6100, off: 500, kind: 'willow', c: 0 },
      { k: 0.6, h: 0.85, ph: [0.45, 1.5], P: 4700, off: 1400, kind: 'peony', c: 2 },
      { k: 1.15, h: 0.6, ph: [-0.5, 1.2], P: 5600, off: 4800, kind: 'peony', c: 3 },
      { k: -1.2, h: 0.05, ph: [0.2, 1.35], P: 6600, off: 3000, kind: 'ring', c: 4 },
    ];
    const LAUNCH = 900, LIFE = 2600;

    // Catherine wheel: jets on the rim, one turn every 3.2 s.
    seed = 11;
    const JETS = 3, SPARK_LIFE = 750, SPIN = 6.283 / 3200;
    const jetSparks = Array.from({ length: 240 }, (_, i) => ({ j: i % JETS, p: rnd() * SPARK_LIFE, v: 0.7 + rnd() * 0.6, r: rnd() * 0.5 - 0.1 }));

    function sky(ctx, g) {
      ctx.globalCompositeOperation = 'lighter';
      // The display's gold-to-pink halo round the wheel...
      const reach = Math.min(g.moonR * 2.2, g.moonR + Math.min(g.W, g.H) * 0.3);
      const halo = ctx.createRadialGradient(g.moonX, g.moonY, g.moonR * 0.9, g.moonX, g.moonY, reach);
      halo.addColorStop(0, 'rgba(255,210,74,0.18)'); halo.addColorStop(0.5, 'rgba(255,79,163,0.06)'); halo.addColorStop(1, 'rgba(255,79,163,0)');
      ctx.fillStyle = halo; ctx.fillRect(0, 0, g.W, g.horizon);
      // ...warmed by the fire, which also lights the low sky above it.
      const warm = ctx.createRadialGradient(g.moonX, g.moonY, g.moonR * 0.9, g.moonX, g.moonY, reach);
      warm.addColorStop(0, 'rgba(255,170,60,0.12)'); warm.addColorStop(1, 'rgba(255,140,40,0)');
      ctx.fillStyle = warm; ctx.fillRect(0, 0, g.W, g.horizon);
      const f = fire(g), r = Math.max(g.W, g.H) * 0.28;
      const glow = ctx.createRadialGradient(f.x, g.horizon, 0, f.x, g.horizon, r);
      glow.addColorStop(0, 'rgba(255,110,30,0.13)'); glow.addColorStop(1, 'rgba(255,110,30,0)');
      ctx.fillStyle = glow; ctx.fillRect(0, 0, g.W, g.horizon);
      ctx.globalCompositeOperation = 'source-over';
    }

    // Onlookers along the headland, inland of the lighthouse.
    function land(ctx, g) {
      const lx = g.lighthouseX(), base = g.horizon + 2;
      ctx.fillStyle = '#02070f';
      for (let i = 0; i < 14; i++) {
        const x = lx - 20 - i * 11 - (i % 3) * 3;
        if (x < 6) break;
        const y = base - g.H * (0.07 - 0.025 * x / (lx + 24)) + 2;   // on the clifftop
        const s = 0.9 + (i * 7 % 4) * 0.08, kid = i % 5 === 3;
        const hh = (kid ? 11 : 16) * s;
        ctx.beginPath(); ctx.arc(x, y - hh - 3 * s, 3 * s, 0, 6.29); ctx.fill();
        ctx.fillRect(x - 3.5 * s, y - hh, 7 * s, hh + 2);
        if (i % 4 === 1) { ctx.fillRect(x + 2 * s, y - hh - 6 * s, 1.5, 6 * s); }   // pointing arm
      }
    }

    // ── Fireworks ────────────────────────────────────────────────────────────
    const burstAt = (g, s, c) => {
      const jit = Math.sin(c * 12.9898 + s.k * 78.2) * 0.12;
      if (phone(g)) return { x: g.W / 2 + Math.sign(s.ph[0]) * g.W * (0.36 + Math.abs(jit)), y: g.moonY - g.moonR * (0.2 + s.ph[1] * 0.35) };
      return { x: g.moonX + (s.k + jit) * spread(g), y: Math.max(40, g.moonY - s.h * g.moonR) };
    };

    function shell(ctx, g, s, a, cx, cy, color) {
      const R = (s.kind === 'willow' ? 90 : s.kind === 'ring' ? 60 : 72) * Math.min(1, g.W / 900 + 0.35);
      const n = s.kind === 'ring' ? 30 : 40, grav = s.kind === 'willow' ? 1.1 : 0.45, tail = s.kind === 'willow' ? 0.3 : 0.16;
      const fade = s.kind === 'willow' ? (a < 0.4 ? 1 : 1 - (a - 0.4) / 0.6) : (a < 0.65 ? 1 : 1 - (a - 0.65) / 0.35);
      const pos = (u, th, v) => {
        const e = 1 - Math.pow(1 - u, 3);
        return [cx + Math.cos(th) * R * v * e, cy + Math.sin(th) * R * v * e + u * u * R * grav];
      };
      ctx.lineWidth = s.kind === 'willow' ? 1.2 : 1.6;
      for (let j = 0; j < n; j++) {
        const th = j / n * 6.283 + s.off;
        const v = s.kind === 'ring' ? 1 : 0.7 + 0.3 * Math.abs(Math.sin(j * 12.9898 + s.off));
        const [x1, y1] = pos(a, th, v), [x0, y0] = pos(Math.max(0, a - tail), th, v);
        ctx.globalAlpha = fade * 0.9; ctx.strokeStyle = color;
        ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.stroke();
        ctx.globalAlpha = fade; ctx.fillStyle = '#fff';
        ctx.fillRect(x1 - 1.2, y1 - 1.2, 2.4, 2.4);
      }
      if (s.kind !== 'ring') {                            // inner pistil: a second, smaller star in white-gold
        for (let j = 0; j < 14; j++) {
          const [x1, y1] = pos(a, j / 14 * 6.283 + 0.2, 0.42);
          ctx.globalAlpha = fade * 0.9; ctx.fillStyle = '#fff6d8'; ctx.fillRect(x1 - 1, y1 - 1, 2, 2);
        }
      }
      if (a < 0.4) {                                      // a soft bloom of the shell's colour
        const bl = ctx.createRadialGradient(cx, cy, 0, cx, cy, R);
        bl.addColorStop(0, color); bl.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.globalAlpha = 0.16 * (1 - a / 0.4); ctx.fillStyle = bl; ctx.fillRect(cx - R, cy - R, R * 2, R * 2);
      }
      if (a < 0.12) {                                     // the bang
        const fl = ctx.createRadialGradient(cx, cy, 0, cx, cy, R * 0.7);
        fl.addColorStop(0, `rgba(255,255,240,${0.55 * (1 - a / 0.12)})`); fl.addColorStop(1, 'rgba(255,255,240,0)');
        ctx.globalAlpha = 1; ctx.fillStyle = fl; ctx.fillRect(cx - R, cy - R, R * 2, R * 2);
      }
      // Its colour on the water below.
      for (let i = 1; i < 14; i++) {
        const d = i / 14 * 0.6, y = g.rowY(d);
        ctx.globalAlpha = fade * 0.35 * (1 - d) * (0.5 + 0.5 * Math.sin(i * 2.7 + a * 9));
        ctx.fillStyle = color;
        const w = (10 + d * 50) * (0.4 + 0.6 * Math.abs(Math.sin(i * 1.3)));
        ctx.fillRect(cx - w / 2 + Math.sin(i * 5.3) * 8 * d, y, w, 1 + d * 2);
      }
      ctx.globalAlpha = 1;
    }

    function display(ctx, g, t, still) {
      ctx.globalCompositeOperation = 'lighter';
      slots.forEach((s, i) => {
        if (still && i > 2) return;   // still frame: three shells mid-burst
        const tt = still ? LAUNCH + [500, 1100, 300][i] : (t + s.off) % s.P;
        const c = still ? 0 : Math.floor((t + s.off) / s.P);
        const { x, y } = burstAt(g, s, c);
        const color = COLORS[(s.c + c) % COLORS.length];
        if (tt < LAUNCH) {                                // climbing from the water
          const u = tt / LAUNCH, ry = g.horizon - (g.horizon - y) * (1 - (1 - u) * (1 - u));
          ctx.globalAlpha = 0.7; ctx.strokeStyle = 'rgba(255,220,160,1)'; ctx.lineWidth = 1.2;
          ctx.beginPath(); ctx.moveTo(x, Math.min(g.horizon, ry + 36)); ctx.lineTo(x, ry); ctx.stroke();
          ctx.globalAlpha = 1; ctx.fillStyle = '#fff'; ctx.fillRect(x - 1, ry - 1, 2, 2);
        } else if (tt < LAUNCH + LIFE) {
          shell(ctx, g, s, (tt - LAUNCH) / LIFE, x, y, s.kind === 'willow' ? GOLD : color);
        }
      });
      ctx.globalCompositeOperation = 'source-over';
      // Smoke hangs where shells burst.
      slots.forEach((s, i) => {
        if (still && i > 2) return;
        const tt = still ? LAUNCH + LIFE : (t + s.off) % s.P, c = still ? 0 : Math.floor((t + s.off) / s.P);
        if (tt < LAUNCH + 400) return;
        const u = Math.min(1, (tt - LAUNCH) / s.P), { x, y } = burstAt(g, s, c), r = 50 + u * 60;
        const m = ctx.createRadialGradient(x + u * 30, y + 20, 0, x + u * 30, y + 20, r);
        m.addColorStop(0, `rgba(170,160,190,${0.09 * (1 - u)})`); m.addColorStop(1, 'rgba(170,160,190,0)');
        ctx.fillStyle = m; ctx.fillRect(x + u * 30 - r, y + 20 - r, r * 2, r * 2);
      });
    }

    // ── Bonfire ──────────────────────────────────────────────────────────────
    function flame(ctx, x, y, w, h, sway, inner) {
      const gr = ctx.createLinearGradient(0, y, 0, y - h);
      if (inner) { gr.addColorStop(0, '#fff3c4'); gr.addColorStop(0.5, '#ffd36a'); gr.addColorStop(1, 'rgba(255,170,40,0)'); }
      else { gr.addColorStop(0, '#ff8a1f'); gr.addColorStop(0.55, '#e8430e'); gr.addColorStop(1, 'rgba(160,20,0,0)'); }
      ctx.fillStyle = gr;
      ctx.beginPath(); ctx.moveTo(x - w, y);
      ctx.quadraticCurveTo(x - w * 0.9, y - h * 0.55, x + sway, y - h);
      ctx.quadraticCurveTo(x + w * 0.9, y - h * 0.55, x + w, y);
      ctx.closePath(); ctx.fill();
    }

    function person(ctx, x, y, s, rim) {
      ctx.fillStyle = '#0a0606';
      ctx.beginPath(); ctx.arc(x, y - 19 * s, 3.2 * s, 0, 6.29); ctx.fill();
      ctx.beginPath(); ctx.moveTo(x - 4.5 * s, y); ctx.lineTo(x - 3.5 * s, y - 15 * s); ctx.lineTo(x + 3.5 * s, y - 15 * s); ctx.lineTo(x + 4.5 * s, y); ctx.fill();
      ctx.fillStyle = 'rgba(255,150,50,0.55)';   // firelit edge
      ctx.fillRect(x + rim * 3.6 * s - 0.5, y - 15 * s, 1.2, 14 * s);
    }

    function bonfire(ctx, g, t, still) {
      const { x, y, s } = fire(g);
      const flick = still ? 1 : 0.85 + 0.15 * Math.sin(t / 60) * Math.sin(t / 170);
      ctx.globalCompositeOperation = 'lighter';
      const glow = ctx.createRadialGradient(x, y - 18 * s, 0, x, y - 18 * s, 130 * s);
      glow.addColorStop(0, `rgba(255,140,40,${0.42 * flick})`); glow.addColorStop(1, 'rgba(255,140,40,0)');
      ctx.fillStyle = glow; ctx.fillRect(x - 130 * s, y - 150 * s, 260 * s, 260 * s);
      ctx.globalCompositeOperation = 'source-over';
      // Its reflection: warm streaks on the water toward the viewer.
      for (let i = 1; i < 9; i++) {
        const ry = y + 6 * s + i * 6 * s, ph = still ? 0.6 : 0.5 + 0.5 * Math.sin(t / 260 + i * 1.9);
        ctx.globalAlpha = (0.42 - i * 0.04) * ph * flick; ctx.fillStyle = i % 3 ? '#ff8a1f' : '#ffd36a';
        const w = (26 - i * 1.5) * s * (0.6 + 0.4 * ph);
        ctx.fillRect(x - w / 2 + Math.sin(i * 7.1) * 6, ry, w, 1.6);
      }
      ctx.globalAlpha = 1;
      // Sandbar
      ctx.fillStyle = '#0b0807';
      ctx.beginPath(); ctx.ellipse(x, y + 2 * s, 70 * s, 7 * s, 0, Math.PI, 0); ctx.fill();
      ctx.fillStyle = 'rgba(255,150,60,0.22)'; ctx.fillRect(x - 40 * s, y - 4 * s, 80 * s, 1.5);
      person(ctx, x - 44 * s, y, s * 0.95, 1); person(ctx, x + 36 * s, y, s, -1); person(ctx, x + 50 * s, y + 1, s * 0.8, -1);
      // A sparkler in the small one's hand.
      const sx = x + 46 * s, sy = y - 14 * s;
      ctx.globalCompositeOperation = 'lighter';
      for (let k = 0; k < 7; k++) {
        const a = k * 0.9 + (still ? 0 : t / 40), l = (4 + (k * 37 % 5)) * s;
        ctx.strokeStyle = '#fff1b8'; ctx.lineWidth = 0.8;
        ctx.beginPath(); ctx.moveTo(sx, sy); ctx.lineTo(sx + Math.cos(a) * l, sy + Math.sin(a) * l); ctx.stroke();
      }
      ctx.globalCompositeOperation = 'source-over';
      // Logs, then flames.
      ctx.strokeStyle = '#140a06'; ctx.lineWidth = 3 * s; ctx.lineCap = 'round';
      for (const dx of [-16, -9, -2, 5, 12, 18]) { ctx.beginPath(); ctx.moveTo(x + dx * s, y); ctx.lineTo(x + dx * 0.15 * s, y - 34 * s); ctx.stroke(); }
      for (let i = 0; i < 5; i++) {
        const fx = x + (i - 2) * 6 * s, h = (34 + 12 * (still ? 0.5 : Math.sin(t / 110 + i * 1.7))) * s * (i === 2 ? 1.25 : 1);
        flame(ctx, fx, y - 2 * s, 8 * s, h, still ? 0 : Math.sin(t / 150 + i) * 5 * s, false);
      }
      for (let i = 0; i < 3; i++) {
        const fx = x + (i - 1) * 5 * s, h = (20 + 8 * (still ? 0.5 : Math.sin(t / 90 + i * 2.3))) * s;
        flame(ctx, fx, y - 2 * s, 5 * s, h, still ? 0 : Math.sin(t / 120 + i) * 3 * s, true);
      }
    }

    function embersRise(ctx, g, t, still) {
      const { x, y, s } = fire(g);
      ctx.globalCompositeOperation = 'lighter';
      for (const e of embers) {
        const age = ((still ? 0.5 : t / (3200 / e.s)) + e.p) % 1;
        const ex = x + e.dx * 10 * s + Math.sin(age * 6 + e.w) * 18 * age - age * age * 70;
        const ey = y - 30 * s - age * g.H * 0.32;
        ctx.globalAlpha = (1 - age) * 0.9;
        ctx.fillStyle = age < 0.4 ? '#ffd36a' : '#ff6a1f';
        ctx.fillRect(ex, ey, 1.8, 1.8);
      }
      ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
    }

    // Smoke rises from the fire and leans across the wheel on the wind, thinning as it goes.
    function smoke(ctx, g, t, still) {
      const { x, y, s } = fire(g);
      for (const p of puffs) {
        const age = ((still ? 0 : t / 16000) + p.p) % 1;
        const px = x - age * age * g.W * 0.32 + Math.sin(age * 5 + p.w) * 10;
        const py = y - 44 * s - age * (y - g.H * 0.08) * 0.85;
        const r = (12 + age * 80) * s;
        const m = ctx.createRadialGradient(px, py, 0, px, py, r);
        m.addColorStop(0, `rgba(120,100,110,${0.2 * (1 - age)})`); m.addColorStop(1, 'rgba(120,100,110,0)');
        ctx.fillStyle = m; ctx.fillRect(px - r, py - r, r * 2, r * 2);
      }
    }

    // Woodsmoke along the horizon, warm near the fire.
    function haze(ctx, g, t, still) {
      const f = fire(g);
      for (let i = 0; i < 5; i++) {
        const x = ((i / 4 + (still ? 0 : t / 200000)) % 1.25 - 0.125) * g.W, w = (0.3 + (i % 2) * 0.12) * g.W;
        const warm = Math.max(0, 1 - Math.abs(x - f.x) / (g.W * 0.35));
        const m = ctx.createRadialGradient(x, g.horizon, 0, x, g.horizon, w);
        m.addColorStop(0, `rgba(${Math.round(130 + 120 * warm)},${Math.round(110 + 20 * warm)},${Math.round(120 - 80 * warm)},0.22)`);
        m.addColorStop(1, 'rgba(120,110,120,0)');
        ctx.save(); ctx.translate(0, g.horizon); ctx.scale(1, 0.12); ctx.translate(0, -g.horizon);
        ctx.fillStyle = m; ctx.fillRect(x - w, g.horizon - w, w * 2, w * 2);
        ctx.restore();
      }
    }

    // ── Catherine wheel ──────────────────────────────────────────────────────
    // Each spark leaves the rim along the jet's direction of travel, then slows and falls.
    function jets(ctx, g, t) {
      const R = g.moonR;
      ctx.globalCompositeOperation = 'lighter';
      ctx.lineWidth = 1.3;
      const pos = (s, te, age) => {
        const th = te * SPIN + s.j * 6.283 / JETS;
        const tx = -Math.sin(th), ty = Math.cos(th), ox = Math.cos(th), oy = Math.sin(th);
        const v = 0.34 * s.v, drag = age - age * age / (2.4 * SPARK_LIFE);
        return [g.moonX + ox * R + (tx * v + ox * v * s.r) * drag, g.moonY + oy * R + (ty * v + oy * v * s.r) * drag + 0.00012 * age * age];
      };
      for (const s of jetSparks) {
        const age = (t + s.p) % SPARK_LIFE, te = t - age, u = age / SPARK_LIFE;
        const [x1, y1] = pos(s, te, age), [x0, y0] = pos(s, te, Math.max(0, age - 30));
        ctx.globalAlpha = 1 - u * u;
        ctx.strokeStyle = u < 0.25 ? '#fff6d8' : u < 0.6 ? '#ffe27a' : '#ff5b3a';
        ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.stroke();
      }
      ctx.globalAlpha = 1;
      for (let j = 0; j < JETS; j++) {                     // the jets themselves, burning on the rim
        const th = t * SPIN + j * 6.283 / JETS, x = g.moonX + Math.cos(th) * R, y = g.moonY + Math.sin(th) * R;
        const gl = ctx.createRadialGradient(x, y, 0, x, y, 34);
        gl.addColorStop(0, 'rgba(255,246,216,0.9)'); gl.addColorStop(0.3, 'rgba(255,200,90,0.45)'); gl.addColorStop(1, 'rgba(255,91,58,0)');
        ctx.fillStyle = gl; ctx.fillRect(x - 34, y - 34, 68, 68);
      }
      ctx.globalCompositeOperation = 'source-over';
    }

    function draw(ctx, g, t, still) {
      display(ctx, g, t, still);
      haze(ctx, g, t, still);
      smoke(ctx, g, t, still);
      bonfire(ctx, g, t, still);
      embersRise(ctx, g, t, still);
      jets(ctx, g, still ? 1700 : t);   // still frame: a mid-shower moment
    }

    return { palette: PALETTE, sky, land, draw };
  }

  window.createBonfireLayer = createBonfireLayer;
})();
