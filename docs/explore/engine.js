let P = null;
const $ = (id) => document.getElementById(id);
const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
let st = null;
let G = null, F = null, isDay = false, D0 = 0;
function prepare() {
  isDay = P.kind === "day";
  P.groups.forEach((g) => {      // slot = horizontal position: the index for days, the year (from the first one) for years
    g._slot = isDay ? g.score.map((_, i) => i) : g.labels.map((l) => l - g.labels[0]);
    g._slots = isDay ? g.n : g.labels[g.n - 1] - g.labels[0] + 1;
    g._map = new Array(g._slots).fill(null); g._slot.forEach((s, i) => { g._map[s] = i; });
  });
  D0 = isDay ? (() => { const [y, m, d] = P.groups[0].start.split("-").map(Number); return Date.UTC(y, m - 1, d); })() : 0;
}

/* ---------- helpers ---------- */
const css = (n) => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
function hex(c) { c = c.replace("#", ""); if (c.length === 3) c = c.split("").map(x => x + x).join(""); return [0, 2, 4].map(i => parseInt(c.substr(i, 2), 16)); }
function ramp(t) {
  const s = [css("--c0"), css("--c1"), css("--c2"), css("--c3"), css("--c4")].map(hex);
  t = Math.max(0, Math.min(1, t)) * 4; const i = Math.min(3, Math.floor(t)), f = t - i;
  return "rgb(" + [0, 1, 2].map(k => Math.round(s[i][k] + (s[i + 1][k] - s[i][k]) * f)).join(",") + ")";
}
function dateOf(i) { return new Date(D0 + i * 864e5); }
function label(i, g) {
  if (!isDay) return String((g || G).labels[i]);
  return dateOf(i).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" });
}
function fmt(v, nd) {
  if (v === null || v === undefined) return "–";
  const a = Math.abs(v);
  if (nd !== undefined) return v.toFixed(nd);
  return a >= 1000 ? v.toLocaleString("en-GB", { maximumFractionDigits: 0 }) : a >= 100 ? v.toFixed(0) : a >= 10 ? v.toFixed(1) : a >= 1 ? v.toFixed(2) : v.toFixed(3);
}
const FONT = 'neue-frutiger-world, "Source Sans 3", Frutiger, "Helvetica Neue", Helvetica, Arial, sans-serif';
function setup(c) {
  const dpr = window.devicePixelRatio || 1, w = c.clientWidth, h = c.clientHeight;
  if (c.width !== Math.round(w * dpr) || c.height !== Math.round(h * dpr)) { c.width = Math.round(w * dpr); c.height = Math.round(h * dpr); }
  const x = c.getContext("2d"); x.setTransform(dpr, 0, 0, dpr, 0, 0); x.clearRect(0, 0, w, h);
  x.font = "12px " + FONT;
  return { x, w, h };
}
function validAt(i) { return G.score[i] !== null && G.score[i] !== undefined; }
function nearestValid(i) {
  if (validAt(i)) return i;
  for (let k = 1; k <= 6; k++) { if (i - k >= 0 && validAt(i - k)) return i - k; if (i + k < G.n && validAt(i + k)) return i + k; }
  return null;
}
const unusualText = (u, short) => u >= 0.9999 ? (short ? "its most unusual year" : "the most unusual year in its record") : (short ? "more unusual than " : "more unusual than ") + Math.min(99, Math.round(u * 100)) + "% of " + (short ? "years" : "its years");
const shade = (u) => P.kind === "river_year" ? Math.max(0, Math.min(1, (u - 0.55) / 0.45)) : u;          // rivers: below the middle of a station's years is ordinary (pale); navy is the top few percent
function colorOf(i) { const v = G.norm[i]; return v === null || v === undefined ? css("--pale") : ramp(shade(v)); }
function heldOutStart() { return isDay ? Math.round((Date.UTC(2023, 0, 1) - D0) / 864e5) : null; }

/* ---------- main chart ---------- */
let plot = null;    // geometry of the last draw, for hit-testing
function drawMain() {
  if (P.body) drawRiver();
  if (!$("main").clientWidth) return;
  if (P.kind === "river_year" && st.step === 1) return drawFramework();
  if (st.view === "ribbon") return drawRibbon();
  if (P.kind === "rain_year" && st.view === "line") return st.step === 0 ? drawRecordEcg() : drawEcg();
  const { x, w, h } = setup($("main"));
  const ink = css("--ink"), muted = css("--muted"), rule = css("--rule");
  const ml = 54, mr = 12, mt = 30, mb = 28, pw = w - ml - mr;
  const stepIdx = st.step, n = G.n, bw = pw / G._slots;          // year pages place a year by its date, so a gap in the record shows as a gap
  const px = (i) => ml + (G._slot[i] + 0.5) * bw;
  let top = mt, rainH = 0;
  if (isDay && stepIdx === 0) rainH = 56;
  const ph = h - top - mb - rainH, y0 = top + rainH;      // flow/score plot area
  plot = { ml, pw, n: G._slots, bw };
  x.textBaseline = "middle";

  // held-out band (day pages)
  if (isDay) {
    const hs = heldOutStart();
    x.fillStyle = css("--surface"); x.fillRect(ml + hs * bw, top, pw - hs * bw, h - top - mb);
    x.fillStyle = muted; x.textAlign = "left"; x.fillText("Held out: never seen by the model", ml + hs * bw + 6, 12);
  }
  // caption
  x.fillStyle = muted; x.textAlign = "left";
  const cap = stepIdx === 0 ? G.rec_label : stepIdx === 1 ? F[st.f].label + " · standard deviations from typical" : (isDay ? "Anomaly score (reconstruction error)" : "Anomaly score: 0 typical, 1 most unusual");
  x.fillText(cap, ml, 12);

  // y mapping per step
  let yv, ticks = [], zero = null;
  if (stepIdx === 0 && !isDay) {
    const mx = Math.max(...G.rec.filter(v => v !== null)) * 1.06;
    yv = (v) => y0 + ph - (v / mx) * ph;
    const stepv = niceStep(mx, 4); for (let t = 0; t <= mx; t += stepv) ticks.push(t);
  } else if (stepIdx === 0) {
    const vals = G.rec.filter(v => v !== null && v > 0);
    const lo = Math.pow(10, Math.floor(Math.log10(Math.min(...vals)))), hi = Math.pow(10, Math.ceil(Math.log10(Math.max(...vals))));
    yv = (v) => y0 + ph - (Math.log10(Math.max(v, lo)) - Math.log10(lo)) / (Math.log10(hi) - Math.log10(lo)) * ph;
    for (let t = lo; t <= hi * 1.001; t *= 10) ticks.push(t);
  } else if (stepIdx === 1) {
    const z = G.z[st.f].filter(v => v !== null);
    const lo = Math.min(-3, Math.floor(Math.min(...z))), hi = Math.max(3, Math.ceil(Math.max(...z)));
    yv = (v) => y0 + ph - ((v - lo) / (hi - lo)) * ph; zero = yv(0);
    const stepv = niceStep(hi - lo, 5); for (let t = Math.ceil(lo / stepv) * stepv; t <= hi; t += stepv) ticks.push(t);
  } else if (!isDay) {
    yv = (v) => y0 + ph - v * ph; [0, 0.25, 0.5, 0.75, 1].forEach(t => ticks.push(t));
  } else {
    const mx = G.smax * 1.05;
    yv = (v) => y0 + ph - (Math.min(v, mx) / mx) * ph;
    const stepv = niceStep(mx, 4); for (let t = 0; t <= mx; t += stepv) ticks.push(t);
  }
  // grid + y labels
  x.textAlign = "right"; x.strokeStyle = rule; x.lineWidth = 1;
  ticks.forEach(t => {
    const yy = Math.round(yv(t)) + 0.5; if (yy < y0 - 1 || yy > y0 + ph + 1) return;
    x.beginPath(); x.moveTo(ml, yy); x.lineTo(ml + pw, yy); x.stroke();
    x.fillStyle = muted; x.fillText(stepIdx === 0 && isDay ? fmt(t) : (t >= 100 || Number.isInteger(t) ? String(Math.round(t)) : fmt(t)), ml - 6, yy);
  });
  // x axis ticks
  x.textAlign = "center"; x.fillStyle = muted; x.strokeStyle = rule;
  if (isDay) {
    for (let yr = 2013; yr <= 2025; yr++) for (const mo of [0, 6]) {
      const i = Math.round((Date.UTC(yr, mo, 1) - D0) / 864e5); if (i < 0 || i >= n) continue;
      x.beginPath(); x.moveTo(px(i), h - mb); x.lineTo(px(i), h - mb + 4); x.stroke();
      if (mo === 0 && (yr % 2 === 1 || w > 700)) x.fillText(String(yr), px(i), h - mb + 16);
    }
  } else {
    const span = G.labels[n - 1] - G.labels[0], stepY = span > 120 ? 20 : span > 60 ? 10 : 10;
    G.labels.forEach((yr, i) => { if (yr % stepY === 0) { x.beginPath(); x.moveTo(px(i), h - mb); x.lineTo(px(i), h - mb + 4); x.stroke(); x.fillText(String(yr), px(i), h - mb + 16); } });
  }
  x.strokeStyle = muted; x.beginPath(); x.moveTo(ml, h - mb + 0.5); x.lineTo(ml + pw, h - mb + 0.5); x.stroke();

  // marks
  const baseY = stepIdx === 1 ? zero : y0 + ph;
  const barW = Math.max(1, Math.min(bw * 0.8, 14));
  if (stepIdx === 0 && isDay) {
    // rain strip (hangs from the top) then flow line
    const rmax = Math.max(...G.rain.filter(v => v !== null), 1);
    x.fillStyle = css("--c1");
    for (let i = 0; i < n; i++) { const v = G.rain[i]; if (v) { const hh = (v / rmax) * (rainH - 6); x.fillRect(px(i) - Math.max(0.5, bw / 2), top, Math.max(1, bw), hh); } }
    x.fillStyle = muted; x.textAlign = "right"; x.fillText("rain", ml - 6, top + 10);
    x.strokeStyle = css("--c3"); x.lineWidth = 1.2; x.beginPath(); let pen = false;
    for (let i = 0; i < n; i++) { const v = G.rec[i]; if (v === null || v <= 0) { pen = false; continue; } const yy = yv(v); if (!pen) { x.moveTo(px(i), yy); pen = true; } else x.lineTo(px(i), yy); }
    x.stroke();
  } else if (stepIdx === 0) {
    for (let i = 0; i < n; i++) { const v = G.rec[i]; if (v === null) continue; x.fillStyle = css("--c2"); const yy = yv(v); x.fillRect(px(i) - barW / 2, yy, barW, baseY - yy); }
  } else if (stepIdx === 1) {
    for (let i = 0; i < n; i++) {
      const v = G.z[st.f][i]; if (v === null) continue; const yy = yv(v);
      x.fillStyle = (!isDay && !G.fit[i]) ? css("--pale") : css("--c2");
      if (isDay) { x.fillRect(px(i) - Math.max(0.5, bw / 2), Math.min(yy, baseY), Math.max(1, bw), Math.abs(baseY - yy) || 1); }
      else x.fillRect(px(i) - barW / 2, Math.min(yy, baseY), barW, Math.abs(baseY - yy) || 1);
    }
  } else {
    for (let i = 0; i < n; i++) {
      const s = G.score[i]; if (s === null) continue;
      if (isDay) {
        x.fillStyle = colorOf(i); const yy = yv(s); const wid = Math.max(1, bw);
        x.fillRect(px(i) - wid / 2, yy, wid, y0 + ph - yy);
      } else if (G.fit[i]) {
        x.fillStyle = colorOf(i); const yy = yv(G.norm[i]); x.fillRect(px(i) - barW / 2, yy, barW, y0 + ph - yy);
      } else {
        const yy = yv(G.norm_all[i]); x.strokeStyle = css("--muted"); x.setLineDash([3, 2]); x.lineWidth = 1;
        x.strokeRect(px(i) - barW / 2 + 0.5, yy + 0.5, barW - 1, y0 + ph - yy); x.setLineDash([]);
      }
    }
    if (isDay) {            // training 95th percentile
      const yy = Math.round(yv(G.p95)) + 0.5; x.strokeStyle = ink; x.setLineDash([5, 4]); x.lineWidth = 1;
      x.beginPath(); x.moveTo(ml, yy); x.lineTo(ml + pw, yy); x.stroke(); x.setLineDash([]);
      x.fillStyle = ink; x.textAlign = "left"; x.fillText("95th percentile of the days it was fitted on", ml + 6, yy - 8);
    }
    // outline and label the top-ranked marks
    x.textAlign = "center"; x.fillStyle = css("--gold"); x.strokeStyle = css("--gold"); x.lineWidth = 1.6;
    G.top.slice(0, isDay ? 1 : 3).forEach((i) => {
      const yy = isDay ? yv(G.score[i]) : yv(G.norm[i]); const wid = isDay ? 6 : barW;
      if (!isDay) x.strokeRect(px(i) - barW / 2, yy, barW, y0 + ph - yy);
      else { x.beginPath(); x.arc(px(i), yy, 4, 0, 6.3); x.stroke(); }
      x.font = "700 12px " + FONT; x.fillText(label(i), Math.min(Math.max(px(i), ml + 28), ml + pw - 40), Math.max(yy - 9, 22));
      x.font = "12px " + FONT;
    });
  }
  // hover and selection
  const mark = (i, strong) => { if (i === null || i === undefined) return; x.strokeStyle = ink; x.globalAlpha = strong ? 0.9 : 0.35; x.lineWidth = strong ? 1.5 : 1;
    const bwid = Math.max(bw, 3); x.strokeRect(px(i) - bwid / 2 - 0.5, top, bwid + 1, h - top - mb); x.globalAlpha = 1; };
  mark(st.hover, false); mark(st.sel, true);
}
function niceStep(range, count) {
  const raw = range / count, p = Math.pow(10, Math.floor(Math.log10(raw))), f = raw / p;
  return (f < 1.5 ? 1 : f < 3.5 ? 2 : f < 7.5 ? 5 : 10) * p;
}


