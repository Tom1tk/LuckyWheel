const {
  useState,
  useRef,
  useEffect,
  useCallback,
  useMemo
} = React;

// ── API helpers ───────────────────────────────────────────────────────────
async function apiFetch(path, opts = {}) {
  const res = await fetch(path, {
    headers: {
      'Content-Type': 'application/json'
    },
    ...opts
  });
  const json = await res.json().catch(() => ({}));
  return {
    ok: res.ok,
    status: res.status,
    data: json
  };
}

// Called by GameApp to bubble up 401s (session booted by newer login)
let _onSessionExpired = null;
function setSessionExpiredHandler(fn) {
  _onSessionExpired = fn;
}
function apiGame(path, opts = {}) {
  return apiFetch(path, opts).then(r => {
    if (r.status === 401 && _onSessionExpired) _onSessionExpired();
    return r;
  });
}

// ── Draw wheel ────────────────────────────────────────────────────────────
function drawWheel(canvas, theme = 'default') {
  const ctx = canvas.getContext('2d');
  const size = canvas.width;
  const cx = size / 2,
    cy = size / 2,
    r = size / 2 - 4;
  ctx.clearRect(0, 0, size, size);
  const THEMES = {
    default: [{
      label: 'WIN',
      color: '#B8860B',
      bright: '#FFD700',
      start: -Math.PI / 2,
      end: Math.PI / 2
    }, {
      label: 'LOSE',
      color: '#8B0000',
      bright: '#FF3333',
      start: Math.PI / 2,
      end: Math.PI * 1.5
    }],
    fire: [{
      label: 'WIN',
      color: '#993300',
      bright: '#FF6600',
      start: -Math.PI / 2,
      end: Math.PI / 2
    }, {
      label: 'LOSE',
      color: '#440000',
      bright: '#CC2200',
      start: Math.PI / 2,
      end: Math.PI * 1.5
    }],
    ice: [{
      label: 'WIN',
      color: '#005577',
      bright: '#00CCFF',
      start: -Math.PI / 2,
      end: Math.PI / 2
    }, {
      label: 'LOSE',
      color: '#002244',
      bright: '#0066CC',
      start: Math.PI / 2,
      end: Math.PI * 1.5
    }],
    neon: [{
      label: 'WIN',
      color: '#440088',
      bright: '#CC00FF',
      start: -Math.PI / 2,
      end: Math.PI / 2
    }, {
      label: 'LOSE',
      color: '#003300',
      bright: '#00FF66',
      start: Math.PI / 2,
      end: Math.PI * 1.5
    }]
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

// ── Number formatter ─────────────────────────────────────────────────────
function fmt(n) {
  if (n >= 1e12) return (n / 1e12).toFixed(n >= 10e12 ? 1 : 2).replace(/\.?0+$/, '') + 'T';
  if (n >= 1e9) return (n / 1e9).toFixed(n >= 10e9 ? 1 : 2).replace(/\.?0+$/, '') + 'B';
  if (n >= 1e6) return (n / 1e6).toFixed(n >= 10e6 ? 1 : 2).replace(/\.?0+$/, '') + 'M';
  if (n >= 1e3) return (n / 1e3).toFixed(n >= 10e3 ? 1 : 2).replace(/\.?0+$/, '') + 'K';
  return String(n);
}

// ── Scoreboard ───────────────────────────────────────────────────────────
const Scoreboard = React.memo(function Scoreboard({
  wins,
  losses,
  lastResult
}) {
  return /*#__PURE__*/React.createElement("div", {
    className: "scoreboard"
  }, /*#__PURE__*/React.createElement("div", {
    className: "score-box wins-box"
  }, /*#__PURE__*/React.createElement("span", {
    className: "score-label"
  }, "Wins"), /*#__PURE__*/React.createElement("span", {
    className: `score-value ${lastResult === 'win' ? 'score-bump' : ''}`,
    key: wins
  }, fmt(wins))), /*#__PURE__*/React.createElement("div", {
    className: "score-box losses-box"
  }, /*#__PURE__*/React.createElement("span", {
    className: "score-label"
  }, "Losses"), /*#__PURE__*/React.createElement("span", {
    className: `score-value ${lastResult === 'lose' ? 'score-bump' : ''}`,
    key: losses
  }, fmt(losses))));
});

// ── Confetti ──────────────────────────────────────────────────────────────
const CONFETTI_COLORS = ['#FFD700', '#FF6600', '#FF3333', '#00FF88', '#00AAFF', '#FF00FF', '#FFFFFF'];
function Confetti({
  active,
  count = 80
}) {
  // Stabilise random values so React re-renders don't reset CSS animations mid-flight
  const pieces = useMemo(() => {
    if (!active) return [];
    return Array.from({
      length: count
    }, (_, i) => ({
      key: i,
      left: Math.random() * 100,
      delay: Math.random() * 0.8,
      dur: 1.8 + Math.random() * 1.5,
      color: CONFETTI_COLORS[Math.floor(Math.random() * CONFETTI_COLORS.length)],
      size: 8 + Math.floor(Math.random() * 10),
      shape: Math.random() > 0.5 ? '50%' : '2px'
    }));
  }, [active, count]);
  return /*#__PURE__*/React.createElement("div", {
    className: "confetti-container"
  }, pieces.map(p => /*#__PURE__*/React.createElement("div", {
    key: p.key,
    className: "confetti-piece",
    style: {
      left: `${p.left}%`,
      top: 0,
      width: p.size,
      height: p.size,
      background: p.color,
      borderRadius: p.shape,
      animationDuration: `${p.dur}s`,
      animationDelay: `${p.delay}s`
    }
  })));
}

// ── Fish ─────────────────────────────────────────────────────────────────
const Fish = React.memo(function Fish({
  mood,
  net,
  fishClicks,
  onFishClick,
  fishData,
  sizeRem,
  trailClass
}) {
  const [spinKey, setSpinKey] = useState(0);
  const [fishSpinning, setFishSpinning] = useState(false);
  const timerRef = useRef(null);
  const {
    emoji,
    labels
  } = fishData || DEFAULT_FISH;
  const handleClick = () => {
    if (timerRef.current) clearTimeout(timerRef.current);
    setFishSpinning(true);
    setSpinKey(k => k + 1);
    timerRef.current = setTimeout(() => setFishSpinning(false), 650);
    onFishClick();
  };
  const diff = Math.abs(net);
  const glowSize = Math.min(8 + diff * 3, 80);
  const glowSize2 = Math.min(16 + diff * 6, 160);
  const glowOpacity = Math.min(0.5 + diff * 0.015, 1.0);
  const fishFilter = net > 0 ? `drop-shadow(0 0 ${glowSize}px rgba(255,140,0,${glowOpacity})) drop-shadow(0 0 ${glowSize2}px rgba(255,80,0,${glowOpacity * 0.6}))` : net < 0 ? `drop-shadow(0 0 ${glowSize}px rgba(160,0,255,${glowOpacity})) drop-shadow(0 0 ${glowSize2}px rgba(80,0,180,${glowOpacity * 0.6}))` : 'drop-shadow(0 0 8px rgba(255,215,0,0.3))';
  const auraBlur = Math.min(80 + diff * 12, 600);
  const auraOpacity = Math.min(0.3 + diff * 0.008, 0.88);
  const auraColor = net > 0 ? 'rgba(255,130,0,0.9)' : 'rgba(150,0,255,0.9)';
  const auraStyle = diff > 0 ? {
    background: auraColor,
    filter: `blur(${auraBlur}px)`,
    opacity: auraOpacity
  } : null;
  const animClass = fishSpinning ? 'spinning-fish' : mood;
  return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    className: `fish-panel ${trailClass || ''}`,
    onClick: handleClick,
    style: {
      filter: fishFilter
    },
    title: "Wheeee!"
  }, auraStyle && /*#__PURE__*/React.createElement("div", {
    className: "fish-aura",
    style: auraStyle
  }), /*#__PURE__*/React.createElement("span", {
    className: `fish-body ${animClass}`,
    key: spinKey || mood,
    style: {
      fontSize: `${sizeRem}rem`
    }
  }, emoji), /*#__PURE__*/React.createElement("span", {
    className: `fish-label ${mood}`
  }, labels[mood])), /*#__PURE__*/React.createElement("div", {
    className: "fish-counter"
  }, /*#__PURE__*/React.createElement("span", {
    className: "fish-counter-label"
  }, "Fish clicks"), /*#__PURE__*/React.createElement("span", {
    className: "fish-counter-value"
  }, emoji, " \xD7 ", fmt(fishClicks))));
});

