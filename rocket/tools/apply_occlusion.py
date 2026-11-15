"""One-off edit: let the scene pass in front of the video panel (depth-correct occlusion), and stop lyric descenders being clipped."""
import io
p = 'viewer.html'
s = io.open(p, encoding='utf-8', newline='').read()
nl = '\r\n' if '\r\n' in s else '\n'


def rep(a, b):
    global s
    a = a.replace('\n', nl); b = b.replace('\n', nl)
    assert a in s, 'not found: ' + a[:80]
    s = s.replace(a, b, 1)


# ---- layers, bottom to top: #input (camera gestures) < #css3d (video) < canvas (3D scene) < #css3dFront (title + lyrics) < UI
rep(' canvas{position:fixed;inset:0}',
    ' canvas{position:fixed;inset:0;z-index:2;pointer-events:none}\n #input{position:fixed;inset:0;z-index:0}')
rep(' #css3d{position:fixed;inset:0;pointer-events:none;z-index:5}',
    ' #css3d{position:fixed;inset:0;pointer-events:none;z-index:1}\n #css3dFront{position:fixed;inset:0;pointer-events:none;z-index:3}')

# ---- lyric descenders were clipped
rep('gap:8px;overflow:hidden}', 'gap:8px;overflow:visible}')
rep('.panel .lyrics .next{text-align:center;font:500 15px/1 ', '.panel .lyrics .next{text-align:center;font:500 15px/1.5 ')
rep('.panel .lyrics .now{position:relative;height:34px;', '.panel .lyrics .now{position:relative;height:38px;')

# ---- renderer needs transparency (to show the video through a hole) and a stencil buffer (to confine the second pass to that hole)
rep('const renderer = new THREE.WebGLRenderer({ antialias: false });',
    'const renderer = new THREE.WebGLRenderer({ antialias: false, alpha: true, stencil: true });')

rep('scene.add(new SparkRenderer({ renderer }));',
    'const spark = new SparkRenderer({ renderer }); scene.add(spark);\n'
    '// The 3D canvas no longer takes the mouse (so clicks can reach the video beneath it); camera gestures land on this layer at the bottom.\n'
    'const inputEl = document.createElement("div"); inputEl.id = "input"; document.body.appendChild(inputEl);')
rep('const controls = new OrbitControls(camera, renderer.domElement);', 'const controls = new OrbitControls(camera, inputEl);')

rep('  apron.rotation.x = -Math.PI / 2; apron.position.y = APRON.y; apron.renderOrder = -500;\n  scene.add(apron);',
    '  apron.rotation.x = -Math.PI / 2; apron.position.y = APRON.y; apron.renderOrder = -500;\n  apron.userData.backdrop = true; scene.add(apron);')
rep('scene.add(skyDome); window.__v && (window.__v.skyDome = skyDome);',
    'skyDome.userData.backdrop = true; scene.add(skyDome); window.__v && (window.__v.skyDome = skyDome);')

rep('const css = new CSS3DRenderer(); css.domElement.id = "css3d"; css.setSize(innerWidth, innerHeight); document.body.appendChild(css.domElement);',
    'const css = new CSS3DRenderer(); css.domElement.id = "css3d"; css.setSize(innerWidth, innerHeight); document.body.appendChild(css.domElement);\n'
    'const cssFront = new CSS3DRenderer(); cssFront.domElement.id = "css3dFront"; cssFront.setSize(innerWidth, innerHeight); document.body.appendChild(cssFront.domElement);')

