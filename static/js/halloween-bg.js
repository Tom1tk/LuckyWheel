// Halloween layer for the Season 9 tides scene (static/js/tides-bg.js).
// Exposes window.createHalloweenLayer() -> { palette, sky(ctx, g), land(ctx, g), draw(ctx, g, t, still) }.
// g is the tide scene's geometry: { W, H, moonX, moonY, moonR, horizon, rowY, lighthouseX }.
// Additive only: the night sea, lighthouse, buoys and boat all stay; this adds
// a harvest-moon glow, bats, a graveyard on the headland, ghosts over the
// water, floating jack-o'-lanterns and a passing witch.
(function () {
  'use strict';

  const ORANGE = '#ff8a1f';
  const PALETTE = {
    skyTop: '#0a0614',
    skyLow: '#34143e',
    win:    ORANGE,
    lamp:   '255,150,60',
  };

  function createHalloweenLayer() {
    let seed = 31;
    const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
    const bats = Array.from({ length: 12 }, () => ({ p: rnd() * 6.28, s: 0.6 + rnd() * 0.8, r: 0.35 + rnd() * 0.5, h: rnd() }));
    // k is the offset from the wheel in units of spread(): desktop keeps them in the open
    // water between the side panels, phones (wheel fills the width) spread them edge to edge.
    const lanterns = [[-1, 0.55], [-0.6, 0.3], [0.62, 0.42], [1, 0.7]].map(([k, d]) => ({ k, d, p: rnd() * 6.28 }));
    const ghosts = [-0.85, 0.45, 0.95].map(k => ({ k, p: rnd() * 6.28 }));
    const fog = [0, 1, 2, 3, 4].map(i => ({ fx: i / 4, p: rnd() * 6.28, w: 0.25 + rnd() * 0.2 }));
    const spread = g => Math.min(g.moonR * 2.1, g.W * 0.42);

    // Harvest-moon glow: the wheel warms the sky orange.
    function sky(ctx, g) {
      // Additive and capped, so on phones (huge wheel) the glow stays orange instead of browning the whole purple sky.
      const reach = Math.min(g.moonR * 2.2, g.moonR + Math.min(g.W, g.H) * 0.3);
      const halo = ctx.createRadialGradient(g.moonX, g.moonY, g.moonR * 0.9, g.moonX, g.moonY, reach);
      halo.addColorStop(0, 'rgba(255,120,20,0.32)'); halo.addColorStop(0.45, 'rgba(255,90,10,0.10)'); halo.addColorStop(1, 'rgba(255,90,10,0)');
      ctx.globalCompositeOperation = 'lighter';
      ctx.fillStyle = halo; ctx.fillRect(0, 0, g.W, g.horizon);
      ctx.globalCompositeOperation = 'source-over';
      const dusk = ctx.createLinearGradient(0, g.horizon - g.H * 0.18, 0, g.horizon);
      dusk.addColorStop(0, 'rgba(255,110,20,0)'); dusk.addColorStop(1, 'rgba(255,110,20,0.22)');
      ctx.fillStyle = dusk; ctx.fillRect(0, g.horizon - g.H * 0.18, g.W, g.H * 0.18);
    }

    function bat(ctx, x, y, s, flap) {
      const w = 14 * s, lift = (flap * 2 - 1) * 6 * s;
      ctx.beginPath(); ctx.ellipse(x, y + 1.5 * s, 2.6 * s, 4 * s, 0, 0, 6.29); ctx.fill();   // body
      ctx.beginPath(); ctx.moveTo(x - 2.2 * s, y - 1 * s); ctx.lineTo(x - 2 * s, y - 5 * s); ctx.lineTo(x - 0.6 * s, y - 2 * s);
      ctx.lineTo(x + 0.6 * s, y - 2 * s); ctx.lineTo(x + 2 * s, y - 5 * s); ctx.lineTo(x + 2.2 * s, y - 1 * s); ctx.fill();   // ears
      ctx.beginPath();
      ctx.moveTo(x, y);
      ctx.quadraticCurveTo(x - w * 0.5, y - lift - 4 * s, x - w, y - lift);
      ctx.quadraticCurveTo(x - w * 0.6, y + 1 * s, x - w * 0.35, y + 2 * s);
      ctx.quadraticCurveTo(x - w * 0.2, y - 1 * s, x, y + 3 * s);
      ctx.quadraticCurveTo(x + w * 0.2, y - 1 * s, x + w * 0.35, y + 2 * s);
      ctx.quadraticCurveTo(x + w * 0.6, y + 1 * s, x + w, y - lift);
      ctx.quadraticCurveTo(x + w * 0.5, y - lift - 4 * s, x, y);
      ctx.fill();
    }

    function flock(ctx, g, t) {
      ctx.fillStyle = '#05030a';
      for (const b of bats) {
        const a = t / 4000 * b.s + b.p;
        const x = g.moonX + Math.cos(a) * g.moonR * (1.3 + b.r) + Math.sin(a * 2.3) * 30;
        const y = Math.max(20, g.moonY - g.moonR * 0.6 + Math.sin(a * 1.7) * g.moonR * (0.5 + b.h * 0.6));
        bat(ctx, x, y, 1 + b.h * 0.8, 0.5 + 0.5 * Math.sin(t / 90 * b.s + b.p));
      }
    }

    function pumpkin(ctx, x, y, s, flicker) {
      const glow = ctx.createRadialGradient(x, y, 0, x, y, 30 * s);
      glow.addColorStop(0, `rgba(255,150,40,${0.45 * flicker})`); glow.addColorStop(1, 'rgba(255,150,40,0)');
      ctx.fillStyle = glow; ctx.fillRect(x - 30 * s, y - 30 * s, 60 * s, 60 * s);
      ctx.fillStyle = '#e8650c';
      for (const dx of [-5, 5, 0]) { ctx.beginPath(); ctx.ellipse(x + dx * s, y, 7 * s, 8 * s, 0, 0, 6.29); ctx.fill(); }
      ctx.fillStyle = '#2f5a1c'; ctx.fillRect(x - 1.2 * s, y - 11 * s, 2.4 * s, 4 * s);
      ctx.fillStyle = `rgba(255,226,120,${0.75 + 0.25 * flicker})`;   // carved face
      ctx.beginPath(); ctx.moveTo(x - 6 * s, y - 2 * s); ctx.lineTo(x - 3 * s, y - 5 * s); ctx.lineTo(x - 1 * s, y - 1.5 * s); ctx.fill();
      ctx.beginPath(); ctx.moveTo(x + 6 * s, y - 2 * s); ctx.lineTo(x + 3 * s, y - 5 * s); ctx.lineTo(x + 1 * s, y - 1.5 * s); ctx.fill();
      ctx.beginPath(); ctx.moveTo(x - 7 * s, y + 2 * s); ctx.quadraticCurveTo(x, y + 9 * s, x + 7 * s, y + 2 * s);
      ctx.quadraticCurveTo(x, y + 5 * s, x - 7 * s, y + 2 * s); ctx.fill();
    }

    function lanternsOnWater(ctx, g, t, still) {
      for (const l of lanterns) {
        const x = g.moonX + l.k * spread(g);
        const y = g.rowY(l.d) + (still ? 0 : Math.sin(t / 800 + l.p) * (2 + l.d * 4));
        const s = 0.6 + l.d * 1.4;
        const flicker = still ? 1 : 0.8 + 0.2 * Math.sin(t / 70 + l.p) * Math.sin(t / 130);
        pumpkin(ctx, x, y - 6 * s, s, flicker);
        ctx.globalAlpha = 0.3 * flicker; ctx.fillStyle = ORANGE;   // reflection
        for (let i = 1; i < 5; i++) ctx.fillRect(x - (8 - i) * s, y + 4 * s + i * 4, (16 - 2 * i) * s, 1.5);
        ctx.globalAlpha = 1;
      }
    }

    // Gravestones and a bare tree on the headland, inland of the lighthouse.
    function land(ctx, g) {
      const base = g.horizon + 2 - g.H * 0.06, lx = g.lighthouseX();
      ctx.fillStyle = '#02070f';
      ctx.shadowColor = 'rgba(255,120,30,0.55)'; ctx.shadowBlur = 6;   // rim light from the harvest moon
      for (const [dx, w, h, round] of [[-0.66, 13, 22, true], [-0.52, 10, 17, false], [-0.4, 14, 25, true], [-0.28, 9, 14, true]]) {
        const x = lx + dx * Math.max(80, lx), y = base + (dx + 0.7) * 10;
        if (x < 8) continue;
        ctx.beginPath(); ctx.moveTo(x - w / 2, y); ctx.lineTo(x - w / 2, y - h + (round ? w / 2 : 0));
        if (round) ctx.arc(x, y - h + w / 2, w / 2, Math.PI, 0); else { ctx.lineTo(x - w / 2, y - h); ctx.lineTo(x + w / 2, y - h); }
        ctx.lineTo(x + w / 2, y); ctx.closePath(); ctx.fill();
        if (!round) { ctx.fillRect(x - 1.5, y - h - 9, 3, 9); ctx.fillRect(x - 6, y - h - 6, 12, 3); }
      }
      const tx = lx - 0.85 * Math.max(80, lx);
      if (tx < 14) { ctx.shadowBlur = 0; return; }
      ctx.strokeStyle = '#02070f'; ctx.lineCap = 'round';
      const branch = (x, y, a, len, w) => {
        if (len < 5) return;
        const x2 = x + Math.cos(a) * len, y2 = y + Math.sin(a) * len;
        ctx.lineWidth = w; ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x2, y2); ctx.stroke();
        branch(x2, y2, a - 0.45, len * 0.68, w * 0.65);
        branch(x2, y2, a + 0.38, len * 0.62, w * 0.65);
      };
      branch(tx, base + 4, -Math.PI / 2 - 0.12, 46, 7);
      ctx.shadowBlur = 0;
    }

    function ghost(ctx, x, y, s, t, a) {
      ctx.globalAlpha = a;
      const glow = ctx.createRadialGradient(x, y, 0, x, y, 26 * s);
      glow.addColorStop(0, 'rgba(230,220,255,0.35)'); glow.addColorStop(1, 'rgba(230,220,255,0)');
      ctx.fillStyle = glow; ctx.fillRect(x - 26 * s, y - 26 * s, 52 * s, 52 * s);
      ctx.fillStyle = 'rgba(236,232,255,0.8)';
      ctx.beginPath(); ctx.moveTo(x - 9 * s, y + 10 * s); ctx.lineTo(x - 9 * s, y - 2 * s);
      ctx.arc(x, y - 2 * s, 9 * s, Math.PI, 0); ctx.lineTo(x + 9 * s, y + 10 * s);
      for (let i = 3; i >= 0; i--) {                       // wavy hem
        const hx = x - 9 * s + i * 6 * s, w = Math.sin(t / 300 + i) * 2 * s;
        ctx.quadraticCurveTo(hx + 3 * s, y + 6 * s + w, hx, y + 10 * s);
      }
      ctx.fill();
      ctx.fillStyle = '#1a0c26';
      ctx.beginPath(); ctx.ellipse(x - 3.2 * s, y - 3 * s, 1.6 * s, 2.4 * s, 0, 0, 6.29); ctx.ellipse(x + 3.2 * s, y - 3 * s, 1.6 * s, 2.4 * s, 0, 0, 6.29); ctx.fill();
      ctx.globalAlpha = 1;
    }

    function haunt(ctx, g, t, still) {
      for (const h of ghosts) {
        const u = still ? 0.5 : 0.5 + 0.5 * Math.sin(t / 5200 + h.p);   // fades in and out
        const x = g.moonX + h.k * spread(g) + (still ? 0 : Math.sin(t / 2600 + h.p) * 24);
        const y = g.horizon - 22 - u * 26 + (still ? 0 : Math.sin(t / 700 + h.p) * 3);
        ghost(ctx, x, y, 0.9, t, 0.25 + 0.5 * u);
      }
    }

    // A witch crosses in front of the moon about once a minute.
    function witch(ctx, g, t) {
      const period = 60000, u = ((t + 25000) % period) / period * 3 - 1;   // only -1..1 of each cycle is on screen; starts mid-flight
      if (u < -1 || u > 1) return;
      const x = g.moonX + u * g.W * 0.7, y = Math.max(60, g.moonY - g.moonR - 50) - Math.cos(u * 1.6) * 24;
      ctx.save(); ctx.translate(x, y); ctx.rotate(-0.08); ctx.scale(1.3, 1.3);
      ctx.shadowColor = 'rgba(255,120,30,0.7)'; ctx.shadowBlur = 8;
      ctx.fillStyle = '#05030a'; ctx.strokeStyle = '#05030a'; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.moveTo(-30, 4); ctx.lineTo(26, -2); ctx.stroke();               // broom
      ctx.beginPath(); ctx.moveTo(-30, 4); ctx.lineTo(-44, -2); ctx.lineTo(-46, 10); ctx.closePath(); ctx.fill();
      ctx.beginPath(); ctx.moveTo(-8, 2); ctx.lineTo(4, -14); ctx.lineTo(10, 0); ctx.closePath(); ctx.fill(); // body
      ctx.beginPath(); ctx.arc(5, -17, 4, 0, 6.29); ctx.fill();                              // head
      ctx.beginPath(); ctx.moveTo(-3, -19); ctx.lineTo(13, -19); ctx.lineTo(3, -34); ctx.closePath(); ctx.fill(); // hat
      ctx.restore();
    }

    // Low mist on the horizon, purple at the edges, warmed orange under the wheel.
    function mist(ctx, g, t, still) {
      for (const f of fog) {
        const x = ((f.fx + (still ? 0 : t / 180000)) % 1.25 - 0.125) * g.W, w = f.w * g.W;
        const warm = Math.max(0, 1 - Math.abs(x - g.moonX) / (g.W * 0.4));
        const m = ctx.createRadialGradient(x, g.horizon, 0, x, g.horizon, w);
        m.addColorStop(0, `rgba(${Math.round(150 + 105 * warm)},${Math.round(90 + 30 * warm)},${Math.round(200 - 170 * warm)},0.26)`);
        m.addColorStop(1, 'rgba(120,80,200,0)');
        ctx.save(); ctx.translate(0, g.horizon); ctx.scale(1, 0.12); ctx.translate(0, -g.horizon);
        ctx.fillStyle = m; ctx.fillRect(x - w, g.horizon - w, w * 2, w * 2);
        ctx.restore();
      }
    }

    function draw(ctx, g, t, still) {
      mist(ctx, g, t, still);
      haunt(ctx, g, t, still);
      flock(ctx, g, t);
      if (!still) witch(ctx, g, t);
      lanternsOnWater(ctx, g, t, still);
    }

    return { palette: PALETTE, sky, land, draw };
  }

  window.createHalloweenLayer = createHalloweenLayer;
})();
