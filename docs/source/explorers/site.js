/* The combined Noéa page: introduction, three chapters (the explorers in engine.js), documentation lightbox.
   Embeds in Webflow as one full-bleed iframe, the way the Hong Kong Heartbeat does. Optional: the page posts its height
   to the parent as { source: "noea", type: "height", height } if the host wants to size the iframe to fit. */
window.NOEA_SITE = true;
(function () {
  const CHAPTERS = [
    { key: "intro", label: "Introduction" },
    { key: "atmosphere", file: "rainfall.json", label: "Hong Kong", kicker: "Climate Pulse · Atmosphere", name: "Hong Kong rainfall", issues: [3, 4] },
    { key: "rivers", file: "river.json", label: "The Rhine and the Alps", kicker: "Climate Pulse · Rivers", name: "Rhine and alpine rivers", issues: [6] },
    { key: "laire", file: "hwi.json", label: "L'Aire, Geneva", kicker: "Human-Water Interface (HWI)", name: "L'Aire, Geneva", issues: [4, 5],
      missing: "L'Aire, Geneva uses validated data from the Office cantonal de l'eau (OCEau). It will appear here once it is released." },
  ];
  const CDN = "https://cdn.prod.website-files.com/63750b34ad85c65beae727c6/";
  const ISSUES = [
    { n: 1, title: "Water Persona Hong Kong", cover: "6ac24bda6859e64eea85831d_issue%201-p-800.png", pdf: "677b61c552207e793d019325_Water%20Persona%20(Part%20I%20-%20Atmosphere).pdf",
      text: "A collaboration between Meeting of Waters and the Hong Kong Observatory: a visual exploration of the relationship between water and climate." },
    { n: 2, title: "Hydro-affects", cover: "6ac24c1626a0b23fca2fbe27_issue%202-p-800.png", pdf: "677b5ea26b82b615546e6066_Water%20Persona%20%232%20Hydro-Affects.pdf",
      text: "The emotional and interconnected states of Earth's water systems, between objective hydrological data and anthropomorphic interpretation." },
    { n: 3, title: "Hong Kong Heartbeat", cover: "67f64c806c86f47cedbb8b0e_Water%20Persona%20%233%20Hong%20Kong%20Heartbeats.jpg", pdf: "67f78cb6ecb4d95ff81712d9_Water%20Persona%20%233%20Hong%20Kong%20Heartbeats.pdf",
      text: "The first prototype of Noéa: climate data read as an ECG, listening for the heartbeat of Hong Kong." },
    { n: 4, title: "Affective Climate", cover: "686c52c97dd9e0e7ece7b7b5_Screenshot%202025-07-07%20at%2023.36.47.png", pdf: "686c52b4586eb6ae2a90e949_Water%20Persona%20-%20Noe%CC%81a%20%234%20Issue.pdf",
      text: "The blueprint for training Noéa's affective AI, and a glimpse of a second prototype exploring proximate hydrological sensing." },
    { n: 5, title: "Technology of Care", cover: "68efa2dd5a99a2c7842550ff_issue%205.jpg", pdf: "68efa1f625eb81a5ebc2262f_issue%205.pdf",
      text: "The XR prototype of Noéa, its debut at the Zurich AI Festival, the WMO collaboration, and the ethics of empathy and technology." },
    { n: 6, title: "River Anatomy", cover: "69eb3cda90e18b66b3b7be96_issue%206.jpg", pdf: "69eb3ce1dca9f12ea6ba2847_Issue%206.pdf",
      text: "Built around the Rhine: 70 years of discharge records, a four-station profile, and four frameworks that read a river as a continuous body." },
  ];
  const LINKS = [
    ["Repository", "https://github.com/qintheory/noea", "The code behind the three prototypes, and the technical introduction."],
    ["Hong Kong Heartbeat", "https://www.meetingofwaters.org/hkheartbeat", "The original rainfall ECG from Issue 3."],
    ["Noéa on Meeting of Waters", "https://www.meetingofwaters.org/noea", "The project page, with every Issue."],
    ["Meeting of Waters on YouTube", "https://www.youtube.com/@meetingofwater", "Talks and films."],
  ];
  // The introduction video, then the four videos on the Noéa page of meetingofwaters.org (titles from YouTube, in the page's order).
  const VIDEOS = [
    { id: "JrARNkbITRQ", title: "Noéa: reading water as rhythm, memory and mood | A technical introduction", group: "intro", chapters: ["intro"] },
    { id: "8FXK6gwkYfc", title: "Zurich AI Festival 2025", group: "site", chapters: [] },
    { id: "ogkWj6PbVt8", title: "Noéa: Human-Water Interface (Teaser)", group: "site", chapters: ["laire"] },
    { id: "Nd1kLk_Cq7U", title: "Noéa Climate Pulse 2025", group: "site", chapters: ["atmosphere", "rivers"] },
    { id: "gAEiVycbZ5c", title: "World Water Day 2026 in Skopje", group: "site", chapters: [] },
  ];
  const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");

  let current = CHAPTERS[0], booted = false, token = 0;
  const cache = {};

  /* ---------- Noéa is always italic, in generated text too ---------- */
  const NOEA = /noéa/gi;
  function italicize(root) {
    const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, { acceptNode: (n) => { const p = n.parentNode; return (!p || /^(SCRIPT|STYLE|TITLE|TEXTAREA|I|EM)$/.test(p.nodeName) || !/noéa/i.test(n.nodeValue)) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT; } });
    const hits = []; while (w.nextNode()) hits.push(w.currentNode);
    hits.forEach((n) => { const t = n.nodeValue, frag = document.createDocumentFragment(); let last = 0, m; NOEA.lastIndex = 0;
      while ((m = NOEA.exec(t))) { frag.appendChild(document.createTextNode(t.slice(last, m.index))); const i = document.createElement("i"); i.textContent = m[0]; frag.appendChild(i); last = m.index + m[0].length; }
      frag.appendChild(document.createTextNode(t.slice(last))); n.parentNode.replaceChild(frag, n); });
  }
  let italicPending = false;
  new MutationObserver(() => { if (italicPending) return; italicPending = true; requestAnimationFrame(() => { italicPending = false; italicize(document.body); }); }).observe(document.body, { childList: true, subtree: true, characterData: true });

  /* ---------- navigation: the stage, three words, a way back ---------- */
  $("cards").innerHTML = CHAPTERS.slice(1).map(c => '<button type="button" class="word" data-ch="' + c.key + '"><span class="k">' + c.kicker + '</span><span class="w">' + c.label + '</span><span class="go" aria-hidden="true">→</span></button>').join("");
  document.querySelectorAll("[data-ch]").forEach(b => b.addEventListener("click", () => { location.hash = b.dataset.ch; }));
  window.addEventListener("hashchange", route);

  function route() {
    const key = (location.hash || "#intro").slice(1);
    show(CHAPTERS.find(c => c.key === key) || CHAPTERS[0]);
  }
  async function show(ch) {
    current = ch; const my = ++token;
    $("markArrow").hidden = ch.key === "intro";
    window.scrollTo(0, 0);
    if (ch.key === "intro") {
      $("sceneExplore").hidden = true; $("sceneIntro").hidden = false; startHero(); postHeight(); return;
    }
    stopHero(); $("sceneIntro").hidden = true; $("sceneExplore").hidden = false;
    $("explorer").hidden = true; $("missing").hidden = true; $("loading").hidden = false;
    try {
      if (!cache[ch.key]) { const r = await fetch("explore/data/" + ch.file); if (!r.ok) throw new Error(r.status); cache[ch.key] = await r.json(); }
    } catch (e) {
      if (my !== token) return;
      $("loading").hidden = true; $("missing").hidden = false;
      $("missing").innerHTML = '<h2>This chapter is not published yet</h2><p>' + esc(ch.missing || "The data for this chapter could not be loaded.") + '</p>';
      postHeight(); return;
    }
    if (my !== token) return;
    $("loading").hidden = true; $("explorer").hidden = false;
    if (!booted) { boot(); booted = true; }
    start(cache[ch.key]); renderRelated(ch); renderPager(ch); postHeight();
  }
  function renderRelated(ch) {
    let el = $("related");
    if (!el) { el = document.createElement("p"); el.id = "related"; el.className = "related"; $("deck").insertAdjacentElement("afterend", el); }
    const rel = (ch.issues || []).map(n => ISSUES.find(i => i.n === n));
    el.innerHTML = "Related reading: " + rel.map(i => '<button type="button" class="link" data-doc="issues">Issue 0' + i.n + ", " + esc(i.title) + "</button>").join(" · ") + ' · <button type="button" class="link" data-doc="video">Videos</button>';
    el.querySelectorAll("[data-doc]").forEach(b => b.addEventListener("click", () => openDocs(b.dataset.doc)));
  }
  function renderPager(ch) {
    const i = CHAPTERS.indexOf(ch), prev = CHAPTERS[i - 1], next = CHAPTERS[i + 1];
    $("pager").innerHTML = '<div class="side"><button class="solid" type="button" id="pagerDocs">Documentation</button></div><div class="side">' +
      (prev.key !== "intro" ? '<button class="btn" type="button" data-ch="' + prev.key + '">← ' + prev.label + '</button>' : "") +
      (next ? '<button class="btn" type="button" data-ch="' + next.key + '">' + next.label + ' →</button>' : '<button class="btn" type="button" data-ch="intro">Back to the start</button>') + '</div>';
    $("pager").querySelectorAll("[data-ch]").forEach(b => b.addEventListener("click", () => { location.hash = b.dataset.ch; }));
    $("pagerDocs").addEventListener("click", () => openDocs("issues"));
  }

  /* ---------- documentation lightbox ---------- */
  const dlg = $("docs"), TABS = [["intro", "Introduction"], ["video", "Videos"], ["issues", "Issues"], ["more", "Code and credits"]];
  let tab = "intro", opener = null, vid = null;
  function openDocs(which) {
    opener = document.activeElement; tab = which; vid = null; renderTabs(); renderPanel();
    if (!dlg.open) dlg.showModal();
  }
  function renderTabs() {
    $("docTabs").innerHTML = TABS.map(t => '<button type="button" role="tab" data-t="' + t[0] + '" aria-selected="' + (t[0] === tab) + '">' + t[1] + '</button>').join("");
    $("docTabs").querySelectorAll("button").forEach(b => b.addEventListener("click", () => { tab = b.dataset.t; renderTabs(); renderPanel(); }));
  }
  function renderPanel() {
    const body = $("docBody"); body.scrollTop = 0;
    if (tab === "intro") body.innerHTML = '<div class="panel fill"><iframe src="introduction.html" title="Noéa technical introduction" loading="lazy"></iframe></div>';
    else if (tab === "video") renderVideos(false);
    else if (tab === "issues") {
      const rel = current.issues || [];
      body.innerHTML = '<div class="panel"><div class="issues">' + ISSUES.map(i => '<article class="issue' + (rel.includes(i.n) ? ' is-related' : '') + '"><img class="cover" loading="lazy" alt="Cover of Issue ' + i.n + ', ' + esc(i.title) + '" src="' + CDN + i.cover + '">' +
        (rel.includes(i.n) ? '<span class="tag">Related to this chapter</span>' : '') + '<h3><small>Issue 0' + i.n + '</small>' + esc(i.title) + '</h3><p>' + esc(i.text) + '</p>' +
        '<a href="' + CDN + i.pdf + '" target="_blank" rel="noopener">Download</a></article>').join("") + '</div></div>';
    } else body.innerHTML = '<div class="panel"><ul class="linklist">' + LINKS.map(l => '<li><a href="' + l[1] + '" target="_blank" rel="noopener">' + esc(l[0]) + ' ↗</a><span>' + esc(l[2]) + '</span></li>').join("") +
      '<li><a href="introduction.html" target="_blank" rel="noopener">Technical introduction ↗</a><span>The deck that explains the method, in its own page (arrow keys to move, N for notes).</span></li></ul>' +
      '<p class="credits">Data: Hong Kong Observatory (rainfall, 1884–2025); Global Runoff Data Centre and the Swiss Federal Office for the Environment (rivers); Office cantonal de l\'eau, Geneva (the L\'Aire gauges). ' +
      'Method: an unsupervised model (PCA reconstruction error) learns what a typical year or day looks like for each record and scores how unusual each one is. No part of this has been tested with viewers yet.</p></div>';
  }
  function renderVideos(play) {
    if (!vid) vid = (VIDEOS.find(v => v.chapters.includes(current.key)) || VIDEOS[0]).id;
    const cur = VIDEOS.find(v => v.id === vid), item = (v) => '<li><button type="button" data-v="' + v.id + '"' + (v.id === vid ? ' aria-current="true"' : "") + '><img loading="lazy" alt="" src="https://i.ytimg.com/vi/' + v.id + '/mqdefault.jpg"><span class="t">' + esc(v.title) + '</span>' +
      (v.chapters.includes(current.key) && current.key !== "intro" ? '<span class="tag">Related to this chapter</span>' : "") + '</button></li>';
    $("docBody").innerHTML = '<div class="panel"><div class="vgrid"><div class="player"><div class="frame"><iframe src="https://www.youtube-nocookie.com/embed/' + cur.id + '?rel=0' + (play ? "&autoplay=1" : "") + '" title="' + esc(cur.title) + '" allow="accelerometer; autoplay; encrypted-media; picture-in-picture; fullscreen" allowfullscreen></iframe></div>' +
      '<h3>' + esc(cur.title) + '</h3></div>' +
      '<div><p class="vgroup">Introduction</p><ul class="vlist">' + VIDEOS.filter(v => v.group === "intro").map(item).join("") + '</ul><p class="vgroup">From the Noéa page</p><ul class="vlist">' + VIDEOS.filter(v => v.group === "site").map(item).join("") + '</ul></div></div></div>';
    $("docBody").querySelectorAll("[data-v]").forEach(b => b.addEventListener("click", () => { vid = b.dataset.v; renderVideos(true); }));
  }
  dlg.addEventListener("close", () => { $("docBody").innerHTML = ""; if (opener && opener.focus) opener.focus(); });
  dlg.addEventListener("click", (e) => { if (e.target === dlg) dlg.close(); });
  $("docClose").addEventListener("click", () => dlg.close());
  document.querySelectorAll("[data-doc]").forEach(b => b.addEventListener("click", () => openDocs(b.dataset.doc)));

  /* ---------- embedding ---------- */
  function postHeight() {
    if (window.parent === window) return;
    requestAnimationFrame(() => window.parent.postMessage({ source: "noea", type: "height", height: document.documentElement.scrollHeight }, "*"));
  }
  new ResizeObserver(postHeight).observe(document.body);

  /* ---------- the introduction: the Hong Kong heart, one beat per year ---------- */
  let hero = null;
  async function loadHero() {
    try {
      const d = await (await fetch("explore/data/rainfall.json")).json();
      hero = NoeaHeart.create($("hero"), d.groups[0], { controls: false, toggle: true, note: true, mode: "2d" });
      if (current.key !== "intro") hero.suspend();
    } catch (e) { /* the heart is optional */ }
  }
  function startHero() { if (hero) hero.resume(); }
  function stopHero() { if (hero) hero.suspend(); }

  loadHero(); route(); italicize(document.body);
})();
