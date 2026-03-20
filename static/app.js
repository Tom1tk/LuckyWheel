"use strict";

function _typeof(o) { "@babel/helpers - typeof"; return _typeof = "function" == typeof Symbol && "symbol" == typeof Symbol.iterator ? function (o) { return typeof o; } : function (o) { return o && "function" == typeof Symbol && o.constructor === Symbol && o !== Symbol.prototype ? "symbol" : typeof o; }, _typeof(o); }
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
  _apiFetch = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee10(path) {
    var opts,
      res,
      json,
      _args10 = arguments;
    return _regeneratorRuntime().wrap(function _callee10$(_context10) {
      while (1) switch (_context10.prev = _context10.next) {
        case 0:
          opts = _args10.length > 1 && _args10[1] !== undefined ? _args10[1] : {};
          _context10.next = 3;
          return fetch(path, _objectSpread({
            headers: {
              'Content-Type': 'application/json'
            }
          }, opts));
        case 3:
          res = _context10.sent;
          _context10.next = 6;
          return res.json()["catch"](function () {
            return {};
          });
        case 6:
          json = _context10.sent;
          return _context10.abrupt("return", {
            ok: res.ok,
            status: res.status,
            data: json
          });
        case 8:
        case "end":
          return _context10.stop();
      }
    }, _callee10);
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
      color: '#006622',
      bright: '#00CC44',
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

  // WIN segment (green, small)
  var gWin = ctx.createRadialGradient(cx, cy, r * 0.1, cx, cy, r);
  gWin.addColorStop(0, '#88FF88');
  gWin.addColorStop(1, '#006600');
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
  if (n >= 1e15) return n.toExponential(2).replace('e+', 'e');
  if (n >= 1e12) return (n / 1e12).toFixed(n >= 10e12 ? 1 : 2).replace(/\.?0+$/, '') + 'T';
  if (n >= 1e9) return (n / 1e9).toFixed(n >= 10e9 ? 1 : 2).replace(/\.?0+$/, '') + 'B';
  if (n >= 1e6) return (n / 1e6).toFixed(n >= 10e6 ? 1 : 2).replace(/\.?0+$/, '') + 'M';
  if (n >= 1e3) return (n / 1e3).toFixed(n >= 10e3 ? 1 : 2).replace(/\.?0+$/, '') + 'K';
  return String(n);
}

// ── Scoreboard ────────────────────────────────────────────────────────────
var Scoreboard = React.memo(function Scoreboard(_ref) {
  var wins = _ref.wins,
    losses = _ref.losses,
    lastResult = _ref.lastResult;
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
var CONFETTI_COLORS = ['#FFD700', '#FF6600', '#FF3333', '#00FF88', '#00AAFF', '#FF00FF', '#FFFFFF'];
function Confetti(_ref2) {
  var active = _ref2.active,
    _ref2$count = _ref2.count,
    count = _ref2$count === void 0 ? 80 : _ref2$count;
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
function GuardWheel(_ref3) {
  var blocked = _ref3.blocked,
    onComplete = _ref3.onComplete;
  var canvasRef = useRef(null);
  var _useState = useState(0),
    _useState2 = _slicedToArray(_useState, 2),
    guardRotation = _useState2[0],
    setGuardRotation = _useState2[1];
  var _useState3 = useState(false),
    _useState4 = _slicedToArray(_useState3, 2),
    revealed = _useState4[0],
    setRevealed = _useState4[1];
  useEffect(function () {
    var canvas = canvasRef.current;
    if (canvas) drawGuardWheel(canvas);

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
    }, 2000);
    var completeTimer = setTimeout(function () {
      return onComplete();
    }, 3400);
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
      transition: "transform 1.8s cubic-bezier(0.17, 0.67, 0.12, 0.99)"
    }
  })), revealed && /*#__PURE__*/React.createElement("div", {
    className: "guard-result ".concat(blocked ? 'blocked' : 'failed')
  }, blocked ? '🛡️ BLOCKED!' : '💔 Guard Failed')));
}

// ── Fish ──────────────────────────────────────────────────────────────────
var Fish = React.memo(function Fish(_ref4) {
  var mood = _ref4.mood,
    net = _ref4.net,
    fishClicks = _ref4.fishClicks,
    onFishClick = _ref4.onFishClick,
    fishData = _ref4.fishData,
    sizeRem = _ref4.sizeRem,
    trailClass = _ref4.trailClass;
  var _useState5 = useState(0),
    _useState6 = _slicedToArray(_useState5, 2),
    spinKey = _useState6[0],
    setSpinKey = _useState6[1];
  var _useState7 = useState(false),
    _useState8 = _slicedToArray(_useState7, 2),
    fishSpinning = _useState8[0],
    setFishSpinning = _useState8[1];
  var timerRef = useRef(null);
  var _ref5 = fishData || DEFAULT_FISH,
    emoji = _ref5.emoji,
    labels = _ref5.labels;
  var handleClick = function handleClick() {
    if (timerRef.current) clearTimeout(timerRef.current);
    setFishSpinning(true);
    setSpinKey(function (k) {
      return k + 1;
    });
    timerRef.current = setTimeout(function () {
      return setFishSpinning(false);
    }, 650);
    onFishClick();
  };
  var diff = Math.abs(net);
  var glowSize = Math.min(8 + diff * 3, 80);
  var glowSize2 = Math.min(16 + diff * 6, 160);
  var glowOpacity = Math.min(0.5 + diff * 0.015, 1.0);
  var fishFilter = net > 0 ? "drop-shadow(0 0 ".concat(glowSize, "px rgba(255,140,0,").concat(glowOpacity, ")) drop-shadow(0 0 ").concat(glowSize2, "px rgba(255,80,0,").concat(glowOpacity * 0.6, "))") : net < 0 ? "drop-shadow(0 0 ".concat(glowSize, "px rgba(160,0,255,").concat(glowOpacity, ")) drop-shadow(0 0 ").concat(glowSize2, "px rgba(80,0,180,").concat(glowOpacity * 0.6, "))") : 'drop-shadow(0 0 8px rgba(255,215,0,0.3))';
  var auraBlur = Math.min(80 + diff * 12, 600);
  var auraOpacity = Math.min(0.3 + diff * 0.008, 0.88);
  var auraColor = net > 0 ? 'rgba(255,130,0,0.9)' : 'rgba(150,0,255,0.9)';
  var auraStyle = diff > 0 ? {
    background: auraColor,
    filter: "blur(".concat(auraBlur, "px)"),
    opacity: auraOpacity
  } : null;
  var animClass = fishSpinning ? 'spinning-fish' : mood;
  return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    className: "fish-panel ".concat(trailClass || ''),
    onClick: handleClick,
    style: {
      filter: fishFilter
    },
    title: "Wheeee!"
  }, auraStyle && /*#__PURE__*/React.createElement("div", {
    className: "fish-aura",
    style: auraStyle
  }), /*#__PURE__*/React.createElement("span", {
    className: "fish-body ".concat(animClass),
    key: spinKey || mood,
    style: {
      fontSize: "".concat(sizeRem, "rem")
    }
  }, emoji), /*#__PURE__*/React.createElement("span", {
    className: "fish-label ".concat(mood)
  }, labels[mood])), /*#__PURE__*/React.createElement("div", {
    className: "fish-counter"
  }, /*#__PURE__*/React.createElement("span", {
    className: "fish-counter-label"
  }, "Balance"), /*#__PURE__*/React.createElement("span", {
    className: "fish-counter-value"
  }, emoji, " \xD7 ", fmt(fishClicks))));
});

