// Season 9: arcade page-background scene (HTML5 Canvas).
// Exposes window.createArcadeScene(canvas, opts) -> { stop }.
//
// A neon synthwave arcade: a retro sun with horizontal slit-lines setting
// over a perspective grid floor, stars drifting overhead, occasional coin
// sparkles, and a subtle scanline shimmer. Motion is slow and minimal —
// busy but not overstimulating.
//
// All colours come from opts.palette so the theme is switchable, not
// hardcoded. The same win/lose pair is mirrored in app.jsx
// THEME_COLORS.arcade so the wheel and the background share one theme.
(function () {
  'use strict';

  // Default arcade palette. Neon magenta = wins, electric cyan = losses,
  // warm gold for the retro sun and grid highlights.
  const DEFAULT_PALETTE = {
    skyTop:    '#0a0420',
    skyMid:    '#1a0a3d',
    skyHorizon:'#3d1048',
    sunCore:   '#ff2e88',
    sunEdge:   '#ffb14d',
    gridHi:    '#ff2ed0',   // grid nearest the viewer (win colour)
    gridLo:    '#2a1050',   // grid at the horizon
    star:      '#cfe8ff',
    lose:      '#00c8ff',
    scanline:  'rgba(0,0,0,0.10)',
    glow:      '255,46,208', // magenta (rgb triplet for rgba())
  };

  function createArcadeScene(canvas, opts) {
    opts = opts || {};
    const palette = Object.assign({}, DEFAULT_PALETTE, opts.palette || {});
    const lowSpec = !!opts.lowSpec;
    const ctx = canvas.getContext('2d', { alpha: true });

    let dpr = Math.min(window.devicePixelRatio || 1, 2);
    let W = 0, H = 0, cx = 0, cy = 0;
    let raf = 0, running = true, start = performance.now();

    const rand = (a, b) => Math.random() * (b - a) + a;
    const rgba = (rgb, a) => `rgba(${rgb},${a})`;

    // Stars drifting slowly in the upper sky.
    let stars = [];
    function seedStars() {
      const n = lowSpec ? 0 : 90;
      stars = [];
      for (let i = 0; i < n; i++) {
        stars.push({
          x: Math.random(), y: Math.random() * 0.55,
          r: rand(0.4, 1.4),
          vx: rand(-0.003, 0.003),
          a: rand(0.15, 0.8), tw: rand(0.5, 1.5), ph: rand(0, Math.PI * 2),
        });
      }
    }

    // Coin sparkles that occasionally blink in the foreground grid.
    let coins = [];
    function seedCoins() {
      const n = lowSpec ? 0 : 12;
      coins = [];
      for (let i = 0; i < n; i++) {
        coins.push({
          x: Math.random(), z: rand(0.2, 0.9),   // 0=far, 1=near
          ph: rand(0, Math.PI * 2), speed: rand(0.02, 0.06),
        });
      }
    }

    function resize() {
      const rect = canvas.getBoundingClientRect();
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      W = canvas.width = Math.max(1, Math.round(rect.width * dpr));
      H = canvas.height = Math.max(1, Math.round(rect.height * dpr));
      cx = W / 2;
      cy = H / 2;
    }

    function drawSky(t) {
      // Vertical gradient: deep indigo up top → horizon magenta band.
      const g = ctx.createLinearGradient(0, 0, 0, H * 0.55);
      g.addColorStop(0, palette.skyTop);
      g.addColorStop(0.7, palette.skyMid);
      g.addColorStop(1, palette.skyHorizon);
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, W, H);
    }

    function drawSun(t) {
      // Retro sun: a large circle clipped with horizontal slits, sitting
      // just above the horizon. Subtle pulse via alpha/scale on the glow.
      // Season 9 polish: the sun used to sit at H*0.46, i.e. dead behind the
      // centered wheel (~98% hidden). It now rises above the wheel — its top
      // edge clears the page header (bottom ~150px) and its lower half is
      // overlapped by the wheel, so it reads as a synthwave sun rising over
      // the play area instead of vanishing behind it.
      const sunTop = Math.max(170, H * 0.17);
      const sunR = Math.min(W * 0.22, H * 0.18);
      const sunY = sunTop + sunR;
      const pulse = 0.9 + 0.1 * Math.sin(t * 0.0006);

      ctx.save();
      // Halo glow
      const halo = ctx.createRadialGradient(cx, sunY, sunR * 0.2, cx, sunY, sunR * 2.1);
      halo.addColorStop(0, rgba(palette.glow, 0.28));
      halo.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = halo;
      ctx.fillRect(0, 0, W, H);

      ctx.beginPath();
      ctx.arc(cx, sunY, sunR * pulse, 0, Math.PI * 2);
      ctx.clip();

      const g = ctx.createLinearGradient(0, sunY - sunR, 0, sunY + sunR);
      g.addColorStop(0, palette.sunEdge);
      g.addColorStop(0.5, palette.sunCore);
      g.addColorStop(1, palette.sunEdge);
      ctx.fillStyle = g;
      ctx.fillRect(cx - sunR, sunY - sunR, sunR * 2, sunR * 2);

      // Slit lines (the classic synthwave cut)
      ctx.fillStyle = palette.skyMid;
      const slitCount = Math.max(4, Math.floor(sunR / 16));
      for (let i = 0; i < slitCount; i++) {
        const sy = sunY - sunR + ((i + 0.5) / slitCount) * sunR * 2;
        const halfW = sunR * 0.75 * Math.sin(Math.acos(Math.min(1, (sy - sunY) / sunR)));
        ctx.fillRect(cx - halfW, sy - 2, halfW * 2, 4);
      }
      ctx.restore();
    }

    function drawStars(t) {
      if (lowSpec) return;
      for (const s of stars) {
        s.x += s.vx;
        if (s.x < 0) s.x = 1;
        if (s.x > 1) s.x = 0;
        const alpha = s.a * (0.5 + 0.5 * Math.sin(t * 0.001 * s.tw + s.ph));
        ctx.globalAlpha = Math.max(0, alpha);
        ctx.fillStyle = palette.star;
        ctx.beginPath();
        ctx.arc(s.x * W, s.y * H, s.r, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.globalAlpha = 1;
    }

    function drawGrid(t) {
      // Perspective floor: horizon at 55%, vanishing point at centre.
      const horizon = H * 0.55;
      const vanishX = cx, vanishY = horizon;
      const spokes = 14;
      const rings = 7;

      ctx.lineWidth = 1;
      for (let i = 0; i <= rings; i++) {
        const f = Math.pow(1.15, i) - 1;              // near rings spaced further
        const yy = horizon + (H - horizon) * Math.min(1, f / 2.2);
        const bright = i / rings;
        ctx.strokeStyle = i === 0 ? 'rgba(0,0,0,0)' : blendHex(palette.gridLo, palette.gridHi, bright);
        ctx.globalAlpha = 0.35 + 0.65 * bright;
        ctx.beginPath();
        ctx.moveTo(0, yy);
        ctx.lineTo(W, yy);
        ctx.stroke();
      }
      ctx.globalAlpha = 1;

      for (let i = -spokes / 2; i <= spokes / 2; i++) {
        if (i === 0) continue;
        const xv = vanishX + i * (W / spokes);
        ctx.strokeStyle = blendHex(palette.gridLo, palette.gridHi, 0.6);
        ctx.globalAlpha = 0.35;
        ctx.beginPath();
        ctx.moveTo(vanishX, vanishY);
        ctx.lineTo(xv, H);
        ctx.stroke();
      }
      ctx.globalAlpha = 1;

      drawCoins(t, horizon);
    }

    function blendHex(a, b, t) {
      const pa = [parseInt(a.slice(1, 3), 16), parseInt(a.slice(3, 5), 16), parseInt(a.slice(5, 7), 16)];
      const pb = [parseInt(b.slice(1, 3), 16), parseInt(b.slice(3, 5), 16), parseInt(b.slice(5, 7), 16)];
      const r = Math.round(pa[0] + (pb[0] - pa[0]) * t);
      const g = Math.round(pa[1] + (pb[1] - pa[1]) * t);
      const b2 = Math.round(pa[2] + (pb[2] - pa[2]) * t);
      return `rgb(${r},${g},${b2})`;
    }

    function drawCoins(t, horizon) {
      if (lowSpec) return;
      for (const c of coins) {
        const blink = 0.5 + 0.5 * Math.sin(t * 0.001 * c.speed + c.ph);
        if (blink < 0.55) continue;
        const yy = horizon + (H - horizon) * c.z;
        const xx = (c.x * 2 - 1) * W * 0.45 * (0.5 + c.z) + cx;
        const r = 2 + 5 * c.z;
        ctx.globalAlpha = (blink - 0.5) * 1.6;
        ctx.fillStyle = palette.sunEdge;
        ctx.beginPath();
        ctx.arc(xx, yy, r, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = palette.gridHi;
        ctx.stroke();
      }
      ctx.globalAlpha = 1;
    }

    function drawScanlines() {
      // Faint horizontal scanlines over everything (CRT feel).
      ctx.fillStyle = palette.scanline;
      const gap = 3;
      for (let y = 0; y < H; y += gap) {
        ctx.fillRect(0, y, W, 1);
      }
    }

    function drawVignette() {
      const g = ctx.createRadialGradient(cx, cy, Math.min(W, H) * 0.35, cx, cy, Math.max(W, H) * 0.75);
      g.addColorStop(0, 'rgba(0,0,0,0)');
      g.addColorStop(1, 'rgba(0,0,0,0.55)');
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, W, H);
    }

    function frame(now) {
      if (!running) return;
      const t = now - start;
      ctx.clearRect(0, 0, W, H);
      drawSky(t);
      drawStars(t);
      drawSun(t);
      drawGrid(t);
      drawScanlines();
      drawVignette();

      if (!lowSpec) raf = requestAnimationFrame(frame);
    }

    resize();
    seedStars();
    seedCoins();
    frame(performance.now());
    window.addEventListener('resize', resize);

    return {
      stop() {
        running = false;
        cancelAnimationFrame(raf);
        window.removeEventListener('resize', resize);
      },
    };
  }

  window.createArcadeScene = createArcadeScene;
})();
