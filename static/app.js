"use strict";

function _typeof(o) { "@babel/helpers - typeof"; return _typeof = "function" == typeof Symbol && "symbol" == typeof Symbol.iterator ? function (o) { return typeof o; } : function (o) { return o && "function" == typeof Symbol && o.constructor === Symbol && o !== Symbol.prototype ? "symbol" : typeof o; }, _typeof(o); }
function _toConsumableArray(r) { return _arrayWithoutHoles(r) || _iterableToArray(r) || _unsupportedIterableToArray(r) || _nonIterableSpread(); }
function _nonIterableSpread() { throw new TypeError("Invalid attempt to spread non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method."); }
function _iterableToArray(r) { if ("undefined" != typeof Symbol && null != r[Symbol.iterator] || null != r["@@iterator"]) return Array.from(r); }
function _arrayWithoutHoles(r) { if (Array.isArray(r)) return _arrayLikeToArray(r); }
function _regeneratorRuntime() { "use strict"; var r = _regenerator(), e = r.m(_regeneratorRuntime), t = (Object.getPrototypeOf ? Object.getPrototypeOf(e) : e.__proto__).constructor; function n(r) { var e = "function" == typeof r && r.constructor; return !!e && (e === t || "GeneratorFunction" === (e.displayName || e.name)); } var o = { "throw": 1, "return": 2, "break": 3, "continue": 3 }; function a(r) { var e, t; return function (n) { e || (e = { stop: function stop() { return t(n.a, 2); }, "catch": function _catch() { return n.v; }, abrupt: function abrupt(r, e) { return t(n.a, o[r], e); }, delegateYield: function delegateYield(r, o, a) { return e.resultName = o, t(n.d, _regeneratorValues(r), a); }, finish: function finish(r) { return t(n.f, r); } }, t = function t(r, _t, o) { n.p = e.prev, n.n = e.next; try { return r(_t, o); } finally { e.next = n.n; } }), e.resultName && (e[e.resultName] = n.v, e.resultName = void 0), e.sent = n.v, e.next = n.n; try { return r.call(this, e); } finally { n.p = e.prev, n.n = e.next; } }; } return (_regeneratorRuntime = function _regeneratorRuntime() { return { wrap: function wrap(e, t, n, o) { return r.w(a(e), t, n, o && o.reverse()); }, isGeneratorFunction: n, mark: r.m, awrap: function awrap(r, e) { return new _OverloadYield(r, e); }, AsyncIterator: _regeneratorAsyncIterator, async: function async(r, e, t, o, u) { return (n(e) ? _regeneratorAsyncGen : _regeneratorAsync)(a(r), e, t, o, u); }, keys: _regeneratorKeys, values: _regeneratorValues }; })(); }
function _regeneratorValues(e) { if (null != e) { var t = e["function" == typeof Symbol && Symbol.iterator || "@@iterator"], r = 0; if (t) return t.call(e); if ("function" == typeof e.next) return e; if (!isNaN(e.length)) return { next: function next() { return e && r >= e.length && (e = void 0), { value: e && e[r++], done: !e }; } }; } throw new TypeError(_typeof(e) + " is not iterable"); }
function _regeneratorKeys(e) { var n = Object(e), r = []; for (var t in n) r.unshift(t); return function e() { for (; r.length;) if ((t = r.pop()) in n) return e.value = t, e.done = !1, e; return e.done = !0, e; }; }
function _regeneratorAsync(n, e, r, t, o) { var a = _regeneratorAsyncGen(n, e, r, t, o); return a.next().then(function (n) { return n.done ? n.value : a.next(); }); }
function _regeneratorAsyncGen(r, e, t, o, n) { return new _regeneratorAsyncIterator(_regenerator().w(r, e, t, o), n || Promise); }
function _regeneratorAsyncIterator(t, e) { function n(r, o, i, f) { try { var c = t[r](o), u = c.value; return u instanceof _OverloadYield ? e.resolve(u.v).then(function (t) { n("next", t, i, f); }, function (t) { n("throw", t, i, f); }) : e.resolve(u).then(function (t) { c.value = t, i(c); }, function (t) { return n("throw", t, i, f); }); } catch (t) { f(t); } } var r; this.next || (_regeneratorDefine2(_regeneratorAsyncIterator.prototype), _regeneratorDefine2(_regeneratorAsyncIterator.prototype, "function" == typeof Symbol && Symbol.asyncIterator || "@asyncIterator", function () { return this; })), _regeneratorDefine2(this, "_invoke", function (t, o, i) { function f() { return new e(function (e, r) { n(t, i, e, r); }); } return r = r ? r.then(f, f) : f(); }, !0); }
function _regenerator() { /*! regenerator-runtime -- Copyright (c) 2014-present, Facebook, Inc. -- license (MIT): https://github.com/babel/babel/blob/main/packages/babel-helpers/LICENSE */ var e, t, r = "function" == typeof Symbol ? Symbol : {}, n = r.iterator || "@@iterator", o = r.toStringTag || "@@toStringTag"; function i(r, n, o, i) { var c = n && n.prototype instanceof Generator ? n : Generator, u = Object.create(c.prototype); return _regeneratorDefine2(u, "_invoke", function (r, n, o) { var i, c, u, f = 0, p = o || [], y = !1, G = { p: 0, n: 0, v: e, a: d, f: d.bind(e, 4), d: function d(t, r) { return i = t, c = 0, u = e, G.n = r, a; } }; function d(r, n) { for (c = r, u = n, t = 0; !y && f && !o && t < p.length; t++) { var o, i = p[t], d = G.p, l = i[2]; r > 3 ? (o = l === n) && (u = i[(c = i[4]) ? 5 : (c = 3, 3)], i[4] = i[5] = e) : i[0] <= d && ((o = r < 2 && d < i[1]) ? (c = 0, G.v = n, G.n = i[1]) : d < l && (o = r < 3 || i[0] > n || n > l) && (i[4] = r, i[5] = n, G.n = l, c = 0)); } if (o || r > 1) return a; throw y = !0, n; } return function (o, p, l) { if (f > 1) throw TypeError("Generator is already running"); for (y && 1 === p && d(p, l), c = p, u = l; (t = c < 2 ? e : u) || !y;) { i || (c ? c < 3 ? (c > 1 && (G.n = -1), d(c, u)) : G.n = u : G.v = u); try { if (f = 2, i) { if (c || (o = "next"), t = i[o]) { if (!(t = t.call(i, u))) throw TypeError("iterator result is not an object"); if (!t.done) return t; u = t.value, c < 2 && (c = 0); } else 1 === c && (t = i["return"]) && t.call(i), c < 2 && (u = TypeError("The iterator does not provide a '" + o + "' method"), c = 1); i = e; } else if ((t = (y = G.n < 0) ? u : r.call(n, G)) !== a) break; } catch (t) { i = e, c = 1, u = t; } finally { f = 1; } } return { value: t, done: y }; }; }(r, o, i), !0), u; } var a = {}; function Generator() {} function GeneratorFunction() {} function GeneratorFunctionPrototype() {} t = Object.getPrototypeOf; var c = [][n] ? t(t([][n]())) : (_regeneratorDefine2(t = {}, n, function () { return this; }), t), u = GeneratorFunctionPrototype.prototype = Generator.prototype = Object.create(c); function f(e) { return Object.setPrototypeOf ? Object.setPrototypeOf(e, GeneratorFunctionPrototype) : (e.__proto__ = GeneratorFunctionPrototype, _regeneratorDefine2(e, o, "GeneratorFunction")), e.prototype = Object.create(u), e; } return GeneratorFunction.prototype = GeneratorFunctionPrototype, _regeneratorDefine2(u, "constructor", GeneratorFunctionPrototype), _regeneratorDefine2(GeneratorFunctionPrototype, "constructor", GeneratorFunction), GeneratorFunction.displayName = "GeneratorFunction", _regeneratorDefine2(GeneratorFunctionPrototype, o, "GeneratorFunction"), _regeneratorDefine2(u), _regeneratorDefine2(u, o, "Generator"), _regeneratorDefine2(u, n, function () { return this; }), _regeneratorDefine2(u, "toString", function () { return "[object Generator]"; }), (_regenerator = function _regenerator() { return { w: i, m: f }; })(); }
function _regeneratorDefine2(e, r, n, t) { var i = Object.defineProperty; try { i({}, "", {}); } catch (e) { i = 0; } _regeneratorDefine2 = function _regeneratorDefine(e, r, n, t) { function o(r, n) { _regeneratorDefine2(e, r, function (e) { return this._invoke(r, n, e); }); } r ? i ? i(e, r, { value: n, enumerable: !t, configurable: !t, writable: !t }) : e[r] = n : (o("next", 0), o("throw", 1), o("return", 2)); }, _regeneratorDefine2(e, r, n, t); }
function _OverloadYield(e, d) { this.v = e, this.k = d; }
function ownKeys(e, r) { var t = Object.keys(e); if (Object.getOwnPropertySymbols) { var o = Object.getOwnPropertySymbols(e); r && (o = o.filter(function (r) { return Object.getOwnPropertyDescriptor(e, r).enumerable; })), t.push.apply(t, o); } return t; }
function _objectSpread(e) { for (var r = 1; r < arguments.length; r++) { var t = null != arguments[r] ? arguments[r] : {}; r % 2 ? ownKeys(Object(t), !0).forEach(function (r) { _defineProperty(e, r, t[r]); }) : Object.getOwnPropertyDescriptors ? Object.defineProperties(e, Object.getOwnPropertyDescriptors(t)) : ownKeys(Object(t)).forEach(function (r) { Object.defineProperty(e, r, Object.getOwnPropertyDescriptor(t, r)); }); } return e; }
function _defineProperty(e, r, t) { return (r = _toPropertyKey(r)) in e ? Object.defineProperty(e, r, { value: t, enumerable: !0, configurable: !0, writable: !0 }) : e[r] = t, e; }
function _toPropertyKey(t) { var i = _toPrimitive(t, "string"); return "symbol" == _typeof(i) ? i : i + ""; }
function _toPrimitive(t, r) { if ("object" != _typeof(t) || !t) return t; var e = t[Symbol.toPrimitive]; if (void 0 !== e) { var i = e.call(t, r || "default"); if ("object" != _typeof(i)) return i; throw new TypeError("@@toPrimitive must return a primitive value."); } return ("string" === r ? String : Number)(t); }
function _slicedToArray(r, e) { return _arrayWithHoles(r) || _iterableToArrayLimit(r, e) || _unsupportedIterableToArray(r, e) || _nonIterableRest(); }
function _nonIterableRest() { throw new TypeError("Invalid attempt to destructure non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method."); }
function _unsupportedIterableToArray(r, a) { if (r) { if ("string" == typeof r) return _arrayLikeToArray(r, a); var t = {}.toString.call(r).slice(8, -1); return "Object" === t && r.constructor && (t = r.constructor.name), "Map" === t || "Set" === t ? Array.from(r) : "Arguments" === t || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(t) ? _arrayLikeToArray(r, a) : void 0; } }
function _arrayLikeToArray(r, a) { (null == a || a > r.length) && (a = r.length); for (var e = 0, n = Array(a); e < a; e++) n[e] = r[e]; return n; }
function _iterableToArrayLimit(r, l) { var t = null == r ? null : "undefined" != typeof Symbol && r[Symbol.iterator] || r["@@iterator"]; if (null != t) { var e, n, i, u, a = [], f = !0, o = !1; try { if (i = (t = t.call(r)).next, 0 === l) { if (Object(t) !== t) return; f = !1; } else for (; !(f = (e = i.call(t)).done) && (a.push(e.value), a.length !== l); f = !0); } catch (r) { o = !0, n = r; } finally { try { if (!f && null != t["return"] && (u = t["return"](), Object(u) !== u)) return; } finally { if (o) throw n; } } return a; } }
function _arrayWithHoles(r) { if (Array.isArray(r)) return r; }
function asyncGeneratorStep(n, t, e, r, o, a, c) { try { var i = n[a](c), u = i.value; } catch (n) { return void e(n); } i.done ? t(u) : Promise.resolve(u).then(r, o); }
function _asyncToGenerator(n) { return function () { var t = this, e = arguments; return new Promise(function (r, o) { var a = n.apply(t, e); function _next(n) { asyncGeneratorStep(a, r, o, _next, _throw, "next", n); } function _throw(n) { asyncGeneratorStep(a, r, o, _next, _throw, "throw", n); } _next(void 0); }); }; }
var _React = React,
  useState = _React.useState,
  useRef = _React.useRef,
  useEffect = _React.useEffect,
  useCallback = _React.useCallback,
  useMemo = _React.useMemo;

// ── API helpers ───────────────────────────────────────────────────────────
function apiFetch(_x) {
  return _apiFetch.apply(this, arguments);
}
function _apiFetch() {
  _apiFetch = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee15(path) {
    var opts,
      res,
      json,
      _args15 = arguments;
    return _regeneratorRuntime().wrap(function _callee15$(_context15) {
      while (1) switch (_context15.prev = _context15.next) {
        case 0:
          opts = _args15.length > 1 && _args15[1] !== undefined ? _args15[1] : {};
          _context15.next = 3;
          return fetch(path, _objectSpread({
            headers: {
              'Content-Type': 'application/json'
            }
          }, opts));
        case 3:
          res = _context15.sent;
          _context15.next = 6;
          return res.json()["catch"](function () {
            return {};
          });
        case 6:
          json = _context15.sent;
          return _context15.abrupt("return", {
            ok: res.ok,
            status: res.status,
            data: json
          });
        case 8:
        case "end":
          return _context15.stop();
      }
    }, _callee15);
  }));
  return _apiFetch.apply(this, arguments);
}
var _onSessionExpired = null;
function setSessionExpiredHandler(fn) {
  _onSessionExpired = fn;
}
function apiGame(path) {
  var opts = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : {};
  return apiFetch(path, opts).then(function (r) {
    if (r.status === 401 && _onSessionExpired) _onSessionExpired();
    return r;
  });
}

// ── Fire Effect ────────────────────────────────────────────────────────────
function makeParticle(w, h, maxHeight, intensity, scattered) {
  // scattered=true: spawn within visible fire zone for immediate appearance
  var y = scattered ? h - Math.random() * maxHeight : h - Math.random() * 8;
  var lifeUsed = scattered ? Math.random() * 60 : 0;
  return {
    x: Math.random() * w,
    y: y,
    vx: (Math.random() - 0.5) * 1.2,
    vy: -(1.5 + Math.random() * 4.0 * intensity + 0.5),
    size: 1.5 + Math.random() * 4.0 * intensity,
    life: lifeUsed,
    maxLife: 60 + Math.random() * 80,
    hue: 10 + Math.random() * 35,
    seed: Math.random() * 100
  };
}
function initMode3(state, w, h) {
  var infInt = arguments.length > 3 && arguments[3] !== undefined ? arguments[3] : 0;
  var bw = Math.max(1, Math.ceil(w / 4));
  var bh = Math.max(1, Math.ceil(h / 4));
  state.buf = new Uint8Array(bw * bh);
  state.bw = bw;
  state.bh = bh;
  var off = document.createElement('canvas');
  off.width = bw;
  off.height = bh;
  state.offCanvas = off;
  state.offCtx = off.getContext('2d');
  // only pre-warm if inferno has actually started
  if (infInt <= 0) return;
  var seedHeat = 60 + infInt * 195;
  var warmupSteps = Math.floor(30 + infInt * 60);
  for (var warmup = 0; warmup < warmupSteps; warmup++) {
    for (var i = 0; i < bw; i++) {
      var row = bh - 1 - Math.floor(Math.random() * 3);
      state.buf[row * bw + i] = Math.min(255, seedHeat * (0.7 + Math.random() * 0.6));
    }
    for (var y = 0; y < bh - 1; y++) {
      for (var x = 0; x < bw; x++) {
        var below = state.buf[(y + 1) * bw + x];
        var bl = x > 0 ? state.buf[(y + 1) * bw + (x - 1)] : below;
        var br = x < bw - 1 ? state.buf[(y + 1) * bw + (x + 1)] : below;
        var wl = 0.8 + Math.random() * 0.6;
        var wr = 0.8 + Math.random() * 0.6;
        var avg = (below * 1.2 + bl * wl + br * wr) / (1.2 + wl + wr);
        var warmCool = infInt > 0 ? Math.max(0.05, 255 / (bh * infInt) - 0.6) : 50;
        state.buf[y * bw + x] = Math.max(0, avg - (warmCool + Math.random() * 1.2));
      }
    }
  }
}
function FireEffect(_ref) {
  var streak = _ref.streak,
    mode = _ref.mode,
    lowSpec = _ref.lowSpec;
  var animRef = useRef(null);
  var stateRef = useRef({});
  var targetRef = useRef({
    intensity: 0,
    inferno: 0
  });
  var intensity = Math.min(Math.max(streak - 3, 0) / 47, 1);
  var infernoIntensity = Math.min(Math.max(streak - 10, 0) / 40, 1);
  var activeMode = lowSpec ? 1 : mode;

  // Keep targets updated every render without restarting the effect
  targetRef.current.intensity = intensity;
  targetRef.current.inferno = infernoIntensity;
  useEffect(function () {
    var canvas = document.createElement('canvas');
    canvas.style.cssText = ['position:fixed', 'inset:0', 'width:100vw', 'height:100vh', 'z-index:1', 'pointer-events:none'].join(';');
    var root = document.getElementById('root') || document.body;
    root.appendChild(canvas);
    var ctx = canvas.getContext('2d');
    function setSize() {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      if (activeMode === 2 || activeMode === 3) initMode3(stateRef.current, canvas.width, canvas.height, targetRef.current.inferno);
    }
    setSize();
    window.addEventListener('resize', setSize);

    // Seed particles at current intensity so there's no startup flash
    var w = canvas.width,
      h = canvas.height;
    var initInt = targetRef.current.intensity;
    if (initInt > 0 && (activeMode === 1 || activeMode === 2)) {
      var maxH = h * (0.05 + initInt * 0.82);
      var count = lowSpec ? Math.floor(25 + initInt * 150) : Math.floor(50 + initInt * 350);
      stateRef.current.particles = Array.from({
        length: count
      }, function (_, i) {
        return makeParticle(w, h, maxH, initInt, i < count * 0.8);
      });
    }

    // Lerped display values — these change every frame, never trigger re-mounts
    var dispInt = targetRef.current.intensity;
    var dispInfern = targetRef.current.inferno;
    var last = 0;
    var FRAME_MS = lowSpec ? 1000 / 24 : 1000 / 40;
    function tick(ts) {
      if (ts - last < FRAME_MS) {
        animRef.current = requestAnimationFrame(tick);
        return;
      }
      last = ts;

      // Lerp towards targets — faster falling (loss) than rising (win)
      var tgt = targetRef.current;
      var intSpeed = dispInt > tgt.intensity ? 0.10 : 0.06;
      var infSpeed = dispInfern > tgt.inferno ? 0.10 : 0.06;
      dispInt += (tgt.intensity - dispInt) * intSpeed;
      dispInfern += (tgt.inferno - dispInfern) * infSpeed;
      if (Math.abs(dispInt - tgt.intensity) < 0.001) dispInt = tgt.intensity;
      if (Math.abs(dispInfern - tgt.inferno) < 0.001) dispInfern = tgt.inferno;
      var cw = canvas.width,
        ch = canvas.height;
      ctx.clearRect(0, 0, cw, ch);
      if (dispInt > 0) {
        if (activeMode === 1) renderEmbers(ctx, cw, ch, dispInt, ts / 1000, stateRef.current);else if (activeMode === 2) renderMix(ctx, cw, ch, dispInt, dispInfern, ts / 1000, stateRef.current);else if (activeMode === 3) renderInferno(ctx, cw, ch, dispInfern, stateRef.current);
      }
      animRef.current = requestAnimationFrame(tick);
    }
    animRef.current = requestAnimationFrame(tick);
    return function () {
      cancelAnimationFrame(animRef.current);
      window.removeEventListener('resize', setSize);
      (document.getElementById('root') || document.body).removeChild(canvas);
    };
  }, [activeMode, lowSpec]); // intensity deliberately excluded — lerped inside tick

  return null;
}

