const { useState, useRef, useEffect, useCallback, useMemo } = React;

// ── API helpers ───────────────────────────────────────────────────────────
async function apiFetch(path, opts = {}) {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  });
  const json = await res.json().catch(() => ({}));
  return { ok: res.ok, status: res.status, data: json };
}

let _onSessionExpired = null;
function setSessionExpiredHandler(fn) { _onSessionExpired = fn; }
function apiGame(path, opts = {}) {
  return apiFetch(path, opts).then(r => {
    if (r.status === 401 && _onSessionExpired) _onSessionExpired();
    return r;
  });
}

// ── Fire Effect ────────────────────────────────────────────────────────────
function makeParticle(w, h, maxHeight, intensity, scattered) {
  // scattered=true: spawn within visible fire zone for immediate appearance
  const y = scattered
    ? h - Math.random() * maxHeight
    : h - Math.random() * 8;
  const lifeUsed = scattered ? Math.random() * 60 : 0;
  return {
    x: Math.random() * w,
    y,
    vx: (Math.random() - 0.5) * 1.2,
    vy: -(1.5 + Math.random() * 4.0 * intensity + 0.5),
    size: 1.5 + Math.random() * 4.0 * intensity,
    life: lifeUsed,
    maxLife: 60 + Math.random() * 80,
    hue: 10 + Math.random() * 35,
    seed: Math.random() * 100,
  };
}

function initMode3(state, w, h, infInt = 0) {
  const bw = Math.max(1, Math.ceil(w / 4));
  const bh = Math.max(1, Math.ceil(h / 4));
  state.buf = new Uint8Array(bw * bh);
  state.bw  = bw;
  state.bh  = bh;
  const off = document.createElement('canvas');
  off.width  = bw;
  off.height = bh;
  state.offCanvas = off;
  state.offCtx    = off.getContext('2d');
  // only pre-warm if inferno has actually started
  if (infInt <= 0) return;
  const seedHeat = 60 + infInt * 195;
  const warmupSteps = Math.floor(30 + infInt * 60);
  for (let warmup = 0; warmup < warmupSteps; warmup++) {
    for (let i = 0; i < bw; i++) {
      const row = bh - 1 - Math.floor(Math.random() * 3);
      state.buf[row * bw + i] = Math.min(255, seedHeat * (0.7 + Math.random() * 0.6));
    }
    for (let y = 0; y < bh - 1; y++) {
      for (let x = 0; x < bw; x++) {
        const below = state.buf[(y + 1) * bw + x];
        const bl = x > 0      ? state.buf[(y + 1) * bw + (x - 1)] : below;
        const br = x < bw - 1 ? state.buf[(y + 1) * bw + (x + 1)] : below;
        const wl = 0.8 + Math.random() * 0.6;
        const wr = 0.8 + Math.random() * 0.6;
        const avg = (below * 1.2 + bl * wl + br * wr) / (1.2 + wl + wr);
        const warmCool = infInt > 0 ? Math.max(0.05, 255 / (bh * infInt) - 0.6) : 50;
        state.buf[y * bw + x] = Math.max(0, avg - (warmCool + Math.random() * 1.2));
      }
    }
  }
}

function FireEffect({ streak, mode, lowSpec }) {
  const animRef   = useRef(null);
  const stateRef  = useRef({});
  const targetRef = useRef({ intensity: 0, inferno: 0 });

  const intensity        = Math.min(Math.max(streak - 3, 0) / 47, 1);
  const infernoIntensity = Math.min(Math.max(streak - 10, 0) / 40, 1);
  const activeMode       = lowSpec ? 1 : mode;

  // Keep targets updated every render without restarting the effect
  targetRef.current.intensity = intensity;
  targetRef.current.inferno   = infernoIntensity;

  useEffect(() => {
    const canvas = document.createElement('canvas');
    canvas.style.cssText = [
      'position:fixed', 'inset:0', 'width:100vw', 'height:100vh',
      'z-index:1', 'pointer-events:none',
    ].join(';');
    const root = document.getElementById('root') || document.body;
    root.appendChild(canvas);
    const ctx = canvas.getContext('2d');

    function setSize() {
      canvas.width  = window.innerWidth;
      canvas.height = window.innerHeight;
      if (activeMode === 2 || activeMode === 3)
        initMode3(stateRef.current, canvas.width, canvas.height, targetRef.current.inferno);
    }
    setSize();
    window.addEventListener('resize', setSize);

    // Seed particles at current intensity so there's no startup flash
    const w = canvas.width, h = canvas.height;
    const initInt = targetRef.current.intensity;
    if (initInt > 0 && (activeMode === 1 || activeMode === 2)) {
      const maxH = h * (0.05 + initInt * 0.82);
      const count = lowSpec ? Math.floor(25 + initInt * 150) : Math.floor(50 + initInt * 350);
      stateRef.current.particles = Array.from({ length: count }, (_, i) =>
        makeParticle(w, h, maxH, initInt, i < count * 0.8)
      );
    }

    // Lerped display values — these change every frame, never trigger re-mounts
    let dispInt    = targetRef.current.intensity;
    let dispInfern = targetRef.current.inferno;

    let last = 0;
    const FRAME_MS = lowSpec ? 1000 / 24 : 1000 / 40;

    function tick(ts) {
      if (ts - last < FRAME_MS) { animRef.current = requestAnimationFrame(tick); return; }
      last = ts;

      // Lerp towards targets — faster falling (loss) than rising (win)
      const tgt = targetRef.current;
      const intSpeed    = dispInt    > tgt.intensity ? 0.10 : 0.06;
      const infSpeed    = dispInfern > tgt.inferno   ? 0.10 : 0.06;
      dispInt    += (tgt.intensity - dispInt)    * intSpeed;
      dispInfern += (tgt.inferno   - dispInfern) * infSpeed;
      if (Math.abs(dispInt    - tgt.intensity) < 0.001) dispInt    = tgt.intensity;
      if (Math.abs(dispInfern - tgt.inferno)   < 0.001) dispInfern = tgt.inferno;

      const cw = canvas.width, ch = canvas.height;
      ctx.clearRect(0, 0, cw, ch);
      if (dispInt > 0) {
        if (activeMode === 1) renderEmbers(ctx, cw, ch, dispInt, ts / 1000, stateRef.current);
        else if (activeMode === 2) renderMix(ctx, cw, ch, dispInt, dispInfern, ts / 1000, stateRef.current);
        else if (activeMode === 3) renderInferno(ctx, cw, ch, dispInfern, stateRef.current);
      }
      animRef.current = requestAnimationFrame(tick);
    }
    animRef.current = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(animRef.current);
      window.removeEventListener('resize', setSize);
      (document.getElementById('root') || document.body).removeChild(canvas);
    };
  }, [activeMode, lowSpec]); // intensity deliberately excluded — lerped inside tick

  return null;
}

