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

// ── Wormhole Background Components ───────────────────────────────────────────

function WormholeBackground({
  className = "", intensity = 1, speed = 1, starCount = 950, streakCount = 240,
  nebulaStrength = 0.95, starDriftSpeed = 0.18,
}) {
  const canvasRef = useRef(null);
  const animationRef = useRef(0);

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
    function frame(now) {
      const dt = Math.min(32, now - lastTime); lastTime = now; time += dt;
      ctx.clearRect(0,0,width,height);
      drawBackgroundGradient(); drawNebulaClouds(time); drawSlowMovingStars(time); drawStreaks(time); drawCentreFlare(time); drawVignette();
      animationRef.current = requestAnimationFrame(frame);
    }
    resize();
    const ro = new ResizeObserver(resize); ro.observe(canvas); window.addEventListener("resize", resize);
    animationRef.current = requestAnimationFrame(frame);
    return () => { cancelAnimationFrame(animationRef.current); ro.disconnect(); window.removeEventListener("resize", resize); };
  }, [intensity, speed, starCount, streakCount, nebulaStrength, starDriftSpeed]);

  return (
    <canvas ref={canvasRef} className={className} aria-hidden="true"
      style={{ width:"100%", height:"100%", display:"block", background:"transparent", pointerEvents:"none" }} />
  );
}