// ── Streak Panel ──────────────────────────────────────────────────────────
var StreakPanel = React.memo(function StreakPanel(_ref6) {
  var streak = _ref6.streak;
  if (Math.abs(streak) < 2) return null;
  var isWin = streak > 0;
  var count = Math.abs(streak);
  var bonus = count >= 3 ? Math.pow(2, count - 3) : 0;
  return /*#__PURE__*/React.createElement("div", {
    className: "streak-panel ".concat(isWin ? 'win-streak' : 'lose-streak'),
    key: streak
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

// ── Season Winners ────────────────────────────────────────────────────────
function SeasonWinners(_ref7) {
  var winners = _ref7.winners,
    seasonNumber = _ref7.seasonNumber;
  if (!winners || winners.length === 0) return null;
  var medals = ['🥇', '🥈', '🥉'];
  var rankClasses = ['sw-gold', 'sw-silver', 'sw-bronze', 'sw-4th', 'sw-5th'];
  return /*#__PURE__*/React.createElement("div", {
    className: "season-winners"
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
function SeasonInfo(_ref8) {
  var seasonNumber = _ref8.seasonNumber,
    endsAt = _ref8.endsAt;
  var _useState9 = useState(''),
    _useState0 = _slicedToArray(_useState9, 2),
    timeLeft = _useState0[0],
    setTimeLeft = _useState0[1];
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
function Leaderboard(_ref9) {
  var currentUser = _ref9.currentUser;
  var _useState1 = useState([]),
    _useState10 = _slicedToArray(_useState1, 2),
    rows = _useState10[0],
    setRows = _useState10[1];
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
    var id = setInterval(load, 60000);
    return function () {
      clearInterval(id);
      ctrl.abort();
    };
  }, []);
  if (rows.length === 0) return null;
  var rankClass = function rankClass(i) {
    return i === 0 ? 'gold' : i === 1 ? 'silver' : i === 2 ? 'bronze' : '';
  };
  var renderRow = function renderRow(r, i, key) {
    return /*#__PURE__*/React.createElement("div", {
      key: key,
      className: "leaderboard-row"
    }, /*#__PURE__*/React.createElement("span", {
      className: "lb-rank ".concat(rankClass(i))
    }, i + 1, "."), /*#__PURE__*/React.createElement("span", {
      className: "lb-name ".concat(r.username === currentUser ? 'is-you' : '')
    }, r.username), /*#__PURE__*/React.createElement("span", {
      className: "lb-wins"
    }, fmt(r.wins), "W"), /*#__PURE__*/React.createElement("span", {
      className: "lb-ratio"
    }, fmt(r.wins), "W:", fmt(r.losses), "L"));
  };
  return /*#__PURE__*/React.createElement("div", {
    className: "leaderboard"
  }, /*#__PURE__*/React.createElement("div", {
    className: "leaderboard-title"
  }, "\uD83C\uDFC6 Top Players"), /*#__PURE__*/React.createElement("div", {
    className: "leaderboard-scroll"
  }, /*#__PURE__*/React.createElement("div", {
    className: "leaderboard-track"
  }, rows.map(function (r, i) {
    return renderRow(r, i, r.username);
  }), rows.map(function (r, i) {
    return renderRow(r, i, "".concat(r.username, "-2"));
  }))));
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
}];
var SHOP_SECTIONS = [{
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
  }, {
    id: 'hyperspin',
    emoji: '💨',
    name: 'Hyper Spin',
    cost: 600,
    desc: 'Spin time: 1.5s → 1s',
    requires: 'turbo_spin'
  }, {
    id: 'ultraspin',
    emoji: '🌀',
    name: 'Ultra Spin',
    cost: 2000,
    desc: 'Spin time: 1s → 0.75s',
    requires: 'hyperspin'
  }, {
    id: 'maxspin',
    emoji: '⚡',
    name: 'Max Spin',
    cost: 6000,
    desc: 'Spin time: 0.75s → 0.5s',
    requires: 'ultraspin'
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
  }, {
    id: 'winmult_5',
    emoji: '💎',
    name: 'Win x32',
    cost: 51200,
    desc: 'Each win scores x32',
    requires: 'winmult_4'
  }, {
    id: 'winmult_6',
    emoji: '👑',
    name: 'Win x64',
    cost: 204800,
    desc: 'Each win scores x64',
    requires: 'winmult_5'
  }, {
    id: 'winmult_7',
    emoji: '👑',
    name: 'Win x128',
    cost: 819200,
    desc: 'Each win scores x128',
    requires: 'winmult_6'
  }]
}, {
  label: '⭐ Bonus Power',
  items: [{
    id: 'bonusmult_1',
    emoji: '⭐',
    name: 'Bonus Boost',
    cost: 300,
    desc: 'Streak bonuses x2 — ⚠️ also amplifies loss streaks'
  }, {
    id: 'bonusmult_2',
    emoji: '⭐',
    name: 'Bonus Mega',
    cost: 1200,
    desc: 'Streak bonuses x5 — ⚠️ also amplifies loss streaks',
    requires: 'bonusmult_1'
  }, {
    id: 'bonusmult_3',
    emoji: '💫',
    name: 'Bonus ULTRA',
    cost: 4800,
    desc: 'Streak bonuses x10 — ⚠️ also amplifies loss streaks',
    requires: 'bonusmult_2'
  }, {
    id: 'bonusmult_4',
    emoji: '💫',
    name: 'Bonus x20',
    cost: 20000,
    desc: 'Streak bonuses x20 — ⚠️ also amplifies loss streaks',
    requires: 'bonusmult_3'
  }, {
    id: 'bonusmult_5',
    emoji: '🌟',
    name: 'Bonus x50',
    cost: 80000,
    desc: 'Streak bonuses x50 — ⚠️ also amplifies loss streaks',
    requires: 'bonusmult_4'
  }, {
    id: 'bonusmult_6',
    emoji: '🌟',
    name: 'Bonus x100',
    cost: 300000,
    desc: 'Streak bonuses x100 — ⚠️ also amplifies loss streaks',
    requires: 'bonusmult_5'
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
  label: '🛡️ Protection',
  items: [{
    id: 'guard',
    emoji: '🛡️',
    name: 'Guard',
    cost: 300,
    desc: '50% chance to block any loss. Breaks on success, survives on failure.'
  }, {
    id: 'regen_shield',
    emoji: '🔄',
    name: 'Regenerating Shield',
    cost: 800,
    desc: 'Blocks any loss when charged. Recharges after 5 wins. Never breaks.'
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
    desc: 'Classic gold & orange casino theme. Season 2 (green/red) is default.'
  }]
}, {
  label: '🎲 Special Upgrades',
  items: [{
    id: 'fortune_charm',
    emoji: '🍀',
    name: 'Fortune Charm',
    cost: 500,
    desc: '+25% to all streak bonus payouts'
  }, {
    id: 'lucky_seven',
    emoji: '7️⃣',
    name: 'Lucky Seven',
    cost: 1000,
    desc: 'Every 7th spin is guaranteed a win'
  }, {
    id: 'win_echo',
    emoji: '🔊',
    name: 'Win Echo',
    cost: 750,
    desc: '20% chance to double wins earned on any win'
  }, {
    id: 'resilience',
    emoji: '💪',
    name: 'Resilience',
    cost: 500000,
    desc: '50% chance: on win streak, a loss only drops streak by 1 instead of resetting'
  }, {
    id: 'jackpot',
    emoji: '🎰',
    name: 'Jackpot',
    cost: 3000,
    desc: '2% chance each win to multiply gains by 50x'
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
var COSMETIC_SECTION_IDS = new Set(['bg_ocean', 'bg_royal', 'bg_inferno', 'bg_forest', 'bg_abyss', 'bg_cosmic', 'fishsize_1', 'fishsize_2', 'fishsize_3', 'confetti_1', 'confetti_2', 'confetti_3', 'party_mode', 'trail_1', 'trail_2', 'trail_3', 'trail_4', 'trail_5', 'trail_6', 'theme_fire', 'theme_ice', 'theme_neon', 'theme_void', 'theme_gold', 'golden_wheel', 'page_season1']);

// ── Shop components ────────────────────────────────────────────────────────
var ShopItem = React.memo(function ShopItem(_ref0) {
  var item = _ref0.item,
    owned = _ref0.owned,
    equipped = _ref0.equipped,
    active = _ref0.active,
    canAfford = _ref0.canAfford,
    onBuy = _ref0.onBuy,
    onEquip = _ref0.onEquip,
    onEquipCosmetic = _ref0.onEquipCosmetic,
    isSkin = _ref0.isSkin,
    isSingularity = _ref0.isSingularity,
    isCosmetic = _ref0.isCosmetic;
  var actionEl;
  if (owned && isSkin) {
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
        return canAfford && onBuy(item.id, item.cost);
      }
    }, "Buy");
  }
  var extraClass = isSingularity && !owned ? 'singularity-item' : '';
  return /*#__PURE__*/React.createElement("div", {
    className: "shop-item ".concat(owned ? equipped || active ? 'equipped' : 'owned' : '', " ").concat(extraClass)
  }, /*#__PURE__*/React.createElement("span", {
    className: "shop-item-emoji"
  }, item.emoji), /*#__PURE__*/React.createElement("div", {
    className: "shop-item-info"
  }, /*#__PURE__*/React.createElement("div", {
    className: "shop-item-name"
  }, item.name), item.desc && /*#__PURE__*/React.createElement("div", {
    className: "shop-item-desc",
    "data-tooltip": item.desc
  }, item.desc), !owned && /*#__PURE__*/React.createElement("div", {
    className: "shop-item-cost"
  }, "\uD83D\uDC1F ", item.cost.toLocaleString())), /*#__PURE__*/React.createElement("div", {
    className: "shop-item-action"
  }, actionEl));
});
var COSMETIC_SECTION_LABELS = new Set(['🐟 Fish Size', '✨ Fish Trail', '🎡 Wheel Theme', '🎊 Confetti', '🎨 Atmosphere', '🖼️ Page Theme']);
function ShopPanel(_ref1) {
  var fishClicks = _ref1.fishClicks,
    ownedItems = _ref1.ownedItems,
    equippedFish = _ref1.equippedFish,
    activeCosmetics = _ref1.activeCosmetics,
    onBuy = _ref1.onBuy,
    onEquip = _ref1.onEquip,
    onEquipCosmetic = _ref1.onEquipCosmetic;
  var _useState11 = useState('cosmetic'),
    _useState12 = _slicedToArray(_useState11, 2),
    activeTab = _useState12[0],
    setActiveTab = _useState12[1];
  var _useMemo = useMemo(function () {
      var cosmetic = [],
        functional = [];
      SHOP_SECTIONS.forEach(function (section) {
        var visibleItems = section.items.filter(function (item) {
          return !item.requires || ownedItems.includes(item.requires);
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
  };
  return /*#__PURE__*/React.createElement("div", {
    className: "shop-panel"
  }, /*#__PURE__*/React.createElement("div", {
    className: "shop-header"
  }, /*#__PURE__*/React.createElement("div", {
    className: "shop-title"
  }, "\uD83D\uDED2 Shop"), /*#__PURE__*/React.createElement("div", {
    className: "shop-balance"
  }, "Balance: ", /*#__PURE__*/React.createElement("span", null, "\uD83D\uDC1F ", fmt(fishClicks)))), /*#__PURE__*/React.createElement("div", {
    className: "shop-tabs"
  }, /*#__PURE__*/React.createElement("button", {
    className: "shop-tab ".concat(activeTab === 'cosmetic' ? 'active' : ''),
    onClick: function onClick() {
      return setActiveTab('cosmetic');
    }
  }, "\uD83C\uDFA8 Cosmetic"), /*#__PURE__*/React.createElement("button", {
    className: "shop-tab ".concat(activeTab === 'functional' ? 'active' : ''),
    onClick: function onClick() {
      return setActiveTab('functional');
    }
  }, "\u26A1 Functional")), /*#__PURE__*/React.createElement("div", {
    className: "shop-tab-content"
  }, activeTab === 'cosmetic' ? /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    className: "shop-section-label"
  }, "\u2500\u2500 Fish Skins \u2500\u2500"), FISH_SKINS.map(function (item) {
    return /*#__PURE__*/React.createElement(ShopItem, {
      key: item.id,
      item: item,
      isSkin: true,
      owned: ownedItems.includes(item.id),
      equipped: equippedFish === item.id,
      canAfford: fishClicks >= item.cost,
      onBuy: onBuy,
      onEquip: onEquip,
      onEquipCosmetic: onEquipCosmetic
    });
  }), cosmeticSections.map(renderSection)) : functionalSections.map(renderSection)));
}

// ── Stats Panel ────────────────────────────────────────────────────────────
function StatsPanel(_ref10) {
  var open = _ref10.open,
    onClose = _ref10.onClose;
  var _useState13 = useState(null),
    _useState14 = _slicedToArray(_useState13, 2),
    stats = _useState14[0],
    setStats = _useState14[1];
  useEffect(function () {
    if (!open) return;
    apiFetch('/api/stats').then(function (r) {
      if (r.ok) setStats(r.data);
    });
  }, [open]);
  if (!open) return null;
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
  }, /*#__PURE__*/React.createElement("span", null, "Lifetime Taps"), /*#__PURE__*/React.createElement("span", null, fmt(stats.total_fish_clicks)))) : /*#__PURE__*/React.createElement("div", {
    className: "stats-loading"
  }, "Loading\u2026"), /*#__PURE__*/React.createElement("button", {
    className: "stats-close-btn",
    onClick: onClose
  }, "\u2715")));
}

// ── Auth Page ──────────────────────────────────────────────────────────────
function AuthPage(_ref11) {
  var onAuth = _ref11.onAuth;
  var _useState15 = useState('login'),
    _useState16 = _slicedToArray(_useState15, 2),
    mode = _useState16[0],
    setMode = _useState16[1];
  var _useState17 = useState(''),
    _useState18 = _slicedToArray(_useState17, 2),
    username = _useState18[0],
    setUsername = _useState18[1];
  var _useState19 = useState(''),
    _useState20 = _slicedToArray(_useState19, 2),
    password = _useState20[0],
    setPassword = _useState20[1];
  var _useState21 = useState(''),
    _useState22 = _slicedToArray(_useState21, 2),
    error = _useState22[0],
    setError = _useState22[1];
  var _useState23 = useState(false),
    _useState24 = _slicedToArray(_useState23, 2),
    loading = _useState24[0],
    setLoading = _useState24[1];
  var submit = /*#__PURE__*/function () {
    var _ref12 = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee(e) {
      var _yield$apiFetch, ok, data;
      return _regeneratorRuntime().wrap(function _callee$(_context) {
        while (1) switch (_context.prev = _context.next) {
          case 0:
            e.preventDefault();
            setError('');
            setLoading(true);
            _context.next = 5;
            return apiFetch("/api/".concat(mode), {
              method: 'POST',
              body: JSON.stringify({
                username: username,
                password: password
              })
            });
          case 5:
            _yield$apiFetch = _context.sent;
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
            return _context.stop();
        }
      }, _callee);
    }));
    return function submit(_x2) {
      return _ref12.apply(this, arguments);
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

// ── Game App ───────────────────────────────────────────────────────────────
function GameApp(_ref13) {
  var username = _ref13.username,
    gameState = _ref13.gameState,
    onLogout = _ref13.onLogout,
    onSessionExpired = _ref13.onSessionExpired;
  var canvasRef = useRef(null);
  var _useState25 = useState(0),
    _useState26 = _slicedToArray(_useState25, 2),
    rotation = _useState26[0],
    setRotation = _useState26[1];
  var _useState27 = useState(false),
    _useState28 = _slicedToArray(_useState27, 2),
    spinning = _useState28[0],
    setSpinning = _useState28[1];
  var _useState29 = useState(null),
    _useState30 = _slicedToArray(_useState29, 2),
    result = _useState30[0],
    setResult = _useState30[1];
  var _useState31 = useState(false),
    _useState32 = _slicedToArray(_useState31, 2),
    showResult = _useState32[0],
    setShowResult = _useState32[1];
  var setShowResultSync = function setShowResultSync(v) {
    showResultRef.current = v;
    setShowResult(v);
  };
  var _useState33 = useState(null),
    _useState34 = _slicedToArray(_useState33, 2),
    shieldFeedback = _useState34[0],
    setShieldFeedback = _useState34[1];
  var _useState35 = useState(null),
    _useState36 = _slicedToArray(_useState35, 2),
    guardState = _useState36[0],
    setGuardState = _useState36[1]; // { blocked, broke } | null
  var guardCompleteRef = useRef(null);
  var _useState37 = useState(false),
    _useState38 = _slicedToArray(_useState37, 2),
    hideResult = _useState38[0],
    setHideResult = _useState38[1];
  var _useState39 = useState(false),
    _useState40 = _slicedToArray(_useState39, 2),
    confetti = _useState40[0],
    setConfetti = _useState40[1];
  var _useState41 = useState(gameState.wins),
    _useState42 = _slicedToArray(_useState41, 2),
    wins = _useState42[0],
    setWins = _useState42[1];
  var _useState43 = useState(gameState.losses),
    _useState44 = _slicedToArray(_useState43, 2),
    losses = _useState44[0],
    setLosses = _useState44[1];
  var _useState45 = useState(gameState.streak),
    _useState46 = _slicedToArray(_useState45, 2),
    streak = _useState46[0],
    setStreak = _useState46[1];
  var _useState47 = useState('idle'),
    _useState48 = _slicedToArray(_useState47, 2),
    fishMood = _useState48[0],
    setFishMood = _useState48[1];
  var _useState49 = useState(gameState.fish_clicks),
    _useState50 = _slicedToArray(_useState49, 2),
    fishClicks = _useState50[0],
    setFishClicks = _useState50[1];
  var _useState51 = useState(0),
    _useState52 = _slicedToArray(_useState51, 2),
    bonusEarned = _useState52[0],
    setBonusEarned = _useState52[1];
  var _useState53 = useState(false),
    _useState54 = _slicedToArray(_useState53, 2),
    echoTriggered = _useState54[0],
    setEchoTriggered = _useState54[1];
  var _useState55 = useState(false),
    _useState56 = _slicedToArray(_useState55, 2),
    jackpotHit = _useState56[0],
    setJackpotHit = _useState56[1];
  var _useState57 = useState(false),
    _useState58 = _slicedToArray(_useState57, 2),
    resilienceTriggered = _useState58[0],
    setResilienceTriggered = _useState58[1];
  var _useState59 = useState(gameState.shield_charges),
    _useState60 = _slicedToArray(_useState59, 2),
    shieldCharges = _useState60[0],
    setShieldCharges = _useState60[1];
  var _useState61 = useState(gameState.regen_recharge_wins || 0),
    _useState62 = _slicedToArray(_useState61, 2),
    regenRechargeWins = _useState62[0],
    setRegenRechargeWins = _useState62[1];
  var _useState63 = useState(false),
    _useState64 = _slicedToArray(_useState63, 2),
    autoSpin = _useState64[0],
    setAutoSpin = _useState64[1];
  var _useState65 = useState(gameState.owned_items),
    _useState66 = _slicedToArray(_useState65, 2),
    ownedItems = _useState66[0],
    setOwnedItems = _useState66[1];
  var _useState67 = useState(gameState.equipped_fish),
    _useState68 = _slicedToArray(_useState67, 2),
    equippedFish = _useState68[0],
    setEquippedFish = _useState68[1];
  var _useState69 = useState(gameState.active_cosmetics || []),
    _useState70 = _slicedToArray(_useState69, 2),
    activeCosmetics = _useState70[0],
    setActiveCosmetics = _useState70[1];
  var _useState71 = useState(false),
    _useState72 = _slicedToArray(_useState71, 2),
    showStats = _useState72[0],
    setShowStats = _useState72[1];
  var _useState73 = useState(null),
    _useState74 = _slicedToArray(_useState73, 2),
    toast = _useState74[0],
    setToast = _useState74[1];
  var _useState75 = useState(gameState.season || null),
    _useState76 = _slicedToArray(_useState75, 2),
    season = _useState76[0],
    setSeason = _useState76[1];
  var spinSpeed = useMemo(function () {
    if (ownedItems.includes('maxspin')) return 0.5;
    if (ownedItems.includes('ultraspin')) return 0.75;
    if (ownedItems.includes('hyperspin')) return 1.0;
    if (ownedItems.includes('turbo_spin')) return 1.5;
    if (ownedItems.includes('speed_boost')) return 3.0;
    return 4.5;
  }, [ownedItems]);
  var autoSpinDelay = useMemo(function () {
    return ownedItems.includes('autospeed_3') ? 0 : ownedItems.includes('autospeed_2') ? 500 : ownedItems.includes('autospeed_1') ? 1000 : 1500;
  }, [ownedItems]);
  var clickAmount = useMemo(function () {
    if (ownedItems.includes('double_click_5')) return 6;
    if (ownedItems.includes('double_click_4')) return 5;
    if (ownedItems.includes('double_click_3')) return 4;
    if (ownedItems.includes('double_click_2')) return 3;
    if (ownedItems.includes('double_click')) return 2;
    return 1;
  }, [ownedItems]);
  var clickFrenzyRate = useMemo(function () {
    if (ownedItems.includes('clickfrenzy_5')) return 100;
    if (ownedItems.includes('clickfrenzy_4')) return 50;
    if (ownedItems.includes('clickfrenzy_3')) return 20;
    if (ownedItems.includes('clickfrenzy_2')) return 5;
    if (ownedItems.includes('clickfrenzy_1')) return 1;
    return 0;
  }, [ownedItems]);
  var fishSizeRem = useMemo(function () {
    return activeCosmetics.includes('fishsize_3') ? 40 : activeCosmetics.includes('fishsize_2') ? 28 : activeCosmetics.includes('fishsize_1') ? 20 : 15;
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
    return 'default';
  }, [activeCosmetics]);
  var bgClass = useMemo(function () {
    if (activeCosmetics.includes('bg_cosmic')) return 'bg-cosmic';
    if (activeCosmetics.includes('bg_abyss')) return 'bg-abyss';
    if (activeCosmetics.includes('bg_forest')) return 'bg-forest';
    if (activeCosmetics.includes('bg_inferno')) return 'bg-inferno';
    if (activeCosmetics.includes('bg_royal')) return 'bg-royal';
    if (activeCosmetics.includes('bg_ocean')) return 'bg-ocean';
    return '';
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
    return activeCosmetics.includes('page_season1') ? 'page-season1' : '';
  }, [activeCosmetics]);
  var currentRotationRef = useRef(0);
  var fishTimerRef = useRef(null);
  var toastTimerRef = useRef(null);
  var autoSpinRef = useRef(false);
  var spinSpeedRef = useRef(4.5);
  var autoSpinDelayRef = useRef(1500);
  var spinningRef = useRef(false);
  var showResultRef = useRef(false);
  var clickBufferRef = useRef(0);
  var activeCosmeticsRef = useRef(activeCosmetics);
  useEffect(function () {
    activeCosmeticsRef.current = activeCosmetics;
  }, [activeCosmetics]);
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
  useEffect(function () {
    setSessionExpiredHandler(onSessionExpired);
    return function () {
      return setSessionExpiredHandler(null);
    };
  }, [onSessionExpired]);
  useEffect(function () {
    if (clickFrenzyRate === 0) return;
    var id = setInterval(/*#__PURE__*/_asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee2() {
      var _yield$apiGame, ok, data;
      return _regeneratorRuntime().wrap(function _callee2$(_context2) {
        while (1) switch (_context2.prev = _context2.next) {
          case 0:
            _context2.next = 2;
            return apiGame('/api/click-frenzy', {
              method: 'POST',
              body: '{}'
            });
          case 2:
            _yield$apiGame = _context2.sent;
            ok = _yield$apiGame.ok;
            data = _yield$apiGame.data;
            if (ok) setFishClicks(data.fish_clicks);
          case 6:
          case "end":
            return _context2.stop();
        }
      }, _callee2);
    })), 5000);
    return function () {
      return clearInterval(id);
    };
  }, [clickFrenzyRate]);
  useEffect(function () {
    var currentNumber = season ? season.season_number : null;
    var id = setInterval(/*#__PURE__*/_asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee3() {
      var r, gs;
      return _regeneratorRuntime().wrap(function _callee3$(_context3) {
        while (1) switch (_context3.prev = _context3.next) {
          case 0:
            _context3.next = 2;
            return apiFetch('/api/season');
          case 2:
            r = _context3.sent;
            if (r.ok) {
              _context3.next = 5;
              break;
            }
            return _context3.abrupt("return");
          case 5:
            if (!(currentNumber !== null && r.data.season_number !== currentNumber)) {
              _context3.next = 13;
              break;
            }
            showToast("Season ".concat(currentNumber, " has ended! Season ").concat(r.data.season_number, " begins!"));
            _context3.next = 9;
            return apiGame('/api/state');
          case 9:
            gs = _context3.sent;
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
            }
            _context3.next = 14;
            break;
          case 13:
            setSeason(r.data);
          case 14:
          case "end":
            return _context3.stop();
        }
      }, _callee3);
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
  var flushClicks = useCallback(/*#__PURE__*/_asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee4() {
    var count, _yield$apiGame2, ok, data;
    return _regeneratorRuntime().wrap(function _callee4$(_context4) {
      while (1) switch (_context4.prev = _context4.next) {
        case 0:
          count = clickBufferRef.current;
          if (!(count === 0)) {
            _context4.next = 3;
            break;
          }
          return _context4.abrupt("return");
        case 3:
          clickBufferRef.current = 0;
          _context4.next = 6;
          return apiGame('/api/fish-click', {
            method: 'POST',
            body: JSON.stringify({
              count: count
            })
          });
        case 6:
          _yield$apiGame2 = _context4.sent;
          ok = _yield$apiGame2.ok;
          data = _yield$apiGame2.data;
          if (ok) setFishClicks(data.fish_clicks);
        case 10:
        case "end":
          return _context4.stop();
      }
    }, _callee4);
  })), []);
  useEffect(function () {
    var id = setInterval(flushClicks, 500);
    return function () {
      clearInterval(id);
      var count = clickBufferRef.current;
      if (count > 0) {
        clickBufferRef.current = 0;
        apiGame('/api/fish-click', {
          method: 'POST',
          body: JSON.stringify({
            count: count
          })
        });
      }
    };
  }, [flushClicks]);
  var handleBuy = useCallback(/*#__PURE__*/function () {
    var _ref17 = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee5(id) {
      var _yield$apiGame3, ok, data, _data$regen_recharge_;
      return _regeneratorRuntime().wrap(function _callee5$(_context5) {
        while (1) switch (_context5.prev = _context5.next) {
          case 0:
            _context5.next = 2;
            return apiGame('/api/buy', {
              method: 'POST',
              body: JSON.stringify({
                item_id: id
              })
            });
          case 2:
            _yield$apiGame3 = _context5.sent;
            ok = _yield$apiGame3.ok;
            data = _yield$apiGame3.data;
            if (ok) {
              setFishClicks(data.fish_clicks);
              setOwnedItems(data.owned_items);
              setShieldCharges(data.shield_charges);
              setRegenRechargeWins((_data$regen_recharge_ = data.regen_recharge_wins) !== null && _data$regen_recharge_ !== void 0 ? _data$regen_recharge_ : 0);
              if (data.active_cosmetics) setActiveCosmetics(data.active_cosmetics);
            } else {
              showToast(data.error || 'Purchase failed');
            }
          case 6:
          case "end":
            return _context5.stop();
        }
      }, _callee5);
    }));
    return function (_x3) {
      return _ref17.apply(this, arguments);
    };
  }(), [showToast]);
  var handleEquip = useCallback(/*#__PURE__*/function () {
    var _ref18 = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee6(id) {
      var _yield$apiGame4, ok, data;
      return _regeneratorRuntime().wrap(function _callee6$(_context6) {
        while (1) switch (_context6.prev = _context6.next) {
          case 0:
            _context6.next = 2;
            return apiGame('/api/equip', {
              method: 'POST',
              body: JSON.stringify({
                fish_id: id
              })
            });
          case 2:
            _yield$apiGame4 = _context6.sent;
            ok = _yield$apiGame4.ok;
            data = _yield$apiGame4.data;
            if (ok) setEquippedFish(data.equipped_fish);else showToast(data.error || 'Equip failed');
          case 6:
          case "end":
            return _context6.stop();
        }
      }, _callee6);
    }));
    return function (_x4) {
      return _ref18.apply(this, arguments);
    };
  }(), [showToast]);
  var handleEquipCosmetic = useCallback(/*#__PURE__*/function () {
    var _ref19 = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee7(id) {
      var _yield$apiGame5, ok, data;
      return _regeneratorRuntime().wrap(function _callee7$(_context7) {
        while (1) switch (_context7.prev = _context7.next) {
          case 0:
            _context7.next = 2;
            return apiGame('/api/equip-cosmetic', {
              method: 'POST',
              body: JSON.stringify({
                item_id: id
              })
            });
          case 2:
            _yield$apiGame5 = _context7.sent;
            ok = _yield$apiGame5.ok;
            data = _yield$apiGame5.data;
            if (ok) setActiveCosmetics(data.active_cosmetics);else showToast(data.error || 'Equip failed');
          case 6:
          case "end":
            return _context7.stop();
        }
      }, _callee7);
    }));
    return function (_x5) {
      return _ref19.apply(this, arguments);
    };
  }(), [showToast]);
  var handleFishClick = useCallback(function () {
    setFishClicks(function (c) {
      return c + clickAmount;
    });
    clickBufferRef.current += 1;
    if (clickBufferRef.current >= 10) flushClicks();
  }, [clickAmount, flushClicks]);

  // Shared post-spin state update (used both directly and via guard callback)
  var applySpinResult = useCallback(function (data) {
    var _data$regen_recharge_2, _data$regen_recharge_3;
    setResult(data.result);
    setWins(data.wins);
    setLosses(data.losses);
    setStreak(data.streak);
    setShieldCharges(data.shield_charges);
    setRegenRechargeWins((_data$regen_recharge_2 = data.regen_recharge_wins) !== null && _data$regen_recharge_2 !== void 0 ? _data$regen_recharge_2 : 0);
    if (data.owned_items) setOwnedItems(data.owned_items);
    setBonusEarned(data.bonus_earned);
    setEchoTriggered(!!data.echo_triggered);
    setJackpotHit(!!data.jackpot_hit);
    setResilienceTriggered(!!data.resilience_triggered);
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
    if (data.result === 'win' || data.guard_triggered && data.guard_blocked) {
      setConfetti(true);
    } else if (cosm.includes('party_mode')) {
      setConfetti(true);
    }
    var mood = data.result === 'win' || data.guard_triggered && data.guard_blocked ? 'happy' : 'sad';
    setFishMood(mood);
    if (fishTimerRef.current) clearTimeout(fishTimerRef.current);
    fishTimerRef.current = setTimeout(function () {
      return setFishMood('idle');
    }, 2500);
    spinningRef.current = false;
    setSpinning(false);
  }, []);
  var spin = useCallback(/*#__PURE__*/_asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee8() {
    var data, res, base, segmentAngle, minTarget, newRotation;
    return _regeneratorRuntime().wrap(function _callee8$(_context8) {
      while (1) switch (_context8.prev = _context8.next) {
        case 0:
          if (!spinningRef.current) {
            _context8.next = 2;
            break;
          }
          return _context8.abrupt("return");
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
          spinningRef.current = true;
          setSpinning(true);
          _context8.prev = 9;
          _context8.next = 12;
          return apiGame('/api/spin', {
            method: 'POST',
            body: '{}'
          });
        case 12:
          res = _context8.sent;
          if (res.ok) {
            _context8.next = 18;
            break;
          }
          spinningRef.current = false;
          setSpinning(false);
          if (autoSpinRef.current) setTimeout(function () {
            if (autoSpinRef.current) spin();
          }, 1000);
          return _context8.abrupt("return");
        case 18:
          data = res.data;
          _context8.next = 27;
          break;
        case 21:
          _context8.prev = 21;
          _context8.t0 = _context8["catch"](9);
          spinningRef.current = false;
          setSpinning(false);
          if (autoSpinRef.current) setTimeout(function () {
            if (autoSpinRef.current) spin();
          }, 1000);
          return _context8.abrupt("return");
        case 27:
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
        case 34:
        case "end":
          return _context8.stop();
      }
    }, _callee8, null, [[9, 21]]);
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
    var _ref21 = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee9() {
      return _regeneratorRuntime().wrap(function _callee9$(_context9) {
        while (1) switch (_context9.prev = _context9.next) {
          case 0:
            _context9.next = 2;
            return apiFetch('/api/logout', {
              method: 'POST',
              body: '{}'
            });
          case 2:
            onLogout();
          case 3:
          case "end":
            return _context9.stop();
        }
      }, _callee9);
    }));
    return function handleLogout() {
      return _ref21.apply(this, arguments);
    };
  }();
  var hasGuard = ownedItems.includes('guard');
  var hasRegen = ownedItems.includes('regen_shield');
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(StatsPanel, {
    open: showStats,
    onClose: function onClose() {
      return setShowStats(false);
    }
  }), toast && /*#__PURE__*/React.createElement("div", {
    className: "toast-notification"
  }, toast), /*#__PURE__*/React.createElement(Confetti, {
    active: confetti,
    count: confettiCount
  }), /*#__PURE__*/React.createElement("div", {
    className: "overlay ".concat(showResult ? 'active' : '')
  }), guardState && /*#__PURE__*/React.createElement(GuardWheel, {
    blocked: guardState.blocked,
    onComplete: function onComplete() {
      return guardCompleteRef.current && guardCompleteRef.current();
    }
  }), season && season.latest_winners && /*#__PURE__*/React.createElement(SeasonWinners, {
    winners: season.latest_winners,
    seasonNumber: season.season_number - 1
  }), /*#__PURE__*/React.createElement("div", {
    className: "user-bar"
  }, /*#__PURE__*/React.createElement("span", {
    className: "user-bar-name"
  }, "\uD83D\uDC64 ", username), /*#__PURE__*/React.createElement("button", {
    className: "stats-btn",
    onClick: function onClick() {
      return setShowStats(true);
    }
  }, "\uD83D\uDCCA"), /*#__PURE__*/React.createElement("button", {
    className: "logout-btn",
    onClick: handleLogout
  }, "Logout"), season && /*#__PURE__*/React.createElement(SeasonInfo, {
    seasonNumber: season.season_number,
    endsAt: season.ends_at
  })), /*#__PURE__*/React.createElement(Fish, {
    mood: fishMood,
    net: wins - losses,
    fishClicks: fishClicks,
    fishData: getFishData(equippedFish),
    sizeRem: fishSizeRem,
    trailClass: trailClass,
    onFishClick: handleFishClick
  }), showResult && /*#__PURE__*/React.createElement("div", {
    className: "result-banner ".concat(showResult && !hideResult ? 'show' : '', " ").concat(hideResult ? 'hide' : '')
  }, result === 'win' || result === 'lose' && shieldFeedback ? /*#__PURE__*/React.createElement("div", {
    className: "result-text ".concat(result === 'win' ? 'win' : 'win')
  }, result === 'win' ? '🎰 YOU WIN! 🎰' : '🛡️ BLOCKED! 🛡️') : /*#__PURE__*/React.createElement("div", {
    className: "result-text lose"
  }, "\uD83D\uDC80 YOU LOSE \uD83D\uDC80"), jackpotHit && /*#__PURE__*/React.createElement("div", {
    className: "bonus-line jackpot-line"
  }, "\uD83C\uDFB0 JACKPOT! 50x MULTIPLIER! \uD83C\uDFB0"), echoTriggered && !jackpotHit && /*#__PURE__*/React.createElement("div", {
    className: "bonus-line echo-line"
  }, "\uD83D\uDD0A WIN ECHO! Double wins!"), resilienceTriggered && /*#__PURE__*/React.createElement("div", {
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
  }), /*#__PURE__*/React.createElement("div", {
    className: "bulbs"
  }, Array.from({
    length: 16
  }, function (_, i) {
    return /*#__PURE__*/React.createElement("div", {
      key: i,
      className: "bulb"
    });
  }))), /*#__PURE__*/React.createElement("div", {
    className: "game-right"
  }, /*#__PURE__*/React.createElement("div", {
    className: "game-right-body"
  }, /*#__PURE__*/React.createElement("div", {
    className: "game-right-sidebar"
  }, /*#__PURE__*/React.createElement(StreakPanel, {
    streak: streak
  }), (hasGuard || hasRegen) && /*#__PURE__*/React.createElement("div", {
    className: "shield-indicator"
  }, hasGuard && /*#__PURE__*/React.createElement("div", null, "\uD83D\uDEE1\uFE0F Guard ready"), hasRegen && /*#__PURE__*/React.createElement("div", null, regenRechargeWins > 0 ? "\uD83D\uDD04 ".concat(regenRechargeWins, " win").concat(regenRechargeWins !== 1 ? 's' : '') : '🔄 ready'))), /*#__PURE__*/React.createElement(ShopPanel, {
    fishClicks: fishClicks,
    ownedItems: ownedItems,
    equippedFish: equippedFish,
    activeCosmetics: activeCosmetics,
    onBuy: handleBuy,
    onEquip: handleEquip,
    onEquipCosmetic: handleEquipCosmetic
  }))), /*#__PURE__*/React.createElement("div", {
    className: "leaderboard-bar"
  }, /*#__PURE__*/React.createElement(Leaderboard, {
    currentUser: username
  })));
}

