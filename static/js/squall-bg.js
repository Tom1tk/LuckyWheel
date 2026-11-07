// Storm Squall: the Tide 9.7 dressing on the Season 9 tides scene (static/js/tides-bg.js).
// Same API as bonfire-bg.js: createSquallLayer() returns { palette, sky, land, draw }.
// A dark storm sky, so the palette turns off the scene's stars and plankton.
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

  // ── 3 · Storm Squall ───────────────────────────────────────────────────────
  // A squall over the bay: low cloud, driving rain, whitecaps, reefed boats heeled hard,
  // and lightning that forks to the sea beside the wheel and lights the whole sky.
  function squall() {
    const BOLT = '#F2E86D';
    const palette = {
      skyTop: '#07090e', skyLow: '#26303c', seaTop: '#1a2630', seaLow: '#05080c', land: '#030507',
      win: BOLT, lose: '#8F7CFF', lamp: '255,236,170', stars: false, plankton: false,
    };
    let seed = 21;
    const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
    const drops = Array.from({ length: 240 }, () => ({ x: rnd(), y: rnd(), l: 12 + rnd() * 14, v: 0.8 + rnd() * 0.5 }));
    const scud = Array.from({ length: 7 }, (_, i) => ({ x0: i / 7, y: 0.04 + rnd() * 0.22, r: 0.18 + rnd() * 0.12 }));
    const boats = [
      { d: 0.16, x0: 0.3, v: 30, bob: 520, heel: 0.22 },
      { d: 0.32, x0: 0.78, v: 36, bob: 480, heel: 0.28 },
      { d: 0.52, x0: 0.05, v: 42, bob: 560, heel: 0.32 },
    ];
    const P = 6500;   // one strike every 6.5 s

    function sky(ctx, g) {
      for (let i = 0; i < 9; i++) {                   // heavy cloud base
        const x = (i / 8) * g.W, y = g.horizon * (0.08 + (i % 3) * 0.07), r = g.W * 0.22;
        const m = ctx.createRadialGradient(x, y, 0, x, y, r);
        m.addColorStop(0, 'rgba(4,6,10,0.75)'); m.addColorStop(1, 'rgba(4,6,10,0)');
        ctx.fillStyle = m; ctx.fillRect(x - r, y - r, r * 2, r * 2);
      }
      const halo = ctx.createRadialGradient(g.moonX, g.moonY, g.moonR * 0.8, g.moonX, g.moonY, g.moonR * 2.4);
      halo.addColorStop(0, 'rgba(200,210,230,0.12)'); halo.addColorStop(1, 'rgba(200,210,230,0)');
      ctx.fillStyle = halo; ctx.fillRect(0, 0, g.W, g.horizon);
    }

    function land() {}

    // A jagged bolt, the same shape all through one strike.
    function bolt(ctx, g, c) {
      let s = c * 7919 + 13;
      const r = () => ((s = (s * 16807) % 2147483647) / 2147483647);
      const side = c % 2 ? 1 : -1;
      const x0 = phone(g) ? g.W / 2 + side * g.W * (0.3 + r() * 0.12) : g.moonX + side * (g.moonR * 1.1 + r() * g.moonR * 0.3);
      const pts = [[x0, 0]];
      let x = x0;
      for (let y = 0; y < g.horizon; y += g.horizon / 14) { x += (r() - 0.5) * 28; pts.push([x, Math.min(g.horizon, y + g.horizon / 14)]); }
      const branch = pts.slice(4, 8).map(([bx, by], i) => [bx + (i + 1) * 14 * -side, by + (i + 1) * 10]);
      return { pts, branch: [pts[4], ...branch], foot: pts[pts.length - 1] };
    }

    function strike(ctx, g, t, still) {
      const tt = still ? 30 : t % P, c = still ? 3 : Math.floor(t / P);
      const k = tt < 70 ? 1 : tt < 120 ? 0 : tt < 260 ? 0.8 : 0;
      if (!k) return;
      ctx.globalCompositeOperation = 'lighter';
      ctx.fillStyle = `rgba(190,200,255,${0.2 * k})`;                 // the whole sky lights up
      ctx.fillRect(0, 0, g.W, g.horizon);
      ctx.fillStyle = `rgba(190,200,255,${0.08 * k})`; ctx.fillRect(0, g.horizon, g.W, g.H - g.horizon);
      const b = bolt(ctx, g, c);
      for (const [path, w] of [[b.pts, 2.4], [b.branch, 1.3]]) {
        ctx.strokeStyle = `rgba(242,232,109,${0.5 * k})`; ctx.lineWidth = w * 4;
        ctx.beginPath(); path.forEach(([x, y], i) => (i ? ctx.lineTo(x, y) : ctx.moveTo(x, y))); ctx.stroke();
        ctx.strokeStyle = `rgba(255,255,240,${k})`; ctx.lineWidth = w;
        ctx.stroke();
      }
      const [fx, fy] = b.foot;                                        // its reflection on the sea
      for (let i = 1; i < 12; i++) {
        const y = fy + i * 5, w = 10 + i * 2;
        ctx.globalAlpha = k * (0.6 - i * 0.045); ctx.fillStyle = '#fffbe0';
        ctx.fillRect(fx - w / 2 + Math.sin(i * 4.1) * 5, y, w, 1.5);
      }
      ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
      return k;
    }

    function draw(ctx, g, t, still) {
      for (const c of scud) {                         // low cloud racing over
        const x = ((c.x0 + (still ? 0 : t / 70000)) % 1.3 - 0.15) * g.W, y = c.y * g.horizon, r = c.r * g.W;
        const m = ctx.createRadialGradient(x, y, 0, x, y, r);
        m.addColorStop(0, 'rgba(60,70,84,0.35)'); m.addColorStop(1, 'rgba(60,70,84,0)');
        ctx.save(); ctx.translate(x, y); ctx.scale(1, 0.35); ctx.translate(-x, -y);
        ctx.fillStyle = m; ctx.fillRect(x - r, y - r, r * 2, r * 2); ctx.restore();
      }
      const flash = strike(ctx, g, t, still) || 0;
      // Whitecaps on the crests.
      for (let i = 1; i < 12; i++) {
        const d = i / 12, y = g.rowY(d), n = Math.round(g.W / 160 * (0.5 + d));
        for (let j = 0; j < n; j++) {
          const ph = Math.sin((still ? 0 : t / 900) + i * 3.1 + j * 1.7);
          if (ph < 0.3) continue;
          const x = ((j / n + Math.sin(i * 9.7 + j) * 0.05 + (still ? 0 : t / (40000 - d * 20000))) % 1) * g.W;
          ctx.globalAlpha = (ph - 0.3) * 0.7; ctx.fillStyle = '#dfe8f0';
          ctx.fillRect(x, y - 1, 6 + d * 30 * ph, 1 + d * 1.8);
        }
      }
      ctx.globalAlpha = 1;
      for (const p of fleet(boats, g, t, still)) {
        const lit = flash > 0;
        wake(ctx, p.x, p.y, p.s, '#dfe8f0', 0.8);
        yacht(ctx, p.x, p.y, p.s, { heel: p.heel - p.b.heel * 2, reef: true, sail: lit ? '#9aa6b8' : '#3a4656', hull: '#080b10', mast: '#1c2531', rim: 'rgba(220,230,245,0.7)' });
        if (!still) {                                 // spray off the bow
          for (let k = 0; k < 6; k++) {
            const u = (t / 500 + k / 6) % 1;
            ctx.globalAlpha = (1 - u) * 0.7; ctx.fillStyle = '#e8eef4';
            ctx.fillRect(p.x + 22 * p.s + u * 10 * p.s, p.y - 6 * p.s - Math.sin(u * 3.1) * 10 * p.s, 1.6, 1.6);
          }
          ctx.globalAlpha = 1;
        }
      }
      // Driving rain, slanting with the wind.
      ctx.strokeStyle = 'rgba(184,198,214,0.28)'; ctx.lineWidth = 1;
      ctx.beginPath();
      for (const d of drops) {
        const y = ((d.y + (still ? 0 : t / 900 * d.v)) % 1) * (g.H + 40) - 20;
        const x = ((d.x + (still ? 0 : t / 900 * d.v * 0.3)) % 1.1 - 0.05) * g.W;
        ctx.moveTo(x, y); ctx.lineTo(x - d.l * 0.3, y - d.l);
      }
      ctx.stroke();
    }

    return { palette, sky, land, draw };
  }

  window.createSquallLayer = squall;
})();
