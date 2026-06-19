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
var _csrfToken = null;
function storeCsrf(data) {
  if (data && data.csrf_token) _csrfToken = data.csrf_token;
}
function apiFetch(_x) {
  return _apiFetch.apply(this, arguments);
}
function _apiFetch() {
  _apiFetch = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee35(path) {
    var opts,
      method,
      headers,
      res,
      json,
      _args35 = arguments;
    return _regeneratorRuntime().wrap(function _callee35$(_context35) {
      while (1) switch (_context35.prev = _context35.next) {
        case 0:
          opts = _args35.length > 1 && _args35[1] !== undefined ? _args35[1] : {};
          method = (opts.method || 'GET').toUpperCase();
          headers = {
            'Content-Type': 'application/json'
          };
          if (_csrfToken && method !== 'GET' && method !== 'HEAD') {
            headers['X-CSRFToken'] = _csrfToken;
          }
          _context35.next = 6;
          return fetch(path, _objectSpread({
            headers: headers
          }, opts));
        case 6:
          res = _context35.sent;
          _context35.next = 9;
          return res.json()["catch"](function () {
            return {};
          });
        case 9:
          json = _context35.sent;
          return _context35.abrupt("return", {
            ok: res.ok,
            status: res.status,
            data: json
          });
        case 11:
        case "end":
          return _context35.stop();
      }
    }, _callee35);
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

// ── Wormhole Background Components ───────────────────────────────────────────

function WormholeBackground(_ref2) {
  var _ref2$className = _ref2.className,
    className = _ref2$className === void 0 ? "" : _ref2$className,
    _ref2$intensity = _ref2.intensity,
    intensity = _ref2$intensity === void 0 ? 1 : _ref2$intensity,
    _ref2$speed = _ref2.speed,
    speed = _ref2$speed === void 0 ? 1 : _ref2$speed,
    _ref2$starCount = _ref2.starCount,
    starCount = _ref2$starCount === void 0 ? 950 : _ref2$starCount,
    _ref2$streakCount = _ref2.streakCount,
    streakCount = _ref2$streakCount === void 0 ? 240 : _ref2$streakCount,
    _ref2$nebulaStrength = _ref2.nebulaStrength,
    nebulaStrength = _ref2$nebulaStrength === void 0 ? 0.95 : _ref2$nebulaStrength,
    _ref2$starDriftSpeed = _ref2.starDriftSpeed,
    starDriftSpeed = _ref2$starDriftSpeed === void 0 ? 0.18 : _ref2$starDriftSpeed,
    _ref2$parallaxStrengt = _ref2.parallaxStrength,
    parallaxStrength = _ref2$parallaxStrengt === void 0 ? 28 : _ref2$parallaxStrengt,
    _ref2$parallaxSmoothi = _ref2.parallaxSmoothing,
    parallaxSmoothing = _ref2$parallaxSmoothi === void 0 ? 0.065 : _ref2$parallaxSmoothi,
    _ref2$parallax = _ref2.parallax,
    parallax = _ref2$parallax === void 0 ? false : _ref2$parallax,
    _ref2$static = _ref2["static"],
    staticMode = _ref2$static === void 0 ? false : _ref2$static;
  var canvasRef = useRef(null);
  var animationRef = useRef(0);
  var parallaxRef = useRef({
    currentX: 0,
    currentY: 0,
    targetX: 0,
    targetY: 0
  });
  useEffect(function () {
    var canvas = canvasRef.current;
    if (!canvas) return;
    var ctx = canvas.getContext("2d", {
      alpha: true
    });
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    var width = 0,
      height = 0,
      cx = 0,
      cy = 0;
    var lastTime = performance.now(),
      time = 0;
    var lerp = function lerp(a, b, t) {
      return a + (b - a) * t;
    };
    var clamp = function clamp(v, min, max) {
      return Math.max(min, Math.min(max, v));
    };
    var rand = function rand(min, max) {
      return Math.random() * (max - min) + min;
    };
    var rgba = function rgba(r, g, b, a) {
      return "rgba(".concat(r, ", ").concat(g, ", ").concat(b, ", ").concat(a, ")");
    };
    var depth = {
      background: 0.16,
      vignette: 0.2,
      focal: 0.12,
      nebula: 0.3,
      slowStars: 0.62,
      streaks: 1.0
    };
    var movingStars = [],
      streaks = [];
    function createMovingStar() {
      var index = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : 0;
      var colourBand = Math.random();
      return {
        angle: rand(0, Math.PI * 2),
        z: Math.pow(Math.random(), 0.55),
        speed: rand(0.0012, 0.0045) * speed * starDriftSpeed * (0.75 + intensity * 0.45),
        size: rand(0.45, 1.7),
        alpha: rand(0.18, 0.95),
        twinkle: rand(0.35, 2.1),
        phase: rand(0, Math.PI * 2),
        colour: colourBand < 0.48 ? [165, 215, 255] : colourBand < 0.82 ? [255, 240, 255] : [255, 185, 235],
        seed: index + Math.random() * 1000
      };
    }
    function createStars() {
      movingStars.length = 0;
      var total = Math.floor(starCount * intensity);
      for (var i = 0; i < total; i++) movingStars.push(createMovingStar(i));
    }
    function createStreak() {
      var index = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : 0;
      var angleJitter = rand(-0.3, 0.3);
      var baseAngle = Math.atan2(rand(-height * 0.55, height * 0.55), rand(-width * 0.55, width * 0.55));
      var hueWeight = Math.random();
      return {
        angle: baseAngle + angleJitter,
        z: rand(0.02, 1),
        speed: rand(0.003, 0.018) * speed * (0.8 + intensity * 0.65),
        width: rand(0.5, 2.6),
        length: rand(22, 180),
        alpha: rand(0.12, 0.85),
        drift: rand(-0.12, 0.12),
        pulse: rand(0.5, 2.3),
        pulseOffset: rand(0, Math.PI * 2),
        colour: hueWeight < 0.18 ? [255, 255, 255] : hueWeight < 0.39 ? [95, 205, 255] : hueWeight < 0.56 ? [0, 255, 220] : hueWeight < 0.68 ? [120, 255, 160] : hueWeight < 0.84 ? [255, 90, 210] : [165, 110, 255],
        seed: index + Math.random() * 1000
      };
    }
    function createStreaks() {
      streaks.length = 0;
      var total = Math.floor(streakCount * intensity);
      for (var i = 0; i < total; i++) streaks.push(createStreak(i));
    }
    function resize() {
      var rect = canvas.getBoundingClientRect();
      width = Math.max(1, Math.floor(rect.width || window.innerWidth));
      height = Math.max(1, Math.floor(rect.height || window.innerHeight));
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
      canvas.style.width = "".concat(width, "px");
      canvas.style.height = "".concat(height, "px");
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      cx = width * 0.5;
      cy = height * 0.5;
      createStars();
      createStreaks();
    }
    function drawBackgroundGradient() {
      var bg = ctx.createLinearGradient(0, 0, width, height);
      bg.addColorStop(0, "rgba(2,6,18,1)");
      bg.addColorStop(0.28, "rgba(5,12,30,1)");
      bg.addColorStop(0.55, "rgba(9,8,24,1)");
      bg.addColorStop(0.78, "rgba(20,7,28,1)");
      bg.addColorStop(1, "rgba(6,2,12,1)");
      ctx.fillStyle = bg;
      ctx.fillRect(0, 0, width, height);
    }
    function drawNebulaClouds(t) {
      ctx.save();
      ctx.globalCompositeOperation = "screen";
      var leftGrad = ctx.createRadialGradient(width * 0.18, height * 0.48, 10, width * 0.18, height * 0.48, width * 0.55);
      leftGrad.addColorStop(0, "rgba(40,140,255,".concat(0.18 * nebulaStrength, ")"));
      leftGrad.addColorStop(0.28, "rgba(20,105,230,".concat(0.12 * nebulaStrength, ")"));
      leftGrad.addColorStop(0.62, "rgba(8,42,120,".concat(0.09 * nebulaStrength, ")"));
      leftGrad.addColorStop(1, "rgba(0,0,0,0)");
      ctx.fillStyle = leftGrad;
      ctx.fillRect(0, 0, width, height);
      var rightGrad = ctx.createRadialGradient(width * 0.8, height * 0.5, 12, width * 0.8, height * 0.5, width * 0.48);
      rightGrad.addColorStop(0, "rgba(255,100,230,".concat(0.2 * nebulaStrength, ")"));
      rightGrad.addColorStop(0.34, "rgba(175,70,255,".concat(0.14 * nebulaStrength, ")"));
      rightGrad.addColorStop(0.7, "rgba(95,25,160,".concat(0.08 * nebulaStrength, ")"));
      rightGrad.addColorStop(1, "rgba(0,0,0,0)");
      ctx.fillStyle = rightGrad;
      ctx.fillRect(0, 0, width, height);
      var blobs = [{
        x: width * 0.16,
        y: height * 0.33,
        rx: width * 0.28,
        ry: height * 0.16,
        c1: "rgba(80,180,255,0.06)",
        c2: "rgba(20,40,100,0)"
      }, {
        x: width * 0.26,
        y: height * 0.72,
        rx: width * 0.24,
        ry: height * 0.12,
        c1: "rgba(0,190,255,0.05)",
        c2: "rgba(0,0,0,0)"
      }, {
        x: width * 0.78,
        y: height * 0.33,
        rx: width * 0.22,
        ry: height * 0.14,
        c1: "rgba(255,90,200,0.07)",
        c2: "rgba(0,0,0,0)"
      }, {
        x: width * 0.86,
        y: height * 0.66,
        rx: width * 0.26,
        ry: height * 0.16,
        c1: "rgba(180,70,255,0.08)",
        c2: "rgba(0,0,0,0)"
      }];
      blobs.forEach(function (b, i) {
        var driftX = Math.sin(t * 0.00018 + i * 1.7) * 18,
          driftY = Math.cos(t * 0.00012 + i * 1.3) * 12;
        var g = ctx.createRadialGradient(b.x + driftX, b.y + driftY, 0, b.x + driftX, b.y + driftY, Math.max(b.rx, b.ry));
        g.addColorStop(0, b.c1);
        g.addColorStop(1, b.c2);
        ctx.save();
        ctx.translate(b.x + driftX, b.y + driftY);
        ctx.scale(1, b.ry / b.rx);
        ctx.beginPath();
        ctx.arc(0, 0, b.rx, 0, Math.PI * 2);
        ctx.closePath();
        ctx.fillStyle = g;
        ctx.fill();
        ctx.restore();
      });
      ctx.restore();
    }
    function drawSlowMovingStars(t) {
      ctx.save();
      ctx.globalCompositeOperation = "screen";
      var maxRadius = Math.hypot(width, height) * 0.77;
      for (var i = 0; i < movingStars.length; i++) {
        var s = movingStars[i];
        s.z += s.speed;
        if (s.z > 1.03) {
          movingStars[i] = createMovingStar(i + t * 0.001);
          movingStars[i].z = rand(0.01, 0.08);
          continue;
        }
        var eased = s.z * s.z;
        var radius = lerp(0, maxRadius, eased);
        var x = cx + Math.cos(s.angle) * radius,
          y = cy + Math.sin(s.angle) * radius;
        if (x < -20 || x > width + 20 || y < -20 || y > height + 20) {
          movingStars[i] = createMovingStar(i + t * 0.001);
          movingStars[i].z = rand(0.01, 0.08);
          continue;
        }
        var pulse = 0.78 + 0.22 * Math.sin(t * 0.0012 * s.twinkle + s.phase);
        var alpha = clamp(s.alpha * (0.35 + eased * 0.95) * pulse, 0.05, 1);
        var radiusPx = s.size * (0.65 + eased * 1.15);
        var _s$colour = _slicedToArray(s.colour, 3),
          r = _s$colour[0],
          g = _s$colour[1],
          b = _s$colour[2];
        ctx.fillStyle = rgba(r, g, b, alpha);
        ctx.beginPath();
        ctx.arc(x, y, radiusPx, 0, Math.PI * 2);
        ctx.fill();
        if (radiusPx > 1.2) {
          ctx.strokeStyle = rgba(255, 255, 255, alpha * 0.18);
          ctx.lineWidth = 0.55;
          ctx.beginPath();
          ctx.moveTo(x - radiusPx * 1.8, y);
          ctx.lineTo(x + radiusPx * 1.8, y);
          ctx.moveTo(x, y - radiusPx * 1.8);
          ctx.lineTo(x, y + radiusPx * 1.8);
          ctx.stroke();
        }
      }
      ctx.restore();
    }
    function drawStreaks(t) {
      ctx.save();
      ctx.globalCompositeOperation = "lighter";
      ctx.lineCap = "round";
      var maxRadius = Math.hypot(width, height) * 0.75;
      for (var i = 0; i < streaks.length; i++) {
        var s = streaks[i];
        s.z += s.speed;
        if (s.z > 1.02) {
          streaks[i] = createStreak(i + t * 0.001);
          continue;
        }
        var eased = s.z * s.z;
        var radius = lerp(6, maxRadius, eased);
        var angle = s.angle + Math.sin(t * 0.0004 * s.pulse + s.pulseOffset) * s.drift * 0.18;
        var x = cx + Math.cos(angle) * radius,
          y = cy + Math.sin(angle) * radius;
        var dirX = x - cx,
          dirY = y - cy,
          dirLen = Math.max(1, Math.hypot(dirX, dirY));
        var ux = dirX / dirLen,
          uy = dirY / dirLen;
        var trail = s.length * (0.18 + eased * 1.75);
        var x2 = x - ux * trail,
          y2 = y - uy * trail;
        var _s$colour2 = _slicedToArray(s.colour, 3),
          r = _s$colour2[0],
          g = _s$colour2[1],
          b = _s$colour2[2];
        var glow = clamp(s.alpha * (0.3 + eased * 1.15), 0.05, 1);
        var grad = ctx.createLinearGradient(x2, y2, x, y);
        grad.addColorStop(0, rgba(255, 255, 255, 0));
        grad.addColorStop(0.45, rgba(r, g, b, glow * 0.33));
        grad.addColorStop(1, rgba(r, g, b, glow));
        ctx.strokeStyle = grad;
        ctx.lineWidth = s.width * (0.3 + eased * 1.4);
        ctx.beginPath();
        ctx.moveTo(x2, y2);
        ctx.lineTo(x, y);
        ctx.stroke();
      }
      ctx.restore();
    }
    function buildSparklePath(sizeOuter, sizeInner) {
      ctx.beginPath();
      ctx.moveTo(cx, cy - sizeOuter);
      ctx.quadraticCurveTo(cx + sizeInner * 0.45, cy - sizeInner * 0.75, cx + sizeOuter, cy);
      ctx.quadraticCurveTo(cx + sizeInner * 0.75, cy + sizeInner * 0.45, cx, cy + sizeOuter);
      ctx.quadraticCurveTo(cx - sizeInner * 0.45, cy + sizeInner * 0.75, cx - sizeOuter, cy);
      ctx.quadraticCurveTo(cx - sizeInner * 0.75, cy - sizeInner * 0.45, cx, cy - sizeOuter);
      ctx.closePath();
    }
    function drawCentreFlare(t) {
      ctx.save();
      ctx.globalCompositeOperation = "screen";
      var pulse = 0.94 + Math.sin(t * 0.0034) * 0.05 + Math.sin(t * 0.0017) * 0.035;
      var minSide = Math.min(width, height);
      var outerGlow = ctx.createRadialGradient(cx, cy, 0, cx, cy, minSide * 0.24);
      outerGlow.addColorStop(0, rgba(255, 255, 255, 0.46 * pulse));
      outerGlow.addColorStop(0.08, rgba(210, 235, 255, 0.22 * pulse));
      outerGlow.addColorStop(0.18, rgba(255, 160, 235, 0.16 * pulse));
      outerGlow.addColorStop(0.28, rgba(120, 180, 255, 0.11 * pulse));
      outerGlow.addColorStop(1, rgba(0, 0, 0, 0));
      ctx.fillStyle = outerGlow;
      ctx.beginPath();
      ctx.arc(cx, cy, minSide * 0.24, 0, Math.PI * 2);
      ctx.fill();
      var starOuter = clamp(minSide * 0.078 * pulse, 36, 82),
        starInner = starOuter * 0.34;
      var starGlowA = ctx.createRadialGradient(cx, cy, 0, cx, cy, starOuter * 1.45);
      starGlowA.addColorStop(0, rgba(255, 255, 255, 0.78));
      starGlowA.addColorStop(0.42, rgba(255, 245, 255, 0.28));
      starGlowA.addColorStop(0.7, rgba(255, 170, 235, 0.16));
      starGlowA.addColorStop(1, rgba(0, 0, 0, 0));
      ctx.fillStyle = starGlowA;
      buildSparklePath(starOuter * 1.22, starInner * 1.22);
      ctx.fill();
      var starFill = ctx.createRadialGradient(cx, cy, 0, cx, cy, starOuter);
      starFill.addColorStop(0, rgba(255, 255, 255, 1));
      starFill.addColorStop(0.28, rgba(255, 255, 255, 0.96));
      starFill.addColorStop(0.62, rgba(255, 230, 245, 0.82));
      starFill.addColorStop(0.86, rgba(190, 225, 255, 0.52));
      starFill.addColorStop(1, rgba(160, 215, 255, 0.18));
      ctx.fillStyle = starFill;
      buildSparklePath(starOuter, starInner);
      ctx.fill();
      ctx.strokeStyle = rgba(255, 255, 255, 0.28);
      ctx.lineWidth = 1.1;
      buildSparklePath(starOuter, starInner);
      ctx.stroke();
      var verticalH = Math.min(height * 0.42, 360),
        verticalW = Math.max(6, Math.min(width * 0.014, 16));
      var vertFlare = ctx.createLinearGradient(cx, cy - verticalH * 0.5, cx, cy + verticalH * 0.5);
      vertFlare.addColorStop(0, rgba(255, 255, 255, 0));
      vertFlare.addColorStop(0.18, rgba(255, 185, 235, 0.22));
      vertFlare.addColorStop(0.5, rgba(255, 255, 255, 0.78));
      vertFlare.addColorStop(0.82, rgba(180, 215, 255, 0.22));
      vertFlare.addColorStop(1, rgba(255, 255, 255, 0));
      ctx.fillStyle = vertFlare;
      ctx.fillRect(cx - verticalW * 0.5, cy - verticalH * 0.5, verticalW, verticalH);
      var horizontalW = width * 0.7;
      var horizFlare = ctx.createLinearGradient(cx - horizontalW * 0.5, cy, cx + horizontalW * 0.5, cy);
      horizFlare.addColorStop(0, rgba(255, 255, 255, 0));
      horizFlare.addColorStop(0.2, rgba(90, 165, 255, 0.05));
      horizFlare.addColorStop(0.42, rgba(255, 180, 235, 0.12));
      horizFlare.addColorStop(0.5, rgba(255, 255, 255, 0.34));
      horizFlare.addColorStop(0.58, rgba(190, 220, 255, 0.12));
      horizFlare.addColorStop(0.8, rgba(255, 120, 220, 0.05));
      horizFlare.addColorStop(1, rgba(255, 255, 255, 0));
      ctx.fillStyle = horizFlare;
      ctx.fillRect(cx - horizontalW * 0.5, cy - 2.5, horizontalW, 5);
      var innerGlow = ctx.createRadialGradient(cx, cy, 0, cx, cy, starOuter * 0.9);
      innerGlow.addColorStop(0, rgba(255, 255, 255, 0.96));
      innerGlow.addColorStop(0.35, rgba(255, 255, 255, 0.55));
      innerGlow.addColorStop(0.8, rgba(180, 225, 255, 0.12));
      innerGlow.addColorStop(1, rgba(0, 0, 0, 0));
      ctx.fillStyle = innerGlow;
      ctx.beginPath();
      ctx.arc(cx, cy, starOuter * 0.9, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }
    function drawVignette() {
      var vig = ctx.createRadialGradient(cx, cy, Math.min(width, height) * 0.2, cx, cy, Math.max(width, height) * 0.8);
      vig.addColorStop(0, "rgba(0,0,0,0)");
      vig.addColorStop(0.65, "rgba(0,0,0,0.08)");
      vig.addColorStop(1, "rgba(0,0,0,0.42)");
      ctx.fillStyle = vig;
      ctx.fillRect(0, 0, width, height);
    }
    function onPointerMove(event) {
      var rect = canvas.getBoundingClientRect();
      var xNorm = rect.width > 0 ? (event.clientX - rect.left) / rect.width * 2 - 1 : 0;
      var yNorm = rect.height > 0 ? (event.clientY - rect.top) / rect.height * 2 - 1 : 0;
      parallaxRef.current.targetX = clamp(xNorm, -1, 1) * parallaxStrength;
      parallaxRef.current.targetY = clamp(yNorm, -1, 1) * parallaxStrength;
    }
    function onPointerLeave() {
      parallaxRef.current.targetX = 0;
      parallaxRef.current.targetY = 0;
    }
    function updateParallax() {
      var p = parallaxRef.current;
      p.currentX = lerp(p.currentX, p.targetX, parallaxSmoothing);
      p.currentY = lerp(p.currentY, p.targetY, parallaxSmoothing);
      return p;
    }
    function drawBackgroundGradientP(p) {
      var shiftX = p.currentX * depth.background,
        shiftY = p.currentY * depth.background;
      var bg = ctx.createLinearGradient(shiftX * 0.8, shiftY * 0.8, width + shiftX * 0.5, height + shiftY * 0.5);
      bg.addColorStop(0, "rgba(2,6,18,1)");
      bg.addColorStop(0.28, "rgba(5,12,30,1)");
      bg.addColorStop(0.55, "rgba(9,8,24,1)");
      bg.addColorStop(0.78, "rgba(20,7,28,1)");
      bg.addColorStop(1, "rgba(6,2,12,1)");
      ctx.fillStyle = bg;
      ctx.fillRect(0, 0, width, height);
    }
    function drawNebulaCloudsP(t, p) {
      ctx.save();
      ctx.globalCompositeOperation = "screen";
      var nx = p.currentX * depth.nebula,
        ny = p.currentY * depth.nebula;
      var leftGrad = ctx.createRadialGradient(width * 0.18 + nx, height * 0.48 + ny, 10, width * 0.18 + nx, height * 0.48 + ny, width * 0.55);
      leftGrad.addColorStop(0, "rgba(40,140,255,".concat(0.18 * nebulaStrength, ")"));
      leftGrad.addColorStop(0.28, "rgba(20,105,230,".concat(0.12 * nebulaStrength, ")"));
      leftGrad.addColorStop(0.62, "rgba(8,42,120,".concat(0.09 * nebulaStrength, ")"));
      leftGrad.addColorStop(1, "rgba(0,0,0,0)");
      ctx.fillStyle = leftGrad;
      ctx.fillRect(0, 0, width, height);
      var rightGrad = ctx.createRadialGradient(width * 0.8 + nx, height * 0.5 + ny, 12, width * 0.8 + nx, height * 0.5 + ny, width * 0.48);
      rightGrad.addColorStop(0, "rgba(255,100,230,".concat(0.2 * nebulaStrength, ")"));
      rightGrad.addColorStop(0.34, "rgba(175,70,255,".concat(0.14 * nebulaStrength, ")"));
      rightGrad.addColorStop(0.7, "rgba(95,25,160,".concat(0.08 * nebulaStrength, ")"));
      rightGrad.addColorStop(1, "rgba(0,0,0,0)");
      ctx.fillStyle = rightGrad;
      ctx.fillRect(0, 0, width, height);
      var blobs = [{
        x: width * 0.16,
        y: height * 0.33,
        rx: width * 0.28,
        ry: height * 0.16,
        c1: "rgba(80,180,255,0.06)",
        c2: "rgba(20,40,100,0)"
      }, {
        x: width * 0.26,
        y: height * 0.72,
        rx: width * 0.24,
        ry: height * 0.12,
        c1: "rgba(0,190,255,0.05)",
        c2: "rgba(0,0,0,0)"
      }, {
        x: width * 0.78,
        y: height * 0.33,
        rx: width * 0.22,
        ry: height * 0.14,
        c1: "rgba(255,90,200,0.07)",
        c2: "rgba(0,0,0,0)"
      }, {
        x: width * 0.86,
        y: height * 0.66,
        rx: width * 0.26,
        ry: height * 0.16,
        c1: "rgba(180,70,255,0.08)",
        c2: "rgba(0,0,0,0)"
      }];
      blobs.forEach(function (b, i) {
        var driftX = Math.sin(t * 0.00018 + i * 1.7) * 18 + nx,
          driftY = Math.cos(t * 0.00012 + i * 1.3) * 12 + ny;
        var g = ctx.createRadialGradient(b.x + driftX, b.y + driftY, 0, b.x + driftX, b.y + driftY, Math.max(b.rx, b.ry));
        g.addColorStop(0, b.c1);
        g.addColorStop(1, b.c2);
        ctx.save();
        ctx.translate(b.x + driftX, b.y + driftY);
        ctx.scale(1, b.ry / b.rx);
        ctx.beginPath();
        ctx.arc(0, 0, b.rx, 0, Math.PI * 2);
        ctx.closePath();
        ctx.fillStyle = g;
        ctx.fill();
        ctx.restore();
      });
      ctx.restore();
    }
    function drawSlowMovingStarsP(t, p) {
      ctx.save();
      ctx.globalCompositeOperation = "screen";
      var maxRadius = Math.hypot(width, height) * 0.77;
      var povX = cx + p.currentX * depth.slowStars,
        povY = cy + p.currentY * depth.slowStars;
      for (var i = 0; i < movingStars.length; i++) {
        var s = movingStars[i];
        s.z += s.speed;
        if (s.z > 1.03) {
          movingStars[i] = createMovingStar(i + t * 0.001);
          movingStars[i].z = rand(0.01, 0.08);
          continue;
        }
        var eased = s.z * s.z,
          radius = lerp(0, maxRadius, eased);
        var x = povX + Math.cos(s.angle) * radius,
          y = povY + Math.sin(s.angle) * radius;
        if (x < -20 || x > width + 20 || y < -20 || y > height + 20) {
          movingStars[i] = createMovingStar(i + t * 0.001);
          movingStars[i].z = rand(0.01, 0.08);
          continue;
        }
        var pulse = 0.78 + 0.22 * Math.sin(t * 0.0012 * s.twinkle + s.phase);
        var alpha = clamp(s.alpha * (0.35 + eased * 0.95) * pulse, 0.05, 1);
        var radiusPx = s.size * (0.65 + eased * 1.15);
        var _s$colour3 = _slicedToArray(s.colour, 3),
          r = _s$colour3[0],
          g = _s$colour3[1],
          b = _s$colour3[2];
        ctx.fillStyle = rgba(r, g, b, alpha);
        ctx.beginPath();
        ctx.arc(x, y, radiusPx, 0, Math.PI * 2);
        ctx.fill();
        if (radiusPx > 1.2) {
          ctx.strokeStyle = rgba(255, 255, 255, alpha * 0.18);
          ctx.lineWidth = 0.55;
          ctx.beginPath();
          ctx.moveTo(x - radiusPx * 1.8, y);
          ctx.lineTo(x + radiusPx * 1.8, y);
          ctx.moveTo(x, y - radiusPx * 1.8);
          ctx.lineTo(x, y + radiusPx * 1.8);
          ctx.stroke();
        }
      }
      ctx.restore();
    }
    function drawStreaksP(t, p) {
      ctx.save();
      ctx.globalCompositeOperation = "lighter";
      ctx.lineCap = "round";
      var maxRadius = Math.hypot(width, height) * 0.75;
      var povX = cx + p.currentX * depth.streaks,
        povY = cy + p.currentY * depth.streaks;
      for (var i = 0; i < streaks.length; i++) {
        var s = streaks[i];
        s.z += s.speed;
        if (s.z > 1.02) {
          streaks[i] = createStreak(i + t * 0.001);
          continue;
        }
        var eased = s.z * s.z,
          radius = lerp(6, maxRadius, eased);
        var angle = s.angle + Math.sin(t * 0.0004 * s.pulse + s.pulseOffset) * s.drift * 0.18;
        var x = povX + Math.cos(angle) * radius,
          y = povY + Math.sin(angle) * radius;
        var dirX = x - povX,
          dirY = y - povY,
          dirLen = Math.max(1, Math.hypot(dirX, dirY));
        var ux = dirX / dirLen,
          uy = dirY / dirLen;
        var trail = s.length * (0.18 + eased * 1.75);
        var x2 = x - ux * trail,
          y2 = y - uy * trail;
        var _s$colour4 = _slicedToArray(s.colour, 3),
          r = _s$colour4[0],
          g = _s$colour4[1],
          b = _s$colour4[2],
          glow = clamp(s.alpha * (0.3 + eased * 1.15), 0.05, 1);
        var grad = ctx.createLinearGradient(x2, y2, x, y);
        grad.addColorStop(0, rgba(255, 255, 255, 0));
        grad.addColorStop(0.45, rgba(r, g, b, glow * 0.33));
        grad.addColorStop(1, rgba(r, g, b, glow));
        ctx.strokeStyle = grad;
        ctx.lineWidth = s.width * (0.3 + eased * 1.4);
        ctx.beginPath();
        ctx.moveTo(x2, y2);
        ctx.lineTo(x, y);
        ctx.stroke();
      }
      ctx.restore();
    }
    function buildSparklePathP(x, y, sizeOuter, sizeInner) {
      ctx.beginPath();
      ctx.moveTo(x, y - sizeOuter);
      ctx.quadraticCurveTo(x + sizeInner * 0.45, y - sizeInner * 0.75, x + sizeOuter, y);
      ctx.quadraticCurveTo(x + sizeInner * 0.75, y + sizeInner * 0.45, x, y + sizeOuter);
      ctx.quadraticCurveTo(x - sizeInner * 0.45, y + sizeInner * 0.75, x - sizeOuter, y);
      ctx.quadraticCurveTo(x - sizeInner * 0.75, y - sizeInner * 0.45, x, y - sizeOuter);
      ctx.closePath();
    }
    function drawCentreFlareP(t, p) {
      ctx.save();
      ctx.globalCompositeOperation = "screen";
      var focalX = cx + p.currentX * depth.focal,
        focalY = cy + p.currentY * depth.focal;
      var pulse = 0.94 + Math.sin(t * 0.0034) * 0.05 + Math.sin(t * 0.0017) * 0.035;
      var minSide = Math.min(width, height);
      var outerGlow = ctx.createRadialGradient(focalX, focalY, 0, focalX, focalY, minSide * 0.24);
      outerGlow.addColorStop(0, rgba(255, 255, 255, 0.46 * pulse));
      outerGlow.addColorStop(0.08, rgba(210, 235, 255, 0.22 * pulse));
      outerGlow.addColorStop(0.18, rgba(255, 160, 235, 0.16 * pulse));
      outerGlow.addColorStop(0.28, rgba(120, 180, 255, 0.11 * pulse));
      outerGlow.addColorStop(1, rgba(0, 0, 0, 0));
      ctx.fillStyle = outerGlow;
      ctx.beginPath();
      ctx.arc(focalX, focalY, minSide * 0.24, 0, Math.PI * 2);
      ctx.fill();
      var starOuter = clamp(minSide * 0.078 * pulse, 36, 82),
        starInner = starOuter * 0.34;
      var starGlowA = ctx.createRadialGradient(focalX, focalY, 0, focalX, focalY, starOuter * 1.45);
      starGlowA.addColorStop(0, rgba(255, 255, 255, 0.78));
      starGlowA.addColorStop(0.42, rgba(255, 245, 255, 0.28));
      starGlowA.addColorStop(0.7, rgba(255, 170, 235, 0.16));
      starGlowA.addColorStop(1, rgba(0, 0, 0, 0));
      ctx.fillStyle = starGlowA;
      buildSparklePathP(focalX, focalY, starOuter * 1.22, starInner * 1.22);
      ctx.fill();
      var starFill = ctx.createRadialGradient(focalX, focalY, 0, focalX, focalY, starOuter);
      starFill.addColorStop(0, rgba(255, 255, 255, 1));
      starFill.addColorStop(0.28, rgba(255, 255, 255, 0.96));
      starFill.addColorStop(0.62, rgba(255, 230, 245, 0.82));
      starFill.addColorStop(0.86, rgba(190, 225, 255, 0.52));
      starFill.addColorStop(1, rgba(160, 215, 255, 0.18));
      ctx.fillStyle = starFill;
      buildSparklePathP(focalX, focalY, starOuter, starInner);
      ctx.fill();
      ctx.strokeStyle = rgba(255, 255, 255, 0.28);
      ctx.lineWidth = 1.1;
      buildSparklePathP(focalX, focalY, starOuter, starInner);
      ctx.stroke();
      var verticalH = Math.min(height * 0.42, 360),
        verticalW = Math.max(6, Math.min(width * 0.014, 16));
      var vertFlare = ctx.createLinearGradient(focalX, focalY - verticalH * 0.5, focalX, focalY + verticalH * 0.5);
      vertFlare.addColorStop(0, rgba(255, 255, 255, 0));
      vertFlare.addColorStop(0.18, rgba(255, 185, 235, 0.22));
      vertFlare.addColorStop(0.5, rgba(255, 255, 255, 0.78));
      vertFlare.addColorStop(0.82, rgba(180, 215, 255, 0.22));
      vertFlare.addColorStop(1, rgba(255, 255, 255, 0));
      ctx.fillStyle = vertFlare;
      ctx.fillRect(focalX - verticalW * 0.5, focalY - verticalH * 0.5, verticalW, verticalH);
      var horizontalW = width * 0.7;
      var horizFlare = ctx.createLinearGradient(focalX - horizontalW * 0.5, focalY, focalX + horizontalW * 0.5, focalY);
      horizFlare.addColorStop(0, rgba(255, 255, 255, 0));
      horizFlare.addColorStop(0.2, rgba(90, 165, 255, 0.05));
      horizFlare.addColorStop(0.42, rgba(255, 180, 235, 0.12));
      horizFlare.addColorStop(0.5, rgba(255, 255, 255, 0.34));
      horizFlare.addColorStop(0.58, rgba(190, 220, 255, 0.12));
      horizFlare.addColorStop(0.8, rgba(255, 120, 220, 0.05));
      horizFlare.addColorStop(1, rgba(255, 255, 255, 0));
      ctx.fillStyle = horizFlare;
      ctx.fillRect(focalX - horizontalW * 0.5, focalY - 2.5, horizontalW, 5);
      var innerGlow = ctx.createRadialGradient(focalX, focalY, 0, focalX, focalY, starOuter * 0.9);
      innerGlow.addColorStop(0, rgba(255, 255, 255, 0.96));
      innerGlow.addColorStop(0.35, rgba(255, 255, 255, 0.55));
      innerGlow.addColorStop(0.8, rgba(180, 225, 255, 0.12));
      innerGlow.addColorStop(1, rgba(0, 0, 0, 0));
      ctx.fillStyle = innerGlow;
      ctx.beginPath();
      ctx.arc(focalX, focalY, starOuter * 0.9, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }
    function drawVignetteP(p) {
      var sx = p.currentX * depth.vignette,
        sy = p.currentY * depth.vignette;
      var vig = ctx.createRadialGradient(cx + sx, cy + sy, Math.min(width, height) * 0.2, cx + sx, cy + sy, Math.max(width, height) * 0.8);
      vig.addColorStop(0, "rgba(0,0,0,0)");
      vig.addColorStop(0.65, "rgba(0,0,0,0.08)");
      vig.addColorStop(1, "rgba(0,0,0,0.42)");
      ctx.fillStyle = vig;
      ctx.fillRect(0, 0, width, height);
    }
    function frame(now) {
      var dt = Math.min(32, now - lastTime);
      lastTime = now;
      time += dt;
      ctx.clearRect(0, 0, width, height);
      drawBackgroundGradient();
      drawNebulaClouds(time);
      drawSlowMovingStars(time);
      drawStreaks(time);
      drawCentreFlare(time);
      drawVignette();
      animationRef.current = requestAnimationFrame(frame);
    }
    function frameParallax(now) {
      var dt = Math.min(32, now - lastTime);
      lastTime = now;
      time += dt;
      var p = updateParallax();
      ctx.clearRect(0, 0, width, height);
      drawBackgroundGradientP(p);
      drawCentreFlareP(time, p);
      drawNebulaCloudsP(time, p);
      drawSlowMovingStarsP(time, p);
      drawStreaksP(time, p);
      drawVignetteP(p);
      animationRef.current = requestAnimationFrame(frameParallax);
    }
    function mulberry32(a) {
      return function () {
        var t = a += 0x6d2b79f5;
        t = Math.imul(t ^ t >>> 15, t | 1);
        t ^= t + Math.imul(t ^ t >>> 7, t | 61);
        return ((t ^ t >>> 14) >>> 0) / 4294967296;
      };
    }
    var rng = mulberry32(1337);
    var srand = function srand(min, max) {
      return rng() * (max - min) + min;
    };
    function resizeStatic() {
      var rect = canvas.getBoundingClientRect();
      width = Math.max(1, Math.floor(rect.width || window.innerWidth));
      height = Math.max(1, Math.floor(rect.height || window.innerHeight));
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
      canvas.style.width = "".concat(width, "px");
      canvas.style.height = "".concat(height, "px");
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      cx = width * 0.5;
      cy = height * 0.5;
      drawStatic();
    }
    function drawBackgroundGradientS() {
      var bg = ctx.createLinearGradient(0, 0, width, height);
      bg.addColorStop(0, "rgba(2,6,18,1)");
      bg.addColorStop(0.28, "rgba(5,12,30,1)");
      bg.addColorStop(0.55, "rgba(9,8,24,1)");
      bg.addColorStop(0.78, "rgba(20,7,28,1)");
      bg.addColorStop(1, "rgba(6,2,12,1)");
      ctx.fillStyle = bg;
      ctx.fillRect(0, 0, width, height);
    }
    function drawNebulaCloudsS() {
      ctx.save();
      ctx.globalCompositeOperation = "screen";
      var leftGrad = ctx.createRadialGradient(width * 0.18, height * 0.48, 10, width * 0.18, height * 0.48, width * 0.55);
      leftGrad.addColorStop(0, "rgba(40,140,255,".concat(0.18 * nebulaStrength, ")"));
      leftGrad.addColorStop(0.28, "rgba(20,105,230,".concat(0.12 * nebulaStrength, ")"));
      leftGrad.addColorStop(0.62, "rgba(8,42,120,".concat(0.09 * nebulaStrength, ")"));
      leftGrad.addColorStop(1, "rgba(0,0,0,0)");
      ctx.fillStyle = leftGrad;
      ctx.fillRect(0, 0, width, height);
      var rightGrad = ctx.createRadialGradient(width * 0.8, height * 0.5, 12, width * 0.8, height * 0.5, width * 0.48);
      rightGrad.addColorStop(0, "rgba(255,100,230,".concat(0.2 * nebulaStrength, ")"));
      rightGrad.addColorStop(0.34, "rgba(175,70,255,".concat(0.14 * nebulaStrength, ")"));
      rightGrad.addColorStop(0.7, "rgba(95,25,160,".concat(0.08 * nebulaStrength, ")"));
      rightGrad.addColorStop(1, "rgba(0,0,0,0)");
      ctx.fillStyle = rightGrad;
      ctx.fillRect(0, 0, width, height);
      var blobs = [{
        x: width * 0.16,
        y: height * 0.33,
        rx: width * 0.28,
        ry: height * 0.16,
        c1: "rgba(80,180,255,0.06)",
        c2: "rgba(20,40,100,0)"
      }, {
        x: width * 0.26,
        y: height * 0.72,
        rx: width * 0.24,
        ry: height * 0.12,
        c1: "rgba(0,190,255,0.05)",
        c2: "rgba(0,0,0,0)"
      }, {
        x: width * 0.78,
        y: height * 0.33,
        rx: width * 0.22,
        ry: height * 0.14,
        c1: "rgba(255,90,200,0.07)",
        c2: "rgba(0,0,0,0)"
      }, {
        x: width * 0.86,
        y: height * 0.66,
        rx: width * 0.26,
        ry: height * 0.16,
        c1: "rgba(180,70,255,0.08)",
        c2: "rgba(0,0,0,0)"
      }];
      blobs.forEach(function (b) {
        var driftX = srand(-18, 18),
          driftY = srand(-12, 12);
        var g = ctx.createRadialGradient(b.x + driftX, b.y + driftY, 0, b.x + driftX, b.y + driftY, Math.max(b.rx, b.ry));
        g.addColorStop(0, b.c1);
        g.addColorStop(1, b.c2);
        ctx.save();
        ctx.translate(b.x + driftX, b.y + driftY);
        ctx.scale(1, b.ry / b.rx);
        ctx.beginPath();
        ctx.arc(0, 0, b.rx, 0, Math.PI * 2);
        ctx.closePath();
        ctx.fillStyle = g;
        ctx.fill();
        ctx.restore();
      });
      ctx.restore();
    }
    function drawStarsS() {
      ctx.save();
      ctx.globalCompositeOperation = "screen";
      var total = Math.floor(starCount * intensity);
      for (var i = 0; i < total; i++) {
        var sideBias = rng(),
          x = srand(0, width),
          y = srand(0, height);
        var base = Math.pow(rng(), 1.6),
          r = srand(0.35, 1.8) * (0.7 + base);
        var a = srand(0.15, 0.95) * srand(0.82, 1);
        var tint = "rgba(255,255,255,1)";
        if (sideBias < 0.46) tint = "rgba(".concat(Math.floor(srand(140, 210)), ",").concat(Math.floor(srand(190, 240)), ",255,1)");else if (sideBias > 0.62) tint = "rgba(255,".concat(Math.floor(srand(150, 205)), ",").concat(Math.floor(srand(220, 255)), ",1)");
        ctx.fillStyle = tint.replace(/,\s*1\)$/, ",".concat(a, ")"));
        ctx.beginPath();
        ctx.arc(x, y, r, 0, Math.PI * 2);
        ctx.fill();
        if (r > 1.15) {
          ctx.strokeStyle = rgba(255, 255, 255, a * 0.2);
          ctx.lineWidth = 0.6;
          ctx.beginPath();
          ctx.moveTo(x - r * 2.1, y);
          ctx.lineTo(x + r * 2.1, y);
          ctx.moveTo(x, y - r * 2.1);
          ctx.lineTo(x, y + r * 2.1);
          ctx.stroke();
        }
      }
      ctx.restore();
    }
    function drawStreaksS() {
      ctx.save();
      ctx.globalCompositeOperation = "lighter";
      ctx.lineCap = "round";
      var total = Math.floor(streakCount * intensity);
      var maxRadius = Math.hypot(width, height) * 0.75;
      for (var i = 0; i < total; i++) {
        var hueWeight = rng();
        var baseAngle = Math.atan2(srand(-height * 0.55, height * 0.55), srand(-width * 0.55, width * 0.55));
        var angle = baseAngle + srand(-0.3, 0.3);
        var z = srand(0.04, 1),
          eased = z * z,
          radius = lerp(6, maxRadius, eased);
        var x = cx + Math.cos(angle) * radius,
          y = cy + Math.sin(angle) * radius;
        var dirX = x - cx,
          dirY = y - cy,
          dirLen = Math.max(1, Math.hypot(dirX, dirY));
        var ux = dirX / dirLen,
          uy = dirY / dirLen;
        var widthPx = srand(0.5, 2.6) * (0.3 + eased * 1.4);
        var trail = srand(22, 180) * (0.18 + eased * 1.75);
        var x2 = x - ux * trail,
          y2 = y - uy * trail;
        var alpha = clamp(srand(0.12, 0.85) * (0.3 + eased * 1.15), 0.05, 1);
        var colour = [165, 110, 255];
        if (hueWeight < 0.18) colour = [255, 255, 255];else if (hueWeight < 0.39) colour = [95, 205, 255];else if (hueWeight < 0.56) colour = [0, 255, 220];else if (hueWeight < 0.68) colour = [120, 255, 160];else if (hueWeight < 0.84) colour = [255, 90, 210];
        var _colour = colour,
          _colour2 = _slicedToArray(_colour, 3),
          r = _colour2[0],
          g = _colour2[1],
          b = _colour2[2];
        var grad = ctx.createLinearGradient(x2, y2, x, y);
        grad.addColorStop(0, rgba(255, 255, 255, 0));
        grad.addColorStop(0.45, rgba(r, g, b, alpha * 0.33));
        grad.addColorStop(1, rgba(r, g, b, alpha));
        ctx.strokeStyle = grad;
        ctx.lineWidth = widthPx;
        ctx.beginPath();
        ctx.moveTo(x2, y2);
        ctx.lineTo(x, y);
        ctx.stroke();
      }
      ctx.restore();
    }
    function buildSparklePathS(x, y, sizeOuter, sizeInner) {
      ctx.beginPath();
      ctx.moveTo(x, y - sizeOuter);
      ctx.quadraticCurveTo(x + sizeInner * 0.45, y - sizeInner * 0.75, x + sizeOuter, y);
      ctx.quadraticCurveTo(x + sizeInner * 0.75, y + sizeInner * 0.45, x, y + sizeOuter);
      ctx.quadraticCurveTo(x - sizeInner * 0.45, y + sizeInner * 0.75, x - sizeOuter, y);
      ctx.quadraticCurveTo(x - sizeInner * 0.75, y - sizeInner * 0.45, x, y - sizeOuter);
      ctx.closePath();
    }
    function drawCentreFlareS() {
      ctx.save();
      ctx.globalCompositeOperation = "screen";
      var minSide = Math.min(width, height);
      var outerGlow = ctx.createRadialGradient(cx, cy, 0, cx, cy, minSide * 0.24);
      outerGlow.addColorStop(0, rgba(255, 255, 255, 0.46));
      outerGlow.addColorStop(0.08, rgba(210, 235, 255, 0.22));
      outerGlow.addColorStop(0.18, rgba(255, 160, 235, 0.16));
      outerGlow.addColorStop(0.28, rgba(120, 180, 255, 0.11));
      outerGlow.addColorStop(1, rgba(0, 0, 0, 0));
      ctx.fillStyle = outerGlow;
      ctx.beginPath();
      ctx.arc(cx, cy, minSide * 0.24, 0, Math.PI * 2);
      ctx.fill();
      var starOuter = clamp(minSide * 0.078, 36, 82),
        starInner = starOuter * 0.34;
      var starGlowA = ctx.createRadialGradient(cx, cy, 0, cx, cy, starOuter * 1.45);
      starGlowA.addColorStop(0, rgba(255, 255, 255, 0.78));
      starGlowA.addColorStop(0.42, rgba(255, 245, 255, 0.28));
      starGlowA.addColorStop(0.7, rgba(255, 170, 235, 0.16));
      starGlowA.addColorStop(1, rgba(0, 0, 0, 0));
      ctx.fillStyle = starGlowA;
      buildSparklePathS(cx, cy, starOuter * 1.22, starInner * 1.22);
      ctx.fill();
      var starFill = ctx.createRadialGradient(cx, cy, 0, cx, cy, starOuter);
      starFill.addColorStop(0, rgba(255, 255, 255, 1));
      starFill.addColorStop(0.28, rgba(255, 255, 255, 0.96));
      starFill.addColorStop(0.62, rgba(255, 230, 245, 0.82));
      starFill.addColorStop(0.86, rgba(190, 225, 255, 0.52));
      starFill.addColorStop(1, rgba(160, 215, 255, 0.18));
      ctx.fillStyle = starFill;
      buildSparklePathS(cx, cy, starOuter, starInner);
      ctx.fill();
      ctx.strokeStyle = rgba(255, 255, 255, 0.28);
      ctx.lineWidth = 1.1;
      buildSparklePathS(cx, cy, starOuter, starInner);
      ctx.stroke();
      var verticalH = Math.min(height * 0.42, 360),
        verticalW = Math.max(6, Math.min(width * 0.014, 16));
      var vertFlare = ctx.createLinearGradient(cx, cy - verticalH * 0.5, cx, cy + verticalH * 0.5);
      vertFlare.addColorStop(0, rgba(255, 255, 255, 0));
      vertFlare.addColorStop(0.18, rgba(255, 185, 235, 0.22));
      vertFlare.addColorStop(0.5, rgba(255, 255, 255, 0.78));
      vertFlare.addColorStop(0.82, rgba(180, 215, 255, 0.22));
      vertFlare.addColorStop(1, rgba(255, 255, 255, 0));
      ctx.fillStyle = vertFlare;
      ctx.fillRect(cx - verticalW * 0.5, cy - verticalH * 0.5, verticalW, verticalH);
      var horizontalW = width * 0.7;
      var horizFlare = ctx.createLinearGradient(cx - horizontalW * 0.5, cy, cx + horizontalW * 0.5, cy);
      horizFlare.addColorStop(0, rgba(255, 255, 255, 0));
      horizFlare.addColorStop(0.2, rgba(90, 165, 255, 0.05));
      horizFlare.addColorStop(0.42, rgba(255, 180, 235, 0.12));
      horizFlare.addColorStop(0.5, rgba(255, 255, 255, 0.34));
      horizFlare.addColorStop(0.58, rgba(190, 220, 255, 0.12));
      horizFlare.addColorStop(0.8, rgba(255, 120, 220, 0.05));
      horizFlare.addColorStop(1, rgba(255, 255, 255, 0));
      ctx.fillStyle = horizFlare;
      ctx.fillRect(cx - horizontalW * 0.5, cy - 2.5, horizontalW, 5);
      var innerGlow = ctx.createRadialGradient(cx, cy, 0, cx, cy, starOuter * 0.9);
      innerGlow.addColorStop(0, rgba(255, 255, 255, 0.96));
      innerGlow.addColorStop(0.35, rgba(255, 255, 255, 0.55));
      innerGlow.addColorStop(0.8, rgba(180, 225, 255, 0.12));
      innerGlow.addColorStop(1, rgba(0, 0, 0, 0));
      ctx.fillStyle = innerGlow;
      ctx.beginPath();
      ctx.arc(cx, cy, starOuter * 0.9, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }
    function drawVignetteS() {
      var vig = ctx.createRadialGradient(cx, cy, Math.min(width, height) * 0.2, cx, cy, Math.max(width, height) * 0.8);
      vig.addColorStop(0, "rgba(0,0,0,0)");
      vig.addColorStop(0.65, "rgba(0,0,0,0.08)");
      vig.addColorStop(1, "rgba(0,0,0,0.42)");
      ctx.fillStyle = vig;
      ctx.fillRect(0, 0, width, height);
    }
    function drawStatic() {
      rng = mulberry32(1337);
      ctx.clearRect(0, 0, width, height);
      drawBackgroundGradientS();
      drawNebulaCloudsS();
      drawStarsS();
      drawStreaksS();
      drawCentreFlareS();
      drawVignetteS();
    }
    if (staticMode) {
      resizeStatic();
      var _ro = new ResizeObserver(resizeStatic);
      _ro.observe(canvas);
      window.addEventListener("resize", resizeStatic);
      return function () {
        _ro.disconnect();
        window.removeEventListener("resize", resizeStatic);
      };
    }
    resize();
    var ro = new ResizeObserver(resize);
    ro.observe(canvas);
    window.addEventListener("resize", resize);
    if (parallax) {
      window.addEventListener("pointermove", onPointerMove, {
        passive: true
      });
      window.addEventListener("pointerleave", onPointerLeave);
      window.addEventListener("blur", onPointerLeave);
      animationRef.current = requestAnimationFrame(frameParallax);
      return function () {
        cancelAnimationFrame(animationRef.current);
        ro.disconnect();
        window.removeEventListener("resize", resize);
        window.removeEventListener("pointermove", onPointerMove);
        window.removeEventListener("pointerleave", onPointerLeave);
        window.removeEventListener("blur", onPointerLeave);
      };
    }
    animationRef.current = requestAnimationFrame(frame);
    return function () {
      cancelAnimationFrame(animationRef.current);
      ro.disconnect();
      window.removeEventListener("resize", resize);
    };
  }, [intensity, speed, starCount, streakCount, nebulaStrength, starDriftSpeed, parallaxStrength, parallaxSmoothing, parallax, staticMode]);
  return /*#__PURE__*/React.createElement("canvas", {
    ref: canvasRef,
    className: className,
    "aria-hidden": "true",
    style: {
      width: "100%",
      height: "100%",
      display: "block",
      background: "transparent",
      pointerEvents: "none"
    }
  });
}

// ── Draw main wheel ────────────────────────────────────────────────────────
// Wheel mode percentages mirrored from wheel_modes.py — used for drawing only.
var WHEEL_MODE_DRAW = {
  steady: {
    win_pct: 70,
    lose_pct: 28,
    jackpot_pct: 2
  },
  "volatile": {
    win_pct: 45,
    lose_pct: 50,
    jackpot_pct: 5
  },
  inverted: {
    win_pct: 60,
    lose_pct: 35,
    jackpot_pct: 5
  },
  gravity: {
    win_pct: 55,
    lose_pct: 40,
    jackpot_pct: 5
  },
  mirror: {
    win_pct: 65,
    lose_pct: 30,
    jackpot_pct: 5
  },
  singularity: {
    win_pct: 75,
    lose_pct: 10,
    jackpot_pct: 15
  }
};
function drawWheel(canvas) {
  var theme = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : 'default';
  var wheelMode = arguments.length > 2 && arguments[2] !== undefined ? arguments[2] : 'steady';
  var ctx = canvas.getContext('2d');
  var size = canvas.width;
  var cx = size / 2,
    cy = size / 2,
    r = size / 2 - 4;
  ctx.clearRect(0, 0, size, size);

  // Per-theme colours for WIN and LOSE segments
  var THEME_COLORS = {
    "default": {
      win: ['#550088', '#AA00FF'],
      lose: ['#7a3300', '#FF6600']
    },
    fire: {
      win: ['#993300', '#FF6600'],
      lose: ['#440000', '#CC2200']
    },
    ice: {
      win: ['#005577', '#00CCFF'],
      lose: ['#002244', '#0066CC']
    },
    neon: {
      win: ['#440088', '#CC00FF'],
      lose: ['#003300', '#00FF66']
    },
    "void": {
      win: ['#0a0a1a', '#6633FF'],
      lose: ['#0d0010', '#330066']
    },
    gold: {
      win: ['#7a5c00', '#FFE566'],
      lose: ['#3d2000', '#CC8800']
    },
    bioluminescence: {
      win: ['#003a4d', '#00E5FF'],
      lose: ['#4d1020', '#FF6B6B']
    },
    night_ocean: {
      win: ['#1a0d4d', '#5533FF'],
      lose: ['#3d0011', '#CC2244']
    },
    wormhole: {
      win: ['#1a0044', '#BB88FF'],
      lose: ['#3d0022', '#FF44AA']
    }
  };
  var colors = THEME_COLORS[theme] || THEME_COLORS["default"];

  // Compute arc spans from mode percentages.
  // Segments radiate clockwise from -π/2 (12-o'clock): WIN → LOSE → JACKPOT
  var modeConfig = WHEEL_MODE_DRAW[wheelMode] || WHEEL_MODE_DRAW.steady;
  var winSpan = modeConfig.win_pct / 100 * Math.PI * 2;
  var loseSpan = modeConfig.lose_pct / 100 * Math.PI * 2;
  var jpSpan = modeConfig.jackpot_pct / 100 * Math.PI * 2;
  var origin = -Math.PI / 2; // 12-o'clock start
  var segments = [{
    label: 'WIN',
    color: colors.win[0],
    bright: colors.win[1],
    start: origin,
    span: winSpan
  }, {
    label: 'LOSE',
    color: colors.lose[0],
    bright: colors.lose[1],
    start: origin + winSpan,
    span: loseSpan
  }, {
    label: '★',
    color: '#4a3800',
    bright: '#FFD700',
    start: origin + winSpan + loseSpan,
    span: jpSpan
  }];
  segments.forEach(function (seg) {
    var end = seg.start + seg.span;

    // Fill
    var grad = ctx.createRadialGradient(cx, cy, r * 0.1, cx, cy, r);
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
    var midAngle = seg.start + seg.span / 2;
    var spanDeg = seg.span * 180 / Math.PI;
    if (spanDeg >= 8) {
      ctx.save();
      ctx.translate(cx, cy);
      ctx.rotate(midAngle);
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.shadowColor = 'rgba(0,0,0,0.8)';
      ctx.shadowBlur = 8;
      if (spanDeg < 25) {
        // Tiny segment — small symbol only
        ctx.font = "bold ".concat(size * 0.07, "px 'Oswald', Arial Black, sans-serif");
        ctx.fillStyle = '#FFF';
        ctx.fillText(seg.label === '★' ? '★' : seg.label[0], r * 0.55, 0);
      } else {
        ctx.font = "bold ".concat(size * 0.1, "px 'Oswald', Arial Black, sans-serif");
        ctx.fillStyle = '#FFF';
        ctx.fillText(seg.label, r * 0.55, 0);
      }
      ctx.restore();
    }

    // Rim dots — scaled to segment size
    var dotCount = Math.max(2, Math.round(seg.span / (Math.PI * 2) * 28));
    for (var i = 0; i <= dotCount; i++) {
      var a = seg.start + seg.span * (i / dotCount);
      var dr = r * 0.88;
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
  // T15: Use shared format_wins() from format.js for consistency
  if (typeof window.format_wins === 'function') return window.format_wins(n);
  // Fallback if format.js not loaded
  if (!isFinite(n) || isNaN(n)) return '0';
  if (n >= 1e15) return n.toExponential(2).replace('e+', 'e');
  if (n >= 1e12) return parseFloat((n / 1e12).toPrecision(3)) + 'T';
  if (n >= 1e9) return parseFloat((n / 1e9).toPrecision(3)) + 'B';
  if (n >= 1e6) return parseFloat((n / 1e6).toPrecision(3)) + 'M';
  if (n >= 10e3) return parseFloat((n / 1e3).toPrecision(3)) + 'K';
  return String(n);
}

// ── Hiatus mode — set to false to re-enable the full game ─────────────────
var HIATUS_MODE = false;
var HIATUS_END = new Date('2026-05-01T23:59:59'); // Next Friday 11:59 pm
var HIATUS_PAST_SEASON = 6; // season that just ended

// ── Scoreboard ────────────────────────────────────────────────────────────
var Scoreboard = React.memo(function Scoreboard(_ref3) {
  var wins = _ref3.wins,
    losses = _ref3.losses,
    lastResult = _ref3.lastResult;
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
function Confetti(_ref4) {
  var active = _ref4.active,
    _ref4$count = _ref4.count,
    count = _ref4$count === void 0 ? 80 : _ref4$count;
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
function GuardWheel(_ref5) {
  var blocked = _ref5.blocked,
    _ref5$speedMult = _ref5.speedMult,
    speedMult = _ref5$speedMult === void 0 ? 1.0 : _ref5$speedMult,
    onComplete = _ref5.onComplete,
    _ref5$contained = _ref5.contained,
    contained = _ref5$contained === void 0 ? false : _ref5$contained;
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
    className: contained ? 'guard-overlay guard-overlay--contained' : 'guard-overlay'
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
function FishEncyclopedia(_ref6) {
  var caughtSpecies = _ref6.caughtSpecies,
    onClose = _ref6.onClose;
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
function FishingPanel(_ref7) {
  var fishClicks = _ref7.fishClicks,
    fishData = _ref7.fishData,
    caughtSpecies = _ref7.caughtSpecies,
    fishingLuckyNext = _ref7.fishingLuckyNext,
    ownedItems = _ref7.ownedItems,
    fishPanelScale = _ref7.fishPanelScale,
    onFishBucksUpdate = _ref7.onFishBucksUpdate,
    onCaughtSpeciesUpdate = _ref7.onCaughtSpeciesUpdate,
    onFishCaught = _ref7.onFishCaught;
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
  var _ref8 = fishData || {
      emoji: '🐟'
    },
    fisherEmoji = _ref8.emoji;
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
      var _ref9 = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee() {
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
                if (onFishCaught) onFishCaught();
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
        return _ref9.apply(this, arguments);
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
      var _ref0 = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee2() {
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
        return _ref0.apply(this, arguments);
      };
    }();
    poll();
  }, [countMiss]); // eslint-disable-line

  var doCast = /*#__PURE__*/function () {
    var _ref1 = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee3() {
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
      return _ref1.apply(this, arguments);
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
            if (onFishCaught) onFishCaught();
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
    className: "fishing-water-area"
  }, /*#__PURE__*/React.createElement("div", {
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
  }, "CLICK TO REEL!")), /*#__PURE__*/React.createElement("div", {
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
      } else {
        apiGame('/api/auto-fish-enabled', {
          method: 'POST',
          body: JSON.stringify({
            enabled: false
          })
        });
      }
    }
  }), /*#__PURE__*/React.createElement("span", {
    className: "fishing-toggle-text"
  }, "Auto-Fish")))), /*#__PURE__*/React.createElement("div", {
    className: "catch-side-info"
  }, phase === 'success' && lastCatch ? /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("span", {
    className: "catch-side-emoji"
  }, lastCatch.emoji), /*#__PURE__*/React.createElement("span", {
    className: "catch-side-value"
  }, "+", lastCatch.value, " \uD83D\uDC1F", lastCatch.doubled ? ' 2x!' : ''), lastCatch.preciseMult && /*#__PURE__*/React.createElement("span", {
    className: "catch-side-precise"
  }, "\uD83C\uDFAF ", lastCatch.preciseMult, "x @ ", lastCatch.precisePct, "%"), lastCatch.isNew && /*#__PURE__*/React.createElement("span", {
    className: "catch-side-tag catch-side-new"
  }, "NEW!"), lastCatch.isLucky && /*#__PURE__*/React.createElement("span", {
    className: "catch-side-tag catch-side-lucky"
  }, "\u2B50 Lucky!")) : phase === 'miss' ? /*#__PURE__*/React.createElement("span", {
    className: "catch-side-miss"
  }, missReason === 'early' ? 'Too early!' : 'Too slow!') : autoFish && autoFishPopup ? autoFishPopup.type === 'hit' ? /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("span", {
    className: "catch-side-emoji"
  }, autoFishPopup.emoji), /*#__PURE__*/React.createElement("span", {
    className: "catch-side-value"
  }, "+", autoFishPopup.value, " \uD83D\uDC1F"), autoFishPopup.isNew && /*#__PURE__*/React.createElement("span", {
    className: "catch-side-tag catch-side-new"
  }, "NEW!")) : /*#__PURE__*/React.createElement("span", {
    className: "catch-side-miss"
  }, "No bite") : lastCatch ? /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("span", {
    className: "catch-side-label"
  }, "Last"), /*#__PURE__*/React.createElement("span", {
    className: "catch-side-emoji"
  }, lastCatch.emoji), /*#__PURE__*/React.createElement("span", {
    className: "catch-side-value"
  }, "+", lastCatch.value, " \uD83D\uDC1F"), lastCatch.preciseMult && /*#__PURE__*/React.createElement("span", {
    className: "catch-side-precise"
  }, "\uD83C\uDFAF ", lastCatch.preciseMult, "x @ ", lastCatch.precisePct, "%")) : null));
}

// ── Lucky Seven Counter ───────────────────────────────────────────────────
var LuckySevenCounter = React.memo(function LuckySevenCounter(_ref11) {
  var spinCount = _ref11.spinCount;
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
var ProcStreakCounter = React.memo(function ProcStreakCounter(_ref12) {
  var streak = _ref12.streak;
  if (streak === 0) return null;
  return /*#__PURE__*/React.createElement("div", {
    className: "proc-streak-counter"
  }, /*#__PURE__*/React.createElement("span", {
    className: "proc-streak-label"
  }, "\u26A1"), /*#__PURE__*/React.createElement("span", {
    className: "proc-streak-value"
  }, streak));
});

// ── Streak Panel ──────────────────────────────────────────────────────────
// Must match models.py bonus_mult_from_level() (Season 7: C1+C2 curve)
function bonusMultFromLevel(level) {
  var fixed = [1, 2, 4, 8, 15, 35, 70];
  if (level <= 6) return fixed[level] || 1;
  if (level <= 30) return 70 + (level - 6) * 8;
  return 262 + (level - 30) * 5;
}
var StreakPanel = React.memo(function StreakPanel(_ref13) {
  var streak = _ref13.streak,
    bonusmultLevel = _ref13.bonusmultLevel;
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
function Die(_ref14) {
  var value = _ref14.value,
    rolling = _ref14.rolling,
    landed = _ref14.landed;
  var pips = PIP_LAYOUTS[value] || [];
  var cls = "die".concat(rolling ? ' die-rolling' : '').concat(landed ? ' die-landed' : '');
  return /*#__PURE__*/React.createElement("div", {
    className: cls
  }, pips.map(function (_ref15, i) {
    var _ref16 = _slicedToArray(_ref15, 2),
      row = _ref16[0],
      col = _ref16[1];
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
function DicePanel(_ref17) {
  var streak = _ref17.streak,
    onRoll = _ref17.onRoll,
    rolling = _ref17.rolling,
    diceResult = _ref17.diceResult,
    guardSpinning = _ref17.guardSpinning,
    lowSpec = _ref17.lowSpec,
    diceCharges = _ref17.diceCharges,
    maxDiceCharges = _ref17.maxDiceCharges,
    diceLastRecharge = _ref17.diceLastRecharge,
    hasDiceExtra = _ref17.hasDiceExtra,
    rolledSinceSpin = _ref17.rolledSinceSpin;
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
  var canRoll = diceCharges >= 1 && streak >= 3 && !rolling && !guardSpinning && !rolledSinceSpin;
  var die1Val = rolling && !lowSpec ? animDie1 : diceResult ? diceResult.die1 : animDie1;
  var die2Val = rolling && !lowSpec ? animDie2 : diceResult ? diceResult.die2 : animDie2;
  var die3Val = rolling && !lowSpec ? animDie3 : diceResult && diceResult.die3 != null ? diceResult.die3 : animDie3;
  var showTip = function showTip() {
    if (guardSpinning) return;
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
  if (diceCharges < 1) disabledReason = 'No charges';else if (streak < 3) disabledReason = 'Need win streak ≥3';else if (rolledSinceSpin) disabledReason = 'Dice buffered — applies next spin';
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
  }, diceResult.cursed_triple ? "\uD83D\uDC80 TRIPLE CURSE! Streak \xF73" : diceResult.blessed_triple ? "\uD83C\uDF1F TRIPLE BLESSED! Streak \xD73!" : diceResult.cursed ? "\uD83D\uDC80 CURSED! Streak -".concat(diceResult.streak_before - diceResult.streak_after) : "+".concat(diceResult.streak_delta, " streak!"), diceResult.pending && rolledSinceSpin && /*#__PURE__*/React.createElement("span", {
    className: "dice-pending-note"
  }, " \u23F3 next spin")), /*#__PURE__*/React.createElement("button", {
    className: "dice-roll-btn".concat(canRoll ? '' : ' dice-roll-btn--disabled'),
    onClick: canRoll ? onRoll : undefined,
    disabled: !canRoll,
    title: canRoll ? 'Roll the dice!' : disabledReason
  }, rolling ? 'Rolling…' : "Roll (".concat(diceCharges, "/").concat(maxDiceCharges, " charges)")));
}

// ── Season Winners ────────────────────────────────────────────────────────
function SeasonWinners(_ref18) {
  var winners = _ref18.winners,
    seasonNumber = _ref18.seasonNumber,
    _ref18$extraClass = _ref18.extraClass,
    extraClass = _ref18$extraClass === void 0 ? '' : _ref18$extraClass;
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
function SeasonInfo(_ref19) {
  var seasonName = _ref19.seasonName;
  return /*#__PURE__*/React.createElement("div", {
    className: "season-info"
  }, /*#__PURE__*/React.createElement("span", null, "Season ", seasonName, " ends:"), /*#__PURE__*/React.createElement("span", {
    className: "season-countdown"
  }, "\u221E"));
}

// ── Hiatus Screen ────────────────────────────────────────────────────────
function HiatusCountdown() {
  var _useState23 = useState(''),
    _useState24 = _slicedToArray(_useState23, 2),
    timeLeft = _useState24[0],
    setTimeLeft = _useState24[1];
  useEffect(function () {
    var update = function update() {
      var diff = HIATUS_END - Date.now();
      if (diff <= 0) {
        setTimeLeft('Starting now!');
        return;
      }
      var d = Math.floor(diff / 86400000);
      var h = Math.floor(diff % 86400000 / 3600000);
      var m = Math.floor(diff % 3600000 / 60000);
      var s = Math.floor(diff % 60000 / 1000);
      setTimeLeft(d > 0 ? "".concat(d, "d ").concat(h, "h ").concat(m, "m ").concat(s, "s") : "".concat(h, "h ").concat(m, "m ").concat(s, "s"));
    };
    update();
    var id = setInterval(update, 1000);
    return function () {
      return clearInterval(id);
    };
  }, []);
  return /*#__PURE__*/React.createElement("span", {
    className: "hiatus-countdown"
  }, timeLeft);
}
function HiatusDice() {
  var _useState25 = useState(false),
    _useState26 = _slicedToArray(_useState25, 2),
    rolling = _useState26[0],
    setRolling = _useState26[1];
  var _useState27 = useState([1, 1, 1]),
    _useState28 = _slicedToArray(_useState27, 2),
    vals = _useState28[0],
    setVals = _useState28[1];
  var _useState29 = useState([1, 1, 1]),
    _useState30 = _slicedToArray(_useState29, 2),
    anim = _useState30[0],
    setAnim = _useState30[1];
  var _useState31 = useState(false),
    _useState32 = _slicedToArray(_useState31, 2),
    landed = _useState32[0],
    setLanded = _useState32[1];
  var itvRef = useRef(null);
  var roll = function roll() {
    if (rolling) return;
    setRolling(true);
    setLanded(false);
    itvRef.current = setInterval(function () {
      setAnim([Math.ceil(Math.random() * 6), Math.ceil(Math.random() * 6), Math.ceil(Math.random() * 6)]);
    }, 80);
    setTimeout(function () {
      clearInterval(itvRef.current);
      var r = [Math.ceil(Math.random() * 6), Math.ceil(Math.random() * 6), Math.ceil(Math.random() * 6)];
      setVals(r);
      setAnim(r);
      setLanded(true);
      setRolling(false);
    }, 800);
  };
  var d = rolling ? anim : vals;
  return /*#__PURE__*/React.createElement("div", {
    className: "hiatus-dice-panel"
  }, /*#__PURE__*/React.createElement("div", {
    className: "dice-triangle"
  }, /*#__PURE__*/React.createElement("div", {
    className: "dice-row dice-row-top"
  }, /*#__PURE__*/React.createElement(Die, {
    value: d[2],
    rolling: rolling,
    landed: landed
  })), /*#__PURE__*/React.createElement("div", {
    className: "dice-row"
  }, /*#__PURE__*/React.createElement(Die, {
    value: d[0],
    rolling: rolling,
    landed: landed
  }), /*#__PURE__*/React.createElement(Die, {
    value: d[1],
    rolling: rolling,
    landed: landed
  }))), /*#__PURE__*/React.createElement("button", {
    className: "dice-roll-btn",
    onClick: roll,
    disabled: rolling
  }, rolling ? 'Rolling…' : 'Roll'));
}
function HiatusWheel() {
  var canvasRef = useRef(null);
  var _useState33 = useState(0),
    _useState34 = _slicedToArray(_useState33, 2),
    rotation = _useState34[0],
    setRotation = _useState34[1];
  var _useState35 = useState(false),
    _useState36 = _slicedToArray(_useState35, 2),
    spinning = _useState36[0],
    setSpinning = _useState36[1];
  var _useState37 = useState(0),
    _useState38 = _slicedToArray(_useState37, 2),
    wins = _useState38[0],
    setWins = _useState38[1];
  var _useState39 = useState(0),
    _useState40 = _slicedToArray(_useState39, 2),
    losses = _useState40[0],
    setLosses = _useState40[1];
  var _useState41 = useState(false),
    _useState42 = _slicedToArray(_useState41, 2),
    autoSpin = _useState42[0],
    setAutoSpin = _useState42[1];
  var spinningRef = useRef(false);
  var rotationRef = useRef(0);
  var autoSpinRef = useRef(false);
  // Use the same sessionStorage key as the main game to avoid tab-lock rejections
  var tabId = useRef(function () {
    var id = sessionStorage.getItem('wheel_tab_id');
    if (!id) {
      id = Math.random().toString(36).slice(2) + Date.now().toString(36);
      sessionStorage.setItem('wheel_tab_id', id);
    }
    return id;
  }());
  var SPEED = 4.5;
  useEffect(function () {
    autoSpinRef.current = autoSpin;
  }, [autoSpin]);
  useEffect(function () {
    if (canvasRef.current) drawWheel(canvasRef.current, 'default');
  }, []);
  var spin = useCallback(/*#__PURE__*/_asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee5() {
    var res, data, base, seg, next;
    return _regeneratorRuntime().wrap(function _callee5$(_context5) {
      while (1) switch (_context5.prev = _context5.next) {
        case 0:
          if (!spinningRef.current) {
            _context5.next = 2;
            break;
          }
          return _context5.abrupt("return");
        case 2:
          spinningRef.current = true;
          setSpinning(true);
          _context5.prev = 4;
          _context5.next = 7;
          return apiGame('/api/spin', {
            method: 'POST',
            body: JSON.stringify({
              tab_id: tabId.current
            })
          });
        case 7:
          res = _context5.sent;
          if (res.ok) {
            _context5.next = 13;
            break;
          }
          spinningRef.current = false;
          setSpinning(false);
          if (autoSpinRef.current) setTimeout(spin, 1500);
          return _context5.abrupt("return");
        case 13:
          data = res.data;
          base = rotationRef.current;
          seg = data.angle % 360;
          next = Math.ceil((base + 5 * 360 - seg) / 360) * 360 + seg;
          rotationRef.current = next;
          setRotation(next);
          setTimeout(function () {
            if (data.result === 'win') setWins(function (w) {
              return w + 1;
            });else setLosses(function (l) {
              return l + 1;
            });
            spinningRef.current = false;
            setSpinning(false);
            if (autoSpinRef.current) setTimeout(spin, 1500);
          }, SPEED * 1000 + 200);
          _context5.next = 27;
          break;
        case 22:
          _context5.prev = 22;
          _context5.t0 = _context5["catch"](4);
          spinningRef.current = false;
          setSpinning(false);
          if (autoSpinRef.current) setTimeout(spin, 1500);
        case 27:
        case "end":
          return _context5.stop();
      }
    }, _callee5, null, [[4, 22]]);
  })), []);
  useEffect(function () {
    if (autoSpin && !spinningRef.current) spin();
  }, [autoSpin, spin]);
  return /*#__PURE__*/React.createElement("div", {
    className: "hiatus-wheel-wrap"
  }, /*#__PURE__*/React.createElement("div", {
    className: "hiatus-wheel-container"
  }, /*#__PURE__*/React.createElement("div", {
    className: "hiatus-wheel-pointer"
  }, "\u25BC"), /*#__PURE__*/React.createElement("canvas", {
    ref: canvasRef,
    width: 180,
    height: 180,
    className: "wheel-canvas".concat(spinning ? ' spinning' : ''),
    style: {
      transform: "rotate(".concat(rotation, "deg)"),
      transition: "transform ".concat(SPEED, "s cubic-bezier(0.17, 0.67, 0.12, 0.99)")
    }
  }), /*#__PURE__*/React.createElement("div", {
    className: "center-hub"
  }, "\u2605")), /*#__PURE__*/React.createElement("div", {
    className: "hiatus-wheel-score"
  }, /*#__PURE__*/React.createElement("span", {
    className: "hiatus-wscore hiatus-wscore-w"
  }, "\u2713 ", wins, "W"), /*#__PURE__*/React.createElement("span", {
    className: "hiatus-wscore hiatus-wscore-l"
  }, "\u2717 ", losses, "L")), /*#__PURE__*/React.createElement("button", {
    className: "hiatus-spin-btn",
    onClick: spin,
    disabled: spinning
  }, spinning ? '● ● ●' : '▶ Spin ◀'), /*#__PURE__*/React.createElement("label", {
    className: "hiatus-autospin-label"
  }, /*#__PURE__*/React.createElement("input", {
    type: "checkbox",
    checked: autoSpin,
    onChange: function onChange(e) {
      return setAutoSpin(e.target.checked);
    }
  }), /*#__PURE__*/React.createElement("span", null, "Auto Spin")));
}
function HiatusScreen(_ref21) {
  var season = _ref21.season,
    username = _ref21.username,
    onLogout = _ref21.onLogout;
  var winners = season && season.latest_winners;
  useEffect(function () {
    apiFetch('/api/register-season', {
      method: 'POST'
    })["catch"](function () {});
  }, []);
  return /*#__PURE__*/React.createElement("div", {
    className: "hiatus-screen"
  }, /*#__PURE__*/React.createElement("div", {
    className: "hiatus-topbar"
  }, /*#__PURE__*/React.createElement("span", {
    className: "hiatus-topbar-title"
  }, "\uD83C\uDFA1 Wheel Hiatus"), /*#__PURE__*/React.createElement("span", {
    className: "hiatus-topbar-user"
  }, "\uD83D\uDC64 ", username), /*#__PURE__*/React.createElement("button", {
    className: "logout-btn",
    onClick: onLogout
  }, "Logout")), /*#__PURE__*/React.createElement("div", {
    className: "hiatus-body"
  }, /*#__PURE__*/React.createElement("div", {
    className: "hiatus-col hiatus-col-left"
  }, /*#__PURE__*/React.createElement("div", {
    className: "hiatus-col-heading"
  }, "Season ", HIATUS_PAST_SEASON, " Winners"), winners && winners.length > 0 ? /*#__PURE__*/React.createElement(SeasonWinners, {
    winners: winners,
    seasonNumber: HIATUS_PAST_SEASON
  }) : /*#__PURE__*/React.createElement("div", {
    className: "hiatus-empty"
  }, "No season data yet"), /*#__PURE__*/React.createElement("div", {
    className: "hiatus-col-heading hiatus-col-heading--sub"
  }, "Mid-Season 6.7"), /*#__PURE__*/React.createElement(Leaderboard, {
    currentUser: username,
    extraClass: "hiatus-lb"
  })), /*#__PURE__*/React.createElement("div", {
    className: "hiatus-col hiatus-col-center"
  }, /*#__PURE__*/React.createElement(HiatusWheel, null), /*#__PURE__*/React.createElement("div", {
    className: "hiatus-col-heading hiatus-col-heading--sub"
  }, "\uD83C\uDFB2 Roll for fun"), /*#__PURE__*/React.createElement(HiatusDice, null), /*#__PURE__*/React.createElement("span", {
    className: "hiatus-dice-note"
  }, "No game effect \u2014 just for fun!")), /*#__PURE__*/React.createElement("div", {
    className: "hiatus-col hiatus-col-message"
  }, /*#__PURE__*/React.createElement("div", {
    className: "hiatus-message-box"
  }, /*#__PURE__*/React.createElement("div", {
    className: "hiatus-message-title"
  }, "\u23F8 Taking a Break"), /*#__PURE__*/React.createElement("p", {
    className: "hiatus-message-body"
  }, "The wheel is on hiatus this week \u2014 thank you for playing Season ", HIATUS_PAST_SEASON, "! We'll be back next Friday with Season7\uFE0F\u20E3."), /*#__PURE__*/React.createElement("div", {
    className: "hiatus-countdown-row"
  }, /*#__PURE__*/React.createElement("span", {
    className: "hiatus-countdown-label"
  }, "Season7\uFE0F\u20E3 begins in"), /*#__PURE__*/React.createElement(HiatusCountdown, null)), /*#__PURE__*/React.createElement("div", {
    className: "hiatus-preregistered"
  }, /*#__PURE__*/React.createElement("p", {
    className: "hiatus-preregistered-text"
  }, /*#__PURE__*/React.createElement("strong", null, "\uD83C\uDFB0 You're pre-registered for Season 7."), " Your auto-spin clock starts the moment the season begins \u2014 so your wins are already accumulating by the time you next log in, no matter how long after launch that is."))))));
}

// ── Leaderboard ───────────────────────────────────────────────────────────
function Leaderboard(_ref22) {
  var currentUser = _ref22.currentUser,
    extraClass = _ref22.extraClass,
    seasonWinners = _ref22.seasonWinners,
    seasonNumber = _ref22.seasonNumber;
  var _useState43 = useState([]),
    _useState44 = _slicedToArray(_useState43, 2),
    rows = _useState44[0],
    setRows = _useState44[1];
  var _useState45 = useState('players'),
    _useState46 = _slicedToArray(_useState45, 2),
    tab = _useState46[0],
    setTab = _useState46[1];
  useEffect(function () {
    var ctrl = new AbortController();
    var load = function load() {
      if (document.hidden) return;
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
    className: "lb-wp-h",
    title: "Win Power level"
  }, "WP"), /*#__PURE__*/React.createElement("span", {
    className: "lb-bp-h",
    title: "Bonus Power level"
  }, "BP"), /*#__PURE__*/React.createElement("span", {
    className: "lb-streak-h"
  }, "\uD83D\uDD25")), rows.map(function (r, i) {
    return /*#__PURE__*/React.createElement("div", {
      key: r.username,
      className: "lb-row".concat(r.active ? '' : ' lb-inactive')
    }, /*#__PURE__*/React.createElement("span", {
      className: "lb-rank ".concat(rankClass(i))
    }, i + 1, "."), /*#__PURE__*/React.createElement("span", {
      className: "lb-name ".concat(r.username === currentUser ? 'is-you' : '')
    }, r.username), /*#__PURE__*/React.createElement("span", {
      className: "lb-wins"
    }, fmt(r.wins)), /*#__PURE__*/React.createElement("span", {
      className: "lb-wp"
    }, r.winmult_inf_level > 0 ? r.winmult_inf_level : '—'), /*#__PURE__*/React.createElement("span", {
      className: "lb-bp"
    }, r.bonusmult_inf_level > 0 ? r.bonusmult_inf_level : '—'), /*#__PURE__*/React.createElement("span", {
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
function ChatPanel(_ref23) {
  var _ref23$extraClass = _ref23.extraClass,
    extraClass = _ref23$extraClass === void 0 ? '' : _ref23$extraClass,
    onClose = _ref23.onClose;
  var _useState47 = useState([]),
    _useState48 = _slicedToArray(_useState47, 2),
    messages = _useState48[0],
    setMessages = _useState48[1];
  var _useState49 = useState(''),
    _useState50 = _slicedToArray(_useState49, 2),
    input = _useState50[0],
    setInput = _useState50[1];
  var _useState51 = useState(''),
    _useState52 = _slicedToArray(_useState51, 2),
    error = _useState52[0],
    setError = _useState52[1];
  var _useState53 = useState(0),
    _useState54 = _slicedToArray(_useState53, 2),
    timeoutSecs = _useState54[0],
    setTimeoutSecs = _useState54[1];
  var _useState55 = useState(function () {
      try {
        var s = JSON.parse(localStorage.getItem('chat_panel_size'));
        if (s && s.w >= CHAT_MIN_W && s.h >= CHAT_MIN_H) return s;
      } catch (_unused2) {}
      return CHAT_DEFAULT_SIZE;
    }),
    _useState56 = _slicedToArray(_useState55, 2),
    size = _useState56[0],
    setSize = _useState56[1];
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
      if (document.hidden) return;
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
    var _ref24 = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee6() {
      var text, r, secs;
      return _regeneratorRuntime().wrap(function _callee6$(_context6) {
        while (1) switch (_context6.prev = _context6.next) {
          case 0:
            text = input.trim();
            if (text) {
              _context6.next = 3;
              break;
            }
            return _context6.abrupt("return");
          case 3:
            setError('');
            _context6.next = 6;
            return apiGame('/api/chat', {
              method: 'POST',
              body: JSON.stringify({
                message: text
              })
            });
          case 6:
            r = _context6.sent;
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
            return _context6.stop();
        }
      }, _callee6);
    }));
    return function sendMessage() {
      return _ref24.apply(this, arguments);
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
    var isSystem = m.message_type && m.message_type !== 'user';
    var isReplay = m.message_type === 'replay';
    if (isReplay) {
      return /*#__PURE__*/React.createElement("div", {
        key: m.id,
        className: "chat-msg chat-msg-replay"
      }, m.created_at && /*#__PURE__*/React.createElement("span", {
        className: "chat-msg-time"
      }, fmtChatTime(m.created_at)), /*#__PURE__*/React.createElement("div", {
        className: "replay-card"
      }, /*#__PURE__*/React.createElement("span", {
        className: "replay-icon"
      }, "\uD83C\uDFAC"), /*#__PURE__*/React.createElement("span", {
        className: "replay-text"
      }, m.message)));
    }
    if (isSystem) {
      return /*#__PURE__*/React.createElement("div", {
        key: m.id,
        className: "chat-msg chat-msg-system"
      }, m.created_at && /*#__PURE__*/React.createElement("span", {
        className: "chat-msg-time"
      }, fmtChatTime(m.created_at)), /*#__PURE__*/React.createElement("span", {
        className: "chat-msg-text chat-system-text"
      }, m.message));
    }
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
}, {
  id: 'fish_rocket',
  emoji: '🚀',
  name: 'Rocket',
  cost: 50000,
  labels: {
    idle: 'T-minus 3...',
    happy: 'BLAST OFF!',
    sad: 'Mission failed...'
  }
}, {
  id: 'fish_comet',
  emoji: '☄️',
  name: 'Comet',
  cost: 85000,
  labels: {
    idle: '*blazing through space*',
    happy: 'Comet strike!',
    sad: 'Burned up...'
  }
}, {
  id: 'fish_saturn',
  emoji: '🪐',
  name: 'Saturn',
  cost: 145000,
  labels: {
    idle: 'Ringing around~',
    happy: 'Orbital win!',
    sad: 'Lost in the rings...'
  }
}, {
  id: 'fish_alien',
  emoji: '👽',
  name: 'Alien',
  cost: 250000,
  labels: {
    idle: 'Greetings, earthling',
    happy: 'ABDUCTION WIN!',
    sad: '*returns to home planet*'
  }
}, {
  id: 'fish_ufo',
  emoji: '🛸',
  name: 'UFO',
  cost: 425000,
  labels: {
    idle: '*hovering*',
    happy: 'BEAM UP!',
    sad: '*crashes*'
  }
}];
var SHOP_SECTIONS = [{
  label: '🪐 Class',
  classSection: true,
  items: [{
    id: 'class_earth',
    emoji: '🌍',
    name: 'Earth',
    cost: 10000000,
    tier: 3,
    desc: '+25% to all fish income while equipped'
  }, {
    id: 'class_moon',
    emoji: '🌙',
    name: 'Moon',
    cost: 10000000,
    tier: 3,
    desc: '+5% to all proc rates (Jackpot, Win Echo, Fortune Charm) while equipped'
  }, {
    id: 'class_star',
    emoji: '⭐',
    name: 'Star',
    cost: 10000000,
    tier: 3,
    desc: '+20% to Win Power payout while equipped'
  }]
}, {
  label: '💰 Win Power',
  items: [{
    id: 'winmult_1',
    emoji: '💰',
    name: 'Win Power I',
    cost: 200,
    desc: '+20% win multiplier'
  }, {
    id: 'winmult_2',
    emoji: '💰',
    name: 'Win Power II',
    cost: 600,
    desc: '+40% win multiplier',
    requires: 'winmult_1'
  }, {
    id: 'winmult_3',
    emoji: '💰',
    name: 'Win Power III',
    cost: 2000,
    desc: '+60% win multiplier',
    requires: 'winmult_2'
  }]
}, {
  label: '⭐ Bonus Power',
  items: [{
    id: 'bonusmult_1',
    emoji: '⭐',
    name: 'Bonus Power I',
    cost: 300,
    desc: 'Multiplies streak bonuses'
  }, {
    id: 'bonusmult_2',
    emoji: '⭐',
    name: 'Bonus Power II',
    cost: 900,
    desc: 'Multiplies streak bonuses',
    requires: 'bonusmult_1'
  }, {
    id: 'bonusmult_3',
    emoji: '⭐',
    name: 'Bonus Power III',
    cost: 2800,
    desc: 'Multiplies streak bonuses',
    requires: 'bonusmult_2'
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
    cost: 1000,
    desc: 'Blocks one loss per manual trigger. Consumes a guard charge.'
  }, {
    id: 'guard_charge',
    emoji: '🔋',
    name: 'Guard Charge',
    cost: 10000,
    desc: 'Adds a guard charge (max 3). Recharges 1 per 50 spins via Regen Shield.',
    tier: 2
  }, {
    id: 'regen_shield',
    emoji: '🔄',
    name: 'Regenerating Shield',
    cost: 5000,
    desc: 'Blocks any loss when charged. Recharges after 5 wins. Never breaks.',
    tier: 2
  }, {
    id: 'resilience',
    emoji: '💪',
    name: 'Resilience',
    cost: 20000,
    desc: '50% chance: on win streak, a loss only drops streak by 1 instead of resetting',
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
    id: 'jackpot',
    emoji: '🎰',
    name: 'Jackpot',
    cost: 3000000,
    desc: '1% chance each win to multiply gains by 25x. 5% chance for Jackpot Echo next spin.',
    tier: 3
  }]
}, {
  label: '⚡ Season 8: Wager System',
  items: [{
    id: 'wager_unlock',
    emoji: '⚡',
    name: 'Wager Unlock',
    cost: 500,
    desc: 'Unlocks stake multiplier (1x-10x) for spins',
    tier: 1
  }, {
    id: 'wager_safety_net',
    emoji: '🛡️',
    name: 'Safety Net',
    cost: 2000,
    desc: 'Reduces loss by 25% at stake 5x+',
    tier: 2,
    requires: 'wager_unlock'
  }, {
    id: 'wager_hot_streak',
    emoji: '🔥',
    name: 'Hot Streak',
    cost: 8000,
    desc: '+5% per consecutive same-stake win, cap +50%',
    tier: 2,
    requires: 'wager_unlock'
  }, {
    id: 'wager_double_down',
    emoji: '⚡',
    name: 'Double Down',
    cost: 25000,
    desc: 'Arm 2x stake for next spin',
    tier: 3,
    requires: 'wager_hot_streak'
  }, {
    id: 'wager_insurance',
    emoji: '🛡️',
    name: 'Insurance',
    cost: 50000,
    desc: 'Caps next loss at stake amount',
    tier: 3,
    requires: 'wager_unlock'
  }]
}, {
  label: '🏅 Season 8: Prestige',
  items: [{
    id: 'prestige_unlock',
    emoji: '🏅',
    name: 'Prestige Unlock',
    cost: 1000000,
    desc: 'Unlocks prestige reset (permanent +2% per level)',
    tier: 3
  }, {
    id: 'prestige_efficiency',
    emoji: '⚡',
    name: 'Prestige Efficiency',
    cost: 500000,
    desc: 'Reduces prestige threshold from 1M to 500K wins',
    tier: 3,
    requires: 'prestige_unlock'
  }, {
    id: 'prestige_legacy',
    emoji: '📜',
    name: 'Prestige Legacy',
    cost: 1000000,
    desc: 'Keep functional upgrades when prestiging',
    tier: 3,
    requires: 'prestige_unlock'
  }]
}, {
  label: '🎣 Season 8: Fishing',
  items: [{
    id: 'fish_to_wager',
    emoji: '🪙',
    name: 'Fish-to-Wager',
    cost: 5000,
    desc: 'Convert caught fish to wager tokens',
    tier: 1
  }, {
    id: 'catch_of_the_day',
    emoji: '📅',
    name: 'Catch of the Day',
    cost: 3000,
    desc: 'First fish conversion each day worth 5x tokens',
    tier: 1
  }, {
    id: 'aquarium',
    emoji: '🐠',
    name: 'Aquarium',
    cost: 15000,
    desc: 'Each unique species adds +0.1% wheel luck',
    tier: 2
  }, {
    id: 'lure_specialization',
    emoji: '🎯',
    name: 'Lure Specialization',
    cost: 10000,
    desc: 'Specialized lure techniques',
    tier: 2,
    requires: 'fish_to_wager'
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
    id: 'theme_tidal',
    emoji: '🌊',
    name: 'Tidal Theme',
    cost: 250,
    desc: 'Cool blue/teal with wave animation'
  }, {
    id: 'theme_ember',
    emoji: '🔥',
    name: 'Ember Theme',
    cost: 1000,
    desc: 'Warm orange with spark animation',
    requires: 'theme_tidal'
  }, {
    id: 'theme_frost',
    emoji: '❄️',
    name: 'Frost Theme',
    cost: 4000,
    desc: 'Ice-crystal palette with crack animation',
    requires: 'theme_ember'
  }, {
    id: 'theme_aurora',
    emoji: '🌌',
    name: 'Aurora Theme',
    cost: 12000,
    desc: 'Shifting greens/purples with northern lights',
    requires: 'theme_frost'
  }, {
    id: 'theme_vintage',
    emoji: '📼',
    name: 'Vintage Theme',
    cost: 40000,
    desc: 'Retro-styled sepia tones'
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
    emoji: '🎊',
    name: 'Party Mode',
    cost: 150,
    desc: 'Win confetti burst every spin'
  }, {
    id: 'confetti_1',
    emoji: '✨',
    name: 'Confetti I',
    cost: 75,
    desc: 'Light confetti on wins'
  }, {
    id: 'confetti_2',
    emoji: '🌟',
    name: 'Confetti II',
    cost: 300,
    desc: 'Heavier confetti shower',
    requires: 'confetti_1'
  }, {
    id: 'confetti_3',
    emoji: '💫',
    name: 'Confetti III',
    cost: 1200,
    desc: 'Maximum confetti eruption',
    requires: 'confetti_2'
  }]
}, {
  label: '🎨 Atmosphere',
  items: [{
    id: 'bg_royal',
    emoji: '👑',
    name: 'Royal',
    cost: 400,
    desc: 'Deep purple radial atmosphere'
  }, {
    id: 'bg_inferno',
    emoji: '🔥',
    name: 'Inferno',
    cost: 1600,
    desc: 'Red hellscape atmosphere',
    requires: 'bg_royal'
  }, {
    id: 'bg_forest',
    emoji: '🌲',
    name: 'Forest',
    cost: 5000,
    desc: 'Dark forest atmosphere',
    requires: 'bg_inferno'
  }, {
    id: 'bg_abyss',
    emoji: '🌑',
    name: 'Abyss',
    cost: 15000,
    desc: 'Void atmosphere',
    requires: 'bg_forest'
  }, {
    id: 'bg_cosmic',
    emoji: '🌌',
    name: 'Cosmic',
    cost: 50000,
    desc: 'Cosmic void atmosphere',
    requires: 'bg_abyss'
  }]
}, {
  label: '🖼️ Page Theme',
  items: [{
    id: 'page_season1',
    emoji: '1️⃣',
    name: 'Season 1',
    cost: 1000,
    desc: 'Season 1 page theme'
  }, {
    id: 'page_season2',
    emoji: '2️⃣',
    name: 'Season 2',
    cost: 1000,
    desc: 'Season 2 page theme'
  }, {
    id: 'page_season3',
    emoji: '3️⃣',
    name: 'Season 3',
    cost: 1000,
    desc: 'Season 3 page theme'
  }, {
    id: 'page_season4',
    emoji: '4️⃣',
    name: 'Season 4',
    cost: 1000,
    desc: 'Season 4 page theme'
  }, {
    id: 'page_season5',
    emoji: '5️⃣',
    name: 'Season 5',
    cost: 1000,
    desc: 'Season 5 page theme — Bioluminescence'
  }, {
    id: 'page_season6',
    emoji: '6️⃣',
    name: 'Season 6',
    cost: 1000,
    desc: 'Season 6 page theme — Night Ocean'
  }, {
    id: 'page_season7',
    emoji: '7️⃣',
    name: 'Season 7',
    cost: 1000,
    desc: 'Season 7 page theme — Wormhole'
  }]
}, {
  label: '🎲 Dice Charges',
  items: [{
    id: 'dice_charge_2',
    emoji: '🎲',
    name: 'Dice Charge +1',
    cost: 2000,
    desc: 'Max dice charges: 2'
  }, {
    id: 'dice_charge_3',
    emoji: '🎲',
    name: 'Dice Charge +2',
    cost: 15000,
    desc: 'Max dice charges: 3',
    requires: 'dice_charge_2'
  }, {
    id: 'dice_charge_4',
    emoji: '🎲',
    name: 'Dice Charge +3',
    cost: 100000,
    desc: 'Max dice charges: 4',
    requires: 'dice_charge_3'
  }, {
    id: 'dice_extra',
    emoji: '🎰',
    name: 'Extra Die',
    cost: 1000000,
    desc: 'Roll 3 dice — take the best result',
    requires: 'dice_charge_3'
  }]
}];

// Infinite upgrade config (mirrors INFINITE_UPGRADES in models.py)
var INF_UPGRADE_CFG = {
  clickmult_inf: {
    tierCosts: [75, 250, 600, 1400, 3000],
    infBase: 10000,
    infScale: 1.5
  }
};
function infCost(id, level) {
  var cfg = INF_UPGRADE_CFG[id];
  if (!cfg) return 0;
  var tierCosts = cfg.tierCosts,
    infBase = cfg.infBase,
    infScale = cfg.infScale;
  if (level < tierCosts.length) return tierCosts[level];
  return Math.floor(infBase * Math.pow(infScale, level - tierCosts.length));
}
function infMultiplier(id, level) {
  if (id === 'clickmult_inf') return 1 + level * 0.15;
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
var COSMETIC_SECTION_IDS = new Set(['bg_royal', 'bg_inferno', 'bg_forest', 'bg_abyss', 'bg_cosmic', 'fishsize_small', 'fishsize_1', 'fishsize_2', 'fishsize_3', 'confetti_1', 'confetti_2', 'confetti_3', 'party_mode', 'trail_1', 'trail_2', 'trail_3', 'trail_4', 'trail_5', 'trail_6', 'theme_fire', 'theme_ice', 'theme_neon', 'theme_void', 'theme_gold', 'theme_tidal', 'theme_ember', 'theme_frost', 'theme_aurora', 'theme_vintage', 'golden_wheel', 'page_season1', 'page_season2', 'page_season3', 'page_season4', 'page_season5', 'page_season6', 'page_season7']);

// Season 3: currency classification (mirrors ITEM_CURRENCY in models.py)
var COSMETIC_IDS = new Set(['fish_tropical', 'fish_puffer', 'fish_octopus', 'fish_shark', 'fish_dolphin', 'fish_squid', 'fish_turtle', 'fish_crab', 'fish_lobster', 'fish_whale', 'fish_seal', 'fish_shrimp', 'fish_coral', 'fish_mermaid', 'fish_croc', 'fish_rocket', 'fish_comet', 'fish_saturn', 'fish_alien', 'fish_ufo', 'fishsize_small', 'fishsize_1', 'fishsize_2', 'fishsize_3', 'trail_1', 'trail_2', 'trail_3', 'trail_4', 'trail_5', 'trail_6', 'theme_fire', 'theme_ice', 'theme_neon', 'theme_void', 'theme_gold', 'golden_wheel', 'theme_tidal', 'theme_ember', 'theme_frost', 'theme_aurora', 'theme_vintage', 'page_season1', 'page_season2', 'page_season3', 'page_season4', 'page_season5', 'page_season6', 'page_season7', 'party_mode', 'confetti_1', 'confetti_2', 'confetti_3', 'bg_royal', 'bg_inferno', 'bg_forest', 'bg_abyss', 'bg_cosmic']);
var getItemCurrency = function getItemCurrency(id) {
  if (COSMETIC_IDS.has(id)) return 'losses';
  return 'wins';
};
var currencyIcon = function currencyIcon(c) {
  return c === 'wins' ? '🏆' : c === 'losses' ? '💀' : '🐟';
};

// Linear decay: 1:1 for first 25M exchanged, linearly down to 10% by 125M
function computeFishExchangeRate(total) {
  if (total < 25000000) return 100;
  if (total >= 125000000) return 10;
  var t = (total - 25000000) / 100000000;
  return Math.round(Math.max(10, 100 - 90 * t));
}

// ── Shop components ────────────────────────────────────────────────────────
var CLASS_IDS = new Set(['class_earth', 'class_moon', 'class_star']);
var ShopItem = React.memo(function ShopItem(_ref25) {
  var item = _ref25.item,
    owned = _ref25.owned,
    equipped = _ref25.equipped,
    active = _ref25.active,
    canAfford = _ref25.canAfford,
    onBuy = _ref25.onBuy,
    onEquip = _ref25.onEquip,
    onEquipCosmetic = _ref25.onEquipCosmetic,
    onEquipClass = _ref25.onEquipClass,
    isSkin = _ref25.isSkin,
    isSingularity = _ref25.isSingularity,
    isCosmetic = _ref25.isCosmetic,
    isClass = _ref25.isClass,
    isClassEquipped = _ref25.isClassEquipped,
    infLevel = _ref25.infLevel,
    displayCost = _ref25.displayCost,
    procStreak = _ref25.procStreak;
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
  } else if (owned && isClass) {
    actionEl = isClassEquipped ? /*#__PURE__*/React.createElement("span", {
      className: "shop-equipped-badge"
    }, "\u2B50 Equipped") : /*#__PURE__*/React.createElement("button", {
      className: "shop-equip-btn",
      onClick: function onClick() {
        return onEquipClass(item.id);
      }
    }, "Equip");
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
    if (item.id === 'proc_streak_inf') {
      var streak = procStreak || 0;
      var currentBonus = (streak * infLevel * 0.5).toFixed(1);
      return "+".concat(currentBonus, "% now (streak ").concat(streak, " \xD7 Lv").concat(infLevel, ") \xB7 Lv").concat(infLevel, " \u2192 Lv").concat(infLevel + 1, "  ").concat(item.desc);
    }
    var cur = infMultiplier(item.id, infLevel);
    var nxt = infMultiplier(item.id, infLevel + 1);
    var sep = 'x';
    if (item.id === 'streak_armor_inf') sep = '%';
    if (item.id === 'jackpot_resonance_inf') sep = '%';
    if (item.id === 'echo_amp_inf') sep = '%';
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
function ShopPanel(_ref26) {
  var fishClicks = _ref26.fishClicks,
    wins = _ref26.wins,
    losses = _ref26.losses,
    ownedItems = _ref26.ownedItems,
    equippedFish = _ref26.equippedFish,
    activeCosmetics = _ref26.activeCosmetics,
    infLevels = _ref26.infLevels,
    onBuy = _ref26.onBuy,
    onEquip = _ref26.onEquip,
    onEquipCosmetic = _ref26.onEquipCosmetic,
    onEquipClass = _ref26.onEquipClass,
    onFishExchange = _ref26.onFishExchange,
    onWinsExchange = _ref26.onWinsExchange,
    equippedClass = _ref26.equippedClass,
    fishExchangeTotal = _ref26.fishExchangeTotal,
    collapsed = _ref26.collapsed,
    winCount = _ref26.winCount,
    caughtSpecies = _ref26.caughtSpecies,
    procStreak = _ref26.procStreak;
  var _useState57 = useState('functional'),
    _useState58 = _slicedToArray(_useState57, 2),
    activeTab = _useState58[0],
    setActiveTab = _useState58[1];
  var _useMemo = useMemo(function () {
      var cosmetic = [],
        functional = [];
      SHOP_SECTIONS.forEach(function (section) {
        var isCosmeticSection = COSMETIC_SECTION_LABELS.has(section.label);
        var visibleItems = section.items.filter(function (item) {
          var requiresMet = !item.requires || ownedItems.includes(item.requires);
          if (isCosmeticSection) return requiresMet;
          if (item.infinite) {
            if (item.id === 'streak_armor_inf') return ownedItems.includes('resilience');
            if (item.id === 'jackpot_resonance_inf') return ownedItems.includes('jackpot');
            if (item.id === 'echo_amp_inf') return ownedItems.includes('win_echo');
            if (item.id === 'proc_streak_inf') return ['jackpot', 'win_echo', 'fortune_charm'].some(function (x) {
              return ownedItems.includes(x);
            });
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
      var isClass = CLASS_IDS.has(item.id);
      var isClassEquipped = isClass && equippedClass === item.id.replace('class_', '');
      return /*#__PURE__*/React.createElement(ShopItem, {
        key: item.id,
        item: item,
        isSkin: false,
        isSingularity: item.id === 'singularity',
        isCosmetic: isCosmetic,
        isClass: isClass,
        isClassEquipped: isClassEquipped,
        owned: !item.infinite && ownedItems.includes(item.id),
        equipped: false,
        active: isCosmetic && activeCosmetics.includes(item.id),
        canAfford: !atMaxLevel && balance >= displayCost,
        infLevel: infLevel,
        displayCost: atMaxLevel ? 0 : displayCost,
        procStreak: procStreak,
        onBuy: onBuy,
        onEquip: onEquip,
        onEquipCosmetic: onEquipCosmetic,
        onEquipClass: onEquipClass
      });
    }));
  };
  var exchangeRate = computeFishExchangeRate(fishExchangeTotal || 0);
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
  }), cosmeticSections.map(renderSection)) : /*#__PURE__*/React.createElement(React.Fragment, null, functionalSections.map(renderSection), (fishClicks > 0 || wins > 0) && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    className: "shop-section-label"
  }, "\u2500\u2500 \uD83D\uDD04 Fish Exchange \u2500\u2500"), fishClicks > 0 && /*#__PURE__*/React.createElement("div", {
    className: "fish-exchange-panel"
  }, /*#__PURE__*/React.createElement("div", {
    className: "fish-exchange-desc"
  }, "Convert \uD83D\uDC1F Fish Bucks \u2192 \uD83C\uDFC6 Wins at ~", exchangeRate, "\xA2 per buck", exchangeRate < 100 && /*#__PURE__*/React.createElement("span", {
    className: "fish-exchange-rate-warn"
  }, " (1:1 for first 25M, then decays)")), /*#__PURE__*/React.createElement("div", {
    className: "fish-exchange-buttons"
  }, /*#__PURE__*/React.createElement("button", {
    className: "shop-buy-btn can-afford",
    onClick: function onClick() {
      return onFishExchange('10pct');
    }
  }, "Exchange 10% (", fmt(Math.max(1, Math.floor(fishClicks / 10))), " \uD83D\uDC1F)"), /*#__PURE__*/React.createElement("button", {
    className: "shop-buy-btn can-afford",
    onClick: function onClick() {
      return onFishExchange('all');
    }
  }, "Exchange All (", fmt(fishClicks), " \uD83D\uDC1F)"))), wins > 0 && /*#__PURE__*/React.createElement("div", {
    className: "wins-exchange-panel"
  }, /*#__PURE__*/React.createElement("div", {
    className: "wins-exchange-desc"
  }, "Convert \uD83C\uDFC6 Wins \u2192 \uD83D\uDC1F Fish Bucks at 1:1"), /*#__PURE__*/React.createElement("div", {
    className: "fish-exchange-buttons"
  }, /*#__PURE__*/React.createElement("button", {
    className: "shop-buy-btn can-afford",
    onClick: function onClick() {
      return onWinsExchange('10pct');
    }
  }, "Exchange 10% (", fmt(Math.max(1, Math.floor(wins / 10))), " \uD83C\uDFC6)"), /*#__PURE__*/React.createElement("button", {
    className: "shop-buy-btn can-afford",
    onClick: function onClick() {
      return onWinsExchange('all');
    }
  }, "Exchange All (", fmt(wins), " \uD83C\uDFC6)")))))));
}

// ── Stats Panel ────────────────────────────────────────────────────────────
var PLACE_LABEL = function PLACE_LABEL(pos) {
  return pos === 1 ? '🥇 1st' : pos === 2 ? '🥈 2nd' : pos === 3 ? '🥉 3rd' : null;
};
function StatsPanel(_ref27) {
  var open = _ref27.open,
    onClose = _ref27.onClose;
  var _useState59 = useState(null),
    _useState60 = _slicedToArray(_useState59, 2),
    stats = _useState60[0],
    setStats = _useState60[1];
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

// ── Patch Notes Panel ──────────────────────────────────────────────────────
function PatchNotesPanel(_ref28) {
  var open = _ref28.open,
    onClose = _ref28.onClose;
  var _useState61 = useState(null),
    _useState62 = _slicedToArray(_useState61, 2),
    md = _useState62[0],
    setMd = _useState62[1];
  useEffect(function () {
    if (!open || md !== null) return;
    apiFetch('/api/patch-notes').then(function (r) {
      if (r.ok) setMd(r.data.content);
    });
  }, [open]);
  if (!open) return null;
  var html = md != null ? window.DOMPurify.sanitize(window.marked.parse(md)) : null;
  return /*#__PURE__*/React.createElement("div", {
    className: "stats-overlay",
    onClick: onClose
  }, /*#__PURE__*/React.createElement("div", {
    className: "patch-notes-card",
    onClick: function onClick(e) {
      return e.stopPropagation();
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "stats-title"
  }, "\uD83D\uDCCB Patch Notes"), /*#__PURE__*/React.createElement("button", {
    className: "stats-close-btn",
    onClick: onClose
  }, "\u2715"), /*#__PURE__*/React.createElement("div", {
    className: "patch-notes-body"
  }, html ? /*#__PURE__*/React.createElement("div", {
    className: "patch-notes-content",
    dangerouslySetInnerHTML: {
      __html: html
    }
  }) : /*#__PURE__*/React.createElement("div", {
    className: "stats-loading"
  }, "Loading\u2026"))));
}

// ── Auth Page ──────────────────────────────────────────────────────────────
function AuthPage(_ref29) {
  var onAuth = _ref29.onAuth;
  var _useState63 = useState('login'),
    _useState64 = _slicedToArray(_useState63, 2),
    mode = _useState64[0],
    setMode = _useState64[1];
  var _useState65 = useState(''),
    _useState66 = _slicedToArray(_useState65, 2),
    username = _useState66[0],
    setUsername = _useState66[1];
  var _useState67 = useState(''),
    _useState68 = _slicedToArray(_useState67, 2),
    password = _useState68[0],
    setPassword = _useState68[1];
  var _useState69 = useState(''),
    _useState70 = _slicedToArray(_useState69, 2),
    error = _useState70[0],
    setError = _useState70[1];
  var _useState71 = useState(false),
    _useState72 = _slicedToArray(_useState71, 2),
    loading = _useState72[0],
    setLoading = _useState72[1];
  var submit = /*#__PURE__*/function () {
    var _ref30 = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee7(e) {
      var _yield$apiFetch, ok, data;
      return _regeneratorRuntime().wrap(function _callee7$(_context7) {
        while (1) switch (_context7.prev = _context7.next) {
          case 0:
            e.preventDefault();
            setError('');
            setLoading(true);
            _context7.next = 5;
            return apiFetch("/api/".concat(mode), {
              method: 'POST',
              body: JSON.stringify({
                username: username,
                password: password
              })
            });
          case 5:
            _yield$apiFetch = _context7.sent;
            ok = _yield$apiFetch.ok;
            data = _yield$apiFetch.data;
            setLoading(false);
            if (ok) {
              storeCsrf(data);
              onAuth(data.username);
            } else {
              setError(data.error || 'Something went wrong');
            }
          case 10:
          case "end":
            return _context7.stop();
        }
      }, _callee7);
    }));
    return function submit(_x4) {
      return _ref30.apply(this, arguments);
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
  var _useState73 = useState(null),
    _useState74 = _slicedToArray(_useState73, 2),
    remaining = _useState74[0],
    setRemaining = _useState74[1];
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
function CommunityPot(_ref31) {
  var pot = _ref31.pot,
    fishClicks = _ref31.fishClicks,
    onContribute = _ref31.onContribute;
  var _useState75 = useState(pot),
    _useState76 = _slicedToArray(_useState75, 2),
    localPot = _useState76[0],
    setLocalPot = _useState76[1];
  var _useState77 = useState(!!pot.active),
    _useState78 = _slicedToArray(_useState77, 2),
    justFilled = _useState78[0],
    setJustFilled = _useState78[1];

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
    var _ref32 = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee8(amount) {
      var _yield$apiGame5, ok, data;
      return _regeneratorRuntime().wrap(function _callee8$(_context8) {
        while (1) switch (_context8.prev = _context8.next) {
          case 0:
            _context8.next = 2;
            return apiGame('/api/community-pot/contribute', {
              method: 'POST',
              body: JSON.stringify({
                amount: amount
              })
            });
          case 2:
            _yield$apiGame5 = _context8.sent;
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
            return _context8.stop();
        }
      }, _callee8);
    }));
    return function handleContribute(_x5) {
      return _ref32.apply(this, arguments);
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
function GameApp(_ref33) {
  var _gameState$dice_charg, _gameState$dice_rolle;
  var username = _ref33.username,
    gameState = _ref33.gameState,
    onLogout = _ref33.onLogout,
    onSessionExpired = _ref33.onSessionExpired;
  var canvasRef = useRef(null);
  var _useState79 = useState(null),
    _useState80 = _slicedToArray(_useState79, 2),
    result = _useState80[0],
    setResult = _useState80[1];
  var _useState81 = useState(false),
    _useState82 = _slicedToArray(_useState81, 2),
    showResult = _useState82[0],
    setShowResult = _useState82[1];
  var setShowResultSync = function setShowResultSync(v) {
    showResultRef.current = v;
    setShowResult(v);
  };
  var _useState83 = useState(null),
    _useState84 = _slicedToArray(_useState83, 2),
    shieldFeedback = _useState84[0],
    setShieldFeedback = _useState84[1];
  var _useState85 = useState(null),
    _useState86 = _slicedToArray(_useState85, 2),
    guardState = _useState86[0],
    setGuardState = _useState86[1]; // { blocked, broke } | null
  var guardCompleteRef = useRef(null);
  var _useState87 = useState(false),
    _useState88 = _slicedToArray(_useState87, 2),
    hideResult = _useState88[0],
    setHideResult = _useState88[1];
  var _useState89 = useState(false),
    _useState90 = _slicedToArray(_useState89, 2),
    confetti = _useState90[0],
    setConfetti = _useState90[1];
  var _useState91 = useState(gameState.wins),
    _useState92 = _slicedToArray(_useState91, 2),
    wins = _useState92[0],
    setWins = _useState92[1];
  var _useState93 = useState(gameState.losses),
    _useState94 = _slicedToArray(_useState93, 2),
    losses = _useState94[0],
    setLosses = _useState94[1];
  var _useState95 = useState(gameState.streak),
    _useState96 = _slicedToArray(_useState95, 2),
    streak = _useState96[0],
    setStreak = _useState96[1];
  var _useState97 = useState('idle'),
    _useState98 = _slicedToArray(_useState97, 2),
    fishMood = _useState98[0],
    setFishMood = _useState98[1];
  var _useState99 = useState(gameState.fish_clicks),
    _useState100 = _slicedToArray(_useState99, 2),
    fishClicks = _useState100[0],
    setFishClicks = _useState100[1];
  var _useState101 = useState(gameState.caught_species || []),
    _useState102 = _slicedToArray(_useState101, 2),
    caughtSpecies = _useState102[0],
    setCaughtSpecies = _useState102[1];
  var _useState103 = useState(gameState.fishing_lucky_next || false),
    _useState104 = _slicedToArray(_useState103, 2),
    fishingLuckyNext = _useState104[0],
    setFishingLuckyNext = _useState104[1];
  var _useState105 = useState(false),
    _useState106 = _slicedToArray(_useState105, 2),
    showEncyclopedia = _useState106[0],
    setShowEncyclopedia = _useState106[1];
  var _useState107 = useState(0),
    _useState108 = _slicedToArray(_useState107, 2),
    bonusEarned = _useState108[0],
    setBonusEarned = _useState108[1];
  var _useState109 = useState(false),
    _useState110 = _slicedToArray(_useState109, 2),
    echoTriggered = _useState110[0],
    setEchoTriggered = _useState110[1];
  var _useState111 = useState(false),
    _useState112 = _slicedToArray(_useState111, 2),
    jackpotHit = _useState112[0],
    setJackpotHit = _useState112[1];
  var _useState113 = useState(false),
    _useState114 = _slicedToArray(_useState113, 2),
    resilienceTriggered = _useState114[0],
    setResilienceTriggered = _useState114[1];
  var _useState115 = useState(false),
    _useState116 = _slicedToArray(_useState115, 2),
    luckySevenTriggered = _useState116[0],
    setLuckySevenTriggered = _useState116[1];
  var _useState117 = useState(false),
    _useState118 = _slicedToArray(_useState117, 2),
    fortuneCharmTriggered = _useState118[0],
    setFortuneCharmTriggered = _useState118[1];
  var _useState119 = useState(gameState.regen_recharge_wins || 0),
    _useState120 = _slicedToArray(_useState119, 2),
    regenRechargeWins = _useState120[0],
    setRegenRechargeWins = _useState120[1];
  var _useState121 = useState(null),
    _useState122 = _slicedToArray(_useState121, 2),
    catchUpSummary = _useState122[0],
    setCatchUpSummary = _useState122[1];
  var _useState123 = useState(null),
    _useState124 = _slicedToArray(_useState123, 2),
    fishCatchUpSummary = _useState124[0],
    setFishCatchUpSummary = _useState124[1];
  var _useState125 = useState(gameState.happy_hour || false),
    _useState126 = _slicedToArray(_useState125, 2),
    happyHour = _useState126[0],
    setHappyHour = _useState126[1];
  var _useState127 = useState(false),
    _useState128 = _slicedToArray(_useState127, 2),
    happyHourDismissed = _useState128[0],
    setHappyHourDismissed = _useState128[1];
  var _useState129 = useState(false),
    _useState130 = _slicedToArray(_useState129, 2),
    catchupBonus = _useState130[0],
    setCatchupBonus = _useState130[1];
  var _useState131 = useState(gameState.owned_items),
    _useState132 = _slicedToArray(_useState131, 2),
    ownedItems = _useState132[0],
    setOwnedItems = _useState132[1];
  var _useState133 = useState(gameState.equipped_fish),
    _useState134 = _slicedToArray(_useState133, 2),
    equippedFish = _useState134[0],
    setEquippedFish = _useState134[1];
  var _useState135 = useState(gameState.active_cosmetics || []),
    _useState136 = _slicedToArray(_useState135, 2),
    activeCosmetics = _useState136[0],
    setActiveCosmetics = _useState136[1];
  var _useState137 = useState(gameState.equipped_class || null),
    _useState138 = _slicedToArray(_useState137, 2),
    equippedClass = _useState138[0],
    setEquippedClass = _useState138[1];
  var _useState139 = useState(gameState.proc_streak || 0),
    _useState140 = _slicedToArray(_useState139, 2),
    procStreak = _useState140[0],
    setProcStreak = _useState140[1];
  var _useState141 = useState(gameState.fish_exchange_total || 0),
    _useState142 = _slicedToArray(_useState141, 2),
    fishExchangeTotal = _useState142[0],
    setFishExchangeTotal = _useState142[1];
  var _useState143 = useState(false),
    _useState144 = _slicedToArray(_useState143, 2),
    showStats = _useState144[0],
    setShowStats = _useState144[1];
  var _useState145 = useState(false),
    _useState146 = _slicedToArray(_useState145, 2),
    showPatchNotes = _useState146[0],
    setShowPatchNotes = _useState146[1];
  var _useState147 = useState(null),
    _useState148 = _slicedToArray(_useState147, 2),
    toast = _useState148[0],
    setToast = _useState148[1];
  var _useState149 = useState(gameState.season || null),
    _useState150 = _slicedToArray(_useState149, 2),
    season = _useState150[0],
    setSeason = _useState150[1];
  var _useState151 = useState(gameState.community_pot || {
      total_contributed: 0,
      target: 1000,
      filled: false,
      active: false,
      win_chance_pct: 50.0
    }),
    _useState152 = _slicedToArray(_useState151, 2),
    communityPot = _useState152[0],
    setCommunityPot = _useState152[1];
  var _useState153 = useState(gameState.spin_count || 0),
    _useState154 = _slicedToArray(_useState153, 2),
    spinCount = _useState154[0],
    setSpinCount = _useState154[1];
  var _useState155 = useState(gameState.win_count || 0),
    _useState156 = _slicedToArray(_useState155, 2),
    winCount = _useState156[0],
    setWinCount = _useState156[1];
  var _useState157 = useState(function () {
      var _gameState$low_spec_m;
      return (_gameState$low_spec_m = gameState.low_spec_mode) !== null && _gameState$low_spec_m !== void 0 ? _gameState$low_spec_m : localStorage.getItem('lowSpecMode') === 'true';
    }),
    _useState158 = _slicedToArray(_useState157, 2),
    lowSpec = _useState158[0],
    setLowSpec = _useState158[1];
  var _useState159 = useState(function () {
      return localStorage.getItem('parallaxEnabled') !== 'false';
    }),
    _useState160 = _slicedToArray(_useState159, 2),
    parallaxEnabled = _useState160[0],
    setParallaxEnabled = _useState160[1];
  var _useState161 = useState(false),
    _useState162 = _slicedToArray(_useState161, 2),
    shopCollapsed = _useState162[0],
    setShopCollapsed = _useState162[1];
  var _useState163 = useState(false),
    _useState164 = _slicedToArray(_useState163, 2),
    diceRolling = _useState164[0],
    setDiceRolling = _useState164[1];
  var _useState165 = useState(null),
    _useState166 = _slicedToArray(_useState165, 2),
    diceResult = _useState166[0],
    setDiceResult = _useState166[1];
  var _useState167 = useState((_gameState$dice_charg = gameState.dice_charges) !== null && _gameState$dice_charg !== void 0 ? _gameState$dice_charg : 1),
    _useState168 = _slicedToArray(_useState167, 2),
    diceCharges = _useState168[0],
    setDiceCharges = _useState168[1];
  var _useState169 = useState(gameState.dice_last_recharge || new Date().toISOString()),
    _useState170 = _slicedToArray(_useState169, 2),
    diceLastRecharge = _useState170[0],
    setDiceLastRecharge = _useState170[1];
  var _useState171 = useState((_gameState$dice_rolle = gameState.dice_rolled_since_spin) !== null && _gameState$dice_rolle !== void 0 ? _gameState$dice_rolle : false),
    _useState172 = _slicedToArray(_useState171, 2),
    diceRolledSinceSpin = _useState172[0],
    setDiceRolledSinceSpin = _useState172[1];
  var _useState173 = useState(function () {
      return window.innerWidth <= 768;
    }),
    _useState174 = _slicedToArray(_useState173, 2),
    isMobile = _useState174[0],
    setIsMobile = _useState174[1];
  var _useState175 = useState(null),
    _useState176 = _slicedToArray(_useState175, 2),
    mobilePanel = _useState176[0],
    setMobilePanel = _useState176[1];
  var _useState177 = useState(function () {
      return localStorage.getItem('chat_open') !== 'false';
    }),
    _useState178 = _slicedToArray(_useState177, 2),
    showChat = _useState178[0],
    setShowChat = _useState178[1];
  var fireMode = 2; // Mix mode
  var _useState179 = useState(0),
    _useState180 = _slicedToArray(_useState179, 2),
    wheelRotation = _useState180[0],
    setWheelRotation = _useState180[1];
  var wheelRotationRef = useRef(0);
  var _useState181 = useState({
      clickmult_inf: gameState.clickmult_inf_level || 0
    }),
    _useState182 = _slicedToArray(_useState181, 2),
    infLevels = _useState182[0],
    setInfLevels = _useState182[1];
  var WHEEL_SPIN_SPEED = 1.5; // seconds

  // Season 8: manual spin state (tab-lock ID mirrors HiatusWheel pattern)
  var _useState183 = useState(false),
    _useState184 = _slicedToArray(_useState183, 2),
    spinning = _useState184[0],
    setSpinning = _useState184[1];
  var spinningRef = useRef(false);
  var tabIdRef = useRef(function () {
    var id = sessionStorage.getItem('wheel_tab_id');
    if (!id) {
      id = Math.random().toString(36).slice(2) + Date.now().toString(36);
      sessionStorage.setItem('wheel_tab_id', id);
    }
    return id;
  }());
  // Season 8: auto-spin budget (0 = inactive)

  var toggleMobilePanel = useCallback(function (panel) {
    setMobilePanel(function (prev) {
      return prev === panel ? null : panel;
    });
  }, []);
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
    if (activeCosmetics.includes('theme_vintage')) return 'vintage';
    if (activeCosmetics.includes('theme_aurora')) return 'aurora';
    if (activeCosmetics.includes('theme_frost')) return 'frost';
    if (activeCosmetics.includes('theme_ember')) return 'ember';
    if (activeCosmetics.includes('theme_tidal')) return 'tidal';
    if (activeCosmetics.includes('page_season7')) return 'wormhole';
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
    if (activeCosmetics.includes('page_season7')) return 'page-season7';
    if (activeCosmetics.includes('page_season1')) return 'page-season1';
    if (activeCosmetics.includes('page_season2')) return 'page-season2';
    if (activeCosmetics.includes('page_season3')) return 'page-season3';
    if (activeCosmetics.includes('page_season4')) return 'page-season4';
    if (activeCosmetics.includes('page_season5')) return 'page-season5';
    if (activeCosmetics.includes('page_season6')) return 'page-season6';
    return '';
  }, [activeCosmetics]);
  var wormholeActive = activeCosmetics.includes('page_season7');
  var fishTimerRef = useRef(null);
  var toastTimerRef = useRef(null);
  var confettiTimerRef = useRef(null);
  var showResultRef = useRef(false);
  var activeCosmeticsRef = useRef(activeCosmetics);
  var lowSpecRef = useRef(lowSpec);
  var tickPendingRef = useRef(false);
  var resultAutoCloseRef = useRef(null);
  var wheelThemeRef = useRef(null);
  useEffect(function () {
    activeCosmeticsRef.current = activeCosmetics;
  }, [activeCosmetics]);
  useEffect(function () {
    lowSpecRef.current = lowSpec;
  }, [lowSpec]);
  useEffect(function () {
    wheelThemeRef.current = wheelTheme;
  }, [wheelTheme]);
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
    var show = bgClass === 'bg-ocean' && !wormholeActive;
    var iframe = document.getElementById('seabed-bg');
    var overlay = document.getElementById('seabed-overlay');
    if (iframe) iframe.style.display = show ? 'block' : 'none';
    if (overlay) overlay.style.display = show ? 'block' : 'none';
  }, [bgClass, wormholeActive]);
  useEffect(function () {
    setSessionExpiredHandler(onSessionExpired);
    return function () {
      return setSessionExpiredHandler(null);
    };
  }, [onSessionExpired]);
  useEffect(function () {
    var currentNumber = season ? season.season_number : null;
    var id = setInterval(/*#__PURE__*/_asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee9() {
      var r, gs, _gs$data$dice_rolled_;
      return _regeneratorRuntime().wrap(function _callee9$(_context9) {
        while (1) switch (_context9.prev = _context9.next) {
          case 0:
            _context9.next = 2;
            return apiFetch('/api/season');
          case 2:
            r = _context9.sent;
            if (r.ok) {
              _context9.next = 5;
              break;
            }
            return _context9.abrupt("return");
          case 5:
            if (!(currentNumber !== null && r.data.season_number !== currentNumber)) {
              _context9.next = 13;
              break;
            }
            showToast("Season ".concat(season.season_name || currentNumber, " has ended! Season ").concat(r.data.season_name || r.data.season_number, " begins!"));
            _context9.next = 9;
            return apiGame('/api/state');
          case 9:
            gs = _context9.sent;
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
                clickmult_inf: gs.data.clickmult_inf_level || 0
              });
              setEquippedClass(gs.data.equipped_class || null);
              setProcStreak(gs.data.proc_streak || 0);
              setFishExchangeTotal(gs.data.fish_exchange_total || 0);
              if (gs.data.caught_species) setCaughtSpecies(gs.data.caught_species);
              setFishingLuckyNext(gs.data.fishing_lucky_next || false);
              if (gs.data.dice_charges != null) setDiceCharges(gs.data.dice_charges);
              if (gs.data.dice_last_recharge) setDiceLastRecharge(gs.data.dice_last_recharge);
              setDiceRolledSinceSpin((_gs$data$dice_rolled_ = gs.data.dice_rolled_since_spin) !== null && _gs$data$dice_rolled_ !== void 0 ? _gs$data$dice_rolled_ : false);
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
            }
            _context9.next = 14;
            break;
          case 13:
            setSeason(r.data);
          case 14:
          case "end":
            return _context9.stop();
        }
      }, _callee9);
    })), 60000);
    return function () {
      return clearInterval(id);
    };
  }, [season ? season.season_number : null]); // eslint-disable-line

  useEffect(function () {
    if (!season) return;
    var key = "patchNotesSeen_s".concat(season.season_number);
    if (!localStorage.getItem(key)) {
      setShowPatchNotes(true);
    }
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
    if (canvas) drawWheel(canvas, wheelTheme, activeWheelMode);
  }, [wheelTheme, activeWheelMode]);
  var showToast = useCallback(function (msg) {
    setToast(msg);
    if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
    toastTimerRef.current = setTimeout(function () {
      return setToast(null);
    }, 3000);
  }, []);
  var handleClosePatchNotes = useCallback(function () {
    setShowPatchNotes(false);
    if (season) localStorage.setItem("patchNotesSeen_s".concat(season.season_number), '1');
  }, [season]);
  var handleBuy = useCallback(/*#__PURE__*/function () {
    var _ref35 = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee0(id) {
      var _yield$apiGame6, ok, data, _data$regen_recharge_;
      return _regeneratorRuntime().wrap(function _callee0$(_context0) {
        while (1) switch (_context0.prev = _context0.next) {
          case 0:
            _context0.next = 2;
            return apiGame('/api/buy', {
              method: 'POST',
              body: JSON.stringify({
                item_id: id
              })
            });
          case 2:
            _yield$apiGame6 = _context0.sent;
            ok = _yield$apiGame6.ok;
            data = _yield$apiGame6.data;
            if (ok) {
              setFishClicks(data.fish_clicks);
              if (data.wins != null) setWins(data.wins);
              if (data.losses != null) setLosses(data.losses);
              setOwnedItems(data.owned_items);
              setRegenRechargeWins((_data$regen_recharge_ = data.regen_recharge_wins) !== null && _data$regen_recharge_ !== void 0 ? _data$regen_recharge_ : 0);
              if (data.active_cosmetics) setActiveCosmetics(data.active_cosmetics);
              if (data.clickmult_inf_level != null) {
                setInfLevels(function (prev) {
                  return _objectSpread(_objectSpread({}, prev), {}, {
                    clickmult_inf: data.clickmult_inf_level
                  });
                });
              }
            } else {
              showToast(data.error || 'Purchase failed');
            }
          case 6:
          case "end":
            return _context0.stop();
        }
      }, _callee0);
    }));
    return function (_x6) {
      return _ref35.apply(this, arguments);
    };
  }(), [showToast]);
  var handleEquip = useCallback(/*#__PURE__*/function () {
    var _ref36 = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee1(id) {
      var _yield$apiGame7, ok, data;
      return _regeneratorRuntime().wrap(function _callee1$(_context1) {
        while (1) switch (_context1.prev = _context1.next) {
          case 0:
            _context1.next = 2;
            return apiGame('/api/equip', {
              method: 'POST',
              body: JSON.stringify({
                fish_id: id
              })
            });
          case 2:
            _yield$apiGame7 = _context1.sent;
            ok = _yield$apiGame7.ok;
            data = _yield$apiGame7.data;
            if (ok) setEquippedFish(data.equipped_fish);else showToast(data.error || 'Equip failed');
          case 6:
          case "end":
            return _context1.stop();
        }
      }, _callee1);
    }));
    return function (_x7) {
      return _ref36.apply(this, arguments);
    };
  }(), [showToast]);
  var handleEquipCosmetic = useCallback(/*#__PURE__*/function () {
    var _ref37 = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee10(id) {
      var _yield$apiGame8, ok, data;
      return _regeneratorRuntime().wrap(function _callee10$(_context10) {
        while (1) switch (_context10.prev = _context10.next) {
          case 0:
            _context10.next = 2;
            return apiGame('/api/equip-cosmetic', {
              method: 'POST',
              body: JSON.stringify({
                item_id: id
              })
            });
          case 2:
            _yield$apiGame8 = _context10.sent;
            ok = _yield$apiGame8.ok;
            data = _yield$apiGame8.data;
            if (ok) setActiveCosmetics(data.active_cosmetics);else showToast(data.error || 'Equip failed');
          case 6:
          case "end":
            return _context10.stop();
        }
      }, _callee10);
    }));
    return function (_x8) {
      return _ref37.apply(this, arguments);
    };
  }(), [showToast]);
  var handleEquipClass = useCallback(/*#__PURE__*/function () {
    var _ref38 = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee11(classItemId) {
      var isCurrentlyEquipped, newClassId, _yield$apiGame9, ok, data;
      return _regeneratorRuntime().wrap(function _callee11$(_context11) {
        while (1) switch (_context11.prev = _context11.next) {
          case 0:
            isCurrentlyEquipped = equippedClass === classItemId.replace('class_', '');
            newClassId = isCurrentlyEquipped ? null : classItemId;
            _context11.next = 4;
            return apiGame('/api/equip-class', {
              method: 'POST',
              body: JSON.stringify({
                class_id: newClassId
              })
            });
          case 4:
            _yield$apiGame9 = _context11.sent;
            ok = _yield$apiGame9.ok;
            data = _yield$apiGame9.data;
            if (ok) setEquippedClass(data.equipped_class);else showToast(data.error || 'Equip failed');
          case 8:
          case "end":
            return _context11.stop();
        }
      }, _callee11);
    }));
    return function (_x9) {
      return _ref38.apply(this, arguments);
    };
  }(), [equippedClass, showToast]);
  var handleFishExchange = useCallback(/*#__PURE__*/function () {
    var _ref39 = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee12(amountType) {
      var _yield$apiGame0, ok, data;
      return _regeneratorRuntime().wrap(function _callee12$(_context12) {
        while (1) switch (_context12.prev = _context12.next) {
          case 0:
            _context12.next = 2;
            return apiGame('/api/fish-exchange', {
              method: 'POST',
              body: JSON.stringify({
                amount: amountType
              })
            });
          case 2:
            _yield$apiGame0 = _context12.sent;
            ok = _yield$apiGame0.ok;
            data = _yield$apiGame0.data;
            if (ok) {
              setFishClicks(data.fish_clicks);
              setWins(data.wins);
              setFishExchangeTotal(function (prev) {
                return prev + data.fish_spent;
              });
              showToast("Exchanged ".concat(fmt(data.fish_spent), " \uD83D\uDC1F \u2192 +").concat(fmt(data.wins_earned), " \uD83C\uDFC6"));
            } else {
              showToast(data.error || 'Exchange failed');
            }
          case 6:
          case "end":
            return _context12.stop();
        }
      }, _callee12);
    }));
    return function (_x0) {
      return _ref39.apply(this, arguments);
    };
  }(), [showToast]);
  var handleWinsExchange = useCallback(/*#__PURE__*/function () {
    var _ref40 = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee13(amountType) {
      var _yield$apiGame1, ok, data;
      return _regeneratorRuntime().wrap(function _callee13$(_context13) {
        while (1) switch (_context13.prev = _context13.next) {
          case 0:
            _context13.next = 2;
            return apiGame('/api/wins-exchange', {
              method: 'POST',
              body: JSON.stringify({
                amount: amountType
              })
            });
          case 2:
            _yield$apiGame1 = _context13.sent;
            ok = _yield$apiGame1.ok;
            data = _yield$apiGame1.data;
            if (ok) {
              setWins(data.wins);
              setFishClicks(data.fish_clicks);
              showToast("Exchanged ".concat(fmt(data.wins_spent), " \uD83C\uDFC6 \u2192 +").concat(fmt(data.fish_earned), " \uD83D\uDC1F"));
            } else {
              showToast(data.error || 'Exchange failed');
            }
          case 6:
          case "end":
            return _context13.stop();
        }
      }, _callee13);
    }));
    return function (_x1) {
      return _ref40.apply(this, arguments);
    };
  }(), [showToast]);
  var handleDiceRoll = useCallback(/*#__PURE__*/_asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee14() {
    var prevStreak, _yield$apiGame10, ok, data;
    return _regeneratorRuntime().wrap(function _callee14$(_context14) {
      while (1) switch (_context14.prev = _context14.next) {
        case 0:
          if (!diceRolling) {
            _context14.next = 2;
            break;
          }
          return _context14.abrupt("return");
        case 2:
          setDiceRolling(true);
          setDiceResult(null);
          prevStreak = streak;
          _context14.next = 7;
          return apiGame('/api/roll-dice', {
            method: 'POST',
            body: JSON.stringify({})
          });
        case 7:
          _yield$apiGame10 = _context14.sent;
          ok = _yield$apiGame10.ok;
          data = _yield$apiGame10.data;
          if (ok) {
            _context14.next = 14;
            break;
          }
          showToast(data.error || 'Roll failed');
          setDiceRolling(false);
          return _context14.abrupt("return");
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
              streak_after: data.streak,
              pending: true
            });
            // Streak is applied by the next /api/tick, not immediately
            if (data.dice_charges != null) setDiceCharges(data.dice_charges);
            if (data.dice_last_recharge) setDiceLastRecharge(data.dice_last_recharge);
            setDiceRolledSinceSpin(true);
            setDiceRolling(false);
          }, lowSpec ? 100 : 1200);
        case 15:
        case "end":
          return _context14.stop();
      }
    }, _callee14);
  })), [diceRolling, streak, lowSpec, showToast]);

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
    setRegenRechargeWins((_data$regen_recharge_2 = data.regen_recharge_wins) !== null && _data$regen_recharge_2 !== void 0 ? _data$regen_recharge_2 : 0);
    if (data.owned_items) {
      var spinResult = new Set(data.owned_items);
      // Sync guard from spin result (can be removed by guard block).
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
    if (data.dice_charges != null) setDiceCharges(data.dice_charges);
    if (data.dice_last_recharge) setDiceLastRecharge(data.dice_last_recharge);
    setDiceRolledSinceSpin(false);
    if (data.wins_delta > 0) setWinCount(function (prev) {
      return prev + 1;
    });
    if (data.proc_streak != null) setProcStreak(data.proc_streak);
    // Season 8: update wager state from spin result
    if (data.wager_streak != null) setWagerStreak(data.wager_streak);
    if (data.stake != null) setWagerLastStake(data.stake);
    if (data.onboarding_advance) {
      setOnboardingStep(function (prev) {
        var next = Math.max(prev, 1);
        if (next >= 5) setShowOnboarding(false);
        return next;
      });
    }
    // Season 8: refresh bounties & community goal after every spin
    refreshBountiesAndGoal();
    // Season 8: update community goal from state poll
    setShieldFeedback(data.shield_used ? {
      type: data.shield_used_type,
      broke: data.shield_broke,
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
  }, [showToast]);

  // Dismiss the result banner smoothly
  var dismissResult = useCallback(function () {
    if (!showResultRef.current) return;
    setHideResult(true);
    setShowResultSync(false);
    setConfetti(false);
    setTimeout(function () {
      setHideResult(false);
      setResult(null);
      setShieldFeedback(null);
    }, 350);
  }, []);

  // Schedule auto-dismissal of the result banner after 2.5s
  var scheduleResultDismiss = useCallback(function () {
    if (resultAutoCloseRef.current) clearTimeout(resultAutoCloseRef.current);
    resultAutoCloseRef.current = setTimeout(dismissResult, 2500);
  }, [dismissResult]);
  var applyFishCatchUp = useCallback(function (fc) {
    if (!fc || fc.fish_count === 0) return;
    setFishClicks(fc.fish_clicks);
    if (fc.new_species && fc.new_species.length > 0) {
      setCaughtSpecies(function (prev) {
        var s = new Set(prev);
        fc.new_species.forEach(function (id) {
          return s.add(id);
        });
        return _toConsumableArray(s);
      });
    }
    var hrs = Math.floor(fc.elapsed_seconds / 3600);
    var mins = Math.floor(fc.elapsed_seconds % 3600 / 60);
    var timeStr = hrs > 0 ? "".concat(hrs, "h ").concat(mins, "m") : "".concat(mins, "m");
    setFishCatchUpSummary("\uD83C\uDFA3 Away ".concat(timeStr, " \u2014 ").concat(fc.fish_count, " fish auto-caught (+").concat(fmt(fc.total_value), " \uD83D\uDC1F)"));
    setTimeout(function () {
      return setFishCatchUpSummary(null);
    }, 5000);
  }, []);

  // Season 8: manual spin (replaces always-on auto-spin as the primary game action)
  var handleManualSpin = useCallback(/*#__PURE__*/_asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee15() {
    var res, _res$data, data, seg, nextRot;
    return _regeneratorRuntime().wrap(function _callee15$(_context15) {
      while (1) switch (_context15.prev = _context15.next) {
        case 0:
          if (!spinningRef.current) {
            _context15.next = 2;
            break;
          }
          return _context15.abrupt("return");
        case 2:
          spinningRef.current = true;
          setSpinning(true);
          _context15.prev = 4;
          _context15.next = 7;
          return apiGame('/api/spin', {
            method: 'POST',
            body: JSON.stringify({
              tab_id: tabIdRef.current,
              stake: stake
            })
          });
        case 7:
          res = _context15.sent;
          if (res.ok) {
            _context15.next = 13;
            break;
          }
          showToast(((_res$data = res.data) === null || _res$data === void 0 ? void 0 : _res$data.error) || 'Spin failed');
          spinningRef.current = false;
          setSpinning(false);
          return _context15.abrupt("return");
        case 13:
          data = res.data; // Animate wheel to the returned segment angle
          seg = data.angle % 360;
          nextRot = Math.ceil((wheelRotationRef.current + 2 * 360 - seg) / 360) * 360 + seg;
          wheelRotationRef.current = nextRot;
          setWheelRotation(nextRot);
          if (data.double_down_pending != null) setDoubleDownPending(data.double_down_pending);

          // Dismiss lingering result before showing new one
          if (showResultRef.current) dismissResult();
          setBonusEarned(0);
          setEchoTriggered(false);
          setJackpotHit(false);
          setResilienceTriggered(false);
          setLuckySevenTriggered(false);
          setFortuneCharmTriggered(false);
          setTimeout(function () {
            if (data.guard_triggered) {
              setGuardState({
                blocked: data.guard_blocked
              });
              guardCompleteRef.current = function () {
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
          _context15.next = 34;
          break;
        case 29:
          _context15.prev = 29;
          _context15.t0 = _context15["catch"](4);
          showToast('Spin failed');
          spinningRef.current = false;
          setSpinning(false);
        case 34:
        case "end":
          return _context15.stop();
      }
    }, _callee15, null, [[4, 29]]);
  })), [stake, showToast, applySpinResult, scheduleResultDismiss, dismissResult]);
  var tick = useCallback(/*#__PURE__*/_asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee16() {
    var res, data, hrs, mins, timeStr, spinResult, seg, nextRot;
    return _regeneratorRuntime().wrap(function _callee16$(_context16) {
      while (1) switch (_context16.prev = _context16.next) {
        case 0:
          if (!tickPendingRef.current) {
            _context16.next = 2;
            break;
          }
          return _context16.abrupt("return");
        case 2:
          tickPendingRef.current = true;
          _context16.prev = 3;
          _context16.next = 6;
          return apiGame('/api/tick', {
            method: 'POST',
            body: JSON.stringify({})
          });
        case 6:
          res = _context16.sent;
          if (res.ok) {
            _context16.next = 9;
            break;
          }
          return _context16.abrupt("return");
        case 9:
          data = res.data;
          if (!(data.auto_spin_active === false)) {
            _context16.next = 12;
            break;
          }
          return _context16.abrupt("return");
        case 12:
          if (data.happy_hour != null) setHappyHour(data.happy_hour);
          if (!data.started) {
            _context16.next = 15;
            break;
          }
          return _context16.abrupt("return");
        case 15:
          if (!data.catch_up) {
            _context16.next = 24;
            break;
          }
          // Many spins processed offline — show summary, update state silently
          if (data.state) {
            if (data.state.wins != null) setWins(data.state.wins);
            if (data.state.losses != null) setLosses(data.state.losses);
            if (data.state.streak != null) setStreak(data.state.streak);
            if (data.state.owned_items) setOwnedItems(function (prev) {
              var s = new Set(data.state.owned_items);
              var withoutGuard = prev.filter(function (id) {
                return id !== 'guard';
              });
              return s.has('guard') ? [].concat(_toConsumableArray(withoutGuard), ['guard']) : withoutGuard;
            });
            if (data.state.regen_recharge_wins != null) setRegenRechargeWins(data.state.regen_recharge_wins);
            if (data.state.active_cosmetics) setActiveCosmetics(data.state.active_cosmetics);
            if (data.state.spin_count != null) setSpinCount(data.state.spin_count);
            if (data.state.win_count != null) setWinCount(data.state.win_count);
            if (data.state.dice_charges != null) setDiceCharges(data.state.dice_charges);
            if (data.state.catchup_bonus_active != null) setCatchupBonus(data.state.catchup_bonus_active);
            if (data.state.proc_streak != null) setProcStreak(data.state.proc_streak);
            setDiceRolledSinceSpin(false);
          }
          hrs = Math.floor(data.elapsed_seconds / 3600);
          mins = Math.floor(data.elapsed_seconds % 3600 / 60);
          timeStr = hrs > 0 ? "".concat(hrs, "h ").concat(mins, "m") : "".concat(mins, "m");
          setCatchUpSummary("\u23F0 Away ".concat(timeStr, " \u2014 ").concat(data.spins_processed, " spins processed"));
          setTimeout(function () {
            return setCatchUpSummary(null);
          }, 5000);
          if (data.fish_catchup) applyFishCatchUp(data.fish_catchup);
          return _context16.abrupt("return");
        case 24:
          if (!(!data.spins || data.spins.length === 0)) {
            _context16.next = 26;
            break;
          }
          return _context16.abrupt("return");
        case 26:
          spinResult = data.spins[data.spins.length - 1]; // Dismiss any lingering result before showing the new one
          if (showResultRef.current) dismissResult();
          setBonusEarned(0);
          setEchoTriggered(false);
          setJackpotHit(false);
          setResilienceTriggered(false);
          setLuckySevenTriggered(false);
          setFortuneCharmTriggered(false);

          // Advance wheel to the correct result segment (same formula as HiatusWheel)
          seg = spinResult.angle % 360;
          nextRot = Math.ceil((wheelRotationRef.current + 2 * 360 - seg) / 360) * 360 + seg;
          wheelRotationRef.current = nextRot;
          setWheelRotation(nextRot);
          setTimeout(function () {
            if (spinResult.guard_triggered) {
              setGuardState({
                blocked: spinResult.guard_blocked
              });
              guardCompleteRef.current = function () {
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
        case 41:
          _context16.prev = 41;
          tickPendingRef.current = false;
          return _context16.finish(41);
        case 44:
        case "end":
          return _context16.stop();
      }
    }, _callee16, null, [[3,, 41, 44]]);
  })), [applySpinResult, applyFishCatchUp, dismissResult, scheduleResultDismiss]);

  // Poll happy_hour status every minute (in case of time zone changes or missed state update)
  useEffect(function () {
    var id = setInterval(function () {
      apiFetch('/api/season').then(function (r) {
        if (r.ok && r.data.happy_hour != null) setHappyHour(r.data.happy_hour);
      });
    }, 60000);
    return function () {
      return clearInterval(id);
    };
  }, []);
  var handleLogout = /*#__PURE__*/function () {
    var _ref44 = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee17() {
      return _regeneratorRuntime().wrap(function _callee17$(_context17) {
        while (1) switch (_context17.prev = _context17.next) {
          case 0:
            _context17.next = 2;
            return apiFetch('/api/logout', {
              method: 'POST',
              body: '{}'
            });
          case 2:
            onLogout();
          case 3:
          case "end":
            return _context17.stop();
        }
      }, _callee17);
    }));
    return function handleLogout() {
      return _ref44.apply(this, arguments);
    };
  }();

  // ── Season 8 state ─────────────────────────────────────────────────────────
  var _useState185 = useState(gameState.prestige_level || 0),
    _useState186 = _slicedToArray(_useState185, 2),
    prestigeLevel = _useState186[0],
    setPrestigeLevel = _useState186[1];
  var _useState187 = useState(gameState.prestige_count || 0),
    _useState188 = _slicedToArray(_useState187, 2),
    prestigeCount = _useState188[0],
    setPrestigeCount = _useState188[1];
  var _useState189 = useState(gameState.legacy_wins || 0),
    _useState190 = _slicedToArray(_useState189, 2),
    legacyWins = _useState190[0],
    setLegacyWins = _useState190[1];
  var _useState191 = useState(gameState.onboarding_step || 0),
    _useState192 = _slicedToArray(_useState191, 2),
    onboardingStep = _useState192[0],
    setOnboardingStep = _useState192[1];
  var _useState193 = useState(gameState.wager_streak || 0),
    _useState194 = _slicedToArray(_useState193, 2),
    wagerStreak = _useState194[0],
    setWagerStreak = _useState194[1];
  var _useState195 = useState(gameState.wager_last_stake || 1),
    _useState196 = _slicedToArray(_useState195, 2),
    wagerLastStake = _useState196[0],
    setWagerLastStake = _useState196[1];
  var _useState197 = useState(gameState.double_down_pending || false),
    _useState198 = _slicedToArray(_useState197, 2),
    doubleDownPending = _useState198[0],
    setDoubleDownPending = _useState198[1];
  var _useState199 = useState(gameState.wager_banked_wins || 0),
    _useState200 = _slicedToArray(_useState199, 2),
    wagerBankedWins = _useState200[0],
    setWagerBankedWins = _useState200[1];
  var _useState201 = useState(gameState.wager_insurance_charges || 0),
    _useState202 = _slicedToArray(_useState201, 2),
    wagerInsuranceCharges = _useState202[0],
    setWagerInsuranceCharges = _useState202[1];
  var _useState203 = useState(gameState.active_wheel_mode || 'steady'),
    _useState204 = _slicedToArray(_useState203, 2),
    activeWheelMode = _useState204[0],
    setActiveWheelMode = _useState204[1];
  var _useState205 = useState(gameState.available_wheel_modes || ['steady', 'volatile']),
    _useState206 = _slicedToArray(_useState205, 2),
    availableWheelModes = _useState206[0],
    setAvailableWheelModes = _useState206[1];
  var _useState207 = useState(gameState.wager_tokens || 0),
    _useState208 = _slicedToArray(_useState207, 2),
    wagerTokens = _useState208[0],
    setWagerTokens = _useState208[1];
  var _useState209 = useState(gameState.aquarium_species || []),
    _useState210 = _slicedToArray(_useState209, 2),
    aquariumSpecies = _useState210[0],
    setAquariumSpecies = _useState210[1];
  var _useState211 = useState(gameState.cosmetic_fragments || 0),
    _useState212 = _slicedToArray(_useState211, 2),
    cosmeticFragments = _useState212[0],
    setCosmeticFragments = _useState212[1];
  var _useState213 = useState(gameState.guard_charges || 0),
    _useState214 = _slicedToArray(_useState213, 2),
    guardCharges = _useState214[0],
    setGuardCharges = _useState214[1];
  var _useState215 = useState(gameState.bounties || []),
    _useState216 = _slicedToArray(_useState215, 2),
    bounties = _useState216[0],
    setBounties = _useState216[1];
  var _useState217 = useState(gameState.community_goal || null),
    _useState218 = _slicedToArray(_useState217, 2),
    communityGoal = _useState218[0],
    setCommunityGoal = _useState218[1];
  var _useState219 = useState(gameState.singularity || null),
    _useState220 = _slicedToArray(_useState219, 2),
    singularity = _useState220[0],
    setSingularity = _useState220[1];
  var _useState221 = useState(gameState.wager_last_stake || 1),
    _useState222 = _slicedToArray(_useState221, 2),
    stake = _useState222[0],
    setStake = _useState222[1];
  var _useState223 = useState(false),
    _useState224 = _slicedToArray(_useState223, 2),
    showPrestigeConfirm = _useState224[0],
    setShowPrestigeConfirm = _useState224[1];
  var _useState225 = useState((gameState.onboarding_step || 0) < 5),
    _useState226 = _slicedToArray(_useState225, 2),
    showOnboarding = _useState226[0],
    setShowOnboarding = _useState226[1];
  var _useState227 = useState(false),
    _useState228 = _slicedToArray(_useState227, 2),
    showLegacyBoards = _useState228[0],
    setShowLegacyBoards = _useState228[1];
  var _useState229 = useState([]),
    _useState230 = _slicedToArray(_useState229, 2),
    legacyBoards = _useState230[0],
    setLegacyBoards = _useState230[1];
  var refreshBountiesAndGoal = useCallback(/*#__PURE__*/_asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee18() {
    var _yield$Promise$all, _yield$Promise$all2, bountyRes, goalRes;
    return _regeneratorRuntime().wrap(function _callee18$(_context18) {
      while (1) switch (_context18.prev = _context18.next) {
        case 0:
          _context18.next = 2;
          return Promise.all([apiGame('/api/bounties'), apiGame('/api/community-goal')]);
        case 2:
          _yield$Promise$all = _context18.sent;
          _yield$Promise$all2 = _slicedToArray(_yield$Promise$all, 2);
          bountyRes = _yield$Promise$all2[0];
          goalRes = _yield$Promise$all2[1];
          if (bountyRes.ok) setBounties(bountyRes.data.bounties || []);
          if (goalRes.ok && goalRes.data.goal) setCommunityGoal(goalRes.data.goal);
        case 8:
        case "end":
          return _context18.stop();
      }
    }, _callee18);
  })), []);

  // Clear any previously-set accessibility classes from localStorage
  useEffect(function () {
    localStorage.removeItem('reducedMotion');
    localStorage.removeItem('highContrast');
    document.body.classList.remove('reduced-motion', 'high-contrast');
  }, []);

  // Season 8: sync state from /api/state poll (season change handler already updates most state)
  // This runs on mount and when gameState changes
  useEffect(function () {
    if (gameState.prestige_level != null) setPrestigeLevel(gameState.prestige_level);
    if (gameState.prestige_count != null) setPrestigeCount(gameState.prestige_count);
    if (gameState.legacy_wins != null) setLegacyWins(gameState.legacy_wins);
    if (gameState.onboarding_step != null) {
      setOnboardingStep(gameState.onboarding_step);
      setShowOnboarding(gameState.onboarding_step < 5);
    }
    if (gameState.wager_streak != null) setWagerStreak(gameState.wager_streak);
    if (gameState.wager_last_stake != null) setWagerLastStake(gameState.wager_last_stake);
    if (gameState.double_down_pending != null) setDoubleDownPending(gameState.double_down_pending);
    if (gameState.wager_banked_wins != null) setWagerBankedWins(gameState.wager_banked_wins);
    if (gameState.wager_insurance_charges != null) setWagerInsuranceCharges(gameState.wager_insurance_charges);
    if (gameState.active_wheel_mode != null) setActiveWheelMode(gameState.active_wheel_mode);
    if (gameState.available_wheel_modes != null) setAvailableWheelModes(gameState.available_wheel_modes);
    if (gameState.wager_tokens != null) setWagerTokens(gameState.wager_tokens);
    if (gameState.aquarium_species != null) setAquariumSpecies(gameState.aquarium_species);
    if (gameState.cosmetic_fragments != null) setCosmeticFragments(gameState.cosmetic_fragments);
    if (gameState.guard_charges != null) setGuardCharges(gameState.guard_charges);
    if (gameState.bounties != null) setBounties(gameState.bounties);
    if (gameState.community_goal != null) setCommunityGoal(gameState.community_goal);
    if (gameState.singularity != null) setSingularity(gameState.singularity);
  }, []); // eslint-disable-line

  // Season 8: community goal background poll (15s interval, respects document.hidden)
  useEffect(function () {
    var ctrl = new AbortController();
    var load = /*#__PURE__*/function () {
      var _ref46 = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee19() {
        var _yield$apiGame11, ok, data;
        return _regeneratorRuntime().wrap(function _callee19$(_context19) {
          while (1) switch (_context19.prev = _context19.next) {
            case 0:
              if (!document.hidden) {
                _context19.next = 2;
                break;
              }
              return _context19.abrupt("return");
            case 2:
              ctrl.abort();
              ctrl = new AbortController();
              _context19.prev = 4;
              _context19.next = 7;
              return apiGame('/api/community-goal', {
                signal: ctrl.signal
              });
            case 7:
              _yield$apiGame11 = _context19.sent;
              ok = _yield$apiGame11.ok;
              data = _yield$apiGame11.data;
              if (ok && data.goal) setCommunityGoal(data.goal);
              _context19.next = 16;
              break;
            case 13:
              _context19.prev = 13;
              _context19.t0 = _context19["catch"](4);
              if (_context19.t0.name !== 'AbortError') console.error('Community goal poll failed', _context19.t0);
            case 16:
            case "end":
              return _context19.stop();
          }
        }, _callee19, null, [[4, 13]]);
      }));
      return function load() {
        return _ref46.apply(this, arguments);
      };
    }();
    load();
    var intervalId = setInterval(load, 15000);
    return function () {
      clearInterval(intervalId);
      ctrl.abort();
    };
  }, []);

  // Season 8: handle stake change
  var handleStakeChange = useCallback(/*#__PURE__*/function () {
    var _ref47 = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee20(newStake) {
      return _regeneratorRuntime().wrap(function _callee20$(_context20) {
        while (1) switch (_context20.prev = _context20.next) {
          case 0:
            setStake(newStake);
            _context20.next = 3;
            return apiGame('/api/wager/stake', {
              method: 'POST',
              body: JSON.stringify({
                stake: newStake
              })
            });
          case 3:
          case "end":
            return _context20.stop();
        }
      }, _callee20);
    }));
    return function (_x10) {
      return _ref47.apply(this, arguments);
    };
  }(), []);

  // Season 8: wheel mode descriptions for tooltips
  var WHEEL_MODE_INFO = {
    steady: {
      label: 'Steady',
      desc: '70% win · 28% loss · 2% jackpot (×25). Consistent and predictable.'
    },
    "volatile": {
      label: 'Volatile',
      desc: '45% win · 50% loss · 5% jackpot (×50). High variance — bigger swings both ways.'
    },
    inverted: {
      label: 'Inverted',
      desc: '60% win · 35% loss · 5% jackpot. Losses still build your streak bonus.'
    },
    gravity: {
      label: 'Gravity',
      desc: '55% win · 40% loss · 5% jackpot. Outcomes drift toward the last result — streaks amplify.'
    },
    mirror: {
      label: 'Mirror',
      desc: '65% win · 30% loss · 5% jackpot. Two spins resolved; the better result wins.'
    },
    singularity: {
      label: 'Singularity',
      desc: '75% win · 10% loss · 15% jackpot (×50). Unlocked when the Singularity meter fills.'
    }
  };

  // Season 8: handle wheel mode change
  var handleWheelModeChange = useCallback(/*#__PURE__*/function () {
    var _ref48 = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee21(mode) {
      var prev, _yield$apiGame12, ok, data;
      return _regeneratorRuntime().wrap(function _callee21$(_context21) {
        while (1) switch (_context21.prev = _context21.next) {
          case 0:
            prev = activeWheelMode;
            setActiveWheelMode(mode);
            if (canvasRef.current) drawWheel(canvasRef.current, wheelThemeRef.current || 'default', mode);
            _context21.next = 5;
            return apiGame('/api/wheel-mode', {
              method: 'POST',
              body: JSON.stringify({
                mode: mode
              })
            });
          case 5:
            _yield$apiGame12 = _context21.sent;
            ok = _yield$apiGame12.ok;
            data = _yield$apiGame12.data;
            if (!ok) {
              setActiveWheelMode(prev);
              if (canvasRef.current) drawWheel(canvasRef.current, wheelThemeRef.current || 'default', prev);
              showToast(data && data.error || 'Mode change failed');
            }
          case 9:
          case "end":
            return _context21.stop();
        }
      }, _callee21);
    }));
    return function (_x11) {
      return _ref48.apply(this, arguments);
    };
  }(), [showToast, activeWheelMode]);

  // Season 8: handle prestige
  var handlePrestige = useCallback(/*#__PURE__*/_asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee22() {
    var _yield$apiGame13, ok, data;
    return _regeneratorRuntime().wrap(function _callee22$(_context22) {
      while (1) switch (_context22.prev = _context22.next) {
        case 0:
          setShowPrestigeConfirm(false);
          _context22.next = 3;
          return apiGame('/api/prestige', {
            method: 'POST',
            body: JSON.stringify({})
          });
        case 3:
          _yield$apiGame13 = _context22.sent;
          ok = _yield$apiGame13.ok;
          data = _yield$apiGame13.data;
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
            showToast(" Prestiged to Level ".concat(data.prestige_level, "!"));
            refreshBountiesAndGoal();
          } else {
            showToast(data.error || 'Prestige failed');
          }
        case 7:
        case "end":
          return _context22.stop();
      }
    }, _callee22);
  })), [showToast]);

  // Season 8: handle guard activation
  var handleGuardActivate = useCallback(/*#__PURE__*/_asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee23() {
    var _yield$apiGame14, ok, data;
    return _regeneratorRuntime().wrap(function _callee23$(_context23) {
      while (1) switch (_context23.prev = _context23.next) {
        case 0:
          _context23.next = 2;
          return apiGame('/api/guard', {
            method: 'POST',
            body: JSON.stringify({})
          });
        case 2:
          _yield$apiGame14 = _context23.sent;
          ok = _yield$apiGame14.ok;
          data = _yield$apiGame14.data;
          if (ok) {
            setGuardCharges(function (prev) {
              return Math.max(0, prev - 1);
            });
            showToast('🛡️ Guard activated');
          } else {
            showToast(data.error || 'Guard failed');
          }
        case 6:
        case "end":
          return _context23.stop();
      }
    }, _callee23);
  })), [showToast]);

  // Season 8: handle bounty claim
  var handleBountyClaim = useCallback(/*#__PURE__*/function () {
    var _ref51 = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee24(bountyId) {
      var _yield$apiGame15, ok, data, _data$rewards, _data$rewards2;
      return _regeneratorRuntime().wrap(function _callee24$(_context24) {
        while (1) switch (_context24.prev = _context24.next) {
          case 0:
            _context24.next = 2;
            return apiGame('/api/bounties/claim', {
              method: 'POST',
              body: JSON.stringify({
                bounty_id: bountyId
              })
            });
          case 2:
            _yield$apiGame15 = _context24.sent;
            ok = _yield$apiGame15.ok;
            data = _yield$apiGame15.data;
            if (ok) {
              if ((_data$rewards = data.rewards) !== null && _data$rewards !== void 0 && _data$rewards.cosmetic_fragments) setCosmeticFragments(function (prev) {
                return prev + data.rewards.cosmetic_fragments;
              });
              if ((_data$rewards2 = data.rewards) !== null && _data$rewards2 !== void 0 && _data$rewards2.wins) setWins(function (prev) {
                return prev + data.rewards.wins;
              });
              setBounties(function (prev) {
                return prev.map(function (b) {
                  return b.bounty_id === bountyId ? _objectSpread(_objectSpread({}, b), {}, {
                    claimed: true
                  }) : b;
                });
              });
              showToast('Bounty claimed!');
            } else {
              showToast(data.error || 'Claim failed');
            }
          case 6:
          case "end":
            return _context24.stop();
        }
      }, _callee24);
    }));
    return function (_x12) {
      return _ref51.apply(this, arguments);
    };
  }(), [showToast]);

  // Season 8: handle singularity contribution (spec S13: deducts fish_clicks, not wins)
  var handleSingularityContribute = useCallback(/*#__PURE__*/function () {
    var _ref52 = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee25(amount) {
      var _yield$apiGame16, ok, data;
      return _regeneratorRuntime().wrap(function _callee25$(_context25) {
        while (1) switch (_context25.prev = _context25.next) {
          case 0:
            _context25.next = 2;
            return apiGame('/api/singularity/contribute', {
              method: 'POST',
              body: JSON.stringify({
                amount: amount
              })
            });
          case 2:
            _yield$apiGame16 = _context25.sent;
            ok = _yield$apiGame16.ok;
            data = _yield$apiGame16.data;
            if (ok) {
              setFishClicks(function (prev) {
                return prev - amount;
              });
              setSingularity(function (prev) {
                return _objectSpread(_objectSpread({}, prev), {}, {
                  total_contributed: data.total_contributed,
                  filled: data.filled
                });
              });
              showToast("Contributed ".concat(fmt(amount), " fish to Singularity"));
            } else {
              showToast(data.error || 'Contribution failed');
            }
          case 6:
          case "end":
            return _context25.stop();
        }
      }, _callee25);
    }));
    return function (_x13) {
      return _ref52.apply(this, arguments);
    };
  }(), [showToast]);

  // Season 8: handle fish-to-wager conversion
  var handleFishToWager = useCallback(/*#__PURE__*/function () {
    var _ref53 = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee26(fishId) {
      var _yield$apiGame17, ok, data;
      return _regeneratorRuntime().wrap(function _callee26$(_context26) {
        while (1) switch (_context26.prev = _context26.next) {
          case 0:
            _context26.next = 2;
            return apiGame('/api/fish-to-wager', {
              method: 'POST',
              body: JSON.stringify({
                fish_id: fishId
              })
            });
          case 2:
            _yield$apiGame17 = _context26.sent;
            ok = _yield$apiGame17.ok;
            data = _yield$apiGame17.data;
            if (ok) {
              setWagerTokens(data.total_wager_tokens);
              showToast("+".concat(data.tokens_earned, " wager tokens"));
            } else {
              showToast(data.error || 'Conversion failed');
            }
          case 6:
          case "end":
            return _context26.stop();
        }
      }, _callee26);
    }));
    return function (_x14) {
      return _ref53.apply(this, arguments);
    };
  }(), [showToast]);

  // Season 8: handle double-down
  var handleDoubleDown = useCallback(/*#__PURE__*/_asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee27() {
    var _yield$apiGame18, ok, data;
    return _regeneratorRuntime().wrap(function _callee27$(_context27) {
      while (1) switch (_context27.prev = _context27.next) {
        case 0:
          _context27.next = 2;
          return apiGame('/api/wager/double-down', {
            method: 'POST',
            body: JSON.stringify({})
          });
        case 2:
          _yield$apiGame18 = _context27.sent;
          ok = _yield$apiGame18.ok;
          data = _yield$apiGame18.data;
          if (ok) {
            setDoubleDownPending(true);
            showToast('⚡ Double down armed!');
          } else {
            showToast(data.error || 'Double down failed');
          }
        case 6:
        case "end":
          return _context27.stop();
      }
    }, _callee27);
  })), [showToast]);

  // Season 8: handle insurance
  var handleInsurance = useCallback(/*#__PURE__*/_asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee28() {
    var _yield$apiGame19, ok, data;
    return _regeneratorRuntime().wrap(function _callee28$(_context28) {
      while (1) switch (_context28.prev = _context28.next) {
        case 0:
          _context28.next = 2;
          return apiGame('/api/wager/insurance', {
            method: 'POST',
            body: JSON.stringify({})
          });
        case 2:
          _yield$apiGame19 = _context28.sent;
          ok = _yield$apiGame19.ok;
          data = _yield$apiGame19.data;
          if (ok) {
            setWagerInsuranceCharges(function (prev) {
              return Math.max(0, prev - 1);
            });
            showToast('🛡️ Insurance activated');
          } else {
            showToast(data.error || 'Insurance failed');
          }
        case 6:
        case "end":
          return _context28.stop();
      }
    }, _callee28);
  })), [showToast]);

  // Season 8: handle loadout save
  var handleLoadoutSave = useCallback(/*#__PURE__*/function () {
    var _ref56 = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee29(slot, loadout) {
      var _yield$apiGame20, ok;
      return _regeneratorRuntime().wrap(function _callee29$(_context29) {
        while (1) switch (_context29.prev = _context29.next) {
          case 0:
            _context29.next = 2;
            return apiGame('/api/loadout', {
              method: 'POST',
              body: JSON.stringify({
                slot: slot,
                loadout: loadout
              })
            });
          case 2:
            _yield$apiGame20 = _context29.sent;
            ok = _yield$apiGame20.ok;
            if (ok) showToast("Loadout ".concat(slot, " saved"));else showToast('Save failed');
          case 5:
          case "end":
            return _context29.stop();
        }
      }, _callee29);
    }));
    return function (_x15, _x16) {
      return _ref56.apply(this, arguments);
    };
  }(), [showToast]);

  // Season 8: handle loadout apply
  var handleLoadoutApply = useCallback(/*#__PURE__*/function () {
    var _ref57 = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee30(slot) {
      var _yield$apiGame21, ok, data;
      return _regeneratorRuntime().wrap(function _callee30$(_context30) {
        while (1) switch (_context30.prev = _context30.next) {
          case 0:
            _context30.next = 2;
            return apiGame('/api/loadout/apply', {
              method: 'POST',
              body: JSON.stringify({
                slot: slot
              })
            });
          case 2:
            _yield$apiGame21 = _context30.sent;
            ok = _yield$apiGame21.ok;
            data = _yield$apiGame21.data;
            if (ok) {
              if (data.owned_items) setOwnedItems(data.owned_items);
              if (data.active_cosmetics) setActiveCosmetics(data.active_cosmetics);
              showToast("Loadout ".concat(slot, " applied"));
            } else {
              showToast(data.error || 'Apply failed');
            }
          case 6:
          case "end":
            return _context30.stop();
        }
      }, _callee30);
    }));
    return function (_x17) {
      return _ref57.apply(this, arguments);
    };
  }(), [showToast]);

  // Season 8: fetch legacy boards
  var handleShowLegacyBoards = useCallback(/*#__PURE__*/_asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee31() {
    var _yield$apiGame22, ok, data;
    return _regeneratorRuntime().wrap(function _callee31$(_context31) {
      while (1) switch (_context31.prev = _context31.next) {
        case 0:
          setShowLegacyBoards(true);
          _context31.next = 3;
          return apiGame('/api/legacy-boards');
        case 3:
          _yield$apiGame22 = _context31.sent;
          ok = _yield$apiGame22.ok;
          data = _yield$apiGame22.data;
          if (ok) setLegacyBoards(data.boards || []);
        case 7:
        case "end":
          return _context31.stop();
      }
    }, _callee31);
  })), []);

  // Season 8: keyboard shortcuts (T37)
  useEffect(function () {
    var handler = function handler(e) {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
      // Spacebar triggers manual spin (Season 8: spin is an active decision)
      if (e.key === ' ') {
        e.preventDefault();
        handleManualSpin();
      }
      // Number keys 1-0 select stake
      if (e.key >= '0' && e.key <= '9' && ownedItems.includes('wager_unlock')) {
        var newStake = e.key === '0' ? 10 : parseInt(e.key);
        handleStakeChange(newStake);
      }
    };
    window.addEventListener('keydown', handler);
    return function () {
      return window.removeEventListener('keydown', handler);
    };
  }, [ownedItems, handleStakeChange, handleManualSpin]);
  var hasGuard = ownedItems.includes('guard');
  var hasRegen = ownedItems.includes('regen_shield');

  // ── HIATUS MODE — comment out or set HIATUS_MODE=false to re-enable game ──
  if (HIATUS_MODE) {
    return /*#__PURE__*/React.createElement(HiatusScreen, {
      season: season,
      username: username,
      onLogout: handleLogout
    });
  }
  // ── END HIATUS MODE ────────────────────────────────────────────────────────

  return /*#__PURE__*/React.createElement("div", {
    className: lowSpec ? 'low-spec' : ''
  }, /*#__PURE__*/React.createElement(StatsPanel, {
    open: showStats,
    onClose: function onClose() {
      return setShowStats(false);
    }
  }), /*#__PURE__*/React.createElement(PatchNotesPanel, {
    open: showPatchNotes,
    onClose: handleClosePatchNotes
  }), toast && /*#__PURE__*/React.createElement("div", {
    className: "toast-notification"
  }, toast), happyHour && !happyHourDismissed && /*#__PURE__*/React.createElement("div", {
    className: "happy-hour-banner"
  }, "\u2B50 Happy Hour! 9\u201310pm \u2014 2\xD7 pot contributions \xB7 boosted legendary fish \u2B50", /*#__PURE__*/React.createElement("button", {
    className: "happy-hour-banner-close",
    onClick: function onClick() {
      return setHappyHourDismissed(true);
    }
  }, "\u2715")), catchUpSummary && /*#__PURE__*/React.createElement("div", {
    className: "catchup-banner"
  }, catchUpSummary), fishCatchUpSummary && /*#__PURE__*/React.createElement("div", {
    className: "catchup-banner catchup-banner--fish"
  }, fishCatchUpSummary), /*#__PURE__*/React.createElement("div", {
    className: "aria-live-region",
    "aria-live": "polite",
    "aria-atomic": "true"
  }, result === 'win' ? 'Win' : result === 'lose' ? 'Loss' : result === 'jackpot' ? 'Jackpot!' : ''), showOnboarding && onboardingStep < 5 && /*#__PURE__*/React.createElement("div", {
    className: "onboarding-overlay"
  }, /*#__PURE__*/React.createElement("div", {
    className: "onboarding-modal"
  }, /*#__PURE__*/React.createElement("h3", null, "Welcome to Season 8!"), /*#__PURE__*/React.createElement("p", null, "Step ", onboardingStep + 1, " of 5: ", onboardingStep === 0 ? 'Spin the wheel to get started!' : onboardingStep === 1 ? 'Try setting a wager stake!' : onboardingStep === 2 ? 'Catch a fish!' : onboardingStep === 3 ? 'Check your bounties!' : 'Explore the new features!'), /*#__PURE__*/React.createElement("button", {
    onClick: function onClick() {
      setShowOnboarding(false);
      setOnboardingStep(5);
    }
  }, "Skip"))), showPrestigeConfirm && /*#__PURE__*/React.createElement("div", {
    className: "onboarding-overlay"
  }, /*#__PURE__*/React.createElement("div", {
    className: "onboarding-modal"
  }, /*#__PURE__*/React.createElement("h3", null, "\u26A0\uFE0F Prestige Reset"), /*#__PURE__*/React.createElement("p", null, "This will reset your wins, losses, streak, and non-cosmetic upgrades. Your legacy wins will be preserved. Continue?"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: '10px',
      justifyContent: 'center'
    }
  }, /*#__PURE__*/React.createElement("button", {
    onClick: handlePrestige
  }, "Confirm Prestige"), /*#__PURE__*/React.createElement("button", {
    onClick: function onClick() {
      return setShowPrestigeConfirm(false);
    }
  }, "Cancel")))), showLegacyBoards && /*#__PURE__*/React.createElement("div", {
    className: "onboarding-overlay",
    onClick: function onClick() {
      return setShowLegacyBoards(false);
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "onboarding-modal",
    onClick: function onClick(e) {
      return e.stopPropagation();
    },
    style: {
      maxWidth: '500px'
    }
  }, /*#__PURE__*/React.createElement("h3", null, "\uD83C\uDFC6 Hall of Fame \u2014 Legacy Wins"), /*#__PURE__*/React.createElement("div", {
    style: {
      maxHeight: '400px',
      overflowY: 'auto'
    }
  }, legacyBoards.length === 0 ? /*#__PURE__*/React.createElement("p", null, "No legacy wins recorded yet.") : /*#__PURE__*/React.createElement("table", {
    style: {
      width: '100%',
      borderCollapse: 'collapse'
    }
  }, /*#__PURE__*/React.createElement("thead", null, /*#__PURE__*/React.createElement("tr", null, /*#__PURE__*/React.createElement("th", {
    style: {
      textAlign: 'left'
    }
  }, "#"), /*#__PURE__*/React.createElement("th", {
    style: {
      textAlign: 'left'
    }
  }, "Player"), /*#__PURE__*/React.createElement("th", {
    style: {
      textAlign: 'right'
    }
  }, "Legacy Wins"))), /*#__PURE__*/React.createElement("tbody", null, legacyBoards.map(function (b, i) {
    return /*#__PURE__*/React.createElement("tr", {
      key: i,
      style: {
        borderBottom: '1px solid #333'
      }
    }, /*#__PURE__*/React.createElement("td", null, i + 1), /*#__PURE__*/React.createElement("td", null, b.username), /*#__PURE__*/React.createElement("td", {
      style: {
        textAlign: 'right'
      }
    }, fmt(b.legacy_wins)));
  })))), /*#__PURE__*/React.createElement("button", {
    onClick: function onClick() {
      return setShowLegacyBoards(false);
    }
  }, "Close"))), /*#__PURE__*/React.createElement(Confetti, {
    active: confetti,
    count: confettiCount
  }), wormholeActive && /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'fixed',
      inset: 0,
      zIndex: 0,
      pointerEvents: 'none'
    }
  }, /*#__PURE__*/React.createElement(WormholeBackground, {
    "static": lowSpec,
    parallax: parallaxEnabled
  })), /*#__PURE__*/React.createElement("div", {
    className: "overlay ".concat(showResult ? 'active' : '')
  }), !isMobile && guardState && /*#__PURE__*/React.createElement(GuardWheel, {
    blocked: guardState.blocked,
    speedMult: 0.4,
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
  }, "\u26A1"), wormholeActive && !lowSpec && /*#__PURE__*/React.createElement("button", {
    className: "stats-btn",
    onClick: function onClick() {
      return setParallaxEnabled(function (v) {
        var next = !v;
        localStorage.setItem('parallaxEnabled', next);
        return next;
      });
    },
    title: parallaxEnabled ? 'Parallax ON — click to disable cursor tracking' : 'Parallax OFF — click to enable cursor tracking',
    style: {
      opacity: parallaxEnabled ? 1 : 0.5
    }
  }, "\uD83D\uDDB1\uFE0F"), !isMobile && /*#__PURE__*/React.createElement("button", {
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
  }, "\uD83D\uDCAC"), /*#__PURE__*/React.createElement("button", {
    className: "stats-btn",
    title: "Patch Notes",
    onClick: function onClick() {
      return setShowPatchNotes(true);
    }
  }, "\uD83D\uDCCB"), /*#__PURE__*/React.createElement("button", {
    className: "stats-btn",
    title: "Hall of Fame \u2014 Legacy Wins",
    onClick: handleShowLegacyBoards
  }, "\uD83C\uDFC6"), /*#__PURE__*/React.createElement("button", {
    className: "logout-btn",
    onClick: handleLogout
  }, "Logout"), season && /*#__PURE__*/React.createElement(SeasonInfo, {
    seasonName: season.season_name || season.season_number,
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
    },
    onFishCaught: refreshBountiesAndGoal
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
    },
    onFishCaught: refreshBountiesAndGoal
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
  }()), /*#__PURE__*/React.createElement("div", {
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
  }, /*#__PURE__*/React.createElement("span", {
    className: "title-lucky-wrap"
  }, /*#__PURE__*/React.createElement("span", {
    className: "title-lucky"
  }, "Lucky"), /*#__PURE__*/React.createElement("span", {
    className: "title-endless"
  }, "SEASON 8")), ' ', "Wheel"), /*#__PURE__*/React.createElement("div", {
    className: "subtitle"
  }, "Season 8 \u2014 Make every spin count")), /*#__PURE__*/React.createElement("div", {
    className: "wheel-wrapper ".concat(activeCosmetics.includes('golden_wheel') ? 'golden' : ''),
    onClick: !spinning ? handleManualSpin : undefined,
    title: spinning ? undefined : 'Click to spin!'
  }, /*#__PURE__*/React.createElement("div", {
    className: "pointer"
  }), /*#__PURE__*/React.createElement("canvas", {
    ref: canvasRef,
    width: 420,
    height: 420,
    className: "wheel-canvas",
    style: {
      transform: "rotate(".concat(wheelRotation, "deg)"),
      transition: "transform ".concat(WHEEL_SPIN_SPEED, "s cubic-bezier(0.17, 0.67, 0.12, 0.99)")
    }
  }), /*#__PURE__*/React.createElement("div", {
    className: "center-hub"
  }, "\u2605")), /*#__PURE__*/React.createElement("div", {
    className: "spin-prompt ".concat(spinning ? 'hidden' : ''),
    onClick: !spinning ? handleManualSpin : undefined
  }, "\u25B6 Click to Spin \u25C0"), catchupBonus && /*#__PURE__*/React.createElement("div", {
    className: "spin-prompt",
    style: {
      opacity: 0.7,
      fontSize: '0.7rem',
      pointerEvents: 'none'
    }
  }, "\uD83D\uDD3C Catch-up bonus active"), ownedItems.includes('wager_unlock') && /*#__PURE__*/React.createElement("div", {
    className: "season8-wager-panel"
  }, /*#__PURE__*/React.createElement("div", {
    className: "wager-stake-control"
  }, /*#__PURE__*/React.createElement("label", null, "Stake"), /*#__PURE__*/React.createElement("input", {
    type: "range",
    min: "1",
    max: "10",
    value: stake,
    onChange: function onChange(e) {
      return handleStakeChange(parseInt(e.target.value));
    },
    className: "wager-slider"
  }), /*#__PURE__*/React.createElement("span", {
    className: "stake-label stake-".concat(stake <= 3 ? 'safe' : stake <= 7 ? 'bold' : 'reckless')
  }, stake, "\xD7 ", stake <= 3 ? 'Safe' : stake <= 7 ? 'Bold' : 'Reckless')), wagerStreak > 0 && /*#__PURE__*/React.createElement("div", {
    className: "wager-hotstreak"
  }, "\uD83D\uDD25 Hot Streak: ", wagerStreak, " (+", Math.min(wagerStreak * 5, 50), "%)"), wagerBankedWins > 0 && /*#__PURE__*/React.createElement("button", {
    className: "wager-action-btn wager-bank-btn",
    onClick: /*#__PURE__*/_asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee32() {
      var _yield$apiGame23, ok, data;
      return _regeneratorRuntime().wrap(function _callee32$(_context32) {
        while (1) switch (_context32.prev = _context32.next) {
          case 0:
            _context32.next = 2;
            return apiGame('/api/wager/bank', {
              method: 'POST',
              body: '{}'
            });
          case 2:
            _yield$apiGame23 = _context32.sent;
            ok = _yield$apiGame23.ok;
            data = _yield$apiGame23.data;
            if (ok) {
              setWins(data.wins);
              setWagerBankedWins(0);
              setWagerStreak(0);
              showToast("Banked ".concat(fmt(data.banked), " wins!"));
              refreshBountiesAndGoal();
            } else showToast(data.error || 'Bank failed');
          case 6:
          case "end":
            return _context32.stop();
        }
      }, _callee32);
    }))
  }, "\uD83C\uDFE6 Bank ", fmt(wagerBankedWins)), ownedItems.includes('wager_double_down') && doubleDownPending && /*#__PURE__*/React.createElement("div", {
    className: "wager-double-down-armed"
  }, "\u26A1 Double-Down armed!"), ownedItems.includes('wager_double_down') && !doubleDownPending && /*#__PURE__*/React.createElement("button", {
    className: "wager-action-btn",
    onClick: handleDoubleDown
  }, "\u26A1 Arm Double Down"), ownedItems.includes('wager_insurance') && wagerInsuranceCharges > 0 && /*#__PURE__*/React.createElement("button", {
    className: "wager-action-btn",
    onClick: handleInsurance
  }, "\uD83D\uDEE1\uFE0F Insurance (", wagerInsuranceCharges, ")")), /*#__PURE__*/React.createElement("div", {
    className: "season8-wheel-mode"
  }, /*#__PURE__*/React.createElement("span", {
    className: "wheel-mode-label"
  }, "Mode"), /*#__PURE__*/React.createElement("div", {
    className: "wheel-mode-btns"
  }, availableWheelModes.map(function (mode) {
    var info = WHEEL_MODE_INFO[mode];
    return /*#__PURE__*/React.createElement("button", {
      key: mode,
      className: "wheel-mode-btn".concat(activeWheelMode === mode ? ' active' : ''),
      "data-tooltip": info ? info.desc : mode,
      onClick: function onClick() {
        return handleWheelModeChange(mode);
      }
    }, info ? info.label : mode);
  }))), /*#__PURE__*/React.createElement(Scoreboard, {
    wins: wins,
    losses: losses,
    lastResult: result
  }), isMobile && /*#__PURE__*/React.createElement("div", {
    className: "mobile-below-wheel"
  }, /*#__PURE__*/React.createElement(StreakPanel, {
    streak: streak,
    bonusmultLevel: 0
  }), /*#__PURE__*/React.createElement(DicePanel, {
    streak: streak,
    onRoll: handleDiceRoll,
    rolling: diceRolling,
    diceResult: diceResult,
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
  })), isMobile && guardState && /*#__PURE__*/React.createElement(GuardWheel, {
    blocked: guardState.blocked,
    speedMult: 0.4,
    onComplete: function onComplete() {
      return guardCompleteRef.current && guardCompleteRef.current();
    },
    contained: true
  }))), /*#__PURE__*/React.createElement("div", {
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
  }, hasGuard && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    className: "guard-charges"
  }, "\uD83D\uDEE1\uFE0F Guard ", guardCharges, "/3"), /*#__PURE__*/React.createElement("button", {
    className: "guard-activate-btn",
    disabled: guardCharges === 0,
    onClick: handleGuardActivate
  }, "Block")), hasRegen && /*#__PURE__*/React.createElement("div", null, regenRechargeWins > 0 ? "\uD83D\uDD04 ".concat(regenRechargeWins, " win").concat(regenRechargeWins !== 1 ? 's' : '') : '🔄 ready')), ownedItems.includes('lucky_seven') && /*#__PURE__*/React.createElement(LuckySevenCounter, {
    spinCount: spinCount
  }), /*#__PURE__*/React.createElement(StreakPanel, {
    streak: streak,
    bonusmultLevel: 0
  }), /*#__PURE__*/React.createElement(DicePanel, {
    streak: streak,
    onRoll: handleDiceRoll,
    rolling: diceRolling,
    diceResult: diceResult,
    guardSpinning: !!guardState,
    lowSpec: lowSpec,
    diceCharges: diceCharges,
    maxDiceCharges: diceMaxCharges,
    diceLastRecharge: diceLastRecharge,
    hasDiceExtra: ownedItems.includes('dice_extra'),
    rolledSinceSpin: diceRolledSinceSpin
  }), ownedItems.includes('prestige_unlock') && /*#__PURE__*/React.createElement("div", {
    className: "season8-prestige-panel"
  }, /*#__PURE__*/React.createElement("div", {
    className: "prestige-badge"
  }, "Prestige Lv.", prestigeLevel, " (+", prestigeLevel * 2, "%)"), legacyWins > 0 && /*#__PURE__*/React.createElement("div", {
    className: "legacy-badge"
  }, "Legacy: ", fmt(legacyWins), " wins"), prestigeLevel < 20 && /*#__PURE__*/React.createElement("button", {
    className: "prestige-btn",
    disabled: wins < (ownedItems.includes('prestige_efficiency') ? 500000 : 1000000),
    onClick: function onClick() {
      return setShowPrestigeConfirm(true);
    }
  }, "Prestige")), bounties && bounties.length > 0 && /*#__PURE__*/React.createElement("div", {
    className: "season8-bounties-panel"
  }, /*#__PURE__*/React.createElement("div", {
    className: "bounties-header"
  }, /*#__PURE__*/React.createElement("span", null, "\uD83D\uDCCB Bounties"), cosmeticFragments > 0 && /*#__PURE__*/React.createElement("span", {
    className: "fragment-count"
  }, "\uD83D\uDC8E ", cosmeticFragments)), bounties.map(function (b) {
    return /*#__PURE__*/React.createElement("div", {
      key: b.bounty_id,
      className: "bounty-card"
    }, /*#__PURE__*/React.createElement("div", {
      className: "bounty-desc"
    }, b.description || b.bounty_id), /*#__PURE__*/React.createElement("div", {
      className: "bounty-progress-bar"
    }, /*#__PURE__*/React.createElement("div", {
      className: "bounty-progress-fill",
      style: {
        width: "".concat(Math.min(100, b.progress / b.target * 100), "%")
      }
    })), /*#__PURE__*/React.createElement("div", {
      className: "bounty-progress-text"
    }, fmt(b.progress), " / ", fmt(b.target)), b.completed && !b.claimed && /*#__PURE__*/React.createElement("button", {
      className: "bounty-claim-btn",
      onClick: function onClick() {
        return handleBountyClaim(b.bounty_id);
      }
    }, "Claim"));
  })), communityGoal && /*#__PURE__*/React.createElement("div", {
    className: "season8-community-goal"
  }, /*#__PURE__*/React.createElement("div", {
    className: "goal-label"
  }, "\uD83C\uDF0D Community Goal"), /*#__PURE__*/React.createElement("div", {
    className: "goal-desc"
  }, communityGoal.description), /*#__PURE__*/React.createElement("div", {
    className: "goal-progress-bar"
  }, /*#__PURE__*/React.createElement("div", {
    className: "goal-progress-fill",
    style: {
      width: "".concat(Math.min(100, communityGoal.current / communityGoal.target * 100), "%")
    }
  })), /*#__PURE__*/React.createElement("div", {
    className: "goal-progress-text"
  }, fmt(communityGoal.current), " / ", fmt(communityGoal.target)), /*#__PURE__*/React.createElement("div", {
    className: "goal-contrib"
  }, "You: ", fmt(communityGoal.player_contribution))), singularity && /*#__PURE__*/React.createElement("div", {
    className: "season8-singularity-panel"
  }, /*#__PURE__*/React.createElement("div", {
    className: "singularity-label"
  }, "\uD83C\uDF00 Singularity"), /*#__PURE__*/React.createElement("div", {
    className: "singularity-progress-bar"
  }, /*#__PURE__*/React.createElement("div", {
    className: "singularity-progress-fill",
    style: {
      width: "".concat(Math.min(100, singularity.total_contributed / singularity.target * 100), "%")
    }
  })), /*#__PURE__*/React.createElement("div", {
    className: "singularity-progress-text"
  }, fmt(singularity.total_contributed), " / ", fmt(singularity.target)), singularity.fill_count > 0 && /*#__PURE__*/React.createElement("div", {
    className: "singularity-fills"
  }, "Convergences: ", singularity.fill_count), !singularity.filled && /*#__PURE__*/React.createElement("div", {
    className: "singularity-buttons"
  }, /*#__PURE__*/React.createElement("button", {
    onClick: function onClick() {
      return handleSingularityContribute(Math.min(fishClicks, Math.floor(singularity.target * 0.1)));
    },
    disabled: fishClicks < 1
  }, "+", fmt(Math.min(fishClicks, Math.floor(singularity.target * 0.1)))), /*#__PURE__*/React.createElement("button", {
    onClick: function onClick() {
      return handleSingularityContribute(fishClicks);
    },
    disabled: fishClicks < 1
  }, "All"))), ownedItems.includes('aquarium') && /*#__PURE__*/React.createElement("div", {
    className: "season8-aquarium-panel"
  }, /*#__PURE__*/React.createElement("div", {
    className: "aquarium-header"
  }, /*#__PURE__*/React.createElement("span", null, "\uD83D\uDC20 Aquarium"), /*#__PURE__*/React.createElement("span", {
    className: "aquarium-luck"
  }, "+", (aquariumSpecies.length * 0.1).toFixed(1), "%")), /*#__PURE__*/React.createElement("div", {
    className: "aquarium-grid"
  }, aquariumSpecies.map(function (s) {
    return /*#__PURE__*/React.createElement("div", {
      key: s,
      className: "aquarium-species",
      title: s
    }, s);
  })), ownedItems.includes('fish_to_wager') && wagerTokens > 0 && /*#__PURE__*/React.createElement("div", {
    className: "wager-tokens"
  }, "\uD83E\uDE99 ", fmt(wagerTokens), " tokens")), ownedItems.length > 0 && /*#__PURE__*/React.createElement("div", {
    className: "season8-loadout-panel"
  }, /*#__PURE__*/React.createElement("div", {
    className: "loadout-label"
  }, "\u2699\uFE0F Loadouts"), /*#__PURE__*/React.createElement("div", {
    className: "loadout-slots"
  }, [1, 2, 3].map(function (slot) {
    return /*#__PURE__*/React.createElement("div", {
      key: slot,
      className: "loadout-slot"
    }, /*#__PURE__*/React.createElement("button", {
      className: "loadout-save-btn",
      onClick: function onClick() {
        return handleLoadoutSave(slot, {
          owned_items: ownedItems,
          active_cosmetics: activeCosmetics
        });
      }
    }, "Save ", slot), /*#__PURE__*/React.createElement("button", {
      className: "loadout-apply-btn",
      onClick: function onClick() {
        return handleLoadoutApply(slot);
      }
    }, "Equip ", slot));
  })))), /*#__PURE__*/React.createElement(ShopPanel, {
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
    onEquipClass: handleEquipClass,
    onFishExchange: handleFishExchange,
    onWinsExchange: handleWinsExchange,
    equippedClass: equippedClass,
    fishExchangeTotal: fishExchangeTotal,
    collapsed: shopCollapsed,
    winCount: winCount,
    caughtSpecies: caughtSpecies,
    procStreak: procStreak
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
  var _useState231 = useState(undefined),
    _useState232 = _slicedToArray(_useState231, 2),
    user = _useState232[0],
    setUser = _useState232[1];
  var _useState233 = useState(null),
    _useState234 = _slicedToArray(_useState233, 2),
    gameState = _useState234[0],
    setGameState = _useState234[1];
  var _useState235 = useState(''),
    _useState236 = _slicedToArray(_useState235, 2),
    sessionMsg = _useState236[0],
    setSessionMsg = _useState236[1];
  useEffect(function () {
    _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee33() {
      var _yield$apiFetch2, ok, data, gs;
      return _regeneratorRuntime().wrap(function _callee33$(_context33) {
        while (1) switch (_context33.prev = _context33.next) {
          case 0:
            _context33.next = 2;
            return apiFetch('/api/me');
          case 2:
            _yield$apiFetch2 = _context33.sent;
            ok = _yield$apiFetch2.ok;
            data = _yield$apiFetch2.data;
            storeCsrf(data);
            if (!(ok && data.username)) {
              _context33.next = 13;
              break;
            }
            _context33.next = 9;
            return apiFetch('/api/state');
          case 9:
            gs = _context33.sent;
            if (gs.ok) {
              setGameState(gs.data);
              setUser(data.username);
            } else {
              setUser(null);
            }
            _context33.next = 14;
            break;
          case 13:
            setUser(null);
          case 14:
          case "end":
            return _context33.stop();
        }
      }, _callee33);
    }))();
  }, []);
  var handleAuth = /*#__PURE__*/function () {
    var _ref61 = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee34(username) {
      var gs;
      return _regeneratorRuntime().wrap(function _callee34$(_context34) {
        while (1) switch (_context34.prev = _context34.next) {
          case 0:
            _context34.next = 2;
            return apiFetch('/api/state');
          case 2:
            gs = _context34.sent;
            if (gs.ok) {
              setGameState(gs.data);
              setUser(username);
              setSessionMsg('');
            }
          case 4:
          case "end":
            return _context34.stop();
        }
      }, _callee34);
    }));
    return function handleAuth(_x18) {
      return _ref61.apply(this, arguments);
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
