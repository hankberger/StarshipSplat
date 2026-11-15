"""One-off edit: draw the title and lyrics inside the 3D scene (so the ship and tower can pass in front of them too),
and push the overlay out past the tower when the tower is on its side of the ship."""
import io
p = 'viewer.html'
s = io.open(p, encoding='utf-8', newline='').read()
nl = '\r\n' if '\r\n' in s else '\n'


def rep(a, b, count=1):
    global s
    a = a.replace('\n', nl); b = b.replace('\n', nl)
    assert a in s, 'not found: ' + a[:80]
    s = s.replace(a, b) if count == 0 else s.replace(a, b, count)


def cut(start, end, new):
    """Replace everything from the start marker up to (not including) the end marker."""
    global s
    i = s.index(start); j = s.index(end, i)
    s = s[:i] + new.replace('\n', nl) + s[j:]


# ---- the front CSS layer is no longer used -------------------------------------------------
rep('cssFront.setSize(innerWidth, innerHeight); document.body.appendChild(cssFront.domElement);',
    'cssFront.setSize(innerWidth, innerHeight);   // (unused now: the title and lyrics are drawn in the 3D scene)')
rep('renderWithOcclusion(); css.render(backScene, camera); cssFront.render(frontScene, camera); });',
    'renderWithOcclusion(); css.render(backScene, camera); });')

