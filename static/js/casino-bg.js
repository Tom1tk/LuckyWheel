// Season 8: casino page-background scene (HTML5 Canvas).
// Exposes window.createCasinoScene(canvas, opts) -> { stop }.
//
// A perspective casino room: a central green poker table on which the wheel
// (a separate, composited element) sits, surrounded by dimmer back tables and
// ambient elements (chips, cards, wall sconces, a hanging spotlight). Motion
// is deliberately slow and minimal — busy but not overstimulating.
//
// All colours come from opts.palette so the theme is switchable, not hardcoded.
// The same green=win / red=lose pair is mirrored in app.jsx THEME_COLORS.casino
// so the wheel and the background share one theme definition.
(function () {
  'use strict';

  // Default casino palette. Green felt + green chips = wins; red accents +
  // red chips = losses; warm gold trim and spotlight tie the room together.
  const DEFAULT_PALETTE = {
    bgTop:    '#0c1410',
    wallLo:   '#070f0b',   // wall near the floor
    floorLo:  '#160810',   // burgundy carpet at the horizon (far)
    floorHi:  '#240c12',   // carpet near the viewer (lit)
    feltHi:   '#0f6e36',   // green felt (win-themed)
    feltLo:   '#063d1f',
    rail:     '#2a0d0d',   // dark padded leather rail
    railHi:   '#7a1f1f',
    wood:     '#4f3420',   // racetrack (wood-effect ring)
    woodHi:   '#6e4a2c',
    gold:     '#d8b13f',
    win:      '#28e070',   // green accent
    lose:     '#ff4040',   // red accent
    chipGreen:'#1faa4e',
    chipRed:  '#d22f2f',
    chipGold: '#e8c24a',
    glow:     '255,224,150', // warm spotlight (rgb triplet for rgba())
  };

  function createCasinoScene(canvas, opts) {
    opts = opts || {};
    const palette = Object.assign({}, DEFAULT_PALETTE, opts.palette || {});
    const lowSpec = !!opts.lowSpec;
    const ctx = canvas.getContext('2d', { alpha: true });

    let dpr = Math.min(window.devicePixelRatio || 1, 2);
    let W = 0, H = 0, cx = 0, cy = 0;
    let raf = 0, running = true, start = performance.now();

    const rand = (a, b) => Math.random() * (b - a) + a;
    const rgba = (rgb, a) => `rgba(${rgb},${a})`;
    const hexA = (hex, a) => {
      const n = parseInt(hex.slice(1), 16);
      return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`;
    };

    // Dust motes drifting in the spotlight — the only free-moving elements.
    let motes = [];
    function seedMotes() {
      const n = lowSpec ? 0 : 26;
      motes = [];
      for (let i = 0; i < n; i++) {
        motes.push({
          x: Math.random(), y: Math.random(),
          r: rand(0.6, 2.0),
          vx: rand(-0.012, 0.012), vy: rand(-0.02, -0.004),
          a: rand(0.05, 0.22), tw: rand(0.4, 1.3), ph: rand(0, Math.PI * 2),
        });
      }
    }

    // Slot machines lining the left and right walls. Seeded once (positions,
    // colours, reel symbols, spin cadence are fixed for the session so nothing
    // flickers); reels/lights animate as deterministic functions of time.
    let slots = [];
    const SLOT_COLORS = [
      ['#ff5a5a', '#9c1818'], ['#3fd07a', '#0d7236'], ['#f2c84b', '#946410'],
      ['#5aa9ff', '#16458c'], ['#c46bff', '#581a96'], ['#3fe0d0', '#0d7068'],
    ];
    function seedSlots() {
      slots = [];
      const perSide = 3;
      ['L', 'R'].forEach((side) => {
        for (let i = 0; i < perSide; i++) {
          const fy = 0.34 + (i + rand(0.2, 0.8)) / perSide * 0.56;  // spread, separated
          slots.push({
            side, fy,
            fx: side === 'L' ? rand(0.045, 0.08) : rand(0.92, 0.955),
            color: SLOT_COLORS[Math.floor(Math.random() * SLOT_COLORS.length)],
            cycle: rand(5.5, 11),            // seconds between spins
            phase: rand(0, 11),
            base: [0, 1, 2].map(() => Math.floor(rand(0, 7))),
            lightOff: Math.floor(rand(0, 3)),
          });
        }
      });
    }

    function resize() {
      const rect = canvas.getBoundingClientRect();
      W = Math.max(1, Math.floor(rect.width || window.innerWidth));
      H = Math.max(1, Math.floor(rect.height || window.innerHeight));
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.floor(W * dpr);
      canvas.height = Math.floor(H * dpr);
      canvas.style.width = W + 'px';
      canvas.style.height = H + 'px';
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      cx = W * 0.5;
      cy = H * 0.5;
      // Low-spec has no animation loop, so repaint the static frame on resize.
      if (lowSpec && running) frame(performance.now());
    }

    // Horizon line (wall meets floor); the floor recedes below it so tables
    // read as sitting in a room rather than floating.
    function horizonY() { return H * 0.42; }

    // ── Room: back wall + receding carpet floor with perspective ────────────
    function drawRoom() {
      const Hh = horizonY();

      // Wall (above the horizon).
      const wall = ctx.createLinearGradient(0, 0, 0, Hh);
      wall.addColorStop(0, palette.bgTop);
      wall.addColorStop(1, palette.wallLo);
      ctx.fillStyle = wall;
      ctx.fillRect(0, 0, W, Hh);

      // Floor (below the horizon) — burgundy casino carpet.
      const floor = ctx.createLinearGradient(0, Hh, 0, H);
      floor.addColorStop(0, palette.floorLo);
      floor.addColorStop(1, palette.floorHi);
      ctx.fillStyle = floor;
      ctx.fillRect(0, Hh, W, H - Hh);

      // Perspective: lines converging to a vanishing point on the horizon,
      // plus depth lines bunched near the horizon. Sells the floor plane.
      ctx.save();
      ctx.globalAlpha = 0.05;
      ctx.strokeStyle = palette.gold;
      ctx.lineWidth = 1;
      const vpx = W * 0.5, n = 16;
      for (let i = 0; i <= n; i++) {
        const fx = (i / n) * (W * 2) - W * 0.5;
        ctx.beginPath(); ctx.moveTo(vpx, Hh); ctx.lineTo(fx, H); ctx.stroke();
      }
      for (let i = 1; i <= 5; i++) {
        const fy = Hh + (H - Hh) * Math.pow(i / 6, 1.8);
        ctx.beginPath(); ctx.moveTo(0, fy); ctx.lineTo(W, fy); ctx.stroke();
      }
      ctx.restore();

      // Soft warm band where wall meets floor (ambient bounce).
      const hg = ctx.createLinearGradient(0, Hh - H * 0.07, 0, Hh + H * 0.06);
      hg.addColorStop(0, 'rgba(0,0,0,0)');
      hg.addColorStop(0.55, rgba(palette.glow, 0.05));
      hg.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = hg;
      ctx.fillRect(0, Hh - H * 0.07, W, H * 0.13);
    }

    // ── Wall sconces: warm glows down the left and right walls ──────────────
    function drawSconces(t) {
      const ys = [0.22, 0.46];
      const breathe = 0.85 + 0.15 * Math.sin(t * 0.0006);
      ys.forEach((fy, i) => {
        const y = H * fy;
        [W * 0.06, W * 0.94].forEach((x) => {
          const r = Math.max(60, W * 0.09) * (i === 0 ? 1 : 0.8);
          const g = ctx.createRadialGradient(x, y, 0, x, y, r);
          g.addColorStop(0, rgba(palette.glow, 0.16 * breathe));
          g.addColorStop(1, rgba(palette.glow, 0));
          ctx.fillStyle = g;
          ctx.fillRect(x - r, y - r, r * 2, r * 2);
        });
      });
    }

    // ── A poker table (perspective oval) ────────────────────────────────────
    // Layers, outer → inner: contact shadow + pedestal (grounds it on the
    // floor), table side-thickness (skirt), padded rail, wood racetrack, felt.
    // detail=true adds betting line, stitching and a dealer chip tray (main
    // table only). alpha dims the distant back tables.
    function drawTable(tx, ty, rx, ry, alpha, detail) {
      ctx.save();
      ctx.globalAlpha = alpha;

      const thick = ry * 0.18;           // tabletop side thickness
      const baseY = ty + ry + thick * 1.6;

      // Contact shadow on the floor — anchors the table, kills the float.
      const sg = ctx.createRadialGradient(tx, ty + ry * 0.9, ry * 0.2, tx, ty + ry * 0.9, rx * 1.2);
      sg.addColorStop(0, 'rgba(0,0,0,0.55)');
      sg.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = sg;
      ctx.beginPath();
      ctx.ellipse(tx, ty + ry * 0.9, rx * 1.15, ry * 0.55, 0, 0, Math.PI * 2);
      ctx.fill();

      // Pedestal: base foot on the floor + tapered central column.
      ctx.fillStyle = '#0b0505';
      ctx.beginPath();
      ctx.ellipse(tx, baseY, rx * 0.36, ry * 0.2, 0, 0, Math.PI * 2);
      ctx.fill();
      const colTop = ty + ry * 0.7, colTW = rx * 0.15, colBW = rx * 0.27;
      const cg = ctx.createLinearGradient(tx - colBW, 0, tx + colBW, 0);
      cg.addColorStop(0, '#160a0a'); cg.addColorStop(0.5, '#3a201a'); cg.addColorStop(1, '#160a0a');
      ctx.fillStyle = cg;
      ctx.beginPath();
      ctx.moveTo(tx - colTW, colTop); ctx.lineTo(tx + colTW, colTop);
      ctx.lineTo(tx + colBW, baseY);  ctx.lineTo(tx - colBW, baseY);
      ctx.closePath(); ctx.fill();

      // Table side-thickness (skirt): a dark copy of the top, offset down.
      ctx.fillStyle = '#180a0a';
      ctx.beginPath();
      ctx.ellipse(tx, ty + thick, rx, ry, 0, 0, Math.PI * 2);
      ctx.fill();

      // Padded leather rail (bullnose).
      const rg = ctx.createLinearGradient(tx, ty - ry, tx, ty + ry);
      rg.addColorStop(0, palette.railHi);
      rg.addColorStop(0.5, palette.rail);
      rg.addColorStop(1, '#1c0909');
      ctx.fillStyle = rg;
      ctx.beginPath();
      ctx.ellipse(tx, ty, rx, ry, 0, 0, Math.PI * 2);
      ctx.fill();
      // Sheen along the top of the padded rail.
      ctx.lineWidth = Math.max(1.5, ry * 0.05);
      ctx.strokeStyle = 'rgba(255,180,150,0.12)';
      ctx.beginPath();
      ctx.ellipse(tx, ty, rx * 0.985, ry * 0.985, 0, Math.PI * 1.08, Math.PI * 1.92);
      ctx.stroke();

      // Racetrack — wood-effect ring inside the rail (rests chips/drinks).
      const wg = ctx.createLinearGradient(tx, ty - ry, tx, ty + ry);
      wg.addColorStop(0, palette.woodHi); wg.addColorStop(1, palette.wood);
      ctx.fillStyle = wg;
      ctx.beginPath();
      ctx.ellipse(tx, ty, rx * 0.9, ry * 0.9, 0, 0, Math.PI * 2);
      ctx.fill();

      // Felt playing surface.
      const fInner = 0.78;
      const fg = ctx.createRadialGradient(tx, ty - ry * 0.25, ry * 0.1, tx, ty, rx * fInner);
      fg.addColorStop(0, palette.feltHi); fg.addColorStop(1, palette.feltLo);
      ctx.fillStyle = fg;
      ctx.beginPath();
      ctx.ellipse(tx, ty, rx * fInner, ry * fInner, 0, 0, Math.PI * 2);
      ctx.fill();

      if (detail) {
        // Decorative stitch line just inside the felt edge.
        ctx.save();
        ctx.setLineDash([6, 7]);
        ctx.lineWidth = 1.2;
        ctx.strokeStyle = 'rgba(255,255,255,0.12)';
        ctx.beginPath();
        ctx.ellipse(tx, ty, rx * fInner * 0.94, ry * fInner * 0.94, 0, 0, Math.PI * 2);
        ctx.stroke();
        ctx.restore();

        // Gold betting line — oval arc on the felt.
        ctx.lineWidth = Math.max(2, rx * 0.01);
        ctx.strokeStyle = rgba('216,177,63', 0.5);
        ctx.beginPath();
        ctx.ellipse(tx, ty, rx * 0.6, ry * 0.6, 0, 0, Math.PI * 2);
        ctx.stroke();

        // Dealer chip tray at the front (player-facing) edge of the felt.
        drawDealerTray(tx, ty + ry * fInner * 0.74, rx * 0.32, ry * 0.13);
      }
      ctx.restore();
    }

    // Slotted dealer chip tray — a recessed oval with vertical chip dividers.
    function drawDealerTray(x, y, w, h) {
      ctx.save();
      ctx.fillStyle = 'rgba(0,0,0,0.45)';
      ctx.beginPath(); ctx.ellipse(x, y, w, h, 0, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = '#26262c';
      ctx.beginPath(); ctx.ellipse(x, y, w * 0.92, h * 0.78, 0, 0, Math.PI * 2); ctx.fill();
      ctx.strokeStyle = 'rgba(0,0,0,0.55)';
      ctx.lineWidth = 1.4;
      const slots = 5;
      for (let i = 0; i < slots; i++) {
        const sx = x + (i - (slots - 1) / 2) * (w * 1.5 / slots);
        const dy = h * 0.6 * Math.sqrt(Math.max(0, 1 - Math.pow((sx - x) / (w * 0.9), 2)));
        ctx.beginPath(); ctx.moveTo(sx, y - dy); ctx.lineTo(sx, y + dy); ctx.stroke();
      }
      ctx.restore();
    }

    // ── A small chip stack ──────────────────────────────────────────────────
    function drawChipStack(x, y, color, count, scale) {
      const w = 11 * scale, h = 4.2 * scale;
      for (let i = 0; i < count; i++) {
        const yy = y - i * (h * 0.95);
        ctx.beginPath();
        ctx.ellipse(x, yy, w, h, 0, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
        ctx.lineWidth = 1;
        ctx.strokeStyle = 'rgba(0,0,0,0.35)';
        ctx.stroke();
        // edge dashes
        ctx.strokeStyle = 'rgba(255,255,255,0.45)';
        ctx.beginPath(); ctx.moveTo(x - w, yy); ctx.lineTo(x - w * 0.7, yy); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(x + w * 0.7, yy); ctx.lineTo(x + w, yy); ctx.stroke();
      }
    }

    // ── Two face-down cards lying on the felt (shapes only, no text) ────────
    function drawCards(x, y, scale) {
      const cw = 26 * scale, ch = 36 * scale;
      [-0.18, 0.12].forEach((rot, i) => {
        ctx.save();
        ctx.translate(x + i * cw * 0.55, y);
        ctx.rotate(rot);
        // Card body.
        ctx.fillStyle = '#f4f1e8';
        ctx.strokeStyle = 'rgba(0,0,0,0.3)';
        roundRect(-cw / 2, -ch / 2, cw, ch, 3 * scale);
        ctx.fill(); ctx.stroke();
        // Patterned back: bordered panel + diagonal cross-hatch (shapes).
        ctx.fillStyle = palette.lose;
        roundRect(-cw / 2 + 2.5 * scale, -ch / 2 + 2.5 * scale, cw - 5 * scale, ch - 5 * scale, 2 * scale);
        ctx.fill();
        ctx.save();
        roundRect(-cw / 2 + 2.5 * scale, -ch / 2 + 2.5 * scale, cw - 5 * scale, ch - 5 * scale, 2 * scale);
        ctx.clip();
        ctx.strokeStyle = 'rgba(255,255,255,0.25)';
        ctx.lineWidth = 0.8;
        for (let d = -ch; d < ch; d += 4 * scale) {
          ctx.beginPath(); ctx.moveTo(-cw, d); ctx.lineTo(cw, d - cw); ctx.stroke();
          ctx.beginPath(); ctx.moveTo(-cw, d); ctx.lineTo(cw, d + cw); ctx.stroke();
        }
        ctx.restore();
        ctx.restore();
      });
    }

    function roundRect(x, y, w, h, r) {
      ctx.beginPath();
      ctx.moveTo(x + r, y);
      ctx.arcTo(x + w, y, x + w, y + h, r);
      ctx.arcTo(x + w, y + h, x, y + h, r);
      ctx.arcTo(x, y + h, x, y, r);
      ctx.arcTo(x, y, x + w, y, r);
      ctx.closePath();
    }

    // ── A pair of dice (pip dots are shapes, no numerals) ───────────────────
    function drawDice(x, y, sz, pips) {
      ctx.save();
      ctx.fillStyle = '#f0ece0';
      ctx.strokeStyle = 'rgba(0,0,0,0.35)';
      roundRect(x - sz / 2, y - sz / 2, sz, sz, sz * 0.2);
      ctx.fill(); ctx.stroke();
      ctx.fillStyle = '#1a1a1a';
      const q = sz * 0.26, r = sz * 0.09;
      const dot = (dx, dy) => { ctx.beginPath(); ctx.arc(x + dx, y + dy, r, 0, Math.PI * 2); ctx.fill(); };
      const P = {
        1: [[0, 0]], 2: [[-q, -q], [q, q]], 3: [[-q, -q], [0, 0], [q, q]],
        4: [[-q, -q], [q, -q], [-q, q], [q, q]],
        5: [[-q, -q], [q, -q], [0, 0], [-q, q], [q, q]],
        6: [[-q, -q], [q, -q], [-q, 0], [q, 0], [-q, q], [q, q]],
      };
      (P[pips] || P[5]).forEach(p => dot(p[0], p[1]));
      ctx.restore();
    }

    // ── A cocktail glass ─────────────────────────────────────────────────────
    function drawDrink(x, y, sc) {
      ctx.save();
      ctx.translate(x, y);
      ctx.lineWidth = 1.2 * sc;
      ctx.strokeStyle = 'rgba(220,235,255,0.55)';
      ctx.beginPath(); ctx.ellipse(0, 14 * sc, 7 * sc, 2.2 * sc, 0, 0, Math.PI * 2); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(0, 14 * sc); ctx.lineTo(0, 2 * sc); ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(-11 * sc, -12 * sc); ctx.lineTo(11 * sc, -12 * sc); ctx.lineTo(0, 2 * sc); ctx.closePath();
      ctx.fillStyle = 'rgba(120,210,170,0.35)';
      ctx.fill(); ctx.stroke();
      ctx.fillStyle = palette.lose;
      ctx.beginPath(); ctx.arc(3 * sc, -7 * sc, 2 * sc, 0, Math.PI * 2); ctx.fill();
      ctx.restore();
    }

    // ── A stacked deck of cards ──────────────────────────────────────────────
    function drawDeck(x, y, sc) {
      const cw = 22 * sc, ch = 30 * sc;
      for (let i = 4; i >= 0; i--) {
        ctx.fillStyle = '#ece8dc';
        ctx.strokeStyle = 'rgba(0,0,0,0.3)';
        roundRect(x - cw / 2 - i * 0.7 * sc, y - ch / 2 - i * 1.4 * sc, cw, ch, 2.4 * sc);
        ctx.fill(); ctx.stroke();
      }
      ctx.fillStyle = palette.lose;
      roundRect(x - cw / 2 + 2 * sc, y - ch / 2 + 2 * sc, cw - 4 * sc, ch - 4 * sc, 1.6 * sc);
      ctx.fill();
    }

    // Place a cluster of props at a seat. Deterministic (no per-frame random,
    // which would flicker).
    function placeProps(x, y, sc, kind) {
      switch (kind) {
        case 'chips':
          drawChipStack(x, y, palette.chipGreen, 4, sc);
          drawChipStack(x + 13 * sc, y + 3 * sc, palette.chipRed, 2, sc);
          break;
        case 'chips2':
          drawChipStack(x, y, palette.chipGold, 5, sc);
          drawChipStack(x + 12 * sc, y + 2 * sc, palette.chipGreen, 3, sc);
          drawChipStack(x - 11 * sc, y + 4 * sc, palette.chipRed, 2, sc);
          break;
        case 'chips+cards':
          drawChipStack(x, y, palette.chipGold, 4, sc);
          drawCards(x - 28 * sc, y + 5 * sc, sc * 0.9);
          break;
        case 'chips+dice':
          drawChipStack(x, y, palette.chipRed, 3, sc);
          drawDice(x + 17 * sc, y + 5 * sc, 11 * sc, 5);
          drawDice(x + 29 * sc, y + 9 * sc, 11 * sc, 2);
          break;
        case 'chips+drink':
          drawChipStack(x, y, palette.chipGreen, 4, sc);
          drawDrink(x - 22 * sc, y - 4 * sc, sc);
          break;
        case 'cards':
          drawCards(x, y, sc);
          drawChipStack(x + 24 * sc, y + 4 * sc, palette.chipGold, 2, sc);
          break;
        case 'deck':
          drawDeck(x, y, sc);
          drawChipStack(x + 22 * sc, y + 6 * sc, palette.chipGreen, 3, sc);
          break;
        case 'drink':
          drawDrink(x, y, sc);
          break;
      }
    }

    // Distribute prop clusters at seat positions around the whole table, scaled
    // by perspective (bigger toward the viewer). Near top/bottom we keep the
    // radius wide so props clear the central wheel; sides can sit closer in.
    function drawTableProps(tx, ty, rx, ry) {
      const seats = [
        { a: 0.15, fr: 0.70, kind: 'chips' },
        { a: 0.55, fr: 0.74, kind: 'cards' },
        { a: 0.95, fr: 0.84, kind: 'chips+dice' },
        { a: 1.30, fr: 0.86, kind: 'chips2' },
        { a: 1.57, fr: 0.88, kind: 'chips' },
        { a: 1.85, fr: 0.86, kind: 'chips+drink' },
        { a: 2.20, fr: 0.84, kind: 'chips' },
        { a: 2.60, fr: 0.74, kind: 'chips+cards' },
        { a: 3.00, fr: 0.70, kind: 'chips' },
        { a: 3.55, fr: 0.82, kind: 'deck' },
        { a: 5.85, fr: 0.82, kind: 'drink' },
        { a: 6.10, fr: 0.72, kind: 'chips' },
      ];
      for (const s of seats) {
        const px = tx + Math.cos(s.a) * rx * s.fr;
        const py = ty + Math.sin(s.a) * ry * s.fr;
        const norm = (py - (ty - ry)) / (2 * ry);   // 0 top → 1 bottom
        placeProps(px, py, 0.55 + 0.7 * norm, s.kind);
      }
    }

    // ── Slot-machine reel symbols (pure shapes, no text/numbers) ────────────
    function drawSymbol(x, y, s, type) {
      ctx.save();
      ctx.translate(x, y);
      switch (type) {
        case 0: // cherries
          ctx.strokeStyle = '#2f7a2f'; ctx.lineWidth = s * 0.06;
          ctx.beginPath(); ctx.moveTo(s * 0.1, -s * 0.4); ctx.quadraticCurveTo(s * 0.3, -s * 0.1, -s * 0.18, s * 0.12); ctx.stroke();
          ctx.beginPath(); ctx.moveTo(s * 0.1, -s * 0.4); ctx.quadraticCurveTo(-s * 0.1, -s * 0.05, s * 0.2, s * 0.16); ctx.stroke();
          ctx.fillStyle = '#e23030';
          ctx.beginPath(); ctx.arc(-s * 0.18, s * 0.22, s * 0.18, 0, Math.PI * 2); ctx.fill();
          ctx.beginPath(); ctx.arc(s * 0.22, s * 0.26, s * 0.18, 0, Math.PI * 2); ctx.fill();
          break;
        case 1: // lemon
          ctx.fillStyle = '#f2d23a';
          ctx.beginPath(); ctx.ellipse(0, 0, s * 0.34, s * 0.24, 0, 0, Math.PI * 2); ctx.fill();
          break;
        case 2: // diamond
          ctx.fillStyle = '#49d6ff';
          ctx.beginPath(); ctx.moveTo(0, -s * 0.34); ctx.lineTo(s * 0.26, 0); ctx.lineTo(0, s * 0.34); ctx.lineTo(-s * 0.26, 0); ctx.closePath(); ctx.fill();
          break;
        case 3: // bell
          ctx.fillStyle = '#f2c84b';
          ctx.beginPath();
          ctx.moveTo(-s * 0.26, s * 0.2);
          ctx.quadraticCurveTo(-s * 0.26, -s * 0.32, 0, -s * 0.32);
          ctx.quadraticCurveTo(s * 0.26, -s * 0.32, s * 0.26, s * 0.2);
          ctx.closePath(); ctx.fill();
          ctx.beginPath(); ctx.arc(0, s * 0.26, s * 0.08, 0, Math.PI * 2); ctx.fill();
          break;
        case 4: // bar (block)
          ctx.fillStyle = '#f4f1e8'; ctx.strokeStyle = '#1a1a1a'; ctx.lineWidth = s * 0.05;
          roundRect(-s * 0.3, -s * 0.16, s * 0.6, s * 0.32, s * 0.06); ctx.fill(); ctx.stroke();
          break;
        case 5: // star
          ctx.fillStyle = '#ffd24a'; ctx.beginPath();
          for (let k = 0; k < 5; k++) {
            const a1 = -Math.PI / 2 + k * 2 * Math.PI / 5, a2 = a1 + Math.PI / 5;
            ctx.lineTo(Math.cos(a1) * s * 0.34, Math.sin(a1) * s * 0.34);
            ctx.lineTo(Math.cos(a2) * s * 0.15, Math.sin(a2) * s * 0.15);
          }
          ctx.closePath(); ctx.fill();
          break;
        default: // clover/club
          ctx.fillStyle = '#3fd07a';
          ctx.beginPath(); ctx.arc(0, -s * 0.12, s * 0.15, 0, Math.PI * 2);
          ctx.arc(-s * 0.15, s * 0.08, s * 0.15, 0, Math.PI * 2);
          ctx.arc(s * 0.15, s * 0.08, s * 0.15, 0, Math.PI * 2); ctx.fill();
          ctx.fillRect(-s * 0.04, 0, s * 0.08, s * 0.26);
      }
      ctx.restore();
    }

    // ── A single slot machine, centred at (x,y) ─────────────────────────────
    function drawSlotMachine(x, y, w, m, t) {
      const h = w * 1.62;
      const top = y - h / 2, bottom = y + h / 2;
      const [lite, dark] = m.color;

      // Colour glow behind the cabinet.
      const gg = ctx.createRadialGradient(x, y, w * 0.1, x, y, w * 1.2);
      gg.addColorStop(0, hexA(lite, 0.22)); gg.addColorStop(1, hexA(lite, 0));
      ctx.fillStyle = gg; ctx.fillRect(x - w * 1.2, y - w * 1.2, w * 2.4, w * 2.4);

      // Floor contact shadow.
      ctx.fillStyle = 'rgba(0,0,0,0.4)';
      ctx.beginPath(); ctx.ellipse(x, bottom, w * 0.6, h * 0.05, 0, 0, Math.PI * 2); ctx.fill();

      // Base plinth.
      ctx.fillStyle = '#15100f';
      roundRect(x - w * 0.5, bottom - h * 0.14, w, h * 0.14, w * 0.05); ctx.fill();

      // Cabinet body.
      const bg = ctx.createLinearGradient(x - w * 0.5, 0, x + w * 0.5, 0);
      bg.addColorStop(0, dark); bg.addColorStop(0.5, lite); bg.addColorStop(1, dark);
      ctx.fillStyle = bg;
      roundRect(x - w * 0.46, top + h * 0.13, w * 0.92, h * 0.75, w * 0.08); ctx.fill();

      // Marquee header.
      ctx.fillStyle = dark;
      roundRect(x - w * 0.5, top, w, h * 0.16, w * 0.06); ctx.fill();
      // Candle light on top.
      ctx.fillStyle = (Math.floor(t / 600) % 2 === 0) ? '#ff5a5a' : '#7a1e1e';
      ctx.beginPath(); ctx.arc(x, top - h * 0.03, w * 0.05, 0, Math.PI * 2); ctx.fill();
      // Chasing marquee lights.
      const nL = Math.max(5, Math.round(w / 12));
      for (let i = 0; i < nL; i++) {
        const lx = x - w * 0.42 + (i / (nL - 1)) * w * 0.84;
        const on = ((Math.floor(t / 220) + i + m.lightOff) % 3) === 0;
        ctx.fillStyle = on ? '#fff0b0' : 'rgba(255,240,176,0.18)';
        ctx.beginPath(); ctx.arc(lx, top + h * 0.08, w * 0.025, 0, Math.PI * 2); ctx.fill();
      }

      // Reel window.
      const rwT = top + h * 0.2, rwH = h * 0.3, rwW = w * 0.78, rwX = x - rwW / 2;
      ctx.fillStyle = '#0a0a0c';
      roundRect(rwX, rwT, rwW, rwH, w * 0.03); ctx.fill();
      ctx.save();
      roundRect(rwX, rwT, rwW, rwH, w * 0.03); ctx.clip();
      const cycleN = Math.floor((t / 1000 + m.phase) / m.cycle);
      const local = (t / 1000 + m.phase) % m.cycle;
      const reelW = rwW / 3, sy = rwT + rwH / 2, ss = rwH * 0.6;
      for (let r = 0; r < 3; r++) {
        const rx = rwX + reelW * (r + 0.5);
        // subtle reel shading
        ctx.fillStyle = 'rgba(255,255,255,0.04)';
        ctx.fillRect(rwX + reelW * r + 1, rwT, reelW - 2, rwH);
        const reelStop = 0.5 + r * 0.45;
        if (local < reelStop) {
          // spinning: blur of cycling symbols scrolling upward
          const off = (local * 90) % ss;
          for (let k = -1; k <= 1; k++) {
            const sym = (Math.floor(local * 16) + r + k + 7) % 7;
            ctx.globalAlpha = 0.6 - Math.abs(k) * 0.2;
            drawSymbol(rx, sy + k * ss - off, ss, sym);
          }
          ctx.globalAlpha = 1;
        } else {
          drawSymbol(rx, sy, ss, (m.base[r] + cycleN) % 7);
        }
      }
      ctx.restore();
      // Reel window inner shadow + payline.
      ctx.strokeStyle = 'rgba(0,0,0,0.6)'; ctx.lineWidth = w * 0.02;
      roundRect(rwX, rwT, rwW, rwH, w * 0.03); ctx.stroke();
      ctx.strokeStyle = hexA(lite, 0.5); ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(rwX, sy); ctx.lineTo(rwX + rwW, sy); ctx.stroke();

      // Button deck.
      const bdY = rwT + rwH + h * 0.08;
      ctx.fillStyle = hexA(lite, 0.35);
      roundRect(x - w * 0.4, bdY, w * 0.8, h * 0.07, w * 0.03); ctx.fill();
      ['#ff5a5a', '#3fd07a', '#f2c84b'].forEach((bc, i) => {
        ctx.fillStyle = bc;
        ctx.beginPath(); ctx.arc(x - w * 0.22 + i * w * 0.22, bdY + h * 0.035, w * 0.04, 0, Math.PI * 2); ctx.fill();
      });

      // Coin tray.
      ctx.fillStyle = '#0c0a09';
      roundRect(x - w * 0.34, bottom - h * 0.11, w * 0.68, h * 0.05, w * 0.02); ctx.fill();

      // Lever on the outer side, with a slow pull when this machine spins.
      const leverX = m.side === 'L' ? x - w * 0.52 : x + w * 0.52;
      const pull = local < 0.5 ? Math.sin(local / 0.5 * Math.PI) * h * 0.06 : 0;
      ctx.strokeStyle = '#9aa0a6'; ctx.lineWidth = w * 0.035; ctx.lineCap = 'round';
      ctx.beginPath(); ctx.moveTo(leverX, rwT + rwH * 0.6); ctx.lineTo(leverX, rwT + pull); ctx.stroke();
      ctx.fillStyle = '#e23030';
      ctx.beginPath(); ctx.arc(leverX, rwT + pull - w * 0.02, w * 0.06, 0, Math.PI * 2); ctx.fill();
    }

    function drawSlots(t) {
      for (const m of slots) {
        const fySc = (m.fy - 0.34) / 0.56;          // 0 (far/up) → 1 (near/down)
        const w = (0.085 + 0.04 * fySc) * Math.min(W, H);
        drawSlotMachine(m.fx * W, m.fy * H, w, m, t);
      }
    }

    // ── Hanging spotlight cone over the central table ───────────────────────
    function drawSpotlight(t) {
      const breathe = 0.82 + 0.18 * Math.sin(t * 0.0007);
      const top = -H * 0.05;
      const g = ctx.createRadialGradient(cx, top, 10, cx, cy + H * 0.12, H * 0.85);
      g.addColorStop(0, rgba(palette.glow, 0.18 * breathe));
      g.addColorStop(0.4, rgba(palette.glow, 0.07 * breathe));
      g.addColorStop(1, rgba(palette.glow, 0));
      ctx.save();
      ctx.globalCompositeOperation = 'screen';
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, W, H);
      ctx.restore();
    }

    function drawMotes(t) {
      ctx.save();
      ctx.globalCompositeOperation = 'screen';
      for (const m of motes) {
        m.x += m.vx * 0.004; m.y += m.vy * 0.004;
        if (m.y < -0.02) { m.y = 1.02; m.x = Math.random(); }
        if (m.x < -0.02) m.x = 1.02; else if (m.x > 1.02) m.x = -0.02;
        const a = m.a * (0.55 + 0.45 * Math.sin(t * 0.001 * m.tw + m.ph));
        ctx.beginPath();
        ctx.arc(m.x * W, m.y * H, m.r, 0, Math.PI * 2);
        ctx.fillStyle = rgba(palette.glow, a);
        ctx.fill();
      }
      ctx.restore();
    }

    function drawVignette() {
      const g = ctx.createRadialGradient(cx, cy, Math.min(W, H) * 0.35, cx, cy, Math.max(W, H) * 0.72);
      g.addColorStop(0, 'rgba(0,0,0,0)');
      g.addColorStop(1, 'rgba(0,0,0,0.6)');
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, W, H);
    }

    function frame(now) {
      if (!running) return;
      const t = lowSpec ? 0 : now - start;
      ctx.clearRect(0, 0, W, H);

      drawRoom();
      drawSconces(t);

      // Slot machines lining the left and right walls (replaces the back
      // tables, which read as floating platforms).
      drawSlots(t);

      // Central poker table — the wheel composites on top of this.
      const mrx = Math.min(W * 0.34, H * 0.62);
      const mry = mrx * 0.46;
      drawTable(cx, cy, mrx, mry, 1, true);

      // A spread of casino props at seats all around the table.
      drawTableProps(cx, cy, mrx, mry);

      drawSpotlight(t);
      if (!lowSpec) drawMotes(t);
      drawVignette();

      // Animate only when not low-spec; low-spec paints a single static frame.
      if (!lowSpec) raf = requestAnimationFrame(frame);
    }

    resize();
    seedMotes();
    seedSlots();
    frame(performance.now());          // first paint (the only paint in low-spec)
    window.addEventListener('resize', resize);

    return {
      stop() {
        running = false;
        cancelAnimationFrame(raf);
        window.removeEventListener('resize', resize);
      },
    };
  }

  window.createCasinoScene = createCasinoScene;
})();