// ── Streak Panel ─────────────────────────────────────────────────────────
const StreakPanel = React.memo(function StreakPanel({
  streak
}) {
  if (Math.abs(streak) < 2) return null;
  const isWin = streak > 0;
  const count = Math.abs(streak);
  const bonus = count >= 3 ? Math.pow(2, count - 3) : 0;
  return /*#__PURE__*/React.createElement("div", {
    className: `streak-panel ${isWin ? 'win-streak' : 'lose-streak'}`,
    key: streak
  }, /*#__PURE__*/React.createElement("span", {
    className: "streak-fire"
  }, isWin ? '🔥' : '💀'), /*#__PURE__*/React.createElement("span", {
    className: "streak-count"
  }, count, "x"), /*#__PURE__*/React.createElement("span", {
    className: "streak-label"
  }, isWin ? 'Win Streak' : 'Lose Streak'), bonus > 0 && /*#__PURE__*/React.createElement("span", {
    className: "streak-bonus"
  }, "Bonus +", bonus));
});

// ── Leaderboard ───────────────────────────────────────────────────────────
function Leaderboard({
  currentUser
}) {
  const [rows, setRows] = useState([]);
  useEffect(() => {
    let ctrl = new AbortController();
    const load = () => {
      ctrl.abort();
      ctrl = new AbortController();
      apiFetch('/api/leaderboard', {
        signal: ctrl.signal
      }).then(r => {
        if (r.ok) setRows(r.data);
      }).catch(() => {}); // silently ignore AbortError and network errors
    };
    load();
    const id = setInterval(load, 60000);
    return () => {
      clearInterval(id);
      ctrl.abort();
    };
  }, []);
  if (rows.length === 0) return null;
  const rankClass = i => i === 0 ? 'gold' : i === 1 ? 'silver' : i === 2 ? 'bronze' : '';
  const renderRow = (r, i, key) => /*#__PURE__*/React.createElement("div", {
    key: key,
    className: "leaderboard-row"
  }, /*#__PURE__*/React.createElement("span", {
    className: `lb-rank ${rankClass(i)}`
  }, i + 1, "."), /*#__PURE__*/React.createElement("span", {
    className: `lb-name ${r.username === currentUser ? 'is-you' : ''}`
  }, r.username), /*#__PURE__*/React.createElement("span", {
    className: "lb-wins"
  }, fmt(r.wins), "W"), /*#__PURE__*/React.createElement("span", {
    className: "lb-ratio"
  }, fmt(r.wins), "W:", fmt(r.losses), "L"));
  return /*#__PURE__*/React.createElement("div", {
    className: "leaderboard"
  }, /*#__PURE__*/React.createElement("div", {
    className: "leaderboard-title"
  }, "\uD83C\uDFC6 Top Players"), /*#__PURE__*/React.createElement("div", {
    className: "leaderboard-scroll"
  }, /*#__PURE__*/React.createElement("div", {
    className: "leaderboard-track"
  }, rows.map((r, i) => renderRow(r, i, r.username)), rows.map((r, i) => renderRow(r, i, `${r.username}-2`)))));
}

