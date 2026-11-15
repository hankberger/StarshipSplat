"""One-off edit: camera feel, composition, constant-size panel, auto-orbit and eased moves for viewer.html."""
import io
p = 'viewer.html'
s = io.open(p, encoding='utf-8', newline='').read()
nl = '\r\n' if '\r\n' in s else '\n'


def rep(a, b):
    global s
    a = a.replace('\n', nl); b = b.replace('\n', nl)
    assert a in s, 'not found: ' + a[:70]
    s = s.replace(a, b, 1)


rep('''window.__v = { camera, controls };''', '''window.__v = { camera, controls };
// How the camera feels and how the shot is composed.
const FEEL = {
  damping: 0.07,            // inertia: lower = longer glide after you let go
  rotateSpeed: 0.45,        // drag sensitivity (1 is the library default; lower suits a long lens)
  zoomSpeed: 0.6,
  minDistance: 45, maxDistance: 240,   // how close and how far the camera may go
  maxElevationDeg: 60,      // highest angle above the horizon
  shiftX: 0.11,             // picture shifted this fraction of the width, so the ship sits left of centre
  autoOrbitDegPerSec: 2.5,  // slow drift when nobody is touching the camera
  idleSeconds: 6,           // how long to wait before the drift starts
  moveSeconds: 1.8,         // eased camera move for "Reset view"
  introSeconds: 3.2,        // eased camera move when a scene opens
};
controls.enableDamping = true; controls.dampingFactor = FEEL.damping;
controls.rotateSpeed = FEEL.rotateSpeed; controls.zoomSpeed = FEEL.zoomSpeed;
controls.minDistance = FEEL.minDistance; controls.maxDistance = FEEL.maxDistance;
controls.minPolarAngle = THREE.MathUtils.degToRad(90 - FEEL.maxElevationDeg);
controls.autoRotateSpeed = -FEEL.autoOrbitDegPerSec / 6;
const applyViewShift = () => { camera.setViewOffset(innerWidth, innerHeight, FEEL.shiftX * innerWidth, 0, innerWidth, innerHeight); camera.setFocalLength(LENS_MM); };
applyViewShift();
let interacting = false, lastInteraction = performance.now();
controls.addEventListener("start", () => { interacting = true; controls.autoRotate = false; });
controls.addEventListener("end", () => { interacting = false; lastInteraction = performance.now(); });
// Eased camera moves: travel around the orbit point rather than cutting straight across.
let move = null; const sph = new THREE.Spherical(), tmpV = new THREE.Vector3();
function flyTo(pos, target, seconds) {
  const toTarget = new THREE.Vector3(...target);
  const from = new THREE.Spherical().setFromVector3(tmpV.copy(camera.position).sub(controls.target));
  const to = new THREE.Spherical().setFromVector3(tmpV.set(...pos).sub(toTarget));
  let dTheta = to.theta - from.theta; dTheta = Math.atan2(Math.sin(dTheta), Math.cos(dTheta));   // the short way round
  move = { t: 0, seconds, from, to, dTheta, fromTarget: controls.target.clone(), toTarget };
  controls.enabled = false; controls.autoRotate = false;
}
function updateMove(dt) {
  if (!move) return;
  move.t = Math.min(1, move.t + dt / move.seconds);
  const e = move.t < 0.5 ? 4 * move.t ** 3 : 1 - Math.pow(-2 * move.t + 2, 3) / 2;               // ease in and out
  sph.radius = THREE.MathUtils.lerp(move.from.radius, move.to.radius, e);
  sph.phi = THREE.MathUtils.lerp(move.from.phi, move.to.phi, e);
  sph.theta = move.from.theta + move.dTheta * e;
  controls.target.lerpVectors(move.fromTarget, move.toTarget, e);
  camera.position.setFromSpherical(sph).add(controls.target);
  if (move.t >= 1) { move = null; controls.enabled = true; lastInteraction = performance.now(); }
}
// Opening shot: start wider, higher and a little round to one side, then settle into the home view.
function intro() {
  const t = new THREE.Vector3(...view.target), s0 = new THREE.Spherical().setFromVector3(new THREE.Vector3(...view.cam).sub(t));
  s0.radius = Math.min(FEEL.maxDistance, s0.radius * 1.45); s0.theta += 0.55; s0.phi = Math.max(controls.minPolarAngle, s0.phi - 0.16);
  controls.target.copy(t); camera.position.setFromSpherical(s0).add(t); controls.update();
  flyTo(view.cam, view.target, FEEL.introSeconds);
}''')

rep('home(); document.getElementById("reset").onclick = home;',
    'home(); document.getElementById("reset").onclick = () => flyTo(view.cam, view.target, FEEL.moveSeconds);')
