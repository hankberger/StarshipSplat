"""One-off edit: make the viewer work on phones and small screens."""
import io
p = 'viewer.html'
s = io.open(p, encoding='utf-8', newline='').read()
nl = '\r\n' if '\r\n' in s else '\n'


def rep(a, b):
    global s
    a = a.replace('\n', nl); b = b.replace('\n', nl)
    assert a in s, 'not found: ' + a[:80]
    s = s.replace(a, b, 1)


# ---- top bar and hint fit narrow screens ----------------------------------------------------
rep(' #bar{z-index:10}', ' #bar{z-index:10;flex-wrap:wrap;max-width:calc(100vw - 24px);box-sizing:border-box}\n'
    ' #bar select{max-width:min(52vw,360px);text-overflow:ellipsis}\n'
    ' @media (max-width:600px){ #bar{gap:6px;padding:6px 8px;font-size:13px} #bar label{display:none} #lyricTimerBtn{display:none} #hint{font-size:12px} }')
rep('home(); document.getElementById("reset").onclick',
    'if (matchMedia("(pointer: coarse)").matches) document.getElementById("hint").textContent = "Drag to orbit \\u00b7 two-finger drag to pan \\u00b7 pinch to zoom";\n'
    'home(); document.getElementById("reset").onclick')

# ---- the picture can shift vertically as well as sideways -----------------------------------
rep('const applyViewShift = () => { camera.setViewOffset(innerWidth, innerHeight, FEEL.shiftX * innerWidth, 0, innerWidth, innerHeight); camera.setFocalLength(LENS_MM); };',
    'const applyViewShift = () => { camera.setViewOffset(innerWidth, innerHeight, FEEL.shiftX * innerWidth, -FEEL.shiftY * innerHeight, innerWidth, innerHeight); camera.setFocalLength(LENS_MM); };')
rep('  shiftX: 0.07, ', '  shiftY: 0,                // vertical shift; used on tall (phone) screens, where the overlay sits above the ship\n  shiftX: 0.07, ')

# ---- panel layout: beside the ship on wide screens, above it on tall ones --------------------
rep('                maxScreenHeight: 0.8, maxScreenWidth: 0.5,',
    '                shortScreen: 700, shortScreenMax: 1.6,   // on screens shorter than this many pixels, enlarge the panel (up to this factor) so the video stays watchable\n'
    '                portrait: { below: 0.85,      // screens narrower than this width-to-height ratio use the stacked layout: overlay above the ship\n'
    '                            widthFrac: 0.86,  // the panel spans this much of the view\'s width at the home distance...\n'
    '                            maxHeightFrac: 0.5, // ...but no more than this much of its height\n'
    '                            shipTop: 3.3, shipBottom: -2.9, gap: 0.9 },   // the ship\'s extent above and below its centre, and the space left above it\n'
    '                maxScreenHeight: 0.8, maxScreenWidth: 0.5,')

rep('''  panelScaleGoal = Math.min(PANEL.worldHeight / PANEL.cssH, PANEL.maxScreenHeight * viewH / PANEL.cssH, PANEL.maxScreenWidth * viewW / PANEL.cssW);''',
    '''  const portrait = camera.aspect < PANEL.portrait.below;
  if (portrait) {
    // Tall screen: there is no room beside the ship, so the overlay goes above it, as wide as the screen allows.
    // Its size is fixed in the scene from the home view, so zooming still makes it bigger.
    const homeDist = Math.hypot(view.cam[0] - view.target[0], view.cam[1] - view.target[1], view.cam[2] - view.target[2]);
    const homeH = viewH * homeDist / dist, homeW = homeH * camera.aspect;
    const worldH = Math.min(PANEL.portrait.widthFrac * homeW * PANEL.cssH / PANEL.cssW, PANEL.portrait.maxHeightFrac * homeH);
    panelScaleGoal = Math.min(worldH / PANEL.cssH, PANEL.maxScreenHeight * viewH / PANEL.cssH, 0.94 * viewW / PANEL.cssW);
    const panelH = panelScaleGoal * PANEL.cssH, lift = PANEL.portrait.shipTop + PANEL.portrait.gap + panelH / 2;
    shiftGoal = 0;                                                                // centred left to right
    shiftYGoal = THREE.MathUtils.clamp((PANEL.portrait.shipBottom + lift + panelH / 2) / 2 / viewH, 0, 0.42);   // frame ship + overlay together
    return goal.copy(anchor).addScaledVector(UP, lift);
  }
  shiftYGoal = 0;
  const boost = THREE.MathUtils.clamp(PANEL.shortScreen / innerHeight, 1, PANEL.shortScreenMax);
  panelScaleGoal = Math.min(PANEL.worldHeight * boost / PANEL.cssH, PANEL.maxScreenHeight * viewH / PANEL.cssH, PANEL.maxScreenWidth * viewW / PANEL.cssW);''')
rep('let panelScaleGoal = 0.016, shiftGoal = FEEL.shiftX;', 'let panelScaleGoal = 0.016, shiftGoal = FEEL.shiftX, shiftYGoal = 0;')
rep('''  const sx = THREE.MathUtils.lerp(FEEL.shiftX, shiftGoal, 1 - Math.exp(-6 * dt));
  if (Math.abs(sx - FEEL.shiftX) > 1e-4) { FEEL.shiftX = sx; applyViewShift(); }''',
    '''  const sx = THREE.MathUtils.lerp(FEEL.shiftX, shiftGoal, 1 - Math.exp(-6 * dt)), sy = THREE.MathUtils.lerp(FEEL.shiftY, shiftYGoal, 1 - Math.exp(-6 * dt));
  if (Math.abs(sx - FEEL.shiftX) > 1e-4 || Math.abs(sy - FEEL.shiftY) > 1e-4) { FEEL.shiftX = sx; FEEL.shiftY = sy; applyViewShift(); }''')

io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('written', len(s))