// ── Shop catalogue ────────────────────────────────────────────────────────
const FISH_SKINS = [{
  id: 'fish_tropical',
  emoji: '🐠',
  name: 'Tropical Fish',
  cost: 25,
  labels: {
    idle: 'Blub blub!',
    happy: 'Splashy win!',
    sad: 'Glub...'
  }
}, {
  id: 'fish_puffer',
  emoji: '🐡',
  name: 'Pufferfish',
  cost: 50,
  labels: {
    idle: '*puffs up*',
    happy: 'PUFF YEAH!',
    sad: '*deflates*'
  }
}, {
  id: 'fish_octopus',
  emoji: '🐙',
  name: 'Octopus',
  cost: 75,
  labels: {
    idle: '8 arms ready!',
    happy: 'Ink-redible!',
    sad: '*squirts ink*'
  }
}, {
  id: 'fish_shark',
  emoji: '🦈',
  name: 'Shark',
  cost: 100,
  labels: {
    idle: 'Chomp chomp',
    happy: 'Feeding frenzy!',
    sad: 'Jaw dropped...'
  }
}, {
  id: 'fish_dolphin',
  emoji: '🐬',
  name: 'Dolphin',
  cost: 150,
  labels: {
    idle: 'Eee-eee!',
    happy: "Flippin' awesome!",
    sad: '*sad clicks*'
  }
}];
const SHOP_SECTIONS = [{
  label: '⚡ Spin Speed',
  items: [{
    id: 'speed_boost',
    emoji: '⚡',
    name: 'Speed Boost',
    cost: 50,
    desc: 'Spin time: 4.5s → 3s'
  }, {
    id: 'turbo_spin',
    emoji: '🚀',
    name: 'Turbo Spin',
    cost: 200,
    desc: 'Spin time: 3s → 1.5s',
    requires: 'speed_boost'
  }]
}, {
  label: '⏩ Auto Speed',
  items: [{
    id: 'autospeed_1',
    emoji: '⏩',
    name: 'Quick Auto',
    cost: 75,
    desc: 'Auto delay: 1.5s → 1s'
  }, {
    id: 'autospeed_2',
    emoji: '⏩',
    name: 'Rapid Auto',
    cost: 300,
    desc: 'Auto delay: 1s → 0.5s',
    requires: 'autospeed_1'
  }, {
    id: 'autospeed_3',
    emoji: '⏩',
    name: 'Instant Auto',
    cost: 1200,
    desc: 'Auto delay: 0.5s → 0',
    requires: 'autospeed_2'
  }]
}, {
  label: '💰 Win Power',
  items: [{
    id: 'winmult_1',
    emoji: '💰',
    name: 'Win x2',
    cost: 200,
    desc: 'Each win scores double'
  }, {
    id: 'winmult_2',
    emoji: '💰',
    name: 'Win x4',
    cost: 800,
    desc: 'Each win scores x4',
    requires: 'winmult_1'
  }, {
    id: 'winmult_3',
    emoji: '💰',
    name: 'Win x8',
    cost: 3200,
    desc: 'Each win scores x8',
    requires: 'winmult_2'
  }, {
    id: 'winmult_4',
    emoji: '💎',
    name: 'Win x16',
    cost: 12800,
    desc: 'Each win scores x16',
    requires: 'winmult_3'
  }]
}, {
  label: '⭐ Bonus Power',
  items: [{
    id: 'bonusmult_1',
    emoji: '⭐',
    name: 'Bonus Boost',
    cost: 300,
    desc: 'Streak bonuses x2'
  }, {
    id: 'bonusmult_2',
    emoji: '⭐',
    name: 'Bonus Mega',
    cost: 1200,
    desc: 'Streak bonuses x5',
    requires: 'bonusmult_1'
  }, {
    id: 'bonusmult_3',
    emoji: '💫',
    name: 'Bonus ULTRA',
    cost: 4800,
    desc: 'Streak bonuses x10',
    requires: 'bonusmult_2'
  }]
}, {
  label: '🐟 Fish Size',
  items: [{
    id: 'fishsize_1',
    emoji: '🔎',
    name: 'Big Fish',
    cost: 50,
    desc: 'Fish size: XL (20rem)'
  }, {
    id: 'fishsize_2',
    emoji: '🔎',
    name: 'Giant Fish',
    cost: 200,
    desc: 'Fish size: XXL (28rem)',
    requires: 'fishsize_1'
  }, {
    id: 'fishsize_3',
    emoji: '🔎',
    name: 'Colossal',
    cost: 800,
    desc: 'Fish size: MEGA (40rem)',
    requires: 'fishsize_2'
  }]
}, {
  label: '✨ Fish Trail',
  items: [{
    id: 'trail_1',
    emoji: '✨',
    name: 'Sparkle Trail',
    cost: 125,
    desc: 'Gold shimmer trail'
  }, {
    id: 'trail_2',
    emoji: '🔥',
    name: 'Fire Trail',
    cost: 500,
    desc: 'Flame glow trail',
    requires: 'trail_1'
  }, {
    id: 'trail_3',
    emoji: '🌈',
    name: 'Rainbow Trail',
    cost: 2000,
    desc: 'Rainbow hue trail',
    requires: 'trail_2'
  }]
}, {
  label: '🖱️ Click Power',
  items: [{
    id: 'double_click',
    emoji: '👆',
    name: 'Double Click',
    cost: 100,
    desc: 'Fish clicks count x2'
  }, {
    id: 'double_click_2',
    emoji: '✌️',
    name: 'Triple Click',
    cost: 400,
    desc: '3 clicks per tap',
    requires: 'double_click'
  }, {
    id: 'double_click_3',
    emoji: '🖖',
    name: 'Quad Click',
    cost: 900,
    desc: '4 clicks per tap',
    requires: 'double_click_2'
  }, {
    id: 'double_click_4',
    emoji: '🤚',
    name: 'Penta Click',
    cost: 2000,
    desc: '5 clicks per tap',
    requires: 'double_click_3'
  }, {
    id: 'double_click_5',
    emoji: '👐',
    name: 'Hexa Click',
    cost: 4500,
    desc: '6 clicks per tap',
    requires: 'double_click_4'
  }, {
    id: 'clickfrenzy_1',
    emoji: '🖱️',
    name: 'Frenzy I',
    cost: 150,
    desc: '+1 click per 5s auto'
  }, {
    id: 'clickfrenzy_2',
    emoji: '🖱️',
    name: 'Frenzy II',
    cost: 600,
    desc: '+5 clicks per 5s',
    requires: 'clickfrenzy_1'
  }, {
    id: 'clickfrenzy_3',
    emoji: '🖱️',
    name: 'Frenzy III',
    cost: 2400,
    desc: '+20 clicks per 5s',
    requires: 'clickfrenzy_2'
  }, {
    id: 'clickfrenzy_4',
    emoji: '🌪️',
    name: 'Frenzy IV',
    cost: 9600,
    desc: '+50 clicks per 5s',
    requires: 'clickfrenzy_3'
  }, {
    id: 'clickfrenzy_5',
    emoji: '⚡',
    name: 'Frenzy V',
    cost: 38400,
    desc: '+100 clicks per 5s',
    requires: 'clickfrenzy_4'
  }]
}, {
  label: '🛡️ Streak Shield',
  items: [{
    id: 'shield_1',
    emoji: '🛡️',
    name: 'Shield',
    cost: 250,
    desc: 'Blocks 1 loss, then breaks'
  }, {
    id: 'iron_shield',
    emoji: '⚔️',
    name: 'Reinforced Shield',
    cost: 600,
    desc: 'Blocks 3 losses, then breaks'
  }, {
    id: 'regen_shield',
    emoji: '🔄',
    name: 'Regenerating Shield',
    cost: 800,
    desc: 'Blocks 1 loss, recharges after 3 wins, never breaks. Stacks with other shields (consumed last)'
  }]
}, {
  label: '🎡 Wheel Theme',
  items: [{
    id: 'theme_fire',
    emoji: '🔥',
    name: 'Fire Theme',
    cost: 250,
    desc: 'Infernal wheel colors'
  }, {
    id: 'theme_ice',
    emoji: '❄️',
    name: 'Ice Theme',
    cost: 1000,
    desc: 'Glacial wheel colors',
    requires: 'theme_fire'
  }, {
    id: 'theme_neon',
    emoji: '🟣',
    name: 'Neon Theme',
    cost: 4000,
    desc: 'Cyberpunk wheel colors',
    requires: 'theme_ice'
  }, {
    id: 'golden_wheel',
    emoji: '✨',
    name: 'Golden Wheel',
    cost: 300,
    desc: 'Radiant glow ring'
  }]
}, {
  label: '🎨 Atmosphere',
  items: [{
    id: 'party_mode',
    emoji: '🎉',
    name: 'Party Mode',
    cost: 150,
    desc: 'Confetti every spin'
  }, {
    id: 'confetti_1',
    emoji: '🎊',
    name: 'Confetti+',
    cost: 75,
    desc: '2x confetti pieces'
  }, {
    id: 'confetti_2',
    emoji: '🎊',
    name: 'Confetti++',
    cost: 300,
    desc: '5x confetti pieces',
    requires: 'confetti_1'
  }, {
    id: 'confetti_3',
    emoji: '🎊',
    name: 'Confetti MAX',
    cost: 1200,
    desc: '15x confetti pieces',
    requires: 'confetti_2'
  }, {
    id: 'bg_ocean',
    emoji: '🌊',
    name: 'Ocean Casino',
    cost: 100,
    desc: 'Deep blue atmosphere'
  }, {
    id: 'bg_royal',
    emoji: '💜',
    name: 'Royal Casino',
    cost: 400,
    desc: 'Purple atmosphere',
    requires: 'bg_ocean'
  }, {
    id: 'bg_inferno',
    emoji: '❤️',
    name: 'Inferno Casino',
    cost: 1600,
    desc: 'Blood red atmosphere',
    requires: 'bg_royal'
  }]
}, {
  label: '🌌 Legendary',
  items: [{
    id: 'singularity',
    emoji: '🌌',
    name: 'The Singularity',
    cost: 1000000000,
    desc: 'Transcend reality itself. Every spin is a win.'
  }]
}];
const DEFAULT_FISH = {
  emoji: '🐟',
  labels: {
    idle: 'Click me!',
    happy: '🎉 Nice!',
    sad: '💀 Ouch!'
  }
};
function getFishData(equippedFish) {
  return FISH_SKINS.find(s => s.id === equippedFish) || DEFAULT_FISH;
}
const COSMETIC_SECTION_IDS = new Set(['bg_ocean', 'bg_royal', 'bg_inferno', 'fishsize_1', 'fishsize_2', 'fishsize_3', 'confetti_1', 'confetti_2', 'confetti_3', 'party_mode', 'trail_1', 'trail_2', 'trail_3', 'theme_fire', 'theme_ice', 'theme_neon', 'golden_wheel']);

