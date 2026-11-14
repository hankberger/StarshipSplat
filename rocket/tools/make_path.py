import bpy, math
from mathutils import Matrix
sc = bpy.context.scene
col = bpy.data.collections.get("Flythrough path") or bpy.data.collections.new("Flythrough path")
if col.name not in sc.collection.children: sc.collection.children.link(col)
for n in ("Orbit pivot", "Tower target", "Flythrough camera"):
    o = bpy.data.objects.get(n)
    if o: bpy.data.objects.remove(o)
Cb = (-5.34, -1.2, 9.0)
pivot = bpy.data.objects.new("Orbit pivot", None); pivot.location = Cb; pivot.empty_display_size = 2; col.objects.link(pivot)
tgt = bpy.data.objects.new("Tower target", None); tgt.location = Cb; tgt.empty_display_size = 1; col.objects.link(tgt)
cd = bpy.data.cameras.new("Flythrough camera"); cd.sensor_width = 36; cd.lens = 36*1461/1280; cd.clip_end = 5000
cam = bpy.data.objects.new("Flythrough camera", cd); col.objects.link(cam); cam.parent = pivot
con = cam.constraints.new("TRACK_TO"); con.target = tgt; con.track_axis = "TRACK_NEGATIVE_Z"; con.up_axis = "UP_Y"
N = 288
sc.render.resolution_x, sc.render.resolution_y, sc.render.fps = 1280, 720, 24
sc.frame_start, sc.frame_end = 1, N
pivot.rotation_euler = (0, 0, math.radians(27)); pivot.keyframe_insert("rotation_euler", frame=1)
pivot.rotation_euler = (0, 0, math.radians(27-360)); pivot.keyframe_insert("rotation_euler", frame=N)
for f, r, h in ((1, 20.5, -0.4), (96, 20.0, 3.5), (192, 21.0, 4.5), (N, 19.0, 0.2)):
    cam.location = (r, 0, h); cam.keyframe_insert("location", frame=f)
sc.camera = cam
T = Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)))
out = []
for f in range(1, N+1):
    sc.frame_set(f)
    M = T @ cam.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world
    q = M.to_quaternion(); p = M.translation
    out.append({"position": [p.x, p.y, p.z], "quaternion": [q.x, q.y, q.z, q.w]})
sc.frame_set(1)
def _s():
    bpy.ops.wm.save_mainfile(); return None
bpy.app.timers.register(_s, first_interval=0.5)
result = {"cams": out}