rep('const panel = new CSS3DObject(panelEl); scene.add(panel);', '''// The panel is split across two layers. The video sits BEHIND the 3D canvas and shows through a hole cut in it, so the
// tower and ship can pass in front of it. The title and lyrics have no background of their own (the sky shows through them),
// so they stay in a layer in FRONT of the canvas.
const panelFrontEl = document.createElement("div"); panelFrontEl.className = "panel";
const gapTop = document.createElement("div"); gapTop.style.cssText = "height:118px;flex:none";
const gapMid = document.createElement("div"); gapMid.style.cssText = "height:360px;flex:none";
panelEl.insertBefore(gapTop, frame); panelFrontEl.append(headEl, gapMid, lyricsEl);
frame.style.boxShadow = "none";                                   // the shadow would be hidden behind the canvas anyway
const panel = new CSS3DObject(panelEl), panelFront = new CSS3DObject(panelFrontEl);
const backScene = new THREE.Scene(), frontScene = new THREE.Scene(); backScene.add(panel); frontScene.add(panelFront);
// The hole: an invisible rectangle exactly over the video that erases the canvas there (and marks the stencil).
const VIDEO = { top: 118, w: 480, h: 360, radius: 12, inset: 1 };  // the video's place inside the panel, in CSS pixels
const hole = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.ShaderMaterial({
  uniforms: { uHalf: { value: new THREE.Vector2(VIDEO.w / 2 - VIDEO.inset, VIDEO.h / 2 - VIDEO.inset) }, uRadius: { value: VIDEO.radius } },
  vertexShader: "varying vec2 vUv; void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
  fragmentShader: "uniform vec2 uHalf; uniform float uRadius; varying vec2 vUv;" +
    "void main() { vec2 p = abs((vUv - 0.5) * 2.0 * uHalf) - (uHalf - vec2(uRadius));" +     // rounded rectangle, to match the video's corners
    " if (length(max(p, 0.0)) > uRadius) discard; gl_FragColor = vec4(0.0); }",
  blending: THREE.NoBlending, depthTest: false, depthWrite: false,
  stencilWrite: true, stencilRef: 1, stencilFunc: THREE.AlwaysStencilFunc, stencilZPass: THREE.ReplaceStencilOp,
}));
hole.frustumCulled = false;
const holeScene = new THREE.Scene(); holeScene.add(hole);
const holeUp = new THREE.Vector3(), holeCorner = new THREE.Vector3(), camFwd = new THREE.Vector3();
// Draw the frame in three steps: (1) the whole scene; (2) cut the hole over the video; (3) redraw, inside the hole only,
// just the splats that are nearer to the camera than the panel, so they cover the video the way a real object would.
function renderWithOcclusion() {
  renderer.autoClear = true; renderer.render(scene, camera);
  if (!panel.visible) return;
  const sc = panel.scale.x;
  holeUp.set(0, 1, 0).applyQuaternion(panel.quaternion);
  hole.quaternion.copy(panel.quaternion); hole.scale.set(VIDEO.w * sc, VIDEO.h * sc, 1);
  hole.position.copy(panel.position).addScaledVector(holeUp, (PANEL.cssH / 2 - (VIDEO.top + VIDEO.h / 2)) * sc);
  hole.updateMatrixWorld(true);
  renderer.autoClear = false; renderer.render(holeScene, camera);
  // How far away the video is along the view direction; anything nearer is "in front".
  camera.getWorldDirection(camFwd);
  const depth = holeCorner.copy(hole.position).sub(camera.position).dot(camFwd);
  if (depth > camera.near * 2) {
    const far0 = camera.far, hidden = [];
    for (const o of scene.children) if (o.userData.backdrop && o.visible) { o.visible = false; hidden.push(o); }
    const m = spark.material;
    if (m) { m.stencilWrite = true; m.stencilFunc = THREE.EqualStencilFunc; m.stencilRef = 1; m.stencilWriteMask = 0x00; }
    camera.far = depth; camera.updateProjectionMatrix();
    renderer.render(scene, camera);
    camera.far = far0; camera.updateProjectionMatrix();
    if (m) { m.stencilWrite = false; m.stencilWriteMask = 0xff; }
    for (const o of hidden) o.visible = true;
  }
  renderer.autoClear = true;
}''')

rep('panelToggle.onclick = () => { panel.visible = !panel.visible; panelEl.style.display = panel.visible ? "" : "none";',
    'panelToggle.onclick = () => { panel.visible = !panel.visible; panelEl.style.display = panelFrontEl.style.display = panel.visible ? "" : "none";')
rep('renderer.setSize(innerWidth, innerHeight); css.setSize(innerWidth, innerHeight); });',
    'renderer.setSize(innerWidth, innerHeight); css.setSize(innerWidth, innerHeight); cssFront.setSize(innerWidth, innerHeight); });')
rep('renderer.render(scene, camera); css.render(scene, camera); });',
    'panelFront.position.copy(panel.position); panelFront.quaternion.copy(panel.quaternion); panelFront.scale.copy(panel.scale);\n'
    '  renderWithOcclusion(); css.render(backScene, camera); cssFront.render(frontScene, camera); });')

io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('written', len(s))