# ---- lyrics: same behaviour as before, but drawn on a canvas that is shown as a texture in the scene ---------
cut('// The old line clears quickly first;', 'function updateLyrics() {', '''// Text in the scene. The title and the lyrics are painted onto small canvases and shown on rectangles in the 3D scene,
// on the same plane as the video, so the ship and tower can pass in front of them just as they do the video.
const TEXT_RES = 3;                                             // canvas pixels per CSS pixel: keeps the type sharp when you zoom in
function makeTextLayer(w, h) {
  const c = document.createElement("canvas"); c.width = w * TEXT_RES; c.height = h * TEXT_RES;
  const ctx = c.getContext("2d"); ctx.scale(TEXT_RES, TEXT_RES);
  const tex = new THREE.CanvasTexture(c); tex.anisotropy = 8;
  return { w, h, ctx, tex };
}
const titleLayer = makeTextLayer(480, 118), lyricsLayer = makeTextLayer(480, 100);
const FONT_TITLE = '600 66px "Barlow Condensed", "Arial Narrow", sans-serif', FONT_LABEL = '500 21px "IBM Plex Mono", ui-monospace, Consolas, monospace';
const FONT_LYRIC = '400 30px "Barlow Condensed", "Arial Narrow", sans-serif', FONT_NEXT = '500 15px "IBM Plex Mono", ui-monospace, Consolas, monospace';
function drawTitle() {
  const { ctx, w, h, tex } = titleLayer; ctx.clearRect(0, 0, w, h);
  ctx.fillStyle = "#1d2930"; ctx.textBaseline = "middle"; ctx.textAlign = "left";
  ctx.font = FONT_LABEL; ctx.letterSpacing = "1.68px"; ctx.fillText(dateEl.textContent.toUpperCase(), 0, 25);
  ctx.font = FONT_TITLE; ctx.letterSpacing = "0.66px"; ctx.fillText(titleEl.textContent.toUpperCase(), 0, 79);
  tex.needsUpdate = true;
}
drawTitle();
Promise.all([FONT_TITLE, FONT_LABEL, FONT_LYRIC, FONT_NEXT].map((f) => document.fonts.load(f))).then(() => { drawTitle(); lyricsDirty = true; }).catch(() => {});

// The old line clears quickly first; then the new line arrives word by word, each word rising a little and sharpening into focus.
const easeOut = (x) => 1 - Math.pow(1 - Math.min(1, Math.max(0, x)), 3), easeIn = (x) => Math.pow(Math.min(1, Math.max(0, x)), 2);
const LYRIC_ANIM = { wordGap: 0.02, fade: 0.24, settle: 0.34, rise: 6.6, blur: 3, leave: 0.13, waitAfterLeave: 0.11, nextOut: 0.25, nextIn: 0.35 };
let activeLines = [], lyricsDirty = true;
const nextState = { text: "", pending: null, t: 0 };
const nowSec = () => performance.now() / 1000;
function showLine(text) {
  const t = nowSec(); let hadLine = false;
  for (const l of activeLines) if (l.leftAt === null) { l.leftAt = t; hadLine = true; }
  if (text) activeLines.push({ words: text.split(" ").filter(Boolean), t0: t + (hadLine ? LYRIC_ANIM.waitAfterLeave : 0), leftAt: null });
  lyricsDirty = true;
}
function showNext(text) {
  const target = nextState.pending !== null ? nextState.pending : nextState.text;
  if (target === text) return;
  if (nextState.pending === null) nextState.t = nowSec();        // start fading the old preview out
  nextState.pending = text; lyricsDirty = true;
}
function drawLyrics() {
  if (!lyricsDirty) return;
  const { ctx, w, h, tex } = lyricsLayer, t = nowSec(); let moving = false;
  ctx.clearRect(0, 0, w, h); ctx.textBaseline = "middle"; ctx.textAlign = "left";
  // current line (and any line still leaving)
  ctx.font = FONT_LYRIC; ctx.letterSpacing = "0.9px";
  activeLines = activeLines.filter((l) => l.leftAt === null || t - l.leftAt < LYRIC_ANIM.leave);
  const space = ctx.measureText(" ").width;
  for (const l of activeLines) {
    const widths = l.words.map((wd) => ctx.measureText(wd).width), total = widths.reduce((a, b) => a + b, 0) + space * (l.words.length - 1);
    const fit = Math.min(1, w / total), leaving = l.leftAt === null ? 0 : easeIn((t - l.leftAt) / LYRIC_ANIM.leave);
    if (l.leftAt !== null) moving = true;
    ctx.save(); ctx.translate(w / 2, 33 - 4 * leaving); ctx.scale(fit, fit);
    let x = -total / 2;
    l.words.forEach((wd, i) => {
      const age = t - l.t0 - i * LYRIC_ANIM.wordGap, a = easeOut(age / LYRIC_ANIM.fade), settle = easeOut(age / LYRIC_ANIM.settle);
      if (age < LYRIC_ANIM.settle) moving = true;
      const blur = LYRIC_ANIM.blur * Math.max(1 - a, leaving);
      if (a > 0.001) {
        ctx.globalAlpha = 0.72 * a * (1 - leaving); ctx.fillStyle = "#000";
        ctx.filter = blur > 0.05 ? `blur(${(blur * TEXT_RES).toFixed(2)}px)` : "none";
        ctx.fillText(wd, x, LYRIC_ANIM.rise * (1 - settle));
      }
      x += widths[i] + space;
    });
    ctx.restore();
  }
  // small preview of the next line, cross-fading when it changes
  let nextAlpha = 1;
  if (nextState.pending !== null) {
    const p = (t - nextState.t) / LYRIC_ANIM.nextOut; moving = true;
    if (p >= 1) { nextState.text = nextState.pending; nextState.pending = null; nextState.t = t; nextAlpha = 0; } else nextAlpha = 1 - p;
  } else { const p = (t - nextState.t) / LYRIC_ANIM.nextIn; nextAlpha = Math.min(1, p); if (p < 1) moving = true; }
  if (nextState.text && nextAlpha > 0.001) {
    ctx.filter = "none"; ctx.font = FONT_NEXT; ctx.letterSpacing = "0.45px"; ctx.globalAlpha = 0.45 * nextAlpha; ctx.fillStyle = "#000"; ctx.textAlign = "center";
    const tw = ctx.measureText(nextState.text).width, fit = Math.min(1, w / tw);
    ctx.save(); ctx.translate(w / 2, 74); ctx.scale(fit, fit); ctx.fillText(nextState.text, 0, 0); ctx.restore();
  }
  ctx.globalAlpha = 1; ctx.filter = "none";
  tex.needsUpdate = true; lyricsDirty = moving;
}
''')

