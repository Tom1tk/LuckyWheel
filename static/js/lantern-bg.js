// Night Race: the Tide 9.6 dressing on the Season 9 tides scene (static/js/tides-bg.js).
// Same API as bonfire-bg.js: createLanternLayer() returns { palette, sky, land, draw }.
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

  // ── 2 · Night Race ─────────────────────────────────────────────────────────
  // The usual night sea. A lantern-lit fleet races through a course of floating
  // lanterns, each boat leaving a glowing wake; a second lighthouse sweeps the far shore.
  function night() {
    const AMBER = '#FFC266';
    const palette = { win: AMBER, lose: '#FF4D5E', lamp: '255,200,120' };
    const boats = [
      { d: 0.12, x0: 0.18, v: 18, bob: 820 },
      { d: 0.2, x0: 0.62, v: 21, bob: 900 },
      { d: 0.3, x0: 0.9, v: 24, bob: 780 },
      { d: 0.42, x0: 0.4, v: 28, bob: 860 },
      { d: 0.56, x0: 0.75, v: 33, bob: 960 },
    ];
    const farX = g => g.W - (phone(g) ? 22 : 54);

    function sky(ctx, g) {
      const halo = ctx.createRadialGradient(g.moonX, g.moonY, g.moonR * 0.8, g.moonX, g.moonY, g.moonR * 3);
      halo.addColorStop(0, 'rgba(255,194,102,0.16)'); halo.addColorStop(1, 'rgba(255,194,102,0)');
      ctx.fillStyle = halo; ctx.fillRect(0, 0, g.W, g.horizon);
    }

    // Lanterns held by onlookers along the clifftop, and the far lighthouse's rock.
    function land(ctx, g) {
      const lx = g.lighthouseX(), base = g.horizon + 2;
      for (let i = 0; i < 9; i++) {
        const x = lx - 26 - i * 17;
        if (x < 8) break;
        const y = base - g.H * (0.07 - 0.025 * x / (lx + 24)) - 8 - (i % 2) * 3;
        const gl = ctx.createRadialGradient(x, y, 0, x, y, 9);
        gl.addColorStop(0, 'rgba(255,200,120,0.9)'); gl.addColorStop(1, 'rgba(255,200,120,0)');
        ctx.fillStyle = gl; ctx.fillRect(x - 9, y - 9, 18, 18);
      }
      const fx = farX(g);
      ctx.fillStyle = '#02070f';
      ctx.beginPath(); ctx.ellipse(fx, g.horizon + 1, 26, 6, 0, Math.PI, 0); ctx.fill();
      ctx.beginPath(); ctx.moveTo(fx - 4, g.horizon - 3); ctx.lineTo(fx - 2.5, g.horizon - 30); ctx.lineTo(fx + 2.5, g.horizon - 30); ctx.lineTo(fx + 4, g.horizon - 3); ctx.fill();
    }

    function farBeam(ctx, g, t, still) {
      const lx = farX(g), ly = g.horizon - 32, a = still ? 2.6 : t / 3400 + 1;
      const reach = -Math.abs(Math.cos(a)) * g.W * 0.45 * (Math.sin(a) > 0 ? 1 : 0.35);
      const gr = ctx.createLinearGradient(lx, ly, lx + reach, ly);
      gr.addColorStop(0, 'rgba(255,214,150,0.22)'); gr.addColorStop(1, 'rgba(255,214,150,0)');
      ctx.fillStyle = gr;
      const spread = 4 + Math.abs(reach) * 0.09;   // the cone widens with its reach
      ctx.beginPath(); ctx.moveTo(lx, ly - 1.5); ctx.lineTo(lx + reach, ly - spread); ctx.lineTo(lx + reach, ly + spread * 0.8); ctx.lineTo(lx, ly + 1.5); ctx.closePath(); ctx.fill();
      const gl = ctx.createRadialGradient(lx, ly, 0, lx, ly, 10);
      gl.addColorStop(0, 'rgba(255,214,150,0.95)'); gl.addColorStop(1, 'rgba(255,214,150,0)');
      ctx.fillStyle = gl; ctx.fillRect(lx - 10, ly - 10, 20, 20);
    }

    // The course: a curving line of floating lanterns from near left to far right.
    function course(ctx, g, t, still) {
      ctx.globalCompositeOperation = 'lighter';
      for (let i = 0; i < 14; i++) {
        const u = i / 13, d = 0.72 - u * 0.62;
        const x = g.W * (0.04 + u * 0.92) + Math.sin(u * 3.2) * g.W * 0.05;
        const y = g.rowY(d) + (still ? 0 : Math.sin(t / 700 + i * 1.7) * (1 + d * 3));
        const s = 0.5 + d * 1.6, flick = still ? 1 : 0.85 + 0.15 * Math.sin(t / 90 + i * 2.1);
        const gl = ctx.createRadialGradient(x, y - 3 * s, 0, x, y - 3 * s, 14 * s);
        gl.addColorStop(0, `rgba(255,200,110,${0.85 * flick})`); gl.addColorStop(1, 'rgba(255,160,60,0)');
        ctx.fillStyle = gl; ctx.fillRect(x - 14 * s, y - 17 * s, 28 * s, 28 * s);
        ctx.fillStyle = '#ffe2a8'; ctx.fillRect(x - 1.5 * s, y - 5 * s, 3 * s, 4 * s);
        ctx.globalAlpha = 0.4 * flick; ctx.fillStyle = AMBER;
        for (let k = 1; k < 4; k++) ctx.fillRect(x - (4 - k) * s, y + k * 3 * s, (8 - 2 * k) * s, 1.2);
        ctx.globalAlpha = 1;
      }
      ctx.globalCompositeOperation = 'source-over';
    }

    function boatLights(ctx, x, y, s, heel, t, still) {
      const pt = (px, py) => [x + px * s * Math.cos(heel) - py * s * Math.sin(heel), y + px * s * Math.sin(heel) + py * s * Math.cos(heel)];
      ctx.globalCompositeOperation = 'lighter';
      const dot = ([px, py], c, r) => {
        const gl = ctx.createRadialGradient(px, py, 0, px, py, r);
        gl.addColorStop(0, c); gl.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.fillStyle = gl; ctx.fillRect(px - r, py - r, r * 2, r * 2);
      };
      dot(pt(0, -54), 'rgba(255,255,255,0.95)', 4 + 3 * s);         // masthead
      dot(pt(20, -7), 'rgba(92,255,176,0.95)', 3 + 4 * s);          // starboard light
      dot(pt(-14, -10), `rgba(255,194,102,${still ? 0.9 : 0.75 + 0.2 * Math.sin(t / 80)})`, 6 + 9 * s);   // cockpit lantern
      ctx.globalCompositeOperation = 'source-over';
    }

    // Bioluminescent wake: sea-glass sparks streaming off the stern.
    function glowWake(ctx, x, y, s, t, still) {
      ctx.globalCompositeOperation = 'lighter';
      for (let i = 0; i < 18; i++) {
        const u = ((still ? 0.3 : t / 1600) + i / 18) % 1;
        const wx = x - 20 * s - u * 120 * s, wy = y + 1 + u * 4 * s + Math.sin(i * 7.3) * u * 5 * s;
        ctx.globalAlpha = (1 - u) * 0.8; ctx.fillStyle = i % 4 ? '#3fd6c6' : '#b8fff4';
        ctx.fillRect(wx, wy, 1.5 + s, 1.5);
      }
      ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
    }

    function draw(ctx, g, t, still) {
      farBeam(ctx, g, t, still);
      course(ctx, g, t, still);
      for (const p of fleet(boats, g, t, still)) {
        glowWake(ctx, p.x, p.y, p.s, t, still);
        yacht(ctx, p.x, p.y, p.s, { heel: p.heel - 0.05, sail: '#16263a', hull: '#060d16', mast: '#16263a', rim: 'rgba(255,194,102,0.75)' });
        boatLights(ctx, p.x, p.y, p.s, p.heel - 0.05, t, still);
      }
    }

    return { palette, sky, land, draw };
  }

  window.createLanternLayer = night;
})();