// Mode 1: rising ember particles — spawn distributed immediately
function renderEmbers(ctx, w, h, intensity, t, state) {
  const maxHeight = h * (0.05 + intensity * 0.82);
  const count = Math.floor(50 + intensity * 350);
  const parts = state.particles;
  if (!parts) return;

  while (parts.length < count) parts.push(makeParticle(w, h, maxHeight, intensity, false));
  if (parts.length > count) parts.splice(count);

  for (let i = 0; i < parts.length; i++) {
    const p = parts[i];
    p.life++;
    p.x += p.vx + Math.sin(t * 2.2 + p.seed) * 0.6;
    p.y += p.vy;

    if (p.y < h - maxHeight || p.life > p.maxLife) {
      parts[i] = makeParticle(w, h, maxHeight, intensity, false);
      continue;
    }

    const age = p.life / p.maxLife;
    // glow: brightest and largest at the base, fading as it rises
    const riseFrac = Math.max(0, (h - p.y) / maxHeight); // 0=bottom, 1=top
    const size  = p.size * (1 - riseFrac * 0.5) * (1 - age * 0.4);
    const light = 50 + riseFrac * 30 + intensity * 15;
    const alpha = (1 - age * 0.7) * (0.75 + intensity * 0.25) * (1 - riseFrac * 0.5);

    ctx.globalAlpha = Math.min(alpha, 1);
    ctx.fillStyle = `hsl(${p.hue}, 100%, ${light}%)`;
    ctx.beginPath();
    ctx.arc(p.x, p.y, Math.max(0.5, size), 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.globalAlpha = 1;
}

// Mode 2: inferno base + ember overlay (combined)
function renderMix(ctx, w, h, intensity, infernoIntensity, t, state) {
  // --- inferno layer at reduced opacity ---
  if (state.buf && state.offCtx && infernoIntensity > 0) {
    stepInferno(state, infernoIntensity);
    const { bw, bh, buf, offCtx, offCanvas } = state;
    const imgData = offCtx.createImageData(bw, bh);
    const pix = imgData.data;
    for (let i = 0; i < bw * bh; i++) {
      const v = buf[i];
      if (v === 0) continue;
      let r, g, b, a;
      if      (v < 64)  { r = v * 4; g = 0;              b = 0;         a = v * 2; }
      else if (v < 128) { r = 255;   g = (v - 64) * 4;   b = 0;         a = 120 + (v - 64); }
      else if (v < 192) { r = 255;   g = 128+(v-128)*2;  b = 0;         a = 175; }
      else              { r = 255;   g = 200+(v-192);    b = (v-192)*3; a = 200; }
      pix[i*4] = r; pix[i*4+1] = g; pix[i*4+2] = b; pix[i*4+3] = a;
    }
    offCtx.putImageData(imgData, 0, 0);
    ctx.save();
    ctx.imageSmoothingEnabled = false;
    ctx.globalAlpha = 0.65;
    ctx.drawImage(offCanvas, 0, 0, bw, bh, 0, 0, w, h);
    ctx.restore();
  }

  // --- ember particles on top with additive blend ---
  ctx.globalCompositeOperation = 'lighter';
  const maxHeight = h * (0.05 + intensity * 0.82);
  const count = Math.floor(50 + intensity * 350);
  const parts = state.particles;
  if (parts) {
    while (parts.length < count) parts.push(makeParticle(w, h, maxHeight, intensity, false));
    if (parts.length > count) parts.splice(count);

    for (let i = 0; i < parts.length; i++) {
      const p = parts[i];
      p.life++;
      p.x += p.vx + Math.sin(t * 2.2 + p.seed) * 0.6;
      p.y += p.vy;
      if (p.y < h - maxHeight || p.life > p.maxLife) {
        parts[i] = makeParticle(w, h, maxHeight, intensity, false);
        continue;
      }
      const age      = p.life / p.maxLife;
      const riseFrac = Math.max(0, (h - p.y) / maxHeight);
      const size     = p.size * (1 - riseFrac * 0.4) * (1 - age * 0.4);
      const light    = 55 + riseFrac * 30 + intensity * 10;
      const alpha    = (1 - age * 0.65) * (0.7 + intensity * 0.3) * (1 - riseFrac * 0.4);
      ctx.globalAlpha = Math.min(alpha, 1);
      ctx.fillStyle = `hsl(${p.hue}, 100%, ${light}%)`;
      ctx.beginPath();
      ctx.arc(p.x, p.y, Math.max(0.5, size), 0, Math.PI * 2);
      ctx.fill();
    }
  }
  ctx.globalAlpha = 1;
  ctx.globalCompositeOperation = 'source-over';
}

// Shared inferno propagation step (used by both mode 2 and mode 3)
function stepInferno(state, infernoIntensity) {
  const { bw, bh, buf } = state;

  // Always keep the very bottom row at max heat — anchors fire to ground level
  for (let x = 0; x < bw; x++) {
    buf[(bh - 1) * bw + x] = 200 + Math.floor(Math.random() * 55);
  }

  // Additional heat sources scale from 0 for intensity-driven height
  const baseCount = Math.floor(bw * infernoIntensity);
  const sources   = Math.max(0, baseCount + Math.floor((Math.random() - 0.5) * baseCount * 0.8));
  const baseStr   = 60 + infernoIntensity * 195;
  for (let i = 0; i < sources; i++) {
    const x = Math.floor(Math.random() * bw);
    const row = bh - 1 - Math.floor(Math.random() * 3);
    const str = baseStr * (0.5 + Math.random() * 0.8);
    buf[row * bw + x] = Math.min(255, buf[row * bw + x] + str);
  }

  // Derive cooling so fire height is LINEAR in infernoIntensity:
  //   height_cells ≈ 255 / baseCool  →  baseCool = 255 / (bh * infernoIntensity)
  // Subtract noise average (0.6) so actual mean cooling lands on the target.
  const baseCool = infernoIntensity > 0
    ? Math.max(0.05, 255 / (2 * bh * infernoIntensity) - 0.6)
    : 50;
  for (let y = 0; y < bh - 1; y++) {
    for (let x = 0; x < bw; x++) {
      const below = buf[(y + 1) * bw + x];
      const bl    = x > 0      ? buf[(y + 1) * bw + (x - 1)] : below;
      const br    = x < bw - 1 ? buf[(y + 1) * bw + (x + 1)] : below;
      const wl = 0.8 + Math.random() * 0.6;
      const wr = 0.8 + Math.random() * 0.6;
      const avg = (below * 1.2 + bl * wl + br * wr) / (1.2 + wl + wr);
      const cooling = baseCool + Math.random() * 1.2;
      buf[y * bw + x] = Math.max(0, avg - cooling);
    }
  }
}

// Mode 3: cellular automaton fire (solo, full opacity)
function renderInferno(ctx, w, h, intensity, state) {
  if (!state.buf || !state.offCtx) return;
  const { bw, bh, buf, offCtx, offCanvas } = state;

  stepInferno(state, intensity);

  const imgData = offCtx.createImageData(bw, bh);
  const pix = imgData.data;
  for (let i = 0; i < bw * bh; i++) {
    const v = buf[i];
    if (v === 0) continue;
    let r, g, b, a;
    if      (v < 64)  { r = v * 4; g = 0;              b = 0;         a = v * 3; }
    else if (v < 128) { r = 255;   g = (v - 64) * 4;   b = 0;         a = 160 + (v - 64); }
    else if (v < 192) { r = 255;   g = 128+(v-128)*2;  b = 0;         a = 210; }
    else              { r = 255;   g = 200+(v-192);    b = (v-192)*4; a = 235; }
    pix[i*4] = r; pix[i*4+1] = g; pix[i*4+2] = b; pix[i*4+3] = a;
  }
  offCtx.putImageData(imgData, 0, 0);

  ctx.save();
  ctx.imageSmoothingEnabled = false;
  ctx.drawImage(offCanvas, 0, 0, bw, bh, 0, 0, w, h);
  ctx.restore();
}

// ── Draw main wheel ────────────────────────────────────────────────────────
function drawWheel(canvas, theme = 'default') {
  const ctx = canvas.getContext('2d');
  const size = canvas.width;
  const cx = size / 2, cy = size / 2, r = size / 2 - 4;

  ctx.clearRect(0, 0, size, size);

  const THEMES = {
    default: [
      { label: 'WIN',  color: '#005588', bright: '#00AAFF', start: -Math.PI/2, end: Math.PI/2 },
      { label: 'LOSE', color: '#7a3300', bright: '#FF6600', start: Math.PI/2,  end: Math.PI*1.5 },
    ],
    fire: [
      { label: 'WIN',  color: '#993300', bright: '#FF6600', start: -Math.PI/2, end: Math.PI/2 },
      { label: 'LOSE', color: '#440000', bright: '#CC2200', start: Math.PI/2,  end: Math.PI*1.5 },
    ],
    ice: [
      { label: 'WIN',  color: '#005577', bright: '#00CCFF', start: -Math.PI/2, end: Math.PI/2 },
      { label: 'LOSE', color: '#002244', bright: '#0066CC', start: Math.PI/2,  end: Math.PI*1.5 },
    ],
    neon: [
      { label: 'WIN',  color: '#440088', bright: '#CC00FF', start: -Math.PI/2, end: Math.PI/2 },
      { label: 'LOSE', color: '#003300', bright: '#00FF66', start: Math.PI/2,  end: Math.PI*1.5 },
    ],
    void: [
      { label: 'WIN',  color: '#0a0a1a', bright: '#6633FF', start: -Math.PI/2, end: Math.PI/2 },
      { label: 'LOSE', color: '#0d0010', bright: '#330066', start: Math.PI/2,  end: Math.PI*1.5 },
    ],
    gold: [
      { label: 'WIN',  color: '#7a5c00', bright: '#FFE566', start: -Math.PI/2, end: Math.PI/2 },
      { label: 'LOSE', color: '#3d2000', bright: '#CC8800', start: Math.PI/2,  end: Math.PI*1.5 },
    ],
  };
  const segments = THEMES[theme] || THEMES.default;

  segments.forEach(seg => {
    const grad = ctx.createRadialGradient(cx, cy, r * 0.1, cx, cy, r);
    grad.addColorStop(0, seg.bright);
    grad.addColorStop(1, seg.color);
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, r, seg.start, seg.end);
    ctx.closePath();
    ctx.fillStyle = grad;
    ctx.fill();

    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, r, seg.start, seg.end);
    ctx.closePath();
    ctx.strokeStyle = '#222';
    ctx.lineWidth = 3;
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(cx, cy);
    const mx = cx + r * Math.cos(seg.start);
    const my = cy + r * Math.sin(seg.start);
    ctx.lineTo(mx, my);
    ctx.strokeStyle = '#111';
    ctx.lineWidth = 4;
    ctx.stroke();

    const midAngle = (seg.start + seg.end) / 2;
    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(midAngle);
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.font = `bold ${size * 0.1}px 'Oswald', Arial Black, sans-serif`;
    ctx.fillStyle = '#FFF';
    ctx.shadowColor = 'rgba(0,0,0,0.8)';
    ctx.shadowBlur = 8;
    ctx.fillText(seg.label, r * 0.55, 0);
    ctx.restore();

    const dotCount = 8;
    for (let i = 0; i <= dotCount; i++) {
      const a = seg.start + (seg.end - seg.start) * (i / dotCount);
      const dr = r * 0.88;
      const dx = cx + dr * Math.cos(a);
      const dy = cy + dr * Math.sin(a);
      ctx.beginPath();
      ctx.arc(dx, dy, 5, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(255,255,255,0.5)';
      ctx.fill();
    }
  });

  ctx.beginPath();
  ctx.arc(cx, cy, r, 0, Math.PI * 2);
  ctx.strokeStyle = '#FFD700';
  ctx.lineWidth = 6;
  ctx.stroke();

  ctx.beginPath();
  ctx.arc(cx, cy, r * 0.12, 0, Math.PI * 2);
  ctx.fillStyle = '#111';
  ctx.fill();
}

// ── Draw guard mini-wheel ──────────────────────────────────────────────────
function drawGuardWheel(canvas) {
  const ctx = canvas.getContext('2d');
  const size = canvas.width;
  const cx = size / 2, cy = size / 2, r = size / 2 - 4;

  ctx.clearRect(0, 0, size, size);

  // WIN (50%): canvas angles centered at 0° (right side = 3 o'clock)
  // At CSS rotation 270° the right side is at 12 o'clock (pointer)
  const winHalf = Math.PI * 0.50; // ±90°
  const winStart = -winHalf;
  const winEnd   = winHalf;

  // FAIL segment (large)
  const gFail = ctx.createRadialGradient(cx, cy, r * 0.1, cx, cy, r);
  gFail.addColorStop(0, '#FF5555');
  gFail.addColorStop(1, '#770000');
  ctx.beginPath();
  ctx.moveTo(cx, cy);
  ctx.arc(cx, cy, r, winEnd, winStart + 2 * Math.PI);
  ctx.closePath();
  ctx.fillStyle = gFail;
  ctx.fill();

  // WIN segment (green, small)
  const gWin = ctx.createRadialGradient(cx, cy, r * 0.1, cx, cy, r);
  gWin.addColorStop(0, '#88DDFF');
  gWin.addColorStop(1, '#005588');
  ctx.beginPath();
  ctx.moveTo(cx, cy);
  ctx.arc(cx, cy, r, winStart, winEnd);
  ctx.closePath();
  ctx.fillStyle = gWin;
  ctx.fill();

  // Divider lines
  [winStart, winEnd].forEach(a => {
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(cx + r * Math.cos(a), cy + r * Math.sin(a));
    ctx.strokeStyle = '#111';
    ctx.lineWidth = 3;
    ctx.stroke();
  });

  // Border
  ctx.beginPath();
  ctx.arc(cx, cy, r, 0, 2 * Math.PI);
  ctx.strokeStyle = '#FFD700';
  ctx.lineWidth = 4;
  ctx.stroke();

  // Center hub
  ctx.beginPath();
  ctx.arc(cx, cy, r * 0.12, 0, 2 * Math.PI);
  ctx.fillStyle = '#111';
  ctx.fill();
}

// ── Number formatter ──────────────────────────────────────────────────────
function fmt(n) {
  if (n >= 1e15) return n.toExponential(2).replace('e+', 'e');
  if (n >= 1e12) return (n / 1e12).toFixed(n >= 10e12 ? 1 : 2).replace(/\.?0+$/, '') + 'T';
  if (n >= 1e9)  return (n / 1e9) .toFixed(n >= 10e9  ? 1 : 2).replace(/\.?0+$/, '') + 'B';
  if (n >= 1e6)  return (n / 1e6) .toFixed(n >= 10e6  ? 1 : 2).replace(/\.?0+$/, '') + 'M';
  if (n >= 1e3)  return (n / 1e3) .toFixed(n >= 10e3  ? 1 : 2).replace(/\.?0+$/, '') + 'K';
  return String(n);
}

// ── Scoreboard ────────────────────────────────────────────────────────────
const Scoreboard = React.memo(function Scoreboard({ wins, losses, lastResult }) {
  return (
    <div className="scoreboard">
      <div className="score-box wins-box">
        <span className="score-label">Wins</span>
        <span className={`score-value ${lastResult === 'win' ? 'score-bump' : ''}`} key={wins}>{fmt(wins)}</span>
      </div>
      <div className="score-box losses-box">
        <span className="score-label">Losses</span>
        <span className={`score-value ${lastResult === 'lose' ? 'score-bump' : ''}`} key={losses}>{fmt(losses)}</span>
      </div>
    </div>
  );
});

// ── Confetti ──────────────────────────────────────────────────────────────
const CONFETTI_COLORS = ['#FFD700','#FF6600','#FF3333','#00FF88','#00AAFF','#FF00FF','#FFFFFF'];
function Confetti({ active, count = 80 }) {
  const pieces = useMemo(() => {
    if (!active) return [];
    return Array.from({ length: count }, (_, i) => ({
      key: i,
      left:  Math.random() * 100,
      delay: Math.random() * 0.8,
      dur:   1.8 + Math.random() * 1.5,
      color: CONFETTI_COLORS[Math.floor(Math.random() * CONFETTI_COLORS.length)],
      size:  8 + Math.floor(Math.random() * 10),
      shape: Math.random() > 0.5 ? '50%' : '2px',
    }));
  }, [active, count]);

  return (
    <div className="confetti-container">
      {pieces.map(p => (
        <div key={p.key} className="confetti-piece" style={{
          left: `${p.left}%`, top: 0, width: p.size, height: p.size,
          background: p.color, borderRadius: p.shape,
          animationDuration: `${p.dur}s`, animationDelay: `${p.delay}s`,
        }} />
      ))}
    </div>
  );
}

// ── Guard Mini-Wheel ──────────────────────────────────────────────────────
function GuardWheel({ blocked, onComplete }) {
  const canvasRef = useRef(null);
  const [guardRotation, setGuardRotation] = useState(0);
  const [revealed, setRevealed] = useState(false);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (canvas) drawGuardWheel(canvas);

    // WIN segment centered at canvas angle 0° (right side).
    // CSS rotation 270° brings right side to 12 o'clock (pointer).
    // FAIL centered at canvas 180°; CSS rotation 90° brings it to pointer.
    const baseSpins = 4 * 360;
    const targetAngle = blocked ? 270 : 90;
    // Delay so browser paints rotation=0 before transitioning (otherwise no animation)
    const spinTimer     = setTimeout(() => setGuardRotation(baseSpins + targetAngle), 50);
    const revealTimer   = setTimeout(() => setRevealed(true), 2000);
    const completeTimer = setTimeout(() => onComplete(), 3400);
    return () => { clearTimeout(spinTimer); clearTimeout(revealTimer); clearTimeout(completeTimer); };
  }, []); // eslint-disable-line

  return (
    <div className="guard-overlay">
      <div className="guard-card">
        <div className="guard-title">🛡️ Guard Activating…</div>
        <div className="guard-wheel-wrap">
          <div className="guard-pointer-arrow" />
          <canvas
            ref={canvasRef}
            width={180}
            height={180}
            className="guard-canvas"
            style={{
              transform: `rotate(${guardRotation}deg)`,
              transition: `transform 1.8s cubic-bezier(0.17, 0.67, 0.12, 0.99)`,
            }}
          />
        </div>
        {revealed && (
          <div className={`guard-result ${blocked ? 'blocked' : 'failed'}`}>
            {blocked ? '🛡️ BLOCKED!' : '💔 Guard Failed'}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Fish ──────────────────────────────────────────────────────────────────
const Fish = React.memo(function Fish({ mood, net, fishClicks, onFishClick, fishData, sizeRem, trailClass, lowSpec }) {
  const [spinKey, setSpinKey] = useState(0);
  const [fishSpinning, setFishSpinning] = useState(false);
  const timerRef = useRef(null);
  const { emoji, labels } = fishData || DEFAULT_FISH;

  const handleClick = () => {
    if (timerRef.current) clearTimeout(timerRef.current);
    setFishSpinning(true);
    setSpinKey(k => k + 1);
    timerRef.current = setTimeout(() => setFishSpinning(false), 650);
    onFishClick();
  };

  const diff = Math.abs(net);
  const glowSize  = Math.min(8  + diff * 3, 80);
  const glowSize2 = Math.min(16 + diff * 6, 160);
  const glowOpacity = Math.min(0.5 + diff * 0.015, 1.0);
  const fishFilter = lowSpec ? 'none' : (net > 0
    ? `drop-shadow(0 0 ${glowSize}px rgba(255,140,0,${glowOpacity})) drop-shadow(0 0 ${glowSize2}px rgba(255,80,0,${glowOpacity * 0.6}))`
    : net < 0
    ? `drop-shadow(0 0 ${glowSize}px rgba(160,0,255,${glowOpacity})) drop-shadow(0 0 ${glowSize2}px rgba(80,0,180,${glowOpacity * 0.6}))`
    : 'drop-shadow(0 0 8px rgba(255,215,0,0.3))');
  const auraBlur    = Math.min(80 + diff * 12, 120);
  const auraOpacity = Math.min(0.3 + diff * 0.008, 0.88);
  const auraColor   = net > 0 ? 'rgba(255,130,0,0.9)' : 'rgba(150,0,255,0.9)';
  const auraStyle   = (!lowSpec && diff > 0) ? {
    background: auraColor,
    filter: `blur(${auraBlur}px)`,
    opacity: auraOpacity,
  } : null;
  const animClass = fishSpinning ? 'spinning-fish' : mood;

  return (
    <div className={`fish-panel ${trailClass || ''}`} onClick={handleClick} style={{ filter: fishFilter }} title="Wheeee!">
      {auraStyle && <div className="fish-aura" style={auraStyle} />}
      <span className={`fish-body ${animClass}`} key={spinKey || mood} style={{ fontSize: `${sizeRem}rem` }}>{emoji}</span>
      <span className={`fish-label ${mood}`}>{labels[mood]}</span>
    </div>
  );
});

// ── Streak Panel ──────────────────────────────────────────────────────────
const StreakPanel = React.memo(function StreakPanel({ streak }) {
  if (Math.abs(streak) < 2) return null;
  const isWin = streak > 0;
  const count = Math.abs(streak);
  const bonus = count >= 3 ? Math.pow(2, count - 3) : 0;
  return (
    <div className={`streak-panel ${isWin ? 'win-streak' : 'lose-streak'}`}>
      <span className="streak-fire">{isWin ? '🔥' : '💀'}</span>
      <span className="streak-count">{count}x</span>
      <span className="streak-label">{isWin ? 'Win Streak' : 'Lose Streak'}</span>
      {bonus > 0 && (
        <span className="streak-bonus">
          {isWin ? `Bonus +${fmt(bonus)}` : `Penalty +${fmt(bonus)}`}
        </span>
      )}
    </div>
  );
});

// ── Season Winners ────────────────────────────────────────────────────────
function SeasonWinners({ winners, seasonNumber }) {
  if (!winners || winners.length === 0) return null;
  const medals = ['🥇', '🥈', '🥉'];
  const rankClasses = ['sw-gold', 'sw-silver', 'sw-bronze', 'sw-4th', 'sw-5th'];
  return (
    <div className="season-winners">
      <div className="season-winners-title">Season {seasonNumber} Winners</div>
      {winners.map(w => (
        <div key={w.position} className={`season-winner-row ${rankClasses[w.position - 1] || ''}`}>
          <span className="sw-medal">{medals[w.position - 1] || w.position}</span>
          <span className="sw-name">{w.username}</span>
          <span className="sw-wins">{fmt(w.wins)}W</span>
        </div>
      ))}
    </div>
  );
}

// ── Season Info ───────────────────────────────────────────────────────────
function SeasonInfo({ seasonNumber, endsAt }) {
  const [timeLeft, setTimeLeft] = useState('');

  useEffect(() => {
    if (!endsAt) return;
    const update = () => {
      const diff = new Date(endsAt) - new Date();
      if (diff <= 0) { setTimeLeft('Ending...'); return; }
      const d = Math.floor(diff / 86400000);
      const h = Math.floor((diff % 86400000) / 3600000);
      const m = Math.floor((diff % 3600000) / 60000);
      setTimeLeft(d > 0 ? `${d}d ${h}h ${m}m` : h > 0 ? `${h}h ${m}m` : `${m}m`);
    };
    update();
    const id = setInterval(update, 60000);
    return () => clearInterval(id);
  }, [endsAt]);

  return (
    <div className="season-info">
      <span>Season {seasonNumber} ends:</span>
      {timeLeft && <span className="season-countdown">{timeLeft}</span>}
    </div>
  );
}

// ── Leaderboard ───────────────────────────────────────────────────────────
function Leaderboard({ currentUser }) {
  const [rows, setRows] = useState([]);

  useEffect(() => {
    let ctrl = new AbortController();
    const load = () => {
      ctrl.abort();
      ctrl = new AbortController();
      apiFetch('/api/leaderboard', { signal: ctrl.signal })
        .then(r => { if (r.ok) setRows(r.data); })
        .catch(() => {});
    };
    load();
    const id = setInterval(load, 5000);
    return () => { clearInterval(id); ctrl.abort(); };
  }, []);

  if (rows.length === 0) return null;

  const rankClass = i => i === 0 ? 'gold' : i === 1 ? 'silver' : i === 2 ? 'bronze' : '';
  const infernoClass = streak => streak > 0 ? `streak-inferno-${Math.min(streak, 10)}` : '';

  return (
    <div className="leaderboard-panel">
      <div className="leaderboard-panel-title">🏆 Top Players</div>
      <div className="lb-header">
        <span className="lb-rank-h"></span>
        <span className="lb-name-h">Player</span>
        <span className="lb-wins-h">W</span>
        <span className="lb-best-h">Best</span>
        <span className="lb-streak-h">Now</span>
      </div>
      {rows.map((r, i) => (
        <div key={r.username} className="lb-row">
          <span className={`lb-rank ${rankClass(i)}`}>{i + 1}.</span>
          <span className={`lb-name ${r.username === currentUser ? 'is-you' : ''}`}>{r.username}</span>
          <span className="lb-wins">{fmt(r.wins)}</span>
          <span className="lb-best">{r.best_streak > 0 ? `${r.best_streak}🔥` : '—'}</span>
          <span className={`lb-streak ${infernoClass(r.streak)}`}>
            {r.streak > 0 ? `${r.streak}🔥` : r.streak < 0 ? `${r.streak}💀` : '0'}
          </span>
        </div>
      ))}
    </div>
  );
}

// ── Shop catalogue ────────────────────────────────────────────────────────
const FISH_SKINS = [
  { id: 'fish_tropical', emoji: '🐠', name: 'Tropical Fish', cost: 25,
    labels: { idle: 'Blub blub!', happy: 'Splashy win!', sad: 'Glub...' } },
  { id: 'fish_puffer',   emoji: '🐡', name: 'Pufferfish',    cost: 50,
    labels: { idle: '*puffs up*', happy: 'PUFF YEAH!', sad: '*deflates*' } },
  { id: 'fish_octopus',  emoji: '🐙', name: 'Octopus',       cost: 75,
    labels: { idle: '8 arms ready!', happy: 'Ink-redible!', sad: '*squirts ink*' } },
  { id: 'fish_shark',    emoji: '🦈', name: 'Shark',         cost: 100,
    labels: { idle: 'Chomp chomp', happy: 'Feeding frenzy!', sad: 'Jaw dropped...' } },
  { id: 'fish_dolphin',  emoji: '🐬', name: 'Dolphin',       cost: 150,
    labels: { idle: 'Eee-eee!', happy: "Flippin' awesome!", sad: '*sad clicks*' } },
  { id: 'fish_squid',    emoji: '🦑', name: 'Squid',         cost: 200,
    labels: { idle: 'Ink at the ready', happy: 'Jet-propelled win!', sad: '*squirts ink cloud*' } },
  { id: 'fish_turtle',   emoji: '🐢', name: 'Turtle',        cost: 350,
    labels: { idle: 'Slow and steady', happy: 'Shell yeah!', sad: 'Into my shell...' } },
  { id: 'fish_crab',     emoji: '🦀', name: 'Crab',          cost: 600,
    labels: { idle: '*snaps claws*', happy: 'CRABULOUS!', sad: 'Crabby mood...' } },
  { id: 'fish_lobster',  emoji: '🦞', name: 'Lobster',       cost: 1000,
    labels: { idle: 'Feeling boujee', happy: 'CLAWSOME WIN!', sad: 'Shellshocked...' } },
  { id: 'fish_whale',    emoji: '🐋', name: 'Whale',         cost: 2000,
    labels: { idle: 'Making waves', happy: 'WHALE of a win!', sad: 'Beached...' } },
];

const SHOP_SECTIONS = [
  { label: '⚡ Spin Speed', items: [
    { id: 'speed_boost', emoji: '⚡', name: 'Speed Boost',  cost: 50,   desc: 'Spin time: 4.5s → 3s' },
    { id: 'turbo_spin',  emoji: '🚀', name: 'Turbo Spin',   cost: 200,  desc: 'Spin time: 3s → 1.5s',  requires: 'speed_boost' },
    { id: 'hyperspin',   emoji: '💨', name: 'Hyper Spin',   cost: 600,  desc: 'Spin time: 1.5s → 1s',  requires: 'turbo_spin' },
    { id: 'ultraspin',   emoji: '🌀', name: 'Ultra Spin',   cost: 2000, desc: 'Spin time: 1s → 0.75s', requires: 'hyperspin' },
    { id: 'maxspin',     emoji: '⚡', name: 'Max Spin',     cost: 6000, desc: 'Spin time: 0.75s → 0.5s',requires: 'ultraspin' },
  ]},
  { label: '⏩ Auto Speed', items: [
    { id: 'autospeed_1', emoji: '⏩', name: 'Quick Auto',   cost: 75,   desc: 'Auto delay: 1.5s → 1s' },
    { id: 'autospeed_2', emoji: '⏩', name: 'Rapid Auto',   cost: 300,  desc: 'Auto delay: 1s → 0.5s',  requires: 'autospeed_1' },
    { id: 'autospeed_3', emoji: '⏩', name: 'Instant Auto', cost: 1200, desc: 'Auto delay: 0.5s → 0',   requires: 'autospeed_2' },
  ]},
  { label: '💰 Win Power', items: [
    { id: 'winmult_inf', emoji: '💰', name: 'Win Power', cost: 0, desc: 'Multiplies each win score', infinite: true },
  ]},
  { label: '⭐ Bonus Power', items: [
    { id: 'bonusmult_inf', emoji: '⭐', name: 'Bonus Power', cost: 0, desc: 'Multiplies streak bonuses — ⚠️ also amplifies loss streaks', infinite: true },
  ]},
  { label: '🐟 Fish Size', items: [
    { id: 'fishsize_1',  emoji: '🔎', name: 'Big Fish',     cost: 50,   desc: 'Fish size: XL (20rem)' },
    { id: 'fishsize_2',  emoji: '🔎', name: 'Giant Fish',   cost: 200,  desc: 'Fish size: XXL (28rem)', requires: 'fishsize_1' },
    { id: 'fishsize_3',  emoji: '🔎', name: 'Colossal',     cost: 800,  desc: 'Fish size: MEGA (40rem)',requires: 'fishsize_2' },
  ]},
  { label: '✨ Fish Trail', items: [
    { id: 'trail_1',     emoji: '✨', name: 'Sparkle Trail', cost: 125,   desc: 'Gold shimmer trail' },
    { id: 'trail_2',     emoji: '🔥', name: 'Fire Trail',    cost: 500,   desc: 'Flame glow trail',       requires: 'trail_1' },
    { id: 'trail_3',     emoji: '🌈', name: 'Rainbow Trail', cost: 2000,  desc: 'Rainbow hue trail',      requires: 'trail_2' },
    { id: 'trail_4',     emoji: '❄️', name: 'Frost Trail',   cost: 7000,  desc: 'Ice crystal aura',       requires: 'trail_3' },
    { id: 'trail_5',     emoji: '⚡', name: 'Thunder Trail', cost: 22000, desc: 'Electric storm aura',    requires: 'trail_4' },
    { id: 'trail_6',     emoji: '🌌', name: 'Galaxy Trail',  cost: 70000, desc: 'Cosmic void aura',       requires: 'trail_5' },
  ]},
  { label: '🖱️ Click Power', items: [
    { id: 'clickmult_inf', emoji: '👆', name: 'Click Power', cost: 0, desc: 'Multiplies fish clicks per tap (also scales frenzy)', infinite: true },
    { id: 'clickfrenzy_1',  emoji: '🖱️', name: 'Frenzy I',    cost: 150,  desc: '+1 passive click/5s (scales with click upgrades)' },
    { id: 'clickfrenzy_2',  emoji: '🖱️', name: 'Frenzy II',   cost: 600,  desc: '+5 passive clicks/5s (scales with click upgrades)',  requires: 'clickfrenzy_1' },
    { id: 'clickfrenzy_3',  emoji: '🖱️', name: 'Frenzy III',  cost: 2400, desc: '+20 passive clicks/5s (scales with click upgrades)', requires: 'clickfrenzy_2' },
    { id: 'clickfrenzy_4',  emoji: '🌪️', name: 'Frenzy IV',   cost: 9600, desc: '+50 passive clicks/5s (scales with click upgrades)', requires: 'clickfrenzy_3' },
    { id: 'clickfrenzy_5',  emoji: '⚡', name: 'Frenzy V',    cost: 38400, desc: '+100 passive clicks/5s (scales with click upgrades)', requires: 'clickfrenzy_4' },
    { id: 'final_frenzy',   emoji: '🌀', name: 'Final Frenzy', cost: 100000, desc: '500 passive clicks/5s (scales with click upgrades) — manual clicking disabled. Toggle to switch back to Frenzy V.', requires: 'clickfrenzy_5' },
  ]},
  { label: '🛡️ Protection', items: [
    { id: 'guard',       emoji: '🛡️', name: 'Guard',              cost: 300,   desc: '50% chance to block any loss. Breaks on success, survives on failure.' },
    { id: 'auto_guard',  emoji: '🔁', name: 'Auto-Guard',         cost: 10000, desc: 'Automatically re-buys a Guard for 500 fish clicks when one breaks. Toggle to enable/disable.', requires: 'guard' },
    { id: 'regen_shield',emoji: '🔄', name: 'Regenerating Shield', cost: 800,  desc: 'Blocks any loss when charged. Recharges after 5 wins. Never breaks.' },
  ]},
  { label: '🎡 Wheel Theme', items: [
    { id: 'theme_fire',  emoji: '🔥', name: 'Fire Theme',    cost: 250,   desc: 'Infernal wheel colors' },
    { id: 'theme_ice',   emoji: '❄️', name: 'Ice Theme',     cost: 1000,  desc: 'Glacial wheel colors',    requires: 'theme_fire' },
    { id: 'theme_neon',  emoji: '🟣', name: 'Neon Theme',    cost: 4000,  desc: 'Cyberpunk wheel colors',  requires: 'theme_ice' },
    { id: 'theme_void',  emoji: '🌑', name: 'Void Theme',    cost: 12000, desc: 'Dark matter wheel',       requires: 'theme_neon' },
    { id: 'theme_gold',  emoji: '🟡', name: 'Gold Theme',    cost: 40000, desc: 'Pure gold wheel',         requires: 'theme_void' },
    { id: 'golden_wheel',emoji: '✨', name: 'Golden Wheel',  cost: 300,   desc: 'Radiant glow ring' },
  ]},
  { label: '🎊 Confetti', items: [
    { id: 'party_mode',  emoji: '🎉', name: 'Party Mode',    cost: 150,  desc: 'Confetti every spin' },
    { id: 'confetti_1',  emoji: '🎊', name: 'Confetti+',     cost: 75,   desc: '2x confetti pieces' },
    { id: 'confetti_2',  emoji: '🎊', name: 'Confetti++',    cost: 300,  desc: '5x confetti pieces',      requires: 'confetti_1' },
    { id: 'confetti_3',  emoji: '🎊', name: 'Confetti MAX',  cost: 1200, desc: '15x confetti pieces',     requires: 'confetti_2' },
  ]},
  { label: '🎨 Atmosphere', items: [
    { id: 'bg_ocean',    emoji: '🌊', name: 'Ocean Casino',    cost: 100,   desc: 'Deep blue atmosphere' },
    { id: 'bg_royal',    emoji: '💜', name: 'Royal Casino',    cost: 400,   desc: 'Purple atmosphere',       requires: 'bg_ocean' },
    { id: 'bg_inferno',  emoji: '❤️', name: 'Inferno Casino',  cost: 1600,  desc: 'Blood red atmosphere',    requires: 'bg_royal' },
    { id: 'bg_forest',   emoji: '🌿', name: 'Enchanted Forest',cost: 5000,  desc: 'Mystical green depths',   requires: 'bg_inferno' },
    { id: 'bg_abyss',    emoji: '🌑', name: 'The Abyss',       cost: 15000, desc: 'Void of darkness',        requires: 'bg_forest' },
    { id: 'bg_cosmic',   emoji: '🌌', name: 'Cosmic Casino',   cost: 50000, desc: 'Deep space nebula',       requires: 'bg_abyss' },
  ]},
  { label: '🖼️ Page Theme', items: [
    { id: 'page_season1', emoji: '🌟', name: 'Season 1 Theme', cost: 1000, desc: 'Classic gold & orange casino theme (S1).' },
    { id: 'page_season2', emoji: '🟢', name: 'Season 2 Theme', cost: 1000, desc: 'Green & red casino theme (S2).' },
  ]},
  { label: '🎲 Special Upgrades', items: [
    { id: 'fortune_charm', emoji: '🍀', name: 'Fortune Charm',  cost: 500,  desc: '25% chance: +25% to streak bonus payout' },
    { id: 'lucky_seven',   emoji: '7️⃣', name: 'Lucky Seven',    cost: 1000, desc: 'Every 7th spin is guaranteed a win' },
    { id: 'win_echo',      emoji: '🔊', name: 'Win Echo',        cost: 750,  desc: '20% chance to double wins earned on any win' },
    { id: 'resilience',    emoji: '💪', name: 'Resilience',      cost: 500000, desc: '50% chance: on win streak, a loss only drops streak by 1 instead of resetting' },
    { id: 'jackpot',       emoji: '🎰', name: 'Jackpot',         cost: 3000, desc: '1% chance each win to multiply gains by 50x' },
  ]},
  { label: '🌌 Legendary', items: [
    { id: 'singularity', emoji: '🌌', name: 'The Singularity', cost: 1000000000,
      desc: 'Transcend reality itself. Every spin is a win.' },
  ]},
];

// Infinite upgrade config (mirrors INFINITE_UPGRADES in models.py)
const INF_UPGRADE_CFG = {
  winmult_inf:   { tierCosts: [200, 800, 3200, 12800, 51200, 204800, 819200], infBase: 1_000_000, infScale: 1.4 },
  bonusmult_inf: { tierCosts: [300, 1200, 4800, 20000, 80000, 300000],        infBase: 500_000,   infScale: 1.4 },
  clickmult_inf: { tierCosts: [100, 400, 900, 2000, 4500],                    infBase: 10_000,    infScale: 1.5 },
};
function infCost(id, level) {
  const { tierCosts, infBase, infScale } = INF_UPGRADE_CFG[id];
  if (level < tierCosts.length) return tierCosts[level];
  return Math.floor(infBase * Math.pow(infScale, level - tierCosts.length));
}
function infMultiplier(id, level) {
  if (id === 'winmult_inf') {
    if (level <= 0) return 1;
    if (level <= 7) return Math.pow(2, level);
    return 128 + (level - 7) * 16;
  }
  if (id === 'bonusmult_inf') {
    const fixed = [1, 2, 5, 10, 20, 50, 100];
    if (level <= 6) return fixed[level];
    return 100 + (level - 6) * 10;
  }
  if (id === 'clickmult_inf') return level <= 0 ? 1 : level + 1;
  return 1;
}

const DEFAULT_FISH = { emoji: '🐟', labels: { idle: 'Click me!', happy: '🎉 Nice!', sad: '💀 Ouch!' } };

function getFishData(equippedFish) {
  return FISH_SKINS.find(s => s.id === equippedFish) || DEFAULT_FISH;
}

const COSMETIC_SECTION_IDS = new Set([
  'bg_ocean','bg_royal','bg_inferno','bg_forest','bg_abyss','bg_cosmic',
  'fishsize_1','fishsize_2','fishsize_3',
  'confetti_1','confetti_2','confetti_3',
  'party_mode',
  'trail_1','trail_2','trail_3','trail_4','trail_5','trail_6',
  'theme_fire','theme_ice','theme_neon','theme_void','theme_gold',
  'golden_wheel',
  'page_season1', 'page_season2',
  'final_frenzy',
  'auto_guard',
]);

// Season 3: currency classification (mirrors ITEM_CURRENCY in models.py)
const COSMETIC_IDS = new Set([
  'fish_tropical','fish_puffer','fish_octopus','fish_shark','fish_dolphin',
  'fish_squid','fish_turtle','fish_crab','fish_lobster','fish_whale',
  'fishsize_1','fishsize_2','fishsize_3',
  'trail_1','trail_2','trail_3','trail_4','trail_5','trail_6',
  'theme_fire','theme_ice','theme_neon','theme_void','theme_gold','golden_wheel',
  'page_season1','page_season2','party_mode','confetti_1','confetti_2','confetti_3',
  'bg_ocean','bg_royal','bg_inferno','bg_forest','bg_abyss','bg_cosmic',
]);
const getItemCurrency = id => id === 'singularity' ? 'fish_clicks' : COSMETIC_IDS.has(id) ? 'losses' : 'wins';
const currencyIcon = c => c === 'wins' ? '🏆' : c === 'losses' ? '💀' : '🐟';

// ── Shop components ────────────────────────────────────────────────────────
const ShopItem = React.memo(function ShopItem({ item, owned, equipped, active, canAfford, onBuy, onEquip, onEquipCosmetic, isSkin, isSingularity, isCosmetic, infLevel, displayCost }) {
  const isInfinite = !!item.infinite;
  const cost = isInfinite ? displayCost : item.cost;

  let actionEl;
  if (isInfinite) {
    actionEl = (
      <button
        className={`shop-buy-btn ${canAfford ? 'can-afford' : 'cant-afford'}`}
        onClick={() => canAfford && onBuy(item.id, cost)}
      >Buy</button>
    );
  } else if (owned && isSkin) {
    actionEl = equipped
      ? <span className="shop-equipped-badge">✓ On</span>
      : <button className="shop-equip-btn" onClick={() => onEquip(item.id)}>Equip</button>;
  } else if (owned && isCosmetic) {
    actionEl = active
      ? <button className="shop-equip-btn active-cosmetic" onClick={() => onEquipCosmetic(item.id)}>Active</button>
      : <button className="shop-equip-btn" onClick={() => onEquipCosmetic(item.id)}>Equip</button>;
  } else if (owned) {
    actionEl = <span className="shop-active-badge">Active</span>;
  } else {
    actionEl = (
      <button
        className={`shop-buy-btn ${canAfford ? 'can-afford' : 'cant-afford'}`}
        onClick={() => canAfford && onBuy(item.id, cost)}
      >Buy</button>
    );
  }
  const extraClass = isSingularity && !owned ? 'singularity-item' : '';
  const infDesc = isInfinite && infLevel != null
    ? (() => {
        const cur = infMultiplier(item.id, infLevel);
        const nxt = infMultiplier(item.id, infLevel + 1);
        return `Lv${infLevel} · x${cur} → x${nxt}  ${item.desc}`;
      })()
    : item.desc;
  return (
    <div className={`shop-item ${!isInfinite && owned ? (equipped || active ? 'equipped' : 'owned') : ''} ${extraClass}`}>
      <span className="shop-item-emoji">{item.emoji}</span>
      <div className="shop-item-info">
        <div className="shop-item-name">{item.name}</div>
        {infDesc && <div className="shop-item-desc" data-tooltip={infDesc}>{infDesc}</div>}
        <div className={`shop-item-cost cost-${getItemCurrency(item.id)}`}>{currencyIcon(getItemCurrency(item.id))} {cost.toLocaleString()}</div>
      </div>
      <div className="shop-item-action">{actionEl}</div>
    </div>
  );
});

const COSMETIC_SECTION_LABELS = new Set(['🐟 Fish Size', '✨ Fish Trail', '🎡 Wheel Theme', '🎊 Confetti', '🎨 Atmosphere', '🖼️ Page Theme']);

function ShopPanel({ fishClicks, wins, losses, ownedItems, equippedFish, activeCosmetics, infLevels, onBuy, onEquip, onEquipCosmetic, collapsed }) {
  const [activeTab, setActiveTab] = useState('functional');

  const { cosmeticSections, functionalSections } = useMemo(() => {
    const cosmetic = [], functional = [];
    SHOP_SECTIONS.forEach(section => {
      const isCosmeticSection = COSMETIC_SECTION_LABELS.has(section.label);
      const visibleItems = section.items.filter(item => {
        const requiresMet = !item.requires || ownedItems.includes(item.requires);
        if (isCosmeticSection) return requiresMet;
        if (item.infinite) return requiresMet; // infinite items always visible once prereq met
        const isOwned = ownedItems.includes(item.id);
        if (!isOwned) return requiresMet; // next tier to buy
        // Owned: show only if this is the latest owned in its chain
        const nextInChain = section.items.find(other => other.requires === item.id && !other.infinite && !COSMETIC_SECTION_IDS.has(other.id));
        return !nextInChain || !ownedItems.includes(nextInChain.id);
      });
      if (visibleItems.length === 0) return;
      (COSMETIC_SECTION_LABELS.has(section.label) ? cosmetic : functional).push({ ...section, visibleItems });
    });
    return { cosmeticSections: cosmetic, functionalSections: functional };
  }, [ownedItems]);

  const renderSection = (section) => (
    <React.Fragment key={section.label}>
      <div className="shop-section-label">── {section.label} ──</div>
      {section.visibleItems.map(item => {
        const isCosmetic = COSMETIC_SECTION_IDS.has(item.id);
        const infLevel = item.infinite ? (infLevels[item.id] || 0) : null;
        const displayCost = item.infinite ? infCost(item.id, infLevel) : item.cost;
        const currency = getItemCurrency(item.id);
        const balance = currency === 'wins' ? wins : currency === 'losses' ? losses : fishClicks;
        return (
          <ShopItem key={item.id} item={item}
            isSkin={false}
            isSingularity={item.id === 'singularity'}
            isCosmetic={isCosmetic}
            owned={!item.infinite && ownedItems.includes(item.id)}
            equipped={false}
            active={isCosmetic && activeCosmetics.includes(item.id)}
            canAfford={balance >= displayCost}
            infLevel={infLevel}
            displayCost={displayCost}
            onBuy={onBuy} onEquip={onEquip} onEquipCosmetic={onEquipCosmetic}
          />
        );
      })}
    </React.Fragment>
  );

  return (
    <div className={`shop-panel${collapsed ? ' shop-panel--collapsed' : ''}`}>
      <div className="shop-header">
        <div className="shop-title">🛒 Shop</div>
        <div className="shop-balance">
          <span className="balance-wins">🏆 {fmt(wins)}</span>
          <span className="balance-losses">💀 {fmt(losses)}</span>
          <span className="balance-clicks">🐟 {fmt(fishClicks)}</span>
        </div>
      </div>
      <div className="shop-tabs">
        <button className={`shop-tab ${activeTab === 'functional' ? 'active' : ''}`} onClick={() => setActiveTab('functional')}>⚡ Functional</button>
        <button className={`shop-tab shop-tab--cosmetic ${activeTab === 'cosmetic' ? 'active' : ''}`} onClick={() => setActiveTab('cosmetic')}>🎨 Cosmetic</button>
      </div>
      <div className={`shop-tab-content${activeTab === 'cosmetic' ? ' shop-tab-content--cosmetic' : ''}`}>
        {activeTab === 'cosmetic' ? (
          <>
            <div className="shop-section-label">── Fish Skins ──</div>
            {FISH_SKINS.map(item => (
              <ShopItem key={item.id} item={item} isSkin
                owned={ownedItems.includes(item.id)}
                equipped={equippedFish === item.id}
                canAfford={losses >= item.cost}
                onBuy={onBuy} onEquip={onEquip} onEquipCosmetic={onEquipCosmetic}
              />
            ))}
            {cosmeticSections.map(renderSection)}
          </>
        ) : (
          functionalSections.map(renderSection)
        )}
      </div>
    </div>
  );
}

// ── Stats Panel ────────────────────────────────────────────────────────────
const PLACE_LABEL = pos =>
  pos === 1 ? '🥇 1st' : pos === 2 ? '🥈 2nd' : pos === 3 ? '🥉 3rd' : null;

function StatsPanel({ open, onClose }) {
  const [stats, setStats] = useState(null);
  useEffect(() => {
    if (!open) return;
    apiFetch('/api/stats').then(r => { if (r.ok) setStats(r.data); });
  }, [open]);
  if (!open) return null;
  const history = stats?.season_history || [];
  return (
    <div className="stats-overlay" onClick={onClose}>
      <div className="stats-card" onClick={e => e.stopPropagation()}>
        <div className="stats-title">📊 Your Stats</div>
        {stats ? (
          <>
            <div className="stats-list">
              <div className="stats-row"><span>Total Spins</span><span>{fmt(stats.spin_count)}</span></div>
              <div className="stats-row"><span>Total Wins</span><span>{fmt(stats.win_count)}</span></div>
              <div className="stats-row"><span>Total Losses</span><span>{fmt(stats.loss_count)}</span></div>
              <div className="stats-row"><span>Win Rate</span><span>{stats.spin_count > 0 ? ((stats.win_count / stats.spin_count) * 100).toFixed(1) + '%' : 'N/A'}</span></div>
              <div className="stats-row"><span>Lifetime Taps</span><span>{fmt(stats.total_fish_clicks)}</span></div>
            </div>
            {history.length > 0 && (
              <div className="stats-season-history">
                <div className="stats-section-title">Season History</div>
                {history.map(s => {
                  const place = PLACE_LABEL(s.finishing_position);
                  const participated = s.final_wins != null;
                  return (
                    <div className="stats-row stats-row--season" key={s.season_number}>
                      <span>Season {s.season_number}</span>
                      <span>
                        {!participated ? '—' : place
                          ? <span className="stats-podium">{place}</span>
                          : `${fmt(s.final_wins)} wins`}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </>
        ) : <div className="stats-loading">Loading…</div>}
        <button className="stats-close-btn" onClick={onClose}>✕</button>
      </div>
    </div>
  );
}

// ── Auth Page ──────────────────────────────────────────────────────────────
function AuthPage({ onAuth }) {
  const [mode, setMode] = useState('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    const { ok, data } = await apiFetch(`/api/${mode}`, {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
    setLoading(false);
    if (ok) {
      onAuth(data.username);
    } else {
      setError(data.error || 'Something went wrong');
    }
  };

  return (
    <div className="auth-overlay">
      <form className="auth-card" onSubmit={submit}>
        <div className="auth-title">Lucky Wheel</div>
        <div className="auth-subtitle">{mode === 'login' ? 'Sign in to play' : 'Create account'}</div>
        {error && <div className="auth-error">{error}</div>}
        <input className="auth-input" type="text" placeholder="Username" value={username}
          onChange={e => setUsername(e.target.value)} autoComplete="username"
          autoCapitalize="none" autoCorrect="off" spellCheck={false} required />
        <input className="auth-input" type="password" placeholder="Password" value={password}
          onChange={e => setPassword(e.target.value)}
          autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
          autoCapitalize="none" autoCorrect="off" spellCheck={false} required />
        <button className="auth-submit-btn" type="submit" disabled={loading}>
          {loading ? 'Please wait…' : mode === 'login' ? 'Sign In' : 'Create Account'}
        </button>
        <div className="auth-toggle">
          {mode === 'login'
            ? <>No account? <a onClick={() => { setMode('register'); setError(''); }}>Register</a></>
            : <>Have an account? <a onClick={() => { setMode('login'); setError(''); }}>Sign in</a></>
          }
        </div>
      </form>
    </div>
  );
}

// ── Community Pot ──────────────────────────────────────────────────────────
function usePotCountdown(filledAt, active) {
  const [remaining, setRemaining] = useState(null);
  useEffect(() => {
    if (!active || !filledAt) { setRemaining(null); return; }
    const expiresAt = new Date(filledAt).getTime() + 3600 * 1000;
    const tick = () => {
      const secs = Math.max(0, Math.floor((expiresAt - Date.now()) / 1000));
      setRemaining(secs);
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [filledAt, active]);
  return remaining;
}

function fmtCountdown(secs) {
  if (secs == null) return '';
  const m = Math.floor(secs / 60);
  const s = secs % 60;
  return `${m}:${String(s).padStart(2, '0')}`;
}

function CommunityPot({ pot, fishClicks, onContribute }) {
  const [localPot, setLocalPot] = useState(pot);

  // Sync when parent pot state changes (e.g. on load)
  useEffect(() => { setLocalPot(pot); }, [pot]);

  // Poll every 10s for live updates
  useEffect(() => {
    const id = setInterval(() => {
      apiFetch('/api/community-pot').then(r => { if (r.ok) setLocalPot(r.data); });
    }, 10000);
    return () => clearInterval(id);
  }, []);

  const handleContribute = async (amount) => {
    const { ok, data } = await apiGame('/api/community-pot/contribute', {
      method: 'POST',
      body: JSON.stringify({ amount }),
    });
    if (ok) {
      setLocalPot({ total_contributed: data.pot_total, target: data.pot_target, filled: data.pot_filled, active: data.pot_active, filled_at: data.filled_at });
      onContribute(data.fish_clicks);
    }
  };

  const total     = localPot.total_contributed || 0;
  const target    = localPot.target || 100_000_000;
  const pct       = Math.min(100, (total / target) * 100);
  const active    = localPot.active;
  const countdown = usePotCountdown(localPot.filled_at, active);

  return (
    <div className={`community-pot-bar${active ? ' community-pot-active' : ''}`}>
      <div className="community-pot-inner">
        <span className="community-pot-label">🎣 Community Pot</span>
        <div className="community-pot-progress">
          <div className="community-pot-fill" style={{ width: pct + '%' }} />
        </div>
        <span className="community-pot-count">{fmt(total)} / {fmt(target)}</span>
        {active ? (
          <>
            <span className="community-pot-bonus">✨ 75% Win Rate Active!</span>
            <span className="community-pot-countdown">{fmtCountdown(countdown)}</span>
          </>
        ) : (
          <div className="community-pot-buttons">
            <button onClick={() => handleContribute('10000')} disabled={fishClicks < 1}>+10k</button>
            <button onClick={() => handleContribute('all')} disabled={fishClicks < 1}>All</button>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Game App ───────────────────────────────────────────────────────────────
function GameApp({ username, gameState, onLogout, onSessionExpired }) {
  const canvasRef = useRef(null);
  const [rotation, setRotation]       = useState(0);
  const [spinning, setSpinning]       = useState(false);
  const [result, setResult]           = useState(null);
  const [showResult, setShowResult]   = useState(false);
  const setShowResultSync = (v) => { showResultRef.current = v; setShowResult(v); };
  const [shieldFeedback, setShieldFeedback] = useState(null);
  const [guardState, setGuardState]   = useState(null); // { blocked, broke } | null
  const guardCompleteRef              = useRef(null);
  const [hideResult, setHideResult]   = useState(false);
  const [confetti, setConfetti]       = useState(false);
  const [wins, setWins]               = useState(gameState.wins);
  const [losses, setLosses]           = useState(gameState.losses);
  const [streak, setStreak]           = useState(gameState.streak);
  const [fishMood, setFishMood]       = useState('idle');
  const [fishClicks, setFishClicks]   = useState(gameState.fish_clicks);
  const [bonusEarned, setBonusEarned] = useState(0);
  const [echoTriggered, setEchoTriggered]               = useState(false);
  const [jackpotHit, setJackpotHit]                     = useState(false);
  const [resilienceTriggered, setResilienceTriggered]   = useState(false);
  const [luckySevenTriggered, setLuckySevenTriggered]   = useState(false);
  const [fortuneCharmTriggered, setFortuneCharmTriggered] = useState(false);
  const [shieldCharges, setShieldCharges]         = useState(gameState.shield_charges);
  const [regenRechargeWins, setRegenRechargeWins] = useState(gameState.regen_recharge_wins || 0);
  const [autoSpin, setAutoSpin]       = useState(false);
  const [ownedItems, setOwnedItems]   = useState(gameState.owned_items);
  const [equippedFish, setEquippedFish] = useState(gameState.equipped_fish);
  const [activeCosmetics, setActiveCosmetics] = useState(gameState.active_cosmetics || []);
  const [infLevels, setInfLevels]     = useState({
    winmult_inf:   gameState.winmult_inf_level   || 0,
    bonusmult_inf: gameState.bonusmult_inf_level || 0,
    clickmult_inf: gameState.clickmult_inf_level || 0,
  });
  const [showStats, setShowStats]     = useState(false);
  const [toast, setToast]             = useState(null);
  const [season, setSeason]           = useState(gameState.season || null);
  const [communityPot, setCommunityPot] = useState(gameState.community_pot || { total_contributed: 0, target: 100_000_000, filled: false, active: false });
  const [lowSpec, setLowSpec]         = useState(() => gameState.low_spec_mode ?? localStorage.getItem('lowSpecMode') === 'true');
  const [shopCollapsed, setShopCollapsed] = useState(false);
  const fireMode = 2; // Mix mode

  const spinSpeed = useMemo(() => {
    if (ownedItems.includes('maxspin'))   return 0.5;
    if (ownedItems.includes('ultraspin')) return 0.75;
    if (ownedItems.includes('hyperspin')) return 1.0;
    if (ownedItems.includes('turbo_spin')) return 1.5;
    if (ownedItems.includes('speed_boost')) return 3.0;
    return 4.5;
  }, [ownedItems]);

  const autoSpinDelay = useMemo(() =>
    ownedItems.includes('autospeed_3') ? 0 : ownedItems.includes('autospeed_2') ? 500 : ownedItems.includes('autospeed_1') ? 1000 : 1500,
  [ownedItems]);

  const clickAmount = useMemo(() => {
    if (ownedItems.includes('double_click_5')) return 6;
    if (ownedItems.includes('double_click_4')) return 5;
    if (ownedItems.includes('double_click_3')) return 4;
    if (ownedItems.includes('double_click_2')) return 3;
    if (ownedItems.includes('double_click')) return 2;
    return 1;
  }, [ownedItems]);

  const clickFrenzyRate = useMemo(() => {
    if (activeCosmetics.includes('final_frenzy'))  return 500;
    if (ownedItems.includes('clickfrenzy_5')) return 100;
    if (ownedItems.includes('clickfrenzy_4')) return 50;
    if (ownedItems.includes('clickfrenzy_3')) return 20;
    if (ownedItems.includes('clickfrenzy_2')) return 5;
    if (ownedItems.includes('clickfrenzy_1')) return 1;
    return 0;
  }, [ownedItems]);

  const fishSizeRem = useMemo(() =>
    activeCosmetics.includes('fishsize_3') ? 40 : activeCosmetics.includes('fishsize_2') ? 28 : activeCosmetics.includes('fishsize_1') ? 20 : 15,
  [activeCosmetics]);

  const confettiCount = useMemo(() =>
    Math.min(200, 80 * (activeCosmetics.includes('confetti_3') ? 15 : activeCosmetics.includes('confetti_2') ? 5 : activeCosmetics.includes('confetti_1') ? 2 : 1)),
  [activeCosmetics]);

  const wheelTheme = useMemo(() => {
    if (activeCosmetics.includes('theme_gold')) return 'gold';
    if (activeCosmetics.includes('theme_void')) return 'void';
    if (activeCosmetics.includes('theme_neon')) return 'neon';
    if (activeCosmetics.includes('theme_ice'))  return 'ice';
    if (activeCosmetics.includes('theme_fire')) return 'fire';
    return 'default';
  }, [activeCosmetics]);

  const bgClass = useMemo(() => {
    if (activeCosmetics.includes('bg_cosmic'))  return 'bg-cosmic';
    if (activeCosmetics.includes('bg_abyss'))   return 'bg-abyss';
    if (activeCosmetics.includes('bg_forest'))  return 'bg-forest';
    if (activeCosmetics.includes('bg_inferno')) return 'bg-inferno';
    if (activeCosmetics.includes('bg_royal'))   return 'bg-royal';
    if (activeCosmetics.includes('bg_ocean'))   return 'bg-ocean';
    return '';
  }, [activeCosmetics]);

  const trailClass = useMemo(() => {
    if (activeCosmetics.includes('trail_6')) return 'trail-galaxy';
    if (activeCosmetics.includes('trail_5')) return 'trail-thunder';
    if (activeCosmetics.includes('trail_4')) return 'trail-frost';
    if (activeCosmetics.includes('trail_3')) return 'trail-rainbow';
    if (activeCosmetics.includes('trail_2')) return 'trail-fire';
    if (activeCosmetics.includes('trail_1')) return 'trail-sparkle';
    return '';
  }, [activeCosmetics]);

  const pageThemeClass = useMemo(() => {
    if (activeCosmetics.includes('page_season1')) return 'page-season1';
    if (activeCosmetics.includes('page_season2')) return 'page-season2';
    return '';
  }, [activeCosmetics]);

  const currentRotationRef = useRef(0);
  const fishTimerRef       = useRef(null);
  const toastTimerRef      = useRef(null);
  const confettiTimerRef   = useRef(null);
  const autoSpinRef        = useRef(false);
  const spinSpeedRef       = useRef(4.5);
  const autoSpinDelayRef   = useRef(1500);
  const spinningRef        = useRef(false);
  const showResultRef      = useRef(false);
  const clickBufferRef     = useRef(0);
  const activeCosmeticsRef = useRef(activeCosmetics);
  const lowSpecRef         = useRef(lowSpec);

  useEffect(() => { activeCosmeticsRef.current = activeCosmetics; }, [activeCosmetics]);
  useEffect(() => { lowSpecRef.current = lowSpec; }, [lowSpec]);
  useEffect(() => {
    autoSpinRef.current = autoSpin;
    if (autoSpin && !spinning) spin();
  }, [autoSpin]); // eslint-disable-line
  useEffect(() => { spinSpeedRef.current = spinSpeed; }, [spinSpeed]);
  useEffect(() => { autoSpinDelayRef.current = autoSpinDelay; }, [autoSpinDelay]);
  useEffect(() => {
    localStorage.setItem('lowSpecMode', lowSpec);
    document.body.classList.toggle('low-spec', lowSpec);
    apiGame('/api/settings', { method: 'POST', body: JSON.stringify({ low_spec_mode: lowSpec }) });
  }, [lowSpec]);

  useEffect(() => {
    setSessionExpiredHandler(onSessionExpired);
    return () => setSessionExpiredHandler(null);
  }, [onSessionExpired]);

  useEffect(() => {
    if (clickFrenzyRate === 0) return;
    const id = setInterval(async () => {
      const { ok, data } = await apiGame('/api/click-frenzy', { method: 'POST', body: '{}' });
      if (ok) setFishClicks(data.fish_clicks);
    }, 5000);
    return () => clearInterval(id);
  }, [clickFrenzyRate]);

  useEffect(() => {
    const currentNumber = season ? season.season_number : null;
    const id = setInterval(async () => {
      const r = await apiFetch('/api/season');
      if (!r.ok) return;
      if (currentNumber !== null && r.data.season_number !== currentNumber) {
        showToast(`Season ${currentNumber} has ended! Season ${r.data.season_number} begins!`);
        const gs = await apiGame('/api/state');
        if (gs.ok) {
          setSeason(gs.data.season);
          setWins(gs.data.wins);
          setLosses(gs.data.losses);
          setStreak(gs.data.streak);
          setFishClicks(gs.data.fish_clicks);
          setOwnedItems(gs.data.owned_items);
          setEquippedFish(gs.data.equipped_fish);
          setShieldCharges(gs.data.shield_charges);
          setRegenRechargeWins(gs.data.regen_recharge_wins || 0);
          setActiveCosmetics(gs.data.active_cosmetics || []);
          setInfLevels({
            winmult_inf:   gs.data.winmult_inf_level   || 0,
            bonusmult_inf: gs.data.bonusmult_inf_level || 0,
            clickmult_inf: gs.data.clickmult_inf_level || 0,
          });
        }
      } else {
        setSeason(r.data);
      }
    }, 60000);
    return () => clearInterval(id);
  }, [season ? season.season_number : null]); // eslint-disable-line

  useEffect(() => {
    const classes = [bgClass, pageThemeClass].filter(Boolean).join(' ');
    document.body.className = classes;
    return () => { document.body.className = ''; };
  }, [bgClass, pageThemeClass]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (canvas) drawWheel(canvas, wheelTheme);
  }, [wheelTheme]);

  const showToast = useCallback((msg) => {
    setToast(msg);
    if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
    toastTimerRef.current = setTimeout(() => setToast(null), 3000);
  }, []);

  const flushClicks = useCallback(async () => {
    const count = clickBufferRef.current;
    if (count === 0) return;
    clickBufferRef.current = 0;
    const { ok, data } = await apiGame('/api/fish-click', {
      method: 'POST',
      body: JSON.stringify({ count }),
    });
    if (ok) setFishClicks(data.fish_clicks);
  }, []);

  useEffect(() => {
    const id = setInterval(flushClicks, 500);
    return () => {
      clearInterval(id);
      const count = clickBufferRef.current;
      if (count > 0) {
        clickBufferRef.current = 0;
        apiGame('/api/fish-click', { method: 'POST', body: JSON.stringify({ count }) });
      }
    };
  }, [flushClicks]);

  const handleBuy = useCallback(async (id) => {
    const { ok, data } = await apiGame('/api/buy', {
      method: 'POST',
      body: JSON.stringify({ item_id: id }),
    });
    if (ok) {
      setFishClicks(data.fish_clicks);
      if (data.wins != null) setWins(data.wins);
      if (data.losses != null) setLosses(data.losses);
      setOwnedItems(data.owned_items);
      setShieldCharges(data.shield_charges);
      setRegenRechargeWins(data.regen_recharge_wins ?? 0);
      if (data.active_cosmetics) setActiveCosmetics(data.active_cosmetics);
      if (data.winmult_inf_level != null || data.bonusmult_inf_level != null || data.clickmult_inf_level != null) {
        setInfLevels({
          winmult_inf:   data.winmult_inf_level   ?? 0,
          bonusmult_inf: data.bonusmult_inf_level ?? 0,
          clickmult_inf: data.clickmult_inf_level ?? 0,
        });
      }
    } else {
      showToast(data.error || 'Purchase failed');
    }
  }, [showToast]);

  const handleEquip = useCallback(async (id) => {
    const { ok, data } = await apiGame('/api/equip', {
      method: 'POST',
      body: JSON.stringify({ fish_id: id }),
    });
    if (ok) setEquippedFish(data.equipped_fish);
    else showToast(data.error || 'Equip failed');
  }, [showToast]);

  const handleEquipCosmetic = useCallback(async (id) => {
    const { ok, data } = await apiGame('/api/equip-cosmetic', {
      method: 'POST',
      body: JSON.stringify({ item_id: id }),
    });
    if (ok) setActiveCosmetics(data.active_cosmetics);
    else showToast(data.error || 'Equip failed');
  }, [showToast]);

  const handleFishClick = useCallback(() => {
    if (activeCosmetics.includes('final_frenzy')) return;
    setFishClicks(c => c + clickAmount);
    clickBufferRef.current += 1;
    if (clickBufferRef.current >= 10) flushClicks();
  }, [clickAmount, flushClicks, activeCosmetics]);

  // Shared post-spin state update (used both directly and via guard callback)
  const applySpinResult = useCallback((data) => {
    setResult(data.result);
    if (data.wins_delta)   setWins(prev => prev + data.wins_delta);
    if (data.losses_delta) setLosses(prev => prev + data.losses_delta);
    setStreak(data.streak);
    setShieldCharges(data.shield_charges);
    setRegenRechargeWins(data.regen_recharge_wins ?? 0);
    if (data.owned_items) {
      const spinResult = new Set(data.owned_items);
      // Sync guard from spin result (can be removed by guard block, added by auto-guard).
      // All other items kept from prev to preserve mid-spin shop purchases.
      setOwnedItems(prev => {
        const withoutGuard = prev.filter(id => id !== 'guard');
        return spinResult.has('guard') ? [...withoutGuard, 'guard'] : withoutGuard;
      });
    }
    setBonusEarned(data.bonus_earned);
    setEchoTriggered(!!data.echo_triggered);
    setJackpotHit(!!data.jackpot_hit);
    setResilienceTriggered(!!data.resilience_triggered);
    setLuckySevenTriggered(!!data.lucky_seven_triggered);
    setFortuneCharmTriggered(!!data.fortune_charm_triggered);
    if (data.active_cosmetics) setActiveCosmetics(data.active_cosmetics);
    if (data.auto_guard_failed) showToast('Not enough wins — Auto-Guard disabled');
    setShieldFeedback(data.shield_used ? {
      type: data.shield_used_type,
      broke: data.shield_broke,
      chargesLeft: data.shield_charges,
      rechargeWins: data.regen_recharge_wins ?? 0,
    } : (data.guard_triggered && data.guard_blocked) ? {
      type: 'guard',
      broke: true,
    } : null);
    setShowResultSync(true);

    const cosm = activeCosmeticsRef.current;
    if (!lowSpecRef.current) {
      if (data.result === 'win' || (data.guard_triggered && data.guard_blocked)) {
        setConfetti(true);
      } else if (cosm.includes('party_mode')) {
        setConfetti(true);
      }
      if (confettiTimerRef.current) clearTimeout(confettiTimerRef.current);
      confettiTimerRef.current = setTimeout(() => setConfetti(false), 3500);
    }

    const mood = (data.result === 'win' || (data.guard_triggered && data.guard_blocked)) ? 'happy' : 'sad';
    setFishMood(mood);
    if (fishTimerRef.current) clearTimeout(fishTimerRef.current);
    fishTimerRef.current = setTimeout(() => setFishMood('idle'), 2500);

    spinningRef.current = false;
    setSpinning(false);
  }, [showToast]);

  const spin = useCallback(async () => {
    if (spinningRef.current) return;
    if (showResultRef.current) {
      setHideResult(true);
      setShowResultSync(false);
      setConfetti(false);
      setTimeout(() => { setHideResult(false); setResult(null); setShieldFeedback(null); }, 350);
    }

    setBonusEarned(0);
    setEchoTriggered(false);
    setJackpotHit(false);
    setResilienceTriggered(false);
    setLuckySevenTriggered(false);
    setFortuneCharmTriggered(false);
    spinningRef.current = true;
    setSpinning(true);

    let data;
    try {
      const res = await apiGame('/api/spin', { method: 'POST', body: '{}' });
      if (!res.ok) {
        spinningRef.current = false;
        setSpinning(false);
        if (autoSpinRef.current) setTimeout(() => { if (autoSpinRef.current) spin(); }, 1000);
        return;
      }
      data = res.data;
    } catch (e) {
      spinningRef.current = false;
      setSpinning(false);
      if (autoSpinRef.current) setTimeout(() => { if (autoSpinRef.current) spin(); }, 1000);
      return;
    }

    const base = currentRotationRef.current;
    const segmentAngle = data.angle % 360;
    const minTarget = base + 5 * 360;
    const newRotation = Math.ceil((minTarget - segmentAngle) / 360) * 360 + segmentAngle;
    currentRotationRef.current = newRotation;
    setRotation(newRotation);

    setTimeout(() => {
      if (data.guard_triggered) {
        // Show guard wheel; defer result display until guard resolves
        setGuardState({ blocked: data.guard_blocked });
        guardCompleteRef.current = () => {
          setGuardState(null);
          applySpinResult(data);

          if (autoSpinRef.current) {
            const delay = Math.max(2000, autoSpinDelayRef.current);
            setTimeout(() => {
              if (autoSpinRef.current) {
                setHideResult(true);
                setTimeout(() => {
                  setShowResultSync(false);
                  setHideResult(false);
                  setResult(null);
                  setShieldFeedback(null);
                  setConfetti(false);
                  spin();
                }, 320);
              }
            }, delay);
          }
        };
      } else {
        applySpinResult(data);

        if (autoSpinRef.current) {
          const delay = data.shield_used
            ? Math.max(2000, autoSpinDelayRef.current)
            : Math.max(1500, autoSpinDelayRef.current);
          setTimeout(() => {
            if (autoSpinRef.current) {
              setHideResult(true);
              setTimeout(() => {
                setShowResultSync(false);
                setHideResult(false);
                setResult(null);
                setShieldFeedback(null);
                spin();
                setTimeout(() => setConfetti(false), 3000);
              }, 320);
            }
          }, delay);
        }
      }
    }, spinSpeedRef.current * 1000 + 200);
  }, [applySpinResult]);

  const handleSpinAgain = useCallback(() => {
    setHideResult(true);
    setTimeout(() => {
      setShowResultSync(false);
      setHideResult(false);
      setResult(null);
      setShieldFeedback(null);
      setConfetti(false);
      spin();
    }, 320);
  }, [spin]);

  const handleLogout = async () => {
    await apiFetch('/api/logout', { method: 'POST', body: '{}' });
    onLogout();
  };

  const hasGuard = ownedItems.includes('guard');
  const hasRegen = ownedItems.includes('regen_shield');

  return (
    <div className={lowSpec ? 'low-spec' : ''}>
      <StatsPanel open={showStats} onClose={() => setShowStats(false)} />
      {toast && <div className="toast-notification">{toast}</div>}
      <Confetti active={confetti} count={confettiCount} />
      <div className={`overlay ${showResult ? 'active' : ''}`} />

      {guardState && (
        <GuardWheel
          blocked={guardState.blocked}
          onComplete={() => guardCompleteRef.current && guardCompleteRef.current()}
        />
      )}

      {season && season.latest_winners && (
        <SeasonWinners winners={season.latest_winners} seasonNumber={season.season_number - 1} />
      )}

      <FireEffect
        streak={streak}
        mode={fireMode}
        lowSpec={lowSpec}
      />

      <div className="user-bar">
        <span className="user-bar-name">👤 {username}</span>
        <button className="stats-btn" onClick={() => setShowStats(true)}>📊</button>
        <button
          className="stats-btn"
          onClick={() => setLowSpec(v => !v)}
          title={lowSpec ? 'Low Spec Mode ON — click to restore animations' : 'Low Spec Mode OFF — click to reduce GPU usage'}
          style={{ opacity: lowSpec ? 1 : 0.5 }}
        >⚡</button>
        <button className="logout-btn" onClick={handleLogout}>Logout</button>
        <CommunityPot
          pot={communityPot}
          fishClicks={fishClicks}
          onContribute={newClicks => setFishClicks(newClicks)}
        />
        {season && <SeasonInfo seasonNumber={season.season_number} endsAt={season.ends_at} />}
      </div>

      <Fish
        mood={fishMood}
        net={wins - losses}
        fishClicks={fishClicks}
        fishData={getFishData(equippedFish)}
        sizeRem={fishSizeRem}
        trailClass={trailClass}
        lowSpec={lowSpec}
        onFishClick={handleFishClick}
      />

      {showResult && (
        <div className={`result-banner ${showResult && !hideResult ? 'show' : ''} ${hideResult ? 'hide' : ''}`}>
          {result === 'win' || (result === 'lose' && shieldFeedback) ? (
            <div className={`result-text ${result === 'win' ? 'win' : 'win'}`}>
              {result === 'win' ? '🎰 YOU WIN! 🎰' : '🛡️ BLOCKED! 🛡️'}
            </div>
          ) : (
            <div className="result-text lose">💀 YOU LOSE 💀</div>
          )}
          {jackpotHit && (
            <div className="bonus-line jackpot-line">🎰 JACKPOT! 50x multiplier applied!</div>
          )}
          {echoTriggered && !jackpotHit && (
            <div className="bonus-line echo-line">🔊 WIN ECHO! Wins doubled!</div>
          )}
          {luckySevenTriggered && (
            <div className="bonus-line lucky-seven-line">7️⃣ LUCKY SEVEN! Guaranteed win triggered!</div>
          )}
          {fortuneCharmTriggered && (
            <div className="bonus-line fortune-charm-line">🍀 FORTUNE CHARM! +25% streak bonus applied!</div>
          )}
          {resilienceTriggered && (
            <div className="bonus-line resilience-line">💪 RESILIENCE! Streak -1 (not reset)</div>
          )}
          {bonusEarned > 0 && (
            <div className="bonus-line">🔥 Streak Bonus +{fmt(bonusEarned)}!</div>
          )}
          {bonusEarned < 0 && (
            <div className="bonus-line lose-bonus">💀 Loss Streak +{fmt(Math.abs(bonusEarned))} extra losses!</div>
          )}
          {shieldFeedback && (() => {
            const names  = { regen_shield: 'Regenerating Shield', guard: 'Guard' };
            const emojis = { regen_shield: '🔄', guard: '🛡️' };
            const name  = names[shieldFeedback.type]  || shieldFeedback.type;
            const emoji = emojis[shieldFeedback.type] || '🛡️';
            const sub   = shieldFeedback.type === 'regen_shield'
              ? `Recharging… ${shieldFeedback.rechargeWins} win${shieldFeedback.rechargeWins !== 1 ? 's' : ''}`
              : shieldFeedback.type === 'guard'
              ? 'Guard consumed'
              : null;
            return (
              <div className="shield-feedback">
                <div className="shield-feedback-icon">{emoji}</div>
                <div className="shield-feedback-label">{name} Blocked!</div>
                {sub && <div className="shield-feedback-sub">{sub}</div>}
              </div>
            );
          })()}
          <button className="spin-again-btn" onClick={handleSpinAgain}>Spin Again</button>
        </div>
      )}

      <div className="casino-container">
        <div className="bulbs">
          {Array.from({length: 16}, (_, i) => <div key={i} className="bulb" />)}
        </div>

        <div className="casino-header">
          <div className="casino-title">Lucky Wheel</div>
          <div className="subtitle">Try Your Fortune</div>
        </div>

        <div
          className={`wheel-wrapper ${activeCosmetics.includes('golden_wheel') ? 'golden' : ''}`}
          onClick={!spinning && !autoSpin ? spin : undefined}
          title={autoSpin ? 'Auto-spin active' : 'Click to spin!'}
        >
          <div className={`pointer ${spinning ? 'spinning' : ''}`} />
          <canvas
            ref={canvasRef}
            width={380}
            height={380}
            className={`wheel-canvas ${spinning ? 'spinning' : ''}`}
            style={{ transform: `rotate(${rotation}deg)`, transition: `transform ${spinSpeed}s cubic-bezier(0.17, 0.67, 0.12, 0.99)` }}
          />
          <div className="center-hub">★</div>
        </div>

        <div className={`spin-prompt ${spinning || autoSpin ? 'hidden' : ''}`} onClick={spin}>
          {spinning || autoSpin ? '' : '▶ Click to Spin ◀'}
        </div>

        <label className="autospin-row">
          <input type="checkbox" checked={autoSpin} onChange={e => setAutoSpin(e.target.checked)} />
          <span className="autospin-label">Auto Spin</span>
        </label>

        <Scoreboard wins={wins} losses={losses} lastResult={result} />

        <div className="bulbs">
          {Array.from({length: 16}, (_, i) => <div key={i} className="bulb" />)}
        </div>
      </div>

      <div className="game-right">
        <button
          className="shop-collapse-btn"
          onClick={() => setShopCollapsed(c => !c)}
          title={shopCollapsed ? 'Expand shop' : 'Collapse shop'}
        >{shopCollapsed ? '‹' : '›'}</button>
        <div className={`game-right-body${shopCollapsed ? ' shop-collapsed' : ''}`}>
          <div className="game-right-sidebar">
            {(hasGuard || hasRegen) && (
              <div className="shield-indicator">
                {hasGuard && <div>🛡️ Guard ready</div>}
                {hasRegen && (
                  <div>{regenRechargeWins > 0 ? `🔄 ${regenRechargeWins} win${regenRechargeWins !== 1 ? 's' : ''}` : '🔄 ready'}</div>
                )}
              </div>
            )}
            <StreakPanel streak={streak} />
          </div>

          <ShopPanel
            fishClicks={fishClicks}
            wins={wins}
            losses={losses}
            ownedItems={ownedItems}
            equippedFish={equippedFish}
            activeCosmetics={activeCosmetics}
            infLevels={infLevels}
            onBuy={handleBuy}
            onEquip={handleEquip}
            onEquipCosmetic={handleEquipCosmetic}
            collapsed={shopCollapsed}
          />
        </div>
      </div>

      <div className="bottom-left-stack">
        <div className="fish-counter">
          <span className="fish-counter-label">Balance</span>
          <span className="fish-counter-value">{getFishData(equippedFish).emoji} × {fmt(fishClicks)}</span>
        </div>
        <Leaderboard currentUser={username} />
      </div>

    </div>
  );
}

// ── Root App ───────────────────────────────────────────────────────────────
function App() {
  const [user, setUser]             = useState(undefined);
  const [gameState, setGameState]   = useState(null);
  const [sessionMsg, setSessionMsg] = useState('');

  useEffect(() => { localStorage.clear(); }, []);

  useEffect(() => {
    (async () => {
      const { ok, data } = await apiFetch('/api/me');
      if (ok && data.username) {
        const gs = await apiFetch('/api/state');
        if (gs.ok) {
          setGameState(gs.data);
          setUser(data.username);
        } else {
          setUser(null);
        }
      } else {
        setUser(null);
      }
    })();
  }, []);

  const handleAuth = async (username) => {
    const gs = await apiFetch('/api/state');
    if (gs.ok) {
      setGameState(gs.data);
      setUser(username);
      setSessionMsg('');
    }
  };

  const handleLogout = () => {
    setUser(null);
    setGameState(null);
    setSessionMsg('');
  };

  const handleSessionExpired = useCallback(() => {
    setUser(null);
    setGameState(null);
    setSessionMsg('Your session was taken over by a new login. Please sign in again.');
  }, []);

  if (user === undefined) {
    return (
      <div style={{ color: '#FFD700', fontSize: '1.5rem', letterSpacing: '4px', textTransform: 'uppercase', textAlign: 'center' }}>
        Loading…
      </div>
    );
  }

  if (!user) {
    return (
      <>
        {sessionMsg && <div className="session-banner">{sessionMsg}</div>}
        <AuthPage onAuth={handleAuth} />
      </>
    );
  }

  return <GameApp username={user} gameState={gameState} onLogout={handleLogout} onSessionExpired={handleSessionExpired} />;
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