// Mode 1: rising ember particles — spawn distributed immediately
function renderEmbers(ctx, w, h, intensity, t, state) {
  var maxHeight = h * (0.05 + intensity * 0.82);
  var count = Math.floor(50 + intensity * 350);
  var parts = state.particles;
  if (!parts) return;
  while (parts.length < count) parts.push(makeParticle(w, h, maxHeight, intensity, false));
  if (parts.length > count) parts.splice(count);
  for (var i = 0; i < parts.length; i++) {
    var p = parts[i];
    p.life++;
    p.x += p.vx + Math.sin(t * 2.2 + p.seed) * 0.6;
    p.y += p.vy;
    if (p.y < h - maxHeight || p.life > p.maxLife) {
      parts[i] = makeParticle(w, h, maxHeight, intensity, false);
      continue;
    }
    var age = p.life / p.maxLife;
    // glow: brightest and largest at the base, fading as it rises
    var riseFrac = Math.max(0, (h - p.y) / maxHeight); // 0=bottom, 1=top
    var size = p.size * (1 - riseFrac * 0.5) * (1 - age * 0.4);
    var light = 50 + riseFrac * 30 + intensity * 15;
    var alpha = (1 - age * 0.7) * (0.75 + intensity * 0.25) * (1 - riseFrac * 0.5);
    ctx.globalAlpha = Math.min(alpha, 1);
    ctx.fillStyle = "hsl(".concat(p.hue, ", 100%, ").concat(light, "%)");
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
    var bw = state.bw,
      bh = state.bh,
      buf = state.buf,
      offCtx = state.offCtx,
      offCanvas = state.offCanvas;
    var imgData = offCtx.createImageData(bw, bh);
    var pix = imgData.data;
    for (var i = 0; i < bw * bh; i++) {
      var v = buf[i];
      if (v === 0) continue;
      var r = void 0,
        g = void 0,
        b = void 0,
        a = void 0;
      if (v < 64) {
        r = v * 4;
        g = 0;
        b = 0;
        a = v * 2;
      } else if (v < 128) {
        r = 255;
        g = (v - 64) * 4;
        b = 0;
        a = 120 + (v - 64);
      } else if (v < 192) {
        r = 255;
        g = 128 + (v - 128) * 2;
        b = 0;
        a = 175;
      } else {
        r = 255;
        g = 200 + (v - 192);
        b = (v - 192) * 3;
        a = 200;
      }
      pix[i * 4] = r;
      pix[i * 4 + 1] = g;
      pix[i * 4 + 2] = b;
      pix[i * 4 + 3] = a;
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
  var maxHeight = h * (0.05 + intensity * 0.82);
  var count = Math.floor(50 + intensity * 350);
  var parts = state.particles;
  if (parts) {
    while (parts.length < count) parts.push(makeParticle(w, h, maxHeight, intensity, false));
    if (parts.length > count) parts.splice(count);
    for (var _i = 0; _i < parts.length; _i++) {
      var p = parts[_i];
      p.life++;
      p.x += p.vx + Math.sin(t * 2.2 + p.seed) * 0.6;
      p.y += p.vy;
      if (p.y < h - maxHeight || p.life > p.maxLife) {
        parts[_i] = makeParticle(w, h, maxHeight, intensity, false);
        continue;
      }
      var age = p.life / p.maxLife;
      var riseFrac = Math.max(0, (h - p.y) / maxHeight);
      var size = p.size * (1 - riseFrac * 0.4) * (1 - age * 0.4);
      var light = 55 + riseFrac * 30 + intensity * 10;
      var alpha = (1 - age * 0.65) * (0.7 + intensity * 0.3) * (1 - riseFrac * 0.4);
      ctx.globalAlpha = Math.min(alpha, 1);
      ctx.fillStyle = "hsl(".concat(p.hue, ", 100%, ").concat(light, "%)");
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
  var bw = state.bw,
    bh = state.bh,
    buf = state.buf;

  // Always keep the very bottom row at max heat — anchors fire to ground level
  for (var x = 0; x < bw; x++) {
    buf[(bh - 1) * bw + x] = 200 + Math.floor(Math.random() * 55);
  }

  // Additional heat sources scale from 0 for intensity-driven height
  var baseCount = Math.floor(bw * infernoIntensity);
  var sources = Math.max(0, baseCount + Math.floor((Math.random() - 0.5) * baseCount * 0.8));
  var baseStr = 60 + infernoIntensity * 195;
  for (var i = 0; i < sources; i++) {
    var _x2 = Math.floor(Math.random() * bw);
    var row = bh - 1 - Math.floor(Math.random() * 3);
    var str = baseStr * (0.5 + Math.random() * 0.8);
    buf[row * bw + _x2] = Math.min(255, buf[row * bw + _x2] + str);
  }

  // Derive cooling so fire height is LINEAR in infernoIntensity:
  //   height_cells ≈ 255 / baseCool  →  baseCool = 255 / (bh * infernoIntensity)
  // Subtract noise average (0.6) so actual mean cooling lands on the target.
  var baseCool = infernoIntensity > 0 ? Math.max(0.05, 255 / (2 * bh * infernoIntensity) - 0.6) : 50;
  for (var y = 0; y < bh - 1; y++) {
    for (var _x3 = 0; _x3 < bw; _x3++) {
      var below = buf[(y + 1) * bw + _x3];
      var bl = _x3 > 0 ? buf[(y + 1) * bw + (_x3 - 1)] : below;
      var br = _x3 < bw - 1 ? buf[(y + 1) * bw + (_x3 + 1)] : below;
      var wl = 0.8 + Math.random() * 0.6;
      var wr = 0.8 + Math.random() * 0.6;
      var avg = (below * 1.2 + bl * wl + br * wr) / (1.2 + wl + wr);
      var cooling = baseCool + Math.random() * 1.2;
      buf[y * bw + _x3] = Math.max(0, avg - cooling);
    }
  }
}

// Mode 3: cellular automaton fire (solo, full opacity)
function renderInferno(ctx, w, h, intensity, state) {
  if (!state.buf || !state.offCtx) return;
  var bw = state.bw,
    bh = state.bh,
    buf = state.buf,
    offCtx = state.offCtx,
    offCanvas = state.offCanvas;
  stepInferno(state, intensity);
  var imgData = offCtx.createImageData(bw, bh);
  var pix = imgData.data;
  for (var i = 0; i < bw * bh; i++) {
    var v = buf[i];
    if (v === 0) continue;
    var r = void 0,
      g = void 0,
      b = void 0,
      a = void 0;
    if (v < 64) {
      r = v * 4;
      g = 0;
      b = 0;
      a = v * 3;
    } else if (v < 128) {
      r = 255;
      g = (v - 64) * 4;
      b = 0;
      a = 160 + (v - 64);
    } else if (v < 192) {
      r = 255;
      g = 128 + (v - 128) * 2;
      b = 0;
      a = 210;
    } else {
      r = 255;
      g = 200 + (v - 192);
      b = (v - 192) * 4;
      a = 235;
    }
    pix[i * 4] = r;
    pix[i * 4 + 1] = g;
    pix[i * 4 + 2] = b;
    pix[i * 4 + 3] = a;
  }
  offCtx.putImageData(imgData, 0, 0);
  ctx.save();
  ctx.imageSmoothingEnabled = false;
  ctx.drawImage(offCanvas, 0, 0, bw, bh, 0, 0, w, h);
  ctx.restore();
}

// ── Draw main wheel ────────────────────────────────────────────────────────
function drawWheel(canvas) {
  var theme = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : 'default';
  var ctx = canvas.getContext('2d');
  var size = canvas.width;
  var cx = size / 2,
    cy = size / 2,
    r = size / 2 - 4;
  ctx.clearRect(0, 0, size, size);
  var THEMES = {
    "default": [{
      label: 'WIN',
      color: '#550088',
      bright: '#AA00FF',
      start: -Math.PI / 2,
      end: Math.PI / 2
    }, {
      label: 'LOSE',
      color: '#7a3300',
      bright: '#FF6600',
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
    }],
    "void": [{
      label: 'WIN',
      color: '#0a0a1a',
      bright: '#6633FF',
      start: -Math.PI / 2,
      end: Math.PI / 2
    }, {
      label: 'LOSE',
      color: '#0d0010',
      bright: '#330066',
      start: Math.PI / 2,
      end: Math.PI * 1.5
    }],
    gold: [{
      label: 'WIN',
      color: '#7a5c00',
      bright: '#FFE566',
      start: -Math.PI / 2,
      end: Math.PI / 2
    }, {
      label: 'LOSE',
      color: '#3d2000',
      bright: '#CC8800',
      start: Math.PI / 2,
      end: Math.PI * 1.5
    }],
    bioluminescence: [{
      label: 'WIN',
      color: '#003a4d',
      bright: '#00E5FF',
      start: -Math.PI / 2,
      end: Math.PI / 2
    }, {
      label: 'LOSE',
      color: '#4d1020',
      bright: '#FF6B6B',
      start: Math.PI / 2,
      end: Math.PI * 1.5
    }],
    night_ocean: [{
      label: 'WIN',
      color: '#1a0d4d',
      bright: '#5533FF',
      start: -Math.PI / 2,
      end: Math.PI / 2
    }, {
      label: 'LOSE',
      color: '#3d0011',
      bright: '#CC2244',
      start: Math.PI / 2,
      end: Math.PI * 1.5
    }]
  };
  var segments = THEMES[theme] || THEMES["default"];
  segments.forEach(function (seg) {
    var grad = ctx.createRadialGradient(cx, cy, r * 0.1, cx, cy, r);
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
    var mx = cx + r * Math.cos(seg.start);
    var my = cy + r * Math.sin(seg.start);
    ctx.lineTo(mx, my);
    ctx.strokeStyle = '#111';
    ctx.lineWidth = 4;
    ctx.stroke();
    var midAngle = (seg.start + seg.end) / 2;
    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(midAngle);
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.font = "bold ".concat(size * 0.1, "px 'Oswald', Arial Black, sans-serif");
    ctx.fillStyle = '#FFF';
    ctx.shadowColor = 'rgba(0,0,0,0.8)';
    ctx.shadowBlur = 8;
    ctx.fillText(seg.label, r * 0.55, 0);
    ctx.restore();
    var dotCount = 8;
    for (var i = 0; i <= dotCount; i++) {
      var a = seg.start + (seg.end - seg.start) * (i / dotCount);
      var dr = r * 0.88;
      var dx = cx + dr * Math.cos(a);
      var dy = cy + dr * Math.sin(a);
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
  var ctx = canvas.getContext('2d');
  var size = canvas.width;
  var cx = size / 2,
    cy = size / 2,
    r = size / 2 - 4;
  ctx.clearRect(0, 0, size, size);

  // WIN (50%): canvas angles centered at 0° (right side = 3 o'clock)
  // At CSS rotation 270° the right side is at 12 o'clock (pointer)
  var winHalf = Math.PI * 0.50; // ±90°
  var winStart = -winHalf;
  var winEnd = winHalf;

  // FAIL segment (large)
  var gFail = ctx.createRadialGradient(cx, cy, r * 0.1, cx, cy, r);
  gFail.addColorStop(0, '#FF5555');
  gFail.addColorStop(1, '#770000');
  ctx.beginPath();
  ctx.moveTo(cx, cy);
  ctx.arc(cx, cy, r, winEnd, winStart + 2 * Math.PI);
  ctx.closePath();
  ctx.fillStyle = gFail;
  ctx.fill();

  // WIN segment (cyan)
  var gWin = ctx.createRadialGradient(cx, cy, r * 0.1, cx, cy, r);
  gWin.addColorStop(0, '#55EEEE');
  gWin.addColorStop(1, '#006666');
  ctx.beginPath();
  ctx.moveTo(cx, cy);
  ctx.arc(cx, cy, r, winStart, winEnd);
  ctx.closePath();
  ctx.fillStyle = gWin;
  ctx.fill();

  // Divider lines
  [winStart, winEnd].forEach(function (a) {
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
  if (n >= 1e12) return (n / 1e12).toFixed(n >= 10e12 ? 2 : 3).replace(/\.?0+$/, '') + 'T';
  if (n >= 1e9) return (n / 1e9).toFixed(n >= 10e9 ? 2 : 3).replace(/\.?0+$/, '') + 'B';
  if (n >= 1e6) return (n / 1e6).toFixed(n >= 10e6 ? 2 : 3).replace(/\.?0+$/, '') + 'M';
  if (n >= 10e3) return (n >= 100e3 ? Math.round(n / 1e3) : (n / 1e3).toFixed(1).replace(/\.0$/, '')) + 'K';
  return String(n);
}

// ── Scoreboard ────────────────────────────────────────────────────────────
var Scoreboard = React.memo(function Scoreboard(_ref2) {
  var wins = _ref2.wins,
    losses = _ref2.losses,
    lastResult = _ref2.lastResult;
  return /*#__PURE__*/React.createElement("div", {
    className: "scoreboard"
  }, /*#__PURE__*/React.createElement("div", {
    className: "score-box wins-box"
  }, /*#__PURE__*/React.createElement("span", {
    className: "score-label"
  }, "Wins"), /*#__PURE__*/React.createElement("span", {
    className: "score-value ".concat(lastResult === 'win' ? 'score-bump' : ''),
    key: wins
  }, fmt(wins))), /*#__PURE__*/React.createElement("div", {
    className: "score-box losses-box"
  }, /*#__PURE__*/React.createElement("span", {
    className: "score-label"
  }, "Losses"), /*#__PURE__*/React.createElement("span", {
    className: "score-value ".concat(lastResult === 'lose' ? 'score-bump' : ''),
    key: losses
  }, fmt(losses))));
});

// ── Confetti ──────────────────────────────────────────────────────────────
var CONFETTI_COLORS = ['#FFD700', '#FF6600', '#FF3333', '#00FF88', '#AA00FF', '#FF00FF', '#FFFFFF'];
function Confetti(_ref3) {
  var active = _ref3.active,
    _ref3$count = _ref3.count,
    count = _ref3$count === void 0 ? 80 : _ref3$count;
  var pieces = useMemo(function () {
    if (!active) return [];
    return Array.from({
      length: count
    }, function (_, i) {
      return {
        key: i,
        left: Math.random() * 100,
        delay: Math.random() * 0.8,
        dur: 1.8 + Math.random() * 1.5,
        color: CONFETTI_COLORS[Math.floor(Math.random() * CONFETTI_COLORS.length)],
        size: 8 + Math.floor(Math.random() * 10),
        shape: Math.random() > 0.5 ? '50%' : '2px'
      };
    });
  }, [active, count]);
  return /*#__PURE__*/React.createElement("div", {
    className: "confetti-container"
  }, pieces.map(function (p) {
    return /*#__PURE__*/React.createElement("div", {
      key: p.key,
      className: "confetti-piece",
      style: {
        left: "".concat(p.left, "%"),
        top: 0,
        width: p.size,
        height: p.size,
        background: p.color,
        borderRadius: p.shape,
        animationDuration: "".concat(p.dur, "s"),
        animationDelay: "".concat(p.delay, "s")
      }
    });
  }));
}

// ── Guard Mini-Wheel ──────────────────────────────────────────────────────
function GuardWheel(_ref4) {
  var blocked = _ref4.blocked,
    _ref4$speedMult = _ref4.speedMult,
    speedMult = _ref4$speedMult === void 0 ? 1.0 : _ref4$speedMult,
    onComplete = _ref4.onComplete;
  var canvasRef = useRef(null);
  var _useState = useState(0),
    _useState2 = _slicedToArray(_useState, 2),
    guardRotation = _useState2[0],
    setGuardRotation = _useState2[1];
  var _useState3 = useState(false),
    _useState4 = _slicedToArray(_useState3, 2),
    revealed = _useState4[0],
    setRevealed = _useState4[1];
  var _useState5 = useState(1.8),
    _useState6 = _slicedToArray(_useState5, 2),
    transDur = _useState6[0],
    setTransDur = _useState6[1];
  useEffect(function () {
    var canvas = canvasRef.current;
    if (canvas) drawGuardWheel(canvas);
    var dur = 1.8 * speedMult;
    setTransDur(dur);

    // WIN segment centered at canvas angle 0° (right side).
    // CSS rotation 270° brings right side to 12 o'clock (pointer).
    // FAIL centered at canvas 180°; CSS rotation 90° brings it to pointer.
    var baseSpins = 4 * 360;
    var targetAngle = blocked ? 270 : 90;
    // Delay so browser paints rotation=0 before transitioning (otherwise no animation)
    var spinTimer = setTimeout(function () {
      return setGuardRotation(baseSpins + targetAngle);
    }, 50);
    var revealTimer = setTimeout(function () {
      return setRevealed(true);
    }, Math.round(2000 * speedMult));
    var completeTimer = setTimeout(function () {
      return onComplete();
    }, Math.round(3400 * speedMult));
    return function () {
      clearTimeout(spinTimer);
      clearTimeout(revealTimer);
      clearTimeout(completeTimer);
    };
  }, []); // eslint-disable-line

  return /*#__PURE__*/React.createElement("div", {
    className: "guard-overlay"
  }, /*#__PURE__*/React.createElement("div", {
    className: "guard-card"
  }, /*#__PURE__*/React.createElement("div", {
    className: "guard-title"
  }, "\uD83D\uDEE1\uFE0F Guard Activating\u2026"), /*#__PURE__*/React.createElement("div", {
    className: "guard-wheel-wrap"
  }, /*#__PURE__*/React.createElement("div", {
    className: "guard-pointer-arrow"
  }), /*#__PURE__*/React.createElement("canvas", {
    ref: canvasRef,
    width: 180,
    height: 180,
    className: "guard-canvas",
    style: {
      transform: "rotate(".concat(guardRotation, "deg)"),
      transition: "transform ".concat(transDur, "s cubic-bezier(0.17, 0.67, 0.12, 0.99)")
    }
  })), revealed && /*#__PURE__*/React.createElement("div", {
    className: "guard-result ".concat(blocked ? 'blocked' : 'failed')
  }, blocked ? '🛡️ BLOCKED!' : '💔 Guard Failed')));
}

// ── Fish Catalog (client-side mirror of server FISH_CATALOG) ──────────────
var FISH_CATALOG_CLIENT = [{
  id: 'minnow',
  emoji: '🐟',
  name: 'Minnow',
  value: 1,
  tier: 'Common'
}, {
  id: 'clownfish',
  emoji: '🐠',
  name: 'Clownfish',
  value: 3,
  tier: 'Common'
}, {
  id: 'pufferfish',
  emoji: '🐡',
  name: 'Pufferfish',
  value: 3,
  tier: 'Common'
}, {
  id: 'shrimp',
  emoji: '🦐',
  name: 'Shrimp',
  value: 2,
  tier: 'Common'
}, {
  id: 'crab',
  emoji: '🦀',
  name: 'Crab',
  value: 8,
  tier: 'Uncommon'
}, {
  id: 'squid',
  emoji: '🦑',
  name: 'Squid',
  value: 8,
  tier: 'Uncommon'
}, {
  id: 'octopus',
  emoji: '🐙',
  name: 'Octopus',
  value: 12,
  tier: 'Uncommon'
}, {
  id: 'lobster',
  emoji: '🦞',
  name: 'Lobster',
  value: 20,
  tier: 'Rare'
}, {
  id: 'dolphin',
  emoji: '🐬',
  name: 'Dolphin',
  value: 30,
  tier: 'Rare'
}, {
  id: 'shark',
  emoji: '🦈',
  name: 'Shark',
  value: 40,
  tier: 'Rare'
}, {
  id: 'whale',
  emoji: '🐋',
  name: 'Blue Whale',
  value: 75,
  tier: 'Legendary'
}, {
  id: 'mermaid',
  emoji: '🧜',
  name: 'Mermaid',
  value: 120,
  tier: 'Legendary'
}, {
  id: 'lucky',
  emoji: '⭐',
  name: 'Lucky Fish',
  value: 100,
  tier: 'Legendary'
}];

// ── Fish Encyclopaedia ────────────────────────────────────────────────────
function FishEncyclopedia(_ref5) {
  var caughtSpecies = _ref5.caughtSpecies,
    onClose = _ref5.onClose;
  var discovered = new Set(caughtSpecies || []);
  var count = discovered.size;
  var TIER_ORDER = {
    Common: 0,
    Uncommon: 1,
    Rare: 2,
    Legendary: 3
  };
  var sorted = [].concat(FISH_CATALOG_CLIENT).sort(function (a, b) {
    return TIER_ORDER[a.tier] - TIER_ORDER[b.tier];
  });
  return /*#__PURE__*/React.createElement("div", {
    className: "encyclopedia-overlay",
    onClick: onClose
  }, /*#__PURE__*/React.createElement("div", {
    className: "encyclopedia-card",
    onClick: function onClick(e) {
      return e.stopPropagation();
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "encyclopedia-title"
  }, "\uD83D\uDCD6 Fish Encyclopaedia"), /*#__PURE__*/React.createElement("div", {
    className: "encyclopedia-progress"
  }, "Discovered: ", count, " / ", FISH_CATALOG_CLIENT.length), /*#__PURE__*/React.createElement("button", {
    className: "encyclopedia-close-btn",
    onClick: onClose
  }, "\u2715"), /*#__PURE__*/React.createElement("div", {
    className: "encyclopedia-grid"
  }, sorted.map(function (fish) {
    var known = discovered.has(fish.id);
    return /*#__PURE__*/React.createElement("div", {
      key: fish.id,
      className: "encyclopedia-entry".concat(known ? ' unlocked' : ' locked')
    }, /*#__PURE__*/React.createElement("span", {
      className: "encyclopedia-entry-emoji"
    }, known ? fish.emoji : '❓'), /*#__PURE__*/React.createElement("span", {
      className: "encyclopedia-entry-name"
    }, known ? fish.name : '???'), /*#__PURE__*/React.createElement("span", {
      className: "encyclopedia-entry-tier ".concat(fish.tier)
    }, fish.tier), /*#__PURE__*/React.createElement("span", {
      className: "encyclopedia-entry-value"
    }, known ? "".concat(fish.value, " \uD83D\uDC1F") : '???'));
  }))));
}

// ── Fishing Panel ─────────────────────────────────────────────────────────
function FishingPanel(_ref6) {
  var fishClicks = _ref6.fishClicks,
    fishData = _ref6.fishData,
    caughtSpecies = _ref6.caughtSpecies,
    fishingLuckyNext = _ref6.fishingLuckyNext,
    ownedItems = _ref6.ownedItems,
    fishPanelScale = _ref6.fishPanelScale,
    onFishBucksUpdate = _ref6.onFishBucksUpdate,
    onCaughtSpeciesUpdate = _ref6.onCaughtSpeciesUpdate;
  var _useState7 = useState('idle'),
    _useState8 = _slicedToArray(_useState7, 2),
    phase = _useState8[0],
    setPhase = _useState8[1]; // idle | waiting | bite | reeling | success | miss
  var _useState9 = useState(null),
    _useState0 = _slicedToArray(_useState9, 2),
    biteAt = _useState0[0],
    setBiteAt = _useState0[1];
  var _useState1 = useState(null),
    _useState10 = _slicedToArray(_useState1, 2),
    expiresAt = _useState10[0],
    setExpiresAt = _useState10[1];
  var _useState11 = useState(null),
    _useState12 = _slicedToArray(_useState11, 2),
    lastCatch = _useState12[0],
    setLastCatch = _useState12[1];
  var _useState13 = useState('late'),
    _useState14 = _slicedToArray(_useState13, 2),
    missReason = _useState14[0],
    setMissReason = _useState14[1]; // 'late' | 'early'
  var _useState15 = useState(fishingLuckyNext || false),
    _useState16 = _slicedToArray(_useState15, 2),
    luckyNextActive = _useState16[0],
    setLuckyNextActive = _useState16[1];
  var _useState17 = useState(false),
    _useState18 = _slicedToArray(_useState17, 2),
    autoCast = _useState18[0],
    setAutoCast = _useState18[1];
  var _useState19 = useState(false),
    _useState20 = _slicedToArray(_useState19, 2),
    autoFish = _useState20[0],
    setAutoFish = _useState20[1];
  var _useState21 = useState(null),
    _useState22 = _slicedToArray(_useState21, 2),
    autoFishPopup = _useState22[0],
    setAutoFishPopup = _useState22[1]; // { key, type:'hit'|'miss', emoji?, value? }
  var autoFishRef = useRef(false);
  var autoCastRef = useRef(false);
  var phaseRef = useRef('idle');
  var biteTimerRef = useRef(null);
  var missTimerRef = useRef(null);
  var pollSessionRef = useRef(0);
  var autoFishIntervalRef = useRef(null);
  var autoFishPopupTimerRef = useRef(null);
  var reelInFlightRef = useRef(false);
  var consecutiveMissesRef = useRef(0);
  var autoFishPopupKeyRef = useRef(0);
  var hasAutoCast = ownedItems.includes('auto_cast');
  var hasAutoFisher = ownedItems.includes('autofisher_1');
  var _ref7 = fishData || {
      emoji: '🐟'
    },
    fisherEmoji = _ref7.emoji;
  var scale = fishPanelScale || 1.0;
  useEffect(function () {
    autoFishRef.current = autoFish;
  }, [autoFish]);
  useEffect(function () {
    autoCastRef.current = autoCast;
  }, [autoCast]);
  useEffect(function () {
    phaseRef.current = phase;
  }, [phase]);
  useEffect(function () {
    setLuckyNextActive(fishingLuckyNext || false);
  }, [fishingLuckyNext]);
  var countMiss = useCallback(function () {
    if (!autoCastRef.current) return;
    consecutiveMissesRef.current += 1;
    if (consecutiveMissesRef.current >= 3) {
      setAutoCast(false);
      consecutiveMissesRef.current = 0;
    }
  }, []);
  var showAutoFishPopup = useCallback(function (popup) {
    if (autoFishPopupTimerRef.current) clearTimeout(autoFishPopupTimerRef.current);
    autoFishPopupKeyRef.current += 1;
    setAutoFishPopup(_objectSpread(_objectSpread({}, popup), {}, {
      key: autoFishPopupKeyRef.current
    }));
    var dur = popup.type === 'hit' ? 2000 : 1500;
    autoFishPopupTimerRef.current = setTimeout(function () {
      return setAutoFishPopup(null);
    }, dur);
  }, []);

  // Auto-fish tick loop — fires every 6 s (half-speed vs manual fishing)
  useEffect(function () {
    if (!autoFish) {
      clearInterval(autoFishIntervalRef.current);
      if (autoFishPopupTimerRef.current) clearTimeout(autoFishPopupTimerRef.current);
      return;
    }
    var tick = /*#__PURE__*/function () {
      var _ref8 = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee() {
        var _yield$apiGame, ok, data, fish, emoji, name;
        return _regeneratorRuntime().wrap(function _callee$(_context) {
          while (1) switch (_context.prev = _context.next) {
            case 0:
              if (autoFishRef.current) {
                _context.next = 2;
                break;
              }
              return _context.abrupt("return");
            case 2:
              _context.next = 4;
              return apiGame('/api/auto-fish-tick', {
                method: 'POST',
                body: '{}'
              });
            case 4:
              _yield$apiGame = _context.sent;
              ok = _yield$apiGame.ok;
              data = _yield$apiGame.data;
              if (!(!ok || !data.result)) {
                _context.next = 9;
                break;
              }
              return _context.abrupt("return");
            case 9:
              if (data.result === 'hit') {
                fish = FISH_CATALOG_CLIENT.find(function (f) {
                  return f.id === data.species;
                });
                emoji = fish ? fish.emoji : '🐟';
                name = fish ? fish.name : data.species;
                setLastCatch({
                  emoji: emoji,
                  name: name,
                  value: data.value,
                  isNew: !!data.first_catch,
                  isLucky: false,
                  doubled: false
                });
                onFishBucksUpdate(data.fish_clicks);
                if (data.first_catch) onCaughtSpeciesUpdate(data.species);
                showAutoFishPopup({
                  type: 'hit',
                  emoji: emoji,
                  value: data.value,
                  isNew: !!data.first_catch
                });
              } else {
                showAutoFishPopup({
                  type: 'miss'
                });
              }
            case 10:
            case "end":
              return _context.stop();
          }
        }, _callee);
      }));
      return function tick() {
        return _ref8.apply(this, arguments);
      };
    }();
    tick();
    autoFishIntervalRef.current = setInterval(tick, 6000);
    return function () {
      return clearInterval(autoFishIntervalRef.current);
    };
  }, [autoFish, showAutoFishPopup]); // eslint-disable-line

  // Auto-cast: trigger cast when idle
  useEffect(function () {
    if (!autoCast || autoFish || phase !== 'idle') return;
    var t = setTimeout(function () {
      if (autoCastRef.current && !autoFishRef.current && phaseRef.current === 'idle') doCast();
    }, 600);
    return function () {
      return clearTimeout(t);
    };
  }, [phase, autoCast, autoFish]); // eslint-disable-line

  // Poll /api/bite-poll until bite detected or window expired.
  // Uses recursive setTimeout (not setInterval) so each poll fires 250ms
  // AFTER the previous fetch completes, keeping at most 1 request in-flight.
  // pollSessionRef is a cancellation token — incremented on each new cast so
  // any in-flight poll from the previous cast exits cleanly without affecting
  // the new session. try/catch ensures a network hiccup doesn't silently
  // break the chain and leave the phase stuck on 'waiting'.
  var startBitePolling = useCallback(function () {
    if (biteTimerRef.current) clearTimeout(biteTimerRef.current);
    var mySession = ++pollSessionRef.current;
    var poll = /*#__PURE__*/function () {
      var _ref9 = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee2() {
        var _yield$apiGame2, ok, data, now;
        return _regeneratorRuntime().wrap(function _callee2$(_context2) {
          while (1) switch (_context2.prev = _context2.next) {
            case 0:
              if (!(pollSessionRef.current !== mySession)) {
                _context2.next = 2;
                break;
              }
              return _context2.abrupt("return");
            case 2:
              _context2.prev = 2;
              _context2.next = 5;
              return apiGame('/api/bite-poll', {
                method: 'POST',
                body: '{}'
              });
            case 5:
              _yield$apiGame2 = _context2.sent;
              ok = _yield$apiGame2.ok;
              data = _yield$apiGame2.data;
              if (!(pollSessionRef.current !== mySession)) {
                _context2.next = 10;
                break;
              }
              return _context2.abrupt("return");
            case 10:
              if (!(phaseRef.current !== 'waiting')) {
                _context2.next = 12;
                break;
              }
              return _context2.abrupt("return");
            case 12:
              if (!ok) {
                _context2.next = 29;
                break;
              }
              if (!data.expired) {
                _context2.next = 21;
                break;
              }
              setMissReason('late');
              setPhase('miss');
              countMiss();
              setTimeout(function () {
                return setPhase('idle');
              }, 1500);
              return _context2.abrupt("return");
            case 21:
              if (!data.bite) {
                _context2.next = 29;
                break;
              }
              // Use remaining_ms from server to drive the bite bar animation.
              now = Date.now();
              setBiteAt(now);
              setExpiresAt(now + data.remaining_ms);
              setPhase('bite');
              if (missTimerRef.current) clearTimeout(missTimerRef.current);
              missTimerRef.current = setTimeout(function () {
                if (phaseRef.current === 'bite') {
                  setMissReason('late');
                  setPhase('miss');
                  countMiss();
                  setTimeout(function () {
                    return setPhase('idle');
                  }, 1500);
                }
              }, data.remaining_ms);
              return _context2.abrupt("return");
            case 29:
              _context2.next = 33;
              break;
            case 31:
              _context2.prev = 31;
              _context2.t0 = _context2["catch"](2);
            case 33:
              if (!(pollSessionRef.current !== mySession)) {
                _context2.next = 35;
                break;
              }
              return _context2.abrupt("return");
            case 35:
              biteTimerRef.current = setTimeout(poll, 250);
            case 36:
            case "end":
              return _context2.stop();
          }
        }, _callee2, null, [[2, 31]]);
      }));
      return function poll() {
        return _ref9.apply(this, arguments);
      };
    }();
    poll();
  }, [countMiss]); // eslint-disable-line

  var doCast = /*#__PURE__*/function () {
    var _ref0 = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee3() {
      var _yield$apiGame3, ok;
      return _regeneratorRuntime().wrap(function _callee3$(_context3) {
        while (1) switch (_context3.prev = _context3.next) {
          case 0:
            if (!(phaseRef.current !== 'idle')) {
              _context3.next = 2;
              break;
            }
            return _context3.abrupt("return");
          case 2:
            _context3.next = 4;
            return apiGame('/api/cast', {
              method: 'POST',
              body: '{}'
            });
          case 4:
            _yield$apiGame3 = _context3.sent;
            ok = _yield$apiGame3.ok;
            if (ok) {
              _context3.next = 8;
              break;
            }
            return _context3.abrupt("return");
          case 8:
            setBiteAt(null);
            setExpiresAt(null);
            setLastCatch(null);
            setMissReason('late');
            setPhase('waiting');
            if (biteTimerRef.current) clearTimeout(biteTimerRef.current);
            if (missTimerRef.current) clearTimeout(missTimerRef.current);
            startBitePolling();
          case 16:
          case "end":
            return _context3.stop();
        }
      }, _callee3);
    }));
    return function doCast() {
      return _ref0.apply(this, arguments);
    };
  }();
  var handleCast = useCallback(function () {
    if (phase !== 'idle') return;
    doCast();
  }, [phase]); // eslint-disable-line

  // Clicking the water area while waiting = reel too early → instant miss
  var handleEarlyReel = useCallback(function () {
    if (phaseRef.current !== 'waiting') return;
    if (biteTimerRef.current) {
      clearTimeout(biteTimerRef.current);
      biteTimerRef.current = null;
    }
    if (missTimerRef.current) {
      clearTimeout(missTimerRef.current);
      missTimerRef.current = null;
    }
    setMissReason('early');
    setPhase('miss');
    countMiss();
    // Tell server to clear the session (will return miss since before bite window)
    apiGame('/api/reel', {
      method: 'POST',
      body: '{}'
    });
    setTimeout(function () {
      return setPhase('idle');
    }, 1500);
  }, [countMiss]); // eslint-disable-line

  var handleReel = useCallback(/*#__PURE__*/_asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee4() {
    var _yield$apiGame4, ok, data, fish;
    return _regeneratorRuntime().wrap(function _callee4$(_context4) {
      while (1) switch (_context4.prev = _context4.next) {
        case 0:
          if (!(phase !== 'bite' || reelInFlightRef.current)) {
            _context4.next = 2;
            break;
          }
          return _context4.abrupt("return");
        case 2:
          reelInFlightRef.current = true;
          if (missTimerRef.current) {
            clearTimeout(missTimerRef.current);
            missTimerRef.current = null;
          }
          if (biteTimerRef.current) {
            clearTimeout(biteTimerRef.current);
            biteTimerRef.current = null;
          }
          setPhase('reeling');
          _context4.next = 8;
          return apiGame('/api/reel', {
            method: 'POST',
            body: '{}'
          });
        case 8:
          _yield$apiGame4 = _context4.sent;
          ok = _yield$apiGame4.ok;
          data = _yield$apiGame4.data;
          reelInFlightRef.current = false;
          if (ok) {
            _context4.next = 15;
            break;
          }
          setPhase('idle');
          return _context4.abrupt("return");
        case 15:
          if (data.result === 'hit') {
            consecutiveMissesRef.current = 0;
            fish = FISH_CATALOG_CLIENT.find(function (f) {
              return f.id === data.species;
            });
            setLastCatch({
              emoji: fish ? fish.emoji : '🐟',
              name: fish ? fish.name : data.species,
              value: data.value,
              isNew: !!data.first_catch,
              isLucky: data.species === 'lucky',
              doubled: !!data.was_doubled,
              preciseMult: data.precise_bonus ? data.precise_mult : null,
              precisePct: data.precise_pct != null ? data.precise_pct : null
            });
            onFishBucksUpdate(data.fish_clicks);
            if (data.first_catch) onCaughtSpeciesUpdate(data.species);
            setLuckyNextActive(!!data.lucky_next_active);
            setPhase('success');
            setTimeout(function () {
              return setPhase('idle');
            }, 2000);
          } else {
            setMissReason('late');
            setPhase('miss');
            countMiss();
            setTimeout(function () {
              return setPhase('idle');
            }, 1500);
          }
        case 16:
        case "end":
          return _context4.stop();
      }
    }, _callee4);
  })), [phase, countMiss]); // eslint-disable-line

  var biteWindowMs = expiresAt && biteAt ? expiresAt - biteAt : 1800;
  var inWater = phase === 'waiting' || phase === 'bite' || phase === 'reeling';
  return /*#__PURE__*/React.createElement("div", {
    className: "fishing-panel",
    style: {
      transform: "translateY(-50%) scale(".concat(scale, ")")
    },
    onClick: phase === 'bite' ? handleReel : undefined
  }, luckyNextActive && /*#__PURE__*/React.createElement("div", {
    className: "fishing-lucky-banner"
  }, "\u2B50 Next catch DOUBLED!"), /*#__PURE__*/React.createElement("div", {
    className: "fishing-fisher"
  }, /*#__PURE__*/React.createElement("span", {
    className: "fishing-fisher-emoji"
  }, fisherEmoji), /*#__PURE__*/React.createElement("span", {
    className: "fishing-rod"
  }, "\uD83C\uDFA3")), /*#__PURE__*/React.createElement("div", {
    className: "fishing-water",
    onClick: function onClick(e) {
      if (phaseRef.current === 'waiting') {
        e.stopPropagation();
        handleEarlyReel();
      }
    }
  }, (inWater || autoFish) && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("span", {
    className: "shadow-fish shadow-fish-1"
  }, "\uD83D\uDC1F"), /*#__PURE__*/React.createElement("span", {
    className: "shadow-fish shadow-fish-2"
  }, "\uD83D\uDC21"), /*#__PURE__*/React.createElement("span", {
    className: "shadow-fish shadow-fish-3"
  }, "\uD83D\uDC20")), autoFish && /*#__PURE__*/React.createElement("span", {
    className: "fishing-bobber bobber-idle"
  }, "\uD83E\uDD16"), !autoFish && inWater && /*#__PURE__*/React.createElement("span", {
    className: "fishing-bobber".concat(phase === 'bite' ? ' bobber-bite' : ' bobber-idle')
  }, "\uD83D\uDD34")), phase === 'bite' && /*#__PURE__*/React.createElement("div", {
    className: "bite-bar-container"
  }, /*#__PURE__*/React.createElement("div", {
    className: "bite-bar-fill",
    key: expiresAt,
    style: {
      animationDuration: "".concat(biteWindowMs, "ms")
    }
  })), phase === 'bite' && /*#__PURE__*/React.createElement("div", {
    className: "bite-hint"
  }, "CLICK TO REEL!"), phase === 'success' && lastCatch && /*#__PURE__*/React.createElement("div", {
    className: "catch-popup"
  }, /*#__PURE__*/React.createElement("span", {
    className: "catch-emoji"
  }, lastCatch.emoji), /*#__PURE__*/React.createElement("span", {
    className: "catch-value"
  }, "+", lastCatch.value, " \uD83D\uDC1F", lastCatch.doubled ? ' (2x!)' : '', lastCatch.preciseMult ? " \uD83C\uDFAF ".concat(lastCatch.preciseMult, "x @ ").concat(lastCatch.precisePct, "%") : ''), lastCatch.isNew && /*#__PURE__*/React.createElement("span", {
    className: "catch-new"
  }, "NEW!"), lastCatch.isLucky && /*#__PURE__*/React.createElement("span", {
    className: "catch-lucky"
  }, "\u2B50 Lucky!")), phase === 'miss' && /*#__PURE__*/React.createElement("div", {
    className: "catch-popup catch-popup--miss"
  }, missReason === 'early' ? 'Too early!' : 'Too slow!'), autoFish && autoFishPopup && (autoFishPopup.type === 'hit' ? /*#__PURE__*/React.createElement("div", {
    key: autoFishPopup.key,
    className: "catch-popup"
  }, /*#__PURE__*/React.createElement("span", {
    className: "catch-emoji"
  }, autoFishPopup.emoji), /*#__PURE__*/React.createElement("span", {
    className: "catch-value"
  }, "+", autoFishPopup.value, " \uD83D\uDC1F"), autoFishPopup.isNew && /*#__PURE__*/React.createElement("span", {
    className: "catch-new"
  }, "NEW!")) : /*#__PURE__*/React.createElement("div", {
    key: autoFishPopup.key,
    className: "catch-popup catch-popup--miss"
  }, "No bite")), /*#__PURE__*/React.createElement("div", {
    className: "fishing-controls"
  }, !autoFish && /*#__PURE__*/React.createElement("button", {
    className: "cast-btn",
    onClick: handleCast,
    disabled: phase !== 'idle'
  }, phase === 'idle' ? '🎣 CAST' : phase === 'waiting' ? 'Waiting…' : phase === 'bite' ? 'TAP!' : phase === 'reeling' ? 'Reeling…' : phase === 'success' ? '✓ Caught!' : 'Miss…'), /*#__PURE__*/React.createElement("div", {
    className: "fishing-toggles"
  }, hasAutoCast && !autoFish && /*#__PURE__*/React.createElement("label", {
    className: "fishing-toggle-label"
  }, /*#__PURE__*/React.createElement("input", {
    type: "checkbox",
    checked: autoCast,
    onChange: function onChange(e) {
      setAutoCast(e.target.checked);
      if (!e.target.checked) consecutiveMissesRef.current = 0;
    }
  }), /*#__PURE__*/React.createElement("span", {
    className: "fishing-toggle-text"
  }, "Auto-Cast")), hasAutoFisher && /*#__PURE__*/React.createElement("label", {
    className: "fishing-toggle-label"
  }, /*#__PURE__*/React.createElement("input", {
    type: "checkbox",
    checked: autoFish,
    onChange: function onChange(e) {
      setAutoFish(e.target.checked);
      if (e.target.checked) {
        setPhase('idle');
      }
    }
  }), /*#__PURE__*/React.createElement("span", {
    className: "fishing-toggle-text"
  }, "Auto-Fish")))), lastCatch && /*#__PURE__*/React.createElement("div", {
    className: "fishing-last-catch"
  }, "Last: ", lastCatch.emoji, " ", lastCatch.name, " +", lastCatch.value, " \uD83D\uDC1F", lastCatch.preciseMult ? " \uD83C\uDFAF ".concat(lastCatch.preciseMult, "x @ ").concat(lastCatch.precisePct, "%") : ''));
}