# ---- text rectangles in the same extra pass as the hole ------------------------------------
rep('const holeScene = new THREE.Scene(); holeScene.add(hole);', '''const holeScene = new THREE.Scene(); holeScene.add(hole);
// Title and lyrics rectangles. They are drawn over the finished scene, mark the stencil wherever they put ink, and the
// nearer splats are then redrawn over them, exactly as for the video.
const textMaterial = (layer) => new THREE.ShaderMaterial({
  uniforms: { map: { value: layer.tex } },
  vertexShader: "varying vec2 vUv; void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
  fragmentShader: "uniform sampler2D map; varying vec2 vUv; void main() { vec4 c = texture2D(map, vUv); if (c.a < 0.01) discard; gl_FragColor = c; }",
  transparent: true, depthTest: false, depthWrite: false,
  stencilWrite: true, stencilRef: 1, stencilFunc: THREE.AlwaysStencilFunc, stencilZPass: THREE.ReplaceStencilOp,
});
const titlePlane = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), textMaterial(titleLayer));
const lyricsPlane = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), textMaterial(lyricsLayer));
titlePlane.frustumCulled = lyricsPlane.frustumCulled = false; titlePlane.renderOrder = lyricsPlane.renderOrder = 1;
holeScene.add(titlePlane, lyricsPlane);
// Place a rectangle that covers CSS rows [top, top + height) of the 480 x 578 panel.
function placeOnPanel(mesh, top, height, sc) {
  mesh.quaternion.copy(panel.quaternion); mesh.scale.set(PANEL.cssW * sc, height * sc, 1);
  mesh.position.copy(panel.position).addScaledVector(holeUp, (PANEL.cssH / 2 - (top + height / 2)) * sc);
  mesh.updateMatrixWorld(true);
}''')
rep('  hole.updateMatrixWorld(true);\n  renderer.autoClear = false; renderer.render(holeScene, camera);',
    '  hole.updateMatrixWorld(true);\n  placeOnPanel(titlePlane, 0, titleLayer.h, sc); placeOnPanel(lyricsPlane, VIDEO.top + VIDEO.h, lyricsLayer.h, sc);\n'
    '  drawLyrics();\n  renderer.autoClear = false; renderer.render(holeScene, camera);')

# ---- keep the overlay clear of the tower -----------------------------------------------------
rep('target: [2.21, 13.8, -0.42], groundNormal: [0.0076, 1, 0.0304], pivot: [2.42, 0.02, -0.14] }',
    'target: [2.21, 13.8, -0.42], tower: [0.0, 1.0], groundNormal: [0.0076, 1, 0.0304], pivot: [2.42, 0.02, -0.14] }', 0)
rep('if (f.cam) view = { cam: f.cam, target: f.target };', 'if (f.cam) view = { cam: f.cam, target: f.target, tower: f.tower };')
rep('                gap: 2.6,           // clear space between the ship\'s centre and the panel\'s near edge, in scene units',
    '                gap: 2.6,           // clear space between the ship\'s centre and the panel\'s near edge, in scene units\n'
    '                towerClear: 2.2,    // when the tower is on the panel\'s side of the ship, keep the panel this far beyond the tower\'s centre line')
rep('  const offset = PANEL.gap + panelScaleGoal * PANEL.cssW / 2;                     // keep the panel\'s near edge a fixed distance from the ship',
    '  // The tower stands about 2.6 units from the ship. When it is on the panel\'s side, slide the panel out past it instead of through it.\n'
    '  let gap = PANEL.gap;\n'
    '  if (view.tower) gap = Math.max(gap, (view.tower[0] - anchor.x) * right.x + (view.tower[1] - anchor.z) * right.z + PANEL.towerClear);\n'
    '  const offset = gap + panelScaleGoal * PANEL.cssW / 2;                           // keep the panel\'s near edge clear of the ship and tower')

io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('written', len(s))