// ── Shop components ───────────────────────────────────────────────────────
const ShopItem = React.memo(function ShopItem({
  item,
  owned,
  equipped,
  active,
  canAfford,
  onBuy,
  onEquip,
  onEquipCosmetic,
  isSkin,
  isSingularity,
  isCosmetic
}) {
  let actionEl;
  if (owned && isSkin) {
    actionEl = equipped ? /*#__PURE__*/React.createElement("span", {
      className: "shop-equipped-badge"
    }, "\u2713 On") : /*#__PURE__*/React.createElement("button", {
      className: "shop-equip-btn",
      onClick: () => onEquip(item.id)
    }, "Equip");
  } else if (owned && isCosmetic) {
    actionEl = active ? /*#__PURE__*/React.createElement("button", {
      className: "shop-equip-btn active-cosmetic",
      onClick: () => onEquipCosmetic(item.id)
    }, "Active") : /*#__PURE__*/React.createElement("button", {
      className: "shop-equip-btn",
      onClick: () => onEquipCosmetic(item.id)
    }, "Equip");
  } else if (owned) {
    actionEl = /*#__PURE__*/React.createElement("span", {
      className: "shop-active-badge"
    }, "Active");
  } else {
    actionEl = /*#__PURE__*/React.createElement("button", {
      className: `shop-buy-btn ${canAfford ? 'can-afford' : 'cant-afford'}`,
      onClick: () => canAfford && onBuy(item.id, item.cost)
    }, "Buy");
  }
  const extraClass = isSingularity && !owned ? 'singularity-item' : '';
  return /*#__PURE__*/React.createElement("div", {
    className: `shop-item ${owned ? equipped || active ? 'equipped' : 'owned' : ''} ${extraClass}`
  }, /*#__PURE__*/React.createElement("span", {
    className: "shop-item-emoji"
  }, item.emoji), /*#__PURE__*/React.createElement("div", {
    className: "shop-item-info"
  }, /*#__PURE__*/React.createElement("div", {
    className: "shop-item-name"
  }, item.name), item.desc && /*#__PURE__*/React.createElement("div", {
    className: "shop-item-desc"
  }, item.desc), !owned && /*#__PURE__*/React.createElement("div", {
    className: "shop-item-cost"
  }, "\uD83D\uDC1F ", item.cost.toLocaleString())), /*#__PURE__*/React.createElement("div", {
    className: "shop-item-action"
  }, actionEl));
});
const COSMETIC_SECTION_LABELS = new Set(['🐟 Fish Size', '✨ Fish Trail', '🎡 Wheel Theme', '🎨 Atmosphere']);
function ShopPanel({
  fishClicks,
  ownedItems,
  equippedFish,
  activeCosmetics,
  onBuy,
  onEquip,
  onEquipCosmetic
}) {
  const {
    cosmeticSections,
    functionalSections
  } = useMemo(() => {
    const cosmetic = [],
      functional = [];
    SHOP_SECTIONS.forEach(section => {
      const visibleItems = section.items.filter(item => !item.requires || ownedItems.includes(item.requires));
      if (visibleItems.length === 0) return;
      (COSMETIC_SECTION_LABELS.has(section.label) ? cosmetic : functional).push({
        ...section,
        visibleItems
      });
    });
    return {
      cosmeticSections: cosmetic,
      functionalSections: functional
    };
  }, [ownedItems]);
  const renderSection = section => /*#__PURE__*/React.createElement(React.Fragment, {
    key: section.label
  }, /*#__PURE__*/React.createElement("div", {
    className: "shop-section-label"
  }, "\u2500\u2500 ", section.label, " \u2500\u2500"), section.visibleItems.map(item => {
    const isCosmetic = COSMETIC_SECTION_IDS.has(item.id);
    return /*#__PURE__*/React.createElement(ShopItem, {
      key: item.id,
      item: item,
      isSkin: false,
      isSingularity: item.id === 'singularity',
      isCosmetic: isCosmetic,
      owned: ownedItems.includes(item.id),
      equipped: false,
      active: isCosmetic && activeCosmetics.includes(item.id),
      canAfford: fishClicks >= item.cost,
      onBuy: onBuy,
      onEquip: onEquip,
      onEquipCosmetic: onEquipCosmetic
    });
  }));
  return /*#__PURE__*/React.createElement("div", {
    className: "shop-panel"
  }, /*#__PURE__*/React.createElement("div", {
    className: "shop-header"
  }, /*#__PURE__*/React.createElement("div", {
    className: "shop-title"
  }, "\uD83D\uDED2 Shop"), /*#__PURE__*/React.createElement("div", {
    className: "shop-balance"
  }, "Balance: ", /*#__PURE__*/React.createElement("span", null, "\uD83D\uDC1F ", fmt(fishClicks)))), /*#__PURE__*/React.createElement("div", {
    className: "shop-columns"
  }, /*#__PURE__*/React.createElement("div", {
    className: "shop-col"
  }, /*#__PURE__*/React.createElement("div", {
    className: "shop-col-header"
  }, "\uD83C\uDFA8 Cosmetic"), /*#__PURE__*/React.createElement("div", {
    className: "shop-col-items"
  }, /*#__PURE__*/React.createElement("div", {
    className: "shop-section-label"
  }, "\u2500\u2500 Fish Skins \u2500\u2500"), FISH_SKINS.map(item => /*#__PURE__*/React.createElement(ShopItem, {
    key: item.id,
    item: item,
    isSkin: true,
    owned: ownedItems.includes(item.id),
    equipped: equippedFish === item.id,
    canAfford: fishClicks >= item.cost,
    onBuy: onBuy,
    onEquip: onEquip,
    onEquipCosmetic: onEquipCosmetic
  })), cosmeticSections.map(renderSection))), /*#__PURE__*/React.createElement("div", {
    className: "shop-col"
  }, /*#__PURE__*/React.createElement("div", {
    className: "shop-col-header"
  }, "\u26A1 Functional"), /*#__PURE__*/React.createElement("div", {
    className: "shop-col-items"
  }, functionalSections.map(renderSection)))));
}