// ── Lucky Seven Counter ───────────────────────────────────────────────────
var LuckySevenCounter = React.memo(function LuckySevenCounter(_ref10) {
  var spinCount = _ref10.spinCount;
  var progress = spinCount % 7;
  return /*#__PURE__*/React.createElement("div", {
    className: "lucky-seven-counter"
  }, /*#__PURE__*/React.createElement("span", {
    className: "lucky-seven-counter-label"
  }, "7\uFE0F\u20E3"), [1, 2, 3, 4, 5, 6, 7].map(function (i) {
    return /*#__PURE__*/React.createElement("div", {
      key: i,
      className: "lucky-seven-pip".concat(i <= progress ? ' filled' : '').concat(i === 7 && progress === 0 && spinCount > 0 ? ' triggered' : '')
    });
  }));
});

// ── Streak Panel ──────────────────────────────────────────────────────────
// Must match models.py bonus_mult_from_level()
function bonusMultFromLevel(level) {
  var fixed = [1, 2, 5, 10, 20, 50, 100];
  if (level <= 6) return fixed[level] || 1;
  return 100 + (level - 6) * 10;
}
var StreakPanel = React.memo(function StreakPanel(_ref11) {
  var streak = _ref11.streak,
    bonusmultLevel = _ref11.bonusmultLevel;
  if (Math.abs(streak) < 2) return null;
  var isWin = streak > 0;
  var count = Math.abs(streak);
  // Season 6 formula — must match models.py streak_bonus()
  var baseBonus = count < 3 ? 0 : count <= 15 ? 1 << count - 3 : count <= 35 ? 4096 + Math.pow(count - 15, 3) * 2 : count <= 75 ? 20096 + (count - 35) * 1200 : count <= 150 ? 68096 + (count - 75) * 600 : 113096;
  var bonus = baseBonus * bonusMultFromLevel(bonusmultLevel || 0);
  return /*#__PURE__*/React.createElement("div", {
    className: "streak-panel ".concat(isWin ? 'win-streak' : 'lose-streak')
  }, /*#__PURE__*/React.createElement("span", {
    className: "streak-fire"
  }, isWin ? '🔥' : '💀'), /*#__PURE__*/React.createElement("span", {
    className: "streak-count"
  }, count, "x"), /*#__PURE__*/React.createElement("span", {
    className: "streak-label"
  }, isWin ? 'Win Streak' : 'Lose Streak'), bonus > 0 && /*#__PURE__*/React.createElement("span", {
    className: "streak-bonus"
  }, isWin ? "Bonus +".concat(fmt(bonus)) : "Penalty +".concat(fmt(bonus))));
});

// ── Dice Panel ───────────────────────────────────────────────────────────
var PIP_LAYOUTS = {
  1: [[2, 2]],
  2: [[1, 1], [3, 3]],
  3: [[1, 1], [2, 2], [3, 3]],
  4: [[1, 1], [1, 3], [3, 1], [3, 3]],
  5: [[1, 1], [1, 3], [2, 2], [3, 1], [3, 3]],
  6: [[1, 1], [1, 3], [2, 1], [2, 3], [3, 1], [3, 3]]
};
function Die(_ref12) {
  var value = _ref12.value,
    rolling = _ref12.rolling,
    landed = _ref12.landed;
  var pips = PIP_LAYOUTS[value] || [];
  var cls = "die".concat(rolling ? ' die-rolling' : '').concat(landed ? ' die-landed' : '');
  return /*#__PURE__*/React.createElement("div", {
    className: cls
  }, pips.map(function (_ref13, i) {
    var _ref14 = _slicedToArray(_ref13, 2),
      row = _ref14[0],
      col = _ref14[1];
    return /*#__PURE__*/React.createElement("div", {
      key: i,
      className: "pip",
      style: {
        gridRow: row,
        gridColumn: col
      }
    });
  }));
}
var DICE_TOOLTIP_W = 240;
var DICE_TOOLTIP_TEXT = 'Roll two dice to amplify your win streak. The sum (2–12) is added to your streak. Requires a win streak of 3 or more. ⚠️ Snake eyes (1+1) curses you — losing half your streak! Charges recharge every 10 minutes.';
function useDiceCountdown(diceLastRecharge, diceCharges, maxCharges) {
  var _React$useState = React.useState(null),
    _React$useState2 = _slicedToArray(_React$useState, 2),
    secsToNext = _React$useState2[0],
    setSecsToNext = _React$useState2[1];
  React.useEffect(function () {
    if (!diceLastRecharge || diceCharges >= maxCharges) {
      setSecsToNext(null);
      return;
    }
    var rechargeAt = new Date(diceLastRecharge).getTime() + 600 * 1000;
    var tick = function tick() {
      var secs = Math.max(0, Math.ceil((rechargeAt - Date.now()) / 1000));
      setSecsToNext(secs);
    };
    tick();
    var id = setInterval(tick, 1000);
    return function () {
      return clearInterval(id);
    };
  }, [diceLastRecharge, diceCharges, maxCharges]);
  return secsToNext;
}
function DicePanel(_ref15) {
  var streak = _ref15.streak,
    onRoll = _ref15.onRoll,
    rolling = _ref15.rolling,
    diceResult = _ref15.diceResult,
    spinning = _ref15.spinning,
    guardSpinning = _ref15.guardSpinning,
    lowSpec = _ref15.lowSpec,
    diceCharges = _ref15.diceCharges,
    maxDiceCharges = _ref15.maxDiceCharges,
    diceLastRecharge = _ref15.diceLastRecharge,
    hasDiceExtra = _ref15.hasDiceExtra,
    rolledSinceSpin = _ref15.rolledSinceSpin;
  var _React$useState3 = React.useState(1),
    _React$useState4 = _slicedToArray(_React$useState3, 2),
    animDie1 = _React$useState4[0],
    setAnimDie1 = _React$useState4[1];
  var _React$useState5 = React.useState(1),
    _React$useState6 = _slicedToArray(_React$useState5, 2),
    animDie2 = _React$useState6[0],
    setAnimDie2 = _React$useState6[1];
  var _React$useState7 = React.useState(1),
    _React$useState8 = _slicedToArray(_React$useState7, 2),
    animDie3 = _React$useState8[0],
    setAnimDie3 = _React$useState8[1];
  var _React$useState9 = React.useState(false),
    _React$useState0 = _slicedToArray(_React$useState9, 2),
    landed = _React$useState0[0],
    setLanded = _React$useState0[1];
  var _React$useState1 = React.useState(false),
    _React$useState10 = _slicedToArray(_React$useState1, 2),
    showResult = _React$useState10[0],
    setShowResult = _React$useState10[1];
  var _React$useState11 = React.useState(false),
    _React$useState12 = _slicedToArray(_React$useState11, 2),
    tipVisible = _React$useState12[0],
    setTipVisible = _React$useState12[1];
  var _React$useState13 = React.useState({
      left: 0,
      bottom: 0
    }),
    _React$useState14 = _slicedToArray(_React$useState13, 2),
    tipPos = _React$useState14[0],
    setTipPos = _React$useState14[1];
  var intervalRef = React.useRef(null);
  var descRef = React.useRef(null);
  var secsToNext = useDiceCountdown(diceLastRecharge, diceCharges, maxDiceCharges);
  React.useEffect(function () {
    if (rolling && !lowSpec) {
      setLanded(false);
      setShowResult(false);
      intervalRef.current = setInterval(function () {
        setAnimDie1(Math.ceil(Math.random() * 6));
        setAnimDie2(Math.ceil(Math.random() * 6));
        setAnimDie3(Math.ceil(Math.random() * 6));
      }, 80);
    } else {
      clearInterval(intervalRef.current);
    }
    return function () {
      return clearInterval(intervalRef.current);
    };
  }, [rolling, lowSpec]);
  React.useEffect(function () {
    if (diceResult) {
      setAnimDie1(diceResult.die1);
      setAnimDie2(diceResult.die2);
      if (diceResult.die3 != null) setAnimDie3(diceResult.die3);
      setLanded(true);
      setShowResult(true);
      var t = setTimeout(function () {
        setShowResult(false);
        setLanded(false);
      }, 3000);
      return function () {
        return clearTimeout(t);
      };
    }
  }, [diceResult]);
  var canRoll = diceCharges >= 1 && streak >= 3 && !rolling && !spinning && !guardSpinning && !rolledSinceSpin;
  var die1Val = rolling && !lowSpec ? animDie1 : diceResult ? diceResult.die1 : animDie1;
  var die2Val = rolling && !lowSpec ? animDie2 : diceResult ? diceResult.die2 : animDie2;
  var die3Val = rolling && !lowSpec ? animDie3 : diceResult && diceResult.die3 != null ? diceResult.die3 : animDie3;
  var showTip = function showTip() {
    if (spinning || guardSpinning) return;
    var rect = descRef.current && descRef.current.getBoundingClientRect();
    if (!rect) return;
    var left = rect.left + rect.width / 2 - DICE_TOOLTIP_W / 2;
    left = Math.max(8, Math.min(left, window.innerWidth - DICE_TOOLTIP_W - 8));
    setTipPos({
      left: left,
      bottom: window.innerHeight - rect.top + 6
    });
    setTipVisible(true);
  };
  var fmtCountdownSecs = function fmtCountdownSecs(s) {
    if (s == null) return '';
    var m = Math.floor(s / 60);
    var sec = s % 60;
    return "".concat(m, ":").concat(String(sec).padStart(2, '0'));
  };
  var chargesDots = Array.from({
    length: maxDiceCharges
  }, function (_, i) {
    return /*#__PURE__*/React.createElement("span", {
      key: i,
      className: "dice-charge-dot".concat(i < diceCharges ? ' charged' : '')
    }, "\u25CF");
  });
  var disabledReason = '';
  if (diceCharges < 1) disabledReason = 'No charges';else if (streak < 3) disabledReason = 'Need win streak ≥3';else if (rolledSinceSpin) disabledReason = 'Spin once before rolling again';
  return /*#__PURE__*/React.createElement("div", {
    className: "dice-panel"
  }, /*#__PURE__*/React.createElement("span", {
    className: "dice-panel-label"
  }, "\uD83C\uDFB2 Dice Roll"), /*#__PURE__*/React.createElement("span", {
    className: "dice-panel-desc",
    ref: descRef,
    onMouseEnter: showTip,
    onMouseLeave: function onMouseLeave() {
      return setTipVisible(false);
    }
  }, "How it works \u24D8"), tipVisible && /*#__PURE__*/React.createElement("div", {
    className: "dice-tooltip",
    style: {
      left: tipPos.left,
      bottom: tipPos.bottom
    }
  }, DICE_TOOLTIP_TEXT), /*#__PURE__*/React.createElement("div", {
    className: "dice-charges-row"
  }, chargesDots, secsToNext != null && diceCharges < maxDiceCharges && /*#__PURE__*/React.createElement("span", {
    className: "dice-recharge-timer"
  }, "+1 in ", fmtCountdownSecs(secsToNext))), hasDiceExtra ? /*#__PURE__*/React.createElement("div", {
    className: "dice-triangle"
  }, /*#__PURE__*/React.createElement("div", {
    className: "dice-row dice-row-top"
  }, /*#__PURE__*/React.createElement(Die, {
    value: die3Val,
    rolling: rolling && !lowSpec,
    landed: landed
  })), /*#__PURE__*/React.createElement("div", {
    className: "dice-row"
  }, /*#__PURE__*/React.createElement(Die, {
    value: die1Val,
    rolling: rolling && !lowSpec,
    landed: landed
  }), /*#__PURE__*/React.createElement(Die, {
    value: die2Val,
    rolling: rolling && !lowSpec,
    landed: landed
  }))) : /*#__PURE__*/React.createElement("div", {
    className: "dice-row"
  }, /*#__PURE__*/React.createElement(Die, {
    value: die1Val,
    rolling: rolling && !lowSpec,
    landed: landed
  }), /*#__PURE__*/React.createElement(Die, {
    value: die2Val,
    rolling: rolling && !lowSpec,
    landed: landed
  })), showResult && diceResult && /*#__PURE__*/React.createElement("span", {
    className: "dice-result-text".concat(diceResult.cursed ? ' dice-cursed' : '')
  }, diceResult.cursed_triple ? "\uD83D\uDC80 TRIPLE CURSE! Streak \xF73" : diceResult.blessed_triple ? "\uD83C\uDF1F TRIPLE BLESSED! Streak \xD73!" : diceResult.cursed ? "\uD83D\uDC80 CURSED! Streak -".concat(diceResult.streak_before - diceResult.streak_after) : "+".concat(diceResult.streak_delta, " streak!")), /*#__PURE__*/React.createElement("button", {
    className: "dice-roll-btn".concat(canRoll ? '' : ' dice-roll-btn--disabled'),
    onClick: canRoll ? onRoll : undefined,
    disabled: !canRoll,
    title: canRoll ? 'Roll the dice!' : disabledReason
  }, rolling ? 'Rolling…' : "Roll (".concat(diceCharges, "/").concat(maxDiceCharges, " charges)")));
}

