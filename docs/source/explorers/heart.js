/* The Hong Kong heart: one beat per year, 1884 to 2025.
   Shape  the year's daily rainfall wrapped round a circle (1 January at the top, clockwise), in five-day bins:
          the wet season is the bulge. A square root keeps one extreme day from flattening every other year.
   Beat   its size is the year's peak day, its pace the days since the previous annual peak (the ECG of Issue 3).
   Colour the anomaly score. The three years before it linger as faint outlines.
   Two renderers share one state: flat (canvas 2D) and 3D (three.js, loaded on demand; the same shape, inflated).
   Needs engine.js for css(), ramp(), rgba(), fmt() and FONT. */
(function () {
  const PBINS = 73, THREE_URL = "https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js";
  const ease3 = (t) => 1 - Math.pow(1 - t, 3), clamp01 = (t) => Math.max(0, Math.min(1, t));
  let threeLoading = null;
  function loadThree() {
    if (window.THREE) return Promise.resolve();
    if (!threeLoading) threeLoading = new Promise((res, rej) => { const s = document.createElement("script"); s.src = THREE_URL; s.onload = res; s.onerror = () => rej(new Error("three.js did not load")); document.head.appendChild(s); });
    return threeLoading;
  }
  function smooth(a) { const n = a.length, w = [0.06, 0.24, 0.4, 0.24, 0.06]; return a.map((_, k) => { let s = 0; for (let j = -2; j <= 2; j++) s += w[j + 2] * a[(k + j + n) % n]; return s; }); }

  function create(root, G, opts) {
    opts = Object.assign({ controls: true, toggle: true, note: true, mode: "2d", autoplay: true, onYear: null }, opts || {});
    const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
    const S = { i: 0, u: reduce ? 0.6 : 0, rest: false, playing: opts.autoplay && !reduce, mode: "2d", raf: 0, last: 0, T: 0, suspended: false, dead: false, t3: null, drag: null };
    const bins = G.daily.map(d => { const b = new Array(PBINS).fill(0); for (let k = 0; k < 366; k++) if (d[k] > 0) b[Math.min(PBINS - 1, Math.floor(k / 5))] += d[k] / 10; return b; });
    const cache = {}, shape = (i) => cache[i] || (cache[i] = smooth(smooth(bins[i].map(v => Math.min(2.4, Math.sqrt(v / 100))))));
    const peakMax = Math.max(...G.facts.map(f => f.peak));
    const last = () => { for (let i = G.n - 1; i >= 0; i--) if (G.fit[i]) return i; return G.n - 1; };
    const dur = (i) => 0.88 * (G.facts[i].rr > 0 ? Math.max(0.6, Math.min(1.4, G.facts[i].rr / 365)) : 1);
    const gapAfter = (i) => i < G.n - 1 && G.labels[i + 1] - G.labels[i] > 1;
    const KEY = '<dl class="hkey"><div><dt>Shape</dt><dd>The year\'s rain round a circle, January at the top.</dd></div>' +
      '<div><dt>Beat</dt><dd>Size: peak day. Pace: days since the last peak.</dd></div>' +
      '<div><dt>Colour</dt><dd>Anomaly score <span class="legend"><span>typical</span><i></i><span>unusual</span></span></dd></div>' +
      (G.va ? '<div><dt>Corner</dt><dd>Valence and arousal, relative to the record.</dd></div>' : '') +
      '<div class="k3" hidden><dt>3D</dt><dd>Drag to turn.</dd></div></dl>';

    root.innerHTML = '<div class="hv"><canvas class="h2d" role="img" aria-label="A blob drawn from one year of Hong Kong rainfall, beating once for each year of the record"></canvas><div class="h3d" hidden></div>' + (G.va ? '<canvas class="hva" role="img" aria-label="Valence and arousal of the year, on a circumplex"></canvas>' : "") + '</div>' +
      (opts.toggle ? '<div class="heart-tools" role="group" aria-label="Rendering"><button type="button" class="chip" data-m="2d" aria-pressed="true">Flat</button><button type="button" class="chip" data-m="3d" aria-pressed="false">3D</button></div>' : "") +
      (opts.controls ? '<div class="pulsebar"><button type="button" class="hplay">Pause</button><input class="hrange" type="range" min="0" max="0" value="0" step="1" aria-label="Year"><output class="hyear"></output></div>' : "") +
      (opts.note ? KEY : "");
    const $r = (s) => root.querySelector(s), c2 = $r(".h2d"), h3 = $r(".h3d");
    const setNote = () => { const k = $r(".k3"); if (k) k.hidden = S.mode !== "3d"; };
    setNote();

    /* ----- the state shared by both renderers ----- */
    function frame() {
      const i = S.i, prev = Math.max(0, i - 1), u = S.u;
      const m = i === 0 ? ease3(clamp01(u / 0.6)) : ease3(clamp01(u / 0.45));
      const s1 = shape(i), s0 = i === 0 ? s1.map(() => 0) : shape(prev), sh = s1.map((v, k) => s0[k] + (v - s0[k]) * m);
      const score = (G.norm[prev] || 0) + ((G.norm[i] || 0) - (G.norm[prev] || 0)) * m;
      const amp = 0.012 + 0.07 * Math.sqrt(G.facts[i].peak / peakMax);
      const beat = S.rest ? 0 : Math.exp(-Math.pow((u - 0.10) / 0.05, 2)) + 0.55 * Math.exp(-Math.pow((u - 0.34) / 0.06, 2));
      return { i, prev, sh, score, amp, sc: 1 + amp * beat, beat };
    }
    function emit() { if (opts.onYear) opts.onYear(S.i); }
    function sync() {
      const p = $r(".hplay"); if (!p) return;
      p.textContent = S.playing ? "Pause" : (S.i >= last() && S.u >= dur(S.i) ? "Replay" : "Play");
      $r(".hrange").max = last(); $r(".hrange").value = S.i; $r(".hyear").textContent = G.labels[S.i];
    }
    function go(i, settled, silent) { S.i = i; S.u = settled ? 0.6 : 0; S.rest = false; sync(); if (!silent) emit(); }
    function step(dt) {
      if (!S.playing) return;
      S.u += dt;
      if (S.rest) { if (S.u >= 2.4) go(S.i + 1); return; }
      if (S.u >= dur(S.i)) {
        if (S.i >= last()) { S.playing = false; sync(); return; }
        if (gapAfter(S.i)) { S.rest = true; S.u = 0; } else go(S.i + 1);
      }
    }

    /* ----- flat ----- */
    function draw2d() {
      const dpr = window.devicePixelRatio || 1, w = c2.clientWidth, h = c2.clientHeight; if (!w || !h) return;
      if (c2.width !== Math.round(w * dpr) || c2.height !== Math.round(h * dpr)) { c2.width = Math.round(w * dpr); c2.height = Math.round(h * dpr); }
      const x = c2.getContext("2d"); x.setTransform(dpr, 0, 0, dpr, 0, 0); x.clearRect(0, 0, w, h); x.font = "12px " + FONT;
      const ink = css("--ink"), muted = css("--muted"), rule = css("--rule"), f = frame(), i = f.i;
      const R = Math.min(w / 2 - 56, h / 2 - 40), cx = w / 2, cy = h / 2 - 8, Rb = R * 0.55, A = R * 0.2;
      x.textBaseline = "middle"; x.textAlign = "center";
      x.strokeStyle = rule; x.lineWidth = 1; x.setLineDash([2, 4]); x.beginPath(); x.arc(cx, cy, Rb, 0, 6.2832); x.stroke(); x.setLineDash([]);
      x.fillStyle = muted; [["JAN", -90], ["APR", 0], ["JUL", 90], ["OCT", 180]].forEach(([t, d]) => { const a = d * Math.PI / 180, r = R + 22; x.fillText(t, cx + r * Math.cos(a), cy + r * Math.sin(a)); });
      if (S.rest) {
        x.fillStyle = ink; x.font = "400 17px " + css("--title"); x.fillText("No record", cx, cy - 7); x.font = "12px " + FONT; x.fillStyle = muted;
        x.fillText(G.labels[i] + 1 + "–" + (G.labels[i + 1] - 1), cx, cy + 16); return;
      }
      const path = (sh, k0) => { const p = sh.map((v, k) => { const a = -Math.PI / 2 + 2 * Math.PI * (k + 0.5) / PBINS, r = (Rb + A * v) * k0; return [cx + r * Math.cos(a), cy + r * Math.sin(a)]; }), n = p.length;
        x.beginPath(); x.moveTo((p[n - 1][0] + p[0][0]) / 2, (p[n - 1][1] + p[0][1]) / 2);
        for (let k = 0; k < n; k++) { const q = p[(k + 1) % n]; x.quadraticCurveTo(p[k][0], p[k][1], (p[k][0] + q[0]) / 2, (p[k][1] + q[1]) / 2); } x.closePath(); };
      for (let g = 3; g >= 1; g--) { const j = i - g; if (j < 0) continue; path(shape(j), 1); x.strokeStyle = rgba(ramp(0.15 + 0.85 * (G.norm[j] || 0)), 0.2 / g + 0.04); x.lineWidth = 1.2; x.stroke(); }
      const gr = (Rb + A * 2.4) * 1.15 * f.sc, glow = x.createRadialGradient(cx, cy, Rb * 0.3, cx, cy, gr);
      glow.addColorStop(0, rgba(css("--c1"), 0)); glow.addColorStop(0.6, rgba(ramp(f.score), 0.16 + 0.06 * f.beat)); glow.addColorStop(1, rgba(ramp(f.score), 0));
      x.fillStyle = glow; x.beginPath(); x.arc(cx, cy, gr, 0, 6.2832); x.fill();
      path(f.sh, f.sc);
      const fill = x.createRadialGradient(cx, cy, 0, cx, cy, (Rb + A * 2.4) * f.sc); fill.addColorStop(0, rgba(css("--c0"), 0.5)); fill.addColorStop(0.55, rgba(ramp(0.1 + 0.7 * f.score), 0.6)); fill.addColorStop(1, rgba(ramp(0.1 + 0.9 * f.score), 0.88));
      x.fillStyle = fill; x.fill(); x.strokeStyle = rgba(ramp(Math.min(1, 0.3 + f.score)), 0.95); x.lineWidth = 1.6; x.stroke();
      x.fillStyle = ink; x.font = "400 20px " + css("--title"); x.fillText(G.labels[i], cx, cy - 5); x.font = "12px " + FONT;
      x.fillStyle = muted; x.fillText(G.fit[i] ? "score " + G.norm[i].toFixed(2) : "not fitted", cx, cy + 20);
      const rr = G.facts[i].rr; x.fillText("peak day " + fmt(G.facts[i].peak) + " mm" + (rr > 0 ? " · " + rr + " days since the previous peak" : ""), cx, h - 10);
    }

    /* ----- 3D: the same shape as a soft, round body floating in mid-air, with its shadow far below ----- */
    const NA = 96, NR = 18, ROWS = 2 * NR + 1;
    const VERT = "varying vec3 vN; varying vec3 vV; varying vec3 vObj;\nvoid main() { vObj = position; vec4 mv = modelViewMatrix * vec4(position, 1.0); vN = normalize(normalMatrix * normal); vV = normalize(-mv.xyz); gl_Position = projectionMatrix * mv; }";
    const FRAG = [
      "uniform vec3 uColor; uniform float uTime; uniform float uBeat; uniform float uBack;",
      "varying vec3 vN; varying vec3 vV; varying vec3 vObj;",
      "float hash(vec3 p) { p = fract(p * 0.3183099 + 0.1); p *= 17.0; return fract(p.x * p.y * p.z * (p.x + p.y + p.z)); }",
      "float noise(vec3 x) { vec3 i = floor(x); vec3 f = fract(x); f = f * f * (3.0 - 2.0 * f);",
      "  return mix(mix(mix(hash(i), hash(i + vec3(1,0,0)), f.x), mix(hash(i + vec3(0,1,0)), hash(i + vec3(1,1,0)), f.x), f.y),",
      "             mix(mix(hash(i + vec3(0,0,1)), hash(i + vec3(1,0,1)), f.x), mix(hash(i + vec3(0,1,1)), hash(i + vec3(1,1,1)), f.x), f.y), f.z); }",
      "float fbm(vec3 p) { float a = 0.5, s = 0.0; for (int i = 0; i < 4; i++) { s += a * noise(p); p *= 2.03; a *= 0.5; } return s; }",
      "void main() {",
      "  vec3 n = normalize(vN); if (uBack > 0.5) n = -n;",
      "  vec3 v = normalize(vV), L = normalize(vec3(-0.45, 0.8, 0.55));",
      "  float diff = clamp(dot(n, L) * 0.5 + 0.5, 0.0, 1.0);",
      "  vec3 p = normalize(vObj - vec3(0.0, 2.6, 0.0)) * 2.0 + vec3(0.0, uTime * 0.04, uTime * 0.02);",
      "  float w = fbm(p * 1.3 + 1.7 * fbm(p * 2.0 + uTime * 0.03));",
      "  float wisp = pow(1.0 - abs(sin(w * 13.0)), 7.0);",
      "  float fres = pow(1.0 - clamp(dot(n, v), 0.0, 1.0), 2.2);",
      "  vec3 col = uColor * (0.64 + 0.5 * diff) * (0.82 + 0.34 * w);",
      "  col = mix(col, vec3(1.0), wisp * 0.62) + fres * vec3(0.26, 0.38, 0.52) + uBeat * 0.1 * uColor;",
      "  vec3 hv = normalize(L + v); col += pow(max(dot(n, hv), 0.0), 46.0) * 0.5;",
      "  float a = clamp(0.5 + 0.4 * fres + 0.3 * wisp + 0.1 * diff, 0.0, 0.96);",
      "  if (uBack > 0.5) { col *= 0.55; a *= 0.5; }",
      "  gl_FragColor = vec4(col, a);",
      "}"].join("\n");
    function build3d() {
      const T = window.THREE, renderer = new T.WebGLRenderer({ antialias: true, alpha: true });
      renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1)); h3.appendChild(renderer.domElement); renderer.domElement.style.cssText = "display:block;width:100%;height:100%;touch-action:none;cursor:grab";
      const cap = document.createElement("div"); cap.className = "h3cap"; h3.appendChild(cap);
      const scene = new T.Scene(), camera = new T.PerspectiveCamera(28, 1, 0.1, 100); camera.position.set(0, 2.7, 13.2); camera.lookAt(0, 1.7, 0);
      const geo = new T.BufferGeometry(), pos = new Float32Array(ROWS * NA * 3), idx = [];
      for (let j = 0; j < ROWS - 1; j++) for (let a = 0; a < NA; a++) { const a2 = (a + 1) % NA, p = j * NA + a, q = j * NA + a2, r = (j + 1) * NA + a, s = (j + 1) * NA + a2; idx.push(p, r, q, q, r, s); }
      geo.setAttribute("position", new T.BufferAttribute(pos, 3)); geo.setIndex(idx);
      const shared = { uColor: { value: new T.Color(0x4682b4) }, uTime: { value: 0 }, uBeat: { value: 0 } };
      const mk = (back, side) => new T.ShaderMaterial({ uniforms: Object.assign({ uBack: { value: back } }, shared), vertexShader: VERT, fragmentShader: FRAG, transparent: true, depthWrite: false, side });
      const inner = new T.Mesh(geo, mk(1, T.BackSide)), body = new T.Mesh(geo, mk(0, T.FrontSide)); inner.renderOrder = 0; body.renderOrder = 1;   // the inside first, then the outside over it
      const group = new T.Group(); group.add(inner); group.add(body);
      scene.add(group);
      const cv = document.createElement("canvas"); cv.width = cv.height = 128; const cg = cv.getContext("2d"), gr = cg.createRadialGradient(64, 64, 6, 64, 64, 62); gr.addColorStop(0, "rgba(10,30,50,.34)"); gr.addColorStop(0.55, "rgba(10,30,50,.12)"); gr.addColorStop(1, "rgba(10,30,50,0)"); cg.fillStyle = gr; cg.fillRect(0, 0, 128, 128);
      const floor = new T.Mesh(new T.PlaneGeometry(1, 1), new T.MeshBasicMaterial({ map: new T.CanvasTexture(cv), transparent: true, depthWrite: false })); floor.rotation.x = -Math.PI / 2; floor.position.y = 0.0; floor.scale.set(5.6, 5.6, 1); scene.add(floor);
      const el = renderer.domElement;
      el.addEventListener("pointerdown", (e) => { S.drag = { x: e.clientX, ry: group.rotation.y }; el.setPointerCapture(e.pointerId); el.style.cursor = "grabbing"; });
      el.addEventListener("pointermove", (e) => { if (S.drag) group.rotation.y = S.drag.ry + (e.clientX - S.drag.x) * 0.01; });
      const end = () => { S.drag = null; el.style.cursor = "grab"; }; el.addEventListener("pointerup", end); el.addEventListener("pointercancel", end);
      S.t3 = { T, renderer, scene, camera, group, geo, pos, shared, cap, floor, w: 0, h: 0 };
    }
    function resample(sh, a) { const f = a * PBINS / NA, k = Math.floor(f), t = f - k; return sh[k % PBINS] * (1 - t) + sh[(k + 1) % PBINS] * t; }
    function render3d() {
      const t3 = S.t3, w = h3.clientWidth, h = h3.clientHeight; if (!t3 || !w || !h) return;
      if (t3.w !== w || t3.h !== h) { t3.renderer.setSize(w, h, false); t3.camera.aspect = w / h; t3.camera.updateProjectionMatrix(); t3.w = w; t3.h = h; }
      const f = frame(), Rb = 1.9, A = 0.5, Ht = 1.85, Hb = 1.85, pos = t3.pos, soft = smooth(smooth(smooth(f.sh))), bob = Math.sin(S.T * 1.05), Yc = 2.6 + 0.14 * bob;
      const grow = 1 + 0.5 * f.amp * f.beat, ys = (S.rest ? 0.2 : 1) * (1 + 2.4 * f.amp * f.beat);          // the beat: a little wider, a little taller
      const radius = Array.from({ length: NA }, (_, a) => S.rest ? Rb : (Rb + A * resample(soft, a)) * grow);
      for (let j = 0; j < ROWS; j++) {
        const top = j <= NR, t = top ? j / NR : (2 * NR - j) / NR, y = Yc + (top ? Ht : -Hb) * Math.sqrt(Math.max(0, 1 - t * t)) * ys;      // a round body, floating
        for (let a = 0; a < NA; a++) { const phi = -Math.PI / 2 + 2 * Math.PI * (a + 0.5) / NA, rho = t * radius[a], o = (j * NA + a) * 3; pos[o] = rho * Math.cos(phi); pos[o + 1] = y; pos[o + 2] = rho * Math.sin(phi); }
      }
      t3.geo.attributes.position.needsUpdate = true; t3.geo.computeVertexNormals();
      t3.floor.material.opacity = (S.rest ? 0.25 : 0.7) - 0.18 * bob; t3.floor.scale.set(5.2 - 0.5 * bob, 5.2 - 0.5 * bob, 1);   // the shadow below, far away like on the poster
      t3.shared.uColor.value.set(ramp(0.3 + 0.7 * f.score)); t3.shared.uTime.value = S.T; t3.shared.uBeat.value = S.rest ? 0 : f.beat;
      if (!S.drag && !reduce) t3.group.rotation.y = 0.28 * Math.sin(S.T * 0.35);
      const g = G.facts[f.i], rr = g.rr, txt = S.rest ? "No record " + (G.labels[f.i] + 1) + "–" + (G.labels[f.i + 1] - 1) : '<b>' + G.labels[f.i] + '</b><span>' + (G.fit[f.i] ? "score " + G.norm[f.i].toFixed(2) : "not fitted") + " · peak day " + fmt(g.peak) + " mm" + (rr > 0 ? " · " + rr + " days since the previous peak" : "") + "</span>";
      if (t3.capTxt !== txt) { t3.cap.innerHTML = txt; t3.capTxt = txt; }
      t3.renderer.render(t3.scene, t3.camera);
    }

    /* ----- the corner: valence (left-right) and arousal (up-down), every year a faint dot, the current year moving ----- */
    function drawVA() {
      const c = $r(".hva"); if (!c || !G.va) return;
      const dpr = window.devicePixelRatio || 1, w = c.clientWidth, h = c.clientHeight; if (!w || !h) return;
      if (c.width !== Math.round(w * dpr) || c.height !== Math.round(h * dpr)) { c.width = Math.round(w * dpr); c.height = Math.round(h * dpr); }
      const x = c.getContext("2d"); x.setTransform(dpr, 0, 0, dpr, 0, 0); x.clearRect(0, 0, w, h);
      const pad = 5, side = Math.min(w - 2 * pad, h - 24), X = (v) => pad + (v + 1) / 2 * side, Y = (a) => pad + (1 - a) * side;
      const muted = css("--muted"), rule = css("--rule"), f = frame(), i = f.i, prev = Math.max(0, i - 1);
      x.fillStyle = rgba(css("--bg"), 0.55); x.fillRect(pad, pad, side, side); x.strokeStyle = rule; x.lineWidth = 1; x.strokeRect(pad + 0.5, pad + 0.5, side - 1, side - 1);
      x.setLineDash([2, 3]); x.beginPath(); x.moveTo(X(0) + 0.5, pad); x.lineTo(X(0) + 0.5, pad + side); x.moveTo(pad, Y(0.5) + 0.5); x.lineTo(pad + side, Y(0.5) + 0.5); x.stroke(); x.setLineDash([]);
      x.fillStyle = rgba(muted, 0.32); for (let k = 0; k < G.n; k++) { const v = G.va.v[k], a = G.va.a[k]; if (v === null || a === null) continue; x.beginPath(); x.arc(X(v), Y(a), 1.2, 0, 6.2832); x.fill(); }
      x.font = "9.5px " + FONT; x.fillStyle = muted; x.textAlign = "center"; x.textBaseline = "middle";
      x.fillText("activated", pad + side / 2, pad + 8); x.fillText("calm", pad + side / 2, pad + side - 8);
      x.save(); x.translate(pad + 8, pad + side / 2); x.rotate(-Math.PI / 2); x.fillText("unpleasant", 0, 0); x.restore();
      x.save(); x.translate(pad + side - 8, pad + side / 2); x.rotate(Math.PI / 2); x.fillText("pleasant", 0, 0); x.restore();
      const ok = (k) => k >= 0 && G.va.v[k] !== null && G.va.a[k] !== null;
      let text = "no record";
      if (!S.rest && ok(i)) {
        const m = i === 0 ? ease3(clamp01(S.u / 0.6)) : ease3(clamp01(S.u / 0.45)), p0 = ok(prev) ? prev : i;
        const v = G.va.v[p0] + (G.va.v[i] - G.va.v[p0]) * m, a = G.va.a[p0] + (G.va.a[i] - G.va.a[p0]) * m;
        x.lineWidth = 1; for (let g2 = 6; g2 >= 1; g2--) { const j = i - g2, j2 = j + 1; if (j < 0 || !ok(j) || !ok(j2)) continue; x.strokeStyle = rgba(css("--c3"), 0.5 / g2); x.beginPath(); x.moveTo(X(G.va.v[j]), Y(G.va.a[j])); x.lineTo(X(G.va.v[j2]), Y(G.va.a[j2])); x.stroke(); }
        x.fillStyle = ramp(0.3 + 0.7 * f.score); x.beginPath(); x.arc(X(v), Y(a), 4, 0, 6.2832); x.fill(); x.strokeStyle = css("--ink"); x.lineWidth = 1.2; x.stroke();
        text = "valence " + (G.va.v[i] >= 0 ? "+" : "−") + Math.abs(G.va.v[i]).toFixed(2) + " · arousal " + G.va.a[i].toFixed(2);
      }
      x.fillStyle = muted; x.font = "10.5px " + FONT; x.fillText(text, pad + side / 2, pad + side + 13);
    }

    /* ----- loop and controls ----- */
    function ensure() { if (S.raf || S.dead || S.suspended) return; S.last = 0; S.raf = requestAnimationFrame(tick); }
    function tick(now) {
      S.raf = 0; if (S.dead || S.suspended || !root.clientWidth) return;
      S.raf = requestAnimationFrame(tick);
      const dt = S.last ? Math.min(0.1, (now - S.last) / 1000) : 0; S.last = now; S.T += dt;
      step(dt); if (S.mode === "3d") render3d(); else draw2d(); drawVA();
    }
    async function setMode(m) {
      if (m === "3d") {
        try { await loadThree(); if (S.dead) return; if (!S.t3) build3d(); } catch (e) { const b = $r('[data-m="3d"]'); if (b) { b.disabled = true; b.title = "3D is not available in this browser"; } m = "2d"; }
      }
      S.mode = m; c2.hidden = m === "3d"; h3.hidden = m !== "3d";
      root.querySelectorAll("[data-m]").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.m === m)));
      setNote(); ensure();
    }
    root.querySelectorAll("[data-m]").forEach(b => b.addEventListener("click", () => setMode(b.dataset.m)));
    if (opts.controls) {
      $r(".hplay").addEventListener("click", () => { if (!S.playing && S.i >= last() && S.u >= dur(S.i)) { S.playing = true; go(0); } else { S.playing = !S.playing; if (S.playing && S.u >= dur(S.i) && S.i < last()) go(S.i + 1); } sync(); });
      $r(".hrange").addEventListener("input", (e) => { S.playing = false; go(+e.target.value, true); });
    }
    const ro = new ResizeObserver(() => ensure()); ro.observe(root);
    sync(); ensure();
    if (opts.mode === "3d") setMode("3d");
    return {
      go: (i, settled, silent) => go(i, settled, silent), year: () => S.i, playing: () => S.playing,
      // the date the heart has reached, in decimal years: through the year while it beats, across the empty years while it rests
      time() { const y = G.labels[S.i]; if (S.rest) return y + 1 + (G.labels[S.i + 1] - y - 1) * clamp01(S.u / 2.4); return S.playing ? y + clamp01(S.u / dur(S.i)) : y + 1; },
      suspend() { S.suspended = true; if (S.raf) cancelAnimationFrame(S.raf); S.raf = 0; }, resume() { S.suspended = false; ensure(); },
      destroy() { S.dead = true; if (S.raf) cancelAnimationFrame(S.raf); ro.disconnect(); if (S.t3) { S.t3.renderer.dispose(); const ext = S.t3.renderer.getContext().getExtension("WEBGL_lose_context"); if (ext) ext.loseContext(); } root.innerHTML = ""; },
    };
  }
  window.NoeaHeart = { create };
})();