// ── Stats Panel ───────────────────────────────────────────────────────────
function StatsPanel({
  open,
  onClose
}) {
  const [stats, setStats] = useState(null);
  useEffect(() => {
    if (!open) return;
    apiFetch('/api/stats').then(r => {
      if (r.ok) setStats(r.data);
    });
  }, [open]);
  if (!open) return null;
  return /*#__PURE__*/React.createElement("div", {
    className: "stats-overlay",
    onClick: onClose
  }, /*#__PURE__*/React.createElement("div", {
    className: "stats-card",
    onClick: e => e.stopPropagation()
  }, /*#__PURE__*/React.createElement("div", {
    className: "stats-title"
  }, "\uD83D\uDCCA Your Stats"), stats ? /*#__PURE__*/React.createElement("div", {
    className: "stats-list"
  }, /*#__PURE__*/React.createElement("div", {
    className: "stats-row"
  }, /*#__PURE__*/React.createElement("span", null, "Total Spins"), /*#__PURE__*/React.createElement("span", null, fmt(stats.spin_count))), /*#__PURE__*/React.createElement("div", {
    className: "stats-row"
  }, /*#__PURE__*/React.createElement("span", null, "Total Wins"), /*#__PURE__*/React.createElement("span", null, fmt(stats.win_count))), /*#__PURE__*/React.createElement("div", {
    className: "stats-row"
  }, /*#__PURE__*/React.createElement("span", null, "Total Losses"), /*#__PURE__*/React.createElement("span", null, fmt(stats.loss_count))), /*#__PURE__*/React.createElement("div", {
    className: "stats-row"
  }, /*#__PURE__*/React.createElement("span", null, "Win Rate"), /*#__PURE__*/React.createElement("span", null, stats.spin_count > 0 ? (stats.win_count / stats.spin_count * 100).toFixed(1) + '%' : 'N/A')), /*#__PURE__*/React.createElement("div", {
    className: "stats-row"
  }, /*#__PURE__*/React.createElement("span", null, "Fish Clicks"), /*#__PURE__*/React.createElement("span", null, fmt(stats.fish_clicks)))) : /*#__PURE__*/React.createElement("div", {
    className: "stats-loading"
  }, "Loading\u2026"), /*#__PURE__*/React.createElement("button", {
    className: "stats-close-btn",
    onClick: onClose
  }, "\u2715")));
}

// ── Auth Page ─────────────────────────────────────────────────────────────
function AuthPage({
  onAuth
}) {
  const [mode, setMode] = useState('login'); // 'login' | 'register'
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const submit = async e => {
    e.preventDefault();
    setError('');
    setLoading(true);
    const {
      ok,
      data
    } = await apiFetch(`/api/${mode}`, {
      method: 'POST',
      body: JSON.stringify({
        username,
        password
      })
    });
    setLoading(false);
    if (ok) {
      onAuth(data.username);
    } else {
      setError(data.error || 'Something went wrong');
    }
  };
  return /*#__PURE__*/React.createElement("div", {
    className: "auth-overlay"
  }, /*#__PURE__*/React.createElement("form", {
    className: "auth-card",
    onSubmit: submit
  }, /*#__PURE__*/React.createElement("div", {
    className: "auth-title"
  }, "Lucky Wheel"), /*#__PURE__*/React.createElement("div", {
    className: "auth-subtitle"
  }, mode === 'login' ? 'Sign in to play' : 'Create account'), error && /*#__PURE__*/React.createElement("div", {
    className: "auth-error"
  }, error), /*#__PURE__*/React.createElement("input", {
    className: "auth-input",
    type: "text",
    placeholder: "Username",
    value: username,
    onChange: e => setUsername(e.target.value),
    autoComplete: "username",
    autoCapitalize: "none",
    autoCorrect: "off",
    spellCheck: false,
    required: true
  }), /*#__PURE__*/React.createElement("input", {
    className: "auth-input",
    type: "password",
    placeholder: "Password",
    value: password,
    onChange: e => setPassword(e.target.value),
    autoComplete: mode === 'login' ? 'current-password' : 'new-password',
    autoCapitalize: "none",
    autoCorrect: "off",
    spellCheck: false,
    required: true
  }), /*#__PURE__*/React.createElement("button", {
    className: "auth-submit-btn",
    type: "submit",
    disabled: loading
  }, loading ? 'Please wait…' : mode === 'login' ? 'Sign In' : 'Create Account'), /*#__PURE__*/React.createElement("div", {
    className: "auth-toggle"
  }, mode === 'login' ? /*#__PURE__*/React.createElement(React.Fragment, null, "No account? ", /*#__PURE__*/React.createElement("a", {
    onClick: () => {
      setMode('register');
      setError('');
    }
  }, "Register")) : /*#__PURE__*/React.createElement(React.Fragment, null, "Have an account? ", /*#__PURE__*/React.createElement("a", {
    onClick: () => {
      setMode('login');
      setError('');
    }
  }, "Sign in")))));
}