// ── Season Winners ────────────────────────────────────────────────────────
function SeasonWinners(_ref16) {
  var winners = _ref16.winners,
    seasonNumber = _ref16.seasonNumber,
    _ref16$extraClass = _ref16.extraClass,
    extraClass = _ref16$extraClass === void 0 ? '' : _ref16$extraClass;
  if (!winners || winners.length === 0) return null;
  var medals = ['🥇', '🥈', '🥉'];
  var rankClasses = ['sw-gold', 'sw-silver', 'sw-bronze', 'sw-4th', 'sw-5th'];
  return /*#__PURE__*/React.createElement("div", {
    className: "season-winners".concat(extraClass ? ' ' + extraClass : '')
  }, /*#__PURE__*/React.createElement("div", {
    className: "season-winners-title"
  }, "Season ", seasonNumber, " Winners"), winners.map(function (w) {
    return /*#__PURE__*/React.createElement("div", {
      key: w.position,
      className: "season-winner-row ".concat(rankClasses[w.position - 1] || '')
    }, /*#__PURE__*/React.createElement("span", {
      className: "sw-medal"
    }, medals[w.position - 1] || w.position), /*#__PURE__*/React.createElement("span", {
      className: "sw-name"
    }, w.username), /*#__PURE__*/React.createElement("span", {
      className: "sw-wins"
    }, fmt(w.wins), "W"));
  }));
}

// ── Season Info ───────────────────────────────────────────────────────────
function SeasonInfo(_ref17) {
  var seasonNumber = _ref17.seasonNumber,
    endsAt = _ref17.endsAt;
  var _useState23 = useState(''),
    _useState24 = _slicedToArray(_useState23, 2),
    timeLeft = _useState24[0],
    setTimeLeft = _useState24[1];
  useEffect(function () {
    if (!endsAt) return;
    var update = function update() {
      var diff = new Date(endsAt) - new Date();
      if (diff <= 0) {
        setTimeLeft('Ending...');
        return;
      }
      var d = Math.floor(diff / 86400000);
      var h = Math.floor(diff % 86400000 / 3600000);
      var m = Math.floor(diff % 3600000 / 60000);
      setTimeLeft(d > 0 ? "".concat(d, "d ").concat(h, "h ").concat(m, "m") : h > 0 ? "".concat(h, "h ").concat(m, "m") : "".concat(m, "m"));
    };
    update();
    var id = setInterval(update, 60000);
    return function () {
      return clearInterval(id);
    };
  }, [endsAt]);
  return /*#__PURE__*/React.createElement("div", {
    className: "season-info"
  }, /*#__PURE__*/React.createElement("span", null, "Season ", seasonNumber, " ends:"), timeLeft && /*#__PURE__*/React.createElement("span", {
    className: "season-countdown"
  }, timeLeft));
}

// ── Leaderboard ───────────────────────────────────────────────────────────
function Leaderboard(_ref18) {
  var currentUser = _ref18.currentUser,
    extraClass = _ref18.extraClass,
    seasonWinners = _ref18.seasonWinners,
    seasonNumber = _ref18.seasonNumber;
  var _useState25 = useState([]),
    _useState26 = _slicedToArray(_useState25, 2),
    rows = _useState26[0],
    setRows = _useState26[1];
  var _useState27 = useState('players'),
    _useState28 = _slicedToArray(_useState27, 2),
    tab = _useState28[0],
    setTab = _useState28[1];
  useEffect(function () {
    var ctrl = new AbortController();
    var load = function load() {
      ctrl.abort();
      ctrl = new AbortController();
      apiFetch('/api/leaderboard', {
        signal: ctrl.signal
      }).then(function (r) {
        if (r.ok) setRows(r.data);
      })["catch"](function () {});
    };
    load();
    var id = setInterval(load, 15000);
    return function () {
      clearInterval(id);
      ctrl.abort();
    };
  }, []);
  if (rows.length === 0) return null;
  var rankClass = function rankClass(i) {
    return i === 0 ? 'gold' : i === 1 ? 'silver' : i === 2 ? 'bronze' : '';
  };
  var infernoClass = function infernoClass(streak) {
    return streak > 0 ? "streak-inferno-".concat(Math.min(streak, 10)) : '';
  };
  var medals = ['🥇', '🥈', '🥉'];
  var rankClasses = ['sw-gold', 'sw-silver', 'sw-bronze', 'sw-4th', 'sw-5th'];
  return /*#__PURE__*/React.createElement("div", {
    className: "leaderboard-panel".concat(extraClass ? ' ' + extraClass : '')
  }, /*#__PURE__*/React.createElement("div", {
    className: "leaderboard-tabs"
  }, /*#__PURE__*/React.createElement("button", {
    className: "leaderboard-tab".concat(tab === 'players' ? ' active' : ''),
    onClick: function onClick() {
      return setTab('players');
    }
  }, "Top Players"), /*#__PURE__*/React.createElement("button", {
    className: "leaderboard-tab".concat(tab === 'winners' ? ' active' : ''),
    onClick: function onClick() {
      return setTab('winners');
    }
  }, "Past Winners")), tab === 'players' && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    className: "lb-header"
  }, /*#__PURE__*/React.createElement("span", {
    className: "lb-rank-h"
  }), /*#__PURE__*/React.createElement("span", {
    className: "lb-name-h"
  }, "Player"), /*#__PURE__*/React.createElement("span", {
    className: "lb-wins-h"
  }, "W"), /*#__PURE__*/React.createElement("span", {
    className: "lb-best-h"
  }, "Best"), /*#__PURE__*/React.createElement("span", {
    className: "lb-streak-h"
  }, "Now")), rows.map(function (r, i) {
    return /*#__PURE__*/React.createElement("div", {
      key: r.username,
      className: "lb-row"
    }, /*#__PURE__*/React.createElement("span", {
      className: "lb-rank ".concat(rankClass(i))
    }, i + 1, "."), /*#__PURE__*/React.createElement("span", {
      className: "lb-name ".concat(r.username === currentUser ? 'is-you' : '')
    }, r.username), /*#__PURE__*/React.createElement("span", {
      className: "lb-wins"
    }, fmt(r.wins)), /*#__PURE__*/React.createElement("span", {
      className: "lb-best"
    }, r.best_streak > 0 ? "".concat(r.best_streak, "\uD83D\uDD25") : '—'), /*#__PURE__*/React.createElement("span", {
      className: "lb-streak ".concat(infernoClass(r.streak))
    }, r.streak > 0 ? "".concat(r.streak, "\uD83D\uDD25") : r.streak < 0 ? "".concat(r.streak, "\uD83D\uDC80") : '0'));
  })), tab === 'winners' && /*#__PURE__*/React.createElement("div", {
    className: "lb-winners-tab"
  }, seasonWinners && seasonWinners.length > 0 ? /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    className: "lb-winners-title"
  }, "Season ", seasonNumber, " Winners"), seasonWinners.map(function (w) {
    return /*#__PURE__*/React.createElement("div", {
      key: w.position,
      className: "season-winner-row ".concat(rankClasses[w.position - 1] || '')
    }, /*#__PURE__*/React.createElement("span", {
      className: "sw-medal"
    }, medals[w.position - 1] || w.position), /*#__PURE__*/React.createElement("span", {
      className: "sw-name"
    }, w.username), /*#__PURE__*/React.createElement("span", {
      className: "sw-wins"
    }, fmt(w.wins), "W"));
  })) : /*#__PURE__*/React.createElement("div", {
    className: "lb-winners-empty"
  }, "No season winners yet.")));
}

// ── Chat Panel ────────────────────────────────────────────────────────────
function fmtChatTime(iso) {
  var d = new Date(iso);
  var h = d.getHours();
  var m = String(d.getMinutes()).padStart(2, '0');
  var ampm = h >= 12 ? 'pm' : 'am';
  h = h % 12 || 12;
  return "".concat(h, ":").concat(m).concat(ampm);
}
var CHAT_DEFAULT_SIZE = {
  w: 231,
  h: 224
};
var CHAT_MIN_W = 180,
  CHAT_MIN_H = 150,
  CHAT_MAX_W = 620,
  CHAT_MAX_H = 620;
function ChatPanel(_ref19) {
  var _ref19$extraClass = _ref19.extraClass,
    extraClass = _ref19$extraClass === void 0 ? '' : _ref19$extraClass,
    onClose = _ref19.onClose;
  var _useState29 = useState([]),
    _useState30 = _slicedToArray(_useState29, 2),
    messages = _useState30[0],
    setMessages = _useState30[1];
  var _useState31 = useState(''),
    _useState32 = _slicedToArray(_useState31, 2),
    input = _useState32[0],
    setInput = _useState32[1];
  var _useState33 = useState(''),
    _useState34 = _slicedToArray(_useState33, 2),
    error = _useState34[0],
    setError = _useState34[1];
  var _useState35 = useState(0),
    _useState36 = _slicedToArray(_useState35, 2),
    timeoutSecs = _useState36[0],
    setTimeoutSecs = _useState36[1];
  var _useState37 = useState(function () {
      try {
        var s = JSON.parse(localStorage.getItem('chat_panel_size'));
        if (s && s.w >= CHAT_MIN_W && s.h >= CHAT_MIN_H) return s;
      } catch (_unused) {}
      return CHAT_DEFAULT_SIZE;
    }),
    _useState38 = _slicedToArray(_useState37, 2),
    size = _useState38[0],
    setSize = _useState38[1];
  var panelRef = useRef(null);
  var messagesEndRef = useRef(null);
  var scrollRef = useRef(null);
  var atBottomRef = useRef(true);
  var timeoutTimerRef = useRef(null);

  // Persist size to localStorage whenever it changes (covers drag, close/reopen, refresh)
  useEffect(function () {
    localStorage.setItem('chat_panel_size', JSON.stringify(size));
  }, [size]);
  var onResizeMouseDown = useCallback(function (e) {
    e.preventDefault();
    var rect = panelRef.current ? panelRef.current.getBoundingClientRect() : CHAT_DEFAULT_SIZE;
    var startW = rect.width,
      startH = rect.height;
    var startX = e.clientX,
      startY = e.clientY;
    var onMove = function onMove(ev) {
      var newW = Math.min(CHAT_MAX_W, Math.max(CHAT_MIN_W, startW + (ev.clientX - startX)));
      var newH = Math.min(CHAT_MAX_H, Math.max(CHAT_MIN_H, startH + (ev.clientY - startY)));
      setSize({
        w: newW,
        h: newH
      });
    };
    var onUp = function onUp() {
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);
    };
    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
  }, []);

  // Poll for new messages
  useEffect(function () {
    var ctrl = new AbortController();
    var load = function load() {
      ctrl.abort();
      ctrl = new AbortController();
      apiFetch('/api/chat', {
        signal: ctrl.signal
      }).then(function (r) {
        if (r.ok) setMessages(r.data);
      })["catch"](function () {});
    };
    load();
    var id = setInterval(load, 5000);
    return function () {
      clearInterval(id);
      ctrl.abort();
    };
  }, []);

  // Auto-scroll only if at bottom
  useEffect(function () {
    if (atBottomRef.current && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({
        behavior: 'smooth'
      });
    }
  }, [messages]);

  // Countdown timer for timeout feedback
  useEffect(function () {
    if (timeoutSecs <= 0) return;
    clearInterval(timeoutTimerRef.current);
    timeoutTimerRef.current = setInterval(function () {
      setTimeoutSecs(function (s) {
        if (s <= 1) {
          clearInterval(timeoutTimerRef.current);
          return 0;
        }
        return s - 1;
      });
    }, 1000);
    return function () {
      return clearInterval(timeoutTimerRef.current);
    };
  }, [timeoutSecs]);
  var handleScroll = function handleScroll() {
    var el = scrollRef.current;
    if (!el) return;
    atBottomRef.current = el.scrollHeight - el.scrollTop - el.clientHeight < 40;
  };
  var sendMessage = /*#__PURE__*/function () {
    var _ref20 = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee5() {
      var text, r, secs;
      return _regeneratorRuntime().wrap(function _callee5$(_context5) {
        while (1) switch (_context5.prev = _context5.next) {
          case 0:
            text = input.trim();
            if (text) {
              _context5.next = 3;
              break;
            }
            return _context5.abrupt("return");
          case 3:
            setError('');
            _context5.next = 6;
            return apiGame('/api/chat', {
              method: 'POST',
              body: JSON.stringify({
                message: text
              })
            });
          case 6:
            r = _context5.sent;
            if (r.ok) {
              setInput('');
              // Immediately reload
              apiFetch('/api/chat').then(function (res) {
                if (res.ok) setMessages(res.data);
              })["catch"](function () {});
            } else if (r.status === 429) {
              secs = r.data.seconds_remaining || 60;
              setTimeoutSecs(secs);
              setError("Timed out. Wait ".concat(secs, "s."));
            } else {
              setError(r.data.error || 'Failed to send');
            }
          case 8:
          case "end":
            return _context5.stop();
        }
      }, _callee5);
    }));
    return function sendMessage() {
      return _ref20.apply(this, arguments);
    };
  }();
  var handleKeyDown = function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };
  var isDisabled = timeoutSecs > 0;
  var panelStyle = extraClass === 'mobile-full' ? {} : {
    width: size.w,
    height: size.h
  };
  return /*#__PURE__*/React.createElement("div", {
    ref: panelRef,
    className: "chat-panel".concat(extraClass ? ' ' + extraClass : ''),
    style: panelStyle
  }, /*#__PURE__*/React.createElement("div", {
    className: "chat-panel-header"
  }, /*#__PURE__*/React.createElement("div", {
    className: "chat-panel-title"
  }, "\uD83D\uDCAC Chat"), onClose && /*#__PURE__*/React.createElement("button", {
    className: "chat-close-btn",
    onClick: onClose,
    title: "Close Chat"
  }, "\u2715")), /*#__PURE__*/React.createElement("div", {
    className: "chat-messages",
    ref: scrollRef,
    onScroll: handleScroll
  }, messages.map(function (m) {
    return /*#__PURE__*/React.createElement("div", {
      key: m.id,
      className: "chat-msg"
    }, m.created_at && /*#__PURE__*/React.createElement("span", {
      className: "chat-msg-time"
    }, fmtChatTime(m.created_at)), /*#__PURE__*/React.createElement("span", {
      className: "chat-msg-name"
    }, m.username, ": "), /*#__PURE__*/React.createElement("span", {
      className: "chat-msg-text"
    }, m.message));
  }), /*#__PURE__*/React.createElement("div", {
    ref: messagesEndRef
  })), error && /*#__PURE__*/React.createElement("div", {
    className: "chat-error"
  }, error), /*#__PURE__*/React.createElement("div", {
    className: "chat-input-row"
  }, /*#__PURE__*/React.createElement("input", {
    className: "chat-input",
    type: "text",
    placeholder: isDisabled ? "Wait ".concat(timeoutSecs, "s\u2026") : 'Message…',
    value: input,
    onChange: function onChange(e) {
      return setInput(e.target.value);
    },
    onKeyDown: handleKeyDown,
    disabled: isDisabled,
    maxLength: 200
  }), /*#__PURE__*/React.createElement("button", {
    className: "chat-send-btn",
    onClick: sendMessage,
    disabled: isDisabled
  }, "\u2191")), extraClass !== 'mobile-full' && /*#__PURE__*/React.createElement("div", {
    className: "chat-resize-handle",
    onMouseDown: onResizeMouseDown,
    title: "Drag to resize"
  }));
}