function rgba(c, a) { if (c.charAt(0) === "#") return "rgba(" + hex(c).join(",") + "," + a + ")"; return c.replace("rgb(", "rgba(").replace(")", "," + a + ")"); }

/* ---------- Hong Kong analysis: a conventional record, then ECG traces ---------- */
// The ECG idea of the Hong Kong Heartbeat (Issue 3): one Gaussian beat per year, at the date of the year's wettest day, so the
// spacing between beats is real time (the R-R interval). The baseline is kept flat, so a beat's height can be read as a value.
function tOf(i) {
  const m = /^(\d+)-(\d+)-(\d+)$/.exec(G.facts[i].peak_date), y = +m[1];
  return y + (Date.UTC(y, +m[2] - 1, +m[3]) - Date.UTC(y, 0, 1)) / (Date.UTC(y + 1, 0, 1) - Date.UTC(y, 0, 1));
}
// The record: the daily rainfall as an ECG that scrolls past as the heart beats (one year per beat), on ECG paper.
// Every spike is a real day's rain, drawn on a square-root scale. The tremor on the baseline is decoration, not data.
let recRaf = 0;
function recHash(n) { const s = Math.sin(n * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); }
function dailyAt(t0, t1) {                 // the wettest day between two decimal years, in mm; -1 where there is no record
  let best = -2;
  for (let t = t0; t <= t1 + 1e-9; t += 1 / 366) {
    const y = Math.floor(t), k = y - G.labels[0], idx = (k >= 0 && k < G._slots) ? G._map[k] : null;
    if (idx === null) { if (best < 0) best = -1; continue; }
    const v = G.daily[idx][Math.max(0, Math.min(365, Math.floor((t - y) * 366)))]; if (v < 0) { if (best < 0) best = -1; } else best = Math.max(best, v / 10);
  }
  return best < 0 ? -1 : best;
}
function drawRecordEcg() {
  const { x, w, h } = setup($("main")), ink = css("--ink"), muted = css("--muted"), rule = css("--rule"), c2 = css("--c2"), c3 = css("--c3");
  const ml = 54, mr = 12, mt = 30, mb = 30, pw = w - ml - mr, ph = h - mt - mb, WIN = w < 560 ? 3 : 4.5, ppy = pw / WIN, headX = ml + pw * 0.8;
  const Th = heart ? heart.time() : G.labels[st.sel] + 1, timeAt = (px) => Th + (px - headX) / ppy, xAt = (t) => headX + (t - Th) * ppy;
  const base = mt + ph - 8, top = mt + 6, SQ = (mm) => Math.sqrt(Math.min(mm, 500) / 500), Y = (mm) => base - SQ(mm) * (base - top);
  plot = { rec: { timeAt, ml, pw, headX } };
  x.textBaseline = "middle"; x.textAlign = "left"; x.fillStyle = muted; x.fillText("Daily rainfall (mm, square-root scale). The faint tremor is decoration.", ml, 12);
  // ECG paper: months and years, and the rainfall levels
  const tl = timeAt(ml), tr = timeAt(ml + pw);
  x.lineWidth = 1; for (let m = Math.floor(tl * 12); m <= Math.ceil(tr * 12); m++) { const xx = Math.round(xAt(m / 12)) + 0.5; if (xx < ml || xx > ml + pw) continue; x.strokeStyle = m % 12 === 0 ? muted : rule; x.globalAlpha = m % 12 === 0 ? 0.55 : 0.55; x.beginPath(); x.moveTo(xx, mt); x.lineTo(xx, mt + ph); x.stroke(); }
  x.globalAlpha = 1; x.textAlign = "right"; [10, 50, 100, 250, 500].forEach(mm => { const yy = Math.round(Y(mm)) + 0.5; x.strokeStyle = rule; x.beginPath(); x.moveTo(ml, yy); x.lineTo(ml + pw, yy); x.stroke(); x.fillStyle = muted; x.fillText(String(mm), ml - 6, yy); });
  x.textAlign = "center"; x.fillStyle = muted; for (let yr = Math.ceil(tl); yr <= tr; yr++) { const xx = xAt(yr); if (xx < ml + 10 || xx > ml + pw - 10) continue; x.fillText(String(yr), xx, mt + ph + 16); }
  x.strokeStyle = muted; x.beginPath(); x.moveTo(ml, Math.round(base) + 0.5); x.lineTo(ml + pw, Math.round(base) + 0.5); x.stroke();
  // the trace, left of the head, fading in; nothing yet on its right
  const grad = x.createLinearGradient(ml, 0, headX, 0); grad.addColorStop(0, rgba(c2, 0)); grad.addColorStop(0.5, rgba(c2, 0.6)); grad.addColorStop(1, c3);
  x.strokeStyle = grad; x.lineWidth = 1.5; x.lineJoin = "round"; x.beginPath(); let yHead = base, gapX = null;
  for (let px = ml; px <= headX; px++) {
    const t0 = timeAt(px - 0.5), t1 = timeAt(px + 0.5), mm = dailyAt(t0, t1), tm = (t0 + t1) / 2;
    const tremor = (1.2 * (recHash(Math.floor(tm * 366) * 3 + px * 0.01) - 0.5) * 2 + 1.7 * Math.sin(tm * 19.4) + 0.8 * Math.sin(tm * 71.7)) * 0.9;
    const yy = mm < 0 ? base : Y(mm) + tremor * (1 - SQ(mm) * 0.85); if (mm < 0 && gapX === null) gapX = px;
    if (px === ml) x.moveTo(px, yy); else x.lineTo(px, yy); yHead = yy;
  }
  x.stroke();
  x.strokeStyle = rule; x.setLineDash([2, 4]); x.beginPath(); x.moveTo(headX, base); x.lineTo(ml + pw, base); x.stroke(); x.setLineDash([]);
  // the head: a glowing point where the heart is now
  const gl = x.createRadialGradient(headX, yHead, 0, headX, yHead, 14); gl.addColorStop(0, rgba(c3, 0.5)); gl.addColorStop(1, rgba(c3, 0)); x.fillStyle = gl; x.beginPath(); x.arc(headX, yHead, 14, 0, 6.2832); x.fill();
  x.fillStyle = c3; x.beginPath(); x.arc(headX, yHead, 3, 0, 6.2832); x.fill();
  for (let s = 0; s < G.n - 1; s++) if (G.labels[s + 1] - G.labels[s] > 1) { const xx = xAt((G.labels[s] + 1 + G.labels[s + 1]) / 2); if (xx > ml + 40 && xx < headX - 20) { x.fillStyle = muted; x.textAlign = "center"; x.fillText("no record", xx, base - 12); } }
  if (st.hover !== null && plot.rec.hx !== undefined) { x.strokeStyle = ink; x.globalAlpha = 0.4; x.setLineDash([3, 3]); x.beginPath(); x.moveTo(plot.rec.hx, mt); x.lineTo(plot.rec.hx, mt + ph); x.stroke(); x.setLineDash([]); x.globalAlpha = 1; }
  if (heart && heart.playing() && !recRaf) recRaf = requestAnimationFrame(() => { recRaf = 0; if (heart && st.step === 0 && st.view === "line" && $("main").clientWidth) drawRecordEcg(); });
}
function recHit(px) {
  const q = plot && plot.rec; if (!q || px < q.ml || px > q.headX) return null;
  const t = q.timeAt(px), y = Math.floor(t), k = y - G.labels[0], i = (k >= 0 && k < G._slots) ? G._map[k] : null; q.hx = px; if (i === null) return null;
  const doy = Math.max(0, Math.min(365, Math.floor((t - y) * 366))), v = G.daily[i][doy], d = new Date(Date.UTC(y, 0, 1 + doy));
  return { g: st.g, i, tip: d.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" }) + " · " + (v < 0 ? "no record" : fmt(v / 10) + " mm") };
}
function drawEcg() {
  const { x, w, h } = setup($("main")), ink = css("--ink"), muted = css("--muted"), rule = css("--rule"), gold = css("--gold");
  const score = st.step === 2, ml = 54, mr = 12, mt = 30, mb = 30, pw = w - ml - mr, ph = h - mt - mb, n = G.n;
  const t0 = G.labels[0], t1 = G.labels[n - 1] + 1, X = (t) => ml + (t - t0) / (t1 - t0) * pw;
  const ts = G.labels.map((_, i) => tOf(i)), amp = (i) => score ? (G.fit[i] ? G.norm[i] : null) : G.z[st.f][i];
  let lo = 0, hi = 1.1; if (!score) { const m = Math.max(3, ...G.z[st.f].filter(v => v !== null).map(Math.abs)); lo = -m * 1.1; hi = m * 1.1; }
  const Y = (v) => mt + ph - (v - lo) / (hi - lo) * ph; plot = { ecg: { ts, X, amp } };
  x.textBaseline = "middle"; x.textAlign = "left"; x.fillStyle = muted;
  x.fillText(score ? "Anomaly score, 0 typical to 1 most unusual, one beat per year" : F[st.f].label + " · standard deviations from typical, one beat per year", ml, 12);
  const stepv = niceStep(hi - lo, 5); x.textAlign = "right"; x.strokeStyle = rule; x.lineWidth = 1;
  for (let t = Math.ceil(lo / stepv) * stepv; t <= hi + 1e-9; t += stepv) { const yy = Math.round(Y(t)) + 0.5; x.beginPath(); x.moveTo(ml, yy); x.lineTo(ml + pw, yy); x.stroke(); x.fillStyle = muted; x.fillText(Math.abs(t) < 1e-9 ? "0" : String(+t.toFixed(2)), ml - 6, yy); }
  x.textAlign = "center"; x.strokeStyle = muted; x.fillStyle = muted;
  for (let yr = Math.ceil(t0 / 20) * 20; yr <= t1; yr += 20) { const xx = X(yr); x.beginPath(); x.moveTo(xx, mt + ph); x.lineTo(xx, mt + ph + 4); x.stroke(); x.fillText(String(yr), xx, mt + ph + 16); }
  x.beginPath(); x.moveTo(ml, mt + ph + 0.5); x.lineTo(ml + pw, mt + ph + 0.5); x.stroke();
  x.strokeStyle = muted; x.lineWidth = 1; x.beginPath(); x.moveTo(ml, Math.round(Y(0)) + 0.5); x.lineTo(ml + pw, Math.round(Y(0)) + 0.5); x.stroke();
  // the trace: a narrow Gaussian beat per year, a small recovery wave after it, a small dip before
  const SUB = 2, N = Math.round(pw * SUB), val = new Float32Array(N + 1), s1 = Math.max(0.2, 1.4 * (t1 - t0) / pw);
  const wave = (dt) => Math.exp(-Math.pow(dt / s1, 2)) + 0.16 * Math.exp(-Math.pow((dt - 0.45) / 0.28, 2)) - 0.1 * Math.exp(-Math.pow((dt + 0.16) / 0.09, 2));
  for (let i = 0; i < n; i++) { const a = amp(i); if (a === null || a === undefined) continue;
    const g0 = Math.max(0, Math.floor((X(ts[i] - 0.4) - ml) * SUB)), g1 = Math.min(N, Math.ceil((X(ts[i] + 1.5) - ml) * SUB));
    for (let g = g0; g <= g1; g++) val[g] += a * wave(t0 + (g / SUB) / pw * (t1 - t0) - ts[i]); }
  x.lineWidth = 1.6; x.lineJoin = "round";
  for (let g = 1; g <= N; g++) { x.beginPath(); x.moveTo(ml + (g - 1) / SUB, Y(val[g - 1])); x.lineTo(ml + g / SUB, Y(val[g]));
    x.strokeStyle = score ? ramp(0.14 + 0.86 * Math.max(0, Math.min(1, val[g]))) : css("--c2"); x.stroke(); }
  for (let s = 0; s < n - 1; s++) if (G.labels[s + 1] - G.labels[s] > 1) { x.fillStyle = muted; x.textAlign = "center"; x.fillText("no record", X((G.labels[s] + 1 + G.labels[s + 1]) / 2), Y(0) - 12); }
  // the tallest beats, named
  const ranked = G.labels.map((_, i) => i).filter(i => amp(i) !== null && amp(i) !== undefined).sort((a, b) => Math.abs(amp(b)) - Math.abs(amp(a))).slice(0, 3);
  x.textAlign = "center"; x.font = "700 12px " + FONT; x.fillStyle = score ? gold : ink;
  ranked.forEach(i => { const a = amp(i); x.fillText(G.labels[i], X(ts[i]), a >= 0 ? Y(a) - 10 : Y(a) + 12); }); x.font = "12px " + FONT;
  const mark = (i, strong) => { if (i === null || i === undefined || amp(i) === null || amp(i) === undefined) return; const xx = X(ts[i]); x.strokeStyle = ink; x.globalAlpha = strong ? 0.8 : 0.35; x.lineWidth = 1; x.setLineDash([3, 3]); x.beginPath(); x.moveTo(xx, mt); x.lineTo(xx, mt + ph); x.stroke(); x.setLineDash([]); x.globalAlpha = 1;
    if (strong) { x.beginPath(); x.arc(xx, Y(amp(i)), 4.5, 0, 6.2832); x.fillStyle = css("--bg"); x.fill(); x.strokeStyle = ink; x.lineWidth = 1.6; x.stroke(); } };
  mark(st.hover, false); mark(st.sel, true);
}
function ecgHit(px) {
  const q = plot && plot.ecg; if (!q) return null; let best = null, bd = 14;
  for (let i = 0; i < G.n; i++) { const a = q.amp(i); if (a === null || a === undefined) continue; const d = Math.abs(q.X(q.ts[i]) - px); if (d < bd) { bd = d; best = i; } }
  return best === null ? null : { g: st.g, i: best };
}

/* ---------- ribbon (Issue 6): stations stacked flush on a shared spine, one column per year or week ---------- */
let RIB = null;
function gIdx(g, yr) { const s = yr - g.labels[0]; return (s >= 0 && s < g._slots) ? g._map[s] : null; }
function buildRibbon() {
  if (!isDay) {
    const W = P.windows && P.windows[st.win], Y0 = W && W[2] != null ? W[2] : Math.min(...P.groups.map(g => g.labels[0])), Y1 = W && W[3] != null ? W[3] : Math.max(...P.groups.map(g => g.labels[g.n - 1]));
    const stp = Y1 - Y0 > 120 ? 20 : 10, ticks = []; for (let yr = Math.ceil(Y0 / stp) * stp; yr <= Y1; yr += stp) ticks.push({ c: yr - Y0, t: String(yr) });
    return { ncol: Y1 - Y0 + 1, y0: Y0, y1: Y1, bands: P.bands, ticks, ref: 1960 - Y0, wide: 2.2,
      colOf: (g, i) => P.groups[g].labels[i] - Y0,
      cell: (g, c) => { const k = P.groups[g], i = gIdx(k, Y0 + c); if (i === null) return null;
        return { h: k.rec[i], i, v1: Math.min(1, Math.abs(k.z[st.f][i]) / 4), v2: k.fit[i] ? shade(k.norm[i]) : null }; } };
  }
  const ncol = Math.ceil(P.groups[0].n / 7);
  P.groups.forEach(k => {
    k._wk = []; const lg = [];
    for (let c = 0; c < ncol; c++) { const vals = []; let best = null;
      for (let d = c * 7; d < Math.min(k.n, c * 7 + 7); d++) { if (k.rec[d] > 0) vals.push(Math.log10(k.rec[d])); if (k.score[d] !== null && (best === null || k.score[d] > k.score[best])) best = d; }
      if (vals.length < 4 || best === null) { k._wk.push(null); continue; }
      vals.sort((a, b) => a - b); const med = vals[vals.length >> 1]; k._wk.push({ med, best }); lg.push(med); }
    lg.sort((a, b) => a - b); k._lo = lg[Math.floor(lg.length * 0.02)]; k._hi = lg[Math.floor(lg.length * 0.98)];
  });
  const ticks = []; for (let yr = 2013; yr <= 2025; yr += 2) ticks.push({ c: Math.floor(((Date.UTC(yr, 0, 1) - D0) / 864e5) / 7), t: String(yr) });
  return { ncol, bands: [{ name: "", layers: P.groups.map((_, k) => k) }], ticks, ref: Math.floor(ncol / 2), wide: 1.6,
    colOf: (g, i) => Math.floor(i / 7),
    cell: (g, c) => { const k = P.groups[g], w = k._wk[c]; if (!w) return null;
      const hn = Math.max(0, Math.min(1, (w.med - k._lo) / (k._hi - k._lo))); let m = 0;
      for (let d = c * 7; d < Math.min(k.n, c * 7 + 7); d++) { const z = k.z[st.f][d]; if (z !== null) m = Math.max(m, Math.abs(z)); }
      return { h: 0.35 + 1.25 * hn, i: w.best, v1: Math.min(1, m / 4), v2: k.norm[w.best] }; } };
}
function ribbonStack(q, b, c) {
  const real = b.layers.map(g => ({ g, cell: q.sp.cell(g, c) }));
  if (b.lanes) {          // separate streams: each gets its own lane and its own spine, so no continuous body is implied
    const lh = b.h / b.layers.length;
    return real.map((L, k) => L.cell ? { g: L.g, cell: L.cell, y0: b.top + lh * (k + 0.5) + L.cell.h * q.unit / 2, y1: b.top + lh * (k + 0.5) - L.cell.h * q.unit / 2 } : null).filter(Boolean);
  }
  const any = real.some(L => L.cell), cells = real.map(L => L.cell ? L : (b.fill && any ? { g: L.g, cell: { h: 1, i: null, v1: null, v2: null, ghost: true } } : null)).filter(Boolean);       // a station with no record that year keeps its share as a grey layer, so the river stays one continuous body
  let y = b.spine + cells.reduce((a, L) => a + L.cell.h * q.unit, 0) / 2;
  return cells.map(L => { const hh = L.cell.h * q.unit, o = { g: L.g, cell: L.cell, ghost: !!L.cell.ghost, y0: y, y1: y - hh }; y -= hh; return o; });
}
function cellColor(cell, sp) {
  if (cell.ghost) return "rgba(116,116,116,0.30)";          // no record: a neutral grey, clearly not a shade of the blue scale
  if (st.step === 0) { if (P.kind !== "river_year") return ramp(0.15 + 0.6 * Math.min(1, cell.h / sp.wide));
    const t = Math.max(0, Math.min(1, (cell.h - 0.35) / 1.3)); return ramp(t * t * (3 - 2 * t)); }          // rivers: a dry year (0.35 of the station's average) is the palest blue, a wet one (1.65 and over) deep navy, with an S-curve so the middle separates too
  if (st.step === 1) return ramp(0.08 + 0.92 * cell.v1);
  return cell.v2 === null ? css("--pale") : ramp(0.08 + 0.92 * cell.v2);
}
function drawRibbon() {
  const { x, w, h } = setup($("main")); RIB = RIB || buildRibbon(); const sp = RIB;
  const muted = css("--muted"), rule = css("--rule"), ink = css("--ink"), gold = css("--gold");
  const small = w < 560, ml = small ? 92 : 128, mr = 12, mt = 28, mb = 26, pw = w - ml - mr, bw = pw / sp.ncol;
  const nb = sp.bands.length, gap = nb > 1 ? 36 : 0, avail = h - mt - mb - 14 - gap, share = nb > 1 ? [0.52, 0.48] : [1];
  let yy = mt + 14; const bands = sp.bands.map((b, k) => { const bh = avail * share[k], o = Object.assign({}, b, { top: yy, h: bh, spine: yy + bh / 2 }); yy += bh + gap; return o; });
  const q = { ml, pw, bw, sp, bands, unit: Infinity }; plot = { rib: q }; q.labels = [];
  bands.forEach(b => { let mx = 0; for (let c = 0; c < sp.ncol; c++) { const cs = b.layers.map(g => sp.cell(g, c)), n = cs.filter(Boolean).length;
      mx = Math.max(mx, b.lanes ? Math.max(0, ...cs.map(k => k ? k.h : 0)) : cs.reduce((a, k) => a + (k ? k.h : 0), 0) + (b.fill && n ? (cs.length - n) : 0)); }
    q.unit = Math.min(q.unit, b.lanes ? (b.h / b.layers.length - 6) / mx : (b.h - 6) / mx); });
  if (P.kind === "river_year") { $("bk1").style.height = Math.max(3, Math.round(q.unit)) + "px"; $("bk2").style.height = Math.max(6, Math.round(2 * q.unit)) + "px"; }          // the key's sample bars, at the scale of the real ones
  x.textBaseline = "middle"; x.textAlign = "left"; x.fillStyle = muted;
  x.fillText(st.step === 0 ? (small ? "Height: " + (isDay ? "the week's median flow (log)" : "the year's mean flow, relative") : isDay ? "Height and shade: the week's median flow, log scale, within each gauge's own range" : "Height and colour: the year's mean flow relative to the station's own average year")
    : st.step === 1 ? F[st.f].label + (small ? "" : " · colour is distance from typical") : small ? (P.kind === "river_year" ? "Colour: how unusual · gold: most unusual" : "Colour: anomaly score · gold: highest") : P.kind === "river_year" ? "Colour is how unusual the year is for its station; gold outlines each station's most unusual year" : "Colour is the anomaly score; gold outlines the highest-scoring " + P.unit + " of each " + (isDay ? "gauge" : "station"), 4, 12);
  const wbar = Math.max(1.2, bw * 0.86);
  bands.forEach(b => {
    if (b.name) { x.fillStyle = muted; x.font = "700 12px " + FONT; x.textAlign = "left"; x.fillText(b.name, 4, b.top - 7); x.font = "12px " + FONT; }
    x.strokeStyle = rule; x.lineWidth = 1; x.beginPath();
    if (b.lanes) b.layers.forEach((g, k) => { const yy = Math.round(b.top + (b.h / b.layers.length) * (k + 0.5)) + 0.5; x.moveTo(ml, yy); x.lineTo(ml + pw, yy); }); else { x.moveTo(ml, Math.round(b.spine) + 0.5); x.lineTo(ml + pw, Math.round(b.spine) + 0.5); }
    x.stroke();
    for (let c = 0; c < sp.ncol; c++) ribbonStack(q, b, c).forEach(L => { x.fillStyle = cellColor(L.cell, sp); x.fillRect(ml + (c + 0.5) * bw - wbar / 2, L.y1 + 0.3, wbar, Math.max(0.5, L.y0 - L.y1 - 0.6)); });
    // station names at the left, at each layer's height in a reference column
    let rc = sp.ref; for (let k = 0; k < sp.ncol; k++) { const c = rc + (k % 2 ? 1 : -1) * Math.ceil(k / 2); if (c >= 0 && c < sp.ncol && ribbonStack(q, b, c).length === b.layers.length && ribbonStack(q, b, c).every(l => !l.ghost)) { rc = c; break; } }
    x.textAlign = "right"; x.font = (small ? "11px " : "12px ") + FONT;
    ribbonStack(q, b, rc).forEach(L => { const k = P.groups[L.g], yc = (L.y0 + L.y1) / 2, on = L.g === st.g || L.g === st.hoverG; x.fillStyle = on ? ink : muted; if (on) x.font = "700 " + (small ? "11px " : "12px ") + FONT; x.fillText(k.short || k.name, ml - 8, yc); x.font = (small ? "11px " : "12px ") + FONT; q.labels.push({ g: L.g, y0: yc - 11, y1: yc + 11 }); });
    x.font = "12px " + FONT;
  });
  // time axis
  x.strokeStyle = muted; x.beginPath(); x.moveTo(ml, h - mb + 0.5); x.lineTo(ml + pw, h - mb + 0.5); x.stroke();
  x.fillStyle = muted; x.textAlign = "center"; sp.ticks.forEach(t => { if (small && !isDay && (+t.t) % 40) return; const xx = ml + (t.c + 0.5) * bw; x.beginPath(); x.moveTo(xx, h - mb); x.lineTo(xx, h - mb + 4); x.stroke(); x.fillText(t.t, xx, h - mb + 16); });
  const outline = (g, i, col, lw, alpha) => { const c = sp.colOf(g, i); for (const b of bands) { const L = ribbonStack(q, b, c).find(l => l.g === g && !l.ghost); if (L) { x.globalAlpha = alpha; x.strokeStyle = col; x.lineWidth = lw;
    x.strokeRect(ml + (c + 0.5) * bw - Math.max(wbar, 3) / 2 - 1, L.y1 - 0.5, Math.max(wbar, 3) + 2, L.y0 - L.y1 + 1); x.globalAlpha = 1; return { b, c }; } } return null; };
  if (st.step === 2) { const used = []; x.textAlign = "center"; x.font = "700 12px " + FONT;
    P.groups.forEach((k, g) => { const i = P.windows ? topIn(k, 1)[0] : k.top[0]; if (i === undefined) return; const r = outline(g, i, gold, 1.8, 1); if (!r) return; const xx = ml + (r.c + 0.5) * bw, tx = label(i, k);
      const near = used.filter(u => u.b === r.b && Math.abs(u.x - xx) < 70); if (near.some(u => u.t === tx)) return;
      used.push({ b: r.b, x: xx, t: tx }); x.fillStyle = gold; x.fillText(tx, Math.min(Math.max(xx, ml + 30), ml + pw - 30), r.b.top - 7 - 14 * near.length); });
    x.font = "12px " + FONT; }
  if (st.hover !== null && st.hoverG !== null && !(st.hoverG === st.g && st.hover === st.sel)) outline(st.hoverG, st.hover, ink, 1.2, 0.6);
  outline(st.g, st.sel, ink, 2, 1);
}
/* ---------- river body (Issue 6, in miniature): the gauges as one branching river that flows down the page, coloured for one year ---------- */
function bodyLayout() { const ix = {}; P.groups.forEach((k, g) => { ix[k.id] = g; }); return { nodes: P.body.nodes.map(n => Object.assign({ g: ix[n.id] }, n)), edges: P.body.edges.map(e => [ix[e[0]], ix[e[1]]]) }; }
function topIn(k, n) { RIB = RIB || buildRibbon(); return k.norm.map((v, i) => [v, i]).filter(([v, i]) => v !== null && k.labels[i] >= RIB.y0 && k.labels[i] <= RIB.y1).sort((p, q) => q[0] - p[0]).slice(0, n).map(p => p[1]); }
let bodyPlot = null;
function drawRiver() {
  const cv = $("river"); if (!cv || !P.body || !cv.clientWidth) return;
  const { x, w, h } = setup(cv); RIB = RIB || buildRibbon(); const sp = RIB, T = bodyLayout();
  if (st.by === undefined) st.by = G.labels[st.sel];
  st.by = Math.max(sp.y0, Math.min(sp.y1, st.by));
  $("bodyRange").min = sp.y0; $("bodyRange").max = sp.y1; $("bodyRange").value = st.by; $("bodyYear").textContent = st.by;
  const muted = css("--muted"), ink = css("--ink"), gold = css("--gold"), small = w < 560;
  const ml = small ? 86 : 170, mr = small ? 86 : 170, mt = 60, mb = 34, pw = w - ml - mr, ph = h - mt - mb, mx = Math.max(...P.groups.map(k => k.mean));
  const pos = {}; T.nodes.forEach(n => { const k = P.groups[n.g]; pos[n.g] = { x: ml + n.x * pw, y: mt + n.y * ph, lw: 2 + 15 * Math.sqrt(k.mean / mx), cell: sp.cell(n.g, st.by - sp.y0), n, spine: n.x === 0.5 }; });
  const col = (p) => p.cell && p.cell.v2 !== null ? ramp(0.08 + 0.92 * p.cell.v2) : css("--pale");
  x.lineCap = "round";
  T.edges.forEach(([a, b], k) => { const A = pos[a], B = pos[b], ok = A.cell && B.cell && A.cell.v2 !== null && B.cell.v2 !== null, spine = A.spine && B.spine, w0 = spine ? A.lw : Math.max(1.6, A.lw * 0.45), w1 = spine ? B.lw : A.lw, S = bodyStrip(A, B, k, w0, w1), gr = x.createLinearGradient(A.x, A.y, B.x, B.y + 0.01);
    gr.addColorStop(0, col(A)); gr.addColorStop(1, col(B)); x.globalAlpha = ok ? 0.94 : 0.55; x.fillStyle = gr;
    x.beginPath(); S.L.forEach((p, i) => i ? x.lineTo(p.x, p.y) : x.moveTo(p.x, p.y)); for (let i = S.R.length - 1; i >= 0; i--) x.lineTo(S.R[i].x, S.R[i].y); x.closePath(); x.fill();
    if (!spine) { x.beginPath(); x.arc(A.x, A.y, w0 / 2, 0, 6.2832); x.fill(); }          // a source starts round
    x.globalAlpha = 1; });
  x.textBaseline = "middle"; const hits = [];
  T.nodes.forEach(n => { const p = pos[n.g], k = P.groups[n.g], i = p.cell ? p.cell.i : null, r = p.lw / 2 + 5, left = n.side === "l";
    x.fillStyle = col(p); x.strokeStyle = css("--bg"); x.lineWidth = 2.5; x.beginPath(); x.arc(p.x, p.y, r, 0, 6.2832); x.fill(); x.stroke();
    const ring = (rr, c, lw, al) => { x.globalAlpha = al; x.strokeStyle = c; x.lineWidth = lw; x.beginPath(); x.arc(p.x, p.y, rr, 0, 6.2832); x.stroke(); x.globalAlpha = 1; };
    if (i !== null && i === topIn(k, 1)[0]) ring(r + 4, gold, 2, 1);
    if (st.bhoverG === n.g && n.g !== st.g) ring(r + 4, ink, 1.2, 0.6);
    if (n.g === st.g) ring(r + 4, ink, 2, 1);
    const tx = p.x + (left ? -(r + 12) : r + 12); x.textAlign = left ? "right" : "left";
    x.font = (n.g === st.g ? "700 " : "400 ") + (small ? "11px " : "12px ") + FONT; x.fillStyle = n.g === st.g ? ink : muted; x.fillText(k.short || k.name, tx, p.y - 8);
    x.font = (small ? "10px " : "11px ") + FONT; x.fillStyle = muted;
    x.fillText(i === null ? "no record this year" : (k.fit[i] ? unusualText(k.norm[i], true) : "not fitted"), tx, p.y + 8);
    hits.push({ g: n.g, x: p.x, y: p.y, r, i }); });
  bodyPlot = hits;
  x.textAlign = "left"; x.fillStyle = ink; x.font = "400 22px " + css("--title"); x.fillText(String(st.by), 4, 24);
  x.font = "11px " + FONT; x.fillStyle = muted; x.fillText("Flows downstream, top to bottom. Not to scale: width is each station's usual flow.", 4, h - 12);
}
/* a branch from A down to B: it swings in a meander that is different for every branch and settles to vertical at both ends, widening as it flows */
function bodyPoint(A, B, k, t) {
  const dx = B.x - A.x, dy = B.y - A.y, spine = A.spine && B.spine, e = t * t * (3 - 2 * t), sg = k % 2 ? 1 : -1;
  const waves = spine ? 1.15 : 1.4 + 0.3 * (k % 3), amp = (spine ? 0.06 : 0.3 + 0.05 * (k % 3)) * Math.abs(dy), s2 = Math.pow(Math.sin(Math.PI * t), 2);
  return { x: A.x + dx * e + sg * amp * Math.sin(2 * Math.PI * waves * t + 0.7 * k) * s2, y: A.y + dy * t };
}
function bodyStrip(A, B, k, w0, w1) {
  const N = 72, L = [], R = [];
  for (let i = 0; i <= N; i++) { const t = i / N, p = bodyPoint(A, B, k, t), q = bodyPoint(A, B, k, Math.min(1, t + 0.004)), o = bodyPoint(A, B, k, Math.max(0, t - 0.004));
    let dx = q.x - o.x, dy = q.y - o.y; const d = Math.hypot(dx, dy) || 1; dx /= d; dy /= d; const e = t * t * (3 - 2 * t), hw = (w0 + (w1 - w0) * e) / 2;
    L.push({ x: p.x - dy * hw, y: p.y + dx * hw }); R.push({ x: p.x + dy * hw, y: p.y - dx * hw }); }
  return { L, R };
}
function bodyHit(px, py) {
  const q = bodyPlot; if (!q) return null; let best = null, bd = 1e9;
  q.forEach(n => { const d = Math.hypot(px - n.x, py - n.y); if (d < n.r + 8 && d < bd) { bd = d; best = n; } });
  if (!best) return null;
  const k = P.groups[best.g], nm = k.short || k.name;
  return best.i === null ? { g: best.g, i: null, tip: nm + " · no record in " + st.by } : { g: best.g, i: best.i, tip: nm + " · " + st.by + " · " + (k.fit[best.i] ? unusualText(k.norm[best.i]) + whyText(best.g, best.i) : "not fitted") };
}
let bodyTimer = 0;
function stopBody() { if (bodyTimer) { clearInterval(bodyTimer); bodyTimer = 0; } const b = $("bodyPlay"); if (b) b.textContent = "Play"; }
function setBodyYear(y) {
  RIB = RIB || buildRibbon(); st.by = Math.max(RIB.y0, Math.min(RIB.y1, y)); const i = gIdx(G, st.by);
  if (i !== null) select(i); else drawMain();
}
function setWindow(wi) {
  st.win = wi; RIB = null; stopBody(); RIB = buildRibbon();
  document.querySelectorAll("#views .chip").forEach((b, k) => b.setAttribute("aria-pressed", String(k === wi)));
  st.by = Math.max(RIB.y0, Math.min(RIB.y1, st.by === undefined ? G.labels[st.sel] : st.by));
  let i = gIdx(G, st.by); if (i === null || !G.fit[i]) i = topIn(G, 1)[0];
  setGroup(st.g, i === undefined ? 0 : i); st.by = G.labels[st.sel]; drawMain();
}
function playBody() {
  if (bodyTimer) return stopBody(); RIB = RIB || buildRibbon();
  if (st.by >= RIB.y1) setBodyYear(RIB.y0);
  $("bodyPlay").textContent = "Pause";
  bodyTimer = setInterval(() => { if (!$("river").clientWidth || st.by >= RIB.y1) return stopBody(); setBodyYear(st.by + 1); }, 380);
}
/* ---------- the four frameworks of Issue 6: one scientific graph for each of the six measures, at every station (rivers, Diagnostics step) ---------- */
const FRAMES = [
  { fw: "Pulse", graph: "the annual flow", note: "Pulse, the annual flow. In each panel a bar is a year's mean flow as a multiple of that station's average year. The grey band holds the middle 80% of the station's years, the dashed line is its typical year, and the dark bar is the chosen year." },
  { fw: "Pulse", graph: "the flood peak", note: "Pulse, the flood peak. A bar is the year's highest day as a multiple of the highest day of that station's typical year. The grey band holds the middle 80% of its years, the dashed line is the typical year, and the dark bar is the chosen year." },
  { fw: "Pulse", graph: "the low flow", note: "Pulse, the low flow. A bar is the year's lowest 7-day mean flow as a multiple of that station's typical low flow: how close the river came to running dry. The grey band holds the middle 80% of its years, and the dark bar is the chosen year." },
  { fw: "Personality", graph: "the flow duration curve", note: "Personality, the flow duration curve. For each share of the days, the flow that was exceeded that often, as a multiple of the station's average. A steep curve is a flashy, spiky river; a flat one is buffered by groundwater and lakes. The grey band holds the middle 80% of its years; the dark line is the chosen year." },
  { fw: "Memory", graph: "the recession curve", note: "Memory, the recession curve. How fast the flow falls back in the 40 days after the year's highest day, as a share of that peak, on a log scale. Slow means the river holds its water. The grey band holds the middle 80% of its years; the dark line is the chosen year." },
  { fw: "Breath", graph: "the seasonal cycle", note: "Breath, the seasonal cycle. The mean flow of each month as a multiple of the station's average. The seasonal shift is winter water against summer water compared with the typical year: snowmelt shows as a high summer. The grey band holds the middle 80% of its years; the dark line is the chosen year." },
];
const quantile = (a, p) => { if (!a.length) return null; const t = (a.length - 1) * p / 100, l = Math.floor(t), u = Math.ceil(t); return a[l] + (a[u] - a[l]) * (t - l); };
function frameLayout(w) { const n = P.bands[st.fg || 0].layers.length, cols = w < 560 ? 1 : 2, rows = Math.ceil(n / cols), plotH = 128, rowH = 18 + plotH + 24 + 14; return { cols, bl: 0, rows, plotH, rowH, top: 50, height: 50 + rows * rowH + 4 }; }
function drawFramework() {
  const { x, w } = setup($("main")); RIB = RIB || buildRibbon();
  const f = st.f, L = frameLayout(w), gap = 16, pw0 = (w - (L.cols - 1) * gap) / L.cols;
  const ink = css("--ink"), muted = css("--muted"), rule = css("--rule"), pale = css("--pale"), mid = css("--c1"), deep = css("--c4"), ok = (v) => v !== null && v !== undefined;
  x.textBaseline = "middle"; x.textAlign = "left"; x.fillStyle = ink; x.font = "700 13px " + FONT; x.fillText(FRAMES[f].fw + " · " + FRAMES[f].graph + " · " + (st.by !== undefined ? st.by : label(st.sel)), 4, 14);
  x.font = "12px " + FONT; x.fillStyle = muted; x.fillText("one panel per station · number: the year's value" + (F[f].unit ? " (" + F[f].unit + ")" : "") + " · band: the middle 80% of its years", 4, 33);
  const panels = [];
  const tick = (px, py, t, al) => { x.textAlign = al; x.fillText(t, px, py); };
  P.bands[st.fg || 0].layers.forEach((g, pi) => {
    const k = P.groups[g], c = pi % L.cols, rr = Math.floor(pi / L.cols), X0 = c * (pw0 + gap), Yb = L.top + rr * L.rowH;
    const Y0 = Yb + L.bl, sel = g === st.g, ml = 30, pw = pw0 - ml - 14, py0 = Y0 + 20, ph = L.plotH, py1 = py0 + ph;
    const fit = k.labels.map((_, j) => j).filter(j => k.fit[j]), yi = gIdx(k, st.by);
    x.font = (sel ? "700 " : "400 ") + "12px " + FONT; x.fillStyle = sel ? ink : muted; x.textAlign = "left"; x.fillText(k.short || k.name, X0 + 2, Y0 + 8);
    const val = yi !== null ? k.raw[f][yi] : null;
    if (ok(val)) { x.font = "11px " + FONT; x.fillStyle = muted; x.textAlign = "right"; x.fillText(fmt(val), X0 + pw0 - 12, Y0 + 8); }
    x.strokeStyle = sel ? ink : rule; x.lineWidth = sel ? 1.4 : 1; x.strokeRect(X0 + ml + 0.5, py0 + 0.5, pw, ph);
    x.font = "10px " + FONT; x.fillStyle = muted;
    const lineOf = (xs, ys, col, lw) => { x.strokeStyle = col; x.lineWidth = lw; x.beginPath(); let pen = false; ys.forEach((v, q) => { if (!ok(v)) { pen = false; return; } if (!pen) { x.moveTo(xs[q], v); pen = true; } else x.lineTo(xs[q], v); }); x.stroke(); };
    const bandOf = (xs, lo, hi) => { x.fillStyle = pale; x.globalAlpha = 0.6; x.beginPath(); lo.forEach((v, q) => q ? x.lineTo(xs[q], v) : x.moveTo(xs[q], v)); for (let q = hi.length - 1; q >= 0; q--) x.lineTo(xs[q], hi[q]); x.closePath(); x.fill(); x.globalAlpha = 1; x.fillStyle = muted; };
    const yTicks = (ticks, yf, ft) => { x.textAlign = "right"; x.strokeStyle = rule; x.lineWidth = 1; ticks.forEach(t => { const yy = Math.round(yf(t)) + 0.5; if (yy > py0 && yy < py1) { x.beginPath(); x.moveTo(X0 + ml, yy); x.lineTo(X0 + ml + pw, yy); x.stroke(); } x.fillText(ft(t), X0 + ml - 4, yf(t)); }); };
    const xTicks = (ticks, xf, ft) => { x.textAlign = "center"; ticks.forEach(t => x.fillText(ft(t), xf(t), py1 + 11)); };
    const cols = (arr, q) => fit.map(j => k[arr][j]).filter(Boolean).map(r => r[q]).filter(ok).sort((p, r) => p - r);
    let ser = null;
    if (!fit.length) { panels.push({ g, X0, Y0, w: pw0, h: 20 + ph + 24, ser }); return; }
    if (f <= 2) {
      const idx = fit.filter(j => k.labels[j] >= RIB.y0 && k.labels[j] <= RIB.y1), vs = idx.map(j => k.raw[f][j]).filter(ok), all = fit.map(j => k.raw[f][j]).filter(ok).sort((p, r) => p - r);
      const hi = Math.max(...(vs.length ? vs : [1]), quantile(all, 90)) * 1.1, bw = pw / Math.max(1, RIB.y1 - RIB.y0 + 1), xv = (j) => X0 + ml + (k.labels[j] - RIB.y0 + 0.5) * bw, yv = (v) => py1 - v / hi * ph, s = niceStep(hi, 3), tk = []; for (let t = 0; t <= hi; t += s) tk.push(t);
      yTicks(tk, yv, (t) => fmt(t, s < 1 ? 1 : 0));
      x.fillStyle = pale; x.globalAlpha = 0.6; x.fillRect(X0 + ml, yv(quantile(all, 90)), pw, yv(quantile(all, 10)) - yv(quantile(all, 90))); x.globalAlpha = 1;
      idx.forEach(j => { const v = k.raw[f][j]; if (!ok(v)) return; x.fillStyle = j === yi ? deep : mid; x.fillRect(xv(j) - Math.max(0.5, bw * 0.4), yv(v), Math.max(0.9, bw * 0.8), py1 - yv(v)); });
      x.strokeStyle = ink; x.setLineDash([3, 3]); x.lineWidth = 1; x.beginPath(); x.moveTo(X0 + ml, yv(quantile(all, 50))); x.lineTo(X0 + ml + pw, yv(quantile(all, 50))); x.stroke(); x.setLineDash([]);
      const stp = RIB.y1 - RIB.y0 > 120 ? 50 : 20, yt = []; for (let yr = Math.ceil(RIB.y0 / stp) * stp; yr <= RIB.y1; yr += stp) yt.push(yr);
      x.fillStyle = muted; xTicks(yt, (yr) => X0 + ml + (yr - RIB.y0 + 0.5) * bw, String);
      ser = { xs: idx.map(j => ({ j, x: xv(j) })), bw, x0: X0 + ml, pw };
    } else if (f === 3 || f === 4) {
      const key = f === 3 ? "fdc" : "recess", ps = f === 3 ? P.frame.fdc_p : P.frame.recess_lag, n_ = ps.length, p10 = ps.map((_, q) => quantile(cols(key, q), 10)), p50 = ps.map((_, q) => quantile(cols(key, q), 50)), p90 = ps.map((_, q) => quantile(cols(key, q), 90)), yr = yi !== null ? k[key][yi] : null;
      const okb = ps.map((_, q) => ok(p10[q]) && ok(p90[q])), lo0 = Math.min(...p10.filter(ok), ...((yr || []).filter(ok)), f === 4 ? 1 : 1e9), hi0 = Math.max(...p90.filter(ok), ...((yr || []).filter(ok)), 0);
      const lo = f === 3 ? lo0 * 0.85 : Math.max(0.02, lo0 * 0.8), hi = f === 3 ? hi0 * 1.15 : 1.1, ly = (v) => py1 - (Math.log(Math.max(v, lo)) - Math.log(lo)) / (Math.log(hi) - Math.log(lo)) * ph, xv = (v) => X0 + ml + v / (f === 3 ? 100 : 40) * pw, xs = ps.map(xv);
      yTicks((f === 3 ? [0.1, 0.2, 0.5, 1, 2, 5, 10] : [0.05, 0.1, 0.2, 0.5, 1]).filter(t => t >= lo && t <= hi), ly, (t) => fmt(t));
      xTicks(f === 3 ? [0, 50, 100] : [0, 20, 40], xv, (t) => f === 3 ? t + "%" : t + "d");
      bandOf(xs.filter((_, q) => okb[q]), p10.filter((_, q) => okb[q]).map(ly), p90.filter((_, q) => okb[q]).map(ly));
      lineOf(xs, p50.map(v => ok(v) ? ly(v) : null), mid, 1.3); if (yr) lineOf(xs, yr.map(v => ok(v) ? ly(v) : null), deep, 2.2);
    } else {
      const mo = yi !== null ? k.monthly[yi] : null, p10 = [...Array(12)].map((_, q) => quantile(cols("monthly", q), 10)), p50 = [...Array(12)].map((_, q) => quantile(cols("monthly", q), 50)), p90 = [...Array(12)].map((_, q) => quantile(cols("monthly", q), 90));
      const hi = Math.max(...p90.filter(ok), ...((mo || []).filter(ok))) * 1.12, yv = (v) => py1 - v / hi * ph, xv = (q) => X0 + ml + (q + 0.5) / 12 * pw, xs = [...Array(12)].map((_, q) => xv(q)), s = niceStep(hi, 3), tk = []; for (let t = 0; t <= hi; t += s) tk.push(t);
      yTicks(tk, yv, (t) => fmt(t, s < 1 ? 1 : 0)); xTicks([0, 3, 6, 9], xv, (q) => MONTHS[q]);
      bandOf(xs, p10.map(yv), p90.map(yv)); lineOf(xs, p50.map(yv), mid, 1.3); if (mo) lineOf(xs, mo.map(v => ok(v) ? yv(v) : null), deep, 2.2);
    }
    if (yi === null) { x.font = "italic 11px " + FONT; x.fillStyle = muted; x.textAlign = "center"; x.fillText("no record in " + st.by, X0 + ml + pw / 2, py0 + ph / 2); }
    if (st.hoverG === g && !sel) { x.strokeStyle = ink; x.globalAlpha = 0.5; x.lineWidth = 1.2; x.strokeRect(X0 + ml + 0.5, py0 + 0.5, pw, ph); x.globalAlpha = 1; }
    panels.push({ g, X0, Y0, w: pw0, h: 20 + ph + 24, ser });
  });
  plot = { frame: { panels } };
}
function frameHit(px, py) {
  const q = plot && plot.frame; if (!q) return null; const p = q.panels.find(a => px >= a.X0 && px <= a.X0 + a.w && py >= a.Y0 && py <= a.Y0 + a.h); if (!p) return null;
  const k = P.groups[p.g], f = st.f; let i = gIdx(k, st.by);
  if (p.ser) { let bd = 1e9; p.ser.xs.forEach(b => { const d = Math.abs(px - b.x); if (d < bd) { bd = d; i = b.j; } }); }
  if (i === null || i === undefined) return { g: p.g, i: null, tip: (k.short || k.name) + " · no record in " + st.by };
  const v = k.raw[f][i], z = k.z[f][i];
  return { g: p.g, i, tip: (k.short || k.name) + " · " + k.labels[i] + " · " + F[f].label + " " + fmt(v) + (F[f].unit ? " " + F[f].unit : "") + " (" + (z >= 0 ? "+" : "") + z.toFixed(1) + " sd from its typical year)" };
}
function kindOf(g, i) {          // the measure that departs most from the station's typical year, and which way (words come from the data)
  const k = P.groups[g]; if (!k.z || !k.fit[i]) return ""; let b = -1, bv = -1; k.z.forEach((c, j) => { if (c[i] !== null && Math.abs(c[i]) > bv) { bv = Math.abs(c[i]); b = j; } });
  return b < 0 || !F[b].words ? "" : F[b].words[k.z[b][i] >= 0 ? 1 : 0];
}
function flowCtx(g, i) {          // the year's flow in plain words, so a score is never read without it
  const v = P.groups[g].rec[i]; if (v === null || v === undefined) return "";
  return "mean flow " + v.toFixed(2) + " × its average" + (v < 0.9 ? " (below average)" : v > 1.1 ? " (above average)" : "");
}
function whyText(g, i) { const c = flowCtx(g, i), kd = kindOf(g, i); return (c ? "\n" + c : "") + (kd ? "\nmost unusual for: " + kd : ""); }
function stationAt(px, py) { const q = plot && plot.rib; if (!q || !q.labels || px < 0 || px > q.ml) return null; return q.labels.find(l => py >= l.y0 && py <= l.y1) || null; }
function stationInfo(g) {
  const k = P.groups[g];
  return [k.name, k.info, "Record " + k.labels[0] + "–" + k.labels[k.n - 1] + " · " + k.summary.n_fit + " fitted years", "Usual flow " + fmt(k.mean) + " m³/s (mean of the daily flow)"].filter(Boolean).join("\n");
}
function ribbonHit(px, py) {
  const q = plot && plot.rib; if (!q || px < q.ml || px > q.ml + q.pw) return null;
  const c = Math.floor((px - q.ml) / q.bw); if (c < 0 || c >= q.sp.ncol) return null;
  let best = null, bd = 1e9;
  q.bands.forEach(b => { if (py < b.top - 6 || py > b.top + b.h + 6) return;
    ribbonStack(q, b, c).forEach(L => { if (L.ghost) return; const d = (py >= L.y1 && py <= L.y0) ? 0 : Math.min(Math.abs(py - L.y0), Math.abs(py - L.y1)); if (d < bd) { bd = d; best = { g: L.g, i: L.cell.i }; } }); });
  return bd < 16 ? best : null;
}
function hitAt(e) {
  const r = $("main").getBoundingClientRect(), px = e.clientX - r.left, py = e.clientY - r.top;
  if (P.kind === "river_year" && st.step === 1) return frameHit(px, py);
  if (st.view === "ribbon") return ribbonHit(px, py);
  if (P.kind === "rain_year" && st.view === "line") return st.step > 0 ? ecgHit(px) : recHit(px);
  if (!plot || !plot.pw || px < plot.ml || px > plot.ml + plot.pw) return null;
  const slot = Math.min(plot.n - 1, Math.max(0, Math.floor((px - plot.ml) / plot.pw * plot.n)));
  for (let k = 0; k < 4; k++) for (const s of [slot - k, slot + k]) { const i = G._map[s]; if (i !== undefined && i !== null && validAt(i)) return { g: st.g, i }; }
  return null;
}
function tipText(hit) {
  if (hit.tip) return hit.tip;
  const g = P.groups[hit.g], i = hit.i;
  let t = (st.view === "ribbon" && P.groups.length > 1 ? (g.short || g.name) + " · " : "") + label(i, g) + " · ";
  if (st.step === 0) t += isDay ? fmt(g.rec[i]) + " m³/s" : fmt(g.rec[i]);
  else if (st.step === 1) t += fmt(g.raw[st.f][i]) + " (" + (g.z[st.f][i] >= 0 ? "+" : "") + g.z[st.f][i].toFixed(1) + "σ)";
  else t += isDay ? "score " + fmt(g.score[i], 1) : (g.fit[i] ? (P.kind === "river_year" ? unusualText(g.norm[i]) + whyText(hit.g, i) : "score " + g.norm[i].toFixed(2)) : "not fitted");
  if (isDay && st.view === "ribbon") t += " · highest day of the week";
  return t;
}
function viewNotes() { return {
  ribbon: [isDay ? "One column per week; each gauge is a layer, stacked flush on a shared spine as in the Issue 6 Rhine ribbon. Click a week to inspect its highest-scoring day." : "One column per year, as in the Issue 6 ribbon: each station is a layer stacked flush on a shared spine. The upper ribbon is the Rhine mainstem; below it each of the four alpine headwaters has a lane of its own.",
           "Colour shows how far each " + P.unit + " is from typical on the chosen diagnostic, in either direction.",
           isDay ? "Colour is the week's highest daily score. A single storm day shows up instead of being averaged away." : P.kind === "river_year" ? "Colour is how unusual the year is for its station: pale for an ordinary year, navy for the top few percent of that station's years. It says how far, not which way. Gold outlines each station's most unusual year." : "Colour is the anomaly score, scaled within each station. Gold outlines each station's highest-scoring year."]
}; }
function sizeCanvas() {
  const c = $("main"), w = c.parentElement.clientWidth;
  c.style.height = (P.kind === "river_year" && st.step === 1 ? frameLayout(w).height : st.view === "ribbon" ? (P.bands ? (w < 560 ? 430 : 480) : 320) : 320) + "px";
}
function setView(v) {
  st.view = v; st.hover = null; st.hoverG = null;
  document.querySelectorAll("#views .chip").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.v === v)));
  sizeCanvas(); setStep(st.step);
}
function selectHit(hit) {
  if (!hit || hit.i === null || hit.i === undefined) return;
  if (hit.g !== st.g) setGroup(hit.g, hit.i); else select(hit.i);
}