// ── Root App ───────────────────────────────────────────────────────────────
function App() {
  var _useState77 = useState(undefined),
    _useState78 = _slicedToArray(_useState77, 2),
    user = _useState78[0],
    setUser = _useState78[1];
  var _useState79 = useState(null),
    _useState80 = _slicedToArray(_useState79, 2),
    gameState = _useState80[0],
    setGameState = _useState80[1];
  var _useState81 = useState(''),
    _useState82 = _slicedToArray(_useState81, 2),
    sessionMsg = _useState82[0],
    setSessionMsg = _useState82[1];
  useEffect(function () {
    localStorage.clear();
  }, []);
  useEffect(function () {
    _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee0() {
      var _yield$apiFetch2, ok, data, gs;
      return _regeneratorRuntime().wrap(function _callee0$(_context0) {
        while (1) switch (_context0.prev = _context0.next) {
          case 0:
            _context0.next = 2;
            return apiFetch('/api/me');
          case 2:
            _yield$apiFetch2 = _context0.sent;
            ok = _yield$apiFetch2.ok;
            data = _yield$apiFetch2.data;
            if (!(ok && data.username)) {
              _context0.next = 12;
              break;
            }
            _context0.next = 8;
            return apiFetch('/api/state');
          case 8:
            gs = _context0.sent;
            if (gs.ok) {
              setGameState(gs.data);
              setUser(data.username);
            } else {
              setUser(null);
            }
            _context0.next = 13;
            break;
          case 12:
            setUser(null);
          case 13:
          case "end":
            return _context0.stop();
        }
      }, _callee0);
    }))();
  }, []);
  var handleAuth = /*#__PURE__*/function () {
    var _ref23 = _asyncToGenerator(/*#__PURE__*/_regeneratorRuntime().mark(function _callee1(username) {
      var gs;
      return _regeneratorRuntime().wrap(function _callee1$(_context1) {
        while (1) switch (_context1.prev = _context1.next) {
          case 0:
            _context1.next = 2;
            return apiFetch('/api/state');
          case 2:
            gs = _context1.sent;
            if (gs.ok) {
              setGameState(gs.data);
              setUser(username);
              setSessionMsg('');
            }
          case 4:
          case "end":
            return _context1.stop();
        }
      }, _callee1);
    }));
    return function handleAuth(_x6) {
      return _ref23.apply(this, arguments);
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
