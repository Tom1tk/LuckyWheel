const { useState, useRef, useEffect, useCallback, useMemo } = React;

// ── API helpers ───────────────────────────────────────────────────────────
let _csrfToken = null;
function storeCsrf(data) { if (data && data.csrf_token) _csrfToken = data.csrf_token; }

async function apiFetch(path, opts = {}) {
  const method = (opts.method || 'GET').toUpperCase();
  const headers = { 'Content-Type': 'application/json' };
  if (_csrfToken && method !== 'GET' && method !== 'HEAD') {
    headers['X-CSRFToken'] = _csrfToken;
  }
  const res = await fetch(path, { headers, ...opts });
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

// ── Wormhole Background Components ───────────────────────────────────────────

function WormholeBackground({
  className = "", intensity = 1, speed = 1, starCount = 950, streakCount = 240,
  nebulaStrength = 0.95, starDriftSpeed = 0.18, parallaxStrength = 28, parallaxSmoothing = 0.065,
  parallax = false, static: staticMode = false,
}) {
  const canvasRef = useRef(null);
  const animationRef = useRef(0);
  const parallaxRef = useRef({ currentX: 0, currentY: 0, targetX: 0, targetY: 0 });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d", { alpha: true });
    let dpr = Math.min(window.devicePixelRatio || 1, 2);
    let width = 0, height = 0, cx = 0, cy = 0;
    let lastTime = performance.now(), time = 0;
    const lerp = (a, b, t) => a + (b - a) * t;
    const clamp = (v, min, max) => Math.max(min, Math.min(max, v));
    const rand = (min, max) => Math.random() * (max - min) + min;
    const rgba = (r, g, b, a) => `rgba(${r}, ${g}, ${b}, ${a})`;
    const depth = { background: 0.16, vignette: 0.2, focal: 0.12, nebula: 0.3, slowStars: 0.62, streaks: 1.0 };
    const movingStars = [], streaks = [];

    function createMovingStar(index = 0) {
      const colourBand = Math.random();
      return {
        angle: rand(0, Math.PI * 2), z: Math.random() ** 0.55,
        speed: rand(0.0012, 0.0045) * speed * starDriftSpeed * (0.75 + intensity * 0.45),
        size: rand(0.45, 1.7), alpha: rand(0.18, 0.95),
        twinkle: rand(0.35, 2.1), phase: rand(0, Math.PI * 2),
        colour: colourBand < 0.48 ? [165, 215, 255] : colourBand < 0.82 ? [255, 240, 255] : [255, 185, 235],
        seed: index + Math.random() * 1000,
      };
    }
    function createStars() {
      movingStars.length = 0;
      const total = Math.floor(starCount * intensity);
      for (let i = 0; i < total; i++) movingStars.push(createMovingStar(i));
    }
    function createStreak(index = 0) {
      const angleJitter = rand(-0.3, 0.3);
      const baseAngle = Math.atan2(rand(-height * 0.55, height * 0.55), rand(-width * 0.55, width * 0.55));
      const hueWeight = Math.random();
      return {
        angle: baseAngle + angleJitter, z: rand(0.02, 1),
        speed: rand(0.003, 0.018) * speed * (0.8 + intensity * 0.65),
        width: rand(0.5, 2.6), length: rand(22, 180),
        alpha: rand(0.12, 0.85), drift: rand(-0.12, 0.12),
        pulse: rand(0.5, 2.3), pulseOffset: rand(0, Math.PI * 2),
        colour: hueWeight < 0.18 ? [255,255,255] : hueWeight < 0.39 ? [95,205,255] : hueWeight < 0.56 ? [0,255,220] : hueWeight < 0.68 ? [120,255,160] : hueWeight < 0.84 ? [255,90,210] : [165,110,255],
        seed: index + Math.random() * 1000,
      };
    }
    function createStreaks() {
      streaks.length = 0;
      const total = Math.floor(streakCount * intensity);
      for (let i = 0; i < total; i++) streaks.push(createStreak(i));
    }
    function resize() {
      const rect = canvas.getBoundingClientRect();
      width = Math.max(1, Math.floor(rect.width || window.innerWidth));
      height = Math.max(1, Math.floor(rect.height || window.innerHeight));
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.floor(width * dpr); canvas.height = Math.floor(height * dpr);
      canvas.style.width = `${width}px`; canvas.style.height = `${height}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      cx = width * 0.5; cy = height * 0.5;
      createStars(); createStreaks();
    }
    function drawBackgroundGradient() {
      const bg = ctx.createLinearGradient(0, 0, width, height);
      bg.addColorStop(0, "rgba(2,6,18,1)"); bg.addColorStop(0.28, "rgba(5,12,30,1)");
      bg.addColorStop(0.55, "rgba(9,8,24,1)"); bg.addColorStop(0.78, "rgba(20,7,28,1)");
      bg.addColorStop(1, "rgba(6,2,12,1)");
      ctx.fillStyle = bg; ctx.fillRect(0, 0, width, height);
    }
    function drawNebulaClouds(t) {
      ctx.save(); ctx.globalCompositeOperation = "screen";
      const leftGrad = ctx.createRadialGradient(width*0.18, height*0.48, 10, width*0.18, height*0.48, width*0.55);
      leftGrad.addColorStop(0, `rgba(40,140,255,${0.18*nebulaStrength})`);
      leftGrad.addColorStop(0.28, `rgba(20,105,230,${0.12*nebulaStrength})`);
      leftGrad.addColorStop(0.62, `rgba(8,42,120,${0.09*nebulaStrength})`);
      leftGrad.addColorStop(1, "rgba(0,0,0,0)");
      ctx.fillStyle = leftGrad; ctx.fillRect(0, 0, width, height);
      const rightGrad = ctx.createRadialGradient(width*0.8, height*0.5, 12, width*0.8, height*0.5, width*0.48);
      rightGrad.addColorStop(0, `rgba(255,100,230,${0.2*nebulaStrength})`);
      rightGrad.addColorStop(0.34, `rgba(175,70,255,${0.14*nebulaStrength})`);
      rightGrad.addColorStop(0.7, `rgba(95,25,160,${0.08*nebulaStrength})`);
      rightGrad.addColorStop(1, "rgba(0,0,0,0)");
      ctx.fillStyle = rightGrad; ctx.fillRect(0, 0, width, height);
      const blobs = [
        { x: width*0.16, y: height*0.33, rx: width*0.28, ry: height*0.16, c1: "rgba(80,180,255,0.06)", c2: "rgba(20,40,100,0)" },
        { x: width*0.26, y: height*0.72, rx: width*0.24, ry: height*0.12, c1: "rgba(0,190,255,0.05)", c2: "rgba(0,0,0,0)" },
        { x: width*0.78, y: height*0.33, rx: width*0.22, ry: height*0.14, c1: "rgba(255,90,200,0.07)", c2: "rgba(0,0,0,0)" },
        { x: width*0.86, y: height*0.66, rx: width*0.26, ry: height*0.16, c1: "rgba(180,70,255,0.08)", c2: "rgba(0,0,0,0)" },
      ];
      blobs.forEach((b, i) => {
        const driftX = Math.sin(t*0.00018+i*1.7)*18, driftY = Math.cos(t*0.00012+i*1.3)*12;
        const g = ctx.createRadialGradient(b.x+driftX, b.y+driftY, 0, b.x+driftX, b.y+driftY, Math.max(b.rx, b.ry));
        g.addColorStop(0, b.c1); g.addColorStop(1, b.c2);
        ctx.save(); ctx.translate(b.x+driftX, b.y+driftY); ctx.scale(1, b.ry/b.rx);
        ctx.beginPath(); ctx.arc(0, 0, b.rx, 0, Math.PI*2); ctx.closePath();
        ctx.fillStyle = g; ctx.fill(); ctx.restore();
      });
      ctx.restore();
    }
    function drawSlowMovingStars(t) {
      ctx.save(); ctx.globalCompositeOperation = "screen";
      const maxRadius = Math.hypot(width, height) * 0.77;
      for (let i = 0; i < movingStars.length; i++) {
        const s = movingStars[i]; s.z += s.speed;
        if (s.z > 1.03) { movingStars[i] = createMovingStar(i + t*0.001); movingStars[i].z = rand(0.01, 0.08); continue; }
        const eased = s.z * s.z;
        const radius = lerp(0, maxRadius, eased);
        const x = cx + Math.cos(s.angle) * radius, y = cy + Math.sin(s.angle) * radius;
        if (x < -20 || x > width+20 || y < -20 || y > height+20) { movingStars[i] = createMovingStar(i + t*0.001); movingStars[i].z = rand(0.01, 0.08); continue; }
        const pulse = 0.78 + 0.22 * Math.sin(t*0.0012*s.twinkle + s.phase);
        const alpha = clamp(s.alpha * (0.35 + eased*0.95) * pulse, 0.05, 1);
        const radiusPx = s.size * (0.65 + eased*1.15);
        const [r, g, b] = s.colour;
        ctx.fillStyle = rgba(r, g, b, alpha); ctx.beginPath(); ctx.arc(x, y, radiusPx, 0, Math.PI*2); ctx.fill();
        if (radiusPx > 1.2) {
          ctx.strokeStyle = rgba(255,255,255, alpha*0.18); ctx.lineWidth = 0.55;
          ctx.beginPath(); ctx.moveTo(x-radiusPx*1.8,y); ctx.lineTo(x+radiusPx*1.8,y);
          ctx.moveTo(x,y-radiusPx*1.8); ctx.lineTo(x,y+radiusPx*1.8); ctx.stroke();
        }
      }
      ctx.restore();
    }
    function drawStreaks(t) {
      ctx.save(); ctx.globalCompositeOperation = "lighter"; ctx.lineCap = "round";
      const maxRadius = Math.hypot(width, height) * 0.75;
      for (let i = 0; i < streaks.length; i++) {
        const s = streaks[i]; s.z += s.speed;
        if (s.z > 1.02) { streaks[i] = createStreak(i + t*0.001); continue; }
        const eased = s.z * s.z;
        const radius = lerp(6, maxRadius, eased);
        const angle = s.angle + Math.sin(t*0.0004*s.pulse + s.pulseOffset)*s.drift*0.18;
        const x = cx + Math.cos(angle)*radius, y = cy + Math.sin(angle)*radius;
        const dirX = x-cx, dirY = y-cy, dirLen = Math.max(1, Math.hypot(dirX, dirY));
        const ux = dirX/dirLen, uy = dirY/dirLen;
        const trail = s.length * (0.18 + eased*1.75);
        const x2 = x - ux*trail, y2 = y - uy*trail;
        const [r, g, b] = s.colour;
        const glow = clamp(s.alpha * (0.3 + eased*1.15), 0.05, 1);
        const grad = ctx.createLinearGradient(x2,y2,x,y);
        grad.addColorStop(0, rgba(255,255,255,0)); grad.addColorStop(0.45, rgba(r,g,b,glow*0.33)); grad.addColorStop(1, rgba(r,g,b,glow));
        ctx.strokeStyle = grad; ctx.lineWidth = s.width * (0.3 + eased*1.4);
        ctx.beginPath(); ctx.moveTo(x2,y2); ctx.lineTo(x,y); ctx.stroke();
      }
      ctx.restore();
    }
    function buildSparklePath(sizeOuter, sizeInner) {
      ctx.beginPath();
      ctx.moveTo(cx, cy - sizeOuter);
      ctx.quadraticCurveTo(cx + sizeInner*0.45, cy - sizeInner*0.75, cx + sizeOuter, cy);
      ctx.quadraticCurveTo(cx + sizeInner*0.75, cy + sizeInner*0.45, cx, cy + sizeOuter);
      ctx.quadraticCurveTo(cx - sizeInner*0.45, cy + sizeInner*0.75, cx - sizeOuter, cy);
      ctx.quadraticCurveTo(cx - sizeInner*0.75, cy - sizeInner*0.45, cx, cy - sizeOuter);
      ctx.closePath();
    }
    function drawCentreFlare(t) {
      ctx.save(); ctx.globalCompositeOperation = "screen";
      const pulse = 0.94 + Math.sin(t*0.0034)*0.05 + Math.sin(t*0.0017)*0.035;
      const minSide = Math.min(width, height);
      const outerGlow = ctx.createRadialGradient(cx,cy,0,cx,cy,minSide*0.24);
      outerGlow.addColorStop(0, rgba(255,255,255,0.46*pulse)); outerGlow.addColorStop(0.08, rgba(210,235,255,0.22*pulse));
      outerGlow.addColorStop(0.18, rgba(255,160,235,0.16*pulse)); outerGlow.addColorStop(0.28, rgba(120,180,255,0.11*pulse));
      outerGlow.addColorStop(1, rgba(0,0,0,0));
      ctx.fillStyle = outerGlow; ctx.beginPath(); ctx.arc(cx,cy,minSide*0.24,0,Math.PI*2); ctx.fill();
      const starOuter = clamp(minSide*0.078*pulse, 36, 82), starInner = starOuter*0.34;
      const starGlowA = ctx.createRadialGradient(cx,cy,0,cx,cy,starOuter*1.45);
      starGlowA.addColorStop(0, rgba(255,255,255,0.78)); starGlowA.addColorStop(0.42, rgba(255,245,255,0.28));
      starGlowA.addColorStop(0.7, rgba(255,170,235,0.16)); starGlowA.addColorStop(1, rgba(0,0,0,0));
      ctx.fillStyle = starGlowA; buildSparklePath(starOuter*1.22, starInner*1.22); ctx.fill();
      const starFill = ctx.createRadialGradient(cx,cy,0,cx,cy,starOuter);
      starFill.addColorStop(0, rgba(255,255,255,1)); starFill.addColorStop(0.28, rgba(255,255,255,0.96));
      starFill.addColorStop(0.62, rgba(255,230,245,0.82)); starFill.addColorStop(0.86, rgba(190,225,255,0.52));
      starFill.addColorStop(1, rgba(160,215,255,0.18));
      ctx.fillStyle = starFill; buildSparklePath(starOuter, starInner); ctx.fill();
      ctx.strokeStyle = rgba(255,255,255,0.28); ctx.lineWidth = 1.1; buildSparklePath(starOuter, starInner); ctx.stroke();
      const verticalH = Math.min(height*0.42,360), verticalW = Math.max(6, Math.min(width*0.014,16));
      const vertFlare = ctx.createLinearGradient(cx, cy-verticalH*0.5, cx, cy+verticalH*0.5);
      vertFlare.addColorStop(0, rgba(255,255,255,0)); vertFlare.addColorStop(0.18, rgba(255,185,235,0.22));
      vertFlare.addColorStop(0.5, rgba(255,255,255,0.78)); vertFlare.addColorStop(0.82, rgba(180,215,255,0.22));
      vertFlare.addColorStop(1, rgba(255,255,255,0));
      ctx.fillStyle = vertFlare; ctx.fillRect(cx-verticalW*0.5, cy-verticalH*0.5, verticalW, verticalH);
      const horizontalW = width*0.7;
      const horizFlare = ctx.createLinearGradient(cx-horizontalW*0.5,cy,cx+horizontalW*0.5,cy);
      horizFlare.addColorStop(0, rgba(255,255,255,0)); horizFlare.addColorStop(0.2, rgba(90,165,255,0.05));
      horizFlare.addColorStop(0.42, rgba(255,180,235,0.12)); horizFlare.addColorStop(0.5, rgba(255,255,255,0.34));
      horizFlare.addColorStop(0.58, rgba(190,220,255,0.12)); horizFlare.addColorStop(0.8, rgba(255,120,220,0.05));
      horizFlare.addColorStop(1, rgba(255,255,255,0));
      ctx.fillStyle = horizFlare; ctx.fillRect(cx-horizontalW*0.5, cy-2.5, horizontalW, 5);
      const innerGlow = ctx.createRadialGradient(cx,cy,0,cx,cy,starOuter*0.9);
      innerGlow.addColorStop(0, rgba(255,255,255,0.96)); innerGlow.addColorStop(0.35, rgba(255,255,255,0.55));
      innerGlow.addColorStop(0.8, rgba(180,225,255,0.12)); innerGlow.addColorStop(1, rgba(0,0,0,0));
      ctx.fillStyle = innerGlow; ctx.beginPath(); ctx.arc(cx,cy,starOuter*0.9,0,Math.PI*2); ctx.fill();
      ctx.restore();
    }
    function drawVignette() {
      const vig = ctx.createRadialGradient(cx,cy,Math.min(width,height)*0.2,cx,cy,Math.max(width,height)*0.8);
      vig.addColorStop(0,"rgba(0,0,0,0)"); vig.addColorStop(0.65,"rgba(0,0,0,0.08)"); vig.addColorStop(1,"rgba(0,0,0,0.42)");
      ctx.fillStyle = vig; ctx.fillRect(0,0,width,height);
    }
    function onPointerMove(event) {
      const rect = canvas.getBoundingClientRect();
      const xNorm = rect.width > 0 ? ((event.clientX - rect.left) / rect.width) * 2 - 1 : 0;
      const yNorm = rect.height > 0 ? ((event.clientY - rect.top) / rect.height) * 2 - 1 : 0;
      parallaxRef.current.targetX = clamp(xNorm, -1, 1) * parallaxStrength;
      parallaxRef.current.targetY = clamp(yNorm, -1, 1) * parallaxStrength;
    }
    function onPointerLeave() { parallaxRef.current.targetX = 0; parallaxRef.current.targetY = 0; }
    function updateParallax() {
      const p = parallaxRef.current;
      p.currentX = lerp(p.currentX, p.targetX, parallaxSmoothing);
      p.currentY = lerp(p.currentY, p.targetY, parallaxSmoothing);
      return p;
    }
    function drawBackgroundGradientP(p) {
      const shiftX = p.currentX * depth.background, shiftY = p.currentY * depth.background;
      const bg = ctx.createLinearGradient(shiftX*0.8, shiftY*0.8, width+shiftX*0.5, height+shiftY*0.5);
      bg.addColorStop(0,"rgba(2,6,18,1)"); bg.addColorStop(0.28,"rgba(5,12,30,1)");
      bg.addColorStop(0.55,"rgba(9,8,24,1)"); bg.addColorStop(0.78,"rgba(20,7,28,1)");
      bg.addColorStop(1,"rgba(6,2,12,1)");
      ctx.fillStyle = bg; ctx.fillRect(0,0,width,height);
    }
    function drawNebulaCloudsP(t, p) {
      ctx.save(); ctx.globalCompositeOperation = "screen";
      const nx = p.currentX * depth.nebula, ny = p.currentY * depth.nebula;
      const leftGrad = ctx.createRadialGradient(width*0.18+nx,height*0.48+ny,10,width*0.18+nx,height*0.48+ny,width*0.55);
      leftGrad.addColorStop(0,`rgba(40,140,255,${0.18*nebulaStrength})`);
      leftGrad.addColorStop(0.28,`rgba(20,105,230,${0.12*nebulaStrength})`);
      leftGrad.addColorStop(0.62,`rgba(8,42,120,${0.09*nebulaStrength})`);
      leftGrad.addColorStop(1,"rgba(0,0,0,0)");
      ctx.fillStyle = leftGrad; ctx.fillRect(0,0,width,height);
      const rightGrad = ctx.createRadialGradient(width*0.8+nx,height*0.5+ny,12,width*0.8+nx,height*0.5+ny,width*0.48);
      rightGrad.addColorStop(0,`rgba(255,100,230,${0.2*nebulaStrength})`);
      rightGrad.addColorStop(0.34,`rgba(175,70,255,${0.14*nebulaStrength})`);
      rightGrad.addColorStop(0.7,`rgba(95,25,160,${0.08*nebulaStrength})`);
      rightGrad.addColorStop(1,"rgba(0,0,0,0)");
      ctx.fillStyle = rightGrad; ctx.fillRect(0,0,width,height);
      const blobs = [
        {x:width*0.16,y:height*0.33,rx:width*0.28,ry:height*0.16,c1:"rgba(80,180,255,0.06)",c2:"rgba(20,40,100,0)"},
        {x:width*0.26,y:height*0.72,rx:width*0.24,ry:height*0.12,c1:"rgba(0,190,255,0.05)",c2:"rgba(0,0,0,0)"},
        {x:width*0.78,y:height*0.33,rx:width*0.22,ry:height*0.14,c1:"rgba(255,90,200,0.07)",c2:"rgba(0,0,0,0)"},
        {x:width*0.86,y:height*0.66,rx:width*0.26,ry:height*0.16,c1:"rgba(180,70,255,0.08)",c2:"rgba(0,0,0,0)"},
      ];
      blobs.forEach((b, i) => {
        const driftX = Math.sin(t*0.00018+i*1.7)*18+nx, driftY = Math.cos(t*0.00012+i*1.3)*12+ny;
        const g = ctx.createRadialGradient(b.x+driftX,b.y+driftY,0,b.x+driftX,b.y+driftY,Math.max(b.rx,b.ry));
        g.addColorStop(0,b.c1); g.addColorStop(1,b.c2);
        ctx.save(); ctx.translate(b.x+driftX,b.y+driftY); ctx.scale(1,b.ry/b.rx);
        ctx.beginPath(); ctx.arc(0,0,b.rx,0,Math.PI*2); ctx.closePath();
        ctx.fillStyle=g; ctx.fill(); ctx.restore();
      });
      ctx.restore();
    }
    function drawSlowMovingStarsP(t, p) {
      ctx.save(); ctx.globalCompositeOperation = "screen";
      const maxRadius = Math.hypot(width,height)*0.77;
      const povX = cx + p.currentX*depth.slowStars, povY = cy + p.currentY*depth.slowStars;
      for (let i = 0; i < movingStars.length; i++) {
        const s = movingStars[i]; s.z += s.speed;
        if (s.z > 1.03) { movingStars[i] = createMovingStar(i+t*0.001); movingStars[i].z = rand(0.01,0.08); continue; }
        const eased = s.z*s.z, radius = lerp(0,maxRadius,eased);
        const x = povX + Math.cos(s.angle)*radius, y = povY + Math.sin(s.angle)*radius;
        if (x<-20||x>width+20||y<-20||y>height+20) { movingStars[i]=createMovingStar(i+t*0.001); movingStars[i].z=rand(0.01,0.08); continue; }
        const pulse = 0.78+0.22*Math.sin(t*0.0012*s.twinkle+s.phase);
        const alpha = clamp(s.alpha*(0.35+eased*0.95)*pulse,0.05,1);
        const radiusPx = s.size*(0.65+eased*1.15);
        const [r,g,b] = s.colour;
        ctx.fillStyle=rgba(r,g,b,alpha); ctx.beginPath(); ctx.arc(x,y,radiusPx,0,Math.PI*2); ctx.fill();
        if (radiusPx>1.2) {
          ctx.strokeStyle=rgba(255,255,255,alpha*0.18); ctx.lineWidth=0.55;
          ctx.beginPath(); ctx.moveTo(x-radiusPx*1.8,y); ctx.lineTo(x+radiusPx*1.8,y);
          ctx.moveTo(x,y-radiusPx*1.8); ctx.lineTo(x,y+radiusPx*1.8); ctx.stroke();
        }
      }
      ctx.restore();
    }
    function drawStreaksP(t, p) {
      ctx.save(); ctx.globalCompositeOperation = "lighter"; ctx.lineCap = "round";
      const maxRadius = Math.hypot(width,height)*0.75;
      const povX = cx+p.currentX*depth.streaks, povY = cy+p.currentY*depth.streaks;
      for (let i = 0; i < streaks.length; i++) {
        const s = streaks[i]; s.z += s.speed;
        if (s.z > 1.02) { streaks[i]=createStreak(i+t*0.001); continue; }
        const eased = s.z*s.z, radius = lerp(6,maxRadius,eased);
        const angle = s.angle + Math.sin(t*0.0004*s.pulse+s.pulseOffset)*s.drift*0.18;
        const x=povX+Math.cos(angle)*radius, y=povY+Math.sin(angle)*radius;
        const dirX=x-povX, dirY=y-povY, dirLen=Math.max(1,Math.hypot(dirX,dirY));
        const ux=dirX/dirLen, uy=dirY/dirLen;
        const trail=s.length*(0.18+eased*1.75);
        const x2=x-ux*trail, y2=y-uy*trail;
        const [r,g,b]=s.colour, glow=clamp(s.alpha*(0.3+eased*1.15),0.05,1);
        const grad=ctx.createLinearGradient(x2,y2,x,y);
        grad.addColorStop(0,rgba(255,255,255,0)); grad.addColorStop(0.45,rgba(r,g,b,glow*0.33)); grad.addColorStop(1,rgba(r,g,b,glow));
        ctx.strokeStyle=grad; ctx.lineWidth=s.width*(0.3+eased*1.4);
        ctx.beginPath(); ctx.moveTo(x2,y2); ctx.lineTo(x,y); ctx.stroke();
      }
      ctx.restore();
    }
    function buildSparklePathP(x, y, sizeOuter, sizeInner) {
      ctx.beginPath();
      ctx.moveTo(x, y-sizeOuter);
      ctx.quadraticCurveTo(x+sizeInner*0.45, y-sizeInner*0.75, x+sizeOuter, y);
      ctx.quadraticCurveTo(x+sizeInner*0.75, y+sizeInner*0.45, x, y+sizeOuter);
      ctx.quadraticCurveTo(x-sizeInner*0.45, y+sizeInner*0.75, x-sizeOuter, y);
      ctx.quadraticCurveTo(x-sizeInner*0.75, y-sizeInner*0.45, x, y-sizeOuter);
      ctx.closePath();
    }
    function drawCentreFlareP(t, p) {
      ctx.save(); ctx.globalCompositeOperation = "screen";
      const focalX = cx+p.currentX*depth.focal, focalY = cy+p.currentY*depth.focal;
      const pulse = 0.94+Math.sin(t*0.0034)*0.05+Math.sin(t*0.0017)*0.035;
      const minSide = Math.min(width,height);
      const outerGlow = ctx.createRadialGradient(focalX,focalY,0,focalX,focalY,minSide*0.24);
      outerGlow.addColorStop(0,rgba(255,255,255,0.46*pulse)); outerGlow.addColorStop(0.08,rgba(210,235,255,0.22*pulse));
      outerGlow.addColorStop(0.18,rgba(255,160,235,0.16*pulse)); outerGlow.addColorStop(0.28,rgba(120,180,255,0.11*pulse));
      outerGlow.addColorStop(1,rgba(0,0,0,0));
      ctx.fillStyle=outerGlow; ctx.beginPath(); ctx.arc(focalX,focalY,minSide*0.24,0,Math.PI*2); ctx.fill();
      const starOuter=clamp(minSide*0.078*pulse,36,82), starInner=starOuter*0.34;
      const starGlowA=ctx.createRadialGradient(focalX,focalY,0,focalX,focalY,starOuter*1.45);
      starGlowA.addColorStop(0,rgba(255,255,255,0.78)); starGlowA.addColorStop(0.42,rgba(255,245,255,0.28));
      starGlowA.addColorStop(0.7,rgba(255,170,235,0.16)); starGlowA.addColorStop(1,rgba(0,0,0,0));
      ctx.fillStyle=starGlowA; buildSparklePathP(focalX,focalY,starOuter*1.22,starInner*1.22); ctx.fill();
      const starFill=ctx.createRadialGradient(focalX,focalY,0,focalX,focalY,starOuter);
      starFill.addColorStop(0,rgba(255,255,255,1)); starFill.addColorStop(0.28,rgba(255,255,255,0.96));
      starFill.addColorStop(0.62,rgba(255,230,245,0.82)); starFill.addColorStop(0.86,rgba(190,225,255,0.52));
      starFill.addColorStop(1,rgba(160,215,255,0.18));
      ctx.fillStyle=starFill; buildSparklePathP(focalX,focalY,starOuter,starInner); ctx.fill();
      ctx.strokeStyle=rgba(255,255,255,0.28); ctx.lineWidth=1.1; buildSparklePathP(focalX,focalY,starOuter,starInner); ctx.stroke();
      const verticalH=Math.min(height*0.42,360), verticalW=Math.max(6,Math.min(width*0.014,16));
      const vertFlare=ctx.createLinearGradient(focalX,focalY-verticalH*0.5,focalX,focalY+verticalH*0.5);
      vertFlare.addColorStop(0,rgba(255,255,255,0)); vertFlare.addColorStop(0.18,rgba(255,185,235,0.22));
      vertFlare.addColorStop(0.5,rgba(255,255,255,0.78)); vertFlare.addColorStop(0.82,rgba(180,215,255,0.22));
      vertFlare.addColorStop(1,rgba(255,255,255,0));
      ctx.fillStyle=vertFlare; ctx.fillRect(focalX-verticalW*0.5,focalY-verticalH*0.5,verticalW,verticalH);
      const horizontalW=width*0.7;
      const horizFlare=ctx.createLinearGradient(focalX-horizontalW*0.5,focalY,focalX+horizontalW*0.5,focalY);
      horizFlare.addColorStop(0,rgba(255,255,255,0)); horizFlare.addColorStop(0.2,rgba(90,165,255,0.05));
      horizFlare.addColorStop(0.42,rgba(255,180,235,0.12)); horizFlare.addColorStop(0.5,rgba(255,255,255,0.34));
      horizFlare.addColorStop(0.58,rgba(190,220,255,0.12)); horizFlare.addColorStop(0.8,rgba(255,120,220,0.05));
      horizFlare.addColorStop(1,rgba(255,255,255,0));
      ctx.fillStyle=horizFlare; ctx.fillRect(focalX-horizontalW*0.5,focalY-2.5,horizontalW,5);
      const innerGlow=ctx.createRadialGradient(focalX,focalY,0,focalX,focalY,starOuter*0.9);
      innerGlow.addColorStop(0,rgba(255,255,255,0.96)); innerGlow.addColorStop(0.35,rgba(255,255,255,0.55));
      innerGlow.addColorStop(0.8,rgba(180,225,255,0.12)); innerGlow.addColorStop(1,rgba(0,0,0,0));
      ctx.fillStyle=innerGlow; ctx.beginPath(); ctx.arc(focalX,focalY,starOuter*0.9,0,Math.PI*2); ctx.fill();
      ctx.restore();
    }
    function drawVignetteP(p) {
      const sx=p.currentX*depth.vignette, sy=p.currentY*depth.vignette;
      const vig=ctx.createRadialGradient(cx+sx,cy+sy,Math.min(width,height)*0.2,cx+sx,cy+sy,Math.max(width,height)*0.8);
      vig.addColorStop(0,"rgba(0,0,0,0)"); vig.addColorStop(0.65,"rgba(0,0,0,0.08)"); vig.addColorStop(1,"rgba(0,0,0,0.42)");
      ctx.fillStyle=vig; ctx.fillRect(0,0,width,height);
    }
    function frame(now) {
      const dt = Math.min(32, now - lastTime); lastTime = now; time += dt;
      ctx.clearRect(0,0,width,height);
      drawBackgroundGradient(); drawNebulaClouds(time); drawSlowMovingStars(time); drawStreaks(time); drawCentreFlare(time); drawVignette();
      animationRef.current = requestAnimationFrame(frame);
    }
    function frameParallax(now) {
      const dt=Math.min(32,now-lastTime); lastTime=now; time+=dt;
      const p=updateParallax();
      ctx.clearRect(0,0,width,height);
      drawBackgroundGradientP(p); drawCentreFlareP(time,p); drawNebulaCloudsP(time,p); drawSlowMovingStarsP(time,p); drawStreaksP(time,p); drawVignetteP(p);
      animationRef.current=requestAnimationFrame(frameParallax);
    }

    function mulberry32(a) {
      return function() { let t=(a+=0x6d2b79f5); t=Math.imul(t^(t>>>15),t|1); t^=t+Math.imul(t^(t>>>7),t|61); return((t^(t>>>14))>>>0)/4294967296; };
    }
    let rng = mulberry32(1337);
    const srand = (min, max) => rng()*(max-min)+min;
    function resizeStatic() {
      const rect=canvas.getBoundingClientRect();
      width=Math.max(1,Math.floor(rect.width||window.innerWidth)); height=Math.max(1,Math.floor(rect.height||window.innerHeight));
      dpr=Math.min(window.devicePixelRatio||1,2);
      canvas.width=Math.floor(width*dpr); canvas.height=Math.floor(height*dpr);
      canvas.style.width=`${width}px`; canvas.style.height=`${height}px`;
      ctx.setTransform(dpr,0,0,dpr,0,0); cx=width*0.5; cy=height*0.5; drawStatic();
    }
    function drawBackgroundGradientS() {
      const bg=ctx.createLinearGradient(0,0,width,height);
      bg.addColorStop(0,"rgba(2,6,18,1)"); bg.addColorStop(0.28,"rgba(5,12,30,1)");
      bg.addColorStop(0.55,"rgba(9,8,24,1)"); bg.addColorStop(0.78,"rgba(20,7,28,1)");
      bg.addColorStop(1,"rgba(6,2,12,1)");
      ctx.fillStyle=bg; ctx.fillRect(0,0,width,height);
    }
    function drawNebulaCloudsS() {
      ctx.save(); ctx.globalCompositeOperation="screen";
      const leftGrad=ctx.createRadialGradient(width*0.18,height*0.48,10,width*0.18,height*0.48,width*0.55);
      leftGrad.addColorStop(0,`rgba(40,140,255,${0.18*nebulaStrength})`);
      leftGrad.addColorStop(0.28,`rgba(20,105,230,${0.12*nebulaStrength})`);
      leftGrad.addColorStop(0.62,`rgba(8,42,120,${0.09*nebulaStrength})`);
      leftGrad.addColorStop(1,"rgba(0,0,0,0)");
      ctx.fillStyle=leftGrad; ctx.fillRect(0,0,width,height);
      const rightGrad=ctx.createRadialGradient(width*0.8,height*0.5,12,width*0.8,height*0.5,width*0.48);
      rightGrad.addColorStop(0,`rgba(255,100,230,${0.2*nebulaStrength})`);
      rightGrad.addColorStop(0.34,`rgba(175,70,255,${0.14*nebulaStrength})`);
      rightGrad.addColorStop(0.7,`rgba(95,25,160,${0.08*nebulaStrength})`);
      rightGrad.addColorStop(1,"rgba(0,0,0,0)");
      ctx.fillStyle=rightGrad; ctx.fillRect(0,0,width,height);
      const blobs=[
        {x:width*0.16,y:height*0.33,rx:width*0.28,ry:height*0.16,c1:"rgba(80,180,255,0.06)",c2:"rgba(20,40,100,0)"},
        {x:width*0.26,y:height*0.72,rx:width*0.24,ry:height*0.12,c1:"rgba(0,190,255,0.05)",c2:"rgba(0,0,0,0)"},
        {x:width*0.78,y:height*0.33,rx:width*0.22,ry:height*0.14,c1:"rgba(255,90,200,0.07)",c2:"rgba(0,0,0,0)"},
        {x:width*0.86,y:height*0.66,rx:width*0.26,ry:height*0.16,c1:"rgba(180,70,255,0.08)",c2:"rgba(0,0,0,0)"},
      ];
      blobs.forEach(b => {
        const driftX=srand(-18,18), driftY=srand(-12,12);
        const g=ctx.createRadialGradient(b.x+driftX,b.y+driftY,0,b.x+driftX,b.y+driftY,Math.max(b.rx,b.ry));
        g.addColorStop(0,b.c1); g.addColorStop(1,b.c2);
        ctx.save(); ctx.translate(b.x+driftX,b.y+driftY); ctx.scale(1,b.ry/b.rx);
        ctx.beginPath(); ctx.arc(0,0,b.rx,0,Math.PI*2); ctx.closePath(); ctx.fillStyle=g; ctx.fill(); ctx.restore();
      });
      ctx.restore();
    }
    function drawStarsS() {
      ctx.save(); ctx.globalCompositeOperation="screen";
      const total=Math.floor(starCount*intensity);
      for (let i=0;i<total;i++) {
        const sideBias=rng(), x=srand(0,width), y=srand(0,height);
        const base=rng()**1.6, r=srand(0.35,1.8)*(0.7+base);
        const a=srand(0.15,0.95)*srand(0.82,1);
        let tint="rgba(255,255,255,1)";
        if (sideBias<0.46) tint=`rgba(${Math.floor(srand(140,210))},${Math.floor(srand(190,240))},255,1)`;
        else if (sideBias>0.62) tint=`rgba(255,${Math.floor(srand(150,205))},${Math.floor(srand(220,255))},1)`;
        ctx.fillStyle=tint.replace(/,\s*1\)$/,`,${a})`);
        ctx.beginPath(); ctx.arc(x,y,r,0,Math.PI*2); ctx.fill();
        if (r>1.15) {
          ctx.strokeStyle=rgba(255,255,255,a*0.2); ctx.lineWidth=0.6;
          ctx.beginPath(); ctx.moveTo(x-r*2.1,y); ctx.lineTo(x+r*2.1,y);
          ctx.moveTo(x,y-r*2.1); ctx.lineTo(x,y+r*2.1); ctx.stroke();
        }
      }
      ctx.restore();
    }
    function drawStreaksS() {
      ctx.save(); ctx.globalCompositeOperation="lighter"; ctx.lineCap="round";
      const total=Math.floor(streakCount*intensity);
      const maxRadius=Math.hypot(width,height)*0.75;
      for (let i=0;i<total;i++) {
        const hueWeight=rng();
        const baseAngle=Math.atan2(srand(-height*0.55,height*0.55),srand(-width*0.55,width*0.55));
        const angle=baseAngle+srand(-0.3,0.3);
        const z=srand(0.04,1), eased=z*z, radius=lerp(6,maxRadius,eased);
        const x=cx+Math.cos(angle)*radius, y=cy+Math.sin(angle)*radius;
        const dirX=x-cx, dirY=y-cy, dirLen=Math.max(1,Math.hypot(dirX,dirY));
        const ux=dirX/dirLen, uy=dirY/dirLen;
        const widthPx=srand(0.5,2.6)*(0.3+eased*1.4);
        const trail=srand(22,180)*(0.18+eased*1.75);
        const x2=x-ux*trail, y2=y-uy*trail;
        const alpha=clamp(srand(0.12,0.85)*(0.3+eased*1.15),0.05,1);
        let colour=[165,110,255];
        if (hueWeight<0.18) colour=[255,255,255];
        else if (hueWeight<0.39) colour=[95,205,255];
        else if (hueWeight<0.56) colour=[0,255,220];
        else if (hueWeight<0.68) colour=[120,255,160];
        else if (hueWeight<0.84) colour=[255,90,210];
        const [r,g,b]=colour;
        const grad=ctx.createLinearGradient(x2,y2,x,y);
        grad.addColorStop(0,rgba(255,255,255,0)); grad.addColorStop(0.45,rgba(r,g,b,alpha*0.33)); grad.addColorStop(1,rgba(r,g,b,alpha));
        ctx.strokeStyle=grad; ctx.lineWidth=widthPx;
        ctx.beginPath(); ctx.moveTo(x2,y2); ctx.lineTo(x,y); ctx.stroke();
      }
      ctx.restore();
    }
    function buildSparklePathS(x, y, sizeOuter, sizeInner) {
      ctx.beginPath();
      ctx.moveTo(x,y-sizeOuter);
      ctx.quadraticCurveTo(x+sizeInner*0.45,y-sizeInner*0.75,x+sizeOuter,y);
      ctx.quadraticCurveTo(x+sizeInner*0.75,y+sizeInner*0.45,x,y+sizeOuter);
      ctx.quadraticCurveTo(x-sizeInner*0.45,y+sizeInner*0.75,x-sizeOuter,y);
      ctx.quadraticCurveTo(x-sizeInner*0.75,y-sizeInner*0.45,x,y-sizeOuter);
      ctx.closePath();
    }
    function drawCentreFlareS() {
      ctx.save(); ctx.globalCompositeOperation="screen";
      const minSide=Math.min(width,height);
      const outerGlow=ctx.createRadialGradient(cx,cy,0,cx,cy,minSide*0.24);
      outerGlow.addColorStop(0,rgba(255,255,255,0.46)); outerGlow.addColorStop(0.08,rgba(210,235,255,0.22));
      outerGlow.addColorStop(0.18,rgba(255,160,235,0.16)); outerGlow.addColorStop(0.28,rgba(120,180,255,0.11));
      outerGlow.addColorStop(1,rgba(0,0,0,0));
      ctx.fillStyle=outerGlow; ctx.beginPath(); ctx.arc(cx,cy,minSide*0.24,0,Math.PI*2); ctx.fill();
      const starOuter=clamp(minSide*0.078,36,82), starInner=starOuter*0.34;
      const starGlowA=ctx.createRadialGradient(cx,cy,0,cx,cy,starOuter*1.45);
      starGlowA.addColorStop(0,rgba(255,255,255,0.78)); starGlowA.addColorStop(0.42,rgba(255,245,255,0.28));
      starGlowA.addColorStop(0.7,rgba(255,170,235,0.16)); starGlowA.addColorStop(1,rgba(0,0,0,0));
      ctx.fillStyle=starGlowA; buildSparklePathS(cx,cy,starOuter*1.22,starInner*1.22); ctx.fill();
      const starFill=ctx.createRadialGradient(cx,cy,0,cx,cy,starOuter);
      starFill.addColorStop(0,rgba(255,255,255,1)); starFill.addColorStop(0.28,rgba(255,255,255,0.96));
      starFill.addColorStop(0.62,rgba(255,230,245,0.82)); starFill.addColorStop(0.86,rgba(190,225,255,0.52));
      starFill.addColorStop(1,rgba(160,215,255,0.18));
      ctx.fillStyle=starFill; buildSparklePathS(cx,cy,starOuter,starInner); ctx.fill();
      ctx.strokeStyle=rgba(255,255,255,0.28); ctx.lineWidth=1.1; buildSparklePathS(cx,cy,starOuter,starInner); ctx.stroke();
      const verticalH=Math.min(height*0.42,360), verticalW=Math.max(6,Math.min(width*0.014,16));
      const vertFlare=ctx.createLinearGradient(cx,cy-verticalH*0.5,cx,cy+verticalH*0.5);
      vertFlare.addColorStop(0,rgba(255,255,255,0)); vertFlare.addColorStop(0.18,rgba(255,185,235,0.22));
      vertFlare.addColorStop(0.5,rgba(255,255,255,0.78)); vertFlare.addColorStop(0.82,rgba(180,215,255,0.22));
      vertFlare.addColorStop(1,rgba(255,255,255,0));
      ctx.fillStyle=vertFlare; ctx.fillRect(cx-verticalW*0.5,cy-verticalH*0.5,verticalW,verticalH);
      const horizontalW=width*0.7;
      const horizFlare=ctx.createLinearGradient(cx-horizontalW*0.5,cy,cx+horizontalW*0.5,cy);
      horizFlare.addColorStop(0,rgba(255,255,255,0)); horizFlare.addColorStop(0.2,rgba(90,165,255,0.05));
      horizFlare.addColorStop(0.42,rgba(255,180,235,0.12)); horizFlare.addColorStop(0.5,rgba(255,255,255,0.34));
      horizFlare.addColorStop(0.58,rgba(190,220,255,0.12)); horizFlare.addColorStop(0.8,rgba(255,120,220,0.05));
      horizFlare.addColorStop(1,rgba(255,255,255,0));
      ctx.fillStyle=horizFlare; ctx.fillRect(cx-horizontalW*0.5,cy-2.5,horizontalW,5);
      const innerGlow=ctx.createRadialGradient(cx,cy,0,cx,cy,starOuter*0.9);
      innerGlow.addColorStop(0,rgba(255,255,255,0.96)); innerGlow.addColorStop(0.35,rgba(255,255,255,0.55));
      innerGlow.addColorStop(0.8,rgba(180,225,255,0.12)); innerGlow.addColorStop(1,rgba(0,0,0,0));
      ctx.fillStyle=innerGlow; ctx.beginPath(); ctx.arc(cx,cy,starOuter*0.9,0,Math.PI*2); ctx.fill();
      ctx.restore();
    }
    function drawVignetteS() {
      const vig=ctx.createRadialGradient(cx,cy,Math.min(width,height)*0.2,cx,cy,Math.max(width,height)*0.8);
      vig.addColorStop(0,"rgba(0,0,0,0)"); vig.addColorStop(0.65,"rgba(0,0,0,0.08)"); vig.addColorStop(1,"rgba(0,0,0,0.42)");
      ctx.fillStyle=vig; ctx.fillRect(0,0,width,height);
    }
    function drawStatic() {
      rng=mulberry32(1337);
      ctx.clearRect(0,0,width,height);
      drawBackgroundGradientS(); drawNebulaCloudsS(); drawStarsS(); drawStreaksS(); drawCentreFlareS(); drawVignetteS();
    }

    if (staticMode) {
      resizeStatic();
      const ro = new ResizeObserver(resizeStatic); ro.observe(canvas); window.addEventListener("resize", resizeStatic);
      return () => { ro.disconnect(); window.removeEventListener("resize", resizeStatic); };
    }
    resize();
    const ro = new ResizeObserver(resize); ro.observe(canvas); window.addEventListener("resize", resize);
    if (parallax) {
      window.addEventListener("pointermove", onPointerMove, { passive: true });
      window.addEventListener("pointerleave", onPointerLeave);
      window.addEventListener("blur", onPointerLeave);
      animationRef.current = requestAnimationFrame(frameParallax);
      return () => {
        cancelAnimationFrame(animationRef.current); ro.disconnect(); window.removeEventListener("resize", resize);
        window.removeEventListener("pointermove", onPointerMove);
        window.removeEventListener("pointerleave", onPointerLeave);
        window.removeEventListener("blur", onPointerLeave);
      };
    }
    animationRef.current = requestAnimationFrame(frame);
    return () => { cancelAnimationFrame(animationRef.current); ro.disconnect(); window.removeEventListener("resize", resize); };
  }, [intensity, speed, starCount, streakCount, nebulaStrength, starDriftSpeed, parallaxStrength, parallaxSmoothing, parallax, staticMode]);

  return (
    <canvas ref={canvasRef} className={className} aria-hidden="true"
      style={{ width:"100%", height:"100%", display:"block", background:"transparent", pointerEvents:"none" }} />
  );
}

// Per-theme colours for WIN and LOSE wheel segments. Shared theme system:
// the page background reads the same palette (e.g. casino green=win/red=lose)
// so nothing is hardcoded per element.
const THEME_COLORS = {
  default:         { win: ['#550088', '#AA00FF'], lose: ['#7a3300', '#FF6600'] },
  fire:            { win: ['#993300', '#FF6600'], lose: ['#440000', '#CC2200'] },
  ice:             { win: ['#005577', '#00CCFF'], lose: ['#002244', '#0066CC'] },
  neon:            { win: ['#440088', '#CC00FF'], lose: ['#003300', '#00FF66'] },
  void:            { win: ['#0a0a1a', '#6633FF'], lose: ['#0d0010', '#330066'] },
  gold:            { win: ['#7a5c00', '#FFE566'], lose: ['#3d2000', '#CC8800'] },
  bioluminescence: { win: ['#003a4d', '#00E5FF'], lose: ['#4d1020', '#FF6B6B'] },
  night_ocean:     { win: ['#1a0d4d', '#5533FF'], lose: ['#3d0011', '#CC2244'] },
  wormhole:        { win: ['#1a0044', '#BB88FF'], lose: ['#3d0022', '#FF44AA'] },
  casino:          { win: ['#063d1f', '#28e070'], lose: ['#4a0808', '#ff4040'] },
};

// ── Casino Background (Season 8) ─────────────────────────────────────────────
// Thin React wrapper around the shared vanilla scene module
// (static/js/casino-bg.js, loaded as window.createCasinoScene). Colours come
// from THEME_COLORS.casino so the wheel and background share one theme.
function CasinoBackground({ lowSpec = false }) {
  const canvasRef = useRef(null);
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !window.createCasinoScene) return;
    const scene = window.createCasinoScene(canvas, {
      lowSpec,
      palette: { win: THEME_COLORS.casino.win[1], lose: THEME_COLORS.casino.lose[1] },
    });
    return () => scene && scene.stop();
  }, [lowSpec]);
  return (
    <canvas ref={canvasRef} aria-hidden="true"
      style={{ width:"100%", height:"100%", display:"block", background:"transparent", pointerEvents:"none" }} />
  );
}

// ── Draw main wheel ────────────────────────────────────────────────────────
// Wheel mode percentages mirrored from wheel_modes.py — used for drawing only.
// T80: the server now supplies wheel_probabilities in /api/state and the
// spin response. drawWheel() prefers those values when provided; this
// table is kept as a backward-compat fallback (per the task note: "If the
// table is referenced in other places, keep backward compat").
const WHEEL_MODE_DRAW = {
  steady:      { win_pct: 70, lose_pct: 28, jackpot_pct: 2 },
  volatile:    { win_pct: 45, lose_pct: 50, jackpot_pct: 5 },
  inverted:    { win_pct: 35, lose_pct: 60, jackpot_pct: 5 },
  gravity:     { win_pct: 55, lose_pct: 40, jackpot_pct: 5 },
  mirror:      { win_pct: 65, lose_pct: 30, jackpot_pct: 5 },
  singularity: { win_pct: 75, lose_pct: 10, jackpot_pct: 15 },
};

function drawWheel(canvas, theme = 'default', wheelMode = 'steady', wheelProbabilities = null) {
  const ctx = canvas.getContext('2d');
  const size = canvas.width;
  const cx = size / 2, cy = size / 2, r = size / 2 - 4;

  ctx.clearRect(0, 0, size, size);

  const colors = THEME_COLORS[theme] || THEME_COLORS.default;

  // T80: prefer the server-supplied wheel_probabilities when available
  // (covers gravity drift, which shifts after every spin). Fall back to
  // the static WHEEL_MODE_DRAW table for backward compatibility.
  const fallback = WHEEL_MODE_DRAW[wheelMode] || WHEEL_MODE_DRAW.steady;
  const modeConfig = wheelProbabilities || fallback;
  const winPct  = modeConfig.win_pct;
  const losePct = modeConfig.lose_pct;
  const jpPct   = modeConfig.jackpot_pct;

  // T80 (T79 AC#11): in inverted mode the labels swap so the player
  // visually sees which outcome is the GOOD one. "LOSE" is rendered with
  // the bright (win-coloured) palette and "WIN" with the dim (lose-coloured)
  // palette; the arc spans are unchanged.
  const isInverted = (wheelMode === 'inverted');
  const winLabel  = isInverted ? 'LOSE' : 'WIN';
  const loseLabel = isInverted ? 'WIN'  : 'LOSE';

  // Compute arc spans from mode percentages.
  // Segments radiate clockwise from -π/2 (12-o'clock): WIN → LOSE → JACKPOT
  const winSpan  = winPct  / 100 * Math.PI * 2;
  const loseSpan = losePct / 100 * Math.PI * 2;
  const jpSpan   = jpPct   / 100 * Math.PI * 2;

  const origin = -Math.PI / 2;  // 12-o'clock start
  // Palette swap: in inverted mode the "good" outcome is LOSE, so the
  // LOSE segment uses the bright win-coloured palette and the WIN segment
  // uses the dim lose-coloured palette. The arc spans are unchanged.
  const winSegPalette  = isInverted ? colors.lose : colors.win;
  const loseSegPalette = isInverted ? colors.win  : colors.lose;
  const segments = [
    { label: winLabel,  color: winSegPalette[0],  bright: winSegPalette[1],  start: origin,                                  span: winSpan  },
    { label: loseLabel, color: loseSegPalette[0], bright: loseSegPalette[1], start: origin + winSpan,                        span: loseSpan },
    { label: '★',       color: '#4a3800',          bright: '#FFD700',         start: origin + winSpan + loseSpan,             span: jpSpan   },
  ];

  segments.forEach(seg => {
    const end = seg.start + seg.span;

    // Fill
    const grad = ctx.createRadialGradient(cx, cy, r * 0.1, cx, cy, r);
    grad.addColorStop(0, seg.bright);
    grad.addColorStop(1, seg.color);
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, r, seg.start, end);
    ctx.closePath();
    ctx.fillStyle = grad;
    ctx.fill();

    // Segment border
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, r, seg.start, end);
    ctx.closePath();
    ctx.strokeStyle = '#222';
    ctx.lineWidth = 3;
    ctx.stroke();

    // Dividing line at start of segment
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(cx + r * Math.cos(seg.start), cy + r * Math.sin(seg.start));
    ctx.strokeStyle = '#111';
    ctx.lineWidth = 4;
    ctx.stroke();

    // Label — omit if segment is too narrow for text
    const midAngle = seg.start + seg.span / 2;
    const spanDeg  = seg.span * 180 / Math.PI;
    if (spanDeg >= 8) {
      ctx.save();
      ctx.translate(cx, cy);
      ctx.rotate(midAngle);
      ctx.textAlign    = 'center';
      ctx.textBaseline = 'middle';
      ctx.shadowColor  = 'rgba(0,0,0,0.8)';
      ctx.shadowBlur   = 8;
      if (spanDeg < 25) {
        // Tiny segment — small symbol only
        ctx.font      = `bold ${size * 0.07}px 'Oswald', Arial Black, sans-serif`;
        ctx.fillStyle = '#FFF';
        ctx.fillText(seg.label === '★' ? '★' : seg.label[0], r * 0.55, 0);
      } else {
        ctx.font      = `bold ${size * 0.1}px 'Oswald', Arial Black, sans-serif`;
        ctx.fillStyle = '#FFF';
        ctx.fillText(seg.label, r * 0.55, 0);
      }
      ctx.restore();
    }

    // Rim dots — scaled to segment size
    const dotCount = Math.max(2, Math.round(seg.span / (Math.PI * 2) * 28));
    for (let i = 0; i <= dotCount; i++) {
      const a  = seg.start + seg.span * (i / dotCount);
      const dr = r * 0.88;
      ctx.beginPath();
      ctx.arc(cx + dr * Math.cos(a), cy + dr * Math.sin(a), 5, 0, Math.PI * 2);
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

  // WIN segment (cyan)
  const gWin = ctx.createRadialGradient(cx, cy, r * 0.1, cx, cy, r);
  gWin.addColorStop(0, '#55EEEE');
  gWin.addColorStop(1, '#006666');
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
  // T15: Use shared format_wins() from format.js for consistency
  if (typeof window.format_wins === 'function') return window.format_wins(n);
  // Fallback if format.js not loaded
  if (!isFinite(n) || isNaN(n)) return '0';
  if (n >= 1e15) return n.toExponential(2).replace('e+', 'e');
  if (n >= 1e12) return parseFloat((n / 1e12).toPrecision(3)) + 'T';
  if (n >= 1e9)  return parseFloat((n / 1e9) .toPrecision(3)) + 'B';
  if (n >= 1e6)  return parseFloat((n / 1e6) .toPrecision(3)) + 'M';
  if (n >= 10e3) return parseFloat((n / 1e3) .toPrecision(3)) + 'K';
  return String(n);
}

// ── Hiatus mode — set to false to re-enable the full game ─────────────────
const HIATUS_MODE        = false;
const HIATUS_END         = new Date('2026-05-01T23:59:59'); // Next Friday 11:59 pm
const HIATUS_PAST_SEASON = 6;  // season that just ended

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
const CONFETTI_COLORS = ['#FFD700','#FF6600','#FF3333','#00FF88','#AA00FF','#FF00FF','#FFFFFF'];
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
function GuardWheel({ blocked, speedMult = 1.0, onComplete, contained = false }) {
  const canvasRef = useRef(null);
  const [guardRotation, setGuardRotation] = useState(0);
  const [revealed, setRevealed] = useState(false);
  const [transDur, setTransDur] = useState(1.8);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (canvas) drawGuardWheel(canvas);

    const dur = 1.8 * speedMult;
    setTransDur(dur);

    // WIN segment centered at canvas angle 0° (right side).
    // CSS rotation 270° brings right side to 12 o'clock (pointer).
    // FAIL centered at canvas 180°; CSS rotation 90° brings it to pointer.
    const baseSpins = 4 * 360;
    const targetAngle = blocked ? 270 : 90;
    // Delay so browser paints rotation=0 before transitioning (otherwise no animation)
    const spinTimer     = setTimeout(() => setGuardRotation(baseSpins + targetAngle), 50);
    const revealTimer   = setTimeout(() => setRevealed(true), Math.round(2000 * speedMult));
    const completeTimer = setTimeout(() => onComplete(), Math.round(3400 * speedMult));
    return () => { clearTimeout(spinTimer); clearTimeout(revealTimer); clearTimeout(completeTimer); };
  }, []); // eslint-disable-line

  return (
    <div className={contained ? 'guard-overlay guard-overlay--contained' : 'guard-overlay'}>
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
              transition: `transform ${transDur}s cubic-bezier(0.17, 0.67, 0.12, 0.99)`,
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

// ── Fish Catalog (client-side mirror of server FISH_CATALOG) ──────────────
const FISH_CATALOG_CLIENT = [
  { id: 'minnow',     emoji: '🐟', name: 'Minnow',     value:   1, tier: 'Common'    },
  { id: 'clownfish',  emoji: '🐠', name: 'Clownfish',  value:   3, tier: 'Common'    },
  { id: 'pufferfish', emoji: '🐡', name: 'Pufferfish', value:   3, tier: 'Common'    },
  { id: 'shrimp',     emoji: '🦐', name: 'Shrimp',     value:   2, tier: 'Common'    },
  { id: 'crab',       emoji: '🦀', name: 'Crab',       value:   8, tier: 'Uncommon'  },
  { id: 'squid',      emoji: '🦑', name: 'Squid',      value:   8, tier: 'Uncommon'  },
  { id: 'octopus',    emoji: '🐙', name: 'Octopus',    value:  12, tier: 'Uncommon'  },
  { id: 'lobster',    emoji: '🦞', name: 'Lobster',    value:  20, tier: 'Rare'      },
  { id: 'dolphin',    emoji: '🐬', name: 'Dolphin',    value:  30, tier: 'Rare'      },
  { id: 'shark',      emoji: '🦈', name: 'Shark',      value:  40, tier: 'Rare'      },
  { id: 'whale',      emoji: '🐋', name: 'Blue Whale', value:  75, tier: 'Legendary' },
  { id: 'mermaid',    emoji: '🧜', name: 'Mermaid',    value: 120, tier: 'Legendary' },
  { id: 'lucky',      emoji: '⭐', name: 'Lucky Fish', value: 100, tier: 'Legendary' },
];

// ── Fish Encyclopaedia ────────────────────────────────────────────────────
function FishEncyclopedia({ caughtSpecies, onClose }) {
  const discovered = new Set(caughtSpecies || []);
  const count = discovered.size;
  const TIER_ORDER = { Common: 0, Uncommon: 1, Rare: 2, Legendary: 3 };
  const sorted = [...FISH_CATALOG_CLIENT].sort((a, b) => TIER_ORDER[a.tier] - TIER_ORDER[b.tier]);
  return (
    <div className="encyclopedia-overlay" onClick={onClose}>
      <div className="encyclopedia-card" onClick={e => e.stopPropagation()}>
        <div className="encyclopedia-title">📖 Fish Encyclopaedia</div>
        <div className="encyclopedia-progress">Discovered: {count} / {FISH_CATALOG_CLIENT.length}</div>
        <button className="encyclopedia-close-btn" onClick={onClose}>✕</button>
        <div className="encyclopedia-grid">
          {sorted.map(fish => {
            const known = discovered.has(fish.id);
            return (
              <div key={fish.id} className={`encyclopedia-entry${known ? ' unlocked' : ' locked'}`}>
                <span className="encyclopedia-entry-emoji">{known ? fish.emoji : '❓'}</span>
                <span className="encyclopedia-entry-name">{known ? fish.name : '???'}</span>
                <span className={`encyclopedia-entry-tier ${fish.tier}`}>{fish.tier}</span>
                <span className="encyclopedia-entry-value">{known ? `${fish.value} 🐟` : '???'}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// ── Fishing Panel ─────────────────────────────────────────────────────────
function FishingPanel({ fishClicks, fishData, caughtSpecies, fishingLuckyNext, ownedItems, fishPanelScale, onFishBucksUpdate, onCaughtSpeciesUpdate, onFishCaught, onOnboardingAdvance }) {
  const [phase, setPhase]         = useState('idle'); // idle | waiting | bite | reeling | success | miss
  const [biteAt, setBiteAt]       = useState(null);
  const [expiresAt, setExpiresAt] = useState(null);
  const [lastCatch, setLastCatch] = useState(null);
  const [missReason, setMissReason] = useState('late'); // 'late' | 'early'
  const [luckyNextActive, setLuckyNextActive] = useState(fishingLuckyNext || false);
  const [autoCast, setAutoCast]   = useState(false);
  const [autoFish, setAutoFish]   = useState(false);
  const [autoFishPopup, setAutoFishPopup] = useState(null); // { key, type:'hit'|'miss', emoji?, value? }
  const autoFishRef               = useRef(false);
  const autoCastRef               = useRef(false);
  const phaseRef                  = useRef('idle');
  const biteTimerRef              = useRef(null);
  const missTimerRef              = useRef(null);
  const pollSessionRef            = useRef(0);
  const autoFishIntervalRef       = useRef(null);
  const autoFishPopupTimerRef     = useRef(null);
  const reelInFlightRef           = useRef(false);
  const consecutiveMissesRef      = useRef(0);
  const autoFishPopupKeyRef       = useRef(0);

  const hasAutoCast   = ownedItems.includes('auto_cast');
  const hasAutoFisher = ownedItems.includes('autofisher_1');
  const { emoji: fisherEmoji } = fishData || { emoji: '🐟' };
  const scale = fishPanelScale || 1.0;

  useEffect(() => { autoFishRef.current = autoFish;  }, [autoFish]);
  useEffect(() => { autoCastRef.current = autoCast;  }, [autoCast]);
  useEffect(() => { phaseRef.current    = phase;     }, [phase]);
  useEffect(() => { setLuckyNextActive(fishingLuckyNext || false); }, [fishingLuckyNext]);

  const countMiss = useCallback(() => {
    if (!autoCastRef.current) return;
    consecutiveMissesRef.current += 1;
    if (consecutiveMissesRef.current >= 3) {
      setAutoCast(false);
      consecutiveMissesRef.current = 0;
    }
  }, []);

  const showAutoFishPopup = useCallback((popup) => {
    if (autoFishPopupTimerRef.current) clearTimeout(autoFishPopupTimerRef.current);
    autoFishPopupKeyRef.current += 1;
    setAutoFishPopup({ ...popup, key: autoFishPopupKeyRef.current });
    const dur = popup.type === 'hit' ? 2000 : 1500;
    autoFishPopupTimerRef.current = setTimeout(() => setAutoFishPopup(null), dur);
  }, []);

  // Auto-fish tick loop — fires every 6 s (half-speed vs manual fishing)
  useEffect(() => {
    if (!autoFish) {
      clearInterval(autoFishIntervalRef.current);
      if (autoFishPopupTimerRef.current) clearTimeout(autoFishPopupTimerRef.current);
      return;
    }
    const tick = async () => {
      if (!autoFishRef.current) return;
      const { ok, data } = await apiGame('/api/auto-fish-tick', { method: 'POST', body: '{}' });
      if (!ok || !data.result) return;
      if (data.result === 'hit') {
        const fish = FISH_CATALOG_CLIENT.find(f => f.id === data.species);
        const emoji = fish ? fish.emoji : '🐟';
        const name  = fish ? fish.name  : data.species;
        setLastCatch({ emoji, name, value: data.value, isNew: !!data.first_catch, isLucky: false, doubled: false });
        onFishBucksUpdate(data.fish_clicks);
        if (data.first_catch) onCaughtSpeciesUpdate(data.species);
        if (onFishCaught) onFishCaught();
        showAutoFishPopup({ type: 'hit', emoji, value: data.value, isNew: !!data.first_catch });
      } else {
        showAutoFishPopup({ type: 'miss' });
      }
    };
    tick();
    autoFishIntervalRef.current = setInterval(tick, 6000);
    return () => clearInterval(autoFishIntervalRef.current);
  }, [autoFish, showAutoFishPopup]); // eslint-disable-line

  // Auto-cast: trigger cast when idle
  useEffect(() => {
    if (!autoCast || autoFish || phase !== 'idle') return;
    const t = setTimeout(() => {
      if (autoCastRef.current && !autoFishRef.current && phaseRef.current === 'idle') doCast();
    }, 600);
    return () => clearTimeout(t);
  }, [phase, autoCast, autoFish]); // eslint-disable-line

  // Poll /api/bite-poll until bite detected or window expired.
  // Uses recursive setTimeout (not setInterval) so each poll fires 250ms
  // AFTER the previous fetch completes, keeping at most 1 request in-flight.
  // pollSessionRef is a cancellation token — incremented on each new cast so
  // any in-flight poll from the previous cast exits cleanly without affecting
  // the new session. try/catch ensures a network hiccup doesn't silently
  // break the chain and leave the phase stuck on 'waiting'.
  const startBitePolling = useCallback(() => {
    if (biteTimerRef.current) clearTimeout(biteTimerRef.current);
    const mySession = ++pollSessionRef.current;

    const poll = async () => {
      if (pollSessionRef.current !== mySession) return;
      // No phaseRef check here — poll() is called immediately after setPhase('waiting')
      // but before React re-renders, so phaseRef.current is still the previous value.
      // The post-await check below runs after React has had time to update.
      try {
        const { ok, data } = await apiGame('/api/bite-poll', { method: 'POST', body: '{}' });
        if (pollSessionRef.current !== mySession) return;
        if (phaseRef.current !== 'waiting') return;
        if (ok) {
          if (data.expired) {
            setMissReason('late');
            setPhase('miss');
            countMiss();
            setTimeout(() => setPhase('idle'), 1500);
            return;
          } else if (data.bite) {
            // Use remaining_ms from server to drive the bite bar animation.
            const now = Date.now();
            setBiteAt(now);
            setExpiresAt(now + data.remaining_ms);
            setPhase('bite');
            if (missTimerRef.current) clearTimeout(missTimerRef.current);
            missTimerRef.current = setTimeout(() => {
              if (phaseRef.current === 'bite') {
                setMissReason('late');
                setPhase('miss');
                countMiss();
                setTimeout(() => setPhase('idle'), 1500);
              }
            }, data.remaining_ms);
            return;
          }
        }
      } catch (_) { /* network error — retry */ }
      if (pollSessionRef.current !== mySession) return;
      biteTimerRef.current = setTimeout(poll, 250);
    };
    poll();
  }, [countMiss]); // eslint-disable-line

  const doCast = async () => {
    if (phaseRef.current !== 'idle') return;
    const { ok } = await apiGame('/api/cast', { method: 'POST', body: '{}' });
    if (!ok) return;
    setBiteAt(null);
    setExpiresAt(null);
    setLastCatch(null);
    setMissReason('late');
    setPhase('waiting');
    if (biteTimerRef.current) clearTimeout(biteTimerRef.current);
    if (missTimerRef.current)  clearTimeout(missTimerRef.current);
    startBitePolling();
  };

  const handleCast = useCallback(() => {
    if (phase !== 'idle') return;
    doCast();
  }, [phase]); // eslint-disable-line

  // Clicking the water area while waiting = reel too early → instant miss
  const handleEarlyReel = useCallback(() => {
    if (phaseRef.current !== 'waiting') return;
    if (biteTimerRef.current) { clearTimeout(biteTimerRef.current); biteTimerRef.current = null; }
    if (missTimerRef.current) { clearTimeout(missTimerRef.current); missTimerRef.current = null; }
    setMissReason('early');
    setPhase('miss');
    countMiss();
    // Tell server to clear the session (will return miss since before bite window)
    apiGame('/api/reel', { method: 'POST', body: '{}' });
    setTimeout(() => setPhase('idle'), 1500);
  }, [countMiss]); // eslint-disable-line

  const handleReel = useCallback(async () => {
    if (phase !== 'bite' || reelInFlightRef.current) return;
    reelInFlightRef.current = true;
    if (missTimerRef.current) { clearTimeout(missTimerRef.current); missTimerRef.current = null; }
    if (biteTimerRef.current) { clearTimeout(biteTimerRef.current); biteTimerRef.current = null; }
    setPhase('reeling');
    const { ok, data } = await apiGame('/api/reel', { method: 'POST', body: '{}' });
    reelInFlightRef.current = false;
    if (!ok) { setPhase('idle'); return; }
    if (data.result === 'hit') {
      consecutiveMissesRef.current = 0;
      const fish = FISH_CATALOG_CLIENT.find(f => f.id === data.species);
      setLastCatch({ emoji: fish ? fish.emoji : '🐟', name: fish ? fish.name : data.species, value: data.value, isNew: !!data.first_catch, isLucky: data.species === 'lucky', doubled: !!data.was_doubled, preciseMult: data.precise_bonus ? data.precise_mult : null, precisePct: data.precise_pct != null ? data.precise_pct : null });
      onFishBucksUpdate(data.fish_clicks);
      if (data.first_catch) onCaughtSpeciesUpdate(data.species);
      if (data.onboarding_advance && onOnboardingAdvance) onOnboardingAdvance();
      if (onFishCaught) onFishCaught();
      setLuckyNextActive(!!data.lucky_next_active);
      setPhase('success');
      setTimeout(() => setPhase('idle'), 2000);
    } else {
      setMissReason('late');
      setPhase('miss');
      countMiss();
      setTimeout(() => setPhase('idle'), 1500);
    }
  }, [phase, countMiss]); // eslint-disable-line

  const biteWindowMs = expiresAt && biteAt ? expiresAt - biteAt : 1800;
  const inWater = phase === 'waiting' || phase === 'bite' || phase === 'reeling';

  return (
    <div className="fishing-panel" style={{ transform: `translateY(-50%) scale(${scale})` }} onClick={phase === 'bite' ? handleReel : undefined}>
      {luckyNextActive && (
        <div className="fishing-lucky-banner">⭐ Next catch DOUBLED!</div>
      )}
      <div className="fishing-fisher">
        <span className="fishing-fisher-emoji">{fisherEmoji}</span>
        <span className="fishing-rod">🎣</span>
      </div>
      <div className="fishing-water-area">
        <div className="fishing-water" onClick={e => { if (phaseRef.current === 'waiting') { e.stopPropagation(); handleEarlyReel(); } }}>
          {(inWater || autoFish) && (
            <>
              <span className="shadow-fish shadow-fish-1">🐟</span>
              <span className="shadow-fish shadow-fish-2">🐡</span>
              <span className="shadow-fish shadow-fish-3">🐠</span>
            </>
          )}
          {autoFish && (
            <span className="fishing-bobber bobber-idle">🤖</span>
          )}
          {!autoFish && inWater && (
            <span className={`fishing-bobber${phase === 'bite' ? ' bobber-bite' : ' bobber-idle'}`}>🔴</span>
          )}
        </div>
        {phase === 'bite' && (
          <div className="bite-bar-container">
            <div className="bite-bar-fill" key={expiresAt} style={{ animationDuration: `${biteWindowMs}ms` }} />
          </div>
        )}
        {phase === 'bite' && <div className="bite-hint">CLICK TO REEL!</div>}
      </div>
      <div className="fishing-controls">
        {!autoFish && (
          <button className="cast-btn" onClick={handleCast} disabled={phase !== 'idle'}>
            {phase === 'idle'    ? '🎣 CAST'    :
             phase === 'waiting' ? 'Waiting…'   :
             phase === 'bite'    ? 'TAP!'        :
             phase === 'reeling' ? 'Reeling…'   :
             phase === 'success' ? '✓ Caught!'  : 'Miss…'}
          </button>
        )}
        <div className="fishing-toggles">
          {hasAutoCast && !autoFish && (
            <label className="fishing-toggle-label">
              <input type="checkbox" checked={autoCast} onChange={e => {
                setAutoCast(e.target.checked);
                if (!e.target.checked) consecutiveMissesRef.current = 0;
              }} />
              <span className="fishing-toggle-text">Auto-Cast</span>
            </label>
          )}
          {hasAutoFisher && (
            <label className="fishing-toggle-label">
              <input type="checkbox" checked={autoFish} onChange={e => {
                setAutoFish(e.target.checked);
                if (e.target.checked) { setPhase('idle'); }
                else { apiGame('/api/auto-fish-enabled', { method: 'POST', body: JSON.stringify({ enabled: false }) }); }
              }} />
              <span className="fishing-toggle-text">Auto-Fish</span>
            </label>
          )}
        </div>
      </div>
      {/* Catch info: absolutely positioned to the right — never shifts main layout */}
      <div className="catch-side-info">
        {phase === 'success' && lastCatch ? (
          <>
            <span className="catch-side-emoji">{lastCatch.emoji}</span>
            <span className="catch-side-value">+{lastCatch.value} 🐟{lastCatch.doubled ? ' 2x!' : ''}</span>
            {lastCatch.preciseMult && <span className="catch-side-precise">🎯 {lastCatch.preciseMult}x @ {lastCatch.precisePct}%</span>}
            {lastCatch.isNew && <span className="catch-side-tag catch-side-new">NEW!</span>}
            {lastCatch.isLucky && <span className="catch-side-tag catch-side-lucky">⭐ Lucky!</span>}
          </>
        ) : phase === 'miss' ? (
          <span className="catch-side-miss">{missReason === 'early' ? 'Too early!' : 'Too slow!'}</span>
        ) : autoFish && autoFishPopup ? (
          autoFishPopup.type === 'hit' ? (
            <>
              <span className="catch-side-emoji">{autoFishPopup.emoji}</span>
              <span className="catch-side-value">+{autoFishPopup.value} 🐟</span>
              {autoFishPopup.isNew && <span className="catch-side-tag catch-side-new">NEW!</span>}
            </>
          ) : (
            <span className="catch-side-miss">No bite</span>
          )
        ) : lastCatch ? (
          <>
            <span className="catch-side-label">Last</span>
            <span className="catch-side-emoji">{lastCatch.emoji}</span>
            <span className="catch-side-value">+{lastCatch.value} 🐟</span>
            {lastCatch.preciseMult && <span className="catch-side-precise">🎯 {lastCatch.preciseMult}x @ {lastCatch.precisePct}%</span>}
          </>
        ) : null}
      </div>
    </div>
  );
}

// ── Lucky Seven Counter ───────────────────────────────────────────────────
const LuckySevenCounter = React.memo(function LuckySevenCounter({ spinCount }) {
  const progress = spinCount % 7;
  return (
    <div className="lucky-seven-counter">
      <span className="lucky-seven-counter-label">7️⃣</span>
      {[1,2,3,4,5,6,7].map(i => (
        <div key={i} className={`lucky-seven-pip${i <= progress ? ' filled' : ''}${i === 7 && progress === 0 && spinCount > 0 ? ' triggered' : ''}`} />
      ))}
    </div>
  );
});

const ProcStreakCounter = React.memo(function ProcStreakCounter({ streak }) {
  if (streak === 0) return null;
  return (
    <div className="proc-streak-counter">
      <span className="proc-streak-label">⚡</span>
      <span className="proc-streak-value">{streak}</span>
    </div>
  );
});

// ── Streak Panel ──────────────────────────────────────────────────────────
// Must match models.py bonus_mult_from_level() (Season 7: C1+C2 curve)
function bonusMultFromLevel(level) {
  const fixed = [1, 2, 4, 8, 15, 35, 70];
  if (level <= 6) return fixed[level] || 1;
  if (level <= 30) return 70 + (level - 6) * 8;
  return 262 + (level - 30) * 5;
}

const StreakPanel = React.memo(function StreakPanel({ streak, bonusmultLevel }) {
  if (Math.abs(streak) < 2) return null;
  const isWin = streak > 0;
  const count = Math.abs(streak);
  // Season 6 formula — must match models.py streak_bonus()
  const baseBonus = count < 3 ? 0
    : count <= 15 ? (1 << (count - 3))
    : count <= 35 ? 4096 + Math.pow(count - 15, 3) * 2
    : count <= 75 ? 20096 + (count - 35) * 1200
    : count <= 150 ? 68096 + (count - 75) * 600
    : 113096;
  const bonus = baseBonus * bonusMultFromLevel(bonusmultLevel || 0);
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

// ── Dice Panel ───────────────────────────────────────────────────────────
const PIP_LAYOUTS = {
  1: [[2,2]],
  2: [[1,1],[3,3]],
  3: [[1,1],[2,2],[3,3]],
  4: [[1,1],[1,3],[3,1],[3,3]],
  5: [[1,1],[1,3],[2,2],[3,1],[3,3]],
  6: [[1,1],[1,3],[2,1],[2,3],[3,1],[3,3]],
};

function Die({ value, rolling, landed }) {
  const pips = PIP_LAYOUTS[value] || [];
  const cls = `die${rolling ? ' die-rolling' : ''}${landed ? ' die-landed' : ''}`;
  return (
    <div className={cls}>
      {pips.map(([row, col], i) => (
        <div key={i} className="pip" style={{ gridRow: row, gridColumn: col }} />
      ))}
    </div>
  );
}

const DICE_TOOLTIP_W = 240;
const DICE_TOOLTIP_TEXT = 'Roll two dice to amplify your win streak. The sum (2–12) is added to your streak. Requires a win streak of 3 or more. ⚠️ Snake eyes (1+1) curses you — losing half your streak! Charges recharge every 10 minutes.';

function useDiceCountdown(diceLastRecharge, diceCharges, maxCharges) {
  const [secsToNext, setSecsToNext] = React.useState(null);
  React.useEffect(() => {
    if (!diceLastRecharge || diceCharges >= maxCharges) { setSecsToNext(null); return; }
    const rechargeAt = new Date(diceLastRecharge).getTime() + 600 * 1000;
    const tick = () => {
      const secs = Math.max(0, Math.ceil((rechargeAt - Date.now()) / 1000));
      setSecsToNext(secs);
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [diceLastRecharge, diceCharges, maxCharges]);
  return secsToNext;
}

function DicePanel({ streak, onRoll, rolling, diceResult, guardSpinning, lowSpec, diceCharges, maxDiceCharges, diceLastRecharge, hasDiceExtra, rolledSinceSpin }) {
  const [animDie1, setAnimDie1] = React.useState(1);
  const [animDie2, setAnimDie2] = React.useState(1);
  const [animDie3, setAnimDie3] = React.useState(1);
  const [landed, setLanded]     = React.useState(false);
  const [showResult, setShowResult] = React.useState(false);
  const [tipVisible, setTipVisible] = React.useState(false);
  const [tipPos, setTipPos]         = React.useState({ left: 0, bottom: 0 });
  const intervalRef = React.useRef(null);
  const descRef     = React.useRef(null);

  const secsToNext = useDiceCountdown(diceLastRecharge, diceCharges, maxDiceCharges);

  React.useEffect(() => {
    if (rolling && !lowSpec) {
      setLanded(false);
      setShowResult(false);
      intervalRef.current = setInterval(() => {
        setAnimDie1(Math.ceil(Math.random() * 6));
        setAnimDie2(Math.ceil(Math.random() * 6));
        setAnimDie3(Math.ceil(Math.random() * 6));
      }, 80);
    } else {
      clearInterval(intervalRef.current);
    }
    return () => clearInterval(intervalRef.current);
  }, [rolling, lowSpec]);

  React.useEffect(() => {
    if (diceResult) {
      setAnimDie1(diceResult.die1);
      setAnimDie2(diceResult.die2);
      if (diceResult.die3 != null) setAnimDie3(diceResult.die3);
      setLanded(true);
      setShowResult(true);
      const t = setTimeout(() => { setShowResult(false); setLanded(false); }, 3000);
      return () => clearTimeout(t);
    }
  }, [diceResult]);

  const canRoll = diceCharges >= 1 && streak >= 3 && !rolling && !guardSpinning && !rolledSinceSpin;

  const die1Val = (rolling && !lowSpec) ? animDie1 : (diceResult ? diceResult.die1 : animDie1);
  const die2Val = (rolling && !lowSpec) ? animDie2 : (diceResult ? diceResult.die2 : animDie2);
  const die3Val = (rolling && !lowSpec) ? animDie3 : (diceResult && diceResult.die3 != null ? diceResult.die3 : animDie3);

  const showTip = () => {
    if (guardSpinning) return;
    const rect = descRef.current && descRef.current.getBoundingClientRect();
    if (!rect) return;
    let left = rect.left + rect.width / 2 - DICE_TOOLTIP_W / 2;
    left = Math.max(8, Math.min(left, window.innerWidth - DICE_TOOLTIP_W - 8));
    setTipPos({ left, bottom: window.innerHeight - rect.top + 6 });
    setTipVisible(true);
  };

  const fmtCountdownSecs = (s) => {
    if (s == null) return '';
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${m}:${String(sec).padStart(2, '0')}`;
  };

  const chargesDots = Array.from({ length: maxDiceCharges }, (_, i) => (
    <span key={i} className={`dice-charge-dot${i < diceCharges ? ' charged' : ''}`}>●</span>
  ));

  let disabledReason = '';
  if (diceCharges < 1) disabledReason = 'No charges';
  else if (streak < 3) disabledReason = 'Need win streak ≥3';
  else if (rolledSinceSpin) disabledReason = 'Dice buffered — applies next spin';

  return (
    <div className="dice-panel">
      <span className="dice-panel-label">🎲 Dice Roll</span>
      <span className="dice-panel-desc" ref={descRef} onMouseEnter={showTip} onMouseLeave={() => setTipVisible(false)}>How it works ⓘ</span>
      {tipVisible && (
        <div className="dice-tooltip" style={{ left: tipPos.left, bottom: tipPos.bottom }}>{DICE_TOOLTIP_TEXT}</div>
      )}
      <div className="dice-charges-row">
        {chargesDots}
        {secsToNext != null && diceCharges < maxDiceCharges && (
          <span className="dice-recharge-timer">+1 in {fmtCountdownSecs(secsToNext)}</span>
        )}
      </div>
      {hasDiceExtra ? (
        <div className="dice-triangle">
          <div className="dice-row dice-row-top">
            <Die value={die3Val} rolling={rolling && !lowSpec} landed={landed} />
          </div>
          <div className="dice-row">
            <Die value={die1Val} rolling={rolling && !lowSpec} landed={landed} />
            <Die value={die2Val} rolling={rolling && !lowSpec} landed={landed} />
          </div>
        </div>
      ) : (
        <div className="dice-row">
          <Die value={die1Val} rolling={rolling && !lowSpec} landed={landed} />
          <Die value={die2Val} rolling={rolling && !lowSpec} landed={landed} />
        </div>
      )}
      {showResult && diceResult && (
        <span className={`dice-result-text${diceResult.cursed ? ' dice-cursed' : ''}`}>
          {diceResult.cursed_triple
            ? `💀 TRIPLE CURSE! Streak ÷3`
            : diceResult.blessed_triple
            ? `🌟 TRIPLE BLESSED! Streak ×3!`
            : diceResult.cursed
            ? `💀 CURSED! Streak -${diceResult.streak_before - diceResult.streak_after}`
            : `+${diceResult.streak_delta} streak!`}
          {diceResult.pending && rolledSinceSpin && <span className="dice-pending-note"> ⏳ next spin</span>}
        </span>
      )}
      <button
        className={`dice-roll-btn${canRoll ? '' : ' dice-roll-btn--disabled'}`}
        onClick={canRoll ? onRoll : undefined}
        disabled={!canRoll}
        title={canRoll ? 'Roll the dice!' : disabledReason}
      >
        {rolling ? 'Rolling…' : `Roll (${diceCharges}/${maxDiceCharges} charges)`}
      </button>
    </div>
  );
}