/* ---------- the heart (Hong Kong): see heart.js ---------- */
let heart = null;
function heartMount() {
  if (heart) { heart.destroy(); heart = null; }
  const box = $("heartBox"), on = P.kind === "rain_year" && window.NoeaHeart;
  box.hidden = !on; if (!on) { box.innerHTML = ""; return; }
  heart = NoeaHeart.create(box, G, { controls: true, toggle: true, note: true, mode: "2d", onYear: (i) => select(i) });
}

/* ---------- selected unit ---------- */
function misfit(i) {
  const r = G.res.map(c => c[i] || 0), t = r.reduce((a, b) => a + b, 0) || 1;
  return r.map(v => v / t);
}
function renderUnit() {
  const i = st.sel, sh = misfit(i);
  $("uTitle").textContent = label(i);
  $("swatch").style.background = colorOf(i);
  const note = (!isDay && !G.fit[i] && G.unit_fit_note) ? G.unit_fit_note[String(G.labels[i])] : null;
  let line, typical;
  if (isDay) {
    const pc = G.pct[i], held = i >= heldOutStart();
    line = "Score " + fmt(G.score[i], 1) + " · worse than " + (pc * 100).toFixed(pc > 0.99 ? 1 : 0) + "% of the days it was fitted on";
    typical = pc < 0.9;
    $("uNote").hidden = false;
    $("uNote").textContent = held ? "Held out: the model never saw this day when it was fitted."
      : dateOf(i).getUTCFullYear() < 2014 ? "2013 was not part of the fit: scored by inference." : "This day was part of the fitting years (2014–2022).";
  } else if (G.fit[i]) {
    line = P.kind === "river_year" ? (G.norm[i] >= 0.9999 ? "The most unusual year in this station's record" : "More unusual than " + Math.min(99, Math.round(G.norm[i] * 100)) + "% of this station's years") : "Anomaly score " + G.norm[i].toFixed(2) + ", on a scale from 0 (" + (P.groups.length > 1 ? "this station's" : "this record's") + " most typical year) to 1 (its most unusual)";
    typical = P.kind === "river_year" ? G.norm[i] < 0.6 : G.norm[i] < 0.2; $("uNote").hidden = true;
  } else { line = "Anomaly score " + fmt(G.score[i], 1) + " (raw), not on the 0–1 scale"; typical = false; $("uNote").hidden = false; $("uNote").textContent = note || "Scored, not fitted."; }
  $("uScore").textContent = line;
  const j = sh.indexOf(Math.max(...sh)), f = F[j];
  const zmax = G.z.map(c => Math.abs(c[i] || 0)), jz = zmax.indexOf(Math.max(...zmax));
  $("uWhy").textContent = P.kind === "river_year" && G.fit[i]
    ? (typical ? "Within the ordinary range for this station. The largest departure is " : "Most unusual for: ") + F[jz].words[G.z[jz][i] >= 0 ? 1 : 0] + ". " + F[jz].label + " is " + fmt(G.raw[jz][i]) + (F[jz].unit ? " " + F[jz].unit : "") + ", " + Math.abs(G.z[jz][i]).toFixed(1) + " standard deviations " + (G.z[jz][i] >= 0 ? "above" : "below") + " the station's typical year."
    : typical
    ? "This " + P.unit + " fits the typical pattern: no single diagnostic stands out."
    : "Largest misfit: " + f.label.toLowerCase() + ", " + Math.round(sh[j] * 100) + "% of the score. " + f.desc + " Here it is " + fmt(G.raw[j][i]) + (f.unit ? " " + f.unit : "") + ", " + Math.abs(G.z[j][i]).toFixed(1) + " standard deviations " + (G.z[j][i] >= 0 ? "above" : "below") + " typical.";
  const k = G.facts ? G.facts[i] : null;
  if (P.kind === "rain_year") {
    const d = new Date(k.peak_date + "T00:00:00Z").toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" });
    $("uFacts").textContent = "Peak day " + fmt(k.peak) + " mm on " + d + " · total " + fmt(k.total) + " mm · " + k.days + " days of data";
  } else if (P.kind === "river_year") {
    $("uFacts").textContent = "Mean " + fmt(k.mean) + " m³/s · highest day " + fmt(k.peak) + " · lowest day " + fmt(k.low) + " · " + k.days + " days of data";
  } else {
    $("uFacts").textContent = "Mean flow " + fmt(G.rec[i]) + " m³/s · rain " + fmt(G.rain[i], 1) + " mm that day";
  }
  $("shareHead").textContent = P.kind === "river_year" ? "Share of the departure" : "Share of misfit";
  $("rows").innerHTML = F.map((ff, jj) => {
    const z = G.z[jj][i], zp = Math.max(-3, Math.min(3, z)) / 3 * 50;
    const left = zp >= 0 ? 50 : 50 + zp, wid = Math.abs(zp);
    return '<tr class="row" tabindex="0" data-f="' + jj + '"' + (st.step === 1 && st.f === jj ? ' aria-selected="true"' : '') + '><td>' + ff.label + '<span class="sub">' + (ff.unit || "") + '</span></td>' +
      '<td class="num">' + fmt(G.raw[jj][i]) + '</td>' +
      '<td class="hide-sm"><div class="zbar" title="' + z.toFixed(1) + ' standard deviations"><span style="left:' + left + '%;width:' + wid + '%"></span></div></td>' +
      '<td class="hide-sm"><div class="mbar" title="' + Math.round(sh[jj] * 100) + '% of the score"><span style="width:' + Math.round(sh[jj] * 100) + '%"></span></div></td></tr>';
  }).join("");
  document.querySelectorAll("tr.row").forEach(tr => {
    const go = () => { st.f = +tr.dataset.f; setStep(1); };
    tr.onclick = go; tr.onkeydown = (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); go(); } };
  });
  drawDetail();
}
function drawDetail() {
  if (!$("detail").clientWidth) return;
  const i = st.sel, { x, w, h } = setup($("detail"));
  const muted = css("--muted"), rule = css("--rule"), ink = css("--ink");
  const ml = 44, mr = 8, mt = 8, mb = 24, pw = w - ml - mr; x.textBaseline = "middle";
  if (P.kind === "rain_year") {
    $("dTitle").textContent = "Rainfall each day of " + label(i) + " (mm)";
    const d = G.daily[i], mx = Math.max(...d, 10) / 10 * 1.08, ph = h - mt - mb, bw = pw / 366;
    const yv = (v) => mt + ph - (v / mx) * ph, s = niceStep(mx, 4);
    x.textAlign = "right"; x.strokeStyle = rule; x.fillStyle = muted;
    for (let t = 0; t <= mx; t += s) { const yy = Math.round(yv(t)) + .5; x.beginPath(); x.moveTo(ml, yy); x.lineTo(ml + pw, yy); x.stroke(); x.fillText(String(t), ml - 6, yy); }
    let pk = 0; d.forEach((v, k) => { if (v > d[pk]) pk = k; });
    d.forEach((v, k) => { const xx = ml + k * bw;
      if (v < 0) { x.fillStyle = rule; x.fillRect(xx, mt + ph - 3, Math.max(1, bw), 3); }
      else if (v > 0) { x.fillStyle = k === pk ? css("--c4") : css("--c2"); const yy = yv(v / 10); x.fillRect(xx, yy, Math.max(1, bw), mt + ph - yy); } });
    x.textAlign = "center"; x.fillStyle = muted;
    for (let m = 0; m < 12; m += 2) { const doy = Math.round(m * 30.5); x.fillText(MONTHS[m], ml + doy * bw + 8, h - 10); }
    x.fillStyle = ink; x.textAlign = pk > 250 ? "right" : "left"; x.fillText(fmt(d[pk] / 10) + " mm", ml + pk * bw + (pk > 250 ? -4 : 6), Math.max(yv(d[pk] / 10) + 6, mt + 8));
    $("detail").setAttribute("aria-label", "Daily rainfall in " + label(i));
  } else if (P.kind === "river_year") {
    $("dTitle").textContent = "Weekly flow in " + label(i) + ", against this station's typical year";
    const wk = G.weekly[i], med = G.weekly_median, all = wk.concat(med).filter(v => v !== null);
    const mx = Math.max(...all) * 1.08, ph = h - mt - mb, xv = (k) => ml + (k / 51) * pw, yv = (v) => mt + ph - (v / mx) * ph, s = niceStep(mx, 4);
    x.textAlign = "right"; x.strokeStyle = rule; x.fillStyle = muted;
    for (let t = 0; t <= mx; t += s) { const yy = Math.round(yv(t)) + .5; x.beginPath(); x.moveTo(ml, yy); x.lineTo(ml + pw, yy); x.stroke(); x.fillText(fmt(t, 1), ml - 6, yy); }
    const line = (arr, col, lw) => { x.strokeStyle = col; x.lineWidth = lw; x.beginPath(); let pen = false; arr.forEach((v, k) => { if (v === null) { pen = false; return; } if (!pen) { x.moveTo(xv(k), yv(v)); pen = true; } else x.lineTo(xv(k), yv(v)); }); x.stroke(); };
    line(med, css("--pale"), 3); line(wk, css("--c3"), 1.8);
    x.textAlign = "center"; x.fillStyle = muted; for (let m = 0; m < 12; m += 2) x.fillText(MONTHS[m], xv(m * 4.33) + 8, h - 10);
    $("detail").setAttribute("aria-label", "Weekly flow in " + label(i) + " against the typical year");
  } else {
    $("dTitle").textContent = "The 41 days around " + label(i) + ": flow (m³/s, log) and rain";
    const a = Math.max(0, i - 20), b = Math.min(G.n - 1, i + 20), rainH = 50, ph = h - mt - mb - rainH, y0 = mt + rainH;
    const fl = []; for (let k = a; k <= b; k++) if (G.rec[k] > 0) fl.push(G.rec[k]);
    const lo = Math.pow(10, Math.floor(Math.log10(Math.min(...fl)))), hi = Math.pow(10, Math.ceil(Math.log10(Math.max(...fl))));
    const xv = (k) => ml + ((k - a + 0.5) / (b - a + 1)) * pw, yv = (v) => y0 + ph - (Math.log10(v) - Math.log10(lo)) / (Math.log10(hi) - Math.log10(lo)) * ph;
    x.textAlign = "right"; x.strokeStyle = rule; x.fillStyle = muted;
    for (let t = lo; t <= hi * 1.001; t *= 10) { const yy = Math.round(yv(t)) + .5; x.beginPath(); x.moveTo(ml, yy); x.lineTo(ml + pw, yy); x.stroke(); x.fillText(fmt(t), ml - 6, yy); }
    const rmax = Math.max(...G.rain.slice(a, b + 1).map(v => v || 0), 10), bwid = pw / (b - a + 1);
    x.fillStyle = css("--c1"); for (let k = a; k <= b; k++) { const v = G.rain[k]; if (v) x.fillRect(xv(k) - bwid * .4, mt, bwid * .8, (v / rmax) * (rainH - 6)); }
    x.fillStyle = muted; x.textAlign = "left"; x.fillText("rain, up to " + fmt(rmax, 0) + " mm", ml + 4, mt + 8);
    for (let k = a; k <= b; k++) { if (!(G.rec[k] > 0)) continue; x.fillStyle = colorOf(k); x.beginPath(); x.arc(xv(k), yv(G.rec[k]), k === i ? 5 : 3, 0, 6.3); x.fill(); if (k === i) { x.strokeStyle = ink; x.lineWidth = 1.5; x.stroke(); } }
    x.textAlign = "center"; x.fillStyle = muted;
    [a, i, b].forEach((k, n) => x.fillText(dateOf(k).toLocaleDateString("en-GB", { day: "numeric", month: "short", timeZone: "UTC" }), Math.min(Math.max(xv(k), ml + 22), ml + pw - 22), h - 10));
    $("detail").setAttribute("aria-label", "Flow and rain around " + label(i));
  }
}