function WormholeBackgroundParallax({
  className = "", intensity = 1, speed = 1, starCount = 950, streakCount = 240,
  nebulaStrength = 0.95, starDriftSpeed = 0.18, parallaxStrength = 28, parallaxSmoothing = 0.065,
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
        angle: rand(0, Math.PI*2), z: Math.random() ** 0.55,
        speed: rand(0.0012, 0.0045) * speed * starDriftSpeed * (0.75 + intensity*0.45),
        size: rand(0.45, 1.7), alpha: rand(0.18, 0.95),
        twinkle: rand(0.35, 2.1), phase: rand(0, Math.PI*2),
        colour: colourBand < 0.48 ? [165,215,255] : colourBand < 0.82 ? [255,240,255] : [255,185,235],
        seed: index + Math.random() * 1000,
      };
    }
    function createStars() {
      movingStars.length = 0;
      const total = Math.floor(starCount * intensity);
      for (let i = 0; i < total; i++) movingStars.push(createMovingStar(i));
    }
    function createStreak(index = 0) {
      const baseAngle = Math.atan2(rand(-height*0.55, height*0.55), rand(-width*0.55, width*0.55));
      const hueWeight = Math.random();
      return {
        angle: baseAngle + rand(-0.3, 0.3), z: rand(0.02, 1),
        speed: rand(0.003, 0.018) * speed * (0.8 + intensity*0.65),
        width: rand(0.5, 2.6), length: rand(22, 180),
        alpha: rand(0.12, 0.85), drift: rand(-0.12, 0.12),
        pulse: rand(0.5, 2.3), pulseOffset: rand(0, Math.PI*2),
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
      canvas.width = Math.floor(width*dpr); canvas.height = Math.floor(height*dpr);
      canvas.style.width = `${width}px`; canvas.style.height = `${height}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      cx = width*0.5; cy = height*0.5;
      createStars(); createStreaks();
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
    function drawBackgroundGradient(p) {
      const shiftX = p.currentX * depth.background, shiftY = p.currentY * depth.background;
      const bg = ctx.createLinearGradient(shiftX*0.8, shiftY*0.8, width+shiftX*0.5, height+shiftY*0.5);
      bg.addColorStop(0,"rgba(2,6,18,1)"); bg.addColorStop(0.28,"rgba(5,12,30,1)");
      bg.addColorStop(0.55,"rgba(9,8,24,1)"); bg.addColorStop(0.78,"rgba(20,7,28,1)");
      bg.addColorStop(1,"rgba(6,2,12,1)");
      ctx.fillStyle = bg; ctx.fillRect(0,0,width,height);
    }
    function drawNebulaClouds(t, p) {
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
    function drawSlowMovingStars(t, p) {
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
    function drawStreaks(t, p) {
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
    function buildSparklePath(x, y, sizeOuter, sizeInner) {
      ctx.beginPath();
      ctx.moveTo(x, y-sizeOuter);
      ctx.quadraticCurveTo(x+sizeInner*0.45, y-sizeInner*0.75, x+sizeOuter, y);
      ctx.quadraticCurveTo(x+sizeInner*0.75, y+sizeInner*0.45, x, y+sizeOuter);
      ctx.quadraticCurveTo(x-sizeInner*0.45, y+sizeInner*0.75, x-sizeOuter, y);
      ctx.quadraticCurveTo(x-sizeInner*0.75, y-sizeInner*0.45, x, y-sizeOuter);
      ctx.closePath();
    }
    function drawCentreFlare(t, p) {
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
      ctx.fillStyle=starGlowA; buildSparklePath(focalX,focalY,starOuter*1.22,starInner*1.22); ctx.fill();
      const starFill=ctx.createRadialGradient(focalX,focalY,0,focalX,focalY,starOuter);
      starFill.addColorStop(0,rgba(255,255,255,1)); starFill.addColorStop(0.28,rgba(255,255,255,0.96));
      starFill.addColorStop(0.62,rgba(255,230,245,0.82)); starFill.addColorStop(0.86,rgba(190,225,255,0.52));
      starFill.addColorStop(1,rgba(160,215,255,0.18));
      ctx.fillStyle=starFill; buildSparklePath(focalX,focalY,starOuter,starInner); ctx.fill();
      ctx.strokeStyle=rgba(255,255,255,0.28); ctx.lineWidth=1.1; buildSparklePath(focalX,focalY,starOuter,starInner); ctx.stroke();
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
    function drawVignette(p) {
      const sx=p.currentX*depth.vignette, sy=p.currentY*depth.vignette;
      const vig=ctx.createRadialGradient(cx+sx,cy+sy,Math.min(width,height)*0.2,cx+sx,cy+sy,Math.max(width,height)*0.8);
      vig.addColorStop(0,"rgba(0,0,0,0)"); vig.addColorStop(0.65,"rgba(0,0,0,0.08)"); vig.addColorStop(1,"rgba(0,0,0,0.42)");
      ctx.fillStyle=vig; ctx.fillRect(0,0,width,height);
    }
    function frame(now) {
      const dt=Math.min(32,now-lastTime); lastTime=now; time+=dt;
      const p=updateParallax();
      ctx.clearRect(0,0,width,height);
      drawBackgroundGradient(p); drawCentreFlare(time,p); drawNebulaClouds(time,p); drawSlowMovingStars(time,p); drawStreaks(time,p); drawVignette(p);
      animationRef.current=requestAnimationFrame(frame);
    }
    resize();
    window.addEventListener("pointermove", onPointerMove, { passive: true });
    window.addEventListener("pointerleave", onPointerLeave);
    window.addEventListener("blur", onPointerLeave);
    const ro=new ResizeObserver(resize); ro.observe(canvas); window.addEventListener("resize", resize);
    animationRef.current=requestAnimationFrame(frame);
    return () => {
      cancelAnimationFrame(animationRef.current); ro.disconnect(); window.removeEventListener("resize", resize);
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("pointerleave", onPointerLeave);
      window.removeEventListener("blur", onPointerLeave);
    };
  }, [intensity, speed, starCount, streakCount, nebulaStrength, starDriftSpeed, parallaxStrength, parallaxSmoothing]);

  return (
    <canvas ref={canvasRef} className={className} aria-hidden="true"
      style={{ width:"100%", height:"100%", display:"block", background:"transparent", pointerEvents:"none" }} />
  );
}

function WormholeBackgroundStatic({
  className = "", intensity = 1, starCount = 950, streakCount = 240, nebulaStrength = 0.95, seed = 1337,
}) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d", { alpha: true });
    let dpr = Math.min(window.devicePixelRatio || 1, 2);
    let width = 0, height = 0, cx = 0, cy = 0;
    function mulberry32(a) {
      return function() { let t=(a+=0x6d2b79f5); t=Math.imul(t^(t>>>15),t|1); t^=t+Math.imul(t^(t>>>7),t|61); return((t^(t>>>14))>>>0)/4294967296; };
    }
    let rng = mulberry32(Number(seed)||1337);
    const rand = (min, max) => rng()*(max-min)+min;
    const clamp = (v, min, max) => Math.max(min, Math.min(max, v));
    const lerp = (a, b, t) => a+(b-a)*t;
    const rgba = (r, g, b, a) => `rgba(${r}, ${g}, ${b}, ${a})`;

    function resize() {
      const rect=canvas.getBoundingClientRect();
      width=Math.max(1,Math.floor(rect.width||window.innerWidth)); height=Math.max(1,Math.floor(rect.height||window.innerHeight));
      dpr=Math.min(window.devicePixelRatio||1,2);
      canvas.width=Math.floor(width*dpr); canvas.height=Math.floor(height*dpr);
      canvas.style.width=`${width}px`; canvas.style.height=`${height}px`;
      ctx.setTransform(dpr,0,0,dpr,0,0); cx=width*0.5; cy=height*0.5; draw();
    }
    function drawBackgroundGradient() {
      const bg=ctx.createLinearGradient(0,0,width,height);
      bg.addColorStop(0,"rgba(2,6,18,1)"); bg.addColorStop(0.28,"rgba(5,12,30,1)");
      bg.addColorStop(0.55,"rgba(9,8,24,1)"); bg.addColorStop(0.78,"rgba(20,7,28,1)");
      bg.addColorStop(1,"rgba(6,2,12,1)");
      ctx.fillStyle=bg; ctx.fillRect(0,0,width,height);
    }
    function drawNebulaClouds() {
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
        const driftX=rand(-18,18), driftY=rand(-12,12);
        const g=ctx.createRadialGradient(b.x+driftX,b.y+driftY,0,b.x+driftX,b.y+driftY,Math.max(b.rx,b.ry));
        g.addColorStop(0,b.c1); g.addColorStop(1,b.c2);
        ctx.save(); ctx.translate(b.x+driftX,b.y+driftY); ctx.scale(1,b.ry/b.rx);
        ctx.beginPath(); ctx.arc(0,0,b.rx,0,Math.PI*2); ctx.closePath(); ctx.fillStyle=g; ctx.fill(); ctx.restore();
      });
      ctx.restore();
    }
    function drawStars() {
      ctx.save(); ctx.globalCompositeOperation="screen";
      const total=Math.floor(starCount*intensity);
      for (let i=0;i<total;i++) {
        const sideBias=rng(), x=rand(0,width), y=rand(0,height);
        const base=rng()**1.6, r=rand(0.35,1.8)*(0.7+base);
        const a=rand(0.15,0.95)*rand(0.82,1);
        let tint="rgba(255,255,255,1)";
        if (sideBias<0.46) tint=`rgba(${Math.floor(rand(140,210))},${Math.floor(rand(190,240))},255,1)`;
        else if (sideBias>0.62) tint=`rgba(255,${Math.floor(rand(150,205))},${Math.floor(rand(220,255))},1)`;
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
    function drawStreaks() {
      ctx.save(); ctx.globalCompositeOperation="lighter"; ctx.lineCap="round";
      const total=Math.floor(streakCount*intensity);
      const maxRadius=Math.hypot(width,height)*0.75;
      for (let i=0;i<total;i++) {
        const hueWeight=rng();
        const baseAngle=Math.atan2(rand(-height*0.55,height*0.55),rand(-width*0.55,width*0.55));
        const angle=baseAngle+rand(-0.3,0.3);
        const z=rand(0.04,1), eased=z*z, radius=lerp(6,maxRadius,eased);
        const x=cx+Math.cos(angle)*radius, y=cy+Math.sin(angle)*radius;
        const dirX=x-cx, dirY=y-cy, dirLen=Math.max(1,Math.hypot(dirX,dirY));
        const ux=dirX/dirLen, uy=dirY/dirLen;
        const widthPx=rand(0.5,2.6)*(0.3+eased*1.4);
        const trail=rand(22,180)*(0.18+eased*1.75);
        const x2=x-ux*trail, y2=y-uy*trail;
        const alpha=clamp(rand(0.12,0.85)*(0.3+eased*1.15),0.05,1);
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
    function buildSparklePath(x, y, sizeOuter, sizeInner) {
      ctx.beginPath();
      ctx.moveTo(x,y-sizeOuter);
      ctx.quadraticCurveTo(x+sizeInner*0.45,y-sizeInner*0.75,x+sizeOuter,y);
      ctx.quadraticCurveTo(x+sizeInner*0.75,y+sizeInner*0.45,x,y+sizeOuter);
      ctx.quadraticCurveTo(x-sizeInner*0.45,y+sizeInner*0.75,x-sizeOuter,y);
      ctx.quadraticCurveTo(x-sizeInner*0.75,y-sizeInner*0.45,x,y-sizeOuter);
      ctx.closePath();
    }
    function drawCentreFlare() {
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
      ctx.fillStyle=starGlowA; buildSparklePath(cx,cy,starOuter*1.22,starInner*1.22); ctx.fill();
      const starFill=ctx.createRadialGradient(cx,cy,0,cx,cy,starOuter);
      starFill.addColorStop(0,rgba(255,255,255,1)); starFill.addColorStop(0.28,rgba(255,255,255,0.96));
      starFill.addColorStop(0.62,rgba(255,230,245,0.82)); starFill.addColorStop(0.86,rgba(190,225,255,0.52));
      starFill.addColorStop(1,rgba(160,215,255,0.18));
      ctx.fillStyle=starFill; buildSparklePath(cx,cy,starOuter,starInner); ctx.fill();
      ctx.strokeStyle=rgba(255,255,255,0.28); ctx.lineWidth=1.1; buildSparklePath(cx,cy,starOuter,starInner); ctx.stroke();
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
    function drawVignette() {
      const vig=ctx.createRadialGradient(cx,cy,Math.min(width,height)*0.2,cx,cy,Math.max(width,height)*0.8);
      vig.addColorStop(0,"rgba(0,0,0,0)"); vig.addColorStop(0.65,"rgba(0,0,0,0.08)"); vig.addColorStop(1,"rgba(0,0,0,0.42)");
      ctx.fillStyle=vig; ctx.fillRect(0,0,width,height);
    }
    function draw() {
      rng=mulberry32(Number(seed)||1337);
      ctx.clearRect(0,0,width,height);
      drawBackgroundGradient(); drawNebulaClouds(); drawStars(); drawStreaks(); drawCentreFlare(); drawVignette();
    }
    resize();
    const ro=new ResizeObserver(resize); ro.observe(canvas); window.addEventListener("resize", resize);
    return () => { ro.disconnect(); window.removeEventListener("resize", resize); };
  }, [intensity, starCount, streakCount, nebulaStrength, seed]);

  return (
    <canvas ref={canvasRef} className={className} aria-hidden="true"
      style={{ width:"100%", height:"100%", display:"block", background:"transparent", pointerEvents:"none" }} />
  );
}

// ── Draw main wheel ────────────────────────────────────────────────────────
function drawWheel(canvas, theme = 'default') {
  const ctx = canvas.getContext('2d');
  const size = canvas.width;
  const cx = size / 2, cy = size / 2, r = size / 2 - 4;

  ctx.clearRect(0, 0, size, size);

  const THEMES = {
    default: [
      { label: 'WIN',  color: '#550088', bright: '#AA00FF', start: -Math.PI/2, end: Math.PI/2 },
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
    bioluminescence: [
      { label: 'WIN',  color: '#003a4d', bright: '#00E5FF', start: -Math.PI/2, end: Math.PI/2 },
      { label: 'LOSE', color: '#4d1020', bright: '#FF6B6B', start: Math.PI/2,  end: Math.PI*1.5 },
    ],
    night_ocean: [
      { label: 'WIN',  color: '#1a0d4d', bright: '#5533FF', start: -Math.PI/2, end: Math.PI/2 },
      { label: 'LOSE', color: '#3d0011', bright: '#CC2244', start: Math.PI/2,  end: Math.PI*1.5 },
    ],
    wormhole: [
      { label: 'WIN',  color: '#1a0044', bright: '#BB88FF', start: -Math.PI/2, end: Math.PI/2 },
      { label: 'LOSE', color: '#3d0022', bright: '#FF44AA', start: Math.PI/2,  end: Math.PI*1.5 },
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
  if (!isFinite(n) || isNaN(n)) return '???';
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
function FishingPanel({ fishClicks, fishData, caughtSpecies, fishingLuckyNext, ownedItems, fishPanelScale, onFishBucksUpdate, onCaughtSpeciesUpdate }) {
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

// ── Streak Panel ──────────────────────────────────────────────────────────
// Must match models.py bonus_mult_from_level()
function bonusMultFromLevel(level) {
  const fixed = [1, 2, 5, 10, 20, 50, 100];
  if (level <= 6) return fixed[level] || 1;
  return 100 + (level - 6) * 10;
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
  else if (rolledSinceSpin) disabledReason = 'Spin once before rolling again';

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

  // Poll for new messages
  useEffect(() => {
    let ctrl = new AbortController();
    const load = () => {
      ctrl.abort();
      ctrl = new AbortController();
      apiFetch('/api/chat', { signal: ctrl.signal })
        .then(r => { if (r.ok) setMessages(r.data); })
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
      // Immediately reload
      apiFetch('/api/chat')
        .then(res => { if (res.ok) setMessages(res.data); })
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
        {messages.map(m => (
          <div key={m.id} className="chat-msg">
            {m.created_at && <span className="chat-msg-time">{fmtChatTime(m.created_at)}</span>}
            <span className="chat-msg-name">{m.username}: </span>
            <span className="chat-msg-text">{m.message}</span>
          </div>
        ))}
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
];

const SHOP_SECTIONS = [
  { label: '💰 Win Power', items: [
    { id: 'winmult_inf', emoji: '💰', name: 'Win Power', cost: 0, desc: 'Multiplies each win score', infinite: true },
  ]},
  { label: '⭐ Bonus Power', items: [
    { id: 'bonusmult_inf', emoji: '⭐', name: 'Bonus Power', cost: 0, desc: 'Multiplies streak bonuses — ⚠️ also amplifies loss streaks', infinite: true },
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
    { id: 'guard',         emoji: '🛡️', name: 'Guard',              cost: 500,    desc: '50% chance to block any loss. Breaks on success, survives on failure.' },
    { id: 'auto_guard',    emoji: '🔁', name: 'Auto-Guard',         cost: 50000,  desc: 'Automatically re-buys a Guard for 500 Wins when one breaks. Toggle to enable/disable.', requires: 'guard', tier: 2 },
    { id: 'regen_shield',  emoji: '🔄', name: 'Regenerating Shield', cost: 1500,  desc: 'Blocks any loss when charged. Recharges after 5 wins. Never breaks.', tier: 2 },
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
    { id: 'bg_royal',    emoji: '💜', name: 'Royal Casino',    cost: 400,   desc: 'Purple atmosphere' },
    { id: 'bg_inferno',  emoji: '❤️', name: 'Inferno Casino',  cost: 1600,  desc: 'Blood red atmosphere',    requires: 'bg_royal' },
    { id: 'bg_forest',   emoji: '🌿', name: 'Enchanted Forest',cost: 5000,  desc: 'Mystical green depths',   requires: 'bg_inferno' },
    { id: 'bg_abyss',    emoji: '🌑', name: 'The Abyss',       cost: 15000, desc: 'Void of darkness',        requires: 'bg_forest' },
    { id: 'bg_cosmic',   emoji: '🌌', name: 'Cosmic Casino',   cost: 50000, desc: 'Deep space nebula',       requires: 'bg_abyss' },
  ]},
  { label: '🖼️ Page Theme', items: [
    { id: 'page_season1', emoji: '🌟', name: 'Season 1 Theme', cost: 1000, desc: 'Classic gold & orange casino theme (S1).' },
    { id: 'page_season2', emoji: '🟢', name: 'Season 2 Theme', cost: 1000, desc: 'Green & red casino theme (S2).' },
    { id: 'page_season3', emoji: '🟣', name: 'Season 3 Theme', cost: 1000, desc: 'Purple & orange casino theme (S3).' },
    { id: 'page_season4', emoji: '💜', name: 'Season 4 Theme', cost: 1000, desc: 'Deep violet casino theme (S4).' },
    { id: 'page_season5', emoji: '🌊', name: 'Season 5 Theme', cost: 1000, desc: 'Bioluminescent deep ocean theme (S5).' },
    { id: 'page_season6', emoji: '🌙', name: 'Season 6 Theme', cost: 1000, desc: 'Night ocean — deep indigo & violet (S6).' },
    { id: 'page_season7', emoji: '🌌', name: 'Season 7 Theme', cost: 1000, desc: 'Sci-fi wormhole — animated star field with parallax (S7).' },
  ]},
  { label: '🎲 Dice Charges', items: [
    { id: 'dice_charge_2', emoji: '🎲', name: 'Extra Charge',    cost: 2000,    desc: 'Max dice charges: 1 → 2', tier: 2 },
    { id: 'dice_charge_3', emoji: '🎲', name: 'Max Charge',      cost: 15000,   desc: 'Max dice charges: 2 → 3', requires: 'dice_charge_2', tier: 3 },
    { id: 'dice_charge_4', emoji: '🎲', name: 'Overcharge',      cost: 100000,  desc: 'Max dice charges: 3 → 4', requires: 'dice_charge_3', tier: 3 },
    { id: 'dice_extra',    emoji: '🎲', name: 'Extra Die',        cost: 1000000, desc: 'Roll 3 dice instead of 2. Triple curses and triple blessings possible.', requires: 'dice_charge_3', tier: 3 },
  ]},
  { label: '🎲 Special Upgrades', items: [
    { id: 'fortune_charm', emoji: '🍀', name: 'Fortune Charm',  cost: 1000000,  desc: '25% chance: +25% to streak bonus payout', tier: 3 },
    { id: 'lucky_seven',   emoji: '7️⃣', name: 'Lucky Seven',    cost: 7000000,  desc: 'Every 7th spin is guaranteed a win', tier: 3 },
    { id: 'win_echo',      emoji: '🔊', name: 'Win Echo',        cost: 1000000,  desc: '20% chance to double wins earned on any win', tier: 3 },
    { id: 'resilience',    emoji: '💪', name: 'Resilience',      cost: 10000000, desc: '50% chance: on win streak, a loss only drops streak by 1 instead of resetting', tier: 3 },
    { id: 'jackpot',       emoji: '🎰', name: 'Jackpot',         cost: 3000000,  desc: '1% chance each win to multiply gains by 25x. 5% chance for Jackpot Echo next spin.', tier: 3 },
    { id: 'streak_armor_inf', emoji: '🛡️', name: 'Streak Armor', cost: 0, desc: '+1% to Resilience save chance per level (base 50%, cap 60%)', infinite: true },
  ]},
  { label: '🌌 Legendary', items: [
    { id: 'singularity', emoji: '🌌', name: 'The Singularity', cost: 1e67,
      desc: 'Transcend reality itself. Every spin is a win.' },
  ]},
];

// Infinite upgrade config (mirrors INFINITE_UPGRADES in models.py)
const INF_UPGRADE_CFG = {
  winmult_inf:      { tierCosts: [200, 600, 2000, 6400, 20000, 64000, 200000],   infBase: 400_000,   infScale: 1.18 },
  bonusmult_inf:    { tierCosts: [300, 900, 2800, 8500, 26000, 80000],           infBase: 200_000,   infScale: 1.18 },
  clickmult_inf:    { tierCosts: [75, 250, 600, 1400, 3000],                     infBase: 10_000,    infScale: 1.5 },
  streak_armor_inf: { tierCosts: [500000, 750000, 1000000, 1250000, 1500000, 1750000, 2000000, 2250000, 2500000, 2750000], infBase: 999_999_999, infScale: 1.0, maxLevel: 10 },
};
function infCost(id, level) {
  const { tierCosts, infBase, infScale } = INF_UPGRADE_CFG[id];
  if (level < tierCosts.length) return tierCosts[level];
  return Math.floor(infBase * Math.pow(infScale, level - tierCosts.length));
}
function infMultiplier(id, level) {
  if (id === 'streak_armor_inf') {
    return Math.min(50 + level, 60);  // resilience % chance
  }
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
  if (id === 'clickmult_inf') return 1 + level * 0.25;
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
  'golden_wheel',
  'page_season1', 'page_season2', 'page_season3', 'page_season4', 'page_season5', 'page_season6', 'page_season7',
  'final_frenzy',
  'auto_guard',
]);

// Season 3: currency classification (mirrors ITEM_CURRENCY in models.py)
const COSMETIC_IDS = new Set([
  'fish_tropical','fish_puffer','fish_octopus','fish_shark','fish_dolphin',
  'fish_squid','fish_turtle','fish_crab','fish_lobster','fish_whale',
  'fish_seal','fish_shrimp','fish_coral','fish_mermaid','fish_croc',
  'fishsize_small','fishsize_1','fishsize_2','fishsize_3',
  'trail_1','trail_2','trail_3','trail_4','trail_5','trail_6',
  'theme_fire','theme_ice','theme_neon','theme_void','theme_gold','golden_wheel',
  'page_season1','page_season2','page_season3','page_season4','page_season5','page_season6','page_season7','party_mode','confetti_1','confetti_2','confetti_3',
  'bg_royal','bg_inferno','bg_forest','bg_abyss','bg_cosmic',
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
        const cfg = INF_UPGRADE_CFG[item.id];
        const atMax = cfg && cfg.maxLevel != null && infLevel >= cfg.maxLevel;
        if (atMax) return `Lv${infLevel} · MAX  ${item.desc}`;
        const cur = infMultiplier(item.id, infLevel);
        const nxt = infMultiplier(item.id, infLevel + 1);
        const sep = item.id === 'streak_armor_inf' ? '%' : 'x';
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

// Season 5 tier thresholds
const TIER_THRESHOLDS = { 2: 1000, 3: 10000 };

function ShopPanel({ fishClicks, wins, losses, ownedItems, equippedFish, activeCosmetics, infLevels, onBuy, onEquip, onEquipCosmetic, collapsed, winCount, caughtSpecies }) {
  const [activeTab, setActiveTab] = useState('functional');

  const { cosmeticSections, functionalSections } = useMemo(() => {
    const cosmetic = [], functional = [];
    SHOP_SECTIONS.forEach(section => {
      const isCosmeticSection = COSMETIC_SECTION_LABELS.has(section.label);
      const visibleItems = section.items.filter(item => {
        const requiresMet = !item.requires || ownedItems.includes(item.requires);
        if (isCosmeticSection) return requiresMet;
        if (item.infinite) {
          // streak_armor_inf requires resilience owned
          if (item.id === 'streak_armor_inf') return ownedItems.includes('resilience');
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
        const tierUnlocked = !tierLocked || (winCount >= (tierThreshold || 0));

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
                <div className="shop-item-desc" style={{ opacity: 0.5 }}>🔒 Unlocks at {fmt(tierThreshold)} total wins</div>
              </div>
              <div className="shop-item-action">
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted, #888)' }}>{fmt(winCount)}/{fmt(tierThreshold)}</span>
              </div>
            </div>
          );
        }

        return (
          <ShopItem key={item.id} item={item}
            isSkin={false}
            isSingularity={item.id === 'singularity'}
            isCosmetic={isCosmetic}
            owned={!item.infinite && ownedItems.includes(item.id)}
            equipped={false}
            active={isCosmetic && activeCosmetics.includes(item.id)}
            canAfford={!atMaxLevel && balance >= displayCost}
            infLevel={infLevel}
            displayCost={atMaxLevel ? 0 : displayCost}
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
  const [shieldCharges, setShieldCharges]         = useState(gameState.shield_charges);
  const [regenRechargeWins, setRegenRechargeWins] = useState(gameState.regen_recharge_wins || 0);
  const [catchUpSummary, setCatchUpSummary] = useState(null);
  const [happyHour, setHappyHour]     = useState(gameState.happy_hour || false);
  const [catchupBonus, setCatchupBonus] = useState(false);
  const [ownedItems, setOwnedItems]   = useState(gameState.owned_items);
  const [equippedFish, setEquippedFish] = useState(gameState.equipped_fish);
  const [activeCosmetics, setActiveCosmetics] = useState(gameState.active_cosmetics || []);
  const [infLevels, setInfLevels]     = useState({
    winmult_inf:      gameState.winmult_inf_level   || 0,
    bonusmult_inf:    gameState.bonusmult_inf_level || 0,
    clickmult_inf:    gameState.clickmult_inf_level || 0,
    streak_armor_inf: gameState.streak_armor_level  || 0,
  });
  const [showStats, setShowStats]     = useState(false);
  const [toast, setToast]             = useState(null);
  const [season, setSeason]           = useState(gameState.season || null);
  const [communityPot, setCommunityPot] = useState(gameState.community_pot || { total_contributed: 0, target: 1_000, filled: false, active: false, win_chance_pct: 50.0 });
  const [spinCount, setSpinCount]     = useState(gameState.spin_count || 0);
  const [winCount, setWinCount]       = useState(gameState.win_count || 0);
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

  useEffect(() => {
    const mq = window.matchMedia('(max-width: 768px)');
    const handler = (e) => setIsMobile(e.matches);
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, []);

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

  const fishTimerRef       = useRef(null);
  const toastTimerRef      = useRef(null);
  const confettiTimerRef   = useRef(null);
  const showResultRef      = useRef(false);
  const activeCosmeticsRef = useRef(activeCosmetics);
  const lowSpecRef         = useRef(lowSpec);
  const tickPendingRef     = useRef(false);
  const resultAutoCloseRef = useRef(null);

  useEffect(() => { activeCosmeticsRef.current = activeCosmetics; }, [activeCosmetics]);
  useEffect(() => { lowSpecRef.current = lowSpec; }, [lowSpec]);
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
    const show = bgClass === 'bg-ocean' && !wormholeActive;
    const iframe = document.getElementById('seabed-bg');
    const overlay = document.getElementById('seabed-overlay');
    if (iframe)  iframe.style.display  = show ? 'block' : 'none';
    if (overlay) overlay.style.display = show ? 'block' : 'none';
  }, [bgClass, wormholeActive]);

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
          if (gs.data.caught_species) setCaughtSpecies(gs.data.caught_species);
          setFishingLuckyNext(gs.data.fishing_lucky_next || false);
          if (gs.data.dice_charges != null) setDiceCharges(gs.data.dice_charges);
          if (gs.data.dice_last_recharge) setDiceLastRecharge(gs.data.dice_last_recharge);
          setDiceRolledSinceSpin(gs.data.dice_rolled_since_spin ?? false);
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
      if (data.winmult_inf_level != null || data.bonusmult_inf_level != null || data.clickmult_inf_level != null || data.streak_armor_level != null) {
        setInfLevels(prev => ({
          winmult_inf:      data.winmult_inf_level    ?? prev.winmult_inf,
          bonusmult_inf:    data.bonusmult_inf_level  ?? prev.bonusmult_inf,
          clickmult_inf:    data.clickmult_inf_level  ?? prev.clickmult_inf,
          streak_armor_inf: data.streak_armor_level   ?? prev.streak_armor_inf,
        }));
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
      });
      setStreak(data.streak);
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
    if (data.new_spin_count != null) setSpinCount(data.new_spin_count);
    if (data.active_cosmetics) setActiveCosmetics(data.active_cosmetics);
    if (data.auto_guard_failed) showToast('Not enough wins — Auto-Guard disabled');
    if (data.dice_charges != null) setDiceCharges(data.dice_charges);
    if (data.dice_last_recharge) setDiceLastRecharge(data.dice_last_recharge);
    setDiceRolledSinceSpin(false);
    if (data.wins_delta > 0) setWinCount(prev => prev + 1);
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

  const tick = useCallback(async () => {
    if (tickPendingRef.current) return;
    tickPendingRef.current = true;
    try {
      const res = await apiGame('/api/tick', { method: 'POST', body: JSON.stringify({}) });
      if (!res.ok) return;
      const data = res.data;

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
          if (data.state.shield_charges      != null) setShieldCharges(data.state.shield_charges);
          if (data.state.regen_recharge_wins != null) setRegenRechargeWins(data.state.regen_recharge_wins);
          if (data.state.active_cosmetics)            setActiveCosmetics(data.state.active_cosmetics);
          if (data.state.spin_count != null) setSpinCount(data.state.spin_count);
          if (data.state.win_count  != null) setWinCount(data.state.win_count);
          if (data.state.dice_charges != null) setDiceCharges(data.state.dice_charges);
          if (data.state.catchup_bonus_active != null) setCatchupBonus(data.state.catchup_bonus_active);
          setDiceRolledSinceSpin(false);
        }
        const hrs = Math.floor(data.elapsed_seconds / 3600);
        const mins = Math.floor((data.elapsed_seconds % 3600) / 60);
        const timeStr = hrs > 0 ? `${hrs}h ${mins}m` : `${mins}m`;
        setCatchUpSummary(`⏰ Away ${timeStr} — ${data.spins_processed} spins processed`);
        setTimeout(() => setCatchUpSummary(null), 5000);
        return;
      }

      if (!data.spins || data.spins.length === 0) return;

      const spinResult = data.spins[data.spins.length - 1];

      // Dismiss any lingering result before showing the new one
      if (showResultRef.current) dismissResult();

      setBonusEarned(0); setEchoTriggered(false); setJackpotHit(false);
      setResilienceTriggered(false); setLuckySevenTriggered(false); setFortuneCharmTriggered(false);

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

      if (data.state) {
        if (data.state.dice_charges != null) setDiceCharges(data.state.dice_charges);
        if (data.state.catchup_bonus_active != null) setCatchupBonus(data.state.catchup_bonus_active);
      }
    } finally {
      tickPendingRef.current = false;
    }
  }, [applySpinResult, dismissResult, scheduleResultDismiss]);

  // Tick every 3 seconds
  useEffect(() => {
    let busy = false;
    const doTick = async () => {
      if (busy) return;
      busy = true;
      try { await tick(); } finally { busy = false; }
    };
    doTick();
    const id = setInterval(doTick, 3000);
    return () => clearInterval(id);
  }, []); // eslint-disable-line

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
      {toast && <div className="toast-notification">{toast}</div>}
      {happyHour && (
        <div className="happy-hour-banner">
          ⭐ Happy Hour! 9–10pm — 2× pot contributions · boosted legendary fish ⭐
        </div>
      )}
      {catchUpSummary && (
        <div className="catchup-banner">{catchUpSummary}</div>
      )}
      <Confetti active={confetti} count={confettiCount} />
      {wormholeActive && (
        <div style={{ position:'fixed', inset:0, zIndex:0, pointerEvents:'none' }}>
          {lowSpec
            ? <WormholeBackgroundStatic />
            : parallaxEnabled
              ? <WormholeBackgroundParallax />
              : <WormholeBackground />
          }
        </div>
      )}
      <div className={`overlay ${showResult ? 'active' : ''}`} />

      {!isMobile && guardState && (
        <GuardWheel
          blocked={guardState.blocked}
          speedMult={1.0}
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
        <a
          className="stats-btn"
          href="https://github.com/Tom1tk/fishspin/wiki/Patch-Notes"
          target="_blank"
          rel="noopener noreferrer"
          title="Patch Notes"
          style={{ textDecoration: 'none' }}
        >📋</a>
        <button className="logout-btn" onClick={handleLogout}>Logout</button>
        <CommunityPot
          pot={communityPot}
          fishClicks={fishClicks}
          onContribute={newClicks => setFishClicks(newClicks)}
        />
        {season && <SeasonInfo seasonNumber={season.season_number} endsAt={season.ends_at} />}
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
          />
          <CommunityPot
            pot={communityPot}
            fishClicks={fishClicks}
            onContribute={newClicks => setFishClicks(newClicks)}
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
            <div className="casino-title">Lucky Wheel</div>
            <div className="subtitle">Try Your Fortune</div>
          </div>

          <div className={`wheel-wrapper ${activeCosmetics.includes('golden_wheel') ? 'golden' : ''}`}>
            <div className="pointer" />
            <canvas
              ref={canvasRef}
              width={380}
              height={380}
              className="wheel-canvas auto-spinning"
            />
            <div className="center-hub">★</div>
          </div>

          {catchupBonus && (
            <div className="spin-prompt" style={{ opacity: 0.7, fontSize: '0.7rem', pointerEvents: 'none' }}>
              🔼 Catch-up bonus active
            </div>
          )}

          <Scoreboard wins={wins} losses={losses} lastResult={result} />

          {isMobile && (
            <div className="mobile-below-wheel">
              <StreakPanel streak={streak} bonusmultLevel={infLevels.bonusmult_inf} />
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
              speedMult={1.0}
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
                  {hasGuard && <div>🛡️ Guard ready</div>}
                  {hasRegen && (
                    <div>{regenRechargeWins > 0 ? `🔄 ${regenRechargeWins} win${regenRechargeWins !== 1 ? 's' : ''}` : '🔄 ready'}</div>
                  )}
                </div>
              )}
              {ownedItems.includes('lucky_seven') && (
                <LuckySevenCounter spinCount={spinCount} />
              )}
              <StreakPanel streak={streak} bonusmultLevel={infLevels.bonusmult_inf} />
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
            winCount={winCount}
            caughtSpecies={caughtSpecies}
          />
        </div>
      </div>

      <div className="bottom-left-stack">
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