// ── Game App ──────────────────────────────────────────────────────────────
function GameApp({
  username,
  gameState,
  onLogout,
  onSessionExpired
}) {
  const canvasRef = useRef(null);
  const [rotation, setRotation] = useState(0);
  const [spinning, setSpinning] = useState(false);
  const [result, setResult] = useState(null);
  const [showResult, setShowResult] = useState(false);
  const setShowResultSync = v => {
    showResultRef.current = v;
    setShowResult(v);
  };
  const [shieldFeedback, setShieldFeedback] = useState(null);
  const [hideResult, setHideResult] = useState(false);
  const [confetti, setConfetti] = useState(false);
  const [wins, setWins] = useState(gameState.wins);
  const [losses, setLosses] = useState(gameState.losses);
  const [streak, setStreak] = useState(gameState.streak);
  const [fishMood, setFishMood] = useState('idle');
  const [fishClicks, setFishClicks] = useState(gameState.fish_clicks);
  const [bonusEarned, setBonusEarned] = useState(0);
  const [shieldCharges, setShieldCharges] = useState(gameState.shield_charges);
  const [regenRechargeWins, setRegenRechargeWins] = useState(gameState.regen_recharge_wins || 0);
  const [autoSpin, setAutoSpin] = useState(false);
  const [ownedItems, setOwnedItems] = useState(gameState.owned_items);
  const [equippedFish, setEquippedFish] = useState(gameState.equipped_fish);
  const [activeCosmetics, setActiveCosmetics] = useState(gameState.active_cosmetics || []);
  const [showStats, setShowStats] = useState(false);
  const [toast, setToast] = useState(null);

  // Memoised derived values
  // Functional items read from ownedItems
  const spinSpeed = useMemo(() => ownedItems.includes('turbo_spin') ? 1.5 : ownedItems.includes('speed_boost') ? 3 : 4.5, [ownedItems]);
  const autoSpinDelay = useMemo(() => ownedItems.includes('autospeed_3') ? 0 : ownedItems.includes('autospeed_2') ? 500 : ownedItems.includes('autospeed_1') ? 1000 : 1500, [ownedItems]);
  const clickAmount = useMemo(() => {
    if (ownedItems.includes('double_click_5')) return 6;
    if (ownedItems.includes('double_click_4')) return 5;
    if (ownedItems.includes('double_click_3')) return 4;
    if (ownedItems.includes('double_click_2')) return 3;
    if (ownedItems.includes('double_click')) return 2;
    return 1;
  }, [ownedItems]);
  const clickFrenzyRate = useMemo(() => {
    if (ownedItems.includes('clickfrenzy_5')) return 100;
    if (ownedItems.includes('clickfrenzy_4')) return 50;
    if (ownedItems.includes('clickfrenzy_3')) return 20;
    if (ownedItems.includes('clickfrenzy_2')) return 5;
    if (ownedItems.includes('clickfrenzy_1')) return 1;
    return 0;
  }, [ownedItems]);
  // Cosmetic items read from activeCosmetics
  const fishSizeRem = useMemo(() => activeCosmetics.includes('fishsize_3') ? 40 : activeCosmetics.includes('fishsize_2') ? 28 : activeCosmetics.includes('fishsize_1') ? 20 : 15, [activeCosmetics]);
  const confettiCount = useMemo(() => Math.min(200, 80 * (activeCosmetics.includes('confetti_3') ? 15 : activeCosmetics.includes('confetti_2') ? 5 : activeCosmetics.includes('confetti_1') ? 2 : 1)), [activeCosmetics]);
  const wheelTheme = useMemo(() => activeCosmetics.includes('theme_neon') ? 'neon' : activeCosmetics.includes('theme_ice') ? 'ice' : activeCosmetics.includes('theme_fire') ? 'fire' : 'default', [activeCosmetics]);
  const bgClass = useMemo(() => activeCosmetics.includes('bg_inferno') ? 'bg-inferno' : activeCosmetics.includes('bg_royal') ? 'bg-royal' : activeCosmetics.includes('bg_ocean') ? 'bg-ocean' : '', [activeCosmetics]);
  const trailClass = useMemo(() => activeCosmetics.includes('trail_3') ? 'trail-rainbow' : activeCosmetics.includes('trail_2') ? 'trail-fire' : activeCosmetics.includes('trail_1') ? 'trail-sparkle' : '', [activeCosmetics]);
  const currentRotationRef = useRef(0);
  const fishTimerRef = useRef(null);
  const toastTimerRef = useRef(null);
  const autoSpinRef = useRef(false);
  const spinSpeedRef = useRef(4.5);
  const autoSpinDelayRef = useRef(1500);
  const spinningRef = useRef(false);
  const showResultRef = useRef(false);
  const clickBufferRef = useRef(0);
  useEffect(() => {
    autoSpinRef.current = autoSpin;
    if (autoSpin && !spinning) spin();
  }, [autoSpin]); // eslint-disable-line
  useEffect(() => {
    spinSpeedRef.current = spinSpeed;
  }, [spinSpeed]);
  useEffect(() => {
    autoSpinDelayRef.current = autoSpinDelay;
  }, [autoSpinDelay]);

  // Register 401 handler
  useEffect(() => {
    setSessionExpiredHandler(onSessionExpired);
    return () => setSessionExpiredHandler(null);
  }, [onSessionExpired]);

  // Click frenzy: passive fish clicks via server
  useEffect(() => {
    if (clickFrenzyRate === 0) return;
    const id = setInterval(async () => {
      const {
        ok,
        data
      } = await apiGame('/api/click-frenzy', {
        method: 'POST',
        body: '{}'
      });
      if (ok) setFishClicks(data.fish_clicks);
    }, 5000);
    return () => clearInterval(id);
  }, [clickFrenzyRate]);

  // Apply background theme to body
  useEffect(() => {
    document.body.className = bgClass;
    return () => {
      document.body.className = '';
    };
  }, [bgClass]);

  // Redraw wheel when theme changes
  useEffect(() => {
    const canvas = canvasRef.current;
    if (canvas) drawWheel(canvas, wheelTheme);
  }, [wheelTheme]);

  // Toast helper
  const showToast = useCallback(msg => {
    setToast(msg);
    if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
    toastTimerRef.current = setTimeout(() => setToast(null), 3000);
  }, []);

  // Fish-click batching: flush buffered clicks to server every 500ms
  const flushClicks = useCallback(async () => {
    const count = clickBufferRef.current;
    if (count === 0) return;
    clickBufferRef.current = 0;
    const {
      ok,
      data
    } = await apiGame('/api/fish-click', {
      method: 'POST',
      body: JSON.stringify({
        count
      })
    });
    if (ok) setFishClicks(data.fish_clicks);
  }, []);
  useEffect(() => {
    const id = setInterval(flushClicks, 500);
    return () => {
      clearInterval(id);
      // Flush any remaining buffered clicks on unmount
      const count = clickBufferRef.current;
      if (count > 0) {
        clickBufferRef.current = 0;
        apiGame('/api/fish-click', {
          method: 'POST',
          body: JSON.stringify({
            count
          })
        });
      }
    };
  }, [flushClicks]);
  const handleBuy = useCallback(async id => {
    const {
      ok,
      data
    } = await apiGame('/api/buy', {
      method: 'POST',
      body: JSON.stringify({
        item_id: id
      })
    });
    if (ok) {
      setFishClicks(data.fish_clicks);
      setOwnedItems(data.owned_items);
      setShieldCharges(data.shield_charges);
      setRegenRechargeWins(data.regen_recharge_wins ?? 0);
      if (data.active_cosmetics) setActiveCosmetics(data.active_cosmetics);
    } else {
      showToast(data.error || 'Purchase failed');
    }
  }, [showToast]);
  const handleEquip = useCallback(async id => {
    const {
      ok,
      data
    } = await apiGame('/api/equip', {
      method: 'POST',
      body: JSON.stringify({
        fish_id: id
      })
    });
    if (ok) {
      setEquippedFish(data.equipped_fish);
    } else {
      showToast(data.error || 'Equip failed');
    }
  }, [showToast]);
  const handleEquipCosmetic = useCallback(async id => {
    const {
      ok,
      data
    } = await apiGame('/api/equip-cosmetic', {
      method: 'POST',
      body: JSON.stringify({
        item_id: id
      })
    });
    if (ok) {
      setActiveCosmetics(data.active_cosmetics);
    } else {
      showToast(data.error || 'Equip failed');
    }
  }, [showToast]);
  const handleFishClick = useCallback(() => {
    // Optimistic update for responsiveness
    setFishClicks(c => c + clickAmount);
    clickBufferRef.current += 1;
    // Eager flush when buffer reaches 10
    if (clickBufferRef.current >= 10) flushClicks();
  }, [clickAmount, flushClicks]);
  const spin = useCallback(async () => {
    if (spinningRef.current) return;
    if (showResultRef.current) {
      setHideResult(true);
      setShowResultSync(false);
      setConfetti(false);
      setTimeout(() => {
        setHideResult(false);
        setResult(null);
      }, 350);
    }
    setBonusEarned(0);
    spinningRef.current = true;
    setSpinning(true);
    let data;
    try {
      const res = await apiGame('/api/spin', {
        method: 'POST',
        body: '{}'
      });
      if (!res.ok) {
        spinningRef.current = false;
        setSpinning(false);
        if (autoSpinRef.current) setTimeout(() => {
          if (autoSpinRef.current) spin();
        }, 1000);
        return;
      }
      data = res.data;
    } catch (e) {
      spinningRef.current = false;
      setSpinning(false);
      if (autoSpinRef.current) setTimeout(() => {
        if (autoSpinRef.current) spin();
      }, 1000);
      return;
    }
    const base = currentRotationRef.current;
    const segmentAngle = data.angle % 360;
    const minTarget = base + 5 * 360;
    const newRotation = Math.ceil((minTarget - segmentAngle) / 360) * 360 + segmentAngle;
    currentRotationRef.current = newRotation;
    setRotation(newRotation);
    setTimeout(() => {
      setResult(data.result);
      setWins(data.wins);
      setLosses(data.losses);
      setStreak(data.streak);
      setShieldCharges(data.shield_charges);
      setRegenRechargeWins(data.regen_recharge_wins ?? 0);
      if (data.owned_items) setOwnedItems(data.owned_items);
      setBonusEarned(data.bonus_earned);
      setShieldFeedback(data.shield_used ? {
        type: data.shield_used_type,
        broke: data.shield_broke,
        chargesLeft: data.shield_charges,
        rechargeWins: data.regen_recharge_wins ?? 0
      } : null);
      setShowResultSync(true);
      if (data.result === 'win') {
        setConfetti(true);
      } else if (activeCosmetics.includes('party_mode')) {
        setConfetti(true);
      }
      const mood = data.result === 'win' ? 'happy' : 'sad';
      setFishMood(mood);
      if (fishTimerRef.current) clearTimeout(fishTimerRef.current);
      fishTimerRef.current = setTimeout(() => setFishMood('idle'), 2500);
      spinningRef.current = false;
      setSpinning(false);
      if (autoSpinRef.current) {
        const delay = data.shield_used ? Math.max(2000, autoSpinDelayRef.current) : Math.max(1500, autoSpinDelayRef.current);
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
    }, spinSpeedRef.current * 1000 + 200);
  }, [activeCosmetics]);
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
    await apiFetch('/api/logout', {
      method: 'POST',
      body: '{}'
    });
    onLogout();
  };
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(StatsPanel, {
    open: showStats,
    onClose: () => setShowStats(false)
  }), toast && /*#__PURE__*/React.createElement("div", {
    className: "toast-notification"
  }, toast), /*#__PURE__*/React.createElement(Confetti, {
    active: confetti,
    count: confettiCount
  }), /*#__PURE__*/React.createElement("div", {
    className: `overlay ${showResult ? 'active' : ''}`
  }), /*#__PURE__*/React.createElement("div", {
    className: "user-bar"
  }, /*#__PURE__*/React.createElement("span", {
    className: "user-bar-name"
  }, "\uD83D\uDC64 ", username), /*#__PURE__*/React.createElement("button", {
    className: "stats-btn",
    onClick: () => setShowStats(true)
  }, "\uD83D\uDCCA"), /*#__PURE__*/React.createElement("button", {
    className: "logout-btn",
    onClick: handleLogout
  }, "Logout")), /*#__PURE__*/React.createElement(Fish, {
    mood: fishMood,
    net: wins - losses,
    fishClicks: fishClicks,
    fishData: getFishData(equippedFish),
    sizeRem: fishSizeRem,
    trailClass: trailClass,
    onFishClick: handleFishClick
  }), showResult && /*#__PURE__*/React.createElement("div", {
    className: `result-banner ${showResult && !hideResult ? 'show' : ''} ${hideResult ? 'hide' : ''}`
  }, /*#__PURE__*/React.createElement("div", {
    className: `result-text ${result}`
  }, result === 'win' ? '🎰 YOU WIN! 🎰' : '💀 YOU LOSE 💀'), bonusEarned > 0 && /*#__PURE__*/React.createElement("div", {
    className: `bonus-line ${result === 'lose' ? 'lose-bonus' : ''}`
  }, "\uD83D\uDD25 Streak Bonus +", fmt(bonusEarned), "!"), shieldFeedback && (() => {
    const names = {
      shield_1: 'Shield',
      iron_shield: 'Reinforced Shield',
      regen_shield: 'Regenerating Shield'
    };
    const emojis = {
      shield_1: '🛡️',
      iron_shield: '⚔️',
      regen_shield: '🔄'
    };
    const name = names[shieldFeedback.type];
    const emoji = emojis[shieldFeedback.type];
    const sub = shieldFeedback.broke ? `${name} broke!` : shieldFeedback.type === 'iron_shield' ? `${shieldFeedback.chargesLeft} charge${shieldFeedback.chargesLeft !== 1 ? 's' : ''} remaining` : shieldFeedback.type === 'regen_shield' ? `Recharging… ${shieldFeedback.rechargeWins} win${shieldFeedback.rechargeWins !== 1 ? 's' : ''}` : null;
    return /*#__PURE__*/React.createElement("div", {
      className: `shield-feedback${shieldFeedback.broke ? ' broke' : ''}`
    }, /*#__PURE__*/React.createElement("div", {
      className: "shield-feedback-icon"
    }, emoji), /*#__PURE__*/React.createElement("div", {
      className: "shield-feedback-label"
    }, name, " Blocked!"), sub && /*#__PURE__*/React.createElement("div", {
      className: "shield-feedback-sub"
    }, sub));
  })(), /*#__PURE__*/React.createElement("button", {
    className: "spin-again-btn",
    onClick: handleSpinAgain
  }, "Spin Again")), /*#__PURE__*/React.createElement("div", {
    className: "casino-container"
  }, /*#__PURE__*/React.createElement("div", {
    className: "bulbs"
  }, Array.from({
    length: 16
  }, (_, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    className: "bulb"
  }))), /*#__PURE__*/React.createElement("div", {
    className: "casino-header"
  }, /*#__PURE__*/React.createElement("div", {
    className: "casino-title"
  }, "Lucky Wheel"), /*#__PURE__*/React.createElement("div", {
    className: "subtitle"
  }, "Try Your Fortune")), /*#__PURE__*/React.createElement("div", {
    className: `wheel-wrapper ${activeCosmetics.includes('golden_wheel') ? 'golden' : ''}`,
    onClick: !spinning && !autoSpin ? spin : undefined,
    title: autoSpin ? 'Auto-spin active' : 'Click to spin!'
  }, /*#__PURE__*/React.createElement("div", {
    className: `pointer ${spinning ? 'spinning' : ''}`
  }), /*#__PURE__*/React.createElement("canvas", {
    ref: canvasRef,
    width: 380,
    height: 380,
    className: `wheel-canvas ${spinning ? 'spinning' : ''}`,
    style: {
      transform: `rotate(${rotation}deg)`,
      transition: `transform ${spinSpeed}s cubic-bezier(0.17, 0.67, 0.12, 0.99)`
    }
  }), /*#__PURE__*/React.createElement("div", {
    className: "center-hub"
  }, "\u2605")), /*#__PURE__*/React.createElement("div", {
    className: `spin-prompt ${spinning || autoSpin ? 'hidden' : ''}`,
    onClick: spin
  }, spinning || autoSpin ? '' : '▶ Click to Spin ◀'), /*#__PURE__*/React.createElement("label", {
    className: "autospin-row"
  }, /*#__PURE__*/React.createElement("input", {
    type: "checkbox",
    checked: autoSpin,
    onChange: e => setAutoSpin(e.target.checked)
  }), /*#__PURE__*/React.createElement("span", {
    className: "autospin-label"
  }, "Auto Spin")), /*#__PURE__*/React.createElement(Scoreboard, {
    wins: wins,
    losses: losses,
    lastResult: result
  }), /*#__PURE__*/React.createElement("div", {
    className: "bulbs"
  }, Array.from({
    length: 16
  }, (_, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    className: "bulb"
  })))), /*#__PURE__*/React.createElement("div", {
    className: "game-right"
  }, /*#__PURE__*/React.createElement("div", {
    className: "game-right-body"
  }, /*#__PURE__*/React.createElement("div", {
    className: "game-right-sidebar"
  }, /*#__PURE__*/React.createElement(StreakPanel, {
    streak: streak
  }), (ownedItems.includes('shield_1') || shieldCharges > 0 || ownedItems.includes('regen_shield')) && /*#__PURE__*/React.createElement("div", {
    className: "shield-indicator"
  }, ownedItems.includes('shield_1') && /*#__PURE__*/React.createElement("div", null, "\uD83D\uDEE1\uFE0F 1 charge"), shieldCharges > 0 && /*#__PURE__*/React.createElement("div", null, "\u2694\uFE0F ", shieldCharges, " charge", shieldCharges !== 1 ? 's' : ''), ownedItems.includes('regen_shield') && /*#__PURE__*/React.createElement("div", null, regenRechargeWins > 0 ? `🔄 ${regenRechargeWins} win${regenRechargeWins !== 1 ? 's' : ''}` : '🔄 ready'))), /*#__PURE__*/React.createElement(ShopPanel, {
    fishClicks: fishClicks,
    ownedItems: ownedItems,
    equippedFish: equippedFish,
    activeCosmetics: activeCosmetics,
    onBuy: handleBuy,
    onEquip: handleEquip,
    onEquipCosmetic: handleEquipCosmetic
  })), /*#__PURE__*/React.createElement(Leaderboard, {
    currentUser: username
  })));
}

