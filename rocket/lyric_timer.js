// Temporary tool: tap out the timing of each lyric line while the video plays.
// Loaded by the "Time lyrics" button in viewer.html. Delete this file and that button when you are done.
(() => {
  const v = window.__v;
  if (!v || !v.ytCommand) { console.warn("Lyric timer: viewer hooks not found"); return; }
  const existing = document.getElementById("lyricTimer");
  if (existing) { existing.remove(); removeEventListener("keydown", window.__lyricTimerKeys, true); return; }  // button toggles the tool

  const TAG = /\[(\d+):(\d+(?:[.:]\d+)?)\]/g;
  const META = /^\[([a-z]+):(.*)\]$/i;
  const fmt = (t) => {
    const cs = Math.max(0, Math.round(t * 100)), m = Math.floor(cs / 6000), s = Math.floor((cs % 6000) / 100), c = cs % 100;
    return `[${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}.${String(c).padStart(2, "0")}]`;
  };

  // rows keep the file's own order: untouched lines (comments, metadata, blanks) and lyric lines.
  let rows = [], cursor = 0;
  const lyricRows = () => rows.filter((r) => r.kind === "lyric");
  function parse(text) {
    rows = text.split(/\r?\n/).map((raw) => {
      const line = raw.trim();
      if (!line || line.startsWith("#") || META.test(line)) return { kind: "raw", raw };
      const tags = [...line.matchAll(TAG)];
      if (!tags.length) return { kind: "lyric", text: line, t: 0, stamped: false };       // a bare line of text counts as a lyric
      const t = parseInt(tags[0][1], 10) * 60 + parseFloat(tags[0][2].replace(":", "."));
      return { kind: "lyric", text: line.replace(TAG, "").trim(), t, stamped: false };
    });
    while (rows.length && rows[rows.length - 1].kind === "raw" && !rows[rows.length - 1].raw.trim()) rows.pop();
    cursor = 0;
  }
  const serialize = () => rows.map((r) => (r.kind === "raw" ? r.raw : `${fmt(r.t)} ${r.text}`.trimEnd())).join("\n") + "\n";

  // Show only the lines stamped so far in the karaoke display, so you can watch your timing as you go.
  function preview() {
    v.setLyrics(lyricRows().filter((r) => r.stamped).map((r) => ({ t: r.t, text: r.text })).sort((a, b) => a.t - b.t));
  }

  // ---- UI ----
  const box = document.createElement("div"); box.id = "lyricTimer";
  box.innerHTML = `
    <style>
      #lyricTimer{position:fixed;left:12px;top:60px;width:380px;max-height:calc(100vh - 110px);z-index:20;display:flex;flex-direction:column;gap:8px;
        background:#151a21f2;border:1px solid #3c4552;border-radius:10px;padding:12px;font:13px system-ui,sans-serif;color:#e8eaed}
      #lyricTimer h2{font-size:14px;margin:0;display:flex;justify-content:space-between;align-items:center}
      #lyricTimer .clock{font:600 20px ui-monospace,Consolas,monospace}
      #lyricTimer .btns{display:flex;flex-wrap:wrap;gap:6px}
      #lyricTimer button{font:inherit;background:#2a313b;color:inherit;border:1px solid #3c4552;border-radius:6px;padding:5px 9px;cursor:pointer}
      #lyricTimer button.main{background:#2f6fde;border-color:#2f6fde;font-weight:600;flex:1 1 100%;padding:10px}
      #lyricTimer .list{overflow:auto;flex:1;min-height:120px;border:1px solid #2a313b;border-radius:6px}
      #lyricTimer .row{display:flex;gap:8px;padding:4px 8px;border-bottom:1px solid #20262e}
      #lyricTimer .row .t{font-family:ui-monospace,Consolas,monospace;color:#8b95a1;flex:none}
      #lyricTimer .row.done .t{color:#7fd28a}
      #lyricTimer .row.cur{background:#2f6fde40;outline:1px solid #2f6fde}
      #lyricTimer .row .x{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
      #lyricTimer .row .x:empty::before{content:"(gap: clears the display)";color:#8b95a1;font-style:italic}
      #lyricTimer .hint{color:#8b95a1;line-height:1.4}
      #lyricTimer .msg{min-height:1.2em;color:#7fd28a}
    </style>
    <h2><span>Lyric timer</span><span class="clock" data-k="clock">00:00.00</span></h2>
    <div class="btns">
      <button class="main" data-a="stamp">Start next line now (Space)</button>
      <button data-a="gap" title="Clear the display at this moment">Gap (G)</button>
      <button data-a="undo">Undo (Backspace)</button>
      <button data-a="back">Back 5s (&larr;)</button>
      <button data-a="pause">Play / pause (P)</button>
      <button data-a="restart">Restart</button>
    </div>
    <div class="list" data-k="list"></div>
    <div class="btns">
      <button data-a="save">Save over lyrics.lrc&hellip;</button>
      <button data-a="download">Download</button>
      <button data-a="copy">Copy</button>
      <button data-a="close">Close</button>
    </div>
    <div class="msg" data-k="msg"></div>
    <div class="hint">Press Space at the instant each highlighted line should appear. If keys stop working, click the scene once: clicks on the video send keys to YouTube instead.</div>`;
  document.body.appendChild(box);
  const $ = (k) => box.querySelector(`[data-k="${k}"]`);
  const say = (m) => { $("msg").textContent = m; };

  function render() {
    const list = $("list"); list.textContent = "";
    const ly = lyricRows();
    ly.forEach((r, i) => {
      const row = document.createElement("div"); row.className = "row" + (r.stamped ? " done" : "") + (i === cursor ? " cur" : "");
      const t = document.createElement("span"); t.className = "t"; t.textContent = r.stamped ? fmt(r.t) : "[--:--.--]";
      const x = document.createElement("span"); x.className = "x"; x.textContent = r.text;
      row.append(t, x); list.appendChild(row);
      if (i === cursor) row.scrollIntoView({ block: "center" });
    });
    box.querySelector('[data-a="stamp"]').textContent = cursor < ly.length ? "Start next line now (Space)" : "All lines timed";
  }

  const actions = {
    stamp() {
      const ly = lyricRows(); if (cursor >= ly.length) return say("All lines are timed. Save, or Undo to redo the last one.");
      ly[cursor].t = v.videoTime(); ly[cursor].stamped = true; cursor++; preview(); render(); say("");
    },
    gap() {
      const ly = lyricRows(), gapRow = { kind: "lyric", text: "", t: v.videoTime(), stamped: true, added: true };
      const at = cursor < ly.length ? rows.indexOf(ly[cursor]) : rows.length;
      rows.splice(at, 0, gapRow); cursor++; preview(); render();
    },
    undo() {
      const ly = lyricRows(); if (cursor === 0) return;
      cursor--; const r = ly[cursor];
      if (r.added) rows.splice(rows.indexOf(r), 1); else r.stamped = false;
      const prev = lyricRows().slice(0, cursor).filter((x) => x.stamped).pop();
      v.ytCommand("seekTo", [Math.max(0, (prev ? prev.t : 0) - 2), true]);     // jump back to just before the previous line
      preview(); render(); say("Undone. The video jumped back a little so you can retime it.");
    },
    back() { v.ytCommand("seekTo", [Math.max(0, v.videoTime() - 5), true]); },
    pause() { v.ytCommand(v.ytState && v.ytState() === 1 ? "pauseVideo" : "playVideo"); },
    restart() {
      rows = rows.filter((r) => !r.added); lyricRows().forEach((r) => { r.stamped = false; }); cursor = 0;
      v.ytCommand("seekTo", [0, true]); v.ytCommand("playVideo"); preview(); render(); say("Restarted from the beginning of the video.");
    },
    async save() {
      if (!window.showSaveFilePicker) return actions.download();
      try {
        const handle = await window.showSaveFilePicker({ suggestedName: "lyrics.lrc", types: [{ description: "Timed lyrics", accept: { "text/plain": [".lrc"] } }] });
        const w = await handle.createWritable(); await w.write(serialize()); await w.close();
        say("Saved. Reload the page to load it normally.");
      } catch (e) { if (e.name !== "AbortError") say("Could not save: " + e.message); }
    },
    download() {
      const a = document.createElement("a"); a.href = URL.createObjectURL(new Blob([serialize()], { type: "text/plain" })); a.download = "lyrics.lrc"; a.click();
      setTimeout(() => URL.revokeObjectURL(a.href), 2000); say("Downloaded. Move it over rocket/lyrics.lrc.");
    },
    async copy() { try { await navigator.clipboard.writeText(serialize()); say("Copied to the clipboard."); } catch { say("Copy was blocked by the browser; use Download."); } },
    close() { removeEventListener("keydown", window.__lyricTimerKeys, true); clearInterval(tick); box.remove(); },
  };
  box.addEventListener("click", (e) => { const a = e.target.closest("button")?.dataset.a; if (a) { actions[a](); e.target.blur(); } });

  window.__lyricTimerKeys = (e) => {
    if (e.target.matches?.("input, textarea, select")) return;
    const map = { " ": "stamp", Enter: "stamp", g: "gap", G: "gap", Backspace: "undo", ArrowLeft: "back", p: "pause", P: "pause" };
    const a = map[e.key]; if (!a) return;
    e.preventDefault(); e.stopPropagation(); if (!e.repeat) actions[a]();
  };
  addEventListener("keydown", window.__lyricTimerKeys, true);
  const tick = setInterval(() => { $("clock").textContent = fmt(v.videoTime()).slice(1, -1); }, 100);

  fetch(v.lyricsUrl + "?t=" + Date.now()).then((r) => { if (!r.ok) throw new Error("HTTP " + r.status); return r.text(); })
    .then((text) => { parse(text); preview(); render(); say(lyricRows().length + " lines loaded from " + v.lyricsUrl + "."); })
    .catch((e) => say("Could not load " + v.lyricsUrl + ": " + e.message));
})();