// ── Shop catalogue ────────────────────────────────────────────────────────
var FISH_SKINS = [{
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
}, {
  id: 'fish_squid',
  emoji: '🦑',
  name: 'Squid',
  cost: 200,
  labels: {
    idle: 'Ink at the ready',
    happy: 'Jet-propelled win!',
    sad: '*squirts ink cloud*'
  }
}, {
  id: 'fish_turtle',
  emoji: '🐢',
  name: 'Turtle',
  cost: 350,
  labels: {
    idle: 'Slow and steady',
    happy: 'Shell yeah!',
    sad: 'Into my shell...'
  }
}, {
  id: 'fish_crab',
  emoji: '🦀',
  name: 'Crab',
  cost: 600,
  labels: {
    idle: '*snaps claws*',
    happy: 'CRABULOUS!',
    sad: 'Crabby mood...'
  }
}, {
  id: 'fish_lobster',
  emoji: '🦞',
  name: 'Lobster',
  cost: 1000,
  labels: {
    idle: 'Feeling boujee',
    happy: 'CLAWSOME WIN!',
    sad: 'Shellshocked...'
  }
}, {
  id: 'fish_whale',
  emoji: '🐋',
  name: 'Whale',
  cost: 2000,
  labels: {
    idle: 'Making waves',
    happy: 'WHALE of a win!',
    sad: 'Beached...'
  }
}, {
  id: 'fish_seal',
  emoji: '🦭',
  name: 'Seal',
  cost: 3500,
  labels: {
    idle: '*claps flippers*',
    happy: 'ARF ARF ARF!',
    sad: '*sad honk*'
  }
}, {
  id: 'fish_shrimp',
  emoji: '🦐',
  name: 'Shrimp',
  cost: 6000,
  labels: {
    idle: 'Small but mighty',
    happy: 'Prawn to win!',
    sad: 'De-veined...'
  }
}, {
  id: 'fish_coral',
  emoji: '🪸',
  name: 'Coral',
  cost: 10000,
  labels: {
    idle: 'Growing strong',
    happy: 'Reef royalty!',
    sad: 'Bleached out...'
  }
}, {
  id: 'fish_mermaid',
  emoji: '🧜',
  name: 'Mermaid',
  cost: 17500,
  labels: {
    idle: 'Under the sea~',
    happy: 'Mythic win!',
    sad: 'Into the deep...'
  }
}, {
  id: 'fish_croc',
  emoji: '🐊',
  name: 'Crocodile',
  cost: 30000,
  labels: {
    idle: '*death roll ready*',
    happy: 'SNAPPED IT!',
    sad: 'Sunk to the bottom...'
  }
}];
var SHOP_SECTIONS = [{
  label: '⚡ Spin Speed',
  items: [{
    id: 'speed_boost',
    emoji: '⚡',
    name: 'Speed Boost',
    cost: 100,
    desc: 'Spin time: 4.5s → 3s'
  }, {
    id: 'turbo_spin',
    emoji: '🚀',
    name: 'Turbo Spin',
    cost: 1000,
    desc: 'Spin time: 3s → 1.5s',
    requires: 'speed_boost'
  }, {
    id: 'hyperspin',
    emoji: '💨',
    name: 'Hyper Spin',
    cost: 10000,
    desc: 'Spin time: 1.5s → 1s',
    requires: 'turbo_spin'
  }, {
    id: 'ultraspin',
    emoji: '🌀',
    name: 'Ultra Spin',
    cost: 100000,
    desc: 'Spin time: 1s → 0.75s',
    requires: 'hyperspin'
  }, {
    id: 'maxspin',
    emoji: '⚡',
    name: 'Max Spin',
    cost: 1000000,
    desc: 'Spin time: 0.75s → 0.5s',
    requires: 'ultraspin'
  }]
}, {
  label: '⏩ Auto Speed',
  items: [{
    id: 'autospeed_1',
    emoji: '⏩',
    name: 'Quick Auto',
    cost: 200,
    desc: 'Auto delay: 1.5s → 1s'
  }, {
    id: 'autospeed_2',
    emoji: '⏩',
    name: 'Rapid Auto',
    cost: 10000,
    desc: 'Auto delay: 1s → 0.5s',
    requires: 'autospeed_1'
  }, {
    id: 'autospeed_3',
    emoji: '⏩',
    name: 'Instant Auto',
    cost: 1000000,
    desc: 'Auto delay: 0.5s → 0',
    requires: 'autospeed_2'
  }]
}, {
  label: '💰 Win Power',
  items: [{
    id: 'winmult_inf',
    emoji: '💰',
    name: 'Win Power',
    cost: 0,
    desc: 'Multiplies each win score',
    infinite: true
  }]
}, {
  label: '⭐ Bonus Power',
  items: [{
    id: 'bonusmult_inf',
    emoji: '⭐',
    name: 'Bonus Power',
    cost: 0,
    desc: 'Multiplies streak bonuses — ⚠️ also amplifies loss streaks',
    infinite: true
  }]
}, {
  label: '🐟 Fishing Panel Size',
  items: [{
    id: 'fishsize_small',
    emoji: '🔍',
    name: 'Compact',
    cost: 1,
    desc: 'Fishing panel: 50% size (compact mode)'
  }, {
    id: 'fishsize_1',
    emoji: '🔎',
    name: 'Big Panel',
    cost: 1,
    desc: 'Fishing panel: 130% size'
  }, {
    id: 'fishsize_2',
    emoji: '🔎',
    name: 'Giant Panel',
    cost: 1,
    desc: 'Fishing panel: 160% size',
    requires: 'fishsize_1'
  }, {
    id: 'fishsize_3',
    emoji: '🔎',
    name: 'Colossal',
    cost: 1,
    desc: 'Fishing panel: 200% size',
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
  }, {
    id: 'trail_4',
    emoji: '❄️',
    name: 'Frost Trail',
    cost: 7000,
    desc: 'Ice crystal aura',
    requires: 'trail_3'
  }, {
    id: 'trail_5',
    emoji: '⚡',
    name: 'Thunder Trail',
    cost: 22000,
    desc: 'Electric storm aura',
    requires: 'trail_4'
  }, {
    id: 'trail_6',
    emoji: '🌌',
    name: 'Galaxy Trail',
    cost: 70000,
    desc: 'Cosmic void aura',
    requires: 'trail_5'
  }]
}, {
  label: '🎣 Fishing Gear',
  items: [{
    id: 'lure_1',
    emoji: '🎣',
    name: 'Lure I',
    cost: 100,
    desc: '10% faster bite times + 1.5× catch value'
  }, {
    id: 'lure_2',
    emoji: '🎣',
    name: 'Lure II',
    cost: 500,
    desc: '20% faster bite times + 2× catch value',
    requires: 'lure_1'
  }, {
    id: 'lure_3',
    emoji: '🎣',
    name: 'Lure III',
    cost: 2500,
    desc: '35% faster bite times + 5× catch value',
    requires: 'lure_2'
  }, {
    id: 'lure_4',
    emoji: '🎣',
    name: 'Lure IV',
    cost: 15000,
    desc: '50% faster bite times + 10× catch value',
    requires: 'lure_3'
  }, {
    id: 'lure_5',
    emoji: '⭐',
    name: 'Master Lure',
    cost: 500000,
    desc: '65% faster bite times + 20× catch value + +1% chance per legendary species — requires complete Encyclopaedia',
    requires: 'lure_4',
    encyclopaediaLocked: true
  }, {
    id: 'auto_cast',
    emoji: '⏭️',
    name: 'Auto-Cast',
    cost: 1000,
    desc: 'Auto-casts line when idle — you still tap the bite window'
  }, {
    id: 'autofisher_1',
    emoji: '🤖',
    name: 'Auto-Fisher I',
    cost: 300,
    desc: 'Automated fishing at 45% catch rate — common & uncommon only'
  }, {
    id: 'autofisher_2',
    emoji: '🤖',
    name: 'Auto-Fisher II',
    cost: 2000,
    desc: 'Auto-Fisher catch rate: 55% — common & uncommon only',
    requires: 'autofisher_1'
  }, {
    id: 'autofisher_3',
    emoji: '🤖',
    name: 'Auto-Fisher III',
    cost: 12000,
    desc: 'Auto-Fisher catch rate: 65% — common & uncommon only',
    requires: 'autofisher_2'
  }, {
    id: 'autofisher_4',
    emoji: '🤖',
    name: 'Master Auto-Fisher',
    cost: 500000,
    desc: 'Auto-Fisher catch rate: 75% — now catches rare species too — requires complete Encyclopaedia',
    requires: 'autofisher_3',
    encyclopaediaLocked: true
  }, {
    id: 'precise_angler_1',
    emoji: '🎯',
    name: 'Precise Angler',
    cost: 50000,
    desc: 'Reel within the first 50% of the bite window for 1.2× catch value',
    tier: 2
  }, {
    id: 'precise_angler_2',
    emoji: '🎯',
    name: 'Precise Angler II',
    cost: 100000,
    desc: 'Also: reel within the first 20% for 1.5× catch value',
    requires: 'precise_angler_1'
  }, {
    id: 'precise_angler_3',
    emoji: '🎯',
    name: 'Master Angler',
    cost: 500000,
    desc: 'Also: reel within the first 15% for 2× catch value — requires complete Encyclopaedia',
    requires: 'precise_angler_2',
    encyclopaediaLocked: true
  }]
}, {
  label: '🛡️ Protection',
  items: [{
    id: 'guard',
    emoji: '🛡️',
    name: 'Guard',
    cost: 500,
    desc: '50% chance to block any loss. Breaks on success, survives on failure.'
  }, {
    id: 'auto_guard',
    emoji: '🔁',
    name: 'Auto-Guard',
    cost: 50000,
    desc: 'Automatically re-buys a Guard for 500 Wins when one breaks. Toggle to enable/disable.',
    requires: 'guard',
    tier: 2
  }, {
    id: 'regen_shield',
    emoji: '🔄',
    name: 'Regenerating Shield',
    cost: 1500,
    desc: 'Blocks any loss when charged. Recharges after 5 wins. Never breaks.',
    tier: 2
  }, {
    id: 'guard_speed_1',
    emoji: '⚡',
    name: 'Guard Speed I',
    cost: 2000,
    desc: 'Guard activates 25% faster.',
    requires: 'guard'
  }, {
    id: 'guard_speed_2',
    emoji: '⚡',
    name: 'Guard Speed II',
    cost: 8000,
    desc: 'Guard activates 50% faster.',
    requires: 'guard_speed_1'
  }, {
    id: 'guard_speed_3',
    emoji: '⚡',
    name: 'Guard Speed III',
    cost: 30000,
    desc: 'Guard activates 65% faster.',
    requires: 'guard_speed_2'
  }, {
    id: 'guard_speed_4',
    emoji: '⚡',
    name: 'Guard Speed MAX',
    cost: 100000,
    desc: 'Guard activates 75% faster — near instant.',
    requires: 'guard_speed_3'
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
    id: 'theme_void',
    emoji: '🌑',
    name: 'Void Theme',
    cost: 12000,
    desc: 'Dark matter wheel',
    requires: 'theme_neon'
  }, {
    id: 'theme_gold',
    emoji: '🟡',
    name: 'Gold Theme',
    cost: 40000,
    desc: 'Pure gold wheel',
    requires: 'theme_void'
  }, {
    id: 'golden_wheel',
    emoji: '✨',
    name: 'Golden Wheel',
    cost: 300,
    desc: 'Radiant glow ring'
  }]
}, {
  label: '🎊 Confetti',
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
  }]
}, {
  label: '🎨 Atmosphere',
  items: [{
    id: 'bg_royal',
    emoji: '💜',
    name: 'Royal Casino',
    cost: 400,
    desc: 'Purple atmosphere'
  }, {
    id: 'bg_inferno',
    emoji: '❤️',
    name: 'Inferno Casino',
    cost: 1600,
    desc: 'Blood red atmosphere',
    requires: 'bg_royal'
  }, {
    id: 'bg_forest',
    emoji: '🌿',
    name: 'Enchanted Forest',
    cost: 5000,
    desc: 'Mystical green depths',
    requires: 'bg_inferno'
  }, {
    id: 'bg_abyss',
    emoji: '🌑',
    name: 'The Abyss',
    cost: 15000,
    desc: 'Void of darkness',
    requires: 'bg_forest'
  }, {
    id: 'bg_cosmic',
    emoji: '🌌',
    name: 'Cosmic Casino',
    cost: 50000,
    desc: 'Deep space nebula',
    requires: 'bg_abyss'
  }]
}, {
  label: '🖼️ Page Theme',
  items: [{
    id: 'page_season1',
    emoji: '🌟',
    name: 'Season 1 Theme',
    cost: 1000,
    desc: 'Classic gold & orange casino theme (S1).'
  }, {
    id: 'page_season2',
    emoji: '🟢',
    name: 'Season 2 Theme',
    cost: 1000,
    desc: 'Green & red casino theme (S2).'
  }, {
    id: 'page_season3',
    emoji: '🟣',
    name: 'Season 3 Theme',
    cost: 1000,
    desc: 'Purple & orange casino theme (S3).'
  }, {
    id: 'page_season4',
    emoji: '💜',
    name: 'Season 4 Theme',
    cost: 1000,
    desc: 'Deep violet casino theme (S4).'
  }, {
    id: 'page_season5',
    emoji: '🌊',
    name: 'Season 5 Theme',
    cost: 1000,
    desc: 'Bioluminescent deep ocean theme (S5).'
  }, {
    id: 'page_season6',
    emoji: '🌙',
    name: 'Season 6 Theme',
    cost: 1000,
    desc: 'Night ocean — deep indigo & violet (S6).'
  }]
}, {
  label: '🎲 Dice Charges',
  items: [{
    id: 'dice_charge_2',
    emoji: '🎲',
    name: 'Extra Charge',
    cost: 2000,
    desc: 'Max dice charges: 1 → 2',
    tier: 2
  }, {
    id: 'dice_charge_3',
    emoji: '🎲',
    name: 'Max Charge',
    cost: 15000,
    desc: 'Max dice charges: 2 → 3',
    requires: 'dice_charge_2',
    tier: 3
  }, {
    id: 'dice_charge_4',
    emoji: '🎲',
    name: 'Overcharge',
    cost: 100000,
    desc: 'Max dice charges: 3 → 4',
    requires: 'dice_charge_3',
    tier: 3
  }, {
    id: 'dice_extra',
    emoji: '🎲',
    name: 'Extra Die',
    cost: 1000000,
    desc: 'Roll 3 dice instead of 2. Triple curses and triple blessings possible.',
    requires: 'dice_charge_3',
    tier: 3
  }]
}, {
  label: '🎲 Special Upgrades',
  items: [{
    id: 'fortune_charm',
    emoji: '🍀',
    name: 'Fortune Charm',
    cost: 1000000,
    desc: '25% chance: +25% to streak bonus payout',
    tier: 3
  }, {
    id: 'lucky_seven',
    emoji: '7️⃣',
    name: 'Lucky Seven',
    cost: 7000000,
    desc: 'Every 7th spin is guaranteed a win',
    tier: 3
  }, {
    id: 'win_echo',
    emoji: '🔊',
    name: 'Win Echo',
    cost: 1000000,
    desc: '20% chance to double wins earned on any win',
    tier: 3
  }, {
    id: 'resilience',
    emoji: '💪',
    name: 'Resilience',
    cost: 10000000,
    desc: '50% chance: on win streak, a loss only drops streak by 1 instead of resetting',
    tier: 3
  }, {
    id: 'jackpot',
    emoji: '🎰',
    name: 'Jackpot',
    cost: 3000000,
    desc: '1% chance each win to multiply gains by 25x. 5% chance for Jackpot Echo next spin.',
    tier: 3
  }, {
    id: 'streak_armor_inf',
    emoji: '🛡️',
    name: 'Streak Armor',
    cost: 0,
    desc: '+1% to Resilience save chance per level (base 50%, cap 60%)',
    infinite: true
  }]
}, {
  label: '🌌 Legendary',
  items: [{
    id: 'singularity',
    emoji: '🌌',
    name: 'The Singularity',
    cost: 1e67,
    desc: 'Transcend reality itself. Every spin is a win.'
  }]
}];

// Infinite upgrade config (mirrors INFINITE_UPGRADES in models.py)
var INF_UPGRADE_CFG = {
  winmult_inf: {
    tierCosts: [200, 600, 2000, 6400, 20000, 64000, 200000],
    infBase: 400000,
    infScale: 1.18
  },
  bonusmult_inf: {
    tierCosts: [300, 900, 2800, 8500, 26000, 80000],
    infBase: 200000,
    infScale: 1.18
  },
  clickmult_inf: {
    tierCosts: [75, 250, 600, 1400, 3000],
    infBase: 10000,
    infScale: 1.5
  },
  streak_armor_inf: {
    tierCosts: [500000, 750000, 1000000, 1250000, 1500000, 1750000, 2000000, 2250000, 2500000, 2750000],
    infBase: 999999999,
    infScale: 1.0,
    maxLevel: 10
  }
};
function infCost(id, level) {
  var _INF_UPGRADE_CFG$id = INF_UPGRADE_CFG[id],
    tierCosts = _INF_UPGRADE_CFG$id.tierCosts,
    infBase = _INF_UPGRADE_CFG$id.infBase,
    infScale = _INF_UPGRADE_CFG$id.infScale;
  if (level < tierCosts.length) return tierCosts[level];
  return Math.floor(infBase * Math.pow(infScale, level - tierCosts.length));
}
function infMultiplier(id, level) {
  if (id === 'streak_armor_inf') {
    return Math.min(50 + level, 60); // resilience % chance
  }
  if (id === 'winmult_inf') {
    if (level <= 0) return 1;
    if (level <= 7) return Math.pow(2, level);
    return 128 + (level - 7) * 16;
  }
  if (id === 'bonusmult_inf') {
    var fixed = [1, 2, 5, 10, 20, 50, 100];
    if (level <= 6) return fixed[level];
    return 100 + (level - 6) * 10;
  }
  if (id === 'clickmult_inf') return 1 + level * 0.25;
  return 1;
}
var DEFAULT_FISH = {
  emoji: '🐟',
  labels: {
    idle: 'Click me!',
    happy: '🎉 Nice!',
    sad: '💀 Ouch!'
  }
};
function getFishData(equippedFish) {
  return FISH_SKINS.find(function (s) {
    return s.id === equippedFish;
  }) || DEFAULT_FISH;
}
var COSMETIC_SECTION_IDS = new Set(['bg_royal', 'bg_inferno', 'bg_forest', 'bg_abyss', 'bg_cosmic', 'fishsize_small', 'fishsize_1', 'fishsize_2', 'fishsize_3', 'confetti_1', 'confetti_2', 'confetti_3', 'party_mode', 'trail_1', 'trail_2', 'trail_3', 'trail_4', 'trail_5', 'trail_6', 'theme_fire', 'theme_ice', 'theme_neon', 'theme_void', 'theme_gold', 'golden_wheel', 'page_season1', 'page_season2', 'page_season3', 'page_season4', 'page_season5', 'page_season6', 'final_frenzy', 'auto_guard']);

// Season 3: currency classification (mirrors ITEM_CURRENCY in models.py)
var COSMETIC_IDS = new Set(['fish_tropical', 'fish_puffer', 'fish_octopus', 'fish_shark', 'fish_dolphin', 'fish_squid', 'fish_turtle', 'fish_crab', 'fish_lobster', 'fish_whale', 'fish_seal', 'fish_shrimp', 'fish_coral', 'fish_mermaid', 'fish_croc', 'fishsize_small', 'fishsize_1', 'fishsize_2', 'fishsize_3', 'trail_1', 'trail_2', 'trail_3', 'trail_4', 'trail_5', 'trail_6', 'theme_fire', 'theme_ice', 'theme_neon', 'theme_void', 'theme_gold', 'golden_wheel', 'page_season1', 'page_season2', 'page_season3', 'page_season4', 'page_season5', 'page_season6', 'party_mode', 'confetti_1', 'confetti_2', 'confetti_3', 'bg_royal', 'bg_inferno', 'bg_forest', 'bg_abyss', 'bg_cosmic']);
var getItemCurrency = function getItemCurrency(id) {
  return id === 'singularity' ? 'fish_clicks' : COSMETIC_IDS.has(id) ? 'losses' : 'wins';
};
var currencyIcon = function currencyIcon(c) {
  return c === 'wins' ? '🏆' : c === 'losses' ? '💀' : '🐟';
};

// ── Shop components ────────────────────────────────────────────────────────
var ShopItem = React.memo(function ShopItem(_ref21) {
  var item = _ref21.item,
    owned = _ref21.owned,
    equipped = _ref21.equipped,
    active = _ref21.active,
    canAfford = _ref21.canAfford,
    onBuy = _ref21.onBuy,
    onEquip = _ref21.onEquip,
    onEquipCosmetic = _ref21.onEquipCosmetic,
    isSkin = _ref21.isSkin,
    isSingularity = _ref21.isSingularity,
    isCosmetic = _ref21.isCosmetic,
    infLevel = _ref21.infLevel,
    displayCost = _ref21.displayCost;
  var isInfinite = !!item.infinite;
  var cost = isInfinite ? displayCost : item.cost;
  var actionEl;
  if (isInfinite) {
    actionEl = /*#__PURE__*/React.createElement("button", {
      className: "shop-buy-btn ".concat(canAfford ? 'can-afford' : 'cant-afford'),
      onClick: function onClick() {
        return canAfford && onBuy(item.id, cost);
      }
    }, "Buy");
  } else if (owned && isSkin) {
    actionEl = equipped ? /*#__PURE__*/React.createElement("span", {
      className: "shop-equipped-badge"
    }, "\u2713 On") : /*#__PURE__*/React.createElement("button", {
      className: "shop-equip-btn",
      onClick: function onClick() {
        return onEquip(item.id);
      }
    }, "Equip");
  } else if (owned && isCosmetic) {
    actionEl = active ? /*#__PURE__*/React.createElement("button", {
      className: "shop-equip-btn active-cosmetic",
      onClick: function onClick() {
        return onEquipCosmetic(item.id);
      }
    }, "Active") : /*#__PURE__*/React.createElement("button", {
      className: "shop-equip-btn",
      onClick: function onClick() {
        return onEquipCosmetic(item.id);
      }
    }, "Equip");
  } else if (owned) {
    actionEl = /*#__PURE__*/React.createElement("span", {
      className: "shop-active-badge"
    }, "Active");
  } else {
    actionEl = /*#__PURE__*/React.createElement("button", {
      className: "shop-buy-btn ".concat(canAfford ? 'can-afford' : 'cant-afford'),
      onClick: function onClick() {
        return canAfford && onBuy(item.id, cost);
      }
    }, "Buy");
  }
  var extraClass = isSingularity && !owned ? 'singularity-item' : '';
  var infDesc = isInfinite && infLevel != null ? function () {
    var cfg = INF_UPGRADE_CFG[item.id];
    var atMax = cfg && cfg.maxLevel != null && infLevel >= cfg.maxLevel;
    if (atMax) return "Lv".concat(infLevel, " \xB7 MAX  ").concat(item.desc);
    var cur = infMultiplier(item.id, infLevel);
    var nxt = infMultiplier(item.id, infLevel + 1);
    var sep = item.id === 'streak_armor_inf' ? '%' : 'x';
    return "Lv".concat(infLevel, " \xB7 ").concat(cur).concat(sep, " \u2192 ").concat(nxt).concat(sep, "  ").concat(item.desc);
  }() : item.desc;
  return /*#__PURE__*/React.createElement("div", {
    className: "shop-item ".concat(!isInfinite && owned ? equipped || active ? 'equipped' : 'owned' : '', " ").concat(extraClass)
  }, /*#__PURE__*/React.createElement("span", {
    className: "shop-item-emoji"
  }, item.emoji), /*#__PURE__*/React.createElement("div", {
    className: "shop-item-info"
  }, /*#__PURE__*/React.createElement("div", {
    className: "shop-item-name"
  }, item.name), infDesc && /*#__PURE__*/React.createElement("div", {
    className: "shop-item-desc",
    "data-tooltip": infDesc
  }, infDesc), /*#__PURE__*/React.createElement("div", {
    className: "shop-item-cost cost-".concat(getItemCurrency(item.id))
  }, currencyIcon(getItemCurrency(item.id)), " ", fmt(cost))), /*#__PURE__*/React.createElement("div", {
    className: "shop-item-action"
  }, actionEl));
});
var COSMETIC_SECTION_LABELS = new Set(['🐟 Fishing Panel Size', '✨ Fish Trail', '🎡 Wheel Theme', '🎊 Confetti', '🎨 Atmosphere', '🖼️ Page Theme']);