// ── Root App ──────────────────────────────────────────────────────────────
function App() {
  const [user, setUser] = useState(undefined); // undefined = loading
  const [gameState, setGameState] = useState(null);
  const [sessionMsg, setSessionMsg] = useState('');

  // Wipe any legacy localStorage data
  useEffect(() => {
    localStorage.clear();
  }, []);
  useEffect(() => {
    (async () => {
      const {
        ok,
        data
      } = await apiFetch('/api/me');
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
  const handleAuth = async username => {
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
    return /*#__PURE__*/React.createElement("div", {
      style: {
        color: '#FFD700',
        fontSize: '1.5rem',
        letterSpacing: '4px',
        textTransform: 'uppercase',
        textAlign: 'center'
      }
    }, "Loading\u2026");
  }
  if (!user) {
    return /*#__PURE__*/React.createElement(React.Fragment, null, sessionMsg && /*#__PURE__*/React.createElement("div", {
      className: "session-banner"
    }, sessionMsg), /*#__PURE__*/React.createElement(AuthPage, {
      onAuth: handleAuth
    }));
  }
  return /*#__PURE__*/React.createElement(GameApp, {
    username: user,
    gameState: gameState,
    onLogout: handleLogout,
    onSessionExpired: handleSessionExpired
  });
}
ReactDOM.createRoot(document.getElementById('root')).render(/*#__PURE__*/React.createElement(App, null));
