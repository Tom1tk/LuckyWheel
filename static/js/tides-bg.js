// Season 9: tides page-background scene (HTML5 Canvas).
// Exposes window.createTidesScene(canvas, opts) -> { stop }.
//
// A night sea. The wheel hangs over the horizon like the moon and lays a
// glittering path across the water; a lighthouse sweeps the headland, two
// buoys blink sea-glass and coral, and a fishing boat bobs with its lantern.
// Bioluminescent sparks in the swell nod to Season 5. Motion is slow; with
// opts.lowSpec or prefers-reduced-motion a single static frame is drawn.
(function () {
  'use strict';

  const DEFAULT_PALETTE = {
    skyTop:   '#040a18',
    skyLow:   '#0d2742',
    seaTop:   '#0a2438',
    seaLow:   '#030c17',
    land:     '#02070f',
    win:      '#3fd6c6',   // sea-glass (wins)
    lose:     '#ff7f6e',   // coral (losses)
    sand:     '#f2e3c6',
    lamp:     '255,214,140',
  };

  function createTidesScene(canvas, opts) {
    opts = opts || {};
    const pal = Object.assign({}, DEFAULT_PALETTE, opts.palette || {});
    const reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const still = !!opts.lowSpec || reduce;
    const ctx = canvas.getContext('2d');
    let W = 0, H = 0, dpr = 1, horizon = 0, moonX = 0, moonY = 0, moonR = 0;
    let stars = [], sparks = [], raf = 0, running = true;
    const start = performance.now();

    // Deterministic pseudo-random so the static frame is stable between loads.
    let seed = 9;
    const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);

    function layout() {
      const wheel = document.querySelector('.wheel-wrapper');
      const r = wheel && wheel.getBoundingClientRect();
      if (r && r.width) {
        moonX = r.left + r.width / 2; moonY = r.top + r.height / 2; moonR = r.width / 2;
      } else {
        moonX = W / 2; moonY = H * 0.4; moonR = Math.min(W, H) * 0.18;
      }
      // The sea starts just under the wheel, never above 55% of the screen.
      horizon = Math.max(H * 0.55, Math.min(H * 0.72, moonY + moonR + 18));
    }

    function seedScene() {
      seed = 9;
      stars = Array.from({ length: Math.round(W * H / 9000) }, () => ({
        x: rnd() * W, y: rnd() * horizon * 0.95, r: rnd() * 1.3 + 0.2, p: rnd() * 6.28,
      }));
      sparks = Array.from({ length: still ? 40 : 70 }, () => ({
        x: rnd() * W, y: horizon + 30 + rnd() * (H - horizon), p: rnd() * 6.28, s: rnd() * 0.4 + 0.2,
        c: rnd() < 0.8 ? pal.win : pal.lose,
      }));
    }

    function resize() {
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      W = canvas.clientWidth; H = canvas.clientHeight;
      canvas.width = W * dpr; canvas.height = H * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      layout(); seedScene();
      if (still && running) frame(start);
    }

    function sky(t) {
      const g = ctx.createLinearGradient(0, 0, 0, horizon);
      g.addColorStop(0, pal.skyTop); g.addColorStop(1, pal.skyLow);
      ctx.fillStyle = g; ctx.fillRect(0, 0, W, horizon + 1);
      for (const s of stars) {
        ctx.globalAlpha = 0.35 + 0.45 * (0.5 + 0.5 * Math.sin(t / 900 + s.p));
        ctx.fillStyle = pal.sand;
        ctx.fillRect(s.x, s.y, s.r, s.r);
      }
      ctx.globalAlpha = 1;
      // Moon-glow from the wheel, warming the sky above the horizon.
      const halo = ctx.createRadialGradient(moonX, moonY, moonR * 0.8, moonX, moonY, moonR * 3.2);
      halo.addColorStop(0, 'rgba(63,214,198,0.16)'); halo.addColorStop(1, 'rgba(63,214,198,0)');
      ctx.fillStyle = halo; ctx.fillRect(0, 0, W, horizon);
    }

    function headland(t) {
      // Low cliff running in from the left; the lighthouse stands at its tip,
      // in the open water between the left-hand panels and the wheel.
      // Phones: the wheel fills the width, so tuck the lighthouse against the edge.
      const lx = moonX - moonR < 60 ? 26 : Math.max(70, moonX - moonR * 2.35), base = horizon + 2;
      ctx.fillStyle = pal.land;
      ctx.beginPath();
      ctx.moveTo(0, base - H * 0.07);
      ctx.quadraticCurveTo(lx * 0.6, base - H * 0.09, lx + 24, base - H * 0.045);
      ctx.quadraticCurveTo(lx + 70, base - 6, lx + 140, base);
      ctx.lineTo(0, base); ctx.closePath(); ctx.fill();

      const top = base - H * 0.045 - 54;
      ctx.beginPath();
      ctx.moveTo(lx - 8, base - H * 0.045 + 2); ctx.lineTo(lx - 5, top);
      ctx.lineTo(lx + 5, top); ctx.lineTo(lx + 8, base - H * 0.045 + 2); ctx.closePath();
      ctx.fill();
      ctx.fillStyle = 'rgba(242,227,198,0.22)';           // painted bands
      ctx.fillRect(lx - 7, top + 18, 14, 5); ctx.fillRect(lx - 7.5, top + 34, 15, 5);
      ctx.fillStyle = pal.land; ctx.fillRect(lx - 7, top - 4, 14, 4);
      ctx.beginPath(); ctx.moveTo(lx - 6, top - 13); ctx.lineTo(lx, top - 20); ctx.lineTo(lx + 6, top - 13); ctx.fill();

      // Rotating beam: a cone whose apparent length foreshortens as it turns.
      const a = still ? 0.35 : t / 2600;
      const reach = Math.cos(a) * W * 0.55;
      const lampY = top - 9;
      const g = ctx.createLinearGradient(lx, lampY, lx + reach, lampY);
      g.addColorStop(0, `rgba(${pal.lamp},0.35)`); g.addColorStop(1, `rgba(${pal.lamp},0)`);
      ctx.fillStyle = g;
      ctx.beginPath();
      ctx.moveTo(lx, lampY); ctx.lineTo(lx + reach, lampY - 26); ctx.lineTo(lx + reach, lampY + 22);
      ctx.closePath(); ctx.fill();
      const glow = ctx.createRadialGradient(lx, lampY, 0, lx, lampY, 16);
      glow.addColorStop(0, `rgba(${pal.lamp},0.95)`); glow.addColorStop(1, `rgba(${pal.lamp},0)`);
      ctx.fillStyle = glow; ctx.fillRect(lx - 16, lampY - 16, 32, 32);
    }

    function sea() {
      const g = ctx.createLinearGradient(0, horizon, 0, H);
      g.addColorStop(0, pal.seaTop); g.addColorStop(1, pal.seaLow);
      ctx.fillStyle = g; ctx.fillRect(0, horizon, W, H - horizon);
    }

    // Depth 0 at the horizon, 1 at the bottom edge; rows bunch up near the horizon.
    const rowY = d => horizon + (H - horizon) * d * d;

    function glitter(t) {
      // The wheel's light on the water: flickering dashes that widen toward the viewer.
      const rows = 46;
      for (let i = 1; i < rows; i++) {
        const d = i / rows, y = rowY(d);
        const spread = moonR * (0.22 + d * 0.8);
        const n = 2 + Math.floor(d * 5);
        for (let k = 0; k < n; k++) {
          const ph = Math.sin(t / 420 + i * 1.7 + k * 2.3);
          if (ph < -0.2) continue;
          const x = moonX + Math.sin(i * 12.9898 + k * 78.233) * spread;
          const w = 4 + d * 26 * (0.5 + 0.5 * ph);
          ctx.globalAlpha = (0.2 + 0.5 * ph) * (1 - d * 0.75);
          ctx.fillStyle = (i + k) % 7 === 0 ? pal.lose : (i + k) % 3 === 0 ? pal.sand : pal.win;
          ctx.fillRect(x - w / 2, y, w, 1 + d * 2);
        }
      }
      ctx.globalAlpha = 1;
    }

    function swell(t) {
      // Layered crests drifting sideways; nearer rows are taller and slower.
      for (let i = 0; i < 9; i++) {
        const d = (i + 1) / 10, y0 = rowY(d);
        const amp = 1.5 + d * 9, len = 90 + d * 260, sp = (still ? 0 : t) / (2400 + d * 1800);
        ctx.beginPath();
        for (let x = -10; x <= W + 10; x += 12) {
          const y = y0 + Math.sin(x / len * 6.28 + sp + i * 1.3) * amp + Math.sin(x / (len * 0.37) - sp * 1.6) * amp * 0.3;
          x === -10 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
        }
        ctx.strokeStyle = `rgba(127,209,199,${0.05 + d * 0.13})`;
        ctx.lineWidth = 1 + d * 1.6;
        ctx.stroke();
      }
    }

    function buoy(x, d, t, color, period) {
      const y = rowY(d) + Math.sin((still ? 0 : t) / 700 + x) * (2 + d * 4);
      const s = 0.5 + d * 1.1;
      ctx.fillStyle = '#081420';
      ctx.beginPath();
      ctx.moveTo(x - 7 * s, y); ctx.lineTo(x - 3 * s, y - 16 * s); ctx.lineTo(x + 3 * s, y - 16 * s); ctx.lineTo(x + 7 * s, y);
      ctx.closePath(); ctx.fill();
      const on = still || Math.floor(t / period) % 2 === 0;
      if (!on) return;
      const ly = y - 19 * s;
      const g = ctx.createRadialGradient(x, ly, 0, x, ly, 18 * s);
      g.addColorStop(0, color); g.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = g; ctx.fillRect(x - 18 * s, ly - 18 * s, 36 * s, 36 * s);
      ctx.fillStyle = '#fff'; ctx.fillRect(x - 1, ly - 1, 2, 2);
      // its own small reflection
      ctx.globalAlpha = 0.35; ctx.fillStyle = color; ctx.fillRect(x - 4 * s, y + 3, 8 * s, 1.5); ctx.globalAlpha = 1;
    }

    function boat(t) {
      const x = Math.min(W - 52, moonX + moonR * 1.55), d = 0.2;
      const bob = still ? 0 : Math.sin(t / 900) * 3, tilt = still ? 0 : Math.sin(t / 1100) * 0.04;
      const y = rowY(d) + bob;
      ctx.save(); ctx.translate(x, y); ctx.rotate(tilt);
      ctx.fillStyle = '#061019';
      ctx.beginPath(); ctx.moveTo(-34, -8); ctx.lineTo(34, -8); ctx.quadraticCurveTo(26, 6, -26, 6); ctx.closePath(); ctx.fill();
      ctx.fillRect(-6, -22, 16, 14);                                  // wheelhouse
      ctx.fillStyle = `rgba(${pal.lamp},0.85)`; ctx.fillRect(-2, -18, 5, 5); // lit window
      ctx.strokeStyle = '#061019'; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.moveTo(-20, -8); ctx.lineTo(-44, -44); ctx.stroke();      // rod
      ctx.strokeStyle = 'rgba(242,227,198,0.35)'; ctx.lineWidth = 0.8;
      ctx.beginPath(); ctx.moveTo(-44, -44); ctx.quadraticCurveTo(-52, -10, -50, 10); ctx.stroke(); // line
      const lg = ctx.createRadialGradient(24, -14, 0, 24, -14, 26);
      lg.addColorStop(0, `rgba(${pal.lamp},0.8)`); lg.addColorStop(1, `rgba(${pal.lamp},0)`);
      ctx.fillStyle = lg; ctx.fillRect(-2, -40, 52, 52);              // lantern
      ctx.restore();
      ctx.globalAlpha = 0.22; ctx.fillStyle = `rgb(${pal.lamp})`;
      for (let i = 1; i < 6; i++) ctx.fillRect(x + 20 - i, y + 8 + i * 5, 6 + i * 2, 1.5);
      ctx.globalAlpha = 1;
    }

    function plankton(t) {
      for (const s of sparks) {
        const a = 0.5 + 0.5 * Math.sin((still ? 0 : t) / 600 * s.s + s.p);
        if (a < 0.55) continue;
        const x = (s.x + (still ? 0 : t) * 0.004 * s.s) % W;
        ctx.globalAlpha = (a - 0.5) * 1.6;
        const g = ctx.createRadialGradient(x, s.y, 0, x, s.y, 5);
        g.addColorStop(0, s.c); g.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.fillStyle = g; ctx.fillRect(x - 5, s.y - 5, 10, 10);
      }
      ctx.globalAlpha = 1;
    }

    function frame(now) {
      if (!running) return;
      const t = now - start;
      if (!still && t % 1000 < 17) layout();   // follow the wheel if the layout shifts
      sky(t); sea(); headland(t); glitter(t); swell(t);
      buoy(moonX - moonR * 1.45, 0.14, t, pal.win, 1300);
      buoy(moonX + moonR * 1.05, 0.06, t, pal.lose, 1700);
      boat(t); plankton(t);
      if (!still) raf = requestAnimationFrame(frame);
    }

    resize();
    window.addEventListener('resize', resize);
    if (!still) raf = requestAnimationFrame(frame);

    return {
      stop() {
        running = false;
        cancelAnimationFrame(raf);
        window.removeEventListener('resize', resize);
      },
    };
  }

  window.createTidesScene = createTidesScene;
})();
