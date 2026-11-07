// Regatta Day: the Tide 9.5 dressing on the Season 9 tides scene (static/js/tides-bg.js).
// Same API as bonfire-bg.js: createRegattaLayer() returns { palette, sky, land, draw }.
// Daylight, so the palette turns off the scene's stars, plankton and lighthouse beam.
(function () {
  'use strict';

  const phone = g => g.moonX - g.moonR < 60;

  // A racing yacht at waterline (x, y), facing right, about 56px tall at s = 1.
  function yacht(ctx, x, y, s, o) {
    ctx.save(); ctx.translate(x, y); ctx.rotate(o.heel || 0); ctx.scale(s, s);
    // Spinnaker first so it sits behind the jib.
    if (o.spin) {
      ctx.fillStyle = o.spin;
      ctx.beginPath(); ctx.moveTo(1, -50); ctx.quadraticCurveTo(34, -40, 26, -8); ctx.lineTo(4, -10); ctx.closePath(); ctx.fill();
    }
    ctx.fillStyle = o.sail;
    const top = o.reef ? -38 : -52;
    ctx.beginPath(); ctx.moveTo(-1, top); ctx.quadraticCurveTo(-10, top * 0.45, -21, -8); ctx.lineTo(-1, -8); ctx.closePath(); ctx.fill();   // main
    if (!o.spin) { ctx.beginPath(); ctx.moveTo(1, top + 4); ctx.lineTo(20, -7); ctx.lineTo(1, -8); ctx.closePath(); ctx.fill(); }         // jib
    if (o.rim) {                                                    // light catching the sail edges
      ctx.strokeStyle = o.rim; ctx.lineWidth = 1.2 / s;
      ctx.beginPath(); ctx.moveTo(-1, top); ctx.quadraticCurveTo(-10, top * 0.45, -21, -8); ctx.stroke();
    }
    ctx.strokeStyle = o.mast || o.hull; ctx.lineWidth = 1.4 / s;
    ctx.beginPath(); ctx.moveTo(0, -4); ctx.lineTo(0, top - 2); ctx.stroke();
    ctx.fillStyle = o.hull;
    ctx.beginPath(); ctx.moveTo(-23, -6); ctx.lineTo(25, -6); ctx.quadraticCurveTo(19, 3, -17, 2); ctx.closePath(); ctx.fill();
    if (o.stripe) { ctx.fillStyle = o.stripe; ctx.fillRect(-20, -5, 41, 1.6); }
    ctx.restore();
  }

  // A fleet racing left to right; each boat wraps round off the right edge.
  function fleet(boats, g, t, still) {
    const span = g.W + 240;
    return boats.map(b => {
      const x = ((still ? b.x0 * span : b.x0 * span + t * b.v * 0.001 * (0.6 + g.W / 2400)) % span) - 120;
      const y = g.rowY(b.d) + (still ? 0 : Math.sin(t / b.bob + b.x0 * 9) * (1 + b.d * 4));
      return { b, x, y, s: 0.3 + b.d * 1.5, heel: (b.heel || 0) + (still ? 0 : Math.sin(t / (b.bob * 1.3) + b.x0 * 5) * 0.04) };
    }).sort((p, q) => p.b.d - q.b.d);
  }

  function wake(ctx, x, y, s, color, alpha) {
    ctx.strokeStyle = color; ctx.lineWidth = Math.max(1, s * 1.4);
    for (let i = 0; i < 5; i++) {
      ctx.globalAlpha = alpha * (1 - i / 5);
      const x0 = x - 18 * s - i * 14 * s, w = 12 * s;
      ctx.beginPath(); ctx.moveTo(x0, y + 1 + i * 0.8 * s); ctx.lineTo(x0 - w, y + 2 + i * 1.6 * s); ctx.stroke();
    }
    ctx.globalAlpha = 1;
  }

  // ── 1 · Regatta Day ────────────────────────────────────────────────────────
  // Daylight. White sails and spinnakers race across a bright bay under bunting;
  // fair-weather clouds and gulls; the lighthouse is painted white and red.
  function day() {
    const palette = {
      skyTop: '#2f6fb8', skyLow: '#a8d8f0', seaTop: '#2b86b8', seaLow: '#0b3a63', land: '#1f3a2c',
      win: '#FFC93C', lose: '#E8443A', sand: '#ffffff', lamp: '255,250,230', stars: false, plankton: false, beam: false,
    };
    let seed = 3;
    const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
    const boats = [
      { d: 0.12, x0: 0.12, v: 22, bob: 800, sail: '#f4f1ea', hull: '#ffffff' },
      { d: 0.2, x0: 0.55, v: 20, bob: 900, sail: '#f4f1ea', hull: '#1d3550', spin: '#E8443A' },
      { d: 0.3, x0: 0.83, v: 26, bob: 760, sail: '#ffffff', hull: '#ffffff', stripe: '#2f6fb8' },
      { d: 0.42, x0: 0.33, v: 30, bob: 840, sail: '#f4f1ea', hull: '#ffffff', spin: '#FFC93C' },
      { d: 0.56, x0: 0.7, v: 34, bob: 950, sail: '#ffffff', hull: '#E8443A', heel: -0.08 },
    ];
    const clouds = Array.from({ length: 6 }, (_, i) => ({ x0: i / 6 + rnd() * 0.08, y: 0.06 + rnd() * 0.28, s: 0.7 + rnd() * 0.7 }));
    const gulls = Array.from({ length: 4 }, () => ({ x0: rnd(), y: 0.12 + rnd() * 0.3, v: 0.7 + rnd() * 0.6, p: rnd() * 6.28 }));
    const FLAGS = ['#E8443A', '#FFC93C', '#2f6fb8', '#ffffff', '#3aa66a'];

    function sky(ctx, g) {
      const halo = ctx.createRadialGradient(g.moonX, g.moonY, g.moonR * 0.8, g.moonX, g.moonY, g.moonR * 2.6);
      halo.addColorStop(0, 'rgba(255,250,225,0.45)'); halo.addColorStop(1, 'rgba(255,250,225,0)');
      ctx.fillStyle = halo; ctx.fillRect(0, 0, g.W, g.horizon);
      // Far shore: a low blue-grey coast along the horizon.
      ctx.fillStyle = 'rgba(70,110,140,0.55)';
      ctx.beginPath(); ctx.moveTo(g.W * 0.45, g.horizon + 1);
      for (let x = g.W * 0.45; x <= g.W + 10; x += 20) ctx.lineTo(x, g.horizon - 4 - 5 * Math.abs(Math.sin(x / 90)) - 4 * Math.sin(x / 37));
      ctx.lineTo(g.W, g.horizon + 1); ctx.closePath(); ctx.fill();
    }

    // Repaint the lighthouse in day colours, and fly a flag on the headland.
    function land(ctx, g) {
      const lx = g.lighthouseX(), base = g.horizon + 2, foot = base - g.H * 0.045 + 2, top = foot - 2 - 54;
      ctx.fillStyle = '#f4f1ea';
      ctx.beginPath(); ctx.moveTo(lx - 8, foot); ctx.lineTo(lx - 5, top); ctx.lineTo(lx + 5, top); ctx.lineTo(lx + 8, foot); ctx.closePath(); ctx.fill();
      ctx.fillStyle = '#E8443A'; ctx.fillRect(lx - 7, top + 18, 14, 6); ctx.fillRect(lx - 7.5, top + 34, 15, 6);
      ctx.fillStyle = '#1d3550'; ctx.fillRect(lx - 7, top - 4, 14, 4); ctx.fillRect(lx - 4, top - 12, 8, 8);
      ctx.fillStyle = '#E8443A'; ctx.beginPath(); ctx.moveTo(lx - 6, top - 12); ctx.lineTo(lx, top - 19); ctx.lineTo(lx + 6, top - 12); ctx.fill();
      ctx.fillStyle = 'rgba(140,190,120,0.5)';                  // sunlit grass on the clifftop
      ctx.beginPath(); ctx.moveTo(0, base - g.H * 0.07);
      ctx.quadraticCurveTo(lx * 0.6, base - g.H * 0.09, lx + 24, base - g.H * 0.045);
      ctx.lineTo(lx + 24, base - g.H * 0.045 + 3); ctx.quadraticCurveTo(lx * 0.6, base - g.H * 0.09 + 3, 0, base - g.H * 0.07 + 3);
      ctx.closePath(); ctx.fill();
    }

    function cloud(ctx, x, y, s) {
      ctx.fillStyle = 'rgba(255,255,255,0.88)';
      for (const [dx, dy, r] of [[-38, 4, 18], [-14, -6, 24], [14, -10, 28], [40, 0, 20], [0, 6, 22]]) {
        ctx.beginPath(); ctx.arc(x + dx * s, y + dy * s, r * s, 0, 6.29); ctx.fill();
      }
      ctx.fillStyle = 'rgba(160,190,215,0.35)';
      ctx.fillRect(x - 50 * s, y + 10 * s, 100 * s, 6 * s);
    }

    function bunting(ctx, g, t, still) {
      const lines = [[0, 6, g.H * 0.07]];
      lines.forEach(([x0, y0, sag], li) => {
        const n = Math.max(9, Math.round(g.W / 44));
        const at = u => [x0 + u * g.W, y0 + sag * 4 * u * (1 - u)];
        ctx.strokeStyle = 'rgba(30,40,55,0.7)'; ctx.lineWidth = 1;
        ctx.beginPath();
        for (let i = 0; i <= 40; i++) { const [x, y] = at(i / 40); i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); }
        ctx.stroke();
        for (let i = 0; i < n; i++) {
          const u = (i + 0.5 + li * 0.5) / (n + li * 0.5), [x, y] = at(u);
          const sway = still ? 0 : Math.sin(t / 380 + i * 1.3 + li) * 3;
          ctx.fillStyle = FLAGS[(i + li * 2) % FLAGS.length];
          ctx.beginPath(); ctx.moveTo(x - 10, y); ctx.lineTo(x + 10, y); ctx.lineTo(x + sway, y + 22); ctx.closePath(); ctx.fill();
        }
      });
    }

    function draw(ctx, g, t, still) {
      for (const c of clouds) {
        const x = ((c.x0 + (still ? 0 : t / 400000)) % 1.2 - 0.1) * g.W;
        cloud(ctx, x, c.y * g.horizon + 30, c.s * Math.min(1, g.W / 1000 + 0.3));
      }
      ctx.strokeStyle = 'rgba(40,50,60,0.75)'; ctx.lineWidth = 1.4;
      for (const b of gulls) {
        const x = ((b.x0 + (still ? 0 : t / 60000 * b.v)) % 1.1 - 0.05) * g.W, y = b.y * g.horizon + 40;
        const f = still ? 0.5 : Math.sin(t / 220 + b.p) * 0.5 + 0.5, w = 7;
        ctx.beginPath(); ctx.moveTo(x - w, y - 2 - f * 3); ctx.quadraticCurveTo(x - w / 2, y - 4, x, y); ctx.quadraticCurveTo(x + w / 2, y - 4, x + w, y - 2 - f * 3); ctx.stroke();
      }
      for (const p of fleet(boats, g, t, still)) {
        wake(ctx, p.x, p.y, p.s, '#ffffff', 0.7);
        yacht(ctx, p.x, p.y, p.s, { heel: p.heel - 0.06, sail: p.b.sail, hull: p.b.hull, spin: p.b.spin, stripe: p.b.stripe, mast: '#5a6470' });
        ctx.globalAlpha = 0.25; ctx.fillStyle = p.b.spin || '#ffffff';  // sail reflection
        ctx.fillRect(p.x - 8 * p.s, p.y + 4, 16 * p.s, 1.5); ctx.globalAlpha = 1;
      }
      if (!phone(g)) bunting(ctx, g, t, still);   // phones: the title sits where the bunting would hang
    }

    return { palette, sky, land, draw };
  }

  window.createRegattaLayer = day;
})();