rep('home(); show({ url: f.url }, f); };', 'home(); intro(); show({ url: f.url }, f); };')

rep('''const files = [
''', '''const files = [
  { label: "New clips, cleaned, soft-edged base", url: "splats_r2/cleaned_disc_soft.spz", cam: [112, 5, 102], target: [2.21, 13.8, -0.42], groundNormal: [0.0076, 1, 0.0304], pivot: [2.42, 0.02, -0.14] },
''')

# Panel: placed and sized as fractions of the view, so the composition holds at any zoom.
rep('''                offset: 9,      // distance to the right of the rocket, in scene units
                lift: 1.5,      // height above the orbit target
                size: 0.016,    // scene units per CSS pixel (480x360, 4:3 -> about 7.7 x 5.8 units)
                ease: 4 };      // higher = snappier follow''',
    '''                offsetFrac: 0.21,   // how far right of the ship the panel's centre sits, as a fraction of the view's width
                liftFrac: -0.02,    // panel centre above (+) or below (-) the ship's centre, as a fraction of the view's height
                screenHeight: 0.44, // the whole panel (title, video, lyrics) fills this fraction of the view's height...
                screenWidth: 0.30,  // ...but never more than this fraction of its width
                cssW: 480, cssH: 578,
                ease: 4 };          // higher = snappier follow''')

rep('''const panel = new CSS3DObject(panelEl); panel.scale.setScalar(PANEL.size); scene.add(panel);''',
    '''const panel = new CSS3DObject(panelEl); scene.add(panel);''')

rep('''function panelGoal() {
  camera.getWorldDirection(fwd); right.crossVectors(fwd, UP);
  if (right.lengthSq() < 1e-6) right.set(1, 0, 0);          // looking straight up or down
  right.normalize();
  return goal.copy(controls.target).addScaledVector(right, PANEL.offset).addScaledVector(UP, PANEL.lift);
}''', '''let panelScaleGoal = 0.016;
function panelGoal() {
  camera.getWorldDirection(fwd); right.crossVectors(fwd, UP);
  if (right.lengthSq() < 1e-6) right.set(1, 0, 0);          // looking straight up or down
  right.normalize();
  // Size of the view at the ship's distance, in scene units. Working in fractions of it keeps the panel the same size
  // on screen, and in the same place relative to the ship, however far the camera is.
  const dist = camera.position.distanceTo(controls.target);
  const viewH = 2 * dist * Math.tan(THREE.MathUtils.degToRad(camera.getEffectiveFOV()) / 2), viewW = viewH * camera.aspect;
  panelScaleGoal = Math.min(PANEL.screenHeight * viewH / PANEL.cssH, PANEL.screenWidth * viewW / PANEL.cssW);
  return goal.copy(controls.target).addScaledVector(right, PANEL.offsetFrac * viewW).addScaledVector(UP, PANEL.liftFrac * viewH);
}''')

rep('''  if (!panelPlaced) { panel.position.copy(g); panel.quaternion.copy(camera.quaternion); panelPlaced = true; return; }
  const k = 1 - Math.exp(-PANEL.ease * dt);                  // frame-rate independent easing
  panel.position.lerp(g, k); panel.quaternion.slerp(camera.quaternion, k);''',
    '''  if (!panelPlaced) { panel.position.copy(g); panel.quaternion.copy(camera.quaternion); panel.scale.setScalar(panelScaleGoal); panelPlaced = true; return; }
  const k = 1 - Math.exp(-PANEL.ease * dt);                  // frame-rate independent easing
  panel.position.lerp(g, k); panel.quaternion.slerp(camera.quaternion, k);
  panel.scale.setScalar(THREE.MathUtils.lerp(panel.scale.x, panelScaleGoal, 1 - Math.exp(-10 * dt)));''')

rep('''addEventListener("resize", () => { camera.aspect = innerWidth / innerHeight; camera.setFocalLength(LENS_MM); renderer.setSize(innerWidth, innerHeight); css.setSize(innerWidth, innerHeight); });''',
    '''addEventListener("resize", () => { camera.aspect = innerWidth / innerHeight; applyViewShift(); renderer.setSize(innerWidth, innerHeight); css.setSize(innerWidth, innerHeight); });''')

rep('''const GROUND = { y: 0, clearance: 1.0 };''', '''const GROUND = { y: 0, clearance: 2.5 };''')

rep('''limitToGround(); controls.update(); updatePanel(dt);''',
    '''updateMove(dt); limitToGround();
  controls.autoRotate = !move && !interacting && performance.now() - lastInteraction > FEEL.idleSeconds * 1000;   // drift when idle
  controls.update(dt); updatePanel(dt);''')

io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('written', len(s))