// ── Season Winners ────────────────────────────────────────────────────────
function SeasonWinners({ winners, seasonNumber, extraClass = '' }) {
  if (!winners || winners.length === 0) return null;
  const medals = ['🥇', '🥈', '🥉'];
  const rankClasses = ['sw-gold', 'sw-silver', 'sw-bronze', 'sw-4th', 'sw-5th'];
  return (
    <div className={`season-winners${extraClass ? ' ' + extraClass : ''}`}>
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
function SeasonInfo({ seasonName, endsAt }) {
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
      <span>Season {seasonName} ends:</span>
      {timeLeft && <span className="season-countdown">{timeLeft}</span>}
    </div>
  );
}


// ── Hiatus Screen ────────────────────────────────────────────────────────
function HiatusCountdown() {
  const [timeLeft, setTimeLeft] = useState('');
  useEffect(() => {
    const update = () => {
      const diff = HIATUS_END - Date.now();
      if (diff <= 0) { setTimeLeft('Starting now!'); return; }
      const d = Math.floor(diff / 86400000);
      const h = Math.floor((diff % 86400000) / 3600000);
      const m = Math.floor((diff % 3600000) / 60000);
      const s = Math.floor((diff % 60000) / 1000);
      setTimeLeft(d > 0 ? `${d}d ${h}h ${m}m ${s}s` : `${h}h ${m}m ${s}s`);
    };
    update();
    const id = setInterval(update, 1000);
    return () => clearInterval(id);
  }, []);
  return <span className="hiatus-countdown">{timeLeft}</span>;
}

function HiatusDice() {
  const [rolling, setRolling] = useState(false);
  const [vals, setVals]       = useState([1, 1, 1]);
  const [anim, setAnim]       = useState([1, 1, 1]);
  const [landed, setLanded]   = useState(false);
  const itvRef                = useRef(null);

  const roll = () => {
    if (rolling) return;
    setRolling(true);
    setLanded(false);
    itvRef.current = setInterval(() => {
      setAnim([Math.ceil(Math.random()*6), Math.ceil(Math.random()*6), Math.ceil(Math.random()*6)]);
    }, 80);
    setTimeout(() => {
      clearInterval(itvRef.current);
      const r = [Math.ceil(Math.random()*6), Math.ceil(Math.random()*6), Math.ceil(Math.random()*6)];
      setVals(r);
      setAnim(r);
      setLanded(true);
      setRolling(false);
    }, 800);
  };

  const d = rolling ? anim : vals;
  return (
    <div className="hiatus-dice-panel">
      <div className="dice-triangle">
        <div className="dice-row dice-row-top">
          <Die value={d[2]} rolling={rolling} landed={landed} />
        </div>
        <div className="dice-row">
          <Die value={d[0]} rolling={rolling} landed={landed} />
          <Die value={d[1]} rolling={rolling} landed={landed} />
        </div>
      </div>
      <button className="dice-roll-btn" onClick={roll} disabled={rolling}>
        {rolling ? 'Rolling…' : 'Roll'}
      </button>
    </div>
  );
}

function HiatusWheel() {
  const canvasRef   = useRef(null);
  const [rotation, setRotation] = useState(0);
  const [spinning, setSpinning] = useState(false);
  const [wins, setWins]         = useState(0);
  const [losses, setLosses]     = useState(0);
  const [autoSpin, setAutoSpin] = useState(false);
  const spinningRef = useRef(false);
  const rotationRef = useRef(0);
  const autoSpinRef = useRef(false);
  // Use the same sessionStorage key as the main game to avoid tab-lock rejections
  const tabId = useRef((() => {
    let id = sessionStorage.getItem('wheel_tab_id');
    if (!id) { id = Math.random().toString(36).slice(2) + Date.now().toString(36); sessionStorage.setItem('wheel_tab_id', id); }
    return id;
  })());
  const SPEED = 4.5;

  useEffect(() => { autoSpinRef.current = autoSpin; }, [autoSpin]);
  useEffect(() => { if (canvasRef.current) drawWheel(canvasRef.current, 'default'); }, []);

  const spin = useCallback(async () => {
    if (spinningRef.current) return;
    spinningRef.current = true;
    setSpinning(true);
    try {
      const res = await apiGame('/api/spin', { method: 'POST', body: JSON.stringify({ tab_id: tabId.current }) });
      if (!res.ok) {
        spinningRef.current = false; setSpinning(false);
        if (autoSpinRef.current) setTimeout(spin, 1500);
        return;
      }
      const data = res.data;
      const base = rotationRef.current;
      const seg  = data.angle % 360;
      const next = Math.ceil((base + 5 * 360 - seg) / 360) * 360 + seg;
      rotationRef.current = next;
      setRotation(next);
      setTimeout(() => {
        if (data.result === 'win') setWins(w => w + 1); else setLosses(l => l + 1);
        spinningRef.current = false; setSpinning(false);
        if (autoSpinRef.current) setTimeout(spin, 1500);
      }, SPEED * 1000 + 200);
    } catch {
      spinningRef.current = false; setSpinning(false);
      if (autoSpinRef.current) setTimeout(spin, 1500);
    }
  }, []);

  useEffect(() => { if (autoSpin && !spinningRef.current) spin(); }, [autoSpin, spin]);

  return (
    <div className="hiatus-wheel-wrap">
      <div className="hiatus-wheel-container">
        <div className="hiatus-wheel-pointer">▼</div>
        <canvas
          ref={canvasRef}
          width={180} height={180}
          className={`wheel-canvas${spinning ? ' spinning' : ''}`}
          style={{ transform: `rotate(${rotation}deg)`, transition: `transform ${SPEED}s cubic-bezier(0.17, 0.67, 0.12, 0.99)` }}
        />
        <div className="center-hub">★</div>
      </div>
      <div className="hiatus-wheel-score">
        <span className="hiatus-wscore hiatus-wscore-w">✓ {wins}W</span>
        <span className="hiatus-wscore hiatus-wscore-l">✗ {losses}L</span>
      </div>
      <button className="hiatus-spin-btn" onClick={spin} disabled={spinning}>
        {spinning ? '● ● ●' : '▶ Spin ◀'}
      </button>
      <label className="hiatus-autospin-label">
        <input type="checkbox" checked={autoSpin} onChange={e => setAutoSpin(e.target.checked)} />
        <span>Auto Spin</span>
      </label>
    </div>
  );
}

function HiatusScreen({ season, username, onLogout }) {
  const winners = season && season.latest_winners;

  useEffect(() => {
    apiFetch('/api/register-season', { method: 'POST' }).catch(() => {});
  }, []);

  return (
    <div className="hiatus-screen">
      <div className="hiatus-topbar">
        <span className="hiatus-topbar-title">🎡 Wheel Hiatus</span>
        <span className="hiatus-topbar-user">👤 {username}</span>
        <button className="logout-btn" onClick={onLogout}>Logout</button>
      </div>

      <div className="hiatus-body">
        {/* Left: past season winners + live mid-season leaderboard */}
        <div className="hiatus-col hiatus-col-left">
          <div className="hiatus-col-heading">Season {HIATUS_PAST_SEASON} Winners</div>
          {winners && winners.length > 0 ? (
            <SeasonWinners winners={winners} seasonNumber={HIATUS_PAST_SEASON} />
          ) : (
            <div className="hiatus-empty">No season data yet</div>
          )}
          <div className="hiatus-col-heading hiatus-col-heading--sub">Mid-Season 6.7</div>
          <Leaderboard currentUser={username} extraClass="hiatus-lb" />
        </div>

        {/* Center: mini wheel + fun dice */}
        <div className="hiatus-col hiatus-col-center">
          <HiatusWheel />
          <div className="hiatus-col-heading hiatus-col-heading--sub">🎲 Roll for fun</div>
          <HiatusDice />
          <span className="hiatus-dice-note">No game effect — just for fun!</span>
        </div>

        {/* Right: message + countdown */}
        <div className="hiatus-col hiatus-col-message">
          <div className="hiatus-message-box">
            <div className="hiatus-message-title">⏸ Taking a Break</div>
            <p className="hiatus-message-body">
              The wheel is on hiatus this week — thank you for playing Season {HIATUS_PAST_SEASON}!
              We'll be back next Friday with Season7️⃣.
            </p>
            <div className="hiatus-countdown-row">
              <span className="hiatus-countdown-label">Season7️⃣ begins in</span>
              <HiatusCountdown />
            </div>
            <div className="hiatus-preregistered">
              <p className="hiatus-preregistered-text">
                <strong>🎰 You&apos;re pre-registered for Season 7.</strong> Your auto-spin clock
                starts the moment the season begins — so your wins are already accumulating by the
                time you next log in, no matter how long after launch that is.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Leaderboard ───────────────────────────────────────────────────────────
function Leaderboard({ currentUser, extraClass, seasonWinners, seasonNumber }) {
  const [rows, setRows] = useState([]);
  const [tab, setTab] = useState('players');

  useEffect(() => {
    let ctrl = new AbortController();
    const load = () => {
      if (document.hidden) return;
      ctrl.abort();
      ctrl = new AbortController();
      apiFetch('/api/leaderboard', { signal: ctrl.signal })
        .then(r => { if (r.ok) setRows(r.data); })
        .catch(() => {});
    };
    load();
    const id = setInterval(load, 15000);
    return () => { clearInterval(id); ctrl.abort(); };
  }, []);

  if (rows.length === 0) return null;

  const rankClass = i => i === 0 ? 'gold' : i === 1 ? 'silver' : i === 2 ? 'bronze' : '';
  const infernoClass = streak => streak > 0 ? `streak-inferno-${Math.min(streak, 10)}` : '';
  const medals = ['🥇', '🥈', '🥉'];
  const rankClasses = ['sw-gold', 'sw-silver', 'sw-bronze', 'sw-4th', 'sw-5th'];

  return (
    <div className={`leaderboard-panel${extraClass ? ' ' + extraClass : ''}`}>
      <div className="leaderboard-tabs">
        <button
          className={`leaderboard-tab${tab === 'players' ? ' active' : ''}`}
          onClick={() => setTab('players')}
        >Top Players</button>
        <button
          className={`leaderboard-tab${tab === 'winners' ? ' active' : ''}`}
          onClick={() => setTab('winners')}
        >Past Winners</button>
      </div>
      {tab === 'players' && (
        <>
          <div className="lb-header">
            <span className="lb-rank-h"></span>
            <span className="lb-name-h">Player</span>
            <span className="lb-wins-h">W</span>
            <span className="lb-wp-h" title="Win Power level">WP</span>
            <span className="lb-bp-h" title="Bonus Power level">BP</span>
            <span className="lb-streak-h">🔥</span>
          </div>
          {rows.map((r, i) => (
            <div key={r.username} className={`lb-row${r.active ? '' : ' lb-inactive'}`}>
              <span className={`lb-rank ${rankClass(i)}`}>{i + 1}.</span>
              <span className={`lb-name ${r.username === currentUser ? 'is-you' : ''}`}>{r.username}</span>
              <span className="lb-wins">{fmt(r.wins)}</span>
              <span className="lb-wp">{r.winmult_inf_level > 0 ? r.winmult_inf_level : '—'}</span>
              <span className="lb-bp">{r.bonusmult_inf_level > 0 ? r.bonusmult_inf_level : '—'}</span>
              <span className={`lb-streak ${infernoClass(r.streak)}`}>
                {r.streak > 0 ? `${r.streak}🔥` : r.streak < 0 ? `${r.streak}💀` : '0'}
              </span>
            </div>
          ))}
        </>
      )}
      {tab === 'winners' && (
        <div className="lb-winners-tab">
          {seasonWinners && seasonWinners.length > 0 ? (
            <>
              <div className="lb-winners-title">Season {seasonNumber} Winners</div>
              {seasonWinners.map(w => (
                <div key={w.position} className={`season-winner-row ${rankClasses[w.position - 1] || ''}`}>
                  <span className="sw-medal">{medals[w.position - 1] || w.position}</span>
                  <span className="sw-name">{w.username}</span>
                  <span className="sw-wins">{fmt(w.wins)}W</span>
                </div>
              ))}
            </>
          ) : (
            <div className="lb-winners-empty">No season winners yet.</div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Chat Panel ────────────────────────────────────────────────────────────
function fmtChatTime(iso) {
  const d = new Date(iso);
  let h = d.getHours();
  const m = String(d.getMinutes()).padStart(2, '0');
  const ampm = h >= 12 ? 'pm' : 'am';
  h = h % 12 || 12;
  return `${h}:${m}${ampm}`;
}

const CHAT_DEFAULT_SIZE = { w: 231, h: 224 };
const CHAT_MIN_W = 180, CHAT_MIN_H = 150, CHAT_MAX_W = 620, CHAT_MAX_H = 620;

function ChatPanel({ extraClass = '', onClose }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [error, setError] = useState('');
  const [timeoutSecs, setTimeoutSecs] = useState(0);
  const [loadingOlder, setLoadingOlder] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [size, setSize] = useState(() => {
    try {
      const s = JSON.parse(localStorage.getItem('chat_panel_size'));
      if (s && s.w >= CHAT_MIN_W && s.h >= CHAT_MIN_H) return s;
    } catch {}
    return CHAT_DEFAULT_SIZE;
  });
  const panelRef = useRef(null);
  const messagesEndRef = useRef(null);
  const scrollRef = useRef(null);
  const atBottomRef = useRef(true);
  const timeoutTimerRef = useRef(null);
  const oldestLoadedIdRef = useRef(null);

  // Persist size to localStorage whenever it changes (covers drag, close/reopen, refresh)
  useEffect(() => {
    localStorage.setItem('chat_panel_size', JSON.stringify(size));
  }, [size]);

  const onResizeMouseDown = useCallback((e) => {
    e.preventDefault();
    const rect = panelRef.current ? panelRef.current.getBoundingClientRect() : CHAT_DEFAULT_SIZE;
    const startW = rect.width, startH = rect.height;
    const startX = e.clientX, startY = e.clientY;

    const onMove = (ev) => {
      const newW = Math.min(CHAT_MAX_W, Math.max(CHAT_MIN_W, startW + (ev.clientX - startX)));
      const newH = Math.min(CHAT_MAX_H, Math.max(CHAT_MIN_H, startH + (ev.clientY - startY)));
      setSize({ w: newW, h: newH });
    };
    const onUp = () => {
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);
    };
    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
  }, []);

  // Merge polled latest-50 with any older messages already loaded via pagination.
  // Returns the merged array; the polled slice is sorted ASC by the server.
  const mergeLatest = (prev, polled) => {
    if (prev.length === 0) {
      if (polled.length > 0) {
        oldestLoadedIdRef.current = polled[0].id;
        if (polled.length < 50) setHasMore(false);
      } else {
        setHasMore(false);
      }
      return polled;
    }
    const polledIds = new Set(polled.map(m => m.id));
    const older = prev.filter(m => !polledIds.has(m.id));
    return [...older, ...polled];
  };

  // Poll for new messages — fetch latest 50, merge with any older messages loaded
  useEffect(() => {
    let ctrl = new AbortController();
    const load = () => {
      if (document.hidden) return;
      ctrl.abort();
      ctrl = new AbortController();
      apiFetch('/api/chat?limit=50', { signal: ctrl.signal })
        .then(r => {
          if (!r.ok) return;
          setMessages(prev => mergeLatest(prev, r.data));
        })
        .catch(() => {});
    };
    load();
    const id = setInterval(load, 5000);
    return () => { clearInterval(id); ctrl.abort(); };
  }, []);

  // Auto-scroll only if at bottom
  useEffect(() => {
    if (atBottomRef.current && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  // Countdown timer for timeout feedback
  useEffect(() => {
    if (timeoutSecs <= 0) return;
    clearInterval(timeoutTimerRef.current);
    timeoutTimerRef.current = setInterval(() => {
      setTimeoutSecs(s => {
        if (s <= 1) { clearInterval(timeoutTimerRef.current); return 0; }
        return s - 1;
      });
    }, 1000);
    return () => clearInterval(timeoutTimerRef.current);
  }, [timeoutSecs]);

  const handleScroll = () => {
    const el = scrollRef.current;
    if (!el) return;
    atBottomRef.current = el.scrollHeight - el.scrollTop - el.clientHeight < 40;
    if (el.scrollTop < 100 && hasMore && !loadingOlder && oldestLoadedIdRef.current != null) {
      loadOlder();
    }
  };

  const loadOlder = async () => {
    if (loadingOlder) return;
    const oldestId = oldestLoadedIdRef.current;
    if (oldestId == null) return;

    setLoadingOlder(true);
    const el = scrollRef.current;
    const prevScrollHeight = el ? el.scrollHeight : 0;

    try {
      const r = await apiFetch(`/api/chat?before=${oldestId}&limit=50`);
      if (!r.ok) return;
      const older = r.data;
      if (older.length === 0) {
        setHasMore(false);
        return;
      }
      setMessages(prev => {
        const existing = new Set(prev.map(m => m.id));
        const fresh = older.filter(m => !existing.has(m.id));
        return [...fresh, ...prev];
      });
      oldestLoadedIdRef.current = older[0].id;
      if (older.length < 50) setHasMore(false);
      // Preserve scroll position: scrollHeight grew by the prepended block,
      // so bump scrollTop by the same amount to keep the user's view anchored.
      if (el) {
        const newScrollHeight = el.scrollHeight;
        el.scrollTop = newScrollHeight - prevScrollHeight + el.scrollTop;
      }
    } finally {
      setLoadingOlder(false);
    }
  };

  const sendMessage = async () => {
    const text = input.trim();
    if (!text) return;
    setError('');
    const r = await apiGame('/api/chat', {
      method: 'POST',
      body: JSON.stringify({ message: text }),
    });
    if (r.ok) {
      setInput('');
      // Reload latest 50 and merge with any older messages already in view
      apiFetch('/api/chat?limit=50')
        .then(res => {
          if (!res.ok) return;
          setMessages(prev => mergeLatest(prev, res.data));
        })
        .catch(() => {});
    } else if (r.status === 429) {
      const secs = r.data.seconds_remaining || 60;
      setTimeoutSecs(secs);
      setError(`Timed out. Wait ${secs}s.`);
    } else {
      setError(r.data.error || 'Failed to send');
    }
  };

  const handleKeyDown = e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const isDisabled = timeoutSecs > 0;

  const panelStyle = extraClass === 'mobile-full' ? {} : { width: size.w, height: size.h };

  return (
    <div ref={panelRef} className={`chat-panel${extraClass ? ' ' + extraClass : ''}`} style={panelStyle}>
      <div className="chat-panel-header">
        <div className="chat-panel-title">💬 Chat</div>
        {onClose && <button className="chat-close-btn" onClick={onClose} title="Close Chat">✕</button>}
      </div>
      <div className="chat-messages" ref={scrollRef} onScroll={handleScroll}>
        {loadingOlder && (
          <div className="chat-loading-older" style={{ textAlign: 'center', padding: '4px 0', opacity: 0.55, fontSize: '0.65rem' }}>
            Loading older…
          </div>
        )}
        {messages.map(m => {
          const isSystem = m.message_type && m.message_type !== 'user';
          if (isSystem) {
            return (
              <div key={m.id} className="chat-msg chat-msg-system">
                {m.created_at && <span className="chat-msg-time">{fmtChatTime(m.created_at)}</span>}
                <span className="chat-msg-text chat-system-text">{m.message}</span>
              </div>
            );
          }
          return (
            <div key={m.id} className="chat-msg">
              {m.created_at && <span className="chat-msg-time">{fmtChatTime(m.created_at)}</span>}
              <span className="chat-msg-name">{m.username}: </span>
              <span className="chat-msg-text">{m.message}</span>
            </div>
          );
        })}
        <div ref={messagesEndRef} />
      </div>
      {error && <div className="chat-error">{error}</div>}
      <div className="chat-input-row">
        <input
          className="chat-input"
          type="text"
          placeholder={isDisabled ? `Wait ${timeoutSecs}s…` : 'Message…'}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isDisabled}
          maxLength={200}
        />
        <button
          className="chat-send-btn"
          onClick={sendMessage}
          disabled={isDisabled}
        >↑</button>
      </div>
      {extraClass !== 'mobile-full' && (
        <div className="chat-resize-handle" onMouseDown={onResizeMouseDown} title="Drag to resize" />
      )}
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
  { id: 'fish_seal',     emoji: '🦭', name: 'Seal',          cost: 3500,
    labels: { idle: '*claps flippers*', happy: 'ARF ARF ARF!', sad: '*sad honk*' } },
  { id: 'fish_shrimp',   emoji: '🦐', name: 'Shrimp',        cost: 6000,
    labels: { idle: 'Small but mighty', happy: 'Prawn to win!', sad: 'De-veined...' } },
  { id: 'fish_coral',    emoji: '🪸', name: 'Coral',         cost: 10000,
    labels: { idle: 'Growing strong', happy: 'Reef royalty!', sad: 'Bleached out...' } },
  { id: 'fish_mermaid',  emoji: '🧜', name: 'Mermaid',       cost: 17500,
    labels: { idle: 'Under the sea~', happy: 'Mythic win!', sad: 'Into the deep...' } },
  { id: 'fish_croc',     emoji: '🐊', name: 'Crocodile',     cost: 30000,
    labels: { idle: '*death roll ready*', happy: 'SNAPPED IT!', sad: 'Sunk to the bottom...' } },
  { id: 'fish_rocket',   emoji: '🚀', name: 'Rocket',         cost: 50000,
    labels: { idle: 'T-minus 3...', happy: 'BLAST OFF!', sad: 'Mission failed...' } },
  { id: 'fish_comet',    emoji: '☄️', name: 'Comet',          cost: 85000,
    labels: { idle: '*blazing through space*', happy: 'Comet strike!', sad: 'Burned up...' } },
  { id: 'fish_saturn',   emoji: '🪐', name: 'Saturn',         cost: 145000,
    labels: { idle: 'Ringing around~', happy: 'Orbital win!', sad: 'Lost in the rings...' } },
  { id: 'fish_alien',    emoji: '👽', name: 'Alien',          cost: 250000,
    labels: { idle: 'Greetings, earthling', happy: 'ABDUCTION WIN!', sad: '*returns to home planet*' } },
  { id: 'fish_ufo',      emoji: '🛸', name: 'UFO',            cost: 425000,
    labels: { idle: '*hovering*', happy: 'BEAM UP!', sad: '*crashes*' } },
];

const SHOP_SECTIONS = [
  { label: '🪐 Class', classSection: true, items: [
    { id: 'class_earth', emoji: '🌍', name: 'Earth', cost: 10000000, tier: 3, desc: '+25% to all fish income while equipped' },
    { id: 'class_moon',  emoji: '🌙', name: 'Moon',  cost: 10000000, tier: 3, desc: '+5% to all proc rates (Jackpot, Win Echo, Fortune Charm) while equipped' },
    { id: 'class_star',  emoji: '⭐', name: 'Star',  cost: 10000000, tier: 3, desc: '+20% to Win Power payout while equipped' },
  ]},
  { label: '💰 Win Power', items: [
    { id: 'winmult_1', emoji: '💰', name: 'Win Power I',  cost: 200,    desc: '+20% win multiplier' },
    { id: 'winmult_2', emoji: '💰', name: 'Win Power II', cost: 600,    desc: '+40% win multiplier', requires: 'winmult_1' },
    { id: 'winmult_3', emoji: '💰', name: 'Win Power III',cost: 2000,   desc: '+60% win multiplier', requires: 'winmult_2' },
  ]},
  { label: '⭐ Bonus Power', items: [
    { id: 'bonusmult_1', emoji: '⭐', name: 'Bonus Power I',  cost: 300,   desc: 'Multiplies streak bonuses' },
    { id: 'bonusmult_2', emoji: '⭐', name: 'Bonus Power II', cost: 900,   desc: 'Multiplies streak bonuses', requires: 'bonusmult_1' },
    { id: 'bonusmult_3', emoji: '⭐', name: 'Bonus Power III',cost: 2800,  desc: 'Multiplies streak bonuses', requires: 'bonusmult_2' },
  ]},
  { label: '🐟 Fishing Panel Size', items: [
    { id: 'fishsize_small', emoji: '🔍', name: 'Compact',      cost: 1,    desc: 'Fishing panel: 50% size (compact mode)' },
    { id: 'fishsize_1',     emoji: '🔎', name: 'Big Panel',    cost: 1,    desc: 'Fishing panel: 130% size' },
    { id: 'fishsize_2',     emoji: '🔎', name: 'Giant Panel',  cost: 1,    desc: 'Fishing panel: 160% size', requires: 'fishsize_1' },
    { id: 'fishsize_3',     emoji: '🔎', name: 'Colossal',     cost: 1,    desc: 'Fishing panel: 200% size', requires: 'fishsize_2' },
  ]},
  { label: '✨ Fish Trail', items: [
    { id: 'trail_1',     emoji: '✨', name: 'Sparkle Trail', cost: 125,   desc: 'Gold shimmer trail' },
    { id: 'trail_2',     emoji: '🔥', name: 'Fire Trail',    cost: 500,   desc: 'Flame glow trail',       requires: 'trail_1' },
    { id: 'trail_3',     emoji: '🌈', name: 'Rainbow Trail', cost: 2000,  desc: 'Rainbow hue trail',      requires: 'trail_2' },
    { id: 'trail_4',     emoji: '❄️', name: 'Frost Trail',   cost: 7000,  desc: 'Ice crystal aura',       requires: 'trail_3' },
    { id: 'trail_5',     emoji: '⚡', name: 'Thunder Trail', cost: 22000, desc: 'Electric storm aura',    requires: 'trail_4' },
    { id: 'trail_6',     emoji: '🌌', name: 'Galaxy Trail',  cost: 70000, desc: 'Cosmic void aura',       requires: 'trail_5' },
  ]},
  { label: '🎣 Fishing Gear', items: [
    { id: 'lure_1',       emoji: '🎣', name: 'Lure I',         cost: 100,     desc: '10% faster bite times + 1.5× catch value' },
    { id: 'lure_2',       emoji: '🎣', name: 'Lure II',        cost: 500,     desc: '20% faster bite times + 2× catch value', requires: 'lure_1' },
    { id: 'lure_3',       emoji: '🎣', name: 'Lure III',       cost: 2500,    desc: '35% faster bite times + 5× catch value', requires: 'lure_2' },
    { id: 'lure_4',       emoji: '🎣', name: 'Lure IV',        cost: 15000,   desc: '50% faster bite times + 10× catch value', requires: 'lure_3' },
    { id: 'lure_5',       emoji: '⭐', name: 'Master Lure',     cost: 500000,  desc: '65% faster bite times + 20× catch value + +1% chance per legendary species — requires complete Encyclopaedia', requires: 'lure_4', encyclopaediaLocked: true },
    { id: 'auto_cast',    emoji: '⏭️', name: 'Auto-Cast',      cost: 1000,    desc: 'Auto-casts line when idle — you still tap the bite window' },
    { id: 'autofisher_1', emoji: '🤖', name: 'Auto-Fisher I',  cost: 300,     desc: 'Automated fishing at 45% catch rate — common & uncommon only' },
    { id: 'autofisher_2', emoji: '🤖', name: 'Auto-Fisher II', cost: 2000,    desc: 'Auto-Fisher catch rate: 55% — common & uncommon only', requires: 'autofisher_1' },
    { id: 'autofisher_3', emoji: '🤖', name: 'Auto-Fisher III',cost: 12000,   desc: 'Auto-Fisher catch rate: 65% — common & uncommon only', requires: 'autofisher_2' },
    { id: 'autofisher_4', emoji: '🤖', name: 'Master Auto-Fisher', cost: 500000, desc: 'Auto-Fisher catch rate: 75% — now catches rare species too — requires complete Encyclopaedia', requires: 'autofisher_3', encyclopaediaLocked: true },
    { id: 'precise_angler_1', emoji: '🎯', name: 'Precise Angler',        cost: 50000,  desc: 'Reel within the first 50% of the bite window for 1.2× catch value', tier: 2 },
    { id: 'precise_angler_2', emoji: '🎯', name: 'Precise Angler II',     cost: 100000, desc: 'Also: reel within the first 20% for 1.5× catch value', requires: 'precise_angler_1' },
    { id: 'precise_angler_3', emoji: '🎯', name: 'Master Angler',         cost: 500000, desc: 'Also: reel within the first 15% for 2× catch value — requires complete Encyclopaedia', requires: 'precise_angler_2', encyclopaediaLocked: true },
  ]},
  { label: '🛡️ Protection', items: [
    { id: 'guard',         emoji: '🛡️', name: 'Guard',              cost: 1000,   desc: 'Blocks one loss per manual trigger. Consumes a guard charge.' },
    { id: 'guard_charge',  emoji: '🔋', name: 'Guard Charge',      cost: 10000,  desc: 'Adds a guard charge (max 3). Recharges 1 per 50 spins via Regen Shield.', tier: 2 },
    { id: 'regen_shield',  emoji: '🔄', name: 'Regenerating Shield', cost: 5000,  desc: 'Blocks any loss when charged. Recharges after 5 wins. Never breaks.', tier: 2 },
    { id: 'resilience',    emoji: '💪', name: 'Resilience',      cost: 20000,  desc: '50% chance: on win streak, a loss only drops streak by 1 instead of resetting', tier: 3 },
  ]},
  { label: '🎲 Special Upgrades', items: [
    { id: 'fortune_charm', emoji: '🍀', name: 'Fortune Charm',  cost: 1000000,  desc: '25% chance: +25% to streak bonus payout', tier: 3 },
    { id: 'lucky_seven',   emoji: '7️⃣', name: 'Lucky Seven',    cost: 7000000,  desc: 'Every 7th spin is guaranteed a win', tier: 3 },
    { id: 'win_echo',      emoji: '🔊', name: 'Win Echo',        cost: 1000000,  desc: '20% chance to double wins earned on any win', tier: 3 },
    { id: 'jackpot',       emoji: '🎰', name: 'Jackpot',         cost: 3000000,  desc: '1% chance each win to multiply gains by 25x. 5% chance for Jackpot Echo next spin.', tier: 3 },
  ]},
  { label: '⚡ Season 8: Wager System', items: [
    { id: 'wager_unlock',      emoji: '⚡', name: 'Wager Unlock',      cost: 500,    desc: 'Unlocks stake slider (0% safe, 5%-30% at risk)', tier: 1 },
    { id: 'wager_safety_net',  emoji: '🛡️', name: 'Safety Net',       cost: 2000,   desc: 'Refunds 25% of lost stake at 15%+ stake', tier: 2, requires: 'wager_unlock' },
    { id: 'wager_hot_streak',  emoji: '🔥', name: 'Hot Streak',       cost: 8000,   desc: '+5% per consecutive same-stake win, cap +50%', tier: 2, requires: 'wager_unlock' },
    { id: 'wager_double_down', emoji: '⚡', name: 'Double Down',      cost: 25000,  desc: 'Arm 2x stake for next spin', tier: 3, requires: 'wager_hot_streak' },
    { id: 'wager_insurance',   emoji: '🛡️', name: 'Insurance',        cost: 50000,  desc: 'Caps next loss at stake amount', tier: 3, requires: 'wager_unlock' },
    { id: 'wager_stake_extend_1', emoji: '📈', name: 'Stake Extender I',  cost: 5000,    desc: 'Raises max stake from 30% to 35%', tier: 1, requires: 'wager_unlock' },
    { id: 'wager_stake_extend_2', emoji: '📈', name: 'Stake Extender II', cost: 15000,   desc: 'Raises max stake from 35% to 40%', tier: 1, requires: 'wager_stake_extend_1' },
    { id: 'wager_stake_extend_3', emoji: '📈', name: 'Stake Extender III',cost: 40000,   desc: 'Raises max stake from 40% to 45%', tier: 1, requires: 'wager_stake_extend_2' },
    { id: 'auto_spin_unlock',  emoji: '🔁', name: 'Auto-Spin Unlock', cost: 5000,    desc: 'Unlocks auto-spin button (100 spins per activation at 0% stake — stake slider hides while active)', tier: 1 },
  ]},
  { label: '🏅 Season 8: Prestige', items: [
    { id: 'prestige_unlock',     emoji: '🏅', name: 'Prestige Unlock',     cost: 1000000, desc: 'Unlocks prestige reset (permanent +2% per level)', tier: 3 },
    { id: 'prestige_efficiency', emoji: '⚡', name: 'Prestige Efficiency', cost: 500000,  desc: 'Reduces prestige threshold from 1M to 500K wins', tier: 3, requires: 'prestige_unlock' },
    { id: 'prestige_legacy',     emoji: '📜', name: 'Prestige Legacy',     cost: 1000000, desc: 'Keep functional upgrades when prestiging', tier: 3, requires: 'prestige_unlock' },
  ]},
  { label: '🎣 Season 8: Fishing', items: [
    { id: 'fish_to_wager',      emoji: '🪙', name: 'Fish-to-Wager',      cost: 5000,   desc: 'Convert caught fish to wager tokens', tier: 1 },
    { id: 'catch_of_the_day',   emoji: '📅', name: 'Catch of the Day',   cost: 3000,   desc: 'First fish conversion each day worth 5x tokens', tier: 1 },
    { id: 'aquarium',           emoji: '🐠', name: 'Aquarium',           cost: 15000,  desc: 'Each unique species adds +0.1% wheel luck', tier: 2 },
    { id: 'lure_specialization',emoji: '🎯', name: 'Lure Specialization',cost: 10000,  desc: 'Specialized lure techniques', tier: 2, requires: 'fish_to_wager' },
  ]},
  { label: '🎡 Wheel Theme', items: [
    { id: 'theme_fire',  emoji: '🔥', name: 'Fire Theme',    cost: 250,   desc: 'Infernal wheel colors' },
    { id: 'theme_ice',   emoji: '❄️', name: 'Ice Theme',     cost: 1000,  desc: 'Glacial wheel colors',    requires: 'theme_fire' },
    { id: 'theme_neon',  emoji: '🟣', name: 'Neon Theme',    cost: 4000,  desc: 'Cyberpunk wheel colors',  requires: 'theme_ice' },
    { id: 'theme_void',  emoji: '🌑', name: 'Void Theme',    cost: 12000, desc: 'Dark matter wheel',       requires: 'theme_neon' },
    { id: 'theme_gold',  emoji: '🟡', name: 'Gold Theme',    cost: 40000, desc: 'Pure gold wheel',         requires: 'theme_void' },
    { id: 'theme_tidal',  emoji: '🌊', name: 'Tidal Theme',   cost: 250,    desc: 'Cool blue/teal with wave animation' },
    { id: 'theme_ember',  emoji: '🔥', name: 'Ember Theme',   cost: 1000,   desc: 'Warm orange with spark animation', requires: 'theme_tidal' },
    { id: 'theme_frost',  emoji: '❄️', name: 'Frost Theme',   cost: 4000,   desc: 'Ice-crystal palette with crack animation', requires: 'theme_ember' },
    { id: 'theme_aurora', emoji: '🌌', name: 'Aurora Theme',  cost: 12000,  desc: 'Shifting greens/purples with northern lights', requires: 'theme_frost' },
    { id: 'theme_vintage',emoji: '📼', name: 'Vintage Theme', cost: 40000,  desc: 'Retro-styled sepia tones' },
    { id: 'golden_wheel',emoji: '✨', name: 'Golden Wheel',  cost: 300,   desc: 'Radiant glow ring' },
  ]},
  { label: '🎊 Confetti', items: [
    { id: 'party_mode', emoji: '🎊', name: 'Party Mode',  cost: 150,  desc: 'Win confetti burst every spin' },
    { id: 'confetti_1', emoji: '✨', name: 'Confetti I',  cost: 75,   desc: 'Light confetti on wins' },
    { id: 'confetti_2', emoji: '🌟', name: 'Confetti II', cost: 300,  desc: 'Heavier confetti shower', requires: 'confetti_1' },
    { id: 'confetti_3', emoji: '💫', name: 'Confetti III',cost: 1200, desc: 'Maximum confetti eruption', requires: 'confetti_2' },
  ]},
  { label: '🎨 Atmosphere', items: [
    { id: 'bg_royal',   emoji: '👑', name: 'Royal',   cost: 400,   desc: 'Deep purple radial atmosphere' },
    { id: 'bg_inferno', emoji: '🔥', name: 'Inferno', cost: 1600,  desc: 'Red hellscape atmosphere', requires: 'bg_royal' },
    { id: 'bg_forest',  emoji: '🌲', name: 'Forest',  cost: 5000,  desc: 'Dark forest atmosphere', requires: 'bg_inferno' },
    { id: 'bg_abyss',   emoji: '🌑', name: 'Abyss',   cost: 15000, desc: 'Void atmosphere', requires: 'bg_forest' },
    { id: 'bg_cosmic',  emoji: '🌌', name: 'Cosmic',  cost: 50000, desc: 'Cosmic void atmosphere', requires: 'bg_abyss' },
  ]},
  { label: '🖼️ Page Theme', items: [
    { id: 'page_season1', emoji: '1️⃣', name: 'Season 1', cost: 1000, desc: 'Season 1 page theme' },
    { id: 'page_season2', emoji: '2️⃣', name: 'Season 2', cost: 1000, desc: 'Season 2 page theme' },
    { id: 'page_season3', emoji: '3️⃣', name: 'Season 3', cost: 1000, desc: 'Season 3 page theme' },
    { id: 'page_season4', emoji: '4️⃣', name: 'Season 4', cost: 1000, desc: 'Season 4 page theme' },
    { id: 'page_season5', emoji: '5️⃣', name: 'Season 5', cost: 1000, desc: 'Season 5 page theme — Bioluminescence' },
    { id: 'page_season6', emoji: '6️⃣', name: 'Season 6', cost: 1000, desc: 'Season 6 page theme — Night Ocean' },
    { id: 'page_season7', emoji: '7️⃣', name: 'Season 7', cost: 1000, desc: 'Season 7 page theme — Wormhole' },
    { id: 'page_season8', emoji: '8️⃣', name: 'Season 8', cost: 1000, desc: 'Season 8 page theme — Casino' },
  ]},
  { label: '🎲 Dice Charges', items: [
    { id: 'dice_charge_2', emoji: '🎲', name: 'Dice Charge +1', cost: 2000,    desc: 'Max dice charges: 2' },
    { id: 'dice_charge_3', emoji: '🎲', name: 'Dice Charge +2', cost: 15000,   desc: 'Max dice charges: 3', requires: 'dice_charge_2' },
    { id: 'dice_charge_4', emoji: '🎲', name: 'Dice Charge +3', cost: 100000,  desc: 'Max dice charges: 4', requires: 'dice_charge_3' },
    { id: 'dice_extra',    emoji: '🎰', name: 'Extra Die',      cost: 1000000, desc: 'Roll 3 dice — take the best result', requires: 'dice_charge_3' },
  ]},
];

// Infinite upgrade config (mirrors INFINITE_UPGRADES in models.py)
const INF_UPGRADE_CFG = {
  clickmult_inf:         { tierCosts: [75, 250, 600, 1400, 3000], infBase: 10_000, infScale: 1.5 },
};
function infCost(id, level) {
  const cfg = INF_UPGRADE_CFG[id];
  if (!cfg) return 0;
  const { tierCosts, infBase, infScale } = cfg;
  if (level < tierCosts.length) return tierCosts[level];
  return Math.floor(infBase * Math.pow(infScale, level - tierCosts.length));
}
function infMultiplier(id, level) {
  if (id === 'clickmult_inf') return 1 + level * 0.15;
  return 1;
}

const DEFAULT_FISH = { emoji: '🐟', labels: { idle: 'Click me!', happy: '🎉 Nice!', sad: '💀 Ouch!' } };

function getFishData(equippedFish) {
  return FISH_SKINS.find(s => s.id === equippedFish) || DEFAULT_FISH;
}

const COSMETIC_SECTION_IDS = new Set([
  'bg_royal','bg_inferno','bg_forest','bg_abyss','bg_cosmic',
  'fishsize_small','fishsize_1','fishsize_2','fishsize_3',
  'confetti_1','confetti_2','confetti_3',
  'party_mode',
  'trail_1','trail_2','trail_3','trail_4','trail_5','trail_6',
  'theme_fire','theme_ice','theme_neon','theme_void','theme_gold',
  'theme_tidal','theme_ember','theme_frost','theme_aurora','theme_vintage',
  'golden_wheel',
  'page_season1', 'page_season2', 'page_season3', 'page_season4', 'page_season5', 'page_season6', 'page_season7', 'page_season8',
]);

// Season 3: currency classification (mirrors ITEM_CURRENCY in models.py)
const COSMETIC_IDS = new Set([
  'fish_tropical','fish_puffer','fish_octopus','fish_shark','fish_dolphin',
  'fish_squid','fish_turtle','fish_crab','fish_lobster','fish_whale',
  'fish_seal','fish_shrimp','fish_coral','fish_mermaid','fish_croc',
  'fish_rocket','fish_comet','fish_saturn','fish_alien','fish_ufo',
  'fishsize_small','fishsize_1','fishsize_2','fishsize_3',
  'trail_1','trail_2','trail_3','trail_4','trail_5','trail_6',
  'theme_fire','theme_ice','theme_neon','theme_void','theme_gold','golden_wheel',
  'theme_tidal','theme_ember','theme_frost','theme_aurora','theme_vintage',
  'page_season1','page_season2','page_season3','page_season4','page_season5','page_season6','page_season7','page_season8','party_mode','confetti_1','confetti_2','confetti_3',
  'bg_royal','bg_inferno','bg_forest','bg_abyss','bg_cosmic',
]);
const getItemCurrency = id => {
  if (COSMETIC_IDS.has(id)) return 'losses';
  return 'wins';
};
const currencyIcon = c => c === 'wins' ? '🏆' : c === 'losses' ? '💀' : '🐟';

// Linear decay: 1:1 for first 25M exchanged, linearly down to 10% by 125M
function computeFishExchangeRate(total) {
  if (total < 25_000_000)  return 100;
  if (total >= 125_000_000) return 10;
  const t = (total - 25_000_000) / 100_000_000;
  return Math.round(Math.max(10, 100 - 90 * t));
}

// ── Shop components ────────────────────────────────────────────────────────
const CLASS_IDS = new Set(['class_earth', 'class_moon', 'class_star']);

const ShopItem = React.memo(function ShopItem({ item, owned, equipped, active, canAfford, onBuy, onEquip, onEquipCosmetic, onEquipClass, isSkin, isSingularity, isCosmetic, isClass, isClassEquipped, infLevel, displayCost, procStreak }) {
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
  } else if (owned && isClass) {
    actionEl = isClassEquipped
      ? <span className="shop-equipped-badge">⭐ Equipped</span>
      : <button className="shop-equip-btn" onClick={() => onEquipClass(item.id)}>Equip</button>;
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
        const cfg = INF_UPGRADE_CFG[item.id];
        const atMax = cfg && cfg.maxLevel != null && infLevel >= cfg.maxLevel;
        if (atMax) return `Lv${infLevel} · MAX  ${item.desc}`;
        if (item.id === 'proc_streak_inf') {
          const streak = procStreak || 0;
          const currentBonus = (streak * infLevel * 0.5).toFixed(1);
          return `+${currentBonus}% now (streak ${streak} × Lv${infLevel}) · Lv${infLevel} → Lv${infLevel + 1}  ${item.desc}`;
        }
        const cur = infMultiplier(item.id, infLevel);
        const nxt = infMultiplier(item.id, infLevel + 1);
        let sep = 'x';
        if (item.id === 'streak_armor_inf')      sep = '%';
        if (item.id === 'jackpot_resonance_inf') sep = '%';
        if (item.id === 'echo_amp_inf')          sep = '%';
        return `Lv${infLevel} · ${cur}${sep} → ${nxt}${sep}  ${item.desc}`;
      })()
    : item.desc;
  return (
    <div className={`shop-item ${!isInfinite && owned ? (equipped || active ? 'equipped' : 'owned') : ''} ${extraClass}`}>
      <span className="shop-item-emoji">{item.emoji}</span>
      <div className="shop-item-info">
        <div className="shop-item-name">{item.name}</div>
        {infDesc && <div className="shop-item-desc" data-tooltip={infDesc}>{infDesc}</div>}
        <div className={`shop-item-cost cost-${getItemCurrency(item.id)}`}>{currencyIcon(getItemCurrency(item.id))} {fmt(cost)}</div>
      </div>
      <div className="shop-item-action">{actionEl}</div>
    </div>
  );
});

const COSMETIC_SECTION_LABELS = new Set(['🐟 Fishing Panel Size', '✨ Fish Trail', '🎡 Wheel Theme', '🎊 Confetti', '🎨 Atmosphere', '🖼️ Page Theme']);

// T106: tier thresholds are now based on cumulative_wins (lifetime value of
// wins gained), not win_count (count of winning spins). Updated from the old
// values (1000 / 10000) to match the new metric scale.
const TIER_THRESHOLDS = { 2: 10000, 3: 100000 };

function ShopPanel({ fishClicks, wins, losses, ownedItems, equippedFish, activeCosmetics, infLevels, onBuy, onEquip, onEquipCosmetic, onEquipClass, onFishExchange, onWinsExchange, equippedClass, fishExchangeTotal, collapsed, cumulativeWins, caughtSpecies, procStreak }) {
  const [activeTab, setActiveTab] = useState('functional');

  const { cosmeticSections, functionalSections } = useMemo(() => {
    const cosmetic = [], functional = [];
    SHOP_SECTIONS.forEach(section => {
      const isCosmeticSection = COSMETIC_SECTION_LABELS.has(section.label);
      const visibleItems = section.items.filter(item => {
        const requiresMet = !item.requires || ownedItems.includes(item.requires);
        if (isCosmeticSection) return requiresMet;
        if (item.infinite) {
          if (item.id === 'streak_armor_inf')      return ownedItems.includes('resilience');
          if (item.id === 'jackpot_resonance_inf') return ownedItems.includes('jackpot');
          if (item.id === 'echo_amp_inf')          return ownedItems.includes('win_echo');
          if (item.id === 'proc_streak_inf')       return ['jackpot','win_echo','fortune_charm'].some(x => ownedItems.includes(x));
          return requiresMet;
        }
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
        const itemTierNum = item.tier || 1;
        const tierLocked = itemTierNum > 1 && !ownedItems.includes(item.id);
        const tierThreshold = tierLocked ? TIER_THRESHOLDS[itemTierNum] : null;
        // T106: gate on cumulative_wins (lifetime value of wins gained), not winCount.
        const tierUnlocked = !tierLocked || ((cumulativeWins || 0) >= (tierThreshold || 0));

        const infLevel = item.infinite ? (infLevels[item.id] || 0) : null;
        const cfg = item.infinite ? INF_UPGRADE_CFG[item.id] : null;
        const atMaxLevel = cfg && cfg.maxLevel != null && infLevel >= cfg.maxLevel;
        const displayCost = item.infinite ? infCost(item.id, infLevel) : item.cost;
        const currency = getItemCurrency(item.id);
        const balance = currency === 'wins' ? wins : currency === 'losses' ? losses : fishClicks;

        // Master Lure (lure_5) requires all species caught (complete Encyclopaedia)
        const encyclopaediaLocked = item.encyclopaediaLocked && !ownedItems.includes(item.id) && (caughtSpecies || []).length < FISH_CATALOG_CLIENT.length;
        if (encyclopaediaLocked) {
          const caught = (caughtSpecies || []).length;
          const total = FISH_CATALOG_CLIENT.length;
          return (
            <div key={item.id} className="shop-item shop-item--locked">
              <span className="shop-item-emoji" style={{ opacity: 0.4 }}>{item.emoji}</span>
              <div className="shop-item-info">
                <div className="shop-item-name" style={{ opacity: 0.5 }}>{item.name}</div>
                <div className="shop-item-desc" style={{ opacity: 0.5 }}>🔒 Complete your Encyclopaedia to unlock ({caught}/{total} species)</div>
              </div>
              <div className="shop-item-action">
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted, #888)' }}>{caught}/{total}</span>
              </div>
            </div>
          );
        }

        if (tierLocked && !tierUnlocked) {
          return (
            <div key={item.id} className="shop-item shop-item--locked">
              <span className="shop-item-emoji" style={{ opacity: 0.4 }}>{item.emoji}</span>
              <div className="shop-item-info">
                <div className="shop-item-name" style={{ opacity: 0.5 }}>{item.name}</div>
                <div className="shop-item-desc" style={{ opacity: 0.5 }}>🔒 Unlocks at {fmt(tierThreshold)} total wins gained</div>
              </div>
              <div className="shop-item-action">
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted, #888)' }}>{fmt(cumulativeWins || 0)}/{fmt(tierThreshold)}</span>
              </div>
            </div>
          );
        }

        const isClass = CLASS_IDS.has(item.id);
        const isClassEquipped = isClass && equippedClass === item.id.replace('class_', '');
        return (
          <ShopItem key={item.id} item={item}
            isSkin={false}
            isSingularity={item.id === 'singularity'}
            isCosmetic={isCosmetic}
            isClass={isClass}
            isClassEquipped={isClassEquipped}
            owned={!item.infinite && ownedItems.includes(item.id)}
            equipped={false}
            active={isCosmetic && activeCosmetics.includes(item.id)}
            canAfford={!atMaxLevel && balance >= displayCost}
            infLevel={infLevel}
            displayCost={atMaxLevel ? 0 : displayCost}
            procStreak={procStreak}
            onBuy={onBuy} onEquip={onEquip} onEquipCosmetic={onEquipCosmetic}
            onEquipClass={onEquipClass}
          />
        );
      })}
    </React.Fragment>
  );

  const exchangeRate = computeFishExchangeRate(fishExchangeTotal || 0);

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
          <>
            {functionalSections.map(renderSection)}
            {(fishClicks > 0 || wins > 0) && (
              <React.Fragment>
                <div className="shop-section-label">── 🔄 Fish Exchange ──</div>
                {fishClicks > 0 && (
                  <div className="fish-exchange-panel">
                    <div className="fish-exchange-desc">
                      Convert 🐟 Fish Bucks → 🏆 Wins at ~{exchangeRate}¢ per buck
                      {exchangeRate < 100 && <span className="fish-exchange-rate-warn"> (1:1 for first 25M, then decays)</span>}
                    </div>
                    <div className="fish-exchange-buttons">
                      <button className="shop-buy-btn can-afford" onClick={() => onFishExchange('10pct')}>
                        Exchange 10% ({fmt(Math.max(1, Math.floor(fishClicks / 10)))} 🐟)
                      </button>
                      <button className="shop-buy-btn can-afford" onClick={() => onFishExchange('all')}>
                        Exchange All ({fmt(fishClicks)} 🐟)
                      </button>
                    </div>
                  </div>
                )}
                {wins > 0 && (
                  <div className="wins-exchange-panel">
                    <div className="wins-exchange-desc">
                      Convert 🏆 Wins → 🐟 Fish Bucks at 1:1
                    </div>
                    <div className="fish-exchange-buttons">
                      <button className="shop-buy-btn can-afford" onClick={() => onWinsExchange('10pct')}>
                        Exchange 10% ({fmt(Math.max(1, Math.floor(wins / 10)))} 🏆)
                      </button>
                      <button className="shop-buy-btn can-afford" onClick={() => onWinsExchange('all')}>
                        Exchange All ({fmt(wins)} 🏆)
                      </button>
                    </div>
                  </div>
                )}
              </React.Fragment>
            )}
          </>
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
              <div className="stats-row"><span>Season Fish Bucks</span><span>{fmt(stats.total_fish_clicks)}</span></div>
              <div className="stats-row"><span>Fastest Catch</span><span>{stats.fastest_catch_pct != null ? `🎯 ${stats.fastest_catch_pct}%` : '—'}</span></div>
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

// ── Patch Notes Panel ──────────────────────────────────────────────────────
function PatchNotesPanel({ open, onClose }) {
  const [md, setMd] = useState(null);
  useEffect(() => {
    if (!open || md !== null) return;
    apiFetch('/api/patch-notes').then(r => { if (r.ok) setMd(r.data.content); });
  }, [open]);
  if (!open) return null;
  const html = md != null ? window.DOMPurify.sanitize(window.marked.parse(md)) : null;
  return (
    <div className="stats-overlay" onClick={onClose}>
      <div className="patch-notes-card" onClick={e => e.stopPropagation()}>
        <div className="stats-title">📋 Patch Notes</div>
        <button className="stats-close-btn" onClick={onClose}>✕</button>
        <div className="patch-notes-body">
          {html
            ? <div className="patch-notes-content" dangerouslySetInnerHTML={{ __html: html }} />
            : <div className="stats-loading">Loading…</div>}
        </div>
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
      storeCsrf(data);
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
    const expiresAt = new Date(filledAt).getTime() + 1800 * 1000;
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
  const [justFilled, setJustFilled] = useState(!!pot.active);

  // Sync when parent pot state changes (e.g. on load)
  useEffect(() => { setLocalPot(pot); setJustFilled(!!pot.active); }, [pot]);

  // Poll every 5s for live updates — drives celebration state from server
  useEffect(() => {
    const id = setInterval(() => {
      apiFetch('/api/community-pot').then(r => {
        if (r.ok) {
          setLocalPot(r.data);
          setJustFilled(!!r.data.active);
        }
      });
    }, 5000);
    return () => clearInterval(id);
  }, []);

  const handleContribute = async (amount) => {
    const { ok, data } = await apiGame('/api/community-pot/contribute', {
      method: 'POST',
      body: JSON.stringify({ amount }),
    });
    if (ok) {
      setLocalPot(prev => ({ ...prev, total_contributed: data.pot_total, target: data.pot_target, filled: data.pot_filled, active: data.pot_active, filled_at: data.filled_at, win_chance_pct: data.win_chance_pct }));
      onContribute(data.fish_clicks);
      setJustFilled(!!data.pot_active);
    }
  };

  const total    = localPot.total_contributed || 0;
  const target   = localPot.target || 1_000;
  const pct      = Math.min(100, (total / target) * 100);
  const winRate  = (localPot.win_chance_pct || 50.0).toFixed(1);
  const active   = localPot.active;
  const countdown = usePotCountdown(localPot.filled_at, active);

  // Ghost bars: how far the bar would extend if clicks were contributed now
  const userClicks = fishClicks || 0;
  const allPendingClicks = localPot.total_pending_clicks || 0;
  const userGhostPct = active ? 0 : Math.min(100, ((total + userClicks) / target) * 100);
  const allGhostPct  = active ? 0 : Math.min(100, ((total + allPendingClicks) / target) * 100);

  return (
    <div className={`community-pot-bar${justFilled ? ' community-pot-active' : ''}`}>
      <div className="community-pot-inner">
        <span className="community-pot-label">🎣 Community Pot</span>
        <div className="community-pot-progress">
          {allGhostPct > pct && <div className="community-pot-ghost-all" style={{ width: allGhostPct + '%' }} title="All players contributing their clicks" />}
          {userGhostPct > pct && <div className="community-pot-ghost-user" style={{ width: userGhostPct + '%' }} title="Your clicks contributed" />}
          <div className="community-pot-fill" style={{ width: pct + '%' }} title="Current pot total" />
        </div>
        <span className="community-pot-count">{fmt(total)} / {fmt(target)}</span>
        {justFilled ? (
          <>
            <span className="community-pot-bonus">🎉 Win Rate {winRate}%</span>
            <span className="season-countdown">{fmtCountdown(countdown)}</span>
          </>
        ) : (
          <>
            <div className="community-pot-buttons">
              <button onClick={() => handleContribute('10pct')} disabled={fishClicks < 1}>+{fmt(Math.max(1, Math.floor(target / 10)))}</button>
              <button onClick={() => handleContribute('all')} disabled={fishClicks < 1}>All</button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// ── Game App ───────────────────────────────────────────────────────────────
function GameApp({ username, gameState, onLogout, onSessionExpired }) {
  const canvasRef = useRef(null);
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
  const [caughtSpecies, setCaughtSpecies]     = useState(gameState.caught_species || []);
  const [fishingLuckyNext, setFishingLuckyNext] = useState(gameState.fishing_lucky_next || false);
  const [showEncyclopedia, setShowEncyclopedia] = useState(false);
  const [bonusEarned, setBonusEarned] = useState(0);
  const [echoTriggered, setEchoTriggered]               = useState(false);
  const [jackpotHit, setJackpotHit]                     = useState(false);
  const [resilienceTriggered, setResilienceTriggered]   = useState(false);
  const [luckySevenTriggered, setLuckySevenTriggered]   = useState(false);
  const [fortuneCharmTriggered, setFortuneCharmTriggered] = useState(false);
  const [regenRechargeWins, setRegenRechargeWins] = useState(gameState.regen_recharge_wins || 0);
  const [catchUpSummary, setCatchUpSummary] = useState(null);
  const [fishCatchUpSummary, setFishCatchUpSummary] = useState(null);
  const [happyHour, setHappyHour]     = useState(gameState.happy_hour || false);
  const [happyHourDismissed, setHappyHourDismissed] = useState(false);
  const [catchupBonus, setCatchupBonus] = useState(false);
  const [ownedItems, setOwnedItems]   = useState(gameState.owned_items);
  const [equippedFish, setEquippedFish] = useState(gameState.equipped_fish);
  const [activeCosmetics, setActiveCosmetics] = useState(gameState.active_cosmetics || []);
  const [equippedClass, setEquippedClass]   = useState(gameState.equipped_class || null);
  const [procStreak, setProcStreak]         = useState(gameState.proc_streak || 0);
  const [fishExchangeTotal, setFishExchangeTotal] = useState(gameState.fish_exchange_total || 0);
  const [showStats, setShowStats]     = useState(false);
  const [showPatchNotes, setShowPatchNotes] = useState(false);
  const [toast, setToast]             = useState(null);
  const [season, setSeason]           = useState(gameState.season || null);
  const [communityPot, setCommunityPot] = useState(gameState.community_pot || { total_contributed: 0, target: 1_000, filled: false, active: false, win_chance_pct: 50.0 });
  const [spinCount, setSpinCount]     = useState(gameState.spin_count || 0);
  const [winCount, setWinCount]       = useState(gameState.win_count || 0);
  // T106: cumulative_wins tracks lifetime value of wins gained. Used for
  // tier-2/3 unlock gating (replaces winCount for that purpose).
  const [cumulativeWins, setCumulativeWins] = useState(gameState.cumulative_wins || 0);
  const [lowSpec, setLowSpec]         = useState(() => gameState.low_spec_mode ?? localStorage.getItem('lowSpecMode') === 'true');
  const [parallaxEnabled, setParallaxEnabled] = useState(() => localStorage.getItem('parallaxEnabled') !== 'false');
  const [shopCollapsed, setShopCollapsed] = useState(false);
  const [diceRolling, setDiceRolling]     = useState(false);
  const [diceResult, setDiceResult]       = useState(null);
  const [diceCharges, setDiceCharges]     = useState(gameState.dice_charges ?? 1);
  const [diceLastRecharge, setDiceLastRecharge] = useState(gameState.dice_last_recharge || new Date().toISOString());
  const [diceRolledSinceSpin, setDiceRolledSinceSpin] = useState(gameState.dice_rolled_since_spin ?? false);
  const [isMobile, setIsMobile] = useState(() => window.innerWidth <= 768);
  const [mobilePanel, setMobilePanel] = useState(null);
  const [showChat, setShowChat] = useState(() => localStorage.getItem('chat_open') !== 'false');
  const fireMode = 2; // Mix mode
  const [wheelRotation, setWheelRotation] = useState(0);
  const wheelRotationRef = useRef(0);
  const [infLevels, setInfLevels]     = useState({
    clickmult_inf: gameState.clickmult_inf_level || 0,
  });
  const WHEEL_SPIN_SPEED = 1.5; // seconds

  // Season 8: manual spin state (tab-lock ID mirrors HiatusWheel pattern)
  const [spinning, setSpinning]         = useState(false);
  const spinningRef                     = useRef(false);
  const tabIdRef                        = useRef((() => {
    let id = sessionStorage.getItem('wheel_tab_id');
    if (!id) { id = Math.random().toString(36).slice(2) + Date.now().toString(36); sessionStorage.setItem('wheel_tab_id', id); }
    return id;
  })());
  // Season 8: auto-spin budget (0 = inactive)

  const toggleMobilePanel = useCallback((panel) => {
    setMobilePanel(prev => prev === panel ? null : panel);
  }, []);

  const diceMaxCharges = useMemo(() => {
    if (ownedItems.includes('dice_charge_4')) return 4;
    if (ownedItems.includes('dice_charge_3')) return 3;
    if (ownedItems.includes('dice_charge_2')) return 2;
    return 1;
  }, [ownedItems]);

  // fishPanelScale: controls the CSS transform scale on the fishing panel
  const fishPanelScale = useMemo(() =>
    activeCosmetics.includes('fishsize_small') ? 0.5 :
    activeCosmetics.includes('fishsize_3') ? 2.0 :
    activeCosmetics.includes('fishsize_2') ? 1.6 :
    activeCosmetics.includes('fishsize_1') ? 1.3 : 1.0,
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
    if (activeCosmetics.includes('theme_vintage')) return 'vintage';
    if (activeCosmetics.includes('theme_aurora')) return 'aurora';
    if (activeCosmetics.includes('theme_frost')) return 'frost';
    if (activeCosmetics.includes('theme_ember')) return 'ember';
    if (activeCosmetics.includes('theme_tidal')) return 'tidal';
    if (activeCosmetics.includes('page_season8')) return 'casino';
    if (activeCosmetics.includes('page_season7')) return 'wormhole';
    if (activeCosmetics.includes('page_season5')) return 'bioluminescence';
    if (activeCosmetics.includes('page_season6')) return 'night_ocean';
    return 'default';
  }, [activeCosmetics]);

  const bgClass = useMemo(() => {
    if (activeCosmetics.includes('bg_cosmic'))  return 'bg-cosmic';
    if (activeCosmetics.includes('bg_abyss'))   return 'bg-abyss';
    if (activeCosmetics.includes('bg_forest'))  return 'bg-forest';
    if (activeCosmetics.includes('bg_inferno')) return 'bg-inferno';
    if (activeCosmetics.includes('bg_royal'))   return 'bg-royal';
    if (activeCosmetics.includes('bg_ocean'))   return 'bg-ocean';
    return 'bg-ocean';  // Season 5 default
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
    if (activeCosmetics.includes('page_season8')) return 'page-season8';
    if (activeCosmetics.includes('page_season7')) return 'page-season7';
    if (activeCosmetics.includes('page_season1')) return 'page-season1';
    if (activeCosmetics.includes('page_season2')) return 'page-season2';
    if (activeCosmetics.includes('page_season3')) return 'page-season3';
    if (activeCosmetics.includes('page_season4')) return 'page-season4';
    if (activeCosmetics.includes('page_season5')) return 'page-season5';
    if (activeCosmetics.includes('page_season6')) return 'page-season6';
    return '';
  }, [activeCosmetics]);

  const wormholeActive = activeCosmetics.includes('page_season7');
  const casinoActive   = activeCosmetics.includes('page_season8');

  const fishTimerRef       = useRef(null);
  const toastTimerRef      = useRef(null);
  const confettiTimerRef   = useRef(null);
  const showResultRef      = useRef(false);
  const activeCosmeticsRef = useRef(activeCosmetics);
  const lowSpecRef         = useRef(lowSpec);
  const tickPendingRef     = useRef(false);
  const resultAutoCloseRef = useRef(null);
  const wheelThemeRef      = useRef(null);
  // T80: a ref mirroring wheelProbabilities so the wheel-mode-change handler
  // can read the latest value from a closure that has stale state.
  const wheelProbabilitiesRef = useRef(null);
  const activeWheelModeRef    = useRef(null);
  // T97 R2 / wager-stale: a ref mirroring stake so the spin handler can
  // read the latest value. React 18 useCallback closures in this build
  // are not reliably re-creating when `stakePct` changes — the label
  // updates correctly but the spin handler's closure keeps the old
  // value. T102: defaults to 0 (safe) instead of 1 (old 1× default).
  const stakeRef              = useRef(gameState.wager_last_stake ?? 0);

  useEffect(() => { activeCosmeticsRef.current = activeCosmetics; }, [activeCosmetics]);
  useEffect(() => { lowSpecRef.current = lowSpec; }, [lowSpec]);
  useEffect(() => { wheelThemeRef.current = wheelTheme; }, [wheelTheme]);
  useEffect(() => { wheelProbabilitiesRef.current = wheelProbabilities; }, [wheelProbabilities]);
  useEffect(() => { activeWheelModeRef.current = activeWheelMode; }, [activeWheelMode]);
  useEffect(() => { stakeRef.current = stakePct; }, [stakePct]);
  useEffect(() => {
    localStorage.setItem('lowSpecMode', lowSpec);
    document.body.classList.toggle('low-spec', lowSpec);
    apiGame('/api/settings', { method: 'POST', body: JSON.stringify({ low_spec_mode: lowSpec }) });
    const iframe = document.getElementById('seabed-bg');
    if (iframe) {
      iframe.src = lowSpec ? '/static/seabed-static.html' : '/static/seabed-animated.html';
    }
  }, [lowSpec]);

  useEffect(() => {
    const show = bgClass === 'bg-ocean' && !wormholeActive && !casinoActive;
    const iframe = document.getElementById('seabed-bg');
    const overlay = document.getElementById('seabed-overlay');
    if (iframe)  iframe.style.display  = show ? 'block' : 'none';
    if (overlay) overlay.style.display = show ? 'block' : 'none';
  }, [bgClass, wormholeActive, casinoActive]);

  useEffect(() => {
    setSessionExpiredHandler(onSessionExpired);
    return () => setSessionExpiredHandler(null);
  }, [onSessionExpired]);

  useEffect(() => {
    const currentNumber = season ? season.season_number : null;
    const id = setInterval(async () => {
      const r = await apiFetch('/api/season');
      if (!r.ok) return;
      if (currentNumber !== null && r.data.season_number !== currentNumber) {
        showToast(`Season ${season.season_name || currentNumber} has ended! Season ${r.data.season_name || r.data.season_number} begins!`);
        const gs = await apiGame('/api/state');
        if (gs.ok) {
          setSeason(gs.data.season);
          setWins(gs.data.wins);
          setLosses(gs.data.losses);
          setStreak(gs.data.streak);
          setFishClicks(gs.data.fish_clicks);
          setOwnedItems(gs.data.owned_items);
          setEquippedFish(gs.data.equipped_fish);
          setRegenRechargeWins(gs.data.regen_recharge_wins || 0);
          setActiveCosmetics(gs.data.active_cosmetics || []);
          setInfLevels({
            clickmult_inf: gs.data.clickmult_inf_level || 0,
          });
          setEquippedClass(gs.data.equipped_class || null);
          setProcStreak(gs.data.proc_streak || 0);
          setFishExchangeTotal(gs.data.fish_exchange_total || 0);
          if (gs.data.caught_species) setCaughtSpecies(gs.data.caught_species);
          setFishingLuckyNext(gs.data.fishing_lucky_next || false);
          if (gs.data.dice_charges != null) setDiceCharges(gs.data.dice_charges);
          if (gs.data.dice_last_recharge) setDiceLastRecharge(gs.data.dice_last_recharge);
          setDiceRolledSinceSpin(gs.data.dice_rolled_since_spin ?? false);
          // Season 8 state sync
          if (gs.data.prestige_level != null) setPrestigeLevel(gs.data.prestige_level);
          if (gs.data.legacy_wins != null) setLegacyWins(gs.data.legacy_wins);
          if (gs.data.onboarding_step != null) setOnboardingStep(gs.data.onboarding_step);
          if (gs.data.wager_streak != null) setWagerStreak(gs.data.wager_streak);
          if (gs.data.active_wheel_mode != null) setActiveWheelMode(gs.data.active_wheel_mode);
          if (gs.data.available_wheel_modes != null) setAvailableWheelModes(gs.data.available_wheel_modes);
          if (gs.data.wager_tokens != null) setWagerTokens(gs.data.wager_tokens);
          if (gs.data.aquarium_species != null) setAquariumSpecies(gs.data.aquarium_species);
          if (gs.data.guard_charges != null) setGuardCharges(gs.data.guard_charges);
          if (gs.data.bounties != null) setBounties(gs.data.bounties);
          if (gs.data.community_goal != null) setCommunityGoal(gs.data.community_goal);
          if (gs.data.singularity != null) setSingularity(gs.data.singularity);
          // T80: sync wheelProbabilities + gravity drift from the new state.
          if (gs.data.wheel_probabilities != null) setWheelProbabilities(gs.data.wheel_probabilities);
          if (gs.data.gravity_drift != null) setGravityDrift(gs.data.gravity_drift);
        }
      } else {
        setSeason(r.data);
      }
    }, 60000);
    return () => clearInterval(id);
  }, [season ? season.season_number : null]); // eslint-disable-line

  useEffect(() => {
    if (!season) return;
    const key = `patchNotesSeen_s${season.season_number}`;
    if (!localStorage.getItem(key)) {
      setShowPatchNotes(true);
    }
  }, [season ? season.season_number : null]); // eslint-disable-line

  useEffect(() => {
    const classes = [bgClass, pageThemeClass].filter(Boolean).join(' ');
    document.body.className = classes;
    return () => { document.body.className = ''; };
  }, [bgClass, pageThemeClass]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    drawWheel(canvas, wheelTheme, activeWheelMode, null);
  }, [wheelTheme, activeWheelMode]);

  const showToast = useCallback((msg) => {
    setToast(msg);
    if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
    toastTimerRef.current = setTimeout(() => setToast(null), 3000);
  }, []);

  const handleClosePatchNotes = useCallback(() => {
    setShowPatchNotes(false);
    if (season) localStorage.setItem(`patchNotesSeen_s${season.season_number}`, '1');
  }, [season]);

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
      setRegenRechargeWins(data.regen_recharge_wins ?? 0);
      if (data.active_cosmetics) setActiveCosmetics(data.active_cosmetics);
      if (data.clickmult_inf_level != null) {
        setInfLevels(prev => ({ ...prev, clickmult_inf: data.clickmult_inf_level }));
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

  const handleEquipClass = useCallback(async (classItemId) => {
    const isCurrentlyEquipped = equippedClass === classItemId.replace('class_', '');
    const newClassId = isCurrentlyEquipped ? null : classItemId;
    const { ok, data } = await apiGame('/api/equip-class', {
      method: 'POST',
      body: JSON.stringify({ class_id: newClassId }),
    });
    if (ok) setEquippedClass(data.equipped_class);
    else showToast(data.error || 'Equip failed');
  }, [equippedClass, showToast]);

  const handleFishExchange = useCallback(async (amountType) => {
    const { ok, data } = await apiGame('/api/fish-exchange', {
      method: 'POST',
      body: JSON.stringify({ amount: amountType }),
    });
    if (ok) {
      setFishClicks(data.fish_clicks);
      setWins(data.wins);
      setFishExchangeTotal(prev => prev + data.fish_spent);
      showToast(`Exchanged ${fmt(data.fish_spent)} 🐟 → +${fmt(data.wins_earned)} 🏆`);
    } else {
      showToast(data.error || 'Exchange failed');
    }
  }, [showToast]);

  const handleWinsExchange = useCallback(async (amountType) => {
    const { ok, data } = await apiGame('/api/wins-exchange', {
      method: 'POST',
      body: JSON.stringify({ amount: amountType }),
    });
    if (ok) {
      setWins(data.wins);
      setFishClicks(data.fish_clicks);
      showToast(`Exchanged ${fmt(data.wins_spent)} 🏆 → +${fmt(data.fish_earned)} 🐟`);
    } else {
      showToast(data.error || 'Exchange failed');
    }
  }, [showToast]);

  const handleDiceRoll = useCallback(async () => {
    if (diceRolling) return;
    setDiceRolling(true);
    setDiceResult(null);
    const prevStreak = streak;
    const { ok, data } = await apiGame('/api/roll-dice', {
      method: 'POST',
      body: JSON.stringify({}),
    });
    if (!ok) {
      showToast(data.error || 'Roll failed');
      setDiceRolling(false);
      return;
    }
    setTimeout(() => {
      const streakDelta = data.streak - prevStreak;
      setDiceResult({
        die1: data.die1, die2: data.die2, die3: data.die3 ?? null,
        dice_sum: data.dice_sum,
        streak_delta: streakDelta, cursed: data.cursed, blessed: data.blessed,
        cursed_triple: data.cursed_triple ?? false,
        blessed_triple: data.blessed_triple ?? false,
        streak_before: prevStreak, streak_after: data.streak,
        pending: true,
      });
      // Streak is applied by the next /api/tick, not immediately
      if (data.dice_charges != null) setDiceCharges(data.dice_charges);
      if (data.dice_last_recharge) setDiceLastRecharge(data.dice_last_recharge);
      setDiceRolledSinceSpin(true);
      setDiceRolling(false);
    }, lowSpec ? 100 : 1200);
  }, [diceRolling, streak, lowSpec, showToast]);

  // Shared post-spin state update (used both directly and via guard callback)
  const applySpinResult = useCallback((data) => {
    setResult(data.result);
    if (data.wins_delta)   setWins(prev => prev + data.wins_delta);
    if (data.losses_delta) setLosses(prev => prev + data.losses_delta);
    setStreak(data.streak);
    setRegenRechargeWins(data.regen_recharge_wins ?? 0);
    if (data.owned_items) {
      const spinResult = new Set(data.owned_items);
      // Sync guard from spin result (can be removed by guard block).
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
    if (data.new_spin_count != null) setSpinCount(data.new_spin_count);
    // T106: cumulative_wins is the new tier-gating metric. Server echoes the
    // new value on every spin/tick so the shop tier-locked text updates live
    // without waiting for the next /api/state poll.
    if (data.cumulative_wins != null) setCumulativeWins(data.cumulative_wins);
    if (data.active_cosmetics) setActiveCosmetics(data.active_cosmetics);
    if (data.dice_charges != null) setDiceCharges(data.dice_charges);
    if (data.dice_last_recharge) setDiceLastRecharge(data.dice_last_recharge);
    setDiceRolledSinceSpin(false);
    if (data.wins_delta > 0) setWinCount(prev => prev + 1);
    if (data.proc_streak != null) setProcStreak(data.proc_streak);
    // Season 8: update wager state from spin result
    if (data.wager_streak != null) setWagerStreak(data.wager_streak);
    if (data.stake != null) setWagerLastStake(data.stake);
    if (data.onboarding_advance) {
      setOnboardingStep(prev => Math.min(prev + 1, 5));
    }
    // Season 8: refresh bounties & community goal after every spin
    refreshBountiesAndGoal();
    // Season 8: update community goal from state poll
    setShieldFeedback(data.shield_used ? {
      type: data.shield_used_type,
      broke: data.shield_broke,
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
  }, [showToast]);

  // Dismiss the result banner smoothly
  const dismissResult = useCallback(() => {
    if (!showResultRef.current) return;
    setHideResult(true);
    setShowResultSync(false);
    setConfetti(false);
    setTimeout(() => { setHideResult(false); setResult(null); setShieldFeedback(null); }, 350);
  }, []);

  // Schedule auto-dismissal of the result banner after 2.5s
  const scheduleResultDismiss = useCallback(() => {
    if (resultAutoCloseRef.current) clearTimeout(resultAutoCloseRef.current);
    resultAutoCloseRef.current = setTimeout(dismissResult, 2500);
  }, [dismissResult]);

  const applyFishCatchUp = useCallback((fc) => {
    if (!fc || fc.fish_count === 0) return;
    setFishClicks(fc.fish_clicks);
    if (fc.new_species && fc.new_species.length > 0) {
      setCaughtSpecies(prev => {
        const s = new Set(prev);
        fc.new_species.forEach(id => s.add(id));
        return [...s];
      });
    }
    const hrs = Math.floor(fc.elapsed_seconds / 3600);
    const mins = Math.floor((fc.elapsed_seconds % 3600) / 60);
    const timeStr = hrs > 0 ? `${hrs}h ${mins}m` : `${mins}m`;
    setFishCatchUpSummary(`🎣 Away ${timeStr} — ${fc.fish_count} fish auto-caught (+${fmt(fc.total_value)} 🐟)`);
    setTimeout(() => setFishCatchUpSummary(null), 5000);
  }, []);

  // Season 8: manual spin (replaces always-on auto-spin as the primary game action)
  const handleManualSpin = useCallback(async () => {
    if (spinningRef.current) return;
    spinningRef.current = true;
    setSpinning(true);
    try {
      const res = await apiGame('/api/spin', {
        method: 'POST',
        body: JSON.stringify({ tab_id: tabIdRef.current, stake: stakeRef.current }),
      });
      if (!res.ok) {
        showToast(res.data?.error || 'Spin failed');
        spinningRef.current = false;
        setSpinning(false);
        return;
      }
      const data = res.data;
      // Animate wheel to the returned segment angle
      const seg = data.angle % 360;
      const nextRot = Math.ceil((wheelRotationRef.current + 2 * 360 - seg) / 360) * 360 + seg;
      wheelRotationRef.current = nextRot;
      setWheelRotation(nextRot);

      if (data.double_down_pending != null) setDoubleDownPending(data.double_down_pending);
      if (data.wager_insurance_armed != null) setWagerInsuranceArmed(data.wager_insurance_armed);
      if (data.wager_insurance_charges != null) setWagerInsuranceCharges(data.wager_insurance_charges);
      if (data.wager_last_win_amount != null) setWagerLastWinAmount(data.wager_last_win_amount);
      // T80: server's drift-adjusted probabilities + new gravity drift.
      if (data.wheel_probabilities != null) setWheelProbabilities(data.wheel_probabilities);
      if (data.gravity_drift != null) setGravityDrift(data.gravity_drift);
      // T102: server echoes the actual stake % it used (clamped to player's
      // max). Sync stakePct + wagerLastStake so the slider position and
      // wager panel match what the spin actually used.
      if (data.stake != null) {
        setStakePct(data.stake);
        setWagerLastStake(data.stake);
      }
      if (data.max_stake_pct != null) setMaxStakePct(data.max_stake_pct);
      // T105: server doesn't echo stake_value; the post-spin update lives
      // in applySpinResult (below) which sees the new wins/losses.
      if (canvasRef.current) drawWheel(
        canvasRef.current, wheelThemeRef.current || 'default',
        activeWheelModeRef.current, data.wheel_probabilities || null,
      );

      // Dismiss lingering result before showing new one
      if (showResultRef.current) dismissResult();
      setBonusEarned(0); setEchoTriggered(false); setJackpotHit(false);
      setResilienceTriggered(false); setLuckySevenTriggered(false); setFortuneCharmTriggered(false);

      setTimeout(() => {
        if (data.guard_triggered) {
          setGuardState({ blocked: data.guard_blocked });
          guardCompleteRef.current = () => {
            setGuardState(null);
            applySpinResult(data);
            scheduleResultDismiss();
          };
        } else {
          applySpinResult(data);
          scheduleResultDismiss();
        }
        spinningRef.current = false;
        setSpinning(false);
      }, Math.round(WHEEL_SPIN_SPEED * 1000) + 100);
    } catch {
      showToast('Spin failed');
      spinningRef.current = false;
      setSpinning(false);
    }
  }, [showToast, applySpinResult, scheduleResultDismiss, dismissResult]);

  // T107: auto-spin start/stop handlers. The auto-spin server endpoint
  // runs at 0% stake (no escrow) and prevents DD/insurance; the UI hides
  // the stake slider while active.
  const handleStartAutoSpin = useCallback(async () => {
    const { ok, data } = await apiGame('/api/auto-spin/start', {
      method: 'POST',
      body: JSON.stringify({ budget: 100 }),
    });
    if (!ok) { showToast(data?.error || 'Auto-spin start failed'); return; }
    setAutoSpinActive(true);
    setAutoSpinBudget(data.budget || 100);
  }, [showToast]);

  const handleStopAutoSpin = useCallback(async () => {
    const { ok, data } = await apiGame('/api/auto-spin/stop', {
      method: 'POST',
      body: '{}',
    });
    if (!ok) { showToast(data?.error || 'Auto-spin stop failed'); return; }
    setAutoSpinActive(false);
    setAutoSpinBudget(0);
  }, [showToast]);

  const tick = useCallback(async () => {
    if (tickPendingRef.current) return;
    tickPendingRef.current = true;
    try {
      const res = await apiGame('/api/tick', { method: 'POST', body: JSON.stringify({}) });
      if (!res.ok) return;
      const data = res.data;

      if (data.auto_spin_active === false) {
        setAutoSpinActive(false);
        return;
      }
      if (data.auto_spin_active === true) {
        setAutoSpinActive(true);
        if (data.auto_spin_budget != null) setAutoSpinBudget(data.auto_spin_budget);
      }

      if (data.happy_hour != null) setHappyHour(data.happy_hour);

      if (data.started) return; // Wheel just initialised — nothing to animate yet

      if (data.catch_up) {
        // Many spins processed offline — show summary, update state silently
        if (data.state) {
          if (data.state.wins   != null) setWins(data.state.wins);
          if (data.state.losses != null) setLosses(data.state.losses);
          if (data.state.streak != null) setStreak(data.state.streak);
          if (data.state.owned_items)    setOwnedItems(prev => {
            const s = new Set(data.state.owned_items);
            const withoutGuard = prev.filter(id => id !== 'guard');
            return s.has('guard') ? [...withoutGuard, 'guard'] : withoutGuard;
          });
          if (data.state.regen_recharge_wins != null) setRegenRechargeWins(data.state.regen_recharge_wins);
          if (data.state.active_cosmetics)            setActiveCosmetics(data.state.active_cosmetics);
          if (data.state.spin_count != null) setSpinCount(data.state.spin_count);
          if (data.state.win_count  != null) setWinCount(data.state.win_count);
          if (data.state.dice_charges != null) setDiceCharges(data.state.dice_charges);
          if (data.state.catchup_bonus_active != null) setCatchupBonus(data.state.catchup_bonus_active);
          if (data.state.proc_streak != null) setProcStreak(data.state.proc_streak);
          if (data.state.cumulative_wins != null) setCumulativeWins(data.state.cumulative_wins);
          setDiceRolledSinceSpin(false);
        }
        const hrs = Math.floor(data.elapsed_seconds / 3600);
        const mins = Math.floor((data.elapsed_seconds % 3600) / 60);
        const timeStr = hrs > 0 ? `${hrs}h ${mins}m` : `${mins}m`;
        setCatchUpSummary(`⏰ Away ${timeStr} — ${data.spins_processed} spins processed`);
        setTimeout(() => setCatchUpSummary(null), 5000);
        if (data.fish_catchup) applyFishCatchUp(data.fish_catchup);
        return;
      }

      if (!data.spins || data.spins.length === 0) return;

      const spinResult = data.spins[data.spins.length - 1];

      // Dismiss any lingering result before showing the new one
      if (showResultRef.current) dismissResult();

      setBonusEarned(0); setEchoTriggered(false); setJackpotHit(false);
      setResilienceTriggered(false); setLuckySevenTriggered(false); setFortuneCharmTriggered(false);

      // Advance wheel to the correct result segment (same formula as HiatusWheel)
      const seg = spinResult.angle % 360;
      const nextRot = Math.ceil((wheelRotationRef.current + 2 * 360 - seg) / 360) * 360 + seg;
      wheelRotationRef.current = nextRot;
      setWheelRotation(nextRot);

      setTimeout(() => {
        if (spinResult.guard_triggered) {
          setGuardState({ blocked: spinResult.guard_blocked });
          guardCompleteRef.current = () => {
            setGuardState(null);
            applySpinResult(spinResult);
            scheduleResultDismiss();
          };
        } else {
          applySpinResult(spinResult);
          scheduleResultDismiss();
        }
      }, Math.round(WHEEL_SPIN_SPEED * 1000) + 100);

      if (data.state) {
        if (data.state.dice_charges != null) setDiceCharges(data.state.dice_charges);
        if (data.state.catchup_bonus_active != null) setCatchupBonus(data.state.catchup_bonus_active);
        if (data.state.dice_rolled_since_spin != null) {
          setDiceRolledSinceSpin(data.state.dice_rolled_since_spin);
          if (!data.state.dice_rolled_since_spin) setDiceResult(null);
        }
      }
      if (data.fish_catchup) applyFishCatchUp(data.fish_catchup);
    } finally {
      tickPendingRef.current = false;
    }
  }, [applySpinResult, applyFishCatchUp, dismissResult, scheduleResultDismiss]);


  // Poll happy_hour status every minute (in case of time zone changes or missed state update)
  useEffect(() => {
    const id = setInterval(() => {
      apiFetch('/api/season').then(r => {
        if (r.ok && r.data.happy_hour != null) setHappyHour(r.data.happy_hour);
      });
    }, 60000);
    return () => clearInterval(id);
  }, []);

  const handleLogout = async () => {
    await apiFetch('/api/logout', { method: 'POST', body: '{}' });
    onLogout();
  };

  // ── Season 8 state ─────────────────────────────────────────────────────────
  const [prestigeLevel, setPrestigeLevel]           = useState(gameState.prestige_level || 0);
  const [prestigeCount, setPrestigeCount]           = useState(gameState.prestige_count || 0);
  const [legacyWins, setLegacyWins]                 = useState(gameState.legacy_wins || 0);
  const [onboardingStep, setOnboardingStep]         = useState(gameState.onboarding_step || 0);
  const [wagerStreak, setWagerStreak]               = useState(gameState.wager_streak || 0);
  const [wagerLastStake, setWagerLastStake]         = useState(gameState.wager_last_stake ?? 0);
  const [doubleDownPending, setDoubleDownPending]   = useState(gameState.double_down_pending || false);
  const [wagerBankedWins, setWagerBankedWins]       = useState(gameState.wager_banked_wins || 0);
  const [wagerLastWinAmount, setWagerLastWinAmount] = useState(gameState.wager_last_win_amount || 0);
  const [wagerInsuranceCharges, setWagerInsuranceCharges] = useState(gameState.wager_insurance_charges || 0);
  const [wagerInsuranceArmed, setWagerInsuranceArmed]   = useState(gameState.wager_insurance_armed || false);
  const [activeWheelMode, setActiveWheelMode]       = useState(gameState.active_wheel_mode || 'steady');
  const [availableWheelModes, setAvailableWheelModes] = useState(gameState.available_wheel_modes || ['steady', 'volatile']);
  // T80: server-provided wheel probabilities (drift-adjusted for gravity,
  // static for other modes). null → fall back to WHEEL_MODE_DRAW.
  const [wheelProbabilities, setWheelProbabilities] = useState(gameState.wheel_probabilities || null);
  // T80: gravity drift echoed by the server; not consumed by the wheel
  // itself but kept in state for UI badges / debug.
  const [gravityDrift, setGravityDrift]             = useState(gameState.gravity_drift || 0);
  const [wagerTokens, setWagerTokens]               = useState(gameState.wager_tokens || 0);
  const [aquariumSpecies, setAquariumSpecies]       = useState(gameState.aquarium_species || []);
  const [cosmeticFragments, setCosmeticFragments]   = useState(gameState.cosmetic_fragments || 0);
  const [guardCharges, setGuardCharges]             = useState(gameState.guard_charges || 0);
  const [bounties, setBounties]                     = useState(gameState.bounties || []);
  const [communityGoal, setCommunityGoal]           = useState(gameState.community_goal || null);
  const [singularity, setSingularity]               = useState(gameState.singularity || null);
  // T102: stake is now a percentage (0-45), not a 1-10 multiplier. 0 is
  // the safe "no risk" position and is valid — use ?? 0 not || 1.
  const [stakePct, setStakePct]                     = useState(gameState.wager_last_stake ?? 0);
  // T102: max stake percentage for this player (30 base, 35/40/45 with
  // stake extension items). Used to size the slider's max attribute.
  const [maxStakePct, setMaxStakePct]               = useState(gameState.max_stake_pct ?? 30);
  // T102+T105: live display of the stake amount (wins escrowed on next
  // spin). Recomputed on stake/wins/losses change and after each spin.
  const [stakeValue, setStakeValue]                 = useState(0);
  // T107: auto-spin as upgrade. `autoSpinActive` mirrors server state — when
  // true, the stake slider is hidden (auto-spin always uses 0% stake).
  const [autoSpinActive, setAutoSpinActive]         = useState(gameState.auto_spin_active || false);
  const [autoSpinBudget, setAutoSpinBudget]         = useState(gameState.auto_spin_budget || 0);

  // T107: poll /api/tick every 3s while auto-spin is active. The tick
  // endpoint processes the pending server-side auto-spins and returns
  // the results. Mirrors the spin's animation by walking the same
  // applySpinResult path on each result.
  //
  // NOTE: placed AFTER the `autoSpinActive` state declaration (was
  // previously above it, at the original T107 commit location) so the
  // deps array reads a stable binding. With the original placement
  // babel hoisted `var autoSpinActive` to the top of the function and
  // the deps comparison saw `[undefined, undefined]` on the first
  // render, then `[false, fn]` on the second — both stored, but the
  // effect never re-fired when `setAutoSpinActive(true)` flipped the
  // value, so the polling never started. See the T107 follow-up notes.
  useEffect(() => {
    if (!autoSpinActive) return;
    const id = setInterval(tick, 3000);
    return () => clearInterval(id);
  }, [autoSpinActive, tick]);
  const [showPrestigeConfirm, setShowPrestigeConfirm] = useState(false);
  const [showOnboarding, setShowOnboarding]         = useState((gameState.onboarding_step || 0) < 5);
  const [showLegacyBoards, setShowLegacyBoards]     = useState(false);
  const [legacyBoards, setLegacyBoards]             = useState([]);

  const refreshBountiesAndGoal = useCallback(async () => {
    const [bountyRes, goalRes] = await Promise.all([
      apiGame('/api/bounties'),
      apiGame('/api/community-goal'),
    ]);
    if (bountyRes.ok) setBounties(bountyRes.data.bounties || []);
    if (goalRes.ok && goalRes.data.goal) setCommunityGoal(goalRes.data.goal);
  }, []);

  // Clear any previously-set accessibility classes from localStorage
  useEffect(() => {
    localStorage.removeItem('reducedMotion');
    localStorage.removeItem('highContrast');
    document.body.classList.remove('reduced-motion', 'high-contrast');
  }, []);

  // Season 8: sync state from /api/state poll (season change handler already updates most state)
  // This runs on mount and when gameState changes
  useEffect(() => {
    if (gameState.prestige_level != null) setPrestigeLevel(gameState.prestige_level);
    if (gameState.prestige_count != null) setPrestigeCount(gameState.prestige_count);
    if (gameState.legacy_wins != null) setLegacyWins(gameState.legacy_wins);
    // T106: tier-gating metric
    if (gameState.cumulative_wins != null) setCumulativeWins(gameState.cumulative_wins);
    if (gameState.onboarding_step != null) {
      setOnboardingStep(gameState.onboarding_step);
      setShowOnboarding(gameState.onboarding_step < 5);
    }
    // T107: sync auto-spin state from server.
    if (gameState.auto_spin_active != null) setAutoSpinActive(gameState.auto_spin_active);
    if (gameState.auto_spin_budget != null) setAutoSpinBudget(gameState.auto_spin_budget);
    if (gameState.wager_streak != null) setWagerStreak(gameState.wager_streak);
    if (gameState.wager_last_stake != null) setWagerLastStake(gameState.wager_last_stake);
    if (gameState.double_down_pending != null) setDoubleDownPending(gameState.double_down_pending);
    if (gameState.wager_banked_wins != null) setWagerBankedWins(gameState.wager_banked_wins);
    if (gameState.wager_last_win_amount != null) setWagerLastWinAmount(gameState.wager_last_win_amount);
    if (gameState.wager_insurance_charges != null) setWagerInsuranceCharges(gameState.wager_insurance_charges);
    if (gameState.wager_insurance_armed != null) setWagerInsuranceArmed(gameState.wager_insurance_armed);
    if (gameState.active_wheel_mode != null) setActiveWheelMode(gameState.active_wheel_mode);
    if (gameState.available_wheel_modes != null) setAvailableWheelModes(gameState.available_wheel_modes);
    if (gameState.wager_tokens != null) setWagerTokens(gameState.wager_tokens);
    if (gameState.aquarium_species != null) setAquariumSpecies(gameState.aquarium_species);
    if (gameState.cosmetic_fragments != null) setCosmeticFragments(gameState.cosmetic_fragments);
    if (gameState.guard_charges != null) setGuardCharges(gameState.guard_charges);
    if (gameState.bounties != null) setBounties(gameState.bounties);
    if (gameState.community_goal != null) setCommunityGoal(gameState.community_goal);
    if (gameState.singularity != null) setSingularity(gameState.singularity);
    // T80: server-provided wheel probabilities + gravity drift.
    if (gameState.wheel_probabilities != null) setWheelProbabilities(gameState.wheel_probabilities);
    if (gameState.gravity_drift != null) setGravityDrift(gameState.gravity_drift);
    // T102: hydrate stake percentage and the player's max (30/35/40/45).
    // `wager_last_stake` is 0-45 in the new system (0 = safe/no-stake).
    if (gameState.wager_last_stake != null) setStakePct(gameState.wager_last_stake);
    if (gameState.max_stake_pct != null) setMaxStakePct(gameState.max_stake_pct);
  }, []); // eslint-disable-line

  // Season 8: community goal background poll (15s interval, respects document.hidden)
  useEffect(() => {
    let ctrl = new AbortController();

    const load = async () => {
      if (document.hidden) return;
      ctrl.abort();
      ctrl = new AbortController();
      try {
        const { ok, data } = await apiGame('/api/community-goal', { signal: ctrl.signal });
        if (ok && data.goal) setCommunityGoal(data.goal);
      } catch (e) {
        if (e.name !== 'AbortError') console.error('Community goal poll failed', e);
      }
    };

    load();
    const intervalId = setInterval(load, 15000);

    return () => {
      clearInterval(intervalId);
      ctrl.abort();
    };
  }, []);

  // T102+T105: pure helper — given current wins/losses + stake %, return
  // the wins/losses that would be escrowed on the next spin. Mirrors
  // wagers.compute_stake_value on the server; the client computes its
  // own copy because the server doesn't echo stake_value in the spin
  // response (T102: response carries stake + effective_stake only).
  const computeStakeValueForDisplay = useCallback((wins, losses, stakePctArg, ownedItemsArg, mode, ddActive, wagerLastWinAmountArg) => {
    if (ddActive && wagerLastWinAmountArg > 0) return wagerLastWinAmountArg;
    if (stakePctArg === 0) return 0;
    const ownsUnlock = ownedItemsArg.includes('wager_unlock') || mode === 'inverted';
    if (!ownsUnlock) return 0;
    const base = mode === 'inverted' ? losses : wins;
    return Math.floor(Math.max(0, base) * stakePctArg / 100);
  }, []);

  // T102+T105: keep stakeValue live in sync with all inputs (wins, losses,
  // stake slider, wheel mode, DD arm). Runs on every relevant state change,
  // including the post-spin wins_delta update from applySpinResult. Pure
  // derived state; no need to thread it through every callback.
  useEffect(() => {
    setStakeValue(computeStakeValueForDisplay(
      wins, losses, stakePct, ownedItems, activeWheelMode,
      doubleDownPending, wagerLastWinAmount,
    ));
  }, [wins, losses, stakePct, ownedItems, activeWheelMode, doubleDownPending, wagerLastWinAmount, computeStakeValueForDisplay]);

  // Season 8: handle stake change
  const handleStakeChange = useCallback(async (newStakePct) => {
    stakeRef.current = newStakePct;
    setStakePct(newStakePct);
    // T105: stakeValue is derived from inputs via the useEffect above;
    // it will update automatically on the next render. The server's
    // /api/wager/stake echoes the clamped value back so the post-call
    // response handler is what confirms the final slider position.
    await apiGame('/api/wager/stake', { method: 'POST', body: JSON.stringify({ stake: newStakePct }) });
  }, []);

  // Season 8: wheel mode descriptions for tooltips
  const WHEEL_MODE_INFO = {
    steady:      { label: 'Steady',      desc: '70% win · 28% loss · 2% jackpot (×25). Consistent and predictable.' },
    volatile:    { label: 'Volatile',    desc: '45% win · 50% loss · 5% jackpot (×50). High variance — bigger swings both ways.' },
    inverted:    { label: 'Inverted',    desc: '60% win · 35% loss · 5% jackpot. Losses still build your streak bonus.' },
    gravity:     { label: 'Gravity',     desc: '55% win · 40% loss · 5% jackpot. Outcomes drift toward the last result — streaks amplify.' },
    mirror:      { label: 'Mirror',      desc: '65% win · 30% loss · 5% jackpot. Two spins resolved; the better result wins.' },
    singularity: { label: 'Singularity', desc: '75% win · 10% loss · 15% jackpot (×50). Unlocked when the Singularity meter fills.' },
  };

  const WAGER_TOOLTIP = 'Stake: 0% (safe) to 30% (max) of your wins, in 5% steps. ' +
    'Upgrades extend to 45% max. ' +
    '0% = no risk, base payout. ' +
    'Each step risks that percentage of your current wins. ' +
    'Win → your risk is returned plus the full payout. ' +
    'Loss → your risk is gone (wins are actually deducted). ' +
    'Hot Streak: consecutive same-stake wins earn +5% bonus per win (max +50%), bankable at any time. ' +
    'Safety Net: at 15%+ stake, 25% of lost risk is refunded. ' +
    'Double-Down: ⚠️ ALL OR NOTHING. Wager your entire last win for a 2× payout. NO INSURANCE, NO SAFETY NET, NO PROTECTIONS. ' +
    'Insurance: guarantees no loss on next spin (consumes a charge). Does NOT apply to Double-Down.';

  // Season 8: handle wheel mode change
  const handleWheelModeChange = useCallback(async (mode) => {
    const prev = activeWheelMode;
    // T99: capture the four wager-state values BEFORE the optimistic update
    // so we can restore them if the server rejects the change.
    const prevStreak = wagerStreak;
    const prevInsuranceArmed = wagerInsuranceArmed;
    const prevDoubleDownPending = doubleDownPending;
    const prevGravityDrift = gravityDrift;
    setActiveWheelMode(mode);
    // T97: clear wheelProbabilities so the redraw useEffect falls back to
    // the new mode's static probabilities (the previous spin's distribution
    // belongs to the previous mode). The useEffect's deps are now
    // [wheelTheme, activeWheelMode] only — the redraw fires reliably with
    // wheelProbabilities=null and draws the new mode's static fallback.
    setWheelProbabilities(null);
    // T97 (R2): the redraw useEffect is not firing reliably in this React 18
    // build when activeWheelMode changes (the active class on the button
    // updates but the canvas does not). Until that's diagnosed, draw the
    // wheel synchronously here so the change is visible immediately.
    // The draw call is idempotent — if the useEffect does fire later it
    // will redraw the same pixels.
    if (canvasRef.current) {
      drawWheel(canvasRef.current, wheelThemeRef.current || 'default', mode, null);
    }
    const { ok, data } = await apiGame('/api/wheel-mode', { method: 'POST', body: JSON.stringify({ mode }) });
    if (!ok) {
      setActiveWheelMode(prev);
      setWheelProbabilities(null);
      // T99: restore the four wager-state values to the pre-click values.
      setWagerStreak(prevStreak);
      setWagerInsuranceArmed(prevInsuranceArmed);
      setDoubleDownPending(prevDoubleDownPending);
      setGravityDrift(prevGravityDrift);
      if (canvasRef.current) {
        drawWheel(canvasRef.current, wheelThemeRef.current || 'default', prev, null);
      }
      showToast((data && data.error) || 'Mode change failed');
    } else if (data) {
      // T99: T76 resets wager_streak / wager_insurance_armed /
      // double_down_pending / gravity_drift on the server when the mode
      // actually changes. Mirror those into the React state so the wager
      // panel updates immediately (otherwise the "armed" indicators and
      // the hot-streak badge would linger until a full /api/state refresh).
      if (data.wager_streak != null) setWagerStreak(data.wager_streak);
      if (data.wager_insurance_armed != null) setWagerInsuranceArmed(data.wager_insurance_armed);
      if (data.double_down_pending != null) setDoubleDownPending(data.double_down_pending);
      if (data.gravity_drift != null) setGravityDrift(data.gravity_drift);
      if (data.wheel_probabilities) {
        // T80: server may echo the new mode's probabilities (gravity
        // drift resets to 0 per T76).
        setWheelProbabilities(data.wheel_probabilities);
      }
    }
  }, [showToast, activeWheelMode, wagerStreak, wagerInsuranceArmed, doubleDownPending, gravityDrift]);

  // Season 8: handle prestige
  const handlePrestige = useCallback(async () => {
    setShowPrestigeConfirm(false);
    const { ok, data } = await apiGame('/api/prestige', { method: 'POST', body: JSON.stringify({}) });
    if (ok) {
      setPrestigeLevel(data.prestige_level);
      setPrestigeCount(data.prestige_count);
      setLegacyWins(data.legacy_wins);
      setWins(0);
      setLosses(0);
      setStreak(0);
      setSpinCount(0);
      setWagerStreak(0);
      setWagerLastStake(0);
      showToast(` Prestiged to Level ${data.prestige_level}!`);
      refreshBountiesAndGoal();
    } else {
      showToast(data.error || 'Prestige failed');
    }
  }, [showToast]);

  // Season 8: handle guard activation
  const handleGuardActivate = useCallback(async () => {
    const { ok, data } = await apiGame('/api/guard', { method: 'POST', body: JSON.stringify({}) });
    if (ok) {
      setGuardCharges(prev => Math.max(0, prev - 1));
      showToast('🛡️ Guard activated');
    } else {
      showToast(data.error || 'Guard failed');
    }
  }, [showToast]);

  // Season 8: handle bounty claim
  const handleBountyClaim = useCallback(async (bountyId) => {
    const { ok, data } = await apiGame('/api/bounties/claim', { method: 'POST', body: JSON.stringify({ bounty_id: bountyId }) });
    if (ok) {
      if (data.rewards?.cosmetic_fragments) setCosmeticFragments(prev => prev + data.rewards.cosmetic_fragments);
      if (data.rewards?.wins) setWins(prev => prev + data.rewards.wins);
      setBounties(prev => prev.map(b => b.bounty_id === bountyId ? { ...b, claimed: true } : b));
      showToast('Bounty claimed!');
    } else {
      showToast(data.error || 'Claim failed');
    }
  }, [showToast]);

  // Season 8: handle singularity contribution (spec S13: deducts fish_clicks, not wins)
  const handleSingularityContribute = useCallback(async (amount) => {
    const { ok, data } = await apiGame('/api/singularity/contribute', { method: 'POST', body: JSON.stringify({ amount }) });
    if (ok) {
      const actual = data.contributed ?? amount;
      setFishClicks(prev => prev - actual);
      setSingularity(prev => ({ ...prev, total_contributed: data.total_contributed, filled: data.filled }));
      showToast(`Contributed ${fmt(actual)} fish to Singularity`);
    } else {
      showToast(data.error || 'Contribution failed');
    }
  }, [showToast]);

  // Season 8: handle double-down
  const handleDoubleDown = useCallback(async () => {
    const { ok, data } = await apiGame('/api/wager/double-down', { method: 'POST', body: JSON.stringify({}) });
    if (ok) {
      setDoubleDownPending(true);
      showToast('⚡ Double down armed!');
    } else {
      showToast(data.error || 'Double down failed');
    }
  }, [showToast]);

  // Season 8: handle insurance
  const handleInsurance = useCallback(async () => {
    const { ok, data } = await apiGame('/api/wager/insurance', { method: 'POST', body: JSON.stringify({}) });
    if (ok) {
      if (data.wager_insurance_charges != null) {
        setWagerInsuranceCharges(data.wager_insurance_charges);
      } else {
        setWagerInsuranceCharges(prev => Math.max(0, prev - 1));
      }
      setWagerInsuranceArmed(true);
      showToast('🛡️ Insurance activated');
    } else {
      showToast(data.error || 'Insurance failed');
    }
  }, [showToast]);

  // Season 8: handle loadout save
  const handleLoadoutSave = useCallback(async (slot, loadout) => {
    const { ok } = await apiGame('/api/loadout', { method: 'POST', body: JSON.stringify({ slot, loadout }) });
    if (ok) showToast(`Loadout ${slot} saved`);
    else showToast('Save failed');
  }, [showToast]);

  // Season 8: handle loadout apply
  const handleLoadoutApply = useCallback(async (slot) => {
    const { ok, data } = await apiGame('/api/loadout/apply', { method: 'POST', body: JSON.stringify({ slot }) });
    if (ok) {
      setEquippedClass(data.equipped_class);
      setActiveWheelMode(data.active_wheel_mode);
      showToast(`Loadout ${slot} applied`);
    } else {
      showToast(data.error || 'Apply failed');
    }
  }, [showToast]);

  // Season 8: fetch legacy boards
  const handleShowLegacyBoards = useCallback(async () => {
    setShowLegacyBoards(true);
    const { ok, data } = await apiGame('/api/legacy-boards');
    if (ok) setLegacyBoards(data.boards || []);
  }, []);

  // Season 8: keyboard shortcuts (T37)
  useEffect(() => {
    const handler = (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
      // Spacebar triggers manual spin (Season 8: spin is an active decision)
      if (e.key === ' ') {
        e.preventDefault();
        handleManualSpin();
      }
      // Number keys 0-9 select stake percentage (T102: 0%=safe, 5%..45% in 5% steps).
      // Server clamps to the player's max (30/35/40/45) so a press of 8
      // (40%) is harmless if the player doesn't own the extension yet.
      if (e.key >= '0' && e.key <= '9' && ownedItems.includes('wager_unlock')) {
        const newStakePct = parseInt(e.key) * 5;
        handleStakeChange(newStakePct);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [ownedItems, handleStakeChange, handleManualSpin]);

  // Position coach-mark near the target element
  useEffect(() => {
    if (!showOnboarding || onboardingStep >= 4) return;
    const targetSelectors = ['.wheel-wrapper', '.wager-stake-control', '.fishing-panel', '.season8-bounties-panel'];
    const selector = targetSelectors[onboardingStep];
    const target = document.querySelector(selector);
    const coach = document.querySelector('.coach-mark');
    if (!target || !coach) return;

    const targetRect = target.getBoundingClientRect();
    let top = targetRect.top + window.scrollY;
    let left = targetRect.right + 10;

    if (left + 300 > window.innerWidth) {
      left = targetRect.left;
      top = targetRect.bottom + 10;
    }

    coach.style.top = `${top}px`;
    coach.style.left = `${left}px`;
  }, [showOnboarding, onboardingStep]);

  useEffect(() => {
    if (!showOnboarding || onboardingStep >= 4) return;
    const handleMove = () => {
      const targetSelectors = ['.wheel-wrapper', '.wager-stake-control', '.fishing-panel', '.season8-bounties-panel'];
      const selector = targetSelectors[onboardingStep];
      const target = document.querySelector(selector);
      const coach = document.querySelector('.coach-mark');
      if (!target || !coach) return;
      const targetRect = target.getBoundingClientRect();
      let top = targetRect.top + window.scrollY;
      let left = targetRect.right + 10;
      if (left + 300 > window.innerWidth) {
        left = targetRect.left;
        top = targetRect.bottom + 10;
      }
      coach.style.top = `${top}px`;
      coach.style.left = `${left}px`;
    };

    window.addEventListener('scroll', handleMove, { passive: true });
    window.addEventListener('resize', handleMove, { passive: true });
    return () => {
      window.removeEventListener('scroll', handleMove);
      window.removeEventListener('resize', handleMove);
    };
  }, [showOnboarding, onboardingStep]);

  const hasGuard = ownedItems.includes('guard');
  const hasRegen = ownedItems.includes('regen_shield');

  // ── HIATUS MODE — comment out or set HIATUS_MODE=false to re-enable game ──
  if (HIATUS_MODE) {
    return <HiatusScreen season={season} username={username} onLogout={handleLogout} />;
  }
  // ── END HIATUS MODE ────────────────────────────────────────────────────────

  return (
    <div className={lowSpec ? 'low-spec' : ''}>
      <StatsPanel open={showStats} onClose={() => setShowStats(false)} />
      <PatchNotesPanel open={showPatchNotes} onClose={handleClosePatchNotes} />
      {toast && <div className="toast-notification">{toast}</div>}
      {happyHour && !happyHourDismissed && (
        <div className="happy-hour-banner">
          ⭐ Happy Hour! 9–10pm — 2× pot contributions · boosted legendary fish ⭐
          <button className="happy-hour-banner-close" onClick={() => setHappyHourDismissed(true)}>✕</button>
        </div>
      )}
      {catchUpSummary && (
        <div className="catchup-banner">{catchUpSummary}</div>
      )}
      {fishCatchUpSummary && (
        <div className="catchup-banner catchup-banner--fish">{fishCatchUpSummary}</div>
      )}
      {/* ── Season 8 UI ─────────────────────────────────────────────────── */}
      {/* aria-live region for screen readers (T37) */}
      <div className="aria-live-region" aria-live="polite" aria-atomic="true">
        {result === 'win' ? 'Win' : result === 'lose' ? 'Loss' : result === 'jackpot' ? 'Jackpot!' : ''}
      </div>

      {/* Season 8: Non-blocking onboarding coach-mark */}
      {showOnboarding && onboardingStep < 4 && (
        <div className="coach-mark" data-step={onboardingStep}>
          <div className="coach-mark-content">
            <span className="coach-mark-text">{
              onboardingStep === 0 ? '🎡 Spin the wheel to get started!' :
              onboardingStep === 1 ? '🎯 Try setting a wager stake!' :
              onboardingStep === 2 ? '🎣 Catch a fish!' :
              '📋 Check your bounties!'
            }</span>
            <div className="coach-mark-actions">
              <button className="coach-mark-dismiss" onClick={() => setShowOnboarding(false)}>✕</button>
            </div>
          </div>
          <div className="coach-mark-arrow" />
        </div>
      )}

      {/* Prestige confirmation modal (T14) */}
      {showPrestigeConfirm && (
        <div className="onboarding-overlay">
          <div className="onboarding-modal">
            <h3>⚠️ Prestige Reset</h3>
            <p>This will reset your wins, losses, streak, and non-cosmetic upgrades. Your legacy wins will be preserved. Continue?</p>
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
              <button onClick={handlePrestige}>Confirm Prestige</button>
              <button onClick={() => setShowPrestigeConfirm(false)}>Cancel</button>
            </div>
          </div>
        </div>
      )}

      {/* Legacy boards modal (T36) */}
      {showLegacyBoards && (
        <div className="onboarding-overlay" onClick={() => setShowLegacyBoards(false)}>
          <div className="onboarding-modal" onClick={e => e.stopPropagation()} style={{ maxWidth: '500px' }}>
            <h3>🏆 Hall of Fame — Legacy Wins</h3>
            <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
              {legacyBoards.length === 0 ? <p>No legacy wins recorded yet.</p> : (
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead><tr><th style={{ textAlign: 'left' }}>#</th><th style={{ textAlign: 'left' }}>Player</th><th style={{ textAlign: 'right' }}>Legacy Wins</th></tr></thead>
                  <tbody>
                    {legacyBoards.map((b, i) => (
                      <tr key={i} style={{ borderBottom: '1px solid #333' }}>
                        <td>{i + 1}</td>
                        <td>{b.username}</td>
                        <td style={{ textAlign: 'right' }}>{fmt(b.legacy_wins)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
            <button onClick={() => setShowLegacyBoards(false)}>Close</button>
          </div>
        </div>
      )}


      <Confetti active={confetti} count={confettiCount} />
      {wormholeActive && (
        <div style={{ position:'fixed', inset:0, zIndex:0, pointerEvents:'none' }}>
          <WormholeBackground
            static={lowSpec}
            parallax={parallaxEnabled} />
        </div>
      )}
      {casinoActive && (
        <div style={{ position:'fixed', inset:0, zIndex:0, pointerEvents:'none' }}>
          <CasinoBackground lowSpec={lowSpec} />
        </div>
      )}
      <div className={`overlay ${showResult ? 'active' : ''}`} />

      {!isMobile && guardState && (
        <GuardWheel
          blocked={guardState.blocked}
          speedMult={0.4}
          onComplete={() => guardCompleteRef.current && guardCompleteRef.current()}
        />
      )}

      {((!isMobile && showChat) || (isMobile && mobilePanel === 'chat')) && (
        <ChatPanel extraClass={isMobile ? 'mobile-full' : ''} onClose={isMobile ? null : () => { localStorage.setItem('chat_open', 'false'); setShowChat(false); }} />
      )}

      <FireEffect
        streak={streak}
        mode={fireMode}
        lowSpec={lowSpec}
      />

      <div className="user-bar">
        <span className="user-bar-name">👤 {username}</span>
        <button className="stats-btn" title="Stats" onClick={() => setShowStats(true)}>📊</button>
        <button className="stats-btn" title="Fish Encyclopaedia" onClick={() => setShowEncyclopedia(true)}>📖</button>
        <button
          className="stats-btn"
          onClick={() => setLowSpec(v => !v)}
          title={lowSpec ? 'Low Spec Mode ON — click to restore animations' : 'Low Spec Mode OFF — click to reduce GPU usage'}
          style={{ opacity: lowSpec ? 1 : 0.5 }}
        >⚡</button>
        {wormholeActive && !lowSpec && (
          <button
            className="stats-btn"
            onClick={() => setParallaxEnabled(v => { const next = !v; localStorage.setItem('parallaxEnabled', next); return next; })}
            title={parallaxEnabled ? 'Parallax ON — click to disable cursor tracking' : 'Parallax OFF — click to enable cursor tracking'}
            style={{ opacity: parallaxEnabled ? 1 : 0.5 }}
          >🖱️</button>
        )}
        {!isMobile && (
          <button
            className="stats-btn"
            onClick={() => setShowChat(v => { localStorage.setItem('chat_open', !v); return !v; })}
            title={showChat ? 'Hide Chat' : 'Show Chat'}
            style={{ opacity: showChat ? 1 : 0.5 }}
          >💬</button>
        )}
        <button className="stats-btn" title="Patch Notes" onClick={() => setShowPatchNotes(true)}>📋</button>
        <button className="stats-btn" title="Hall of Fame — Legacy Wins" onClick={handleShowLegacyBoards}>🏆</button>
        <button className="logout-btn" onClick={handleLogout}>Logout</button>
        {season && <SeasonInfo seasonName={season.season_name || season.season_number} endsAt={season.ends_at} />}
      </div>

      {showEncyclopedia && (
        <FishEncyclopedia
          caughtSpecies={caughtSpecies}
          onClose={() => setShowEncyclopedia(false)}
        />
      )}

      {!isMobile && (
        <FishingPanel
          fishClicks={fishClicks}
          fishData={getFishData(equippedFish)}
          caughtSpecies={caughtSpecies}
          fishingLuckyNext={fishingLuckyNext}
          ownedItems={ownedItems}
          fishPanelScale={fishPanelScale}
          onFishBucksUpdate={v => setFishClicks(v)}
          onCaughtSpeciesUpdate={id => setCaughtSpecies(prev => prev.includes(id) ? prev : [...prev, id])}
          onFishCaught={refreshBountiesAndGoal}
          onOnboardingAdvance={() => setOnboardingStep(prev => Math.min(prev + 1, 5))}
        />
      )}

      {isMobile && (
        <div className={`mobile-fish-panel${mobilePanel === 'fish' ? ' mobile-visible' : ''}`}>
          <FishingPanel
            fishClicks={fishClicks}
            fishData={getFishData(equippedFish)}
            caughtSpecies={caughtSpecies}
            fishingLuckyNext={fishingLuckyNext}
            ownedItems={ownedItems}
            fishPanelScale={fishPanelScale}
            onFishBucksUpdate={v => setFishClicks(v)}
            onCaughtSpeciesUpdate={id => setCaughtSpecies(prev => prev.includes(id) ? prev : [...prev, id])}
            onFishCaught={refreshBountiesAndGoal}
            onOnboardingAdvance={() => setOnboardingStep(prev => Math.min(prev + 1, 5))}
          />
        </div>
      )}

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
            <div className="bonus-line jackpot-line">🎰 JACKPOT! 25x multiplier applied!</div>
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
        </div>
      )}

      <div className="main-layout-row">
        <div className="casino-container">
          <div className="bulbs">
            {Array.from({length: 16}, (_, i) => <div key={i} className="bulb" />)}
          </div>

          <div className="casino-header">
            <div className="casino-title">
              <span className="title-lucky-wrap">
                <span className="title-lucky">Lucky</span>
                <span className="title-endless">Casino</span>
              </span>
              {' '}Wheel
            </div>
            <div className="subtitle">All or nothing</div>
          </div>

          <div
            className={`wheel-wrapper ${activeCosmetics.includes('golden_wheel') ? 'golden' : ''}`}
            onClick={!spinning ? handleManualSpin : undefined}
            title={spinning ? undefined : 'Click to spin!'}
          >
            <div className="pointer" />
            <canvas
              ref={canvasRef}
              width={420}
              height={420}
              className="wheel-canvas"
              style={{ transform: `rotate(${wheelRotation}deg)`, transition: `transform ${WHEEL_SPIN_SPEED}s cubic-bezier(0.17, 0.67, 0.12, 0.99)` }}
            />
            <div className="center-hub">★</div>
          </div>

          <div className={`spin-prompt ${spinning ? 'hidden' : ''}`} onClick={!spinning ? handleManualSpin : undefined}>
            ▶ Click to Spin ◀
          </div>

          {catchupBonus && (
            <div className="spin-prompt" style={{ opacity: 0.7, fontSize: '0.7rem', pointerEvents: 'none' }}>
              🔼 Catch-up bonus active
            </div>
          )}

          {/* T107: auto-spin as upgrade. Visible only when player owns the
              `auto_spin_unlock` shop item. Checkbox style mirrors the
              pre-S8 auto-spin toggle (`.autospin-row` from Season 5/6/7).
              Server-side budget of 100 spins; cleared on uncheck. While
              active, the stake slider below is hidden (auto-spin always
              uses 0% stake). */}
          {ownedItems.includes('auto_spin_unlock') && (
            <label className="autospin-row" style={{ justifyContent: 'center', marginTop: '0.4rem' }}>
              <input
                type="checkbox"
                checked={autoSpinActive}
                onChange={e => e.target.checked ? handleStartAutoSpin() : handleStopAutoSpin()}
                title="Spin automatically at 0% stake. Stakes are disabled while auto-spin is on."
              />
              <span className="autospin-label">
                {autoSpinActive
                  ? `Auto Spin (${autoSpinBudget} left)`
                  : 'Auto Spin'}
              </span>
            </label>
          )}

          {/* Season 8: Wager panel — always visible (T75); slider disabled until wager_unlock owned */}
          <div className="season8-wager-panel">
            {/* T107: stake slider is hidden while auto-spin is active (auto-spin
                always uses 0% stake; manual input would be confusing). */}
            {!autoSpinActive && <div className="wager-stake-control">
              <label>Stake</label>
              <input
                type="range"
                min="0"
                max={maxStakePct}
                step="5"
                value={stakePct}
                onChange={e => handleStakeChange(parseInt(e.target.value))}
                className="wager-slider"
                disabled={!ownedItems.includes('wager_unlock') && activeWheelMode !== 'inverted'}
                title={(!ownedItems.includes('wager_unlock') && activeWheelMode !== 'inverted') ? 'Buy wager_unlock (500 wins).' : undefined}
                style={(!ownedItems.includes('wager_unlock') && activeWheelMode !== 'inverted') ? { opacity: 0.5, cursor: 'not-allowed' } : undefined}
              />
              <span className={`stake-label ${
                stakePct === 0 ? 'stake-safe' :
                stakePct <= 20 ? 'stake-bold' : 'stake-reckless'
              }`}>{stakePct}%</span>
              <span className="wager-tooltip-trigger" data-tooltip={WAGER_TOOLTIP}>?</span>
            </div>}
            {!autoSpinActive && (<>
            {wagerStreak > 0 && ownedItems.includes('wager_hot_streak') && (
              <div className="wager-hotstreak">🔥 Hot Streak: {wagerStreak} (+{Math.min(wagerStreak * 5, 50)}%)</div>
            )}
            {wagerBankedWins > 0 && !doubleDownPending && ownedItems.includes('wager_hot_streak') && (
              <button className="wager-action-btn wager-bank-btn" onClick={async () => {
                const { ok, data } = await apiGame('/api/wager/bank', { method: 'POST', body: '{}' });
                if (ok) {
                  setWins(data.wins);
                  if (data.losses != null) setLosses(data.losses);
                  setWagerBankedWins(0);
                  setWagerStreak(0);
                  refreshBountiesAndGoal();
                  // T79: surface both banked wins and banked losses in the toast.
                  const w = data.banked_wins || 0, l = data.banked_losses || 0;
                  if (w > 0 && l > 0) showToast(`Banked ${fmt(w)} wins + ${fmt(l)} losses!`);
                  else if (l > 0)      showToast(`Banked ${fmt(l)} losses!`);
                  else                 showToast(`Banked ${fmt(w)} wins!`);
                } else showToast(data.error || 'Bank failed');
              }}>🏦 Bank {fmt(wagerBankedWins)}</button>
            )}
            {ownedItems.includes('wager_double_down') && doubleDownPending && (
              <div className="wager-double-down-armed">⚡ Double-Down armed! ⚠️ No protections.</div>
            )}
            {ownedItems.includes('wager_double_down') && !doubleDownPending && (
              <button className="wager-action-btn" onClick={handleDoubleDown}>⚡ Arm Double-Down (all-or-nothing)</button>
            )}
            {ownedItems.includes('wager_insurance') && wagerInsuranceArmed && (
              <div className="wager-insurance-armed">🛡️ Insurance ARMED — next loss protected</div>
            )}
            {ownedItems.includes('wager_insurance') && !wagerInsuranceArmed && wagerInsuranceCharges > 0 && (
              <button className="wager-action-btn" onClick={handleInsurance}>🛡️ Insurance ({wagerInsuranceCharges})</button>
            )}
            </>)}
            {/* T102+T105: live stake value display at the bottom of the wager panel.
                Always visible so the player can see the dollar cost of the
                current stake position before spinning. */}
            <div className="wager-stake-value">
              {doubleDownPending && wagerLastWinAmount > 0 ? (
                <span className="stake-value-dd">⚡ {fmt(stakeValue)}</span>
              ) : stakePct === 0 ? (
                <span className="stake-value-safe">🛡️ No stake</span>
              ) : activeWheelMode === 'inverted' ? (
                <span className="stake-value-inverted">💀 {fmt(stakeValue)}</span>
              ) : (
                <span className="stake-value-normal">💰 {fmt(stakeValue)}</span>
              )}
            </div>
          </div>

          {/* Season 8: Wheel mode selector */}
          <div className="season8-wheel-mode">
            <span className="wheel-mode-label">Mode</span>
            <div className="wheel-mode-btns">
              {availableWheelModes.map(mode => {
                const info = WHEEL_MODE_INFO[mode];
                return (
                  <button
                    key={mode}
                    className={`wheel-mode-btn${activeWheelMode === mode ? ' active' : ''}`}
                    data-tooltip={info ? info.desc : mode}
                    onClick={() => handleWheelModeChange(mode)}
                  >{info ? info.label : mode}</button>
                );
              })}
            </div>
          </div>

          <Scoreboard wins={wins} losses={losses} lastResult={result} />

          {isMobile && (
            <div className="mobile-below-wheel">
              <StreakPanel streak={streak} bonusmultLevel={0} />
              <DicePanel
                streak={streak}
                onRoll={handleDiceRoll}
                rolling={diceRolling}
                diceResult={diceResult}
                guardSpinning={!!guardState}
                lowSpec={lowSpec}
                diceCharges={diceCharges}
                maxDiceCharges={diceMaxCharges}
                diceLastRecharge={diceLastRecharge}
                hasDiceExtra={ownedItems.includes('dice_extra')}
                rolledSinceSpin={diceRolledSinceSpin}
              />
            </div>
          )}

          <div className="bulbs">
            {Array.from({length: 16}, (_, i) => <div key={i} className="bulb" />)}
          </div>

          {isMobile && guardState && (
            <GuardWheel
              blocked={guardState.blocked}
              speedMult={0.4}
              onComplete={() => guardCompleteRef.current && guardCompleteRef.current()}
              contained
            />
          )}
        </div>
      </div>

      <div className={`game-right${isMobile && mobilePanel === 'shop' ? ' mobile-open' : ''}`}>
        <button
          className="shop-collapse-btn"
          onClick={() => setShopCollapsed(c => !c)}
          title={shopCollapsed ? 'Expand shop' : 'Collapse shop'}
        >{shopCollapsed ? '‹' : '›'}</button>
        <div className={`game-right-body${shopCollapsed ? ' shop-collapsed' : ''}`}>
          {!isMobile && (
            <div className="game-right-sidebar">
              {(hasGuard || hasRegen) && (
                <div className="shield-indicator">
                  {hasGuard && (
                    <>
                      <div className="guard-charges">🛡️ Guard {guardCharges}/3</div>
                      <button
                        className="guard-activate-btn"
                        disabled={guardCharges === 0}
                        onClick={handleGuardActivate}
                      >Block</button>
                    </>
                  )}
                  {hasRegen && (
                    <div>{regenRechargeWins > 0 ? `🔄 ${regenRechargeWins} win${regenRechargeWins !== 1 ? 's' : ''}` : '🔄 ready'}</div>
                  )}
                </div>
              )}
              {ownedItems.includes('lucky_seven') && (
                <LuckySevenCounter spinCount={spinCount} />
              )}
              <StreakPanel streak={streak} bonusmultLevel={0} />
              <DicePanel
                streak={streak}
                onRoll={handleDiceRoll}
                rolling={diceRolling}
                diceResult={diceResult}
                guardSpinning={!!guardState}
                lowSpec={lowSpec}
                diceCharges={diceCharges}
                maxDiceCharges={diceMaxCharges}
                diceLastRecharge={diceLastRecharge}
                hasDiceExtra={ownedItems.includes('dice_extra')}
                rolledSinceSpin={diceRolledSinceSpin}
              />

              {/* Season 8: Prestige panel */}
              {ownedItems.includes('prestige_unlock') && (
                <div className="season8-prestige-panel">
                  <div className="prestige-badge">Prestige Lv.{prestigeLevel} (+{prestigeLevel * 2}%)</div>
                  {legacyWins > 0 && <div className="legacy-badge">Legacy: {fmt(legacyWins)} wins</div>}
                  {prestigeLevel < 20 && (
                    <button
                      className="prestige-btn"
                      disabled={wins < (ownedItems.includes('prestige_efficiency') ? 500000 : 1000000)}
                      onClick={() => setShowPrestigeConfirm(true)}
                    >Prestige</button>
                  )}
                </div>
              )}

              {/* Season 8: Bounties panel */}
              {bounties && bounties.length > 0 && (
                <div className="season8-bounties-panel">
                  <div className="bounties-header">
                    <span>📋 Bounties</span>
                    {cosmeticFragments > 0 && <span className="fragment-count">💎 {cosmeticFragments}</span>}
                  </div>
                  {bounties.map(b => (
                    <div key={b.bounty_id} className="bounty-card">
                      <div className="bounty-desc">{b.description || b.bounty_id}</div>
                      <div className="bounty-progress-bar">
                        <div className="bounty-progress-fill" style={{ width: `${Math.min(100, (b.progress / b.target) * 100)}%` }} />
                      </div>
                      <div className="bounty-progress-text">{fmt(b.progress)} / {fmt(b.target)}</div>
                      {b.completed && !b.claimed && (
                        <button className="bounty-claim-btn" onClick={() => handleBountyClaim(b.bounty_id)}>Claim</button>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Season 8: Aquarium */}
              {ownedItems.includes('aquarium') && (
                <div className="season8-aquarium-panel">
                  <div className="aquarium-header">
                    <span>🐠 Aquarium</span>
                    <span className="aquarium-luck">+{(aquariumSpecies.length * 0.1).toFixed(1)}%</span>
                  </div>
                  <div className="aquarium-grid">
                    {aquariumSpecies.map(s => (
                      <div key={s} className="aquarium-species" title={s}>{s}</div>
                    ))}
                  </div>
                  {ownedItems.includes('fish_to_wager') && wagerTokens > 0 && (
                    <div className="wager-tokens">🪙 {fmt(wagerTokens)} tokens</div>
                  )}
                </div>
              )}

              {/* Season 8: Loadout (shown once something is owned) */}
              {ownedItems.length > 0 && (
                <div className="season8-loadout-panel">
                  <div className="loadout-label">⚙️ Loadouts</div>
                  <div className="loadout-slots">
                    {[1, 2, 3].map(slot => (
                      <div key={slot} className="loadout-slot">
                        <button className="loadout-save-btn" onClick={() => handleLoadoutSave(slot, { equipped_class: equippedClass, active_wheel_mode: activeWheelMode })}>Save {slot}</button>
                        <button className="loadout-apply-btn" onClick={() => handleLoadoutApply(slot)}>Equip {slot}</button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

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
            onEquipClass={handleEquipClass}
            onFishExchange={handleFishExchange}
            onWinsExchange={handleWinsExchange}
            equippedClass={equippedClass}
            fishExchangeTotal={fishExchangeTotal}
            collapsed={shopCollapsed}
            cumulativeWins={cumulativeWins}
            caughtSpecies={caughtSpecies}
            procStreak={procStreak}
          />
        </div>
      </div>

      <div className="bottom-left-stack">
        {/* Season 8: Community goal + Singularity — merged into one slim panel (was two tall panels in the right sidebar, causing overflow scroll, then collided with the fishing panel on short viewports when first relocated here) */}
        {!isMobile && (communityGoal || singularity) && (
          <div className="season8-meta-panel mini-panel">
            {communityGoal && (
              <div className="meta-goal-row">
                <div className="goal-label">🌍 {communityGoal.description}</div>
                <div className="goal-progress-bar">
                  <div className="goal-progress-fill" style={{ width: `${Math.min(100, (communityGoal.current / communityGoal.target) * 100)}%` }} />
                </div>
                <div className="goal-progress-text">{fmt(communityGoal.current)} / {fmt(communityGoal.target)} · You: {fmt(communityGoal.player_contribution)}</div>
              </div>
            )}
            {communityGoal && singularity && <div className="meta-divider" />}
            {singularity && (
              <div className="meta-goal-row">
                <div className="singularity-label-row">
                  <span className="singularity-label">🌀 Singularity</span>
                  {!singularity.filled && (
                    <span className="singularity-buttons">
                      <button
                        onClick={() => handleSingularityContribute(Math.min(fishClicks, Math.floor(singularity.target * 0.1)))}
                        disabled={fishClicks < 1}
                      >+{fmt(Math.min(fishClicks, Math.floor(singularity.target * 0.1)))}</button>
                      <button
                        onClick={() => handleSingularityContribute(fishClicks)}
                        disabled={fishClicks < 1}
                      >All</button>
                    </span>
                  )}
                </div>
                <div className="singularity-progress-bar">
                  <div className="singularity-progress-fill" style={{ width: `${Math.min(100, (singularity.total_contributed / singularity.target) * 100)}%` }} />
                </div>
                <div className="singularity-progress-text">{fmt(singularity.total_contributed)} / {fmt(singularity.target)}{singularity.fill_count > 0 ? ` · Convergences: ${singularity.fill_count}` : ''}</div>
              </div>
            )}
          </div>
        )}
        <div className="fish-counter">
          <span className="fish-counter-label">Balance</span>
          <span className="fish-counter-value">{getFishData(equippedFish).emoji} × {fmt(fishClicks)}</span>
        </div>
        <Leaderboard
          currentUser={username}
          extraClass={isMobile && mobilePanel === 'leaderboard' ? 'mobile-visible' : ''}
          seasonWinners={season && season.latest_winners}
          seasonNumber={season && season.season_number - 1}
        />
      </div>

      {isMobile && mobilePanel && mobilePanel !== 'chat' && (
        <div className="mobile-backdrop" onClick={() => setMobilePanel(null)} />
      )}

      <div className="mobile-toolbar">
        <button
          className={`mobile-toolbar-btn${mobilePanel === 'shop' ? ' active' : ''}`}
          onClick={() => toggleMobilePanel('shop')}
          title="Shop"
        >🏪</button>
        <button
          className={`mobile-toolbar-btn${mobilePanel === 'leaderboard' ? ' active' : ''}`}
          onClick={() => toggleMobilePanel('leaderboard')}
          title="Leaderboard"
        >🏆</button>
        <button
          className={`mobile-toolbar-btn${mobilePanel === 'fish' ? ' active' : ''}`}
          onClick={() => toggleMobilePanel('fish')}
          title="Fishing"
        >🎣</button>
        <button
          className={`mobile-toolbar-btn${mobilePanel === 'chat' ? ' active' : ''}`}
          onClick={() => toggleMobilePanel('chat')}
          title="Chat"
        >💬</button>
        <button
          className="mobile-toolbar-btn"
          onClick={() => setShowStats(true)}
          title="Stats"
        >📊</button>
      </div>

    </div>
  );
}

// ── Root App ───────────────────────────────────────────────────────────────
function App() {
  const [user, setUser]             = useState(undefined);
  const [gameState, setGameState]   = useState(null);
  const [sessionMsg, setSessionMsg] = useState('');


  useEffect(() => {
    (async () => {
      const { ok, data } = await apiFetch('/api/me');
      storeCsrf(data);
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