// Season 5 tier thresholds
var TIER_THRESHOLDS = {
  2: 1000,
  3: 10000
};
function ShopPanel(_ref22) {
  var fishClicks = _ref22.fishClicks,
    wins = _ref22.wins,
    losses = _ref22.losses,
    ownedItems = _ref22.ownedItems,
    equippedFish = _ref22.equippedFish,
    activeCosmetics = _ref22.activeCosmetics,
    infLevels = _ref22.infLevels,
    onBuy = _ref22.onBuy,
    onEquip = _ref22.onEquip,
    onEquipCosmetic = _ref22.onEquipCosmetic,
    collapsed = _ref22.collapsed,
    winCount = _ref22.winCount,
    caughtSpecies = _ref22.caughtSpecies;
  var _useState39 = useState('functional'),
    _useState40 = _slicedToArray(_useState39, 2),
    activeTab = _useState40[0],
    setActiveTab = _useState40[1];
  var _useMemo = useMemo(function () {
      var cosmetic = [],
        functional = [];
      SHOP_SECTIONS.forEach(function (section) {
        var isCosmeticSection = COSMETIC_SECTION_LABELS.has(section.label);
        var visibleItems = section.items.filter(function (item) {
          var requiresMet = !item.requires || ownedItems.includes(item.requires);
          if (isCosmeticSection) return requiresMet;
          if (item.infinite) {
            // streak_armor_inf requires resilience owned
            if (item.id === 'streak_armor_inf') return ownedItems.includes('resilience');
            return requiresMet;
          }
          var isOwned = ownedItems.includes(item.id);
          if (!isOwned) return requiresMet; // next tier to buy
          // Owned: show only if this is the latest owned in its chain
          var nextInChain = section.items.find(function (other) {
            return other.requires === item.id && !other.infinite && !COSMETIC_SECTION_IDS.has(other.id);
          });
          return !nextInChain || !ownedItems.includes(nextInChain.id);
        });
        if (visibleItems.length === 0) return;
        (COSMETIC_SECTION_LABELS.has(section.label) ? cosmetic : functional).push(_objectSpread(_objectSpread({}, section), {}, {
          visibleItems: visibleItems
        }));
      });
      return {
        cosmeticSections: cosmetic,
        functionalSections: functional
      };
    }, [ownedItems]),
    cosmeticSections = _useMemo.cosmeticSections,
    functionalSections = _useMemo.functionalSections;
  var renderSection = function renderSection(section) {
    return /*#__PURE__*/React.createElement(React.Fragment, {
      key: section.label
    }, /*#__PURE__*/React.createElement("div", {
      className: "shop-section-label"
    }, "\u2500\u2500 ", section.label, " \u2500\u2500"), section.visibleItems.map(function (item) {
      var isCosmetic = COSMETIC_SECTION_IDS.has(item.id);
      var itemTierNum = item.tier || 1;
      var tierLocked = itemTierNum > 1 && !ownedItems.includes(item.id);
      var tierThreshold = tierLocked ? TIER_THRESHOLDS[itemTierNum] : null;
      var tierUnlocked = !tierLocked || winCount >= (tierThreshold || 0);
      var infLevel = item.infinite ? infLevels[item.id] || 0 : null;
      var cfg = item.infinite ? INF_UPGRADE_CFG[item.id] : null;
      var atMaxLevel = cfg && cfg.maxLevel != null && infLevel >= cfg.maxLevel;
      var displayCost = item.infinite ? infCost(item.id, infLevel) : item.cost;
      var currency = getItemCurrency(item.id);
      var balance = currency === 'wins' ? wins : currency === 'losses' ? losses : fishClicks;

      // Master Lure (lure_5) requires all species caught (complete Encyclopaedia)
      var encyclopaediaLocked = item.encyclopaediaLocked && !ownedItems.includes(item.id) && (caughtSpecies || []).length < FISH_CATALOG_CLIENT.length;
      if (encyclopaediaLocked) {
        var caught = (caughtSpecies || []).length;
        var total = FISH_CATALOG_CLIENT.length;
        return /*#__PURE__*/React.createElement("div", {
          key: item.id,
          className: "shop-item shop-item--locked"
        }, /*#__PURE__*/React.createElement("span", {
          className: "shop-item-emoji",
          style: {
            opacity: 0.4
          }
        }, item.emoji), /*#__PURE__*/React.createElement("div", {
          className: "shop-item-info"
        }, /*#__PURE__*/React.createElement("div", {
          className: "shop-item-name",
          style: {
            opacity: 0.5
          }
        }, item.name), /*#__PURE__*/React.createElement("div", {
          className: "shop-item-desc",
          style: {
            opacity: 0.5
          }
        }, "\uD83D\uDD12 Complete your Encyclopaedia to unlock (", caught, "/", total, " species)")), /*#__PURE__*/React.createElement("div", {
          className: "shop-item-action"
        }, /*#__PURE__*/React.createElement("span", {
          style: {
            fontSize: '0.7rem',
            color: 'var(--text-muted, #888)'
          }
        }, caught, "/", total)));
      }
      if (tierLocked && !tierUnlocked) {
        return /*#__PURE__*/React.createElement("div", {
          key: item.id,
          className: "shop-item shop-item--locked"
        }, /*#__PURE__*/React.createElement("span", {
          className: "shop-item-emoji",
          style: {
            opacity: 0.4
          }
        }, item.emoji), /*#__PURE__*/React.createElement("div", {
          className: "shop-item-info"
        }, /*#__PURE__*/React.createElement("div", {
          className: "shop-item-name",
          style: {
            opacity: 0.5
          }
        }, item.name), /*#__PURE__*/React.createElement("div", {
          className: "shop-item-desc",
          style: {
            opacity: 0.5
          }
        }, "\uD83D\uDD12 Unlocks at ", fmt(tierThreshold), " total wins")), /*#__PURE__*/React.createElement("div", {
          className: "shop-item-action"
        }, /*#__PURE__*/React.createElement("span", {
          style: {
            fontSize: '0.7rem',
            color: 'var(--text-muted, #888)'
          }
        }, fmt(winCount), "/", fmt(tierThreshold))));
      }
      return /*#__PURE__*/React.createElement(ShopItem, {
        key: item.id,
        item: item,
        isSkin: false,
        isSingularity: item.id === 'singularity',
        isCosmetic: isCosmetic,
        owned: !item.infinite && ownedItems.includes(item.id),
        equipped: false,
        active: isCosmetic && activeCosmetics.includes(item.id),
        canAfford: !atMaxLevel && balance >= displayCost,
        infLevel: infLevel,
        displayCost: atMaxLevel ? 0 : displayCost,
        onBuy: onBuy,
        onEquip: onEquip,
        onEquipCosmetic: onEquipCosmetic
      });
    }));
  };
  return /*#__PURE__*/React.createElement("div", {
    className: "shop-panel".concat(collapsed ? ' shop-panel--collapsed' : '')
  }, /*#__PURE__*/React.createElement("div", {
    className: "shop-header"
  }, /*#__PURE__*/React.createElement("div", {
    className: "shop-title"
  }, "\uD83D\uDED2 Shop"), /*#__PURE__*/React.createElement("div", {
    className: "shop-balance"
  }, /*#__PURE__*/React.createElement("span", {
    className: "balance-wins"
  }, "\uD83C\uDFC6 ", fmt(wins)), /*#__PURE__*/React.createElement("span", {
    className: "balance-losses"
  }, "\uD83D\uDC80 ", fmt(losses)), /*#__PURE__*/React.createElement("span", {
    className: "balance-clicks"
  }, "\uD83D\uDC1F ", fmt(fishClicks)))), /*#__PURE__*/React.createElement("div", {
    className: "shop-tabs"
  }, /*#__PURE__*/React.createElement("button", {
    className: "shop-tab ".concat(activeTab === 'functional' ? 'active' : ''),
    onClick: function onClick() {
      return setActiveTab('functional');
    }
  }, "\u26A1 Functional"), /*#__PURE__*/React.createElement("button", {
    className: "shop-tab shop-tab--cosmetic ".concat(activeTab === 'cosmetic' ? 'active' : ''),
    onClick: function onClick() {
      return setActiveTab('cosmetic');
    }
  }, "\uD83C\uDFA8 Cosmetic")), /*#__PURE__*/React.createElement("div", {
    className: "shop-tab-content".concat(activeTab === 'cosmetic' ? ' shop-tab-content--cosmetic' : '')
  }, activeTab === 'cosmetic' ? /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    className: "shop-section-label"
  }, "\u2500\u2500 Fish Skins \u2500\u2500"), FISH_SKINS.map(function (item) {
    return /*#__PURE__*/React.createElement(ShopItem, {
      key: item.id,
      item: item,
      isSkin: true,
      owned: ownedItems.includes(item.id),
      equipped: equippedFish === item.id,
      canAfford: losses >= item.cost,
      onBuy: onBuy,
      onEquip: onEquip,
      onEquipCosmetic: onEquipCosmetic
    });
  }), cosmeticSections.map(renderSection)) : functionalSections.map(renderSection)));
}

// ── Stats Panel ────────────────────────────────────────────────────────────
var PLACE_LABEL = function PLACE_LABEL(pos) {
  return pos === 1 ? '🥇 1st' : pos === 2 ? '🥈 2nd' : pos === 3 ? '🥉 3rd' : null;
};
function StatsPanel(_ref23) {
  var open = _ref23.open,
    onClose = _ref23.onClose;
  var _useState41 = useState(null),
    _useState42 = _slicedToArray(_useState41, 2),
    stats = _useState42[0],
    setStats = _useState42[1];
  useEffect(function () {
    if (!open) return;
    apiFetch('/api/stats').then(function (r) {
      if (r.ok) setStats(r.data);
    });
  }, [open]);
  if (!open) return null;
  var history = (stats === null || stats === void 0 ? void 0 : stats.season_history) || [];
  return /*#__PURE__*/React.createElement("div", {
    className: "stats-overlay",
    onClick: onClose
  }, /*#__PURE__*/React.createElement("div", {
    className: "stats-card",
    onClick: function onClick(e) {
      return e.stopPropagation();
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "stats-title"
  }, "\uD83D\uDCCA Your Stats"), stats ? /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
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
  }, /*#__PURE__*/React.createElement("span", null, "Season Fish Bucks"), /*#__PURE__*/React.createElement("span", null, fmt(stats.total_fish_clicks))), /*#__PURE__*/React.createElement("div", {
    className: "stats-row"
  }, /*#__PURE__*/React.createElement("span", null, "Fastest Catch"), /*#__PURE__*/React.createElement("span", null, stats.fastest_catch_pct != null ? "\uD83C\uDFAF ".concat(stats.fastest_catch_pct, "%") : '—'))), history.length > 0 && /*#__PURE__*/React.createElement("div", {
    className: "stats-season-history"
  }, /*#__PURE__*/React.createElement("div", {
    className: "stats-section-title"
  }, "Season History"), history.map(function (s) {
    var place = PLACE_LABEL(s.finishing_position);
    var participated = s.final_wins != null;
    return /*#__PURE__*/React.createElement("div", {
      className: "stats-row stats-row--season",
      key: s.season_number
    }, /*#__PURE__*/React.createElement("span", null, "Season ", s.season_number), /*#__PURE__*/React.createElement("span", null, !participated ? '—' : place ? /*#__PURE__*/React.createElement("span", {
      className: "stats-podium"
    }, place) : "".concat(fmt(s.final_wins), " wins")));
  }))) : /*#__PURE__*/React.createElement("div", {
    className: "stats-loading"
  }, "Loading\u2026"), /*#__PURE__*/React.createElement("button", {
    className: "stats-close-btn",
    onClick: onClose
  }, "\u2715")));
}

// ── Auth Page ──────────────────────────────────────────────────────────────
function AuthPage(_ref24) {
  var onAuth = _ref24.onAuth;
  var _useState43 = useState('login'),
    _useState44 = _slicedToArray(_useState43, 2),
    mode = _useState44[0],
    setMode = _useState44[1];
  var _useState45 = useState(''),
    _useState46 = _slicedToArray(_useState45, 2),
    username = _useState46[0],
    setUsername = _useState46[1];
  var _useState47 = useState(''),
    _useState48 = _slicedToArray(_useState47, 2),
    password = _useState48[0],
    setPassword = _useState48[1];
  var _useState49 = useState(''),
    _useState50 = _slicedToArray(_useState49, 2),
    error = _useState50[0],
    setError = _useState50[1];
  var _useState51 = useState(false),
    _useState52 = _slicedToArray(_useState51, 2),
    loading = _useState52[0],
    setLoading = _useState52[1];
  var submit = /*#__PURE__*/function () {
    var _ref25 = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee6(e) {
      var _yield$apiFetch, ok, data;
      return _regeneratorRuntime().wrap(function _callee6$(_context6) {
        while (1) switch (_context6.prev = _context6.next) {
          case 0:
            e.preventDefault();
            setError('');
            setLoading(true);
            _context6.next = 5;
            return apiFetch("/api/".concat(mode), {
              method: 'POST',
              body: JSON.stringify({
                username: username,
                password: password
              })
            });
          case 5:
            _yield$apiFetch = _context6.sent;
            ok = _yield$apiFetch.ok;
            data = _yield$apiFetch.data;
            setLoading(false);
            if (ok) {
              onAuth(data.username);
            } else {
              setError(data.error || 'Something went wrong');
            }
          case 10:
          case "end":
            return _context6.stop();
        }
      }, _callee6);
    }));
    return function submit(_x4) {
      return _ref25.apply(this, arguments);
    };
  }();
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
    onChange: function onChange(e) {
      return setUsername(e.target.value);
    },
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
    onChange: function onChange(e) {
      return setPassword(e.target.value);
    },
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
    onClick: function onClick() {
      setMode('register');
      setError('');
    }
  }, "Register")) : /*#__PURE__*/React.createElement(React.Fragment, null, "Have an account? ", /*#__PURE__*/React.createElement("a", {
    onClick: function onClick() {
      setMode('login');
      setError('');
    }
  }, "Sign in")))));
}

// ── Community Pot ──────────────────────────────────────────────────────────
function usePotCountdown(filledAt, active) {
  var _useState53 = useState(null),
    _useState54 = _slicedToArray(_useState53, 2),
    remaining = _useState54[0],
    setRemaining = _useState54[1];
  useEffect(function () {
    if (!active || !filledAt) {
      setRemaining(null);
      return;
    }
    var expiresAt = new Date(filledAt).getTime() + 1800 * 1000;
    var tick = function tick() {
      var secs = Math.max(0, Math.floor((expiresAt - Date.now()) / 1000));
      setRemaining(secs);
    };
    tick();
    var id = setInterval(tick, 1000);
    return function () {
      return clearInterval(id);
    };
  }, [filledAt, active]);
  return remaining;
}
function fmtCountdown(secs) {
  if (secs == null) return '';
  var m = Math.floor(secs / 60);
  var s = secs % 60;
  return "".concat(m, ":").concat(String(s).padStart(2, '0'));
}
function CommunityPot(_ref26) {
  var pot = _ref26.pot,
    fishClicks = _ref26.fishClicks,
    onContribute = _ref26.onContribute;
  var _useState55 = useState(pot),
    _useState56 = _slicedToArray(_useState55, 2),
    localPot = _useState56[0],
    setLocalPot = _useState56[1];
  var _useState57 = useState(!!pot.active),
    _useState58 = _slicedToArray(_useState57, 2),
    justFilled = _useState58[0],
    setJustFilled = _useState58[1];

  // Sync when parent pot state changes (e.g. on load)
  useEffect(function () {
    setLocalPot(pot);
    setJustFilled(!!pot.active);
  }, [pot]);

  // Poll every 5s for live updates — drives celebration state from server
  useEffect(function () {
    var id = setInterval(function () {
      apiFetch('/api/community-pot').then(function (r) {
        if (r.ok) {
          setLocalPot(r.data);
          setJustFilled(!!r.data.active);
        }
      });
    }, 5000);
    return function () {
      return clearInterval(id);
    };
  }, []);
  var handleContribute = /*#__PURE__*/function () {
    var _ref27 = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee7(amount) {
      var _yield$apiGame5, ok, data;
      return _regeneratorRuntime().wrap(function _callee7$(_context7) {
        while (1) switch (_context7.prev = _context7.next) {
          case 0:
            _context7.next = 2;
            return apiGame('/api/community-pot/contribute', {
              method: 'POST',
              body: JSON.stringify({
                amount: amount
              })
            });
          case 2:
            _yield$apiGame5 = _context7.sent;
            ok = _yield$apiGame5.ok;
            data = _yield$apiGame5.data;
            if (ok) {
              setLocalPot(function (prev) {
                return _objectSpread(_objectSpread({}, prev), {}, {
                  total_contributed: data.pot_total,
                  target: data.pot_target,
                  filled: data.pot_filled,
                  active: data.pot_active,
                  filled_at: data.filled_at,
                  win_chance_pct: data.win_chance_pct
                });
              });
              onContribute(data.fish_clicks);
              setJustFilled(!!data.pot_active);
            }
          case 6:
          case "end":
            return _context7.stop();
        }
      }, _callee7);
    }));
    return function handleContribute(_x5) {
      return _ref27.apply(this, arguments);
    };
  }();
  var total = localPot.total_contributed || 0;
  var target = localPot.target || 1000;
  var pct = Math.min(100, total / target * 100);
  var winRate = (localPot.win_chance_pct || 50.0).toFixed(1);
  var active = localPot.active;
  var countdown = usePotCountdown(localPot.filled_at, active);

  // Ghost bars: how far the bar would extend if clicks were contributed now
  var userClicks = fishClicks || 0;
  var allPendingClicks = localPot.total_pending_clicks || 0;
  var userGhostPct = active ? 0 : Math.min(100, (total + userClicks) / target * 100);
  var allGhostPct = active ? 0 : Math.min(100, (total + allPendingClicks) / target * 100);
  return /*#__PURE__*/React.createElement("div", {
    className: "community-pot-bar".concat(justFilled ? ' community-pot-active' : '')
  }, /*#__PURE__*/React.createElement("div", {
    className: "community-pot-inner"
  }, /*#__PURE__*/React.createElement("span", {
    className: "community-pot-label"
  }, "\uD83C\uDFA3 Community Pot"), /*#__PURE__*/React.createElement("div", {
    className: "community-pot-progress"
  }, allGhostPct > pct && /*#__PURE__*/React.createElement("div", {
    className: "community-pot-ghost-all",
    style: {
      width: allGhostPct + '%'
    },
    title: "All players contributing their clicks"
  }), userGhostPct > pct && /*#__PURE__*/React.createElement("div", {
    className: "community-pot-ghost-user",
    style: {
      width: userGhostPct + '%'
    },
    title: "Your clicks contributed"
  }), /*#__PURE__*/React.createElement("div", {
    className: "community-pot-fill",
    style: {
      width: pct + '%'
    },
    title: "Current pot total"
  })), /*#__PURE__*/React.createElement("span", {
    className: "community-pot-count"
  }, fmt(total), " / ", fmt(target)), justFilled ? /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("span", {
    className: "community-pot-bonus"
  }, "\uD83C\uDF89 Win Rate ", winRate, "%"), /*#__PURE__*/React.createElement("span", {
    className: "season-countdown"
  }, fmtCountdown(countdown))) : /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    className: "community-pot-buttons"
  }, /*#__PURE__*/React.createElement("button", {
    onClick: function onClick() {
      return handleContribute('10pct');
    },
    disabled: fishClicks < 1
  }, "+", fmt(Math.max(1, Math.floor(target / 10)))), /*#__PURE__*/React.createElement("button", {
    onClick: function onClick() {
      return handleContribute('all');
    },
    disabled: fishClicks < 1
  }, "All")))));
}