/* ---------- controls ---------- */
function setStep(s) {
  st.step = s; sizeCanvas();
  document.querySelectorAll(".step").forEach((b, k) => b.setAttribute("aria-selected", String(k === s)));
  $("stepText").textContent = P.steps[s][1];
  const rich = st.view !== "line";
  const yr = P.kind === "river_year" && st.view === "ribbon" && s !== 1;
  $("featBox").hidden = s !== 1; $("legend").hidden = !(s === 2 || (rich && s === 1 && P.kind !== "river_year") || yr); $("sumLine").hidden = s !== 2;
  $("lgA").textContent = yr && s === 0 ? "low flow" : P.kind === "river_year" && s === 2 ? "an ordinary year" : "typical"; $("lgB").textContent = yr && s === 0 ? "high flow" : s === 1 ? "far from typical" : P.kind === "river_year" ? "among its most unusual years" : "most unusual";
  $("barKey").hidden = !yr;
  if (P.kind === "river_year") $("groupBox").hidden = s !== 1;
  if (P.windows) $("viewBox").hidden = s === 1 && st.f > 2;          // the window only matters for the graphs drawn over the years
  if (yr) { $("bkText").textContent = s === 0 ? "Height and colour both show the year's mean flow, for visual effect: tall and navy for a high-flow year, short and pale for a low-flow year, measured against that station's own average. Grey: no record that year."
    : "Bar height: the year's mean flow as a multiple of that station's own average, so 1.0 is an average year. " + (s === 1 ? "Colour: how far the year is from typical on the chosen diagnostic." : "Colour: how unusual the year is for this station, from pale (an ordinary year) to navy (among its most unusual, the top few percent). It does not say which way, so hover a bar to see the year's flow and what makes it unusual. Gold outline: the station's most unusual year.") + " Grey: no record that year.";
    document.querySelector("#barKey .bkscale").style.display = s === 0 ? "none" : ""; }
  $("viewNote").textContent = P.kind === "river_year" && s === 1 ? FRAMES[st.f].note : rich ? viewNotes()[st.view][s] + (st.view === "ribbon" && P.bands && P.bands.some(b => b.fill) ? " The Rhine keeps its full thickness as one continuous river; the alpine streams are separate lanes, not one body." : "") : "";
  const sm = G.summary, vr = Math.round(sm.variance * 100) + "%";
  $("sumLine").textContent = isDay
    ? sm.components + " components keep " + vr + " of the variance in " + sm.n_fit.toLocaleString("en-GB") + " fitting days. Of the " + sm.n_test.toLocaleString("en-GB") + " held-out days, " + (sm.test_above_p95 * 100).toFixed(1) + "% score above the training 95th percentile (5% expected if nothing had changed) and " + (sm.test_above_p99 * 100).toFixed(1) + "% above the 99th (1% expected)."
    : sm.components + " components keep " + vr + " of the variance in the " + sm.n_fit + " fitted years" + (P.groups.length > 1 ? " of this station." : ".");
  document.querySelectorAll("#feats .chip").forEach((b, k) => b.setAttribute("aria-pressed", String(k === st.f)));
  $("main").setAttribute("aria-label", P.steps[s][0] + ": " + P.steps[s][1]);
  $("hint").textContent = P.kind === "river_year" && s === 1 ? "Pick a measure above. Choose the stations above. Click a panel to select that station" + (st.f <= 2 ? ", or a bar to choose that year" : "") + "; the year also follows the slider on the river." : (P.kind === "river_year" ? "Hover a station name for its details; click it to choose that station. " : "") + "Click a " + (st.view === "ring" ? "filament" : st.view === "ribbon" ? (isDay ? "week" : "layer") : P.unit) + " to inspect it. Arrow keys step by one " + P.unit + (isDay ? ", Shift for a month." : ", Shift for ten.");
  drawMain(); renderUnit();
}
function markFrameChips() { document.querySelectorAll("#groups .chip").forEach((b, k) => b.setAttribute("aria-pressed", String(P.kind === "river_year" ? k === (st.fg || 0) : false))); }
function setFrameGroup(k) {
  st.fg = k; markFrameChips();
  if (!P.bands[k].layers.includes(st.g)) { const g2 = P.bands[k].layers[0]; let i = gIdx(P.groups[g2], st.by); if (i === null || !P.groups[g2].fit[i]) i = topIn(P.groups[g2], 1)[0]; setGroup(g2, i === undefined ? 0 : i); }
  else { sizeCanvas(); drawMain(); }
}
function setGroup(g, keep) {
  st.g = g; G = P.groups[g]; st.hover = null; st.hoverG = null; st.sel = keep !== undefined ? keep : G.top[0];
  $("gNote").hidden = !G.note; $("gNote").textContent = G.note || "";
  if (P.kind === "river_year") { const bi = P.bands.findIndex(b => b.layers.includes(g)); if (bi >= 0) st.fg = bi; markFrameChips(); st.by = G.labels[st.sel]; }
  else document.querySelectorAll("#groups .chip").forEach((b, k) => b.setAttribute("aria-pressed", String(k === g)));
  renderFlagged(); setStep(st.step);
}
function select(i) { if (i === null || i === undefined) return; st.sel = i; if (P.kind === "river_year") st.by = G.labels[i]; if (heart && heart.year() !== i) heart.go(i, true, true); drawMain(); renderUnit(); }
function renderFlagged() {
  $("flagLabel").textContent = isDay ? "Highest-scoring days in the held-out years (2023–2025)" : "Highest-scoring " + P.unit_plural + (P.windows ? " in this window" : " in this record");
  $("flagged").innerHTML = (P.windows ? topIn(G, 6) : G.top).map(i => '<button class="chip" data-i="' + i + '">' + label(i) + '</button>').join("");
  document.querySelectorAll("#flagged .chip").forEach(b => b.onclick = () => select(+b.dataset.i));
}
function start(data) {
  P = data; prepare();
  st = { g: 0, step: 0, f: 0, sel: 0, win: 0, fg: 0, hover: null, hoverG: null, bhoverG: null, view: (P.views || [["line"]])[0][0] };
  G = P.groups[0]; F = P.features; RIB = null; plot = null; stopBody(); bodyPlot = null; $("riverBox").hidden = !P.body; if (P.body) $("riverNote").textContent = P.body.note || ""; heartMount();
  if (!window.NOEA_SITE) document.title = P.title;
  $("eyebrow").textContent = P.eyebrow; $("title").textContent = P.title; $("deck").textContent = P.deck;
  $("steps").innerHTML = P.steps.map((s, k) => '<button class="step" role="tab" data-k="' + k + '"><b>' + (k + 1) + '</b>' + s[0] + '</button>').join("");
  document.querySelectorAll(".step").forEach(b => b.onclick = () => setStep(+b.dataset.k));
  $("feats").innerHTML = F.map((f, k) => '<button class="chip" title="' + f.desc.replace(/"/g, "&quot;") + '" data-k="' + k + '">' + f.label + '</button>').join("");
  document.querySelectorAll("#feats .chip").forEach(b => b.onclick = () => { st.f = +b.dataset.k; setStep(1); });
  $("groupBox").hidden = P.groups.length <= 1 || P.kind === "river_year";
  if (P.groups.length > 1) {
    $("groupBox").hidden = P.kind === "river_year"; $("groupLabel").textContent = isDay ? "Gauge" : "Station";
    if (P.kind === "river_year") { $("groupLabel").textContent = "Stations"; $("groups").innerHTML = P.bands.map((b, k) => '<button class="chip" data-k="' + k + '">' + b.name + '</button>').join("");
      document.querySelectorAll("#groups .chip").forEach(b => b.onclick = () => setFrameGroup(+b.dataset.k)); }
    else { $("groups").innerHTML = P.groups.map((g, k) => '<button class="chip" data-k="' + k + '">' + g.name + '</button>').join("");
      document.querySelectorAll("#groups .chip").forEach(b => b.onclick = () => setGroup(+b.dataset.k)); }
  }
  $("limits").innerHTML = P.limits.map(t => "<li>" + t + "</li>").join("");
  $("method").textContent = "Method: " + P.method;
  $("source").textContent = "Data: " + P.source;
  const VIEWS = P.views || [["line", "Timeline"]];
  $("viewBox").hidden = VIEWS.length <= 1 && !P.windows;
  if (P.windows) { $("viewBox").hidden = false; $("viewLabel").textContent = "Window";
    $("views").innerHTML = P.windows.map((v, k) => '<button class="chip" data-v="' + k + '" aria-pressed="' + (k === 0) + '">' + v[1] + '</button>').join("");
    document.querySelectorAll("#views .chip").forEach((b, k) => b.onclick = () => setWindow(k)); }
  else if (VIEWS.length > 1) { $("viewLabel").textContent = "View"; $("viewBox").hidden = false;
    $("views").innerHTML = VIEWS.map(v => '<button class="chip" data-v="' + v[0] + '">' + v[1] + '</button>').join("");
    document.querySelectorAll("#views .chip").forEach(b => b.onclick = () => setView(b.dataset.v)); }
  $("bodyPlay").onclick = playBody; $("bodyRange").oninput = (e) => { stopBody(); setBodyYear(+e.target.value); };
  sizeCanvas();
  setGroup(0);
}
function boot() {
  if (document.fonts && document.fonts.addEventListener) document.fonts.addEventListener("loadingdone", () => { if (P && $("main").clientWidth) { drawMain(); drawDetail(); } });
  const c = $("main"), tip = $("tip");
  c.addEventListener("pointermove", (e) => {
    const r0 = c.getBoundingClientRect(), lab = st.view === "ribbon" && P.kind === "river_year" ? stationAt(e.clientX - r0.left, e.clientY - r0.top) : null;
    if (lab) { st.hover = null; st.hoverG = lab.g; drawMain(); c.style.cursor = "pointer"; tip.style.whiteSpace = "pre"; tip.textContent = stationInfo(lab.g); tip.hidden = false;
      tip.style.left = Math.max(e.clientX - r0.left + 150, 150) + "px"; tip.style.top = Math.max(e.clientY - r0.top - 10, 24) + "px"; return; }
    c.style.cursor = ""; tip.style.whiteSpace = "pre";
    const hit = hitAt(e); st.hover = hit ? hit.i : null; st.hoverG = hit ? hit.g : null; drawMain();
    if (!hit) { tip.hidden = true; return; }
    const r = c.getBoundingClientRect();
    tip.textContent = tipText(hit); tip.hidden = false;
    tip.style.left = Math.min(Math.max(e.clientX - r.left, 70), r.width - 70) + "px"; tip.style.top = Math.max(e.clientY - r.top - 10, 24) + "px";
  });
  c.addEventListener("pointerleave", () => { st.hover = null; st.hoverG = null; tip.hidden = true; tip.style.whiteSpace = ""; drawMain(); });
  c.addEventListener("click", (e) => {
    const r = c.getBoundingClientRect(), lab = st.view === "ribbon" && P.kind === "river_year" ? stationAt(e.clientX - r.left, e.clientY - r.top) : null;
    if (lab) { let i = gIdx(P.groups[lab.g], st.by); if (i === null || !P.groups[lab.g].fit[i]) i = topIn(P.groups[lab.g], 1)[0]; if (i !== undefined) setGroup(lab.g, i); return; }
    selectHit(hitAt(e)); });
  const rc = $("river"), rtip = $("riverTip");
  rc.addEventListener("pointermove", (e) => { if (!P || !P.body) return; const r = rc.getBoundingClientRect(), hit = bodyHit(e.clientX - r.left, e.clientY - r.top); st.bhoverG = hit ? hit.g : null; drawRiver();
    if (!hit) { rtip.hidden = true; return; } rtip.style.whiteSpace = "pre"; rtip.textContent = hit.tip; rtip.hidden = false; rtip.style.left = Math.min(Math.max(e.clientX - r.left, 70), r.width - 70) + "px"; rtip.style.top = Math.max(e.clientY - r.top - 10, 24) + "px"; });
  rc.addEventListener("pointerleave", () => { st.bhoverG = null; rtip.hidden = true; drawRiver(); });
  rc.addEventListener("click", (e) => { const r = rc.getBoundingClientRect(); selectHit(bodyHit(e.clientX - r.left, e.clientY - r.top)); });
  rc.addEventListener("keydown", (e) => { const k = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0; if (!k) return; e.preventDefault(); stopBody(); setBodyYear(st.by + k * (e.shiftKey ? 10 : 1)); });
  c.addEventListener("keydown", (e) => {
    const k = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0; if (!k) return; e.preventDefault();
    let i = st.sel + k * (e.shiftKey ? (isDay ? 30 : 10) : 1); i = Math.min(G.n - 1, Math.max(0, i));
    const v = nearestValid(i); if (v !== null) select(v);
  });
  new ResizeObserver(() => { if (!$("main").clientWidth || !P) return; sizeCanvas(); drawMain(); drawDetail(); }).observe(document.querySelector(".wrap"));
}