// ── Game App ───────────────────────────────────────────────────────────────
function GameApp(_ref28) {
  var _gameState$dice_charg, _gameState$dice_rolle;
  var username = _ref28.username,
    gameState = _ref28.gameState,
    onLogout = _ref28.onLogout,
    onSessionExpired = _ref28.onSessionExpired;
  var canvasRef = useRef(null);
  var _useState59 = useState(0),
    _useState60 = _slicedToArray(_useState59, 2),
    rotation = _useState60[0],
    setRotation = _useState60[1];
  var _useState61 = useState(false),
    _useState62 = _slicedToArray(_useState61, 2),
    spinning = _useState62[0],
    setSpinning = _useState62[1];
  var _useState63 = useState(null),
    _useState64 = _slicedToArray(_useState63, 2),
    result = _useState64[0],
    setResult = _useState64[1];
  var _useState65 = useState(false),
    _useState66 = _slicedToArray(_useState65, 2),
    showResult = _useState66[0],
    setShowResult = _useState66[1];
  var setShowResultSync = function setShowResultSync(v) {
    showResultRef.current = v;
    setShowResult(v);
  };
  var _useState67 = useState(null),
    _useState68 = _slicedToArray(_useState67, 2),
    shieldFeedback = _useState68[0],
    setShieldFeedback = _useState68[1];
  var _useState69 = useState(null),
    _useState70 = _slicedToArray(_useState69, 2),
    guardState = _useState70[0],
    setGuardState = _useState70[1]; // { blocked, broke } | null
  var guardCompleteRef = useRef(null);
  var _useState71 = useState(false),
    _useState72 = _slicedToArray(_useState71, 2),
    hideResult = _useState72[0],
    setHideResult = _useState72[1];
  var _useState73 = useState(false),
    _useState74 = _slicedToArray(_useState73, 2),
    confetti = _useState74[0],
    setConfetti = _useState74[1];
  var _useState75 = useState(gameState.wins),
    _useState76 = _slicedToArray(_useState75, 2),
    wins = _useState76[0],
    setWins = _useState76[1];
  var _useState77 = useState(gameState.losses),
    _useState78 = _slicedToArray(_useState77, 2),
    losses = _useState78[0],
    setLosses = _useState78[1];
  var _useState79 = useState(gameState.streak),
    _useState80 = _slicedToArray(_useState79, 2),
    streak = _useState80[0],
    setStreak = _useState80[1];
  var _useState81 = useState('idle'),
    _useState82 = _slicedToArray(_useState81, 2),
    fishMood = _useState82[0],
    setFishMood = _useState82[1];
  var _useState83 = useState(gameState.fish_clicks),
    _useState84 = _slicedToArray(_useState83, 2),
    fishClicks = _useState84[0],
    setFishClicks = _useState84[1];
  var _useState85 = useState(gameState.caught_species || []),
    _useState86 = _slicedToArray(_useState85, 2),
    caughtSpecies = _useState86[0],
    setCaughtSpecies = _useState86[1];
  var _useState87 = useState(gameState.fishing_lucky_next || false),
    _useState88 = _slicedToArray(_useState87, 2),
    fishingLuckyNext = _useState88[0],
    setFishingLuckyNext = _useState88[1];
  var _useState89 = useState(false),
    _useState90 = _slicedToArray(_useState89, 2),
    showEncyclopedia = _useState90[0],
    setShowEncyclopedia = _useState90[1];
  var _useState91 = useState(0),
    _useState92 = _slicedToArray(_useState91, 2),
    bonusEarned = _useState92[0],
    setBonusEarned = _useState92[1];
  var _useState93 = useState(false),
    _useState94 = _slicedToArray(_useState93, 2),
    echoTriggered = _useState94[0],
    setEchoTriggered = _useState94[1];
  var _useState95 = useState(false),
    _useState96 = _slicedToArray(_useState95, 2),
    jackpotHit = _useState96[0],
    setJackpotHit = _useState96[1];
  var _useState97 = useState(false),
    _useState98 = _slicedToArray(_useState97, 2),
    resilienceTriggered = _useState98[0],
    setResilienceTriggered = _useState98[1];
  var _useState99 = useState(false),
    _useState100 = _slicedToArray(_useState99, 2),
    luckySevenTriggered = _useState100[0],
    setLuckySevenTriggered = _useState100[1];
  var _useState101 = useState(false),
    _useState102 = _slicedToArray(_useState101, 2),
    fortuneCharmTriggered = _useState102[0],
    setFortuneCharmTriggered = _useState102[1];
  var _useState103 = useState(gameState.shield_charges),
    _useState104 = _slicedToArray(_useState103, 2),
    shieldCharges = _useState104[0],
    setShieldCharges = _useState104[1];
  var _useState105 = useState(gameState.regen_recharge_wins || 0),
    _useState106 = _slicedToArray(_useState105, 2),
    regenRechargeWins = _useState106[0],
    setRegenRechargeWins = _useState106[1];
  var _useState107 = useState(false),
    _useState108 = _slicedToArray(_useState107, 2),
    autoSpin = _useState108[0],
    setAutoSpin = _useState108[1];
  var _useState109 = useState(gameState.owned_items),
    _useState110 = _slicedToArray(_useState109, 2),
    ownedItems = _useState110[0],
    setOwnedItems = _useState110[1];
  var _useState111 = useState(gameState.equipped_fish),
    _useState112 = _slicedToArray(_useState111, 2),
    equippedFish = _useState112[0],
    setEquippedFish = _useState112[1];
  var _useState113 = useState(gameState.active_cosmetics || []),
    _useState114 = _slicedToArray(_useState113, 2),
    activeCosmetics = _useState114[0],
    setActiveCosmetics = _useState114[1];
  var _useState115 = useState({
      winmult_inf: gameState.winmult_inf_level || 0,
      bonusmult_inf: gameState.bonusmult_inf_level || 0,
      clickmult_inf: gameState.clickmult_inf_level || 0,
      streak_armor_inf: gameState.streak_armor_level || 0
    }),
    _useState116 = _slicedToArray(_useState115, 2),
    infLevels = _useState116[0],
    setInfLevels = _useState116[1];
  var _useState117 = useState(false),
    _useState118 = _slicedToArray(_useState117, 2),
    showStats = _useState118[0],
    setShowStats = _useState118[1];
  var _useState119 = useState(null),
    _useState120 = _slicedToArray(_useState119, 2),
    toast = _useState120[0],
    setToast = _useState120[1];
  var _useState121 = useState(gameState.season || null),
    _useState122 = _slicedToArray(_useState121, 2),
    season = _useState122[0],
    setSeason = _useState122[1];
  var _useState123 = useState(gameState.community_pot || {
      total_contributed: 0,
      target: 1000,
      filled: false,
      active: false,
      win_chance_pct: 50.0
    }),
    _useState124 = _slicedToArray(_useState123, 2),
    communityPot = _useState124[0],
    setCommunityPot = _useState124[1];
  var _useState125 = useState(gameState.spin_count || 0),
    _useState126 = _slicedToArray(_useState125, 2),
    spinCount = _useState126[0],
    setSpinCount = _useState126[1];
  var _useState127 = useState(gameState.win_count || 0),
    _useState128 = _slicedToArray(_useState127, 2),
    winCount = _useState128[0],
    setWinCount = _useState128[1];
  var _useState129 = useState(function () {
      var _gameState$low_spec_m;
      return (_gameState$low_spec_m = gameState.low_spec_mode) !== null && _gameState$low_spec_m !== void 0 ? _gameState$low_spec_m : localStorage.getItem('lowSpecMode') === 'true';
    }),
    _useState130 = _slicedToArray(_useState129, 2),
    lowSpec = _useState130[0],
    setLowSpec = _useState130[1];
  var _useState131 = useState(false),
    _useState132 = _slicedToArray(_useState131, 2),
    shopCollapsed = _useState132[0],
    setShopCollapsed = _useState132[1];
  var _useState133 = useState(false),
    _useState134 = _slicedToArray(_useState133, 2),
    diceRolling = _useState134[0],
    setDiceRolling = _useState134[1];
  var _useState135 = useState(null),
    _useState136 = _slicedToArray(_useState135, 2),
    diceResult = _useState136[0],
    setDiceResult = _useState136[1];
  var _useState137 = useState((_gameState$dice_charg = gameState.dice_charges) !== null && _gameState$dice_charg !== void 0 ? _gameState$dice_charg : 1),
    _useState138 = _slicedToArray(_useState137, 2),
    diceCharges = _useState138[0],
    setDiceCharges = _useState138[1];
  var _useState139 = useState(gameState.dice_last_recharge || new Date().toISOString()),
    _useState140 = _slicedToArray(_useState139, 2),
    diceLastRecharge = _useState140[0],
    setDiceLastRecharge = _useState140[1];
  var _useState141 = useState((_gameState$dice_rolle = gameState.dice_rolled_since_spin) !== null && _gameState$dice_rolle !== void 0 ? _gameState$dice_rolle : false),
    _useState142 = _slicedToArray(_useState141, 2),
    diceRolledSinceSpin = _useState142[0],
    setDiceRolledSinceSpin = _useState142[1];
  var _useState143 = useState(false),
    _useState144 = _slicedToArray(_useState143, 2),
    tabLocked = _useState144[0],
    setTabLocked = _useState144[1];
  var tabIdRef = useRef(function () {
    var id = sessionStorage.getItem('wheel_tab_id');
    if (!id) {
      id = Math.random().toString(36).slice(2) + Date.now().toString(36);
      sessionStorage.setItem('wheel_tab_id', id);
    }
    return id;
  }());
  var _useState145 = useState(function () {
      return window.innerWidth <= 768;
    }),
    _useState146 = _slicedToArray(_useState145, 2),
    isMobile = _useState146[0],
    setIsMobile = _useState146[1];
  var _useState147 = useState(null),
    _useState148 = _slicedToArray(_useState147, 2),
    mobilePanel = _useState148[0],
    setMobilePanel = _useState148[1];
  var _useState149 = useState(function () {
      return localStorage.getItem('chat_open') !== 'false';
    }),
    _useState150 = _slicedToArray(_useState149, 2),
    showChat = _useState150[0],
    setShowChat = _useState150[1];
  var fireMode = 2; // Mix mode

  useEffect(function () {
    var mq = window.matchMedia('(max-width: 768px)');
    var handler = function handler(e) {
      return setIsMobile(e.matches);
    };
    mq.addEventListener('change', handler);
    return function () {
      return mq.removeEventListener('change', handler);
    };
  }, []);
  var toggleMobilePanel = useCallback(function (panel) {
    setMobilePanel(function (prev) {
      return prev === panel ? null : panel;
    });
  }, []);
  var spinSpeed = useMemo(function () {
    if (ownedItems.includes('maxspin')) return 0.5;
    if (ownedItems.includes('ultraspin')) return 0.75;
    if (ownedItems.includes('hyperspin')) return 1.0;
    if (ownedItems.includes('turbo_spin')) return 1.5;
    if (ownedItems.includes('speed_boost')) return 3.0;
    return 4.5;
  }, [ownedItems]);

  // Guard animation speed multiplier (1.0 = normal, lower = faster)
  var guardSpeedMult = useMemo(function () {
    if (ownedItems.includes('guard_speed_4')) return 0.25;
    if (ownedItems.includes('guard_speed_3')) return 0.35;
    if (ownedItems.includes('guard_speed_2')) return 0.5;
    if (ownedItems.includes('guard_speed_1')) return 0.75;
    return 1.0;
  }, [ownedItems]);
  var autoSpinDelay = useMemo(function () {
    return activeCosmetics.includes('autospeed_3') ? 0 : activeCosmetics.includes('autospeed_2') ? 500 : activeCosmetics.includes('autospeed_1') ? 1000 : 1500;
  }, [activeCosmetics]);
  var diceMaxCharges = useMemo(function () {
    if (ownedItems.includes('dice_charge_4')) return 4;
    if (ownedItems.includes('dice_charge_3')) return 3;
    if (ownedItems.includes('dice_charge_2')) return 2;
    return 1;
  }, [ownedItems]);

  // fishPanelScale: controls the CSS transform scale on the fishing panel
  var fishPanelScale = useMemo(function () {
    return activeCosmetics.includes('fishsize_small') ? 0.5 : activeCosmetics.includes('fishsize_3') ? 2.0 : activeCosmetics.includes('fishsize_2') ? 1.6 : activeCosmetics.includes('fishsize_1') ? 1.3 : 1.0;
  }, [activeCosmetics]);
  var confettiCount = useMemo(function () {
    return Math.min(200, 80 * (activeCosmetics.includes('confetti_3') ? 15 : activeCosmetics.includes('confetti_2') ? 5 : activeCosmetics.includes('confetti_1') ? 2 : 1));
  }, [activeCosmetics]);
  var wheelTheme = useMemo(function () {
    if (activeCosmetics.includes('theme_gold')) return 'gold';
    if (activeCosmetics.includes('theme_void')) return 'void';
    if (activeCosmetics.includes('theme_neon')) return 'neon';
    if (activeCosmetics.includes('theme_ice')) return 'ice';
    if (activeCosmetics.includes('theme_fire')) return 'fire';
    if (activeCosmetics.includes('page_season5')) return 'bioluminescence';
    if (activeCosmetics.includes('page_season6')) return 'night_ocean';
    return 'default';
  }, [activeCosmetics]);
  var bgClass = useMemo(function () {
    if (activeCosmetics.includes('bg_cosmic')) return 'bg-cosmic';
    if (activeCosmetics.includes('bg_abyss')) return 'bg-abyss';
    if (activeCosmetics.includes('bg_forest')) return 'bg-forest';
    if (activeCosmetics.includes('bg_inferno')) return 'bg-inferno';
    if (activeCosmetics.includes('bg_royal')) return 'bg-royal';
    if (activeCosmetics.includes('bg_ocean')) return 'bg-ocean';
    return 'bg-ocean'; // Season 5 default
  }, [activeCosmetics]);
  var trailClass = useMemo(function () {
    if (activeCosmetics.includes('trail_6')) return 'trail-galaxy';
    if (activeCosmetics.includes('trail_5')) return 'trail-thunder';
    if (activeCosmetics.includes('trail_4')) return 'trail-frost';
    if (activeCosmetics.includes('trail_3')) return 'trail-rainbow';
    if (activeCosmetics.includes('trail_2')) return 'trail-fire';
    if (activeCosmetics.includes('trail_1')) return 'trail-sparkle';
    return '';
  }, [activeCosmetics]);
  var pageThemeClass = useMemo(function () {
    if (activeCosmetics.includes('page_season1')) return 'page-season1';
    if (activeCosmetics.includes('page_season2')) return 'page-season2';
    if (activeCosmetics.includes('page_season3')) return 'page-season3';
    if (activeCosmetics.includes('page_season4')) return 'page-season4';
    if (activeCosmetics.includes('page_season5')) return 'page-season5';
    if (activeCosmetics.includes('page_season6')) return 'page-season6';
    return '';
  }, [activeCosmetics]);
  var currentRotationRef = useRef(0);
  var fishTimerRef = useRef(null);
  var toastTimerRef = useRef(null);
  var confettiTimerRef = useRef(null);
  var autoSpinRef = useRef(false);
  var spinSpeedRef = useRef(4.5);
  var autoSpinDelayRef = useRef(1500);
  var spinningRef = useRef(false);
  var showResultRef = useRef(false);
  var activeCosmeticsRef = useRef(activeCosmetics);
  var lowSpecRef = useRef(lowSpec);
  useEffect(function () {
    activeCosmeticsRef.current = activeCosmetics;
  }, [activeCosmetics]);
  useEffect(function () {
    lowSpecRef.current = lowSpec;
  }, [lowSpec]);
  useEffect(function () {
    autoSpinRef.current = autoSpin;
    if (autoSpin && !spinning) spin();
  }, [autoSpin]); // eslint-disable-line
  useEffect(function () {
    spinSpeedRef.current = spinSpeed;
  }, [spinSpeed]);
  useEffect(function () {
    autoSpinDelayRef.current = autoSpinDelay;
  }, [autoSpinDelay]);

  // Tab heartbeat — claim the lock on mount, refresh every 10s
  useEffect(function () {
    var tabId = tabIdRef.current;
    var beat = function beat() {
      return apiGame('/api/tab/heartbeat', {
        method: 'POST',
        body: JSON.stringify({
          tab_id: tabId
        })
      }).then(function (r) {
        if (r.ok) setTabLocked(!r.data.active);
      });
    };
    beat();
    var id = setInterval(beat, 10000);
    return function () {
      return clearInterval(id);
    };
  }, []); // eslint-disable-line
  useEffect(function () {
    localStorage.setItem('lowSpecMode', lowSpec);
    document.body.classList.toggle('low-spec', lowSpec);
    apiGame('/api/settings', {
      method: 'POST',
      body: JSON.stringify({
        low_spec_mode: lowSpec
      })
    });
    var iframe = document.getElementById('seabed-bg');
    if (iframe) {
      iframe.src = lowSpec ? '/static/seabed-static.html' : '/static/seabed-animated.html';
    }
  }, [lowSpec]);
  useEffect(function () {
    var show = bgClass === 'bg-ocean';
    var iframe = document.getElementById('seabed-bg');
    var overlay = document.getElementById('seabed-overlay');
    if (iframe) iframe.style.display = show ? 'block' : 'none';
    if (overlay) overlay.style.display = show ? 'block' : 'none';
  }, [bgClass]);
  useEffect(function () {
    setSessionExpiredHandler(onSessionExpired);
    return function () {
      return setSessionExpiredHandler(null);
    };
  }, [onSessionExpired]);
  useEffect(function () {
    var currentNumber = season ? season.season_number : null;
    var id = setInterval(/*#__PURE__*/_asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee8() {
      var r, gs, _gs$data$dice_rolled_;
      return _regeneratorRuntime().wrap(function _callee8$(_context8) {
        while (1) switch (_context8.prev = _context8.next) {
          case 0:
            _context8.next = 2;
            return apiFetch('/api/season');
          case 2:
            r = _context8.sent;
            if (r.ok) {
              _context8.next = 5;
              break;
            }
            return _context8.abrupt("return");
          case 5:
            if (!(currentNumber !== null && r.data.season_number !== currentNumber)) {
              _context8.next = 13;
              break;
            }
            showToast("Season ".concat(currentNumber, " has ended! Season ").concat(r.data.season_number, " begins!"));
            _context8.next = 9;
            return apiGame('/api/state');
          case 9:
            gs = _context8.sent;
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
                winmult_inf: gs.data.winmult_inf_level || 0,
                bonusmult_inf: gs.data.bonusmult_inf_level || 0,
                clickmult_inf: gs.data.clickmult_inf_level || 0
              });
              if (gs.data.caught_species) setCaughtSpecies(gs.data.caught_species);
              setFishingLuckyNext(gs.data.fishing_lucky_next || false);
              if (gs.data.dice_charges != null) setDiceCharges(gs.data.dice_charges);
              if (gs.data.dice_last_recharge) setDiceLastRecharge(gs.data.dice_last_recharge);
              setDiceRolledSinceSpin((_gs$data$dice_rolled_ = gs.data.dice_rolled_since_spin) !== null && _gs$data$dice_rolled_ !== void 0 ? _gs$data$dice_rolled_ : false);
            }
            _context8.next = 14;
            break;
          case 13:
            setSeason(r.data);
          case 14:
          case "end":
            return _context8.stop();
        }
      }, _callee8);
    })), 60000);
    return function () {
      return clearInterval(id);
    };
  }, [season ? season.season_number : null]); // eslint-disable-line

  useEffect(function () {
    var classes = [bgClass, pageThemeClass].filter(Boolean).join(' ');
    document.body.className = classes;
    return function () {
      document.body.className = '';
    };
  }, [bgClass, pageThemeClass]);
  useEffect(function () {
    var canvas = canvasRef.current;
    if (canvas) drawWheel(canvas, wheelTheme);
  }, [wheelTheme]);
  var showToast = useCallback(function (msg) {
    setToast(msg);
    if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
    toastTimerRef.current = setTimeout(function () {
      return setToast(null);
    }, 3000);
  }, []);
  var handleBuy = useCallback(/*#__PURE__*/function () {
    var _ref30 = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee9(id) {
      var _yield$apiGame6, ok, data, _data$regen_recharge_;
      return _regeneratorRuntime().wrap(function _callee9$(_context9) {
        while (1) switch (_context9.prev = _context9.next) {
          case 0:
            _context9.next = 2;
            return apiGame('/api/buy', {
              method: 'POST',
              body: JSON.stringify({
                item_id: id
              })
            });
          case 2:
            _yield$apiGame6 = _context9.sent;
            ok = _yield$apiGame6.ok;
            data = _yield$apiGame6.data;
            if (ok) {
              setFishClicks(data.fish_clicks);
              if (data.wins != null) setWins(data.wins);
              if (data.losses != null) setLosses(data.losses);
              setOwnedItems(data.owned_items);
              setShieldCharges(data.shield_charges);
              setRegenRechargeWins((_data$regen_recharge_ = data.regen_recharge_wins) !== null && _data$regen_recharge_ !== void 0 ? _data$regen_recharge_ : 0);
              if (data.active_cosmetics) setActiveCosmetics(data.active_cosmetics);
              if (data.winmult_inf_level != null || data.bonusmult_inf_level != null || data.clickmult_inf_level != null || data.streak_armor_level != null) {
                setInfLevels(function (prev) {
                  var _data$winmult_inf_lev, _data$bonusmult_inf_l, _data$clickmult_inf_l, _data$streak_armor_le;
                  return {
                    winmult_inf: (_data$winmult_inf_lev = data.winmult_inf_level) !== null && _data$winmult_inf_lev !== void 0 ? _data$winmult_inf_lev : prev.winmult_inf,
                    bonusmult_inf: (_data$bonusmult_inf_l = data.bonusmult_inf_level) !== null && _data$bonusmult_inf_l !== void 0 ? _data$bonusmult_inf_l : prev.bonusmult_inf,
                    clickmult_inf: (_data$clickmult_inf_l = data.clickmult_inf_level) !== null && _data$clickmult_inf_l !== void 0 ? _data$clickmult_inf_l : prev.clickmult_inf,
                    streak_armor_inf: (_data$streak_armor_le = data.streak_armor_level) !== null && _data$streak_armor_le !== void 0 ? _data$streak_armor_le : prev.streak_armor_inf
                  };
                });
              }
            } else {
              showToast(data.error || 'Purchase failed');
            }
          case 6:
          case "end":
            return _context9.stop();
        }
      }, _callee9);
    }));
    return function (_x6) {
      return _ref30.apply(this, arguments);
    };
  }(), [showToast]);
  var handleEquip = useCallback(/*#__PURE__*/function () {
    var _ref31 = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee0(id) {
      var _yield$apiGame7, ok, data;
      return _regeneratorRuntime().wrap(function _callee0$(_context0) {
        while (1) switch (_context0.prev = _context0.next) {
          case 0:
            _context0.next = 2;
            return apiGame('/api/equip', {
              method: 'POST',
              body: JSON.stringify({
                fish_id: id
              })
            });
          case 2:
            _yield$apiGame7 = _context0.sent;
            ok = _yield$apiGame7.ok;
            data = _yield$apiGame7.data;
            if (ok) setEquippedFish(data.equipped_fish);else showToast(data.error || 'Equip failed');
          case 6:
          case "end":
            return _context0.stop();
        }
      }, _callee0);
    }));
    return function (_x7) {
      return _ref31.apply(this, arguments);
    };
  }(), [showToast]);
  var handleEquipCosmetic = useCallback(/*#__PURE__*/function () {
    var _ref32 = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee1(id) {
      var _yield$apiGame8, ok, data;
      return _regeneratorRuntime().wrap(function _callee1$(_context1) {
        while (1) switch (_context1.prev = _context1.next) {
          case 0:
            _context1.next = 2;
            return apiGame('/api/equip-cosmetic', {
              method: 'POST',
              body: JSON.stringify({
                item_id: id
              })
            });
          case 2:
            _yield$apiGame8 = _context1.sent;
            ok = _yield$apiGame8.ok;
            data = _yield$apiGame8.data;
            if (ok) setActiveCosmetics(data.active_cosmetics);else showToast(data.error || 'Equip failed');
          case 6:
          case "end":
            return _context1.stop();
        }
      }, _callee1);
    }));
    return function (_x8) {
      return _ref32.apply(this, arguments);
    };
  }(), [showToast]);
  var handleDiceRoll = useCallback(/*#__PURE__*/_asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee10() {
    var prevStreak, _yield$apiGame9, ok, data;
    return _regeneratorRuntime().wrap(function _callee10$(_context10) {
      while (1) switch (_context10.prev = _context10.next) {
        case 0:
          if (!(diceRolling || spinning)) {
            _context10.next = 2;
            break;
          }
          return _context10.abrupt("return");
        case 2:
          setDiceRolling(true);
          setDiceResult(null);
          prevStreak = streak;
          _context10.next = 7;
          return apiGame('/api/roll-dice', {
            method: 'POST',
            body: JSON.stringify({})
          });
        case 7:
          _yield$apiGame9 = _context10.sent;
          ok = _yield$apiGame9.ok;
          data = _yield$apiGame9.data;
          if (ok) {
            _context10.next = 14;
            break;
          }
          showToast(data.error || 'Roll failed');
          setDiceRolling(false);
          return _context10.abrupt("return");
        case 14:
          setTimeout(function () {
            var _data$die, _data$cursed_triple, _data$blessed_triple;
            var streakDelta = data.streak - prevStreak;
            setDiceResult({
              die1: data.die1,
              die2: data.die2,
              die3: (_data$die = data.die3) !== null && _data$die !== void 0 ? _data$die : null,
              dice_sum: data.dice_sum,
              streak_delta: streakDelta,
              cursed: data.cursed,
              blessed: data.blessed,
              cursed_triple: (_data$cursed_triple = data.cursed_triple) !== null && _data$cursed_triple !== void 0 ? _data$cursed_triple : false,
              blessed_triple: (_data$blessed_triple = data.blessed_triple) !== null && _data$blessed_triple !== void 0 ? _data$blessed_triple : false,
              streak_before: prevStreak,
              streak_after: data.streak
            });
            setStreak(data.streak);
            if (data.dice_charges != null) setDiceCharges(data.dice_charges);
            if (data.dice_last_recharge) setDiceLastRecharge(data.dice_last_recharge);
            setDiceRolledSinceSpin(true);
            setDiceRolling(false);
          }, lowSpec ? 100 : 1200);
        case 15:
        case "end":
          return _context10.stop();
      }
    }, _callee10);
  })), [diceRolling, spinning, streak, lowSpec, showToast]);

  // Shared post-spin state update (used both directly and via guard callback)
  var applySpinResult = useCallback(function (data) {
    var _data$regen_recharge_2, _data$regen_recharge_3;
    setResult(data.result);
    if (data.wins_delta) setWins(function (prev) {
      return prev + data.wins_delta;
    });
    if (data.losses_delta) setLosses(function (prev) {
      return prev + data.losses_delta;
    });
    setStreak(data.streak);
    setShieldCharges(data.shield_charges);
    setRegenRechargeWins((_data$regen_recharge_2 = data.regen_recharge_wins) !== null && _data$regen_recharge_2 !== void 0 ? _data$regen_recharge_2 : 0);
    if (data.owned_items) {
      var spinResult = new Set(data.owned_items);
      // Sync guard from spin result (can be removed by guard block, added by auto-guard).
      // All other items kept from prev to preserve mid-spin shop purchases.
      setOwnedItems(function (prev) {
        var withoutGuard = prev.filter(function (id) {
          return id !== 'guard';
        });
        return spinResult.has('guard') ? [].concat(_toConsumableArray(withoutGuard), ['guard']) : withoutGuard;
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
    if (data.wins_delta > 0) setWinCount(function (prev) {
      return prev + 1;
    });
    setShieldFeedback(data.shield_used ? {
      type: data.shield_used_type,
      broke: data.shield_broke,
      chargesLeft: data.shield_charges,
      rechargeWins: (_data$regen_recharge_3 = data.regen_recharge_wins) !== null && _data$regen_recharge_3 !== void 0 ? _data$regen_recharge_3 : 0
    } : data.guard_triggered && data.guard_blocked ? {
      type: 'guard',
      broke: true
    } : null);
    setShowResultSync(true);
    var cosm = activeCosmeticsRef.current;
    if (!lowSpecRef.current) {
      if (data.result === 'win' || data.guard_triggered && data.guard_blocked) {
        setConfetti(true);
      } else if (cosm.includes('party_mode')) {
        setConfetti(true);
      }
      if (confettiTimerRef.current) clearTimeout(confettiTimerRef.current);
      confettiTimerRef.current = setTimeout(function () {
        return setConfetti(false);
      }, 3500);
    }
    var mood = data.result === 'win' || data.guard_triggered && data.guard_blocked ? 'happy' : 'sad';
    setFishMood(mood);
    if (fishTimerRef.current) clearTimeout(fishTimerRef.current);
    fishTimerRef.current = setTimeout(function () {
      return setFishMood('idle');
    }, 2500);
    spinningRef.current = false;
    setSpinning(false);
  }, [showToast]);
  var spin = useCallback(/*#__PURE__*/_asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee11() {
    var data, res, base, segmentAngle, minTarget, newRotation;
    return _regeneratorRuntime().wrap(function _callee11$(_context11) {
      while (1) switch (_context11.prev = _context11.next) {
        case 0:
          if (!spinningRef.current) {
            _context11.next = 2;
            break;
          }
          return _context11.abrupt("return");
        case 2:
          if (showResultRef.current) {
            setHideResult(true);
            setShowResultSync(false);
            setConfetti(false);
            setTimeout(function () {
              setHideResult(false);
              setResult(null);
              setShieldFeedback(null);
            }, 350);
          }
          setBonusEarned(0);
          setEchoTriggered(false);
          setJackpotHit(false);
          setResilienceTriggered(false);
          setLuckySevenTriggered(false);
          setFortuneCharmTriggered(false);
          spinningRef.current = true;
          setSpinning(true);
          _context11.prev = 11;
          _context11.next = 14;
          return apiGame('/api/spin', {
            method: 'POST',
            body: JSON.stringify({
              tab_id: tabIdRef.current
            })
          });
        case 14:
          res = _context11.sent;
          if (res.ok) {
            _context11.next = 24;
            break;
          }
          spinningRef.current = false;
          setSpinning(false);
          if (!(res.status === 423)) {
            _context11.next = 22;
            break;
          }
          setTabLocked(true);
          setAutoSpin(false);
          return _context11.abrupt("return");
        case 22:
          if (autoSpinRef.current) setTimeout(function () {
            if (autoSpinRef.current) spin();
          }, 1000);
          return _context11.abrupt("return");
        case 24:
          setTabLocked(false);
          data = res.data;
          _context11.next = 34;
          break;
        case 28:
          _context11.prev = 28;
          _context11.t0 = _context11["catch"](11);
          spinningRef.current = false;
          setSpinning(false);
          if (autoSpinRef.current) setTimeout(function () {
            if (autoSpinRef.current) spin();
          }, 1000);
          return _context11.abrupt("return");
        case 34:
          base = currentRotationRef.current;
          segmentAngle = data.angle % 360;
          minTarget = base + 5 * 360;
          newRotation = Math.ceil((minTarget - segmentAngle) / 360) * 360 + segmentAngle;
          currentRotationRef.current = newRotation;
          setRotation(newRotation);
          setTimeout(function () {
            if (data.guard_triggered) {
              // Show guard wheel; defer result display until guard resolves
              setGuardState({
                blocked: data.guard_blocked
              });
              guardCompleteRef.current = function () {
                setGuardState(null);
                applySpinResult(data);
                if (autoSpinRef.current) {
                  var delay = Math.max(2000, autoSpinDelayRef.current);
                  setTimeout(function () {
                    if (autoSpinRef.current) {
                      setHideResult(true);
                      setTimeout(function () {
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
                var delay = data.shield_used ? Math.max(2000, autoSpinDelayRef.current) : Math.max(1500, autoSpinDelayRef.current);
                setTimeout(function () {
                  if (autoSpinRef.current) {
                    setHideResult(true);
                    setTimeout(function () {
                      setShowResultSync(false);
                      setHideResult(false);
                      setResult(null);
                      setShieldFeedback(null);
                      spin();
                      setTimeout(function () {
                        return setConfetti(false);
                      }, 3000);
                    }, 320);
                  }
                }, delay);
              }
            }
          }, spinSpeedRef.current * 1000 + 200);
        case 41:
        case "end":
          return _context11.stop();
      }
    }, _callee11, null, [[11, 28]]);
  })), [applySpinResult]);
  var handleSpinAgain = useCallback(function () {
    setHideResult(true);
    setTimeout(function () {
      setShowResultSync(false);
      setHideResult(false);
      setResult(null);
      setShieldFeedback(null);
      setConfetti(false);
      spin();
    }, 320);
  }, [spin]);
  var handleLogout = /*#__PURE__*/function () {
    var _ref35 = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee12() {
      return _regeneratorRuntime().wrap(function _callee12$(_context12) {
        while (1) switch (_context12.prev = _context12.next) {
          case 0:
            _context12.next = 2;
            return apiFetch('/api/logout', {
              method: 'POST',
              body: '{}'
            });
          case 2:
            onLogout();
          case 3:
          case "end":
            return _context12.stop();
        }
      }, _callee12);
    }));
    return function handleLogout() {
      return _ref35.apply(this, arguments);
    };
  }();
  var hasGuard = ownedItems.includes('guard');
  var hasRegen = ownedItems.includes('regen_shield');
  return /*#__PURE__*/React.createElement("div", {
    className: lowSpec ? 'low-spec' : ''
  }, /*#__PURE__*/React.createElement(StatsPanel, {
    open: showStats,
    onClose: function onClose() {
      return setShowStats(false);
    }
  }), toast && /*#__PURE__*/React.createElement("div", {
    className: "toast-notification"
  }, toast), tabLocked && /*#__PURE__*/React.createElement("div", {
    className: "tab-locked-banner"
  }, "This tab is locked \u2014 another tab is already active. Close it or wait 30s for the lock to expire."), /*#__PURE__*/React.createElement(Confetti, {
    active: confetti,
    count: confettiCount
  }), /*#__PURE__*/React.createElement("div", {
    className: "overlay ".concat(showResult ? 'active' : '')
  }), guardState && /*#__PURE__*/React.createElement(GuardWheel, {
    blocked: guardState.blocked,
    speedMult: guardSpeedMult,
    onComplete: function onComplete() {
      return guardCompleteRef.current && guardCompleteRef.current();
    }
  }), (!isMobile && showChat || isMobile && mobilePanel === 'chat') && /*#__PURE__*/React.createElement(ChatPanel, {
    extraClass: isMobile ? 'mobile-full' : '',
    onClose: isMobile ? null : function () {
      localStorage.setItem('chat_open', 'false');
      setShowChat(false);
    }
  }), /*#__PURE__*/React.createElement(FireEffect, {
    streak: streak,
    mode: fireMode,
    lowSpec: lowSpec
  }), /*#__PURE__*/React.createElement("div", {
    className: "user-bar"
  }, /*#__PURE__*/React.createElement("span", {
    className: "user-bar-name"
  }, "\uD83D\uDC64 ", username), /*#__PURE__*/React.createElement("button", {
    className: "stats-btn",
    title: "Stats",
    onClick: function onClick() {
      return setShowStats(true);
    }
  }, "\uD83D\uDCCA"), /*#__PURE__*/React.createElement("button", {
    className: "stats-btn",
    title: "Fish Encyclopaedia",
    onClick: function onClick() {
      return setShowEncyclopedia(true);
    }
  }, "\uD83D\uDCD6"), /*#__PURE__*/React.createElement("button", {
    className: "stats-btn",
    onClick: function onClick() {
      return setLowSpec(function (v) {
        return !v;
      });
    },
    title: lowSpec ? 'Low Spec Mode ON — click to restore animations' : 'Low Spec Mode OFF — click to reduce GPU usage',
    style: {
      opacity: lowSpec ? 1 : 0.5
    }
  }, "\u26A1"), !isMobile && /*#__PURE__*/React.createElement("button", {
    className: "stats-btn",
    onClick: function onClick() {
      return setShowChat(function (v) {
        localStorage.setItem('chat_open', !v);
        return !v;
      });
    },
    title: showChat ? 'Hide Chat' : 'Show Chat',
    style: {
      opacity: showChat ? 1 : 0.5
    }
  }, "\uD83D\uDCAC"), /*#__PURE__*/React.createElement("a", {
    className: "stats-btn",
    href: "https://github.com/Tom1tk/fishspin/wiki/Patch-Notes",
    target: "_blank",
    rel: "noopener noreferrer",
    title: "Patch Notes",
    style: {
      textDecoration: 'none'
    }
  }, "\uD83D\uDCCB"), /*#__PURE__*/React.createElement("button", {
    className: "logout-btn",
    onClick: handleLogout
  }, "Logout"), /*#__PURE__*/React.createElement(CommunityPot, {
    pot: communityPot,
    fishClicks: fishClicks,
    onContribute: function onContribute(newClicks) {
      return setFishClicks(newClicks);
    }
  }), season && /*#__PURE__*/React.createElement(SeasonInfo, {
    seasonNumber: season.season_number,
    endsAt: season.ends_at
  })), showEncyclopedia && /*#__PURE__*/React.createElement(FishEncyclopedia, {
    caughtSpecies: caughtSpecies,
    onClose: function onClose() {
      return setShowEncyclopedia(false);
    }
  }), !isMobile && /*#__PURE__*/React.createElement(FishingPanel, {
    fishClicks: fishClicks,
    fishData: getFishData(equippedFish),
    caughtSpecies: caughtSpecies,
    fishingLuckyNext: fishingLuckyNext,
    ownedItems: ownedItems,
    fishPanelScale: fishPanelScale,
    onFishBucksUpdate: function onFishBucksUpdate(v) {
      return setFishClicks(v);
    },
    onCaughtSpeciesUpdate: function onCaughtSpeciesUpdate(id) {
      return setCaughtSpecies(function (prev) {
        return prev.includes(id) ? prev : [].concat(_toConsumableArray(prev), [id]);
      });
    }
  }), isMobile && /*#__PURE__*/React.createElement("div", {
    className: "mobile-fish-panel".concat(mobilePanel === 'fish' ? ' mobile-visible' : '')
  }, /*#__PURE__*/React.createElement(FishingPanel, {
    fishClicks: fishClicks,
    fishData: getFishData(equippedFish),
    caughtSpecies: caughtSpecies,
    fishingLuckyNext: fishingLuckyNext,
    ownedItems: ownedItems,
    fishPanelScale: fishPanelScale,
    onFishBucksUpdate: function onFishBucksUpdate(v) {
      return setFishClicks(v);
    },
    onCaughtSpeciesUpdate: function onCaughtSpeciesUpdate(id) {
      return setCaughtSpecies(function (prev) {
        return prev.includes(id) ? prev : [].concat(_toConsumableArray(prev), [id]);
      });
    }
  }), /*#__PURE__*/React.createElement(CommunityPot, {
    pot: communityPot,
    fishClicks: fishClicks,
    onContribute: function onContribute(newClicks) {
      return setFishClicks(newClicks);
    }
  })), showResult && /*#__PURE__*/React.createElement("div", {
    className: "result-banner ".concat(showResult && !hideResult ? 'show' : '', " ").concat(hideResult ? 'hide' : '')
  }, result === 'win' || result === 'lose' && shieldFeedback ? /*#__PURE__*/React.createElement("div", {
    className: "result-text ".concat(result === 'win' ? 'win' : 'win')
  }, result === 'win' ? '🎰 YOU WIN! 🎰' : '🛡️ BLOCKED! 🛡️') : /*#__PURE__*/React.createElement("div", {
    className: "result-text lose"
  }, "\uD83D\uDC80 YOU LOSE \uD83D\uDC80"), jackpotHit && /*#__PURE__*/React.createElement("div", {
    className: "bonus-line jackpot-line"
  }, "\uD83C\uDFB0 JACKPOT! 25x multiplier applied!"), echoTriggered && !jackpotHit && /*#__PURE__*/React.createElement("div", {
    className: "bonus-line echo-line"
  }, "\uD83D\uDD0A WIN ECHO! Wins doubled!"), luckySevenTriggered && /*#__PURE__*/React.createElement("div", {
    className: "bonus-line lucky-seven-line"
  }, "7\uFE0F\u20E3 LUCKY SEVEN! Guaranteed win triggered!"), fortuneCharmTriggered && /*#__PURE__*/React.createElement("div", {
    className: "bonus-line fortune-charm-line"
  }, "\uD83C\uDF40 FORTUNE CHARM! +25% streak bonus applied!"), resilienceTriggered && /*#__PURE__*/React.createElement("div", {
    className: "bonus-line resilience-line"
  }, "\uD83D\uDCAA RESILIENCE! Streak -1 (not reset)"), bonusEarned > 0 && /*#__PURE__*/React.createElement("div", {
    className: "bonus-line"
  }, "\uD83D\uDD25 Streak Bonus +", fmt(bonusEarned), "!"), bonusEarned < 0 && /*#__PURE__*/React.createElement("div", {
    className: "bonus-line lose-bonus"
  }, "\uD83D\uDC80 Loss Streak +", fmt(Math.abs(bonusEarned)), " extra losses!"), shieldFeedback && function () {
    var names = {
      regen_shield: 'Regenerating Shield',
      guard: 'Guard'
    };
    var emojis = {
      regen_shield: '🔄',
      guard: '🛡️'
    };
    var name = names[shieldFeedback.type] || shieldFeedback.type;
    var emoji = emojis[shieldFeedback.type] || '🛡️';
    var sub = shieldFeedback.type === 'regen_shield' ? "Recharging\u2026 ".concat(shieldFeedback.rechargeWins, " win").concat(shieldFeedback.rechargeWins !== 1 ? 's' : '') : shieldFeedback.type === 'guard' ? 'Guard consumed' : null;
    return /*#__PURE__*/React.createElement("div", {
      className: "shield-feedback"
    }, /*#__PURE__*/React.createElement("div", {
      className: "shield-feedback-icon"
    }, emoji), /*#__PURE__*/React.createElement("div", {
      className: "shield-feedback-label"
    }, name, " Blocked!"), sub && /*#__PURE__*/React.createElement("div", {
      className: "shield-feedback-sub"
    }, sub));
  }(), /*#__PURE__*/React.createElement("button", {
    className: "spin-again-btn",
    onClick: handleSpinAgain
  }, "Spin Again")), /*#__PURE__*/React.createElement("div", {
    className: "main-layout-row"
  }, /*#__PURE__*/React.createElement("div", {
    className: "casino-container"
  }, /*#__PURE__*/React.createElement("div", {
    className: "bulbs"
  }, Array.from({
    length: 16
  }, function (_, i) {
    return /*#__PURE__*/React.createElement("div", {
      key: i,
      className: "bulb"
    });
  })), /*#__PURE__*/React.createElement("div", {
    className: "casino-header"
  }, /*#__PURE__*/React.createElement("div", {
    className: "casino-title"
  }, "Lucky Wheel"), /*#__PURE__*/React.createElement("div", {
    className: "subtitle"
  }, "Try Your Fortune")), /*#__PURE__*/React.createElement("div", {
    className: "wheel-wrapper ".concat(activeCosmetics.includes('golden_wheel') ? 'golden' : ''),
    onClick: !spinning && !autoSpin ? spin : undefined,
    title: autoSpin ? 'Auto-spin active' : 'Click to spin!'
  }, /*#__PURE__*/React.createElement("div", {
    className: "pointer ".concat(spinning ? 'spinning' : '')
  }), /*#__PURE__*/React.createElement("canvas", {
    ref: canvasRef,
    width: 380,
    height: 380,
    className: "wheel-canvas ".concat(spinning ? 'spinning' : ''),
    style: {
      transform: "rotate(".concat(rotation, "deg)"),
      transition: "transform ".concat(spinSpeed, "s cubic-bezier(0.17, 0.67, 0.12, 0.99)")
    }
  }), /*#__PURE__*/React.createElement("div", {
    className: "center-hub"
  }, "\u2605")), /*#__PURE__*/React.createElement("div", {
    className: "spin-prompt ".concat(spinning || autoSpin ? 'hidden' : ''),
    onClick: spin
  }, spinning || autoSpin ? '' : '▶ Click to Spin ◀'), /*#__PURE__*/React.createElement("label", {
    className: "autospin-row"
  }, /*#__PURE__*/React.createElement("input", {
    type: "checkbox",
    checked: autoSpin,
    onChange: function onChange(e) {
      return setAutoSpin(e.target.checked);
    }
  }), /*#__PURE__*/React.createElement("span", {
    className: "autospin-label"
  }, "Auto Spin")), /*#__PURE__*/React.createElement(Scoreboard, {
    wins: wins,
    losses: losses,
    lastResult: result
  }), isMobile && /*#__PURE__*/React.createElement("div", {
    className: "mobile-below-wheel"
  }, /*#__PURE__*/React.createElement(StreakPanel, {
    streak: streak,
    bonusmultLevel: infLevels.bonusmult_inf
  }), /*#__PURE__*/React.createElement(DicePanel, {
    streak: streak,
    onRoll: handleDiceRoll,
    rolling: diceRolling,
    diceResult: diceResult,
    spinning: spinning,
    guardSpinning: !!guardState,
    lowSpec: lowSpec,
    diceCharges: diceCharges,
    maxDiceCharges: diceMaxCharges,
    diceLastRecharge: diceLastRecharge,
    hasDiceExtra: ownedItems.includes('dice_extra'),
    rolledSinceSpin: diceRolledSinceSpin
  })), /*#__PURE__*/React.createElement("div", {
    className: "bulbs"
  }, Array.from({
    length: 16
  }, function (_, i) {
    return /*#__PURE__*/React.createElement("div", {
      key: i,
      className: "bulb"
    });
  })))), /*#__PURE__*/React.createElement("div", {
    className: "game-right".concat(isMobile && mobilePanel === 'shop' ? ' mobile-open' : '')
  }, /*#__PURE__*/React.createElement("button", {
    className: "shop-collapse-btn",
    onClick: function onClick() {
      return setShopCollapsed(function (c) {
        return !c;
      });
    },
    title: shopCollapsed ? 'Expand shop' : 'Collapse shop'
  }, shopCollapsed ? '‹' : '›'), /*#__PURE__*/React.createElement("div", {
    className: "game-right-body".concat(shopCollapsed ? ' shop-collapsed' : '')
  }, !isMobile && /*#__PURE__*/React.createElement("div", {
    className: "game-right-sidebar"
  }, (hasGuard || hasRegen) && /*#__PURE__*/React.createElement("div", {
    className: "shield-indicator"
  }, hasGuard && /*#__PURE__*/React.createElement("div", null, "\uD83D\uDEE1\uFE0F Guard ready"), hasRegen && /*#__PURE__*/React.createElement("div", null, regenRechargeWins > 0 ? "\uD83D\uDD04 ".concat(regenRechargeWins, " win").concat(regenRechargeWins !== 1 ? 's' : '') : '🔄 ready')), ownedItems.includes('lucky_seven') && /*#__PURE__*/React.createElement(LuckySevenCounter, {
    spinCount: spinCount
  }), /*#__PURE__*/React.createElement(StreakPanel, {
    streak: streak,
    bonusmultLevel: infLevels.bonusmult_inf
  }), /*#__PURE__*/React.createElement(DicePanel, {
    streak: streak,
    onRoll: handleDiceRoll,
    rolling: diceRolling,
    diceResult: diceResult,
    spinning: spinning,
    guardSpinning: !!guardState,
    lowSpec: lowSpec,
    diceCharges: diceCharges,
    maxDiceCharges: diceMaxCharges,
    diceLastRecharge: diceLastRecharge,
    hasDiceExtra: ownedItems.includes('dice_extra'),
    rolledSinceSpin: diceRolledSinceSpin
  })), /*#__PURE__*/React.createElement(ShopPanel, {
    fishClicks: fishClicks,
    wins: wins,
    losses: losses,
    ownedItems: ownedItems,
    equippedFish: equippedFish,
    activeCosmetics: activeCosmetics,
    infLevels: infLevels,
    onBuy: handleBuy,
    onEquip: handleEquip,
    onEquipCosmetic: handleEquipCosmetic,
    collapsed: shopCollapsed,
    winCount: winCount,
    caughtSpecies: caughtSpecies
  }))), /*#__PURE__*/React.createElement("div", {
    className: "bottom-left-stack"
  }, /*#__PURE__*/React.createElement("div", {
    className: "fish-counter"
  }, /*#__PURE__*/React.createElement("span", {
    className: "fish-counter-label"
  }, "Balance"), /*#__PURE__*/React.createElement("span", {
    className: "fish-counter-value"
  }, getFishData(equippedFish).emoji, " \xD7 ", fmt(fishClicks))), /*#__PURE__*/React.createElement(Leaderboard, {
    currentUser: username,
    extraClass: isMobile && mobilePanel === 'leaderboard' ? 'mobile-visible' : '',
    seasonWinners: season && season.latest_winners,
    seasonNumber: season && season.season_number - 1
  })), isMobile && mobilePanel && mobilePanel !== 'chat' && /*#__PURE__*/React.createElement("div", {
    className: "mobile-backdrop",
    onClick: function onClick() {
      return setMobilePanel(null);
    }
  }), /*#__PURE__*/React.createElement("div", {
    className: "mobile-toolbar"
  }, /*#__PURE__*/React.createElement("button", {
    className: "mobile-toolbar-btn".concat(mobilePanel === 'shop' ? ' active' : ''),
    onClick: function onClick() {
      return toggleMobilePanel('shop');
    },
    title: "Shop"
  }, "\uD83C\uDFEA"), /*#__PURE__*/React.createElement("button", {
    className: "mobile-toolbar-btn".concat(mobilePanel === 'leaderboard' ? ' active' : ''),
    onClick: function onClick() {
      return toggleMobilePanel('leaderboard');
    },
    title: "Leaderboard"
  }, "\uD83C\uDFC6"), /*#__PURE__*/React.createElement("button", {
    className: "mobile-toolbar-btn".concat(mobilePanel === 'fish' ? ' active' : ''),
    onClick: function onClick() {
      return toggleMobilePanel('fish');
    },
    title: "Fishing"
  }, "\uD83C\uDFA3"), /*#__PURE__*/React.createElement("button", {
    className: "mobile-toolbar-btn".concat(mobilePanel === 'chat' ? ' active' : ''),
    onClick: function onClick() {
      return toggleMobilePanel('chat');
    },
    title: "Chat"
  }, "\uD83D\uDCAC"), /*#__PURE__*/React.createElement("button", {
    className: "mobile-toolbar-btn",
    onClick: function onClick() {
      return setShowStats(true);
    },
    title: "Stats"
  }, "\uD83D\uDCCA")));
}

// ── Root App ───────────────────────────────────────────────────────────────
function App() {
  var _useState151 = useState(undefined),
    _useState152 = _slicedToArray(_useState151, 2),
    user = _useState152[0],
    setUser = _useState152[1];
  var _useState153 = useState(null),
    _useState154 = _slicedToArray(_useState153, 2),
    gameState = _useState154[0],
    setGameState = _useState154[1];
  var _useState155 = useState(''),
    _useState156 = _slicedToArray(_useState155, 2),
    sessionMsg = _useState156[0],
    setSessionMsg = _useState156[1];
  useEffect(function () {
    _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee13() {
      var _yield$apiFetch2, ok, data, gs;
      return _regeneratorRuntime().wrap(function _callee13$(_context13) {
        while (1) switch (_context13.prev = _context13.next) {
          case 0:
            _context13.next = 2;
            return apiFetch('/api/me');
          case 2:
            _yield$apiFetch2 = _context13.sent;
            ok = _yield$apiFetch2.ok;
            data = _yield$apiFetch2.data;
            if (!(ok && data.username)) {
              _context13.next = 12;
              break;
            }
            _context13.next = 8;
            return apiFetch('/api/state');
          case 8:
            gs = _context13.sent;
            if (gs.ok) {
              setGameState(gs.data);
              setUser(data.username);
            } else {
              setUser(null);
            }
            _context13.next = 13;
            break;
          case 12:
            setUser(null);
          case 13:
          case "end":
            return _context13.stop();
        }
      }, _callee13);
    }))();
  }, []);
  var handleAuth = /*#__PURE__*/function () {
    var _ref37 = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee14(username) {
      var gs;
      return _regeneratorRuntime().wrap(function _callee14$(_context14) {
        while (1) switch (_context14.prev = _context14.next) {
          case 0:
            _context14.next = 2;
            return apiFetch('/api/state');
          case 2:
            gs = _context14.sent;
            if (gs.ok) {
              setGameState(gs.data);
              setUser(username);
              setSessionMsg('');
            }
          case 4:
          case "end":
            return _context14.stop();
        }
      }, _callee14);
    }));
    return function handleAuth(_x9) {
      return _ref37.apply(this, arguments);
    };
  }();
  var handleLogout = function handleLogout() {
    setUser(null);
    setGameState(null);
    setSessionMsg('');
  };
  var handleSessionExpired = useCallback(function () {
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
